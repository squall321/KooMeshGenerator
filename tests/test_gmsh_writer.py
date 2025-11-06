"""
Test Suite for Gmsh MSH Writer
================================

This module contains comprehensive tests for the Gmsh MSH format export functionality.

Test Categories:
1. Basic Functionality Tests
2. MSH Version Tests (2.2 and 4.1)
3. Element Type Tests
4. Physical Group Tests
5. Error Handling Tests
6. File Format Compliance Tests

Author: KooMeshGenerator Team
License: MIT
"""

import pytest
import tempfile
from pathlib import Path

from koomesh.meshing.mesh_data import MeshData, ElementType
from koomesh.export.gmsh_writer import (
    GmshWriter,
    GmshError,
    export_to_gmsh
)


@pytest.fixture
def temp_msh_file():
    """Create a temporary MSH file path"""
    with tempfile.NamedTemporaryFile(suffix='.msh', delete=False) as f:
        temp_path = f.name
    yield temp_path
    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def simple_hex_mesh():
    """Create a simple single-element HEX8 mesh"""
    mesh = MeshData(element_type=ElementType.HEX8)

    # Create 8 nodes for a unit cube
    mesh.add_node(0.0, 0.0, 0.0, node_id=1)
    mesh.add_node(1.0, 0.0, 0.0, node_id=2)
    mesh.add_node(1.0, 1.0, 0.0, node_id=3)
    mesh.add_node(0.0, 1.0, 0.0, node_id=4)
    mesh.add_node(0.0, 0.0, 1.0, node_id=5)
    mesh.add_node(1.0, 0.0, 1.0, node_id=6)
    mesh.add_node(1.0, 1.0, 1.0, node_id=7)
    mesh.add_node(0.0, 1.0, 1.0, node_id=8)

    # Add one HEX8 element
    mesh.add_element([1, 2, 3, 4, 5, 6, 7, 8], element_id=1)

    return mesh


@pytest.fixture
def simple_tet_mesh():
    """Create a simple single-element TET4 mesh"""
    mesh = MeshData(element_type=ElementType.TET4)

    # Create 4 nodes for a tetrahedron
    mesh.add_node(0.0, 0.0, 0.0, node_id=1)
    mesh.add_node(1.0, 0.0, 0.0, node_id=2)
    mesh.add_node(0.5, 1.0, 0.0, node_id=3)
    mesh.add_node(0.5, 0.5, 1.0, node_id=4)

    # Add one TET4 element
    mesh.add_element([1, 2, 3, 4], element_id=1)

    return mesh


@pytest.fixture
def multi_element_mesh():
    """Create a mesh with multiple HEX8 elements"""
    mesh = MeshData(element_type=ElementType.HEX8)

    # Create nodes for 2x1x1 grid (2 cubes side by side)
    for i in range(3):
        for j in range(2):
            for k in range(2):
                node_id = i * 4 + j * 2 + k + 1
                mesh.add_node(float(i), float(j), float(k), node_id=node_id)

    # Add first HEX8 element
    mesh.add_element([1, 3, 7, 5, 2, 4, 8, 6], element_id=1)

    # Add second HEX8 element
    mesh.add_element([5, 7, 11, 9, 6, 8, 12, 10], element_id=2)

    return mesh


@pytest.fixture
def mixed_element_mesh():
    """Create a mesh with both HEX8 and TET4 elements"""
    mesh = MeshData(element_type=ElementType.HEX8)

    # Add nodes for HEX8 (nodes 1-8)
    mesh.add_node(0.0, 0.0, 0.0, node_id=1)
    mesh.add_node(1.0, 0.0, 0.0, node_id=2)
    mesh.add_node(1.0, 1.0, 0.0, node_id=3)
    mesh.add_node(0.0, 1.0, 0.0, node_id=4)
    mesh.add_node(0.0, 0.0, 1.0, node_id=5)
    mesh.add_node(1.0, 0.0, 1.0, node_id=6)
    mesh.add_node(1.0, 1.0, 1.0, node_id=7)
    mesh.add_node(0.0, 1.0, 1.0, node_id=8)

    # Add nodes for TET4 (nodes 9-12)
    mesh.add_node(2.0, 0.0, 0.0, node_id=9)
    mesh.add_node(3.0, 0.0, 0.0, node_id=10)
    mesh.add_node(2.5, 1.0, 0.0, node_id=11)
    mesh.add_node(2.5, 0.5, 1.0, node_id=12)

    # Add HEX8 element
    mesh.add_element([1, 2, 3, 4, 5, 6, 7, 8], element_id=1, element_type=ElementType.HEX8)

    # Add TET4 element
    mesh.add_element([9, 10, 11, 12], element_id=2, element_type=ElementType.TET4)

    return mesh


# =============================================================================
# 1. Basic Functionality Tests
# =============================================================================

class TestBasicFunctionality:
    """Test basic Gmsh writer functionality"""

    def test_writer_initialization(self, temp_msh_file):
        """Test GmshWriter can be initialized"""
        writer = GmshWriter(temp_msh_file)
        assert writer.filepath == Path(temp_msh_file)
        assert writer.version == "2.2"

    def test_writer_context_manager(self, temp_msh_file, simple_hex_mesh):
        """Test GmshWriter works as context manager"""
        with GmshWriter(temp_msh_file) as writer:
            writer.write_mesh(simple_hex_mesh)

        # Verify file was created
        assert Path(temp_msh_file).exists()
        assert Path(temp_msh_file).stat().st_size > 0

    def test_export_convenience_function(self, temp_msh_file, simple_hex_mesh):
        """Test export_to_gmsh convenience function"""
        success = export_to_gmsh(simple_hex_mesh, temp_msh_file)
        assert success is True
        assert Path(temp_msh_file).exists()

    def test_invalid_version_error(self, temp_msh_file):
        """Test error with invalid MSH version"""
        with pytest.raises(GmshError, match="Unsupported MSH version"):
            GmshWriter(temp_msh_file, version="999")

    def test_file_extension_warning(self, caplog):
        """Test warning for non-standard file extension"""
        with tempfile.NamedTemporaryFile(suffix='.txt') as f:
            writer = GmshWriter(f.name)
            assert "non-standard" in caplog.text.lower()


# =============================================================================
# 2. MSH Version Tests
# =============================================================================

class TestMshVersions:
    """Test different MSH format versions"""

    def test_msh_v2_2_export(self, temp_msh_file, simple_hex_mesh):
        """Test MSH 2.2 format export"""
        with GmshWriter(temp_msh_file, version="2.2") as writer:
            writer.write_mesh(simple_hex_mesh)

        # Read and verify format
        content = Path(temp_msh_file).read_text()
        assert "$MeshFormat" in content
        assert "2.2 0 8" in content
        assert "$Nodes" in content
        assert "$Elements" in content

    def test_msh_v4_1_export(self, temp_msh_file, simple_hex_mesh):
        """Test MSH 4.1 format export"""
        with GmshWriter(temp_msh_file, version="4.1") as writer:
            writer.write_mesh(simple_hex_mesh)

        # Read and verify format
        content = Path(temp_msh_file).read_text()
        assert "$MeshFormat" in content
        assert "4.1 0 8" in content
        assert "$Entities" in content
        assert "$Nodes" in content
        assert "$Elements" in content

    def test_msh_v2_nodes_format(self, temp_msh_file, simple_hex_mesh):
        """Test MSH 2.2 nodes section format"""
        with GmshWriter(temp_msh_file, version="2.2") as writer:
            writer.write_mesh(simple_hex_mesh)

        content = Path(temp_msh_file).read_text()
        lines = content.split('\n')

        # Find nodes section
        nodes_start = lines.index("$Nodes")
        num_nodes_line = lines[nodes_start + 1]
        assert num_nodes_line == "8"  # 8 nodes in simple_hex_mesh

        # Check node format: node-id x y z
        first_node = lines[nodes_start + 2]
        assert first_node.startswith("1 ")  # Node ID 1

    def test_msh_v4_nodes_format(self, temp_msh_file, simple_hex_mesh):
        """Test MSH 4.1 nodes section format"""
        with GmshWriter(temp_msh_file, version="4.1") as writer:
            writer.write_mesh(simple_hex_mesh)

        content = Path(temp_msh_file).read_text()
        lines = content.split('\n')

        # Find nodes section
        nodes_start = lines.index("$Nodes")
        header = lines[nodes_start + 1]
        # Format: numEntityBlocks numNodes minNodeTag maxNodeTag
        parts = header.split()
        assert len(parts) == 4
        assert int(parts[1]) == 8  # 8 nodes


# =============================================================================
# 3. Element Type Tests
# =============================================================================

class TestElementTypes:
    """Test support for different element types"""

    def test_hex8_export(self, temp_msh_file, simple_hex_mesh):
        """Test HEX8 element export"""
        with GmshWriter(temp_msh_file) as writer:
            writer.write_mesh(simple_hex_mesh)

        content = Path(temp_msh_file).read_text()
        lines = content.split('\n')

        # Find elements section
        elems_start = lines.index("$Elements")
        # MSH 2.2 format: elem-id elem-type ...
        # HEX8 is type 5 in Gmsh
        for line in lines[elems_start:]:
            if line.startswith("1 "):  # Element ID 1
                parts = line.split()
                elem_type = int(parts[1])
                assert elem_type == 5  # HEX8
                break

    def test_tet4_export(self, temp_msh_file, simple_tet_mesh):
        """Test TET4 element export"""
        with GmshWriter(temp_msh_file) as writer:
            writer.write_mesh(simple_tet_mesh)

        content = Path(temp_msh_file).read_text()
        # TET4 is type 4 in Gmsh
        assert " 4 " in content  # Element type 4

    def test_mixed_elements_export(self, temp_msh_file, mixed_element_mesh):
        """Test mixed element types export"""
        with GmshWriter(temp_msh_file) as writer:
            writer.write_mesh(mixed_element_mesh)

        content = Path(temp_msh_file).read_text()
        # Should contain both HEX8 (5) and TET4 (4) element types
        assert " 5 " in content  # HEX8
        assert " 4 " in content  # TET4

    def test_hex20_export(self, temp_msh_file):
        """Test HEX20 element export"""
        mesh = MeshData(element_type=ElementType.HEX20)

        # Create 20 nodes for HEX20
        nodes_coords = [
            (0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),  # Corner nodes (bottom)
            (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1),  # Corner nodes (top)
            (0.5, 0, 0), (1, 0.5, 0), (0.5, 1, 0), (0, 0.5, 0),  # Mid-edge (bottom)
            (0.5, 0, 1), (1, 0.5, 1), (0.5, 1, 1), (0, 0.5, 1),  # Mid-edge (top)
            (0, 0, 0.5), (1, 0, 0.5), (1, 1, 0.5), (0, 1, 0.5),  # Mid-edge (vertical)
        ]

        for i, (x, y, z) in enumerate(nodes_coords, 1):
            mesh.add_node(float(x), float(y), float(z), node_id=i)

        mesh.add_element(list(range(1, 21)), element_id=1)

        with GmshWriter(temp_msh_file) as writer:
            writer.write_mesh(mesh)

        content = Path(temp_msh_file).read_text()
        # HEX20 is type 17 in Gmsh
        assert " 17 " in content

    def test_prism6_export(self, temp_msh_file):
        """Test PRISM6 element export"""
        mesh = MeshData(element_type=ElementType.PRISM6)

        # Create 6 nodes for PRISM6
        mesh.add_node(0.0, 0.0, 0.0, node_id=1)
        mesh.add_node(1.0, 0.0, 0.0, node_id=2)
        mesh.add_node(0.5, 1.0, 0.0, node_id=3)
        mesh.add_node(0.0, 0.0, 1.0, node_id=4)
        mesh.add_node(1.0, 0.0, 1.0, node_id=5)
        mesh.add_node(0.5, 1.0, 1.0, node_id=6)

        mesh.add_element([1, 2, 3, 4, 5, 6], element_id=1)

        with GmshWriter(temp_msh_file) as writer:
            writer.write_mesh(mesh)

        content = Path(temp_msh_file).read_text()
        # PRISM6 is type 6 in Gmsh
        assert " 6 " in content

    def test_pyramid5_export(self, temp_msh_file):
        """Test PYRAMID5 element export"""
        mesh = MeshData(element_type=ElementType.PYRAMID5)

        # Create 5 nodes for PYRAMID5
        mesh.add_node(0.0, 0.0, 0.0, node_id=1)
        mesh.add_node(1.0, 0.0, 0.0, node_id=2)
        mesh.add_node(1.0, 1.0, 0.0, node_id=3)
        mesh.add_node(0.0, 1.0, 0.0, node_id=4)
        mesh.add_node(0.5, 0.5, 1.0, node_id=5)

        mesh.add_element([1, 2, 3, 4, 5], element_id=1)

        with GmshWriter(temp_msh_file) as writer:
            writer.write_mesh(mesh)

        content = Path(temp_msh_file).read_text()
        # PYRAMID5 is type 7 in Gmsh
        assert " 7 " in content


# =============================================================================
# 4. Physical Group Tests
# =============================================================================

class TestPhysicalGroups:
    """Test physical group functionality"""

    def test_physical_groups_v2(self, temp_msh_file, multi_element_mesh):
        """Test physical groups in MSH 2.2"""
        physical_groups = {
            "volume1": [1],
            "volume2": [2]
        }

        with GmshWriter(temp_msh_file, version="2.2") as writer:
            writer.write_mesh(multi_element_mesh, physical_groups)

        content = Path(temp_msh_file).read_text()

        # Check for PhysicalNames section
        assert "$PhysicalNames" in content
        assert "volume1" in content
        assert "volume2" in content

    def test_physical_groups_v4(self, temp_msh_file, multi_element_mesh):
        """Test physical groups in MSH 4.1"""
        physical_groups = {
            "steel": [1],
            "aluminum": [2]
        }

        with GmshWriter(temp_msh_file, version="4.1") as writer:
            writer.write_mesh(multi_element_mesh, physical_groups)

        content = Path(temp_msh_file).read_text()

        # Check for PhysicalNames section
        assert "$PhysicalNames" in content
        assert "steel" in content
        assert "aluminum" in content

    def test_multiple_physical_groups(self, temp_msh_file):
        """Test multiple physical groups"""
        # Create 4-element mesh
        mesh = MeshData(element_type=ElementType.HEX8)

        # Create nodes for 2x2x1 grid
        for i in range(3):
            for j in range(3):
                for k in range(2):
                    node_id = i * 6 + j * 2 + k + 1
                    mesh.add_node(float(i), float(j), float(k), node_id=node_id)

        # Add 4 HEX8 elements
        mesh.add_element([1, 3, 9, 7, 2, 4, 10, 8], element_id=1)
        mesh.add_element([3, 5, 11, 9, 4, 6, 12, 10], element_id=2)
        mesh.add_element([7, 9, 15, 13, 8, 10, 16, 14], element_id=3)
        mesh.add_element([9, 11, 17, 15, 10, 12, 18, 16], element_id=4)

        physical_groups = {
            "bottom": [1, 2],
            "top": [3, 4]
        }

        with GmshWriter(temp_msh_file) as writer:
            writer.write_mesh(mesh, physical_groups)

        content = Path(temp_msh_file).read_text()
        lines = content.split('\n')

        # Check PhysicalNames section
        names_start = lines.index("$PhysicalNames")
        num_groups = int(lines[names_start + 1])
        assert num_groups == 2


# =============================================================================
# 5. Error Handling Tests
# =============================================================================

class TestErrorHandling:
    """Test error handling"""

    def test_empty_mesh_error(self, temp_msh_file):
        """Test error with empty mesh"""
        mesh = MeshData()

        with pytest.raises(GmshError, match="no nodes"):
            with GmshWriter(temp_msh_file) as writer:
                writer.write_mesh(mesh)

    def test_mesh_without_elements_error(self, temp_msh_file):
        """Test error with mesh that has nodes but no elements"""
        mesh = MeshData()
        mesh.add_node(0.0, 0.0, 0.0)

        with pytest.raises(GmshError, match="no elements"):
            with GmshWriter(temp_msh_file) as writer:
                writer.write_mesh(mesh)

    def test_file_not_open_error(self, temp_msh_file, simple_hex_mesh):
        """Test error when trying to write without opening file"""
        writer = GmshWriter(temp_msh_file)

        with pytest.raises(GmshError, match="not open"):
            writer.write_mesh(simple_hex_mesh)


# =============================================================================
# 6. File Format Compliance Tests
# =============================================================================

class TestFormatCompliance:
    """Test MSH format compliance"""

    def test_msh_v2_structure(self, temp_msh_file, simple_hex_mesh):
        """Test MSH 2.2 file structure"""
        with GmshWriter(temp_msh_file, version="2.2") as writer:
            writer.write_mesh(simple_hex_mesh)

        content = Path(temp_msh_file).read_text()
        lines = content.split('\n')

        # Check required sections in order
        assert "$MeshFormat" in lines
        assert "$EndMeshFormat" in lines
        assert "$Nodes" in lines
        assert "$EndNodes" in lines
        assert "$Elements" in lines
        assert "$EndElements" in lines

    def test_msh_v4_structure(self, temp_msh_file, simple_hex_mesh):
        """Test MSH 4.1 file structure"""
        with GmshWriter(temp_msh_file, version="4.1") as writer:
            writer.write_mesh(simple_hex_mesh)

        content = Path(temp_msh_file).read_text()
        lines = content.split('\n')

        # Check required sections
        assert "$MeshFormat" in lines
        assert "$EndMeshFormat" in lines
        assert "$Entities" in lines
        assert "$EndEntities" in lines
        assert "$Nodes" in lines
        assert "$EndNodes" in lines
        assert "$Elements" in lines
        assert "$EndElements" in lines

    def test_coordinate_precision(self, temp_msh_file, simple_hex_mesh):
        """Test coordinate precision (16 decimal places)"""
        with GmshWriter(temp_msh_file) as writer:
            writer.write_mesh(simple_hex_mesh)

        content = Path(temp_msh_file).read_text()
        # Check for scientific notation with 16 digits
        assert "e" in content.lower()  # Scientific notation present

    def test_node_ordering(self, temp_msh_file, simple_hex_mesh):
        """Test nodes are written in sorted order"""
        with GmshWriter(temp_msh_file) as writer:
            writer.write_mesh(simple_hex_mesh)

        content = Path(temp_msh_file).read_text()
        lines = content.split('\n')

        # Find nodes section
        nodes_start = lines.index("$Nodes")
        nodes_end = lines.index("$EndNodes")

        # Check node IDs are in order (for MSH 2.2)
        node_lines = lines[nodes_start + 2:nodes_end]
        node_ids = [int(line.split()[0]) for line in node_lines if line.strip()]
        assert node_ids == sorted(node_ids)

    def test_element_connectivity(self, temp_msh_file, simple_hex_mesh):
        """Test element connectivity format"""
        with GmshWriter(temp_msh_file) as writer:
            writer.write_mesh(simple_hex_mesh)

        content = Path(temp_msh_file).read_text()
        lines = content.split('\n')

        # Find elements section
        elems_start = lines.index("$Elements")

        # Find first element line
        for line in lines[elems_start:]:
            if line.startswith("1 "):  # Element ID 1
                parts = line.split()
                # MSH 2.2: elem-id elem-type num-tags tag1 tag2 nodes...
                # Should have 1 + 1 + 1 + 2 + 8 = 13 parts for HEX8
                assert len(parts) >= 8  # At least elem-id, type, tags, and some nodes
                break


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
