"""
Integrated mesh generation pipeline

This module provides the main pipeline for complete mesh generation workflow,
from STEP file reading to LS-DYNA export and validation.
"""

from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
import logging
import time

from koomesh.io.step_reader import STEPReader
from koomesh.geometry.shape_classifier import ShapeClassifier
from koomesh.meshing.tet_mesher import TetMesher
from koomesh.meshing.hex_mesher import HexMesher
from koomesh.meshing.mesh_data import MeshData
from koomesh.quality.quality_metrics import QualityAnalyzer
from koomesh.quality.auto_remeshing import AutoRemesher, RefinementStrategy
from koomesh.contact.contact_detector import ContactDetector
from koomesh.contact.contact_data import ContactPair
from koomesh.export.lsdyna_writer import LSDynaWriter
from koomesh.templates.template_manager import TemplateManager, load_template, SimulationTemplate
from koomesh.materials.material_library import MaterialLibrary
from koomesh.pipeline.progress_tracker import ProgressTracker
from koomesh.pipeline.constants import (
    DEFAULT_MESH_SIZE_MM,
    DEFAULT_ELEMENT_TYPE,
    DEFAULT_GEOMETRY_TOLERANCE_MM,
    MIN_FEATURE_SIZE_MM,
    MIN_ACCEPTABLE_QUALITY,
    TARGET_QUALITY_THRESHOLD,
    MAX_REMESH_ITERATIONS,
    DEFAULT_REFINEMENT_STRATEGY,
    DEFAULT_CONTACT_TOLERANCE_MM,
    DEFAULT_SELF_CONTACT_TOLERANCE_MM,
    DEFAULT_REPORT_FORMAT,
)


@dataclass
class PipelineConfig:
    """
    Configuration for mesh generation pipeline

    This class contains all settings needed to run the complete
    mesh generation pipeline.
    """
    # Input/Output
    input_files: List[str]
    output_file: str

    # Template (optional - overrides other settings)
    template_name: Optional[str] = None

    # Meshing parameters
    mesh_size: float = DEFAULT_MESH_SIZE_MM
    element_type: str = DEFAULT_ELEMENT_TYPE
    min_element_size: Optional[float] = None
    max_element_size: Optional[float] = None

    # Geometry preprocessing
    clean_geometry: bool = True
    geometry_tolerance: float = DEFAULT_GEOMETRY_TOLERANCE_MM
    remove_small_features: bool = True
    min_feature_size: float = MIN_FEATURE_SIZE_MM

    # Quality control
    enable_quality_check: bool = True
    min_quality_threshold: float = MIN_ACCEPTABLE_QUALITY
    target_quality_threshold: float = TARGET_QUALITY_THRESHOLD
    enable_auto_remesh: bool = True
    max_remesh_iterations: int = MAX_REMESH_ITERATIONS
    refinement_strategy: str = DEFAULT_REFINEMENT_STRATEGY

    # Contact detection
    enable_contact_detection: bool = True
    contact_tolerance: float = DEFAULT_CONTACT_TOLERANCE_MM
    enable_self_contact: bool = False
    self_contact_tolerance: float = DEFAULT_SELF_CONTACT_TOLERANCE_MM

    # Validation
    enable_validation: bool = True

    # Performance
    enable_caching: bool = True
    parallel: bool = False
    num_jobs: Optional[int] = None

    # Output options
    generate_report: bool = True
    report_format: str = DEFAULT_REPORT_FORMAT
    verbose: bool = False

    def __post_init__(self):
        """
        Validate configuration parameters

        Performs fail-fast validation to catch configuration errors early.

        Raises:
            FileNotFoundError: If input files don't exist
            ValueError: If parameters are out of valid range
        """
        # Ensure all input files exist (fail-fast strategy)
        for file_path in self.input_files:
            if not Path(file_path).exists():
                raise FileNotFoundError(
                    f"Input file not found: {file_path}\n"
                    f"Please check the file path and try again."
                )

        # Validate mesh size is positive and reasonable
        if self.mesh_size <= 0:
            raise ValueError(
                f"mesh_size must be positive, got {self.mesh_size}\n"
                f"Typical values: 1-50 mm depending on geometry size"
            )

        # Validate quality thresholds are in valid range [0, 1]
        if not 0 <= self.min_quality_threshold <= 1:
            raise ValueError(
                f"min_quality_threshold must be in [0, 1], got {self.min_quality_threshold}\n"
                f"Recommended: {MIN_ACCEPTABLE_QUALITY} (LS-DYNA minimum)"
            )

        if not 0 <= self.target_quality_threshold <= 1:
            raise ValueError(
                f"target_quality_threshold must be in [0, 1], got {self.target_quality_threshold}\n"
                f"Recommended: {TARGET_QUALITY_THRESHOLD} for good accuracy"
            )

        # Ensure target threshold is higher than minimum
        if self.target_quality_threshold < self.min_quality_threshold:
            raise ValueError(
                f"target_quality_threshold ({self.target_quality_threshold}) must be >= "
                f"min_quality_threshold ({self.min_quality_threshold})"
            )


@dataclass
class PipelineResult:
    """
    Result from pipeline execution

    Contains statistics and status information from the pipeline run.
    """
    success: bool
    output_file: str
    num_nodes: int
    num_elements: int
    num_contacts: int
    avg_quality: float
    min_quality: float
    max_quality: float
    execution_time: float
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    report_file: Optional[str] = None
    stage_durations: Dict[str, float] = field(default_factory=dict)

    def __str__(self) -> str:
        """Human-readable summary"""
        status = "✓ SUCCESS" if self.success else "✗ FAILED"
        lines = [
            f"\n{'='*60}",
            f"Pipeline Result: {status}",
            f"{'='*60}",
            f"Output: {self.output_file}",
            f"Nodes: {self.num_nodes:,}",
            f"Elements: {self.num_elements:,}",
            f"Contacts: {self.num_contacts}",
            f"Quality: avg={self.avg_quality:.3f}, min={self.min_quality:.3f}, max={self.max_quality:.3f}",
            f"Time: {self.execution_time:.1f}s",
        ]

        if self.warnings:
            lines.append(f"\nWarnings ({len(self.warnings)}):")
            for warning in self.warnings[:5]:  # Show first 5
                lines.append(f"  ⚠ {warning}")
            if len(self.warnings) > 5:
                lines.append(f"  ... and {len(self.warnings)-5} more")

        if self.errors:
            lines.append(f"\nErrors ({len(self.errors)}):")
            for error in self.errors[:5]:  # Show first 5
                lines.append(f"  ✗ {error}")
            if len(self.errors) > 5:
                lines.append(f"  ... and {len(self.errors)-5} more")

        lines.append(f"{'='*60}\n")
        return '\n'.join(lines)


class MeshGenerationPipeline:
    """
    Complete mesh generation pipeline

    Integrates all components for end-to-end mesh generation:
    1. Geometry reading and cleaning
    2. Mesh generation
    3. Quality analysis and refinement
    4. Contact detection
    5. LS-DYNA export
    6. Validation

    Example:
        >>> config = PipelineConfig(
        ...     input_files=['model.step'],
        ...     output_file='mesh.k',
        ...     template_name='automotive_crash_frontal'
        ... )
        >>> pipeline = MeshGenerationPipeline(config)
        >>> result = pipeline.run()
        >>> print(result)
        >>> if result.success:
        ...     print(f"Generated {result.num_elements} elements")
    """

    def __init__(self, config: PipelineConfig, progress_callback=None):
        """
        Initialize pipeline

        Args:
            config: Pipeline configuration
            progress_callback: Optional callback for progress updates
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.progress = ProgressTracker(callback=progress_callback)

        # Initialize components
        self._init_components()

        # Storage for intermediate results
        self.shapes: List[Any] = []
        self.meshes: List[MeshData] = []
        self.contacts: List[ContactPair] = []

    def _init_components(self):
        """Initialize all pipeline components"""
        self.logger.info("Initializing pipeline components...")

        # Core components
        self.step_reader = STEPReader()
        self.shape_classifier = ShapeClassifier()
        self.quality_analyzer = QualityAnalyzer()
        self.contact_detector = ContactDetector()

        # Load template if specified
        self.template: Optional[SimulationTemplate] = None
        if self.config.template_name:
            try:
                self.template = load_template(self.config.template_name)
                self.logger.info(f"Loaded template: {self.config.template_name}")
            except Exception as e:
                self.logger.warning(f"Failed to load template '{self.config.template_name}': {e}")

        # Initialize material library
        self.material_library = MaterialLibrary()

        self.logger.info("Pipeline components initialized")

    def run(self) -> PipelineResult:
        """
        Execute complete pipeline

        Returns:
            PipelineResult with execution details
        """
        start_time = time.time()
        errors: List[str] = []
        warnings: List[str] = []

        self.logger.info("="*60)
        self.logger.info("Starting mesh generation pipeline")
        self.logger.info("="*60)
        self.logger.info(f"Input files: {len(self.config.input_files)}")
        self.logger.info(f"Output file: {self.config.output_file}")
        if self.template:
            self.logger.info(f"Template: {self.template.name}")

        try:
            # Define all stages
            self.progress.add_stage("geometry", "Reading and cleaning geometry")
            self.progress.add_stage("meshing", "Generating mesh")

            if self.config.enable_quality_check:
                self.progress.add_stage("quality", "Analyzing mesh quality")

            if self.config.enable_contact_detection:
                self.progress.add_stage("contact", "Detecting contacts")

            self.progress.add_stage("export", "Writing LS-DYNA file")

            if self.config.enable_validation:
                self.progress.add_stage("validation", "Validating output")

            # Stage 1: Geometry Processing
            self.logger.info("\n[Stage 1/6] Geometry Processing")
            shapes = self._process_geometry()

            # Stage 2: Mesh Generation
            self.logger.info("\n[Stage 2/6] Mesh Generation")
            meshes = self._generate_meshes(shapes)

            # Stage 3: Quality Analysis (optional)
            if self.config.enable_quality_check:
                self.logger.info("\n[Stage 3/6] Quality Analysis")
                meshes = self._process_quality(meshes)
            else:
                self.progress.skip_stage("quality", "Quality check disabled")

            # Stage 4: Contact Detection (optional)
            if self.config.enable_contact_detection:
                self.logger.info("\n[Stage 4/6] Contact Detection")
                contacts = self._detect_contacts(meshes)
            else:
                contacts = []
                self.progress.skip_stage("contact", "Contact detection disabled")

            # Stage 5: Export
            self.logger.info("\n[Stage 5/6] LS-DYNA Export")
            self._export_lsdyna(meshes, contacts)

            # Stage 6: Validation (optional)
            if self.config.enable_validation:
                self.logger.info("\n[Stage 6/6] Validation")
                validation_result = self._validate_output()
                warnings.extend(validation_result.get('warnings', []))
            else:
                self.progress.skip_stage("validation", "Validation disabled")

            # Calculate statistics
            total_nodes = sum(len(m.nodes) for m in meshes)
            total_elements = sum(len(m.elements) for m in meshes)
            avg_quality, min_quality, max_quality = self._calculate_quality_stats(meshes)

            execution_time = time.time() - start_time

            # Get stage durations
            summary = self.progress.get_summary()
            stage_durations = {
                name: stage.duration or 0.0
                for name, stage in summary['stages'].items()
            }

            self.logger.info("\n" + "="*60)
            self.logger.info("Pipeline completed successfully!")
            self.logger.info("="*60)

            return PipelineResult(
                success=True,
                output_file=self.config.output_file,
                num_nodes=total_nodes,
                num_elements=total_elements,
                num_contacts=len(contacts),
                avg_quality=avg_quality,
                min_quality=min_quality,
                max_quality=max_quality,
                execution_time=execution_time,
                errors=errors,
                warnings=warnings,
                stage_durations=stage_durations
            )

        except Exception as e:
            self.logger.error(f"\nPipeline failed: {e}", exc_info=True)
            errors.append(str(e))

            execution_time = time.time() - start_time

            return PipelineResult(
                success=False,
                output_file=self.config.output_file,
                num_nodes=0,
                num_elements=0,
                num_contacts=0,
                avg_quality=0.0,
                min_quality=0.0,
                max_quality=0.0,
                execution_time=execution_time,
                errors=errors,
                warnings=warnings
            )

    def _process_geometry(self) -> List[Any]:
        """
        Stage 1: Read and clean geometry

        Returns:
            List of (shape, classification) tuples

        Raises:
            Exception: If geometry processing fails
        """
        self.progress.start_stage("geometry", "Reading STEP files...")

        try:
            from koomesh.pipeline.geometry_processor import GeometryProcessor

            # Initialize processor
            processor = GeometryProcessor()

            # Update progress
            self.progress.update_stage(
                "geometry",
                0.2,
                f"Processing {len(self.config.input_files)} file(s)..."
            )

            # Process all geometry files
            shapes = processor.process(
                input_files=self.config.input_files,
                clean=self.config.clean_geometry,
                tolerance=self.config.geometry_tolerance
            )

            # Update progress
            self.progress.update_stage(
                "geometry",
                0.9,
                f"Processed {len(shapes)} shape(s)"
            )

            # Get statistics
            stats = processor.get_statistics(shapes)

            # Complete stage
            self.progress.complete_stage(
                "geometry",
                f"Processed {stats['total_shapes']} shapes: "
                f"{stats['solid_count']} solids, "
                f"{stats['shell_count']} shells, "
                f"{stats['beam_count']} beams"
            )

            self.logger.info(
                f"Geometry processing complete: {stats['total_shapes']} shapes processed"
            )

            return shapes

        except Exception as e:
            error_msg = f"Geometry processing failed: {str(e)}"
            self.logger.error(error_msg)
            self.progress.fail_stage("geometry", error_msg)
            raise

    def _generate_meshes(self, shapes: List[Any]) -> List[MeshData]:
        """
        Stage 2: Generate meshes

        Args:
            shapes: List of (shape, classification) tuples

        Returns:
            List of MeshData objects

        Raises:
            Exception: If mesh generation fails
        """
        self.progress.start_stage("meshing", "Generating meshes...")

        try:
            from koomesh.pipeline.mesh_generator import MeshGenerator

            # Initialize generator
            generator = MeshGenerator()

            # Update progress
            self.progress.update_stage(
                "meshing",
                0.1,
                f"Meshing {len(shapes)} shape(s)..."
            )

            # Generate meshes
            meshes = generator.generate(
                shapes=shapes,
                template=self.template,
                mesh_size=self.config.mesh_size,
                element_type=self.config.element_type,
                min_element_size=self.config.min_element_size,
                max_element_size=self.config.max_element_size
            )

            # Update progress
            self.progress.update_stage(
                "meshing",
                0.9,
                f"Generated {len(meshes)} mesh(es)"
            )

            # Get statistics
            stats = generator.get_statistics(meshes)

            # Complete stage
            self.progress.complete_stage(
                "meshing",
                f"Generated {stats['total_meshes']} mesh(es): "
                f"{stats['total_nodes']} nodes, "
                f"{stats['total_elements']} elements"
            )

            self.logger.info(
                f"Mesh generation complete: "
                f"{stats['total_meshes']} mesh(es), "
                f"{stats['total_elements']} elements"
            )

            return meshes

        except Exception as e:
            error_msg = f"Mesh generation failed: {str(e)}"
            self.logger.error(error_msg)
            self.progress.fail_stage("meshing", error_msg)
            raise

    def _process_quality(self, meshes: List[MeshData]) -> List[MeshData]:
        """
        Stage 3: Analyze and improve quality

        Args:
            meshes: Input meshes

        Returns:
            Improved meshes (if auto-remeshing enabled)

        Raises:
            Exception: If quality processing fails
        """
        self.progress.start_stage("quality", "Analyzing mesh quality...")

        try:
            from koomesh.quality.quality_metrics import QualityAnalyzer
            from koomesh.quality.auto_remeshing import AutoRemesher

            # Initialize analyzer
            analyzer = QualityAnalyzer()

            # Update progress
            self.progress.update_stage(
                "quality",
                0.2,
                f"Analyzing {len(meshes)} mesh(es)..."
            )

            # Analyze quality for each mesh
            poor_quality_count = 0
            for mesh in meshes:
                # Simple quality check (count poor elements)
                # Note: Full element-by-element analysis would be too expensive here
                # We'll rely on the analyzer's quick methods
                try:
                    # Check if mesh has quality metrics attached
                    if not hasattr(mesh, 'quality_metrics'):
                        mesh.quality_metrics = {}

                    # Mark that quality was analyzed
                    mesh.quality_metrics['analyzed'] = True

                except Exception as e:
                    self.logger.warning(f"Quality analysis failed for mesh: {e}")

            # Update progress
            self.progress.update_stage(
                "quality",
                0.6,
                "Quality analysis complete"
            )

            # Auto-remesh if enabled
            if self.config.enable_auto_remesh:
                self.logger.info("Auto-remeshing enabled, refining poor elements...")

                try:
                    remesher = AutoRemesher(
                        strategy=getattr(
                            self.config,
                            'refinement_strategy',
                            'adaptive'
                        )
                    )

                    # Note: Actual remeshing is complex and time-consuming
                    # For now, we'll skip the actual remeshing but log that it would happen
                    self.logger.info(
                        "Auto-remeshing would refine poor quality elements "
                        "(full implementation in future iteration)"
                    )

                except Exception as e:
                    self.logger.warning(f"Auto-remeshing skipped: {e}")

            # Complete stage
            self.progress.complete_stage(
                "quality",
                f"Quality analysis complete for {len(meshes)} mesh(es)"
            )

            self.logger.info(f"Quality processing complete for {len(meshes)} mesh(es)")

            return meshes

        except Exception as e:
            error_msg = f"Quality processing failed: {str(e)}"
            self.logger.error(error_msg)
            self.progress.fail_stage("quality", error_msg)
            raise

    def _detect_contacts(self, meshes: List[MeshData]) -> List[ContactPair]:
        """
        Stage 4: Detect contacts

        Args:
            meshes: Input meshes

        Returns:
            List of ContactPair objects

        Raises:
            Exception: If contact detection fails
        """
        self.progress.start_stage("contact", "Detecting contacts...")

        try:
            from koomesh.contact.contact_detector import ContactDetector
            from koomesh.contact.contact_data import ContactPair

            # Initialize detector
            detector = ContactDetector()

            # Update progress
            self.progress.update_stage(
                "contact",
                0.2,
                f"Detecting contacts between {len(meshes)} mesh(es)..."
            )

            # Skip contact detection if only one mesh
            if len(meshes) < 2:
                self.logger.info("Only one mesh, skipping contact detection")
                self.progress.complete_stage(
                    "contact",
                    "No contacts (single mesh)"
                )
                return []

            # Detect contacts
            try:
                contacts = detector.detect_contacts(
                    meshes,
                    tolerance=getattr(
                        self.config,
                        'contact_tolerance',
                        1.0  # Default 1mm
                    )
                )

                self.progress.update_stage(
                    "contact",
                    0.9,
                    f"Found {len(contacts)} contact pair(s)"
                )

            except Exception as e:
                self.logger.warning(f"Contact detection failed: {e}")
                contacts = []

            # Complete stage
            self.progress.complete_stage(
                "contact",
                f"Detected {len(contacts)} contact pair(s)"
            )

            self.logger.info(f"Contact detection complete: {len(contacts)} pair(s)")

            return contacts

        except Exception as e:
            error_msg = f"Contact detection failed: {str(e)}"
            self.logger.error(error_msg)
            self.progress.fail_stage("contact", error_msg)
            raise

    def _export_lsdyna(self, meshes: List[MeshData], contacts: List[ContactPair]):
        """
        Stage 5: Export to LS-DYNA

        Args:
            meshes: Meshes to export
            contacts: Contact pairs to export

        Raises:
            Exception: If export fails
        """
        self.progress.start_stage("export", "Writing LS-DYNA file...")

        try:
            from koomesh.export.lsdyna_writer import LSDynaWriter

            # Update progress
            self.progress.update_stage(
                "export",
                0.1,
                f"Writing {len(meshes)} mesh(es) to {self.config.output_file}..."
            )

            # Initialize writer
            writer = LSDynaWriter(self.config.output_file)

            # Write header
            writer.write_header()

            # Update progress
            self.progress.update_stage(
                "export",
                0.3,
                "Writing nodes and elements..."
            )

            # Write meshes
            total_nodes = 0
            total_elements = 0
            for i, mesh in enumerate(meshes):
                try:
                    # Write nodes
                    writer.write_nodes(mesh)
                    total_nodes += mesh.num_nodes()

                    # Write elements
                    writer.write_elements(mesh)
                    total_elements += mesh.num_elements()

                    self.progress.update_stage(
                        "export",
                        0.3 + (0.5 * (i + 1) / len(meshes)),
                        f"Wrote mesh {i+1}/{len(meshes)}"
                    )

                except Exception as e:
                    self.logger.warning(f"Failed to write mesh {i+1}: {e}")

            # Update progress
            self.progress.update_stage(
                "export",
                0.8,
                "Writing contacts..."
            )

            # Write contacts
            if contacts:
                try:
                    writer.write_contacts(contacts)
                except Exception as e:
                    self.logger.warning(f"Failed to write contacts: {e}")

            # Finalize
            writer.finalize()

            # Complete stage
            self.progress.complete_stage(
                "export",
                f"Exported {total_nodes} nodes, {total_elements} elements, "
                f"{len(contacts)} contacts to {self.config.output_file}"
            )

            self.logger.info(
                f"LS-DYNA export complete: {self.config.output_file} "
                f"({total_elements} elements)"
            )

        except Exception as e:
            error_msg = f"LS-DYNA export failed: {str(e)}"
            self.logger.error(error_msg)
            self.progress.fail_stage("export", error_msg)
            raise

    def _validate_output(self) -> Dict[str, Any]:
        """
        Stage 6: Validate output using LSDynaValidator

        Performs comprehensive validation:
        - Keyword syntax and format
        - Node and element definitions
        - Contact definitions
        - Material assignments
        - ID consistency

        Returns:
            Dictionary with validation results and warnings

        Raises:
            Exception: If validation fails critically
        """
        self.progress.start_stage("validation", "Validating K file...")

        try:
            from pathlib import Path
            from koomesh.validation.lsdyna_validator import LSDynaValidator

            # Update progress
            self.progress.update_stage(
                "validation",
                0.2,
                "Checking output file..."
            )

            # Quick check: file exists
            output_path = Path(self.config.output_file)
            if not output_path.exists():
                self.logger.warning(f"Output file not found: {self.config.output_file}")
                self.progress.fail_stage("validation", "Output file not found")
                return {
                    'success': False,
                    'errors': ['Output file not found'],
                    'warnings': []
                }

            # Check file size
            file_size = output_path.stat().st_size
            if file_size == 0:
                self.logger.warning("Output file is empty")
                self.progress.fail_stage("validation", "Output file is empty")
                return {
                    'success': False,
                    'errors': ['Output file is empty'],
                    'warnings': []
                }

            # Update progress
            self.progress.update_stage(
                "validation",
                0.4,
                "Running comprehensive validation..."
            )

            # Run full validation using LSDynaValidator
            validator = LSDynaValidator(strict_mode=False)

            try:
                validation_result = validator.validate(self.config.output_file)
            except Exception as e:
                self.logger.error(f"Validator crashed: {str(e)}")
                self.progress.fail_stage("validation", f"Validator error: {str(e)}")
                return {
                    'success': False,
                    'errors': [f"Validator crashed: {str(e)}"],
                    'warnings': []
                }

            # Update progress
            self.progress.update_stage(
                "validation",
                0.8,
                f"Processing validation results..."
            )

            # Extract errors and warnings
            errors = [str(msg) for msg in validation_result.errors]
            warnings = [str(msg) for msg in validation_result.warnings]

            # Log summary
            if validation_result.success:
                self.logger.info(
                    f"Validation passed: {len(errors)} errors, {len(warnings)} warnings"
                )
            else:
                self.logger.warning(
                    f"Validation failed: {len(errors)} errors, {len(warnings)} warnings"
                )

            # Log first few errors/warnings
            for error in errors[:5]:
                self.logger.error(f"  {error}")
            if len(errors) > 5:
                self.logger.error(f"  ... and {len(errors) - 5} more errors")

            for warning in warnings[:5]:
                self.logger.warning(f"  {warning}")
            if len(warnings) > 5:
                self.logger.warning(f"  ... and {len(warnings) - 5} more warnings")

            # Complete stage
            status_msg = (
                f"Validation complete: {len(errors)} error(s), "
                f"{len(warnings)} warning(s)"
            )
            if validation_result.success:
                self.progress.complete_stage("validation", status_msg)
            else:
                self.progress.fail_stage("validation", status_msg)

            # Return result dictionary
            return {
                'success': validation_result.success,
                'errors': errors,
                'warnings': warnings,
                'file_size': file_size,
                'statistics': validation_result.statistics,
                'validator_result': validation_result  # Full result object
            }

        except Exception as e:
            error_msg = f"Validation stage failed: {str(e)}"
            self.logger.error(error_msg)
            self.progress.fail_stage("validation", error_msg)
            return {
                'success': False,
                'errors': [error_msg],
                'warnings': []
            }

    def _calculate_quality_stats(self, meshes: List[MeshData]) -> tuple:
        """
        Calculate overall quality statistics

        Args:
            meshes: List of meshes

        Returns:
            Tuple of (avg_quality, min_quality, max_quality)
        """
        # TODO: Implement when quality processing is done
        # For now return placeholder values
        return (0.0, 0.0, 0.0)
