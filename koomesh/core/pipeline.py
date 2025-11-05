"""
KooMesh Pipeline
================

This module provides the main pipeline for automated mesh generation from STEP files.

The pipeline orchestrates:
1. STEP file reading and validation
2. Hierarchy parsing and analysis
3. Shape classification (hex vs tet)
4. Mesh generation with quality control
5. Contact detection and rule application
6. LS-DYNA export

Features:
- Progress tracking with callbacks
- Error recovery and validation
- Statistics collection
- Batch processing support

Usage:
    >>> from koomesh.core.pipeline import MeshPipeline
    >>> pipeline = MeshPipeline()
    >>> result = pipeline.run('model.step', 'output.k', mesh_size=1.0)
"""

import logging
import time
from pathlib import Path
from typing import Optional, List, Dict, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

try:
    from OCC.Core.TopoDS import TopoDS_Shape
    PYTHONOCC_AVAILABLE = True
except ImportError:
    PYTHONOCC_AVAILABLE = False
    TopoDS_Shape = object

from koomesh.config import KooMeshConfig
from koomesh.io.step_reader import STEPReader, STEPReaderError
from koomesh.io.hierarchy_parser import HierarchyParser, HierarchyNode
from koomesh.geometry.shape_classifier import ShapeClassifier, MeshType
from koomesh.meshing.mesh_data import MeshData, ElementType
from koomesh.meshing.hex_mesher import HexMesher
from koomesh.meshing.tet_mesher import TetMesher
from koomesh.meshing.quality_checker import QualityChecker, QualityReport
from koomesh.contact.contact_detector import ContactDetector
from koomesh.contact.contact_data import ContactPair, ContactManager
from koomesh.contact.hierarchy_rules import HierarchyRules
from koomesh.export.lsdyna_writer import LSDynaWriter


class PipelineStage(Enum):
    """Pipeline execution stages"""
    INITIALIZATION = "initialization"
    STEP_READING = "step_reading"
    HIERARCHY_PARSING = "hierarchy_parsing"
    SHAPE_CLASSIFICATION = "shape_classification"
    MESH_GENERATION = "mesh_generation"
    QUALITY_CHECK = "quality_check"
    CONTACT_DETECTION = "contact_detection"
    CONTACT_RULES = "contact_rules"
    EXPORT = "export"
    FINALIZATION = "finalization"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PipelineProgress:
    """
    Pipeline progress tracking

    Attributes:
        stage: Current pipeline stage
        progress: Progress percentage (0-100)
        message: Status message
        start_time: Pipeline start time
        current_time: Current time
        elapsed_seconds: Elapsed time in seconds
        estimated_remaining: Estimated remaining time (seconds)
    """
    stage: PipelineStage
    progress: float = 0.0
    message: str = ""
    start_time: float = field(default_factory=time.time)
    current_time: float = field(default_factory=time.time)

    @property
    def elapsed_seconds(self) -> float:
        """Get elapsed time in seconds"""
        return self.current_time - self.start_time

    @property
    def estimated_remaining(self) -> Optional[float]:
        """Estimate remaining time based on current progress"""
        if self.progress > 0:
            total_estimated = self.elapsed_seconds / (self.progress / 100.0)
            return total_estimated - self.elapsed_seconds
        return None

    def format_time(self, seconds: float) -> str:
        """Format time in human-readable format"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}h {minutes}m"


@dataclass
class PipelineResult:
    """
    Pipeline execution result

    Attributes:
        success: Whether pipeline completed successfully
        output_path: Path to output file
        meshes: Generated meshes
        contacts: Detected contacts
        hierarchy: Hierarchy tree
        statistics: Execution statistics
        errors: List of errors encountered
        warnings: List of warnings
        quality_report: Mesh quality report
        execution_time: Total execution time (seconds)
    """
    success: bool
    output_path: Optional[Path] = None
    meshes: List[MeshData] = field(default_factory=list)
    contacts: List[ContactPair] = field(default_factory=list)
    hierarchy: Optional[HierarchyNode] = None
    statistics: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    quality_report: Optional[QualityReport] = None
    execution_time: float = 0.0

    def print_summary(self):
        """Print pipeline result summary"""
        print("\n" + "=" * 70)
        print("KOOMESH PIPELINE RESULT")
        print("=" * 70)

        status = "✓ SUCCESS" if self.success else "✗ FAILED"
        print(f"Status: {status}")
        print(f"Execution Time: {self.execution_time:.2f}s")

        if self.output_path:
            print(f"Output: {self.output_path}")

        print(f"\nMeshes Generated: {len(self.meshes)}")
        total_nodes = sum(m.num_nodes() for m in self.meshes)
        total_elements = sum(m.num_elements() for m in self.meshes)
        print(f"  Total Nodes: {total_nodes:,}")
        print(f"  Total Elements: {total_elements:,}")

        print(f"\nContacts Detected: {len(self.contacts)}")

        if self.quality_report:
            print(f"\nMesh Quality:")
            print(f"  Min Jacobian: {self.quality_report.min_jacobian:.6f}")
            print(f"  Avg Jacobian: {self.quality_report.avg_jacobian:.6f}")
            print(f"  Failed Elements: {self.quality_report.num_failed}")

        if self.warnings:
            print(f"\nWarnings: {len(self.warnings)}")
            for warn in self.warnings[:5]:
                print(f"  ⚠ {warn}")

        if self.errors:
            print(f"\nErrors: {len(self.errors)}")
            for err in self.errors[:5]:
                print(f"  ✗ {err}")

        print("=" * 70 + "\n")


class MeshPipeline:
    """
    Main mesh generation pipeline

    Orchestrates the complete workflow from STEP file to LS-DYNA output.

    Attributes:
        config: KooMesh configuration
        logger: Logger instance
        progress_callback: Optional callback for progress updates

    Example:
        >>> pipeline = MeshPipeline()
        >>> result = pipeline.run(
        ...     step_file='model.step',
        ...     output_file='output.k',
        ...     mesh_size=1.0,
        ...     hex_priority=True
        ... )
        >>> result.print_summary()
    """

    def __init__(self,
                 config: Optional[KooMeshConfig] = None,
                 progress_callback: Optional[Callable[[PipelineProgress], None]] = None):
        """
        Initialize mesh pipeline

        Args:
            config: Pipeline configuration
            progress_callback: Optional callback for progress updates
        """
        self.config = config or KooMeshConfig()
        self.logger = logging.getLogger(__name__)
        self.progress_callback = progress_callback

        # Initialize components
        self.step_reader = STEPReader()
        self.hierarchy_parser = HierarchyParser()
        self.shape_classifier = ShapeClassifier()
        self.quality_checker = QualityChecker()
        self.contact_detector = ContactDetector(tolerance=self.config.contact.tolerance)
        self.hierarchy_rules = HierarchyRules()
        self.contact_manager = ContactManager()

        # Pipeline state
        self.current_progress = PipelineProgress(stage=PipelineStage.INITIALIZATION)
        self.start_time = None

    def run(self,
            step_file: str,
            output_file: str,
            mesh_size: Optional[float] = None,
            hex_priority: Optional[bool] = None,
            validate_quality: bool = True) -> PipelineResult:
        """
        Run complete mesh generation pipeline

        Args:
            step_file: Input STEP file path
            output_file: Output LS-DYNA file path
            mesh_size: Mesh element size (uses config default if not specified)
            hex_priority: Prioritize hexahedral meshing (uses config default if not specified)
            validate_quality: Validate mesh quality

        Returns:
            PipelineResult with execution results

        Example:
            >>> result = pipeline.run('model.step', 'output.k', mesh_size=1.0)
        """
        self.start_time = time.time()
        result = PipelineResult(success=False)

        # Apply overrides
        if mesh_size is not None:
            self.config.mesh.default_size = mesh_size
        if hex_priority is not None:
            self.config.mesh.hex_priority = hex_priority

        try:
            self.logger.info("=" * 70)
            self.logger.info("KOOMESH PIPELINE STARTED")
            self.logger.info("=" * 70)
            self.logger.info(f"Input: {step_file}")
            self.logger.info(f"Output: {output_file}")
            self.logger.info(f"Mesh size: {self.config.mesh.default_size}")
            self.logger.info(f"Hex priority: {self.config.mesh.hex_priority}")

            # Stage 1: Read STEP file
            self._update_progress(PipelineStage.STEP_READING, 10, "Reading STEP file...")
            shapes, hierarchy = self._read_step_file(step_file)
            result.hierarchy = hierarchy

            # Stage 2: Parse hierarchy
            self._update_progress(PipelineStage.HIERARCHY_PARSING, 20, "Parsing hierarchy...")
            if hierarchy is None:
                hierarchy = self._parse_hierarchy(shapes)
                result.hierarchy = hierarchy

            # Stage 3: Classify shapes
            self._update_progress(PipelineStage.SHAPE_CLASSIFICATION, 30, "Classifying shapes...")
            classifications = self._classify_shapes(shapes)

            # Stage 4: Generate meshes
            self._update_progress(PipelineStage.MESH_GENERATION, 40, "Generating meshes...")
            meshes = self._generate_meshes(shapes, classifications)
            result.meshes = meshes

            # Stage 5: Quality check
            if validate_quality:
                self._update_progress(PipelineStage.QUALITY_CHECK, 60, "Checking mesh quality...")
                quality_report = self._check_quality(meshes)
                result.quality_report = quality_report

                # Add warnings for quality issues
                if quality_report.num_failed > 0:
                    result.warnings.append(
                        f"{quality_report.num_failed} elements failed quality check"
                    )

            # Stage 6: Detect contacts
            self._update_progress(PipelineStage.CONTACT_DETECTION, 70, "Detecting contacts...")
            contacts = self._detect_contacts(meshes, hierarchy)

            # Stage 7: Apply hierarchy rules
            self._update_progress(PipelineStage.CONTACT_RULES, 80, "Applying contact rules...")
            self._apply_contact_rules(contacts, hierarchy)
            result.contacts = contacts

            # Stage 8: Export to LS-DYNA
            self._update_progress(PipelineStage.EXPORT, 90, "Exporting to LS-DYNA...")
            output_path = self._export_lsdyna(meshes, contacts, hierarchy, output_file)
            result.output_path = output_path

            # Finalize
            self._update_progress(PipelineStage.FINALIZATION, 95, "Finalizing...")
            result.statistics = self._collect_statistics(meshes, contacts, hierarchy)

            # Success
            result.success = True
            result.execution_time = time.time() - self.start_time

            self._update_progress(PipelineStage.COMPLETED, 100, "Pipeline completed successfully")

            self.logger.info("=" * 70)
            self.logger.info("PIPELINE COMPLETED SUCCESSFULLY")
            self.logger.info(f"Execution time: {result.execution_time:.2f}s")
            self.logger.info("=" * 70)

        except Exception as e:
            result.success = False
            result.execution_time = time.time() - self.start_time
            error_msg = f"Pipeline failed: {str(e)}"
            result.errors.append(error_msg)

            self._update_progress(PipelineStage.FAILED, 0, error_msg)

            self.logger.error("=" * 70)
            self.logger.error("PIPELINE FAILED")
            self.logger.error(f"Error: {error_msg}")
            self.logger.error("=" * 70)
            self.logger.exception(e)

        return result

    def _read_step_file(self, filepath: str) -> tuple[List[TopoDS_Shape], Optional[HierarchyNode]]:
        """Read STEP file and extract shapes"""
        self.logger.info(f"Reading STEP file: {filepath}")

        # Try reading with hierarchy (XDE)
        try:
            hierarchy = self.hierarchy_parser.parse_step_file(filepath)
            shapes = []

            # Extract shapes from hierarchy
            def collect_shapes(node: HierarchyNode):
                if node.shape is not None:
                    shapes.append(node.shape)
                for child in node.children:
                    collect_shapes(child)

            collect_shapes(hierarchy)

            self.logger.info(f"Read {len(shapes)} shapes with hierarchy")
            return shapes, hierarchy

        except Exception as e:
            self.logger.warning(f"Failed to read with hierarchy: {e}")

            # Fallback to simple reading
            shape = self.step_reader.read_file(filepath)
            self.logger.info("Read STEP file as single shape")
            return [shape], None

    def _parse_hierarchy(self, shapes: List[TopoDS_Shape]) -> HierarchyNode:
        """Create hierarchy from shapes"""
        self.logger.info("Creating hierarchy from shapes")

        # Create simple flat hierarchy
        root = HierarchyNode(name="Assembly", level=0)

        for i, shape in enumerate(shapes):
            child = HierarchyNode(
                name=f"Part{i+1}",
                shape=shape,
                parent=root,
                level=1
            )
            root.children.append(child)

        self.logger.info(f"Created hierarchy with {len(shapes)} parts")
        return root

    def _classify_shapes(self, shapes: List[TopoDS_Shape]) -> List[Dict]:
        """Classify shapes for mesh type determination"""
        self.logger.info(f"Classifying {len(shapes)} shapes...")

        classifications = []
        for i, shape in enumerate(shapes):
            result = self.shape_classifier.classify(shape)
            classifications.append({
                'index': i,
                'shape': shape,
                'result': result
            })

            self.logger.debug(
                f"Shape {i+1}: {result.shape_type.value}, "
                f"mesh_type={result.mesh_type.value}, "
                f"confidence={result.confidence:.2f}"
            )

        return classifications

    def _generate_meshes(self, shapes: List[TopoDS_Shape],
                         classifications: List[Dict]) -> List[MeshData]:
        """Generate meshes for all shapes"""
        self.logger.info(f"Generating meshes for {len(shapes)} shapes...")

        meshes = []
        hex_mesher = HexMesher(mesh_size=self.config.mesh.default_size)
        tet_mesher = TetMesher(
            mesh_size=self.config.mesh.default_size,
            algorithm=self.config.mesh.tet_algorithm
        )

        for i, classification in enumerate(classifications):
            shape = classification['shape']
            result = classification['result']

            self.logger.info(f"Meshing shape {i+1}/{len(shapes)}...")

            try:
                # Determine mesher based on classification and priority
                use_hex = (result.mesh_type == MeshType.HEXAHEDRAL and
                          self.config.mesh.hex_enabled)

                if self.config.mesh.hex_priority and result.mesh_type != MeshType.TETRAHEDRAL:
                    use_hex = True

                # Generate mesh
                if use_hex:
                    self.logger.info("  Using hexahedral mesher")
                    mesh = hex_mesher.mesh_shape(shape, shape_type=result.shape_type.value)
                else:
                    self.logger.info("  Using tetrahedral mesher")
                    mesh = tet_mesher.mesh_shape(shape)

                meshes.append(mesh)

                self.logger.info(
                    f"  Generated: {mesh.num_nodes()} nodes, "
                    f"{mesh.num_elements()} elements ({mesh.element_type.code})"
                )

            except Exception as e:
                self.logger.error(f"Failed to mesh shape {i+1}: {e}")

                # Try fallback to tetrahedral
                if use_hex:
                    self.logger.info("  Falling back to tetrahedral mesher")
                    try:
                        mesh = tet_mesher.mesh_shape(shape)
                        meshes.append(mesh)
                        self.logger.info(
                            f"  Generated (fallback): {mesh.num_nodes()} nodes, "
                            f"{mesh.num_elements()} elements"
                        )
                    except Exception as e2:
                        self.logger.error(f"Fallback meshing also failed: {e2}")
                        raise
                else:
                    raise

        total_nodes = sum(m.num_nodes() for m in meshes)
        total_elements = sum(m.num_elements() for m in meshes)
        self.logger.info(
            f"Mesh generation complete: {total_nodes:,} nodes, {total_elements:,} elements"
        )

        return meshes

    def _check_quality(self, meshes: List[MeshData]) -> QualityReport:
        """Check mesh quality for all meshes"""
        self.logger.info("Checking mesh quality...")

        # Combine reports from all meshes
        all_reports = []
        for i, mesh in enumerate(meshes):
            report = self.quality_checker.check_mesh(mesh)
            all_reports.append(report)

            self.logger.info(
                f"Mesh {i+1}: min_jacobian={report.min_jacobian:.6f}, "
                f"failed={report.num_failed}/{mesh.num_elements()}"
            )

        # Create combined report (using first mesh as base)
        if all_reports:
            combined = all_reports[0]
            for report in all_reports[1:]:
                combined.num_failed += report.num_failed
            return combined

        return QualityReport()

    def _detect_contacts(self, meshes: List[MeshData],
                         hierarchy: HierarchyNode) -> List[ContactPair]:
        """Detect contacts between meshes"""
        self.logger.info(f"Detecting contacts between {len(meshes)} meshes...")

        contacts = self.contact_detector.detect_contacts(
            meshes, hierarchy, self.contact_manager
        )

        self.logger.info(f"Detected {len(contacts)} contact pairs")
        return contacts

    def _apply_contact_rules(self, contacts: List[ContactPair],
                             hierarchy: HierarchyNode):
        """Apply hierarchy-based contact rules"""
        self.logger.info(f"Applying hierarchy rules to {len(contacts)} contacts...")

        # Get flattened hierarchy nodes
        nodes = self._flatten_hierarchy(hierarchy)

        for contact in contacts:
            # Find corresponding hierarchy nodes
            node1 = self._find_node_by_name(nodes, contact.master_surface.part_name)
            node2 = self._find_node_by_name(nodes, contact.slave_surface.part_name)

            if node1 and node2:
                self.hierarchy_rules.apply_rules_to_contact(contact, node1, node2)
                self.logger.debug(
                    f"Applied rules: {contact.master_surface.part_name} <-> "
                    f"{contact.slave_surface.part_name} → {contact.contact_type.value}"
                )

    def _flatten_hierarchy(self, root: HierarchyNode) -> List[HierarchyNode]:
        """Flatten hierarchy to list"""
        result = [root]
        for child in root.children:
            result.extend(self._flatten_hierarchy(child))
        return result

    def _find_node_by_name(self, nodes: List[HierarchyNode], name: str) -> Optional[HierarchyNode]:
        """Find hierarchy node by name"""
        for node in nodes:
            if node.name == name:
                return node
        return None

    def _export_lsdyna(self, meshes: List[MeshData],
                       contacts: List[ContactPair],
                       hierarchy: HierarchyNode,
                       output_file: str) -> Path:
        """Export to LS-DYNA format"""
        self.logger.info(f"Exporting to LS-DYNA: {output_file}")

        with LSDynaWriter(output_file, precision=self.config.export.precision) as writer:
            writer.write_complete_model(meshes, contacts, hierarchy)

        output_path = Path(output_file)
        file_size = output_path.stat().st_size / (1024 * 1024)  # MB
        self.logger.info(f"Export complete: {output_path} ({file_size:.2f} MB)")

        return output_path

    def _collect_statistics(self, meshes: List[MeshData],
                            contacts: List[ContactPair],
                            hierarchy: HierarchyNode) -> Dict[str, Any]:
        """Collect pipeline statistics"""
        stats = {
            'num_meshes': len(meshes),
            'total_nodes': sum(m.num_nodes() for m in meshes),
            'total_elements': sum(m.num_elements() for m in meshes),
            'num_contacts': len(contacts),
            'num_parts': len(self._flatten_hierarchy(hierarchy)),
            'timestamp': datetime.now().isoformat()
        }

        # Element type breakdown
        element_types = {}
        for mesh in meshes:
            elem_type = mesh.element_type.code
            element_types[elem_type] = element_types.get(elem_type, 0) + mesh.num_elements()
        stats['element_types'] = element_types

        # Contact type breakdown
        contact_types = {}
        for contact in contacts:
            ctype = contact.contact_type.value
            contact_types[ctype] = contact_types.get(ctype, 0) + 1
        stats['contact_types'] = contact_types

        return stats

    def _update_progress(self, stage: PipelineStage, progress: float, message: str):
        """Update pipeline progress"""
        self.current_progress.stage = stage
        self.current_progress.progress = progress
        self.current_progress.message = message
        self.current_progress.current_time = time.time()

        # Call progress callback if provided
        if self.progress_callback:
            self.progress_callback(self.current_progress)

        # Log progress
        elapsed = self.current_progress.elapsed_seconds
        remaining = self.current_progress.estimated_remaining

        if remaining:
            self.logger.info(
                f"[{progress:3.0f}%] {stage.value}: {message} "
                f"(elapsed: {self.current_progress.format_time(elapsed)}, "
                f"remaining: {self.current_progress.format_time(remaining)})"
            )
        else:
            self.logger.info(f"[{progress:3.0f}%] {stage.value}: {message}")
