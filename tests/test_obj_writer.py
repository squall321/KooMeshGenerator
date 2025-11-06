"""
Tests for OBJ Writer

Author: KooMeshGenerator Team
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from koomesh.meshing.mesh_data import MeshData, ElementType
from koomesh.export.obj_writer import OBJWriter, export_to_obj


@pytest.fixture
def temp_dir():
    """Create temporary directory"""
    tmp = tempfile.mkdtemp()
    yield Path(tmp)
    shutil.rmtree(tmp)


@pytest.fixture
def simple_tet_mesh():
    """Create simple tet mesh"""
    mesh = MeshData(element_type=ElementType.TET4)

    node_ids = []
    node_ids.append(mesh.add_node(0.0, 0.0, 0.0))
    node_ids.append(mesh.add_node(1.0, 0.0, 0.0))
    node_ids.append(mesh.add_node(0.0, 1.0, 0.0))
    node_ids.append(mesh.add_node(0.0, 0.0, 1.0))

    mesh.add_element(node_ids)
    return mesh


@pytest.fixture
def simple_hex_mesh():
    """Create simple hex mesh"""
    mesh = MeshData(element_type=ElementType.HEX8)

    node_ids = []
    for i in range(2):
        for j in range(2):
            for k in range(2):
                node_ids.append(mesh.add_node(float(i), float(j), float(k)))

    mesh.add_element([node_ids[0], node_ids[1], node_ids[3], node_ids[2],
                     node_ids[4], node_ids[5], node_ids[7], node_ids[6]])
    return mesh


class TestOBJWriter:
    """Test OBJ writer basic functionality"""

    def test_write_creates_file(self, simple_tet_mesh, temp_dir):
        """Test that OBJ file is created"""
        output_file = temp_dir / "test.obj"

        writer = OBJWriter()
        writer.write_mesh(simple_tet_mesh, str(output_file))

        assert output_file.exists()

    def test_obj_format(self, simple_tet_mesh, temp_dir):
        """Test OBJ format structure"""
        output_file = temp_dir / "test.obj"

        writer = OBJWriter()
        writer.write_mesh(simple_tet_mesh, str(output_file), "TestMesh")

        content = output_file.read_text()

        assert "# OBJ file" in content
        assert "o TestMesh" in content
        assert "v " in content  # Vertices
        assert "vn " in content  # Normals
        assert "f " in content  # Faces

    def test_hex_mesh(self, simple_hex_mesh, temp_dir):
        """Test hex mesh export"""
        output_file = temp_dir / "hex.obj"

        writer = OBJWriter()
        writer.write_mesh(simple_hex_mesh, str(output_file))

        content = output_file.read_text()

        # Count vertices
        vertices = [line for line in content.split('\n') if line.startswith('v ')]
        assert len(vertices) == 8  # 8 nodes

    def test_vertex_format(self, simple_tet_mesh, temp_dir):
        """Test vertex format"""
        output_file = temp_dir / "test.obj"

        writer = OBJWriter()
        writer.write_mesh(simple_tet_mesh, str(output_file))

        content = output_file.read_text()

        # Check that vertices are present
        vertices = [line for line in content.split('\n') if line.startswith('v ')]
        assert len(vertices) == 4  # 4 nodes

    def test_normal_format(self, simple_tet_mesh, temp_dir):
        """Test normal format"""
        output_file = temp_dir / "test.obj"

        writer = OBJWriter()
        writer.write_mesh(simple_tet_mesh, str(output_file))

        content = output_file.read_text()

        # Check that normals are present
        normals = [line for line in content.split('\n') if line.startswith('vn ')]
        assert len(normals) > 0

    def test_face_format(self, simple_tet_mesh, temp_dir):
        """Test face format"""
        output_file = temp_dir / "test.obj"

        writer = OBJWriter()
        writer.write_mesh(simple_tet_mesh, str(output_file))

        content = output_file.read_text()

        # Check that faces are present with normals
        faces = [line for line in content.split('\n') if line.startswith('f ')]
        assert len(faces) > 0
        assert "//" in faces[0]  # OBJ format: v//vn


class TestOBJConvenience:
    """Test convenience function"""

    def test_export_to_obj(self, simple_tet_mesh, temp_dir):
        """Test export_to_obj function"""
        output_file = temp_dir / "test.obj"

        result = export_to_obj(simple_tet_mesh, str(output_file))

        assert result is True
        assert output_file.exists()

    def test_export_with_name(self, simple_tet_mesh, temp_dir):
        """Test export with custom object name"""
        output_file = temp_dir / "test.obj"

        export_to_obj(simple_tet_mesh, str(output_file), "CustomName")

        content = output_file.read_text()
        assert "o CustomName" in content

    def test_export_default_name(self, simple_tet_mesh, temp_dir):
        """Test export with default name"""
        output_file = temp_dir / "test.obj"

        export_to_obj(simple_tet_mesh, str(output_file))

        content = output_file.read_text()
        assert "o mesh" in content


class TestOBJElementTypes:
    """Test different element types"""

    def test_tri_mesh(self, temp_dir):
        """Test triangular mesh"""
        mesh = MeshData(element_type=ElementType.TRI3)
        n1 = mesh.add_node(0.0, 0.0, 0.0)
        n2 = mesh.add_node(1.0, 0.0, 0.0)
        n3 = mesh.add_node(0.0, 1.0, 0.0)
        mesh.add_element([n1, n2, n3])

        output_file = temp_dir / "tri.obj"
        export_to_obj(mesh, str(output_file))

        content = output_file.read_text()
        faces = [line for line in content.split('\n') if line.startswith('f ')]
        assert len(faces) == 1  # One triangle

    def test_quad_mesh(self, temp_dir):
        """Test quad mesh"""
        mesh = MeshData(element_type=ElementType.QUAD4)
        n1 = mesh.add_node(0.0, 0.0, 0.0)
        n2 = mesh.add_node(1.0, 0.0, 0.0)
        n3 = mesh.add_node(1.0, 1.0, 0.0)
        n4 = mesh.add_node(0.0, 1.0, 0.0)
        mesh.add_element([n1, n2, n3, n4])

        output_file = temp_dir / "quad.obj"
        export_to_obj(mesh, str(output_file))

        content = output_file.read_text()
        faces = [line for line in content.split('\n') if line.startswith('f ')]
        assert len(faces) == 1  # One quad face

    def test_prism_mesh(self, temp_dir):
        """Test prism mesh"""
        mesh = MeshData(element_type=ElementType.PRISM6)
        node_ids = []
        node_ids.append(mesh.add_node(0.0, 0.0, 0.0))
        node_ids.append(mesh.add_node(1.0, 0.0, 0.0))
        node_ids.append(mesh.add_node(0.0, 1.0, 0.0))
        node_ids.append(mesh.add_node(0.0, 0.0, 1.0))
        node_ids.append(mesh.add_node(1.0, 0.0, 1.0))
        node_ids.append(mesh.add_node(0.0, 1.0, 1.0))
        mesh.add_element(node_ids)

        output_file = temp_dir / "prism.obj"
        export_to_obj(mesh, str(output_file))

        assert output_file.exists()

    def test_pyramid_mesh(self, temp_dir):
        """Test pyramid mesh"""
        mesh = MeshData(element_type=ElementType.PYRAMID5)
        node_ids = []
        node_ids.append(mesh.add_node(0.0, 0.0, 0.0))
        node_ids.append(mesh.add_node(1.0, 0.0, 0.0))
        node_ids.append(mesh.add_node(1.0, 1.0, 0.0))
        node_ids.append(mesh.add_node(0.0, 1.0, 0.0))
        node_ids.append(mesh.add_node(0.5, 0.5, 1.0))
        mesh.add_element(node_ids)

        output_file = temp_dir / "pyramid.obj"
        export_to_obj(mesh, str(output_file))

        assert output_file.exists()


class TestOBJMultiElement:
    """Test meshes with multiple elements"""

    def test_multiple_tets(self, temp_dir):
        """Test mesh with multiple tets"""
        mesh = MeshData(element_type=ElementType.TET4)

        for i in range(3):
            node_ids = []
            node_ids.append(mesh.add_node(float(i), 0.0, 0.0))
            node_ids.append(mesh.add_node(float(i+1), 0.0, 0.0))
            node_ids.append(mesh.add_node(float(i+0.5), 1.0, 0.0))
            node_ids.append(mesh.add_node(float(i+0.5), 0.5, 1.0))
            mesh.add_element(node_ids)

        output_file = temp_dir / "multi.obj"
        export_to_obj(mesh, str(output_file))

        content = output_file.read_text()
        faces = [line for line in content.split('\n') if line.startswith('f ')]
        assert len(faces) > 3  # At least 3 elements * 4 faces each = 12
