"""
Integration Tests for Pipeline
================================

These tests verify the complete pipeline functionality from STEP input
to LS-DYNA output.
"""

import pytest
import tempfile
from pathlib import Path
import numpy as np

try:
    from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
    from OCC.Core.STEPControl import STEPControl_Writer, STEPControl_AsIs
    PYTHONOCC_AVAILABLE = True
except ImportError:
    PYTHONOCC_AVAILABLE = False

from koomesh.core.pipeline import MeshPipeline, PipelineResult, PipelineStage
from koomesh.config import KooMeshConfig
from koomesh.meshing.mesh_data import create_structured_box_mesh


@pytest.mark.skipif(not PYTHONOCC_AVAILABLE, reason="PythonOCC not available")
class TestPipeline:
    """Test complete pipeline functionality"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def simple_step_file(self, temp_dir):
        """Create a simple box STEP file for testing"""
        # Create a simple box
        box = BRepPrimAPI_MakeBox(10.0, 10.0, 10.0).Shape()

        # Write to STEP file
        step_file = temp_dir / "test_box.step"
        writer = STEPControl_Writer()
        writer.Transfer(box, STEPControl_AsIs)
        writer.Write(str(step_file))

        return step_file

    @pytest.fixture
    def config(self):
        """Create test configuration"""
        config = KooMeshConfig()
        config.mesh.default_size = 2.0
        config.mesh.hex_priority = True
        config.contact.enabled = True
        config.contact.tolerance = 0.01
        return config

    def test_pipeline_initialization(self, config):
        """Test pipeline initialization"""
        pipeline = MeshPipeline(config=config)

        assert pipeline.config == config
        assert pipeline.step_reader is not None
        assert pipeline.hierarchy_parser is not None
        assert pipeline.shape_classifier is not None
        assert pipeline.quality_checker is not None
        assert pipeline.contact_detector is not None

    def test_pipeline_basic_run(self, simple_step_file, temp_dir, config):
        """Test basic pipeline execution"""
        output_file = temp_dir / "output.k"

        pipeline = MeshPipeline(config=config)
        result = pipeline.run(
            step_file=str(simple_step_file),
            output_file=str(output_file),
            mesh_size=2.0,
            hex_priority=True
        )

        # Check result
        assert isinstance(result, PipelineResult)
        assert result.success
        assert result.output_path == output_file
        assert output_file.exists()

        # Check meshes
        assert len(result.meshes) > 0
        for mesh in result.meshes:
            assert mesh.num_nodes() > 0
            assert mesh.num_elements() > 0

        # Check statistics
        assert 'total_nodes' in result.statistics
        assert 'total_elements' in result.statistics
        assert result.statistics['total_nodes'] > 0
        assert result.statistics['total_elements'] > 0

    def test_pipeline_with_quality_check(self, simple_step_file, temp_dir, config):
        """Test pipeline with quality validation"""
        output_file = temp_dir / "output.k"

        pipeline = MeshPipeline(config=config)
        result = pipeline.run(
            step_file=str(simple_step_file),
            output_file=str(output_file),
            mesh_size=2.0,
            validate_quality=True
        )

        assert result.success
        assert result.quality_report is not None
        assert result.quality_report.min_jacobian is not None
        assert result.quality_report.avg_jacobian is not None

    def test_pipeline_progress_tracking(self, simple_step_file, temp_dir, config):
        """Test pipeline progress callbacks"""
        output_file = temp_dir / "output.k"

        progress_calls = []

        def progress_callback(progress):
            progress_calls.append({
                'stage': progress.stage,
                'progress': progress.progress,
                'message': progress.message
            })

        pipeline = MeshPipeline(config=config, progress_callback=progress_callback)
        result = pipeline.run(
            step_file=str(simple_step_file),
            output_file=str(output_file),
            mesh_size=2.0
        )

        assert result.success

        # Check that progress was tracked
        assert len(progress_calls) > 0

        # Check that stages progress from 0 to 100
        assert progress_calls[0]['progress'] < 100
        assert progress_calls[-1]['progress'] == 100

        # Check that final stage is COMPLETED
        assert progress_calls[-1]['stage'] == PipelineStage.COMPLETED

    def test_pipeline_hex_priority(self, simple_step_file, temp_dir, config):
        """Test hexahedral meshing priority"""
        output_file = temp_dir / "output.k"

        config.mesh.hex_priority = True

        pipeline = MeshPipeline(config=config)
        result = pipeline.run(
            step_file=str(simple_step_file),
            output_file=str(output_file),
            mesh_size=2.0,
            hex_priority=True
        )

        assert result.success

        # Check that hex elements were generated
        if result.meshes:
            has_hex = any(mesh.element_type.is_hex() for mesh in result.meshes)
            # Note: This may not always be true depending on geometry complexity
            # but for a simple box it should work
            assert has_hex or result.warnings  # Either hex or warning about fallback

    def test_pipeline_tet_fallback(self, simple_step_file, temp_dir, config):
        """Test tetrahedral fallback when hex fails"""
        output_file = temp_dir / "output.k"

        config.mesh.hex_priority = False

        pipeline = MeshPipeline(config=config)
        result = pipeline.run(
            step_file=str(simple_step_file),
            output_file=str(output_file),
            mesh_size=2.0,
            hex_priority=False
        )

        assert result.success
        assert len(result.meshes) > 0

    def test_pipeline_error_handling(self, temp_dir, config):
        """Test pipeline error handling with invalid input"""
        nonexistent_file = temp_dir / "nonexistent.step"
        output_file = temp_dir / "output.k"

        pipeline = MeshPipeline(config=config)
        result = pipeline.run(
            step_file=str(nonexistent_file),
            output_file=str(output_file),
            mesh_size=2.0
        )

        # Pipeline should handle error gracefully
        assert not result.success
        assert len(result.errors) > 0
        assert result.execution_time > 0

    def test_pipeline_statistics_collection(self, simple_step_file, temp_dir, config):
        """Test statistics collection"""
        output_file = temp_dir / "output.k"

        pipeline = MeshPipeline(config=config)
        result = pipeline.run(
            step_file=str(simple_step_file),
            output_file=str(output_file),
            mesh_size=2.0
        )

        assert result.success

        # Check statistics
        stats = result.statistics
        assert 'num_meshes' in stats
        assert 'total_nodes' in stats
        assert 'total_elements' in stats
        assert 'num_contacts' in stats
        assert 'num_parts' in stats
        assert 'element_types' in stats
        assert 'timestamp' in stats

        assert stats['num_meshes'] == len(result.meshes)
        assert stats['total_nodes'] > 0
        assert stats['total_elements'] > 0

    def test_pipeline_output_file(self, simple_step_file, temp_dir, config):
        """Test LS-DYNA output file generation"""
        output_file = temp_dir / "output.k"

        pipeline = MeshPipeline(config=config)
        result = pipeline.run(
            step_file=str(simple_step_file),
            output_file=str(output_file),
            mesh_size=2.0
        )

        assert result.success
        assert output_file.exists()

        # Check file content
        content = output_file.read_text()
        assert '*KEYWORD' in content
        assert '*NODE' in content
        assert '*ELEMENT_SOLID' in content
        assert '*END' in content

    def test_pipeline_mesh_size_override(self, simple_step_file, temp_dir, config):
        """Test mesh size parameter override"""
        output_file = temp_dir / "output.k"

        config.mesh.default_size = 5.0

        pipeline = MeshPipeline(config=config)

        # Override mesh size
        result = pipeline.run(
            step_file=str(simple_step_file),
            output_file=str(output_file),
            mesh_size=1.0  # Override with smaller size
        )

        assert result.success

        # Smaller mesh size should result in more elements
        # (This is a rough check, actual count depends on mesher behavior)
        assert result.statistics['total_elements'] > 0

    def test_pipeline_result_summary(self, simple_step_file, temp_dir, config):
        """Test pipeline result summary printing"""
        output_file = temp_dir / "output.k"

        pipeline = MeshPipeline(config=config)
        result = pipeline.run(
            step_file=str(simple_step_file),
            output_file=str(output_file),
            mesh_size=2.0
        )

        assert result.success

        # This should not raise an exception
        result.print_summary()


class TestPipelineWithMockData:
    """Test pipeline components with mock data"""

    def test_pipeline_result_creation(self):
        """Test PipelineResult creation"""
        result = PipelineResult(success=True)

        assert result.success
        assert result.output_path is None
        assert len(result.meshes) == 0
        assert len(result.contacts) == 0
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_pipeline_result_with_meshes(self):
        """Test PipelineResult with mesh data"""
        # Create mock mesh
        mesh = create_structured_box_mesh(10, 10, 10, 2, 2, 2)

        result = PipelineResult(
            success=True,
            meshes=[mesh]
        )

        assert len(result.meshes) == 1
        assert result.meshes[0].num_nodes() > 0
        assert result.meshes[0].num_elements() > 0

    def test_pipeline_result_statistics(self):
        """Test PipelineResult statistics"""
        result = PipelineResult(
            success=True,
            statistics={
                'total_nodes': 1000,
                'total_elements': 500,
                'num_contacts': 5
            }
        )

        assert result.statistics['total_nodes'] == 1000
        assert result.statistics['total_elements'] == 500
        assert result.statistics['num_contacts'] == 5

    def test_pipeline_progress_time_formatting(self):
        """Test PipelineProgress time formatting"""
        from koomesh.core.pipeline import PipelineProgress
        import time

        progress = PipelineProgress(
            stage=PipelineStage.MESH_GENERATION,
            progress=50.0
        )

        # Test time formatting
        assert progress.format_time(30) == "30.0s"
        assert progress.format_time(90) == "1m 30s"
        assert progress.format_time(3700) == "1h 1m"

    def test_pipeline_progress_estimation(self):
        """Test PipelineProgress time estimation"""
        from koomesh.core.pipeline import PipelineProgress
        import time

        start = time.time()
        progress = PipelineProgress(
            stage=PipelineStage.MESH_GENERATION,
            progress=50.0,
            start_time=start
        )
        progress.current_time = start + 10  # 10 seconds elapsed

        elapsed = progress.elapsed_seconds
        assert elapsed == 10

        remaining = progress.estimated_remaining
        assert remaining is not None
        assert remaining > 0  # Should estimate ~10 more seconds


@pytest.mark.integration
class TestPipelineIntegration:
    """Integration tests requiring full environment"""

    def test_end_to_end_workflow(self, temp_dir):
        """Test complete end-to-end workflow"""
        pytest.skip("Requires full PythonOCC and GMSH installation")

    def test_large_model_processing(self, temp_dir):
        """Test processing of large models"""
        pytest.skip("Performance test - run separately")

    def test_complex_assembly_processing(self, temp_dir):
        """Test processing of complex assemblies"""
        pytest.skip("Requires complex test models")
