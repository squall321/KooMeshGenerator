"""
Tests for Elmer FEM Writer

Author: KooMeshGenerator Team
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from koomesh.meshing.mesh_data import MeshData, ElementType
from koomesh.export.elmer_writer import ElmerWriter


@pytest.fixture
def temp_dir():
    """Create temporary directory for test outputs"""
    tmp = tempfile.mkdtemp()
    yield Path(tmp)
    shutil.rmtree(tmp)


@pytest.fixture
def simple_hex_mesh():
    """Create a simple hex mesh for testing"""
    mesh = MeshData(element_type=ElementType.HEX8)

    # Create 2x2x2 grid of nodes
    node_ids = []
    for i in range(2):
        for j in range(2):
            for k in range(2):
                node_ids.append(mesh.add_node(float(i), float(j), float(k)))

    # Add one hex element
    mesh.add_element([node_ids[0], node_ids[1], node_ids[3], node_ids[2],
                     node_ids[4], node_ids[5], node_ids[7], node_ids[6]])

    return mesh


@pytest.fixture
def simple_tet_mesh():
    """Create a simple tet mesh for testing"""
    mesh = MeshData(element_type=ElementType.TET4)

    # Create 4 nodes for a tetrahedron
    node_ids = []
    node_ids.append(mesh.add_node(0.0, 0.0, 0.0))
    node_ids.append(mesh.add_node(1.0, 0.0, 0.0))
    node_ids.append(mesh.add_node(0.0, 1.0, 0.0))
    node_ids.append(mesh.add_node(0.0, 0.0, 1.0))

    # Add tet element
    mesh.add_element([node_ids[0], node_ids[1], node_ids[2], node_ids[3]])

    return mesh


class TestElmerWriter:
    """Test basic Elmer writer functionality"""

    def test_write_creates_directory(self, simple_hex_mesh, temp_dir):
        """Test that writer creates output directory"""
        output_dir = temp_dir / "elmer_mesh"

        writer = ElmerWriter(str(output_dir))
        writer.write_mesh(simple_hex_mesh)

        assert output_dir.exists()
        assert output_dir.is_dir()

    def test_write_creates_all_files(self, simple_hex_mesh, temp_dir):
        """Test that all required Elmer files are created"""
        output_dir = temp_dir / "elmer_mesh"

        writer = ElmerWriter(str(output_dir))
        writer.write_mesh(simple_hex_mesh)

        # Check all required files exist
        assert (output_dir / "mesh.header").exists()
        assert (output_dir / "mesh.nodes").exists()
        assert (output_dir / "mesh.elements").exists()
        assert (output_dir / "mesh.boundary").exists()

    def test_header_content(self, simple_hex_mesh, temp_dir):
        """Test mesh.header content"""
        output_dir = temp_dir / "elmer_mesh"

        writer = ElmerWriter(str(output_dir))
        writer.write_mesh(simple_hex_mesh)

        content = (output_dir / "mesh.header").read_text()
        lines = content.strip().split('\n')

        # Header has multiple lines: count line, type count, type info
        assert len(lines) >= 1
        parts = lines[0].split()
        assert len(parts) == 3
        assert int(parts[0]) == 8  # 8 nodes
        assert int(parts[1]) == 1  # 1 element
        assert int(parts[2]) == 0  # 0 boundary elements

    def test_nodes_content(self, simple_hex_mesh, temp_dir):
        """Test mesh.nodes content"""
        output_dir = temp_dir / "elmer_mesh"

        writer = ElmerWriter(str(output_dir))
        writer.write_mesh(simple_hex_mesh)

        content = (output_dir / "mesh.nodes").read_text()
        lines = [l.strip() for l in content.strip().split('\n') if l.strip()]

        # Should have 8 nodes
        assert len(lines) == 8

        # Check format: node_id -1 x y z
        parts = lines[0].split()
        assert len(parts) == 5
        assert int(parts[1]) == -1  # Partition number

    def test_elements_content_hex8(self, simple_hex_mesh, temp_dir):
        """Test mesh.elements content for HEX8"""
        output_dir = temp_dir / "elmer_mesh"

        writer = ElmerWriter(str(output_dir))
        writer.write_mesh(simple_hex_mesh)

        content = (output_dir / "mesh.elements").read_text()
        lines = [l.strip() for l in content.strip().split('\n') if l.strip()]

        # Should have 1 element
        assert len(lines) == 1

        # Format: elem_id body_id elem_type node1 node2 ...
        parts = lines[0].split()
        assert int(parts[1]) == 1  # Body ID
        assert int(parts[2]) == 808  # HEX8 type code
        assert len(parts) == 3 + 8  # elem_id + body_id + type + 8 nodes

    def test_elements_content_tet4(self, simple_tet_mesh, temp_dir):
        """Test mesh.elements content for TET4"""
        output_dir = temp_dir / "elmer_mesh"

        writer = ElmerWriter(str(output_dir))
        writer.write_mesh(simple_tet_mesh)

        content = (output_dir / "mesh.elements").read_text()
        lines = [l.strip() for l in content.strip().split('\n') if l.strip()]

        # Should have 1 element
        assert len(lines) == 1

        # Format: elem_id body_id elem_type node1 node2 ...
        parts = lines[0].split()
        assert int(parts[2]) == 504  # TET4 type code
        assert len(parts) == 3 + 4  # elem_id + body_id + type + 4 nodes

    def test_boundary_empty(self, simple_hex_mesh, temp_dir):
        """Test mesh.boundary is empty (no boundary implementation yet)"""
        output_dir = temp_dir / "elmer_mesh"

        writer = ElmerWriter(str(output_dir))
        writer.write_mesh(simple_hex_mesh)

        content = (output_dir / "mesh.boundary").read_text()

        # Should contain "0 0 0" (no boundary elements)
        assert "0 0 0" in content

    def test_multiple_elements(self, temp_dir):
        """Test mesh with multiple elements"""
        mesh = MeshData(element_type=ElementType.TET4)

        # Create two tetrahedrons
        node_ids = []
        # First tet
        node_ids.append(mesh.add_node(0.0, 0.0, 0.0))
        node_ids.append(mesh.add_node(1.0, 0.0, 0.0))
        node_ids.append(mesh.add_node(0.0, 1.0, 0.0))
        node_ids.append(mesh.add_node(0.0, 0.0, 1.0))
        # Second tet
        node_ids.append(mesh.add_node(1.0, 1.0, 1.0))

        mesh.add_element([node_ids[0], node_ids[1], node_ids[2], node_ids[3]])
        mesh.add_element([node_ids[1], node_ids[2], node_ids[3], node_ids[4]])

        output_dir = temp_dir / "elmer_mesh"
        writer = ElmerWriter(str(output_dir))
        writer.write_mesh(mesh)

        # Check header
        header = (output_dir / "mesh.header").read_text().strip()
        parts = header.split()
        assert int(parts[0]) == 5  # 5 nodes
        assert int(parts[1]) == 2  # 2 elements

        # Check elements
        content = (output_dir / "mesh.elements").read_text()
        lines = [l.strip() for l in content.strip().split('\n') if l.strip()]
        assert len(lines) == 2


class TestElmerElementTypes:
    """Test Elmer element type mappings"""

    def test_hex8_type_code(self, temp_dir):
        """Test HEX8 maps to 808"""
        mesh = MeshData(element_type=ElementType.HEX8)
        node_ids = [mesh.add_node(float(i % 2), float((i // 2) % 2), float(i // 4))
                    for i in range(8)]
        mesh.add_element(node_ids)

        output_dir = temp_dir / "elmer_mesh"
        writer = ElmerWriter(str(output_dir))
        writer.write_mesh(mesh)

        content = (output_dir / "mesh.elements").read_text()
        assert " 808 " in content

    def test_tet4_type_code(self, temp_dir):
        """Test TET4 maps to 504"""
        mesh = MeshData(element_type=ElementType.TET4)
        node_ids = []
        node_ids.append(mesh.add_node(0.0, 0.0, 0.0))
        node_ids.append(mesh.add_node(1.0, 0.0, 0.0))
        node_ids.append(mesh.add_node(0.0, 1.0, 0.0))
        node_ids.append(mesh.add_node(0.0, 0.0, 1.0))
        mesh.add_element(node_ids)

        output_dir = temp_dir / "elmer_mesh"
        writer = ElmerWriter(str(output_dir))
        writer.write_mesh(mesh)

        content = (output_dir / "mesh.elements").read_text()
        assert " 504 " in content

    def test_prism6_type_code(self, temp_dir):
        """Test PRISM6 maps to 706"""
        mesh = MeshData(element_type=ElementType.PRISM6)
        node_ids = []
        # Bottom triangle
        node_ids.append(mesh.add_node(0.0, 0.0, 0.0))
        node_ids.append(mesh.add_node(1.0, 0.0, 0.0))
        node_ids.append(mesh.add_node(0.0, 1.0, 0.0))
        # Top triangle
        node_ids.append(mesh.add_node(0.0, 0.0, 1.0))
        node_ids.append(mesh.add_node(1.0, 0.0, 1.0))
        node_ids.append(mesh.add_node(0.0, 1.0, 1.0))
        mesh.add_element(node_ids)

        output_dir = temp_dir / "elmer_mesh"
        writer = ElmerWriter(str(output_dir))
        writer.write_mesh(mesh)

        content = (output_dir / "mesh.elements").read_text()
        assert " 706 " in content


class TestElmerErrors:
    """Test error handling"""

    def test_unsupported_element_type(self, temp_dir):
        """Test that unsupported element types use default"""
        mesh = MeshData(element_type=ElementType.QUAD4)
        node_ids = []
        node_ids.append(mesh.add_node(0.0, 0.0, 0.0))
        node_ids.append(mesh.add_node(1.0, 0.0, 0.0))
        node_ids.append(mesh.add_node(1.0, 1.0, 0.0))
        node_ids.append(mesh.add_node(0.0, 1.0, 0.0))
        mesh.add_element(node_ids)

        output_dir = temp_dir / "elmer_mesh"
        writer = ElmerWriter(str(output_dir))

        # QUAD4 is not in ELMER_ELEMENT_TYPES, but it uses default value 808
        writer.write_mesh(mesh)
        assert (output_dir / "mesh.elements").exists()

    def test_empty_mesh(self, temp_dir):
        """Test that empty mesh raises error"""
        mesh = MeshData(element_type=ElementType.HEX8)

        output_dir = temp_dir / "elmer_mesh"
        writer = ElmerWriter(str(output_dir))

        # Should raise ElmerError for empty mesh
        from koomesh.export.elmer_writer import ElmerError
        with pytest.raises(ElmerError, match="empty"):
            writer.write_mesh(mesh)
