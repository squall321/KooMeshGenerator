"""
Tests for MeshGenerator

Tests the mesh generation functionality for the pipeline.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch

from koomesh.pipeline.mesh_generator import (
    MeshGenerator,
    MeshGenerationError
)
from koomesh.pipeline.constants import (
    DEFAULT_MESH_SIZE_MM,
    DEFAULT_ELEMENT_TYPE,
)


class TestMeshGeneratorInit:
    """Test MeshGenerator initialization"""

    def test_init_success(self):
        """Test successful initialization"""
        generator = MeshGenerator()

        assert generator is not None
        assert generator.logger is not None
        assert generator._tet_mesher is None  # Lazy initialization
        assert generator._hex_mesher is None  # Lazy initialization


class TestMeshGeneratorGenerate:
    """Test MeshGenerator.generate() method"""

    def test_generate_empty_shapes(self):
        """Test generate with empty shapes list"""
        generator = MeshGenerator()

        with pytest.raises(ValueError, match="No shapes provided"):
            generator.generate(shapes=[])

    @patch('koomesh.pipeline.mesh_generator.TetMesher')
    def test_generate_single_shape(self, mock_tet_class):
        """Test generating mesh for single shape"""
        # Mock shape
        mock_shape = Mock()

        # Mock mesh
        mock_mesh = Mock()
        mock_mesh.num_nodes.return_value = 100
        mock_mesh.num_elements.return_value = 50

        # Mock TetMesher
        mock_tet = Mock()
        mock_tet.mesh_shape.return_value = mock_mesh
        mock_tet_class.return_value = mock_tet

        # Generate
        generator = MeshGenerator()
        meshes = generator.generate(
            shapes=[(mock_shape, 'solid')],
            mesh_size=5.0
        )

        # Assertions
        assert len(meshes) == 1
        assert meshes[0] == mock_mesh

        # Verify mesher was called
        mock_tet.mesh_shape.assert_called_once()

    @patch('koomesh.pipeline.mesh_generator.TetMesher')
    def test_generate_multiple_shapes(self, mock_tet_class):
        """Test generating meshes for multiple shapes"""
        # Mock shapes
        mock_shape1 = Mock()
        mock_shape2 = Mock()
        mock_shape3 = Mock()

        # Mock meshes
        mock_mesh1 = Mock()
        mock_mesh1.num_nodes.return_value = 100
        mock_mesh1.num_elements.return_value = 50

        mock_mesh2 = Mock()
        mock_mesh2.num_nodes.return_value = 200
        mock_mesh2.num_elements.return_value = 100

        mock_mesh3 = Mock()
        mock_mesh3.num_nodes.return_value = 150
        mock_mesh3.num_elements.return_value = 75

        # Mock TetMesher
        mock_tet = Mock()
        mock_tet.mesh_shape.side_effect = [mock_mesh1, mock_mesh2, mock_mesh3]
        mock_tet_class.return_value = mock_tet

        # Generate
        generator = MeshGenerator()
        shapes = [
            (mock_shape1, 'solid'),
            (mock_shape2, 'shell'),
            (mock_shape3, 'solid'),
        ]
        meshes = generator.generate(shapes=shapes)

        # Assertions
        assert len(meshes) == 3
        assert meshes[0] == mock_mesh1
        assert meshes[1] == mock_mesh2
        assert meshes[2] == mock_mesh3

        # Verify mesher was called 3 times
        assert mock_tet.mesh_shape.call_count == 3

    @patch('koomesh.pipeline.mesh_generator.TetMesher')
    def test_generate_with_template(self, mock_tet_class):
        """Test generating mesh with template parameters"""
        # Mock shape
        mock_shape = Mock()

        # Mock mesh
        mock_mesh = Mock()
        mock_mesh.num_nodes.return_value = 100
        mock_mesh.num_elements.return_value = 50

        # Mock TetMesher
        mock_tet = Mock()
        mock_tet.mesh_shape.return_value = mock_mesh
        mock_tet_class.return_value = mock_tet

        # Mock template
        mock_template = Mock()
        mock_template.name = "automotive_crash_test"
        mock_template.target_element_size = 3.0
        mock_template.element_formulation = "tet4"
        mock_template.min_element_size = 1.0
        mock_template.max_element_size = 10.0

        # Generate
        generator = MeshGenerator()
        meshes = generator.generate(
            shapes=[(mock_shape, 'solid')],
            template=mock_template,
            mesh_size=5.0  # This should be overridden by template
        )

        # Assertions
        assert len(meshes) == 1

        # Verify mesher was configured with template parameters
        assert mock_tet.mesh_size == 3.0  # From template, not config
        assert mock_tet.min_size == 1.0   # From template
        assert mock_tet.max_size == 10.0  # From template

    @patch('koomesh.pipeline.mesh_generator.TetMesher')
    def test_generate_partial_failure(self, mock_tet_class):
        """Test handling of partial failures"""
        # Mock shapes
        mock_shape1 = Mock()
        mock_shape2 = Mock()
        mock_shape3 = Mock()

        # Mock mesh (only for shape 1 and 3)
        mock_mesh1 = Mock()
        mock_mesh1.num_nodes.return_value = 100
        mock_mesh1.num_elements.return_value = 50

        mock_mesh3 = Mock()
        mock_mesh3.num_nodes.return_value = 150
        mock_mesh3.num_elements.return_value = 75

        # Mock TetMesher - shape 2 fails
        mock_tet = Mock()
        mock_tet.mesh_shape.side_effect = [
            mock_mesh1,
            Exception("Meshing failed for shape 2"),
            mock_mesh3
        ]
        mock_tet_class.return_value = mock_tet

        # Generate
        generator = MeshGenerator()
        shapes = [
            (mock_shape1, 'solid'),
            (mock_shape2, 'shell'),  # This will fail
            (mock_shape3, 'solid'),
        ]
        meshes = generator.generate(shapes=shapes)

        # Should still return meshes for shapes 1 and 3
        assert len(meshes) == 2

    @patch('koomesh.pipeline.mesh_generator.TetMesher')
    def test_generate_complete_failure(self, mock_tet_class):
        """Test handling when all shapes fail"""
        # Mock shape
        mock_shape = Mock()

        # Mock TetMesher - always fails
        mock_tet = Mock()
        mock_tet.mesh_shape.side_effect = Exception("Meshing always fails")
        mock_tet_class.return_value = mock_tet

        # Generate - should raise MeshGenerationError
        generator = MeshGenerator()
        with pytest.raises(MeshGenerationError, match="Failed to generate any meshes"):
            generator.generate(shapes=[(mock_shape, 'solid')])


class TestMeshGeneratorMesherSelection:
    """Test mesher selection logic"""

    @patch('koomesh.pipeline.mesh_generator.TetMesher')
    @patch('koomesh.pipeline.mesh_generator.HexMesher')
    def test_select_tet_mesher_for_tet_element(self, mock_hex_class, mock_tet_class):
        """Test that tet mesher is selected for tet elements"""
        mock_shape = Mock()
        mock_mesh = Mock()
        mock_mesh.num_nodes.return_value = 100
        mock_mesh.num_elements.return_value = 50

        mock_tet = Mock()
        mock_tet.mesh_shape.return_value = mock_mesh
        mock_tet_class.return_value = mock_tet

        generator = MeshGenerator()
        meshes = generator.generate(
            shapes=[(mock_shape, 'solid')],
            element_type='tet4'
        )

        # TetMesher should be used
        mock_tet_class.assert_called()
        # HexMesher should not be used
        mock_hex_class.assert_not_called()

    @patch('koomesh.pipeline.mesh_generator.TetMesher')
    @patch('koomesh.pipeline.mesh_generator.HexMesher')
    def test_select_hex_mesher_for_hex_element(self, mock_hex_class, mock_tet_class):
        """Test that hex mesher is selected for hex elements"""
        mock_shape = Mock()
        mock_mesh = Mock()
        mock_mesh.num_nodes.return_value = 64
        mock_mesh.num_elements.return_value = 8

        mock_hex = Mock()
        mock_hex.mesh_box.return_value = mock_mesh
        mock_hex_class.return_value = mock_hex

        generator = MeshGenerator()
        meshes = generator.generate(
            shapes=[(mock_shape, 'solid')],
            element_type='hex8'
        )

        # HexMesher should be used
        mock_hex_class.assert_called()


class TestMeshGeneratorStatistics:
    """Test statistics generation"""

    def test_get_statistics_empty(self):
        """Test statistics with empty meshes"""
        generator = MeshGenerator()
        stats = generator.get_statistics([])

        assert stats['total_meshes'] == 0
        assert stats['total_nodes'] == 0
        assert stats['total_elements'] == 0
        assert stats['avg_nodes_per_mesh'] == 0
        assert stats['avg_elements_per_mesh'] == 0

    def test_get_statistics_single_mesh(self):
        """Test statistics with single mesh"""
        mock_mesh = Mock()
        mock_mesh.num_nodes.return_value = 100
        mock_mesh.num_elements.return_value = 50

        generator = MeshGenerator()
        stats = generator.get_statistics([mock_mesh])

        assert stats['total_meshes'] == 1
        assert stats['total_nodes'] == 100
        assert stats['total_elements'] == 50
        assert stats['avg_nodes_per_mesh'] == 100
        assert stats['avg_elements_per_mesh'] == 50

    def test_get_statistics_multiple_meshes(self):
        """Test statistics with multiple meshes"""
        mock_mesh1 = Mock()
        mock_mesh1.num_nodes.return_value = 100
        mock_mesh1.num_elements.return_value = 50

        mock_mesh2 = Mock()
        mock_mesh2.num_nodes.return_value = 200
        mock_mesh2.num_elements.return_value = 100

        generator = MeshGenerator()
        stats = generator.get_statistics([mock_mesh1, mock_mesh2])

        assert stats['total_meshes'] == 2
        assert stats['total_nodes'] == 300
        assert stats['total_elements'] == 150
        assert stats['avg_nodes_per_mesh'] == 150
        assert stats['avg_elements_per_mesh'] == 75
