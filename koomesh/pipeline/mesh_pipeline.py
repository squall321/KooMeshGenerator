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
        """
        self.progress.start_stage("quality", "Analyzing mesh quality...")
        # TODO: Implement in Day 5-7
        raise NotImplementedError(
            "Quality processing to be implemented on Day 5-7.\n"
            "This will include:\n"
            "  - Quality metric calculation\n"
            "  - Auto-remeshing for poor elements\n"
            "  - Quality reporting"
        )

    def _detect_contacts(self, meshes: List[MeshData]) -> List[ContactPair]:
        """
        Stage 4: Detect contacts

        Args:
            meshes: Input meshes

        Returns:
            List of ContactPair objects
        """
        self.progress.start_stage("contact", "Detecting contacts...")
        # TODO: Implement in Day 5-7
        raise NotImplementedError(
            "Contact detection to be implemented on Day 5-7.\n"
            "This will include:\n"
            "  - Multi-body contact detection\n"
            "  - Self-contact detection (if enabled)\n"
            "  - Contact pair optimization"
        )

    def _export_lsdyna(self, meshes: List[MeshData], contacts: List[ContactPair]):
        """
        Stage 5: Export to LS-DYNA

        Args:
            meshes: Meshes to export
            contacts: Contact pairs to export
        """
        self.progress.start_stage("export", "Writing LS-DYNA file...")
        # TODO: Implement in Day 5-7
        raise NotImplementedError(
            "LS-DYNA export to be implemented on Day 5-7.\n"
            "This will include:\n"
            "  - K file writing\n"
            "  - Material card generation\n"
            "  - Contact definition writing"
        )

    def _validate_output(self) -> Dict[str, Any]:
        """
        Stage 6: Validate output

        Returns:
            Dictionary with validation results and warnings
        """
        self.progress.start_stage("validation", "Validating K file...")
        # TODO: Implement in Week 2 (Day 11-13)
        # For now, just return empty result
        self.progress.complete_stage("validation", "Validation not yet implemented")
        return {'warnings': ['Validation not yet implemented']}

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
