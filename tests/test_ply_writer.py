"""
Tests for PLY Writer

Author: KooMeshGenerator Team
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from koomesh.meshing.mesh_data import MeshData, ElementType
from koomesh.export.ply_writer import PLYWriter, export_to_ply


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


class TestPLYWriter:
    """Test PLY writer basic functionality"""

    def test_write_creates_file(self, simple_tet_mesh, temp_dir):
        """Test that PLY file is created"""
        output_file = temp_dir / "test.ply"

        writer = PLYWriter()
        writer.write_mesh(simple_tet_mesh, str(output_file))

        assert output_file.exists()

    def test_ascii_format(self, simple_tet_mesh, temp_dir):
        """Test ASCII PLY format"""
        output_file = temp_dir / "test.ply"

        writer = PLYWriter()
        writer.write_mesh(simple_tet_mesh, str(output_file), ascii_format=True)

        content = output_file.read_text()

        assert "ply" in content
        assert "format ascii" in content
        assert "element vertex" in content
        assert "element face" in content

    def test_binary_format(self, simple_tet_mesh, temp_dir):
        """Test binary PLY format"""
        output_file = temp_dir / "test.ply"

        writer = PLYWriter()
        writer.write_mesh(simple_tet_mesh, str(output_file), ascii_format=False)

        content = output_file.read_bytes()

        assert b"ply" in content
        assert b"format binary_little_endian" in content

    def test_hex_mesh(self, simple_hex_mesh, temp_dir):
        """Test hex mesh export"""
        output_file = temp_dir / "hex.ply"

        writer = PLYWriter()
        writer.write_mesh(simple_hex_mesh, str(output_file))

        content = output_file.read_text()

        assert "ply" in content
        assert "element vertex 8" in content  # 8 nodes

    def test_vertex_count(self, simple_tet_mesh, temp_dir):
        """Test that vertex count is correct"""
        output_file = temp_dir / "test.ply"

        writer = PLYWriter()
        writer.write_mesh(simple_tet_mesh, str(output_file))

        content = output_file.read_text()

        assert f"element vertex {len(simple_tet_mesh.nodes)}" in content

    def test_face_count(self, simple_tet_mesh, temp_dir):
        """Test that face count is present"""
        output_file = temp_dir / "test.ply"

        writer = PLYWriter()
        writer.write_mesh(simple_tet_mesh, str(output_file))

        content = output_file.read_text()

        assert "element face" in content


class TestPLYConvenience:
    """Test convenience function"""

    def test_export_to_ply(self, simple_tet_mesh, temp_dir):
        """Test export_to_ply function"""
        output_file = temp_dir / "test.ply"

        result = export_to_ply(simple_tet_mesh, str(output_file))

        assert result is True
        assert output_file.exists()

    def test_export_ascii(self, simple_tet_mesh, temp_dir):
        """Test ASCII export"""
        output_file = temp_dir / "test.ply"

        export_to_ply(simple_tet_mesh, str(output_file), ascii_format=True)

        content = output_file.read_text()
        assert "format ascii" in content

    def test_export_binary(self, simple_tet_mesh, temp_dir):
        """Test binary export"""
        output_file = temp_dir / "test.ply"

        export_to_ply(simple_tet_mesh, str(output_file), ascii_format=False)

        content = output_file.read_bytes()
        assert b"binary" in content


class TestPLYElementTypes:
    """Test different element types"""

    def test_tri_mesh(self, temp_dir):
        """Test triangular mesh"""
        mesh = MeshData(element_type=ElementType.TRI3)
        n1 = mesh.add_node(0.0, 0.0, 0.0)
        n2 = mesh.add_node(1.0, 0.0, 0.0)
        n3 = mesh.add_node(0.0, 1.0, 0.0)
        mesh.add_element([n1, n2, n3])

        output_file = temp_dir / "tri.ply"
        export_to_ply(mesh, str(output_file))

        assert output_file.exists()

    def test_quad_mesh(self, temp_dir):
        """Test quad mesh"""
        mesh = MeshData(element_type=ElementType.QUAD4)
        n1 = mesh.add_node(0.0, 0.0, 0.0)
        n2 = mesh.add_node(1.0, 0.0, 0.0)
        n3 = mesh.add_node(1.0, 1.0, 0.0)
        n4 = mesh.add_node(0.0, 1.0, 0.0)
        mesh.add_element([n1, n2, n3, n4])

        output_file = temp_dir / "quad.ply"
        export_to_ply(mesh, str(output_file))

        assert output_file.exists()

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

        output_file = temp_dir / "prism.ply"
        export_to_ply(mesh, str(output_file))

        assert output_file.exists()
