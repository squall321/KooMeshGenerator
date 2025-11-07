"""
Test Configuration System

Tests YAML config loading, validation, and override functionality.
"""

import pytest
from pathlib import Path
import tempfile
import yaml

from koomesh.config.workflow_schema import (
    WorkflowConfig,
    ProjectConfig,
    InputConfig,
    MeshingConfig,
    QualityConfig
)


class TestConfigLoading:
    """Test config file loading"""

    def test_load_valid_config(self):
        """Test loading a valid YAML config"""
        config_data = {
            'project': {
                'name': 'test_project',
                'description': 'Test project'
            },
            'input': {
                'step_files': ['test.step']
            },
            'meshing': {
                'mesh_size': 2.0,
                'element_type': 'tet4'
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            config = WorkflowConfig.from_yaml(temp_path)
            assert config.project.name == 'test_project'
            assert config.meshing.mesh_size == 2.0
            assert config.meshing.element_type == 'tet4'
        finally:
            Path(temp_path).unlink()

    def test_load_minimal_config(self):
        """Test loading minimal config with defaults"""
        config_data = {
            'project': {
                'name': 'minimal'
            },
            'input': {
                'step_files': ['test.step']
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            config = WorkflowConfig.from_yaml(temp_path)
            assert config.project.name == 'minimal'
            # Should have defaults
            assert config.meshing.mesh_size == 1.0
            assert config.meshing.element_type == 'tet4'
        finally:
            Path(temp_path).unlink()


class TestConfigValidation:
    """Test config validation"""

    def test_valid_mesh_size(self):
        """Test valid mesh size"""
        config_data = {
            'mesh_size': 2.0,
            'element_type': 'tet4'
        }
        config = MeshingConfig(**config_data)
        assert config.mesh_size == 2.0

    def test_invalid_mesh_size_negative(self):
        """Test invalid negative mesh size"""
        with pytest.raises(ValueError):
            MeshingConfig(mesh_size=-1.0)

    def test_invalid_mesh_size_zero(self):
        """Test invalid zero mesh size"""
        with pytest.raises(ValueError):
            MeshingConfig(mesh_size=0.0)

    def test_valid_element_types(self):
        """Test valid element types"""
        valid_types = ['tet4', 'tet10', 'hex8', 'hex20', 'mixed']
        for elem_type in valid_types:
            config = MeshingConfig(element_type=elem_type)
            assert config.element_type == elem_type

    def test_invalid_element_type(self):
        """Test invalid element type"""
        with pytest.raises(ValueError):
            MeshingConfig(element_type='invalid_type')

    def test_quality_thresholds(self):
        """Test quality threshold validation"""
        config = QualityConfig(
            thresholds={
                'aspect_ratio': 10.0,
                'jacobian': 0.1,
                'skewness': 0.8
            }
        )
        assert config.thresholds['aspect_ratio'] == 10.0


class TestConfigOverrides:
    """Test config override functionality"""

    def test_simple_override(self):
        """Test simple value override"""
        config_data = {
            'project': {'name': 'test'},
            'input': {'step_files': ['test.step']},
            'meshing': {'mesh_size': 2.0}
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            config = WorkflowConfig.from_yaml(temp_path)

            # Apply override
            config.apply_overrides({'meshing.mesh_size': 3.5})

            assert config.meshing.mesh_size == 3.5
        finally:
            Path(temp_path).unlink()

    def test_nested_override(self):
        """Test nested config override"""
        config_data = {
            'project': {'name': 'test'},
            'input': {'step_files': ['test.step']},
            'quality': {
                'thresholds': {
                    'aspect_ratio': 10.0,
                    'jacobian': 0.1
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            config = WorkflowConfig.from_yaml(temp_path)

            # Apply nested override
            config.apply_overrides({'quality.thresholds.aspect_ratio': 15.0})

            assert config.quality.thresholds['aspect_ratio'] == 15.0
            assert config.quality.thresholds['jacobian'] == 0.1  # Unchanged
        finally:
            Path(temp_path).unlink()

    def test_multiple_overrides(self):
        """Test multiple overrides at once"""
        config_data = {
            'project': {'name': 'test'},
            'input': {'step_files': ['test.step']},
            'meshing': {
                'mesh_size': 2.0,
                'element_type': 'tet4'
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            config = WorkflowConfig.from_yaml(temp_path)

            # Apply multiple overrides
            config.apply_overrides({
                'meshing.mesh_size': 3.0,
                'meshing.element_type': 'hex8'
            })

            assert config.meshing.mesh_size == 3.0
            assert config.meshing.element_type == 'hex8'
        finally:
            Path(temp_path).unlink()


class TestTemplateConfigs:
    """Test template config files"""

    def test_crash_analysis_template(self):
        """Test crash analysis template exists and loads"""
        template_path = Path(__file__).parent.parent.parent / 'templates' / 'crash_analysis.yaml'

        if template_path.exists():
            config = WorkflowConfig.from_yaml(str(template_path))
            assert config.project is not None
            assert config.meshing is not None

    def test_forming_simulation_template(self):
        """Test forming simulation template exists and loads"""
        template_path = Path(__file__).parent.parent.parent / 'templates' / 'forming_simulation.yaml'

        if template_path.exists():
            config = WorkflowConfig.from_yaml(str(template_path))
            assert config.project is not None

    def test_drop_test_template(self):
        """Test drop test template exists and loads"""
        template_path = Path(__file__).parent.parent.parent / 'templates' / 'drop_test.yaml'

        if template_path.exists():
            config = WorkflowConfig.from_yaml(str(template_path))
            assert config.project is not None

    def test_simple_part_template(self):
        """Test simple part template exists and loads"""
        template_path = Path(__file__).parent.parent.parent / 'templates' / 'simple_part.yaml'

        if template_path.exists():
            config = WorkflowConfig.from_yaml(str(template_path))
            assert config.project is not None


class TestConfigToYAML:
    """Test config export to YAML"""

    def test_export_to_yaml(self):
        """Test exporting config to YAML"""
        config = WorkflowConfig(
            project=ProjectConfig(name='export_test'),
            input=InputConfig(step_files=['test.step']),
            meshing=MeshingConfig(mesh_size=2.5)
        )

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name

        try:
            config.to_yaml(temp_path)

            # Reload and verify
            reloaded = WorkflowConfig.from_yaml(temp_path)
            assert reloaded.project.name == 'export_test'
            assert reloaded.meshing.mesh_size == 2.5
        finally:
            if Path(temp_path).exists():
                Path(temp_path).unlink()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
