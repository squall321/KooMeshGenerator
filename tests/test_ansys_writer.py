"""
Tests for ANSYS export functionality
"""

import pytest
from pathlib import Path
import tempfile

from koomesh.meshing.mesh_data import MeshData, ElementType, Node, Element
from koomesh.export.ansys_writer import ANSYSWriter


@pytest.fixture
def temp_dir():
    """Create temporary directory for test outputs"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def simple_hex8_mesh():
    """Create a simple HEX8 mesh with 2 elements"""
    mesh = MeshData(element_type=ElementType.HEX8)

    # Create 12 nodes for 2 hex elements
    mesh.nodes[1] = Node(1, 0.0, 0.0, 0.0)
    mesh.nodes[2] = Node(2, 1.0, 0.0, 0.0)
    mesh.nodes[3] = Node(3, 1.0, 1.0, 0.0)
    mesh.nodes[4] = Node(4, 0.0, 1.0, 0.0)
    mesh.nodes[5] = Node(5, 0.0, 0.0, 1.0)
    mesh.nodes[6] = Node(6, 1.0, 0.0, 1.0)
    mesh.nodes[7] = Node(7, 1.0, 1.0, 1.0)
    mesh.nodes[8] = Node(8, 0.0, 1.0, 1.0)
    mesh.nodes[9] = Node(9, 2.0, 0.0, 0.0)
    mesh.nodes[10] = Node(10, 2.0, 1.0, 0.0)
    mesh.nodes[11] = Node(11, 2.0, 0.0, 1.0)
    mesh.nodes[12] = Node(12, 2.0, 1.0, 1.0)

    mesh.elements[1] = Element(1, ElementType.HEX8, [1, 2, 3, 4, 5, 6, 7, 8])
    mesh.elements[2] = Element(2, ElementType.HEX8, [2, 9, 10, 3, 6, 11, 12, 7])

    return mesh


@pytest.fixture
def simple_tet4_mesh():
    """Create a simple TET4 mesh with 2 elements"""
    mesh = MeshData(element_type=ElementType.TET4)

    mesh.nodes[1] = Node(1, 0.0, 0.0, 0.0)
    mesh.nodes[2] = Node(2, 1.0, 0.0, 0.0)
    mesh.nodes[3] = Node(3, 0.5, 1.0, 0.0)
    mesh.nodes[4] = Node(4, 0.5, 0.5, 1.0)
    mesh.nodes[5] = Node(5, 1.5, 0.5, 0.5)

    mesh.elements[1] = Element(1, ElementType.TET4, [1, 2, 3, 4])
    mesh.elements[2] = Element(2, ElementType.TET4, [2, 5, 3, 4])

    return mesh


@pytest.fixture
def hex20_mesh():
    """Create a simple HEX20 mesh with 1 element"""
    mesh = MeshData(element_type=ElementType.HEX20)

    # 8 corner nodes
    for i in range(8):
        x = float(i % 2)
        y = float((i // 2) % 2)
        z = float(i // 4)
        mesh.nodes[i+1] = Node(i+1, x, y, z)

    # 12 mid-edge nodes
    mid_edges = [
        (0.5, 0.0, 0.0), (1.0, 0.5, 0.0), (0.5, 1.0, 0.0), (0.0, 0.5, 0.0),
        (0.5, 0.0, 1.0), (1.0, 0.5, 1.0), (0.5, 1.0, 1.0), (0.0, 0.5, 1.0),
        (0.0, 0.0, 0.5), (1.0, 0.0, 0.5), (1.0, 1.0, 0.5), (0.0, 1.0, 0.5)
    ]

    for i, (x, y, z) in enumerate(mid_edges, start=9):
        mesh.nodes[i] = Node(i, x, y, z)

    node_ids = list(range(1, 21))
    mesh.elements[1] = Element(1, ElementType.HEX20, node_ids)

    return mesh


class TestANSYSWriterInitialization:
    """Test ANSYSWriter initialization"""

    def test_init_default(self, temp_dir):
        """Test default initialization"""
        output_path = temp_dir / "test.cdb"
        writer = ANSYSWriter(str(output_path))

        assert writer.output_path == output_path
        assert writer.precision == 13

    def test_init_custom(self, temp_dir):
        """Test custom initialization"""
        output_path = temp_dir / "test.cdb"
        writer = ANSYSWriter(str(output_path), precision=10)

        assert writer.precision == 10

    def test_context_manager(self, temp_dir):
        """Test context manager functionality"""
        output_path = temp_dir / "test.cdb"

        with ANSYSWriter(str(output_path)) as writer:
            assert writer.file is not None
            writer.write_header("Test Model")

        assert writer.file.closed
        assert output_path.exists()


class TestANSYSHeaderAndNodes:
    """Test header and node writing"""

    def test_write_header(self, temp_dir):
        """Test header writing"""
        output_path = temp_dir / "test.cdb"

        with ANSYSWriter(str(output_path)) as writer:
            writer.write_header("My Test Model", comments=["Test comment 1", "Test comment 2"])

        content = output_path.read_text()
        assert "/PREP7" in content
        assert "My Test Model" in content
        assert "KooMeshGenerator" in content
        assert "/COM,  Test comment 1" in content
        assert "/COM,  Test comment 2" in content

    def test_write_nodes_hex8(self, temp_dir, simple_hex8_mesh):
        """Test node writing for HEX8 mesh"""
        output_path = temp_dir / "test.cdb"

        with ANSYSWriter(str(output_path)) as writer:
            writer.write_nodes(simple_hex8_mesh)

        content = output_path.read_text()
        assert "NBLOCK" in content
        assert "N,R5.3,LOC,       -1," in content  # NBLOCK terminator
        # Check that nodes are present - ANSYS format has 9 chars for node ID
        lines = content.split('\n')
        # Node lines are between NBLOCK and terminator
        in_nblock = False
        node_count = 0
        for line in lines:
            if "NBLOCK" in line:
                in_nblock = True
                continue
            if "N,R5.3,LOC" in line:
                break
            if in_nblock and line.strip() and not line.startswith('('):
                node_count += 1
        assert node_count >= 12  # 12 nodes

    def test_node_format(self, temp_dir, simple_hex8_mesh):
        """Test node format (e20.13)"""
        output_path = temp_dir / "test.cdb"

        with ANSYSWriter(str(output_path)) as writer:
            writer.write_nodes(simple_hex8_mesh)

        content = output_path.read_text()
        # ANSYS uses scientific notation with e
        assert 'e' in content.lower()


class TestANSYSElements:
    """Test element writing for different element types"""

    def test_write_hex8_elements(self, temp_dir, simple_hex8_mesh):
        """Test HEX8 element writing"""
        output_path = temp_dir / "test.cdb"

        with ANSYSWriter(str(output_path)) as writer:
            writer.write_element_types(simple_hex8_mesh, et_id=1)
            writer.write_elements(simple_hex8_mesh, et_id=1, mat_id=1)

        content = output_path.read_text()
        assert "ET,1,185" in content  # SOLID185
        assert "EBLOCK" in content
        assert "        -1" in content  # EBLOCK terminator

    def test_write_tet4_elements(self, temp_dir, simple_tet4_mesh):
        """Test TET4 element writing"""
        output_path = temp_dir / "test.cdb"

        with ANSYSWriter(str(output_path)) as writer:
            writer.write_element_types(simple_tet4_mesh, et_id=1)
            writer.write_elements(simple_tet4_mesh, et_id=1, mat_id=1)

        content = output_path.read_text()
        assert "ET,1,285" in content  # SOLID285
        assert "EBLOCK" in content

    def test_write_hex20_elements(self, temp_dir, hex20_mesh):
        """Test HEX20 element writing"""
        output_path = temp_dir / "test.cdb"

        with ANSYSWriter(str(output_path)) as writer:
            writer.write_element_types(hex20_mesh, et_id=1)
            writer.write_elements(hex20_mesh, et_id=1, mat_id=1)

        content = output_path.read_text()
        assert "ET,1,186" in content  # SOLID186
        assert "EBLOCK" in content

    def test_element_type_mapping(self):
        """Test element type mapping to ANSYS types"""
        from koomesh.export.ansys_writer import ANSYSWriter

        assert ANSYSWriter.ELEMENT_TYPE_MAP[ElementType.HEX8] == 185
        assert ANSYSWriter.ELEMENT_TYPE_MAP[ElementType.HEX20] == 186
        assert ANSYSWriter.ELEMENT_TYPE_MAP[ElementType.HEX27] == 186
        assert ANSYSWriter.ELEMENT_TYPE_MAP[ElementType.TET4] == 285
        assert ANSYSWriter.ELEMENT_TYPE_MAP[ElementType.TET10] == 187
        assert ANSYSWriter.ELEMENT_TYPE_MAP[ElementType.PRISM6] == 185
        assert ANSYSWriter.ELEMENT_TYPE_MAP[ElementType.PYRAMID5] == 185


class TestANSYSComponents:
    """Test component writing"""

    def test_write_node_component(self, temp_dir, simple_hex8_mesh):
        """Test node component writing"""
        output_path = temp_dir / "test.cdb"

        with ANSYSWriter(str(output_path)) as writer:
            writer.write_component("BOTTOM_NODES", "NODE", [1, 2, 3, 4])

        content = output_path.read_text()
        assert "CMBLOCK,BOTTOM_NODES,NODE,4" in content

    def test_write_element_component(self, temp_dir, simple_hex8_mesh):
        """Test element component writing"""
        output_path = temp_dir / "test.cdb"

        with ANSYSWriter(str(output_path)) as writer:
            writer.write_component("ALL_ELEMS", "ELEM", [1, 2])

        content = output_path.read_text()
        assert "CMBLOCK,ALL_ELEMS,ELEM,2" in content

    def test_duplicate_component_warning(self, temp_dir, simple_hex8_mesh):
        """Test warning when writing duplicate components"""
        output_path = temp_dir / "test.cdb"

        with ANSYSWriter(str(output_path)) as writer:
            writer.write_component("COMP1", "NODE", [1, 2])
            writer.write_component("COMP1", "NODE", [3, 4])  # Should warn

        content = output_path.read_text()
        # Should only appear once
        count = content.count("CMBLOCK,COMP1,NODE")
        assert count == 1


class TestANSYSMaterial:
    """Test material writing"""

    def test_write_material_full(self, temp_dir):
        """Test material writing with all properties"""
        output_path = temp_dir / "test.cdb"

        with ANSYSWriter(str(output_path)) as writer:
            writer.write_material("STEEL", mat_id=1, youngs=210000.0, poisson=0.3, density=7.85e-9)

        content = output_path.read_text()
        assert "/COM,  Material 1: STEEL" in content
        assert "MPDATA,EX,1,1,2.100000e+05" in content
        assert "MPDATA,PRXY,1,1,3.000000e-01" in content
        assert "MPDATA,DENS,1,1,7.850000e-09" in content

    def test_write_material_elastic_only(self, temp_dir):
        """Test material writing with elastic properties only"""
        output_path = temp_dir / "test.cdb"

        with ANSYSWriter(str(output_path)) as writer:
            writer.write_material("ALUMINUM", mat_id=2, youngs=70000.0, poisson=0.33)

        content = output_path.read_text()
        assert "/COM,  Material 2: ALUMINUM" in content
        assert "MPDATA,EX,2,1,7.000000e+04" in content
        assert "MPDATA,PRXY,2,1,3.300000e-01" in content
        assert "MPDATA,DENS" not in content

    def test_write_material_with_comments(self, temp_dir):
        """Test material writing with comments"""
        output_path = temp_dir / "test.cdb"

        with ANSYSWriter(str(output_path)) as writer:
            writer.write_material(
                "STEEL",
                mat_id=1,
                youngs=210000.0,
                poisson=0.3,
                comments=["Grade: AISI 1045", "Temperature: 20C"]
            )

        content = output_path.read_text()
        assert "/COM,  Grade: AISI 1045" in content
        assert "/COM,  Temperature: 20C" in content


class TestANSYSCompleteModel:
    """Test complete model export"""

    def test_write_complete_model_minimal(self, temp_dir, simple_hex8_mesh):
        """Test complete model export with minimal options"""
        output_path = temp_dir / "complete.cdb"

        with ANSYSWriter(str(output_path)) as writer:
            writer.write_complete_model(simple_hex8_mesh, title="Test Model")

        content = output_path.read_text()
        assert "/PREP7" in content
        assert "Test Model" in content
        assert "NBLOCK" in content
        assert "EBLOCK" in content
        assert "FINISH" in content

    def test_write_complete_model_with_material(self, temp_dir, simple_hex8_mesh):
        """Test complete model export with material properties"""
        output_path = temp_dir / "complete.cdb"

        with ANSYSWriter(str(output_path)) as writer:
            writer.write_complete_model(
                simple_hex8_mesh,
                title="Steel Model",
                material_name="STEEL",
                et_id=1,
                mat_id=1,
                youngs=210000.0,
                poisson=0.3,
                density=7.85e-9
            )

        content = output_path.read_text()
        assert "/COM,  Material 1: STEEL" in content
        assert "MPDATA,EX" in content
        assert "MPDATA,PRXY" in content
        assert "MPDATA,DENS" in content

    def test_complete_workflow(self, temp_dir, simple_hex8_mesh):
        """Test complete workflow with all features"""
        output_path = temp_dir / "workflow.cdb"

        with ANSYSWriter(str(output_path)) as writer:
            # Header
            writer.write_header("Complete Workflow Test")

            # Element types
            writer.write_element_types(simple_hex8_mesh, et_id=1)

            # Nodes
            writer.write_nodes(simple_hex8_mesh)

            # Elements
            writer.write_elements(simple_hex8_mesh, et_id=1, mat_id=1)

            # Components
            writer.write_component("BOTTOM_NODES", "NODE", [1, 2, 3, 4])
            writer.write_component("TOP_NODES", "NODE", [5, 6, 7, 8])
            writer.write_component("ALL_ELEMS", "ELEM", [1, 2])

            # Material
            writer.write_material("STEEL", mat_id=1, youngs=210000.0, poisson=0.3, density=7.85e-9)

        # Verify all sections are present
        content = output_path.read_text()
        assert "/PREP7" in content
        assert "ET,1,185" in content
        assert "NBLOCK" in content
        assert "EBLOCK" in content
        assert "CMBLOCK,BOTTOM_NODES,NODE" in content
        assert "CMBLOCK,TOP_NODES,NODE" in content
        assert "CMBLOCK,ALL_ELEMS,ELEM" in content
        assert "MPDATA,EX,1,1" in content


class TestANSYSFileFormat:
    """Test ANSYS file format compliance"""

    def test_precision_control(self, temp_dir, simple_hex8_mesh):
        """Test precision control in output"""
        output_path = temp_dir / "precision.cdb"

        with ANSYSWriter(str(output_path), precision=10) as writer:
            writer.write_nodes(simple_hex8_mesh)

        content = output_path.read_text()
        # Check that numbers are in scientific notation
        assert 'e' in content.lower() or 'E' in content

    def test_eblock_format(self, temp_dir, simple_hex8_mesh):
        """Test EBLOCK format with 19 integer fields"""
        output_path = temp_dir / "format.cdb"

        with ANSYSWriter(str(output_path)) as writer:
            writer.write_elements(simple_hex8_mesh, et_id=1, mat_id=1)

        content = output_path.read_text()
        assert "EBLOCK,19,SOLID" in content
        assert "(19i9)" in content
        assert "        -1" in content  # Terminator

    def test_nblock_format(self, temp_dir, simple_hex8_mesh):
        """Test NBLOCK format"""
        output_path = temp_dir / "format.cdb"

        with ANSYSWriter(str(output_path)) as writer:
            writer.write_nodes(simple_hex8_mesh)

        content = output_path.read_text()
        assert "NBLOCK,6,SOLID" in content
        assert "(1i9,3e20.13)" in content
        assert "N,R5.3,LOC,       -1," in content  # Terminator

    def test_commands_present(self, temp_dir, simple_hex8_mesh):
        """Test that all major ANSYS commands are present"""
        output_path = temp_dir / "commands.cdb"

        with ANSYSWriter(str(output_path)) as writer:
            writer.write_complete_model(
                simple_hex8_mesh,
                title="Test",
                youngs=210000.0,
                poisson=0.3
            )

        content = output_path.read_text()
        # Check for major ANSYS commands
        assert "/PREP7" in content
        assert "/COM," in content
        assert "ET," in content
        assert "NBLOCK" in content
        assert "EBLOCK" in content
        assert "MPDATA" in content
        assert "FINISH" in content
