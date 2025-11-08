"""
Tests for MeshGenerationPipeline
"""

import pytest
from pathlib import Path
import tempfile

from koomesh.pipeline.mesh_pipeline import (
    MeshGenerationPipeline,
    PipelineConfig,
    PipelineResult
)


class TestPipelineConfig:
    """Test PipelineConfig dataclass"""

    def test_create_minimal_config(self, tmp_path):
        """Test creating minimal configuration"""
        # Create a temporary STEP file
        step_file = tmp_path / "test.step"
        step_file.write_text("ISO-10303-21;")

        config = PipelineConfig(
            input_files=[str(step_file)],
            output_file="output.k"
        )

        assert len(config.input_files) == 1
        assert config.output_file == "output.k"
        assert config.mesh_size == 5.0
        assert config.element_type == "tet4"
        assert config.enable_quality_check is True

    def test_create_full_config(self, tmp_path):
        """Test creating full configuration"""
        step_file = tmp_path / "test.step"
        step_file.write_text("ISO-10303-21;")

        config = PipelineConfig(
            input_files=[str(step_file)],
            output_file="output.k",
            template_name="automotive_crash_frontal",
            mesh_size=3.0,
            element_type="hex8",
            enable_quality_check=True,
            min_quality_threshold=0.4,
            enable_auto_remesh=True,
            max_remesh_iterations=5,
            enable_contact_detection=True,
            contact_tolerance=1.5,
            enable_validation=True,
            parallel=True
        )

        assert config.template_name == "automotive_crash_frontal"
        assert config.mesh_size == 3.0
        assert config.element_type == "hex8"
        assert config.max_remesh_iterations == 5

    def test_config_validation_file_not_found(self):
        """Test configuration validation for missing file"""
        with pytest.raises(FileNotFoundError, match="Input file not found"):
            PipelineConfig(
                input_files=["nonexistent.step"],
                output_file="output.k"
            )

    def test_config_validation_invalid_mesh_size(self, tmp_path):
        """Test configuration validation for invalid mesh size"""
        step_file = tmp_path / "test.step"
        step_file.write_text("ISO-10303-21;")

        with pytest.raises(ValueError, match="mesh_size must be positive"):
            PipelineConfig(
                input_files=[str(step_file)],
                output_file="output.k",
                mesh_size=-1.0
            )

    def test_config_validation_invalid_quality_threshold(self, tmp_path):
        """Test configuration validation for invalid quality threshold"""
        step_file = tmp_path / "test.step"
        step_file.write_text("ISO-10303-21;")

        with pytest.raises(ValueError, match="min_quality_threshold must be in"):
            PipelineConfig(
                input_files=[str(step_file)],
                output_file="output.k",
                min_quality_threshold=1.5
            )

    def test_config_multiple_input_files(self, tmp_path):
        """Test configuration with multiple input files"""
        files = []
        for i in range(3):
            step_file = tmp_path / f"test{i}.step"
            step_file.write_text("ISO-10303-21;")
            files.append(str(step_file))

        config = PipelineConfig(
            input_files=files,
            output_file="output.k"
        )

        assert len(config.input_files) == 3


class TestPipelineResult:
    """Test PipelineResult dataclass"""

    def test_create_success_result(self):
        """Test creating successful result"""
        result = PipelineResult(
            success=True,
            output_file="mesh.k",
            num_nodes=1000,
            num_elements=5000,
            num_contacts=3,
            avg_quality=0.85,
            min_quality=0.42,
            max_quality=0.98,
            execution_time=45.2
        )

        assert result.success is True
        assert result.num_nodes == 1000
        assert result.num_elements == 5000
        assert result.avg_quality == 0.85

    def test_create_failure_result(self):
        """Test creating failed result"""
        result = PipelineResult(
            success=False,
            output_file="mesh.k",
            num_nodes=0,
            num_elements=0,
            num_contacts=0,
            avg_quality=0.0,
            min_quality=0.0,
            max_quality=0.0,
            execution_time=5.0,
            errors=["STEP file read error", "Invalid geometry"]
        )

        assert result.success is False
        assert len(result.errors) == 2

    def test_result_with_warnings(self):
        """Test result with warnings"""
        result = PipelineResult(
            success=True,
            output_file="mesh.k",
            num_nodes=500,
            num_elements=2000,
            num_contacts=1,
            avg_quality=0.75,
            min_quality=0.28,
            max_quality=0.95,
            execution_time=30.0,
            warnings=["3 elements below quality threshold", "Self-contact not detected"]
        )

        assert result.success is True
        assert len(result.warnings) == 2

    def test_result_str_representation(self):
        """Test string representation of result"""
        result = PipelineResult(
            success=True,
            output_file="mesh.k",
            num_nodes=1000,
            num_elements=5000,
            num_contacts=2,
            avg_quality=0.85,
            min_quality=0.42,
            max_quality=0.98,
            execution_time=45.2
        )

        result_str = str(result)
        assert "SUCCESS" in result_str
        assert "mesh.k" in result_str
        assert "1,000" in result_str  # Formatted with commas
        assert "5,000" in result_str


class TestMeshGenerationPipeline:
    """Test MeshGenerationPipeline class"""

    def test_create_pipeline(self, tmp_path):
        """Test creating pipeline"""
        step_file = tmp_path / "test.step"
        step_file.write_text("ISO-10303-21;")

        config = PipelineConfig(
            input_files=[str(step_file)],
            output_file="output.k"
        )

        pipeline = MeshGenerationPipeline(config)

        assert pipeline.config == config
        assert pipeline.progress is not None
        assert pipeline.step_reader is not None
        assert pipeline.quality_analyzer is not None

    def test_create_pipeline_with_template(self, tmp_path):
        """Test creating pipeline with template"""
        step_file = tmp_path / "test.step"
        step_file.write_text("ISO-10303-21;")

        config = PipelineConfig(
            input_files=[str(step_file)],
            output_file="output.k",
            template_name="automotive_crash_frontal"
        )

        pipeline = MeshGenerationPipeline(config)

        # Template should be loaded (or None if not found)
        # Don't assert template exists as templates may not be available in test
        assert hasattr(pipeline, 'template')

    def test_progress_callback(self, tmp_path):
        """Test progress callback functionality"""
        step_file = tmp_path / "test.step"
        step_file.write_text("ISO-10303-21;")

        callback_calls = []

        def on_progress(stages):
            callback_calls.append(len(stages))

        config = PipelineConfig(
            input_files=[str(step_file)],
            output_file="output.k"
        )

        pipeline = MeshGenerationPipeline(config, progress_callback=on_progress)

        # Progress tracker should use the callback
        assert pipeline.progress.callback is not None

    def test_run_not_implemented(self, tmp_path):
        """Test that run raises NotImplementedError for now"""
        step_file = tmp_path / "test.step"
        step_file.write_text("ISO-10303-21;")

        config = PipelineConfig(
            input_files=[str(step_file)],
            output_file="output.k"
        )

        pipeline = MeshGenerationPipeline(config)

        # Should raise NotImplementedError since stages not implemented yet
        with pytest.raises(NotImplementedError, match="Geometry processing to be implemented"):
            pipeline.run()

    def test_process_geometry_not_implemented(self, tmp_path):
        """Test _process_geometry raises NotImplementedError"""
        step_file = tmp_path / "test.step"
        step_file.write_text("ISO-10303-21;")

        config = PipelineConfig(
            input_files=[str(step_file)],
            output_file="output.k"
        )

        pipeline = MeshGenerationPipeline(config)

        with pytest.raises(NotImplementedError, match="Day 2"):
            pipeline._process_geometry()

    def test_generate_meshes_not_implemented(self, tmp_path):
        """Test _generate_meshes raises NotImplementedError"""
        step_file = tmp_path / "test.step"
        step_file.write_text("ISO-10303-21;")

        config = PipelineConfig(
            input_files=[str(step_file)],
            output_file="output.k"
        )

        pipeline = MeshGenerationPipeline(config)

        with pytest.raises(NotImplementedError, match="Day 3-4"):
            pipeline._generate_meshes([])

    def test_process_quality_not_implemented(self, tmp_path):
        """Test _process_quality raises NotImplementedError"""
        step_file = tmp_path / "test.step"
        step_file.write_text("ISO-10303-21;")

        config = PipelineConfig(
            input_files=[str(step_file)],
            output_file="output.k"
        )

        pipeline = MeshGenerationPipeline(config)

        with pytest.raises(NotImplementedError, match="Day 5-7"):
            pipeline._process_quality([])

    def test_detect_contacts_not_implemented(self, tmp_path):
        """Test _detect_contacts raises NotImplementedError"""
        step_file = tmp_path / "test.step"
        step_file.write_text("ISO-10303-21;")

        config = PipelineConfig(
            input_files=[str(step_file)],
            output_file="output.k"
        )

        pipeline = MeshGenerationPipeline(config)

        with pytest.raises(NotImplementedError, match="Day 5-7"):
            pipeline._detect_contacts([])

    def test_export_lsdyna_not_implemented(self, tmp_path):
        """Test _export_lsdyna raises NotImplementedError"""
        step_file = tmp_path / "test.step"
        step_file.write_text("ISO-10303-21;")

        config = PipelineConfig(
            input_files=[str(step_file)],
            output_file="output.k"
        )

        pipeline = MeshGenerationPipeline(config)

        with pytest.raises(NotImplementedError, match="Day 5-7"):
            pipeline._export_lsdyna([], [])

    def test_validate_output_placeholder(self, tmp_path):
        """Test _validate_output returns placeholder"""
        step_file = tmp_path / "test.step"
        step_file.write_text("ISO-10303-21;")

        config = PipelineConfig(
            input_files=[str(step_file)],
            output_file="output.k"
        )

        pipeline = MeshGenerationPipeline(config)

        result = pipeline._validate_output()

        # Should return placeholder result
        assert 'warnings' in result
        assert 'Validation not yet implemented' in result['warnings']

    def test_component_initialization(self, tmp_path):
        """Test that all components are initialized"""
        step_file = tmp_path / "test.step"
        step_file.write_text("ISO-10303-21;")

        config = PipelineConfig(
            input_files=[str(step_file)],
            output_file="output.k"
        )

        pipeline = MeshGenerationPipeline(config)

        # Check all components exist
        assert hasattr(pipeline, 'step_reader')
        assert hasattr(pipeline, 'shape_classifier')
        assert hasattr(pipeline, 'quality_analyzer')
        assert hasattr(pipeline, 'contact_detector')
        assert hasattr(pipeline, 'material_library')
        assert hasattr(pipeline, 'progress')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
