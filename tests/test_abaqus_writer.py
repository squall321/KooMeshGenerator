"""
Tests for ABAQUS export functionality
"""

import pytest
from pathlib import Path
import tempfile

from koomesh.meshing.mesh_data import MeshData, ElementType, Node, Element
from koomesh.export.abaqus_writer import AbaqusWriter


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
    # First element: nodes 1-8
    mesh.nodes[1] = Node(1, 0.0, 0.0, 0.0)
    mesh.nodes[2] = Node(2, 1.0, 0.0, 0.0)
    mesh.nodes[3] = Node(3, 1.0, 1.0, 0.0)
    mesh.nodes[4] = Node(4, 0.0, 1.0, 0.0)
    mesh.nodes[5] = Node(5, 0.0, 0.0, 1.0)
    mesh.nodes[6] = Node(6, 1.0, 0.0, 1.0)
    mesh.nodes[7] = Node(7, 1.0, 1.0, 1.0)
    mesh.nodes[8] = Node(8, 0.0, 1.0, 1.0)

    # Second element: nodes 2,3,6,7,9,10,11,12
    mesh.nodes[9] = Node(9, 2.0, 0.0, 0.0)
    mesh.nodes[10] = Node(10, 2.0, 1.0, 0.0)
    mesh.nodes[11] = Node(11, 2.0, 0.0, 1.0)
    mesh.nodes[12] = Node(12, 2.0, 1.0, 1.0)

    # Create elements
    mesh.elements[1] = Element(1, ElementType.HEX8, [1, 2, 3, 4, 5, 6, 7, 8])
    mesh.elements[2] = Element(2, ElementType.HEX8, [2, 9, 10, 3, 6, 11, 12, 7])

    return mesh


@pytest.fixture
def simple_tet4_mesh():
    """Create a simple TET4 mesh with 2 elements"""
    mesh = MeshData(element_type=ElementType.TET4)

    # Create nodes
    mesh.nodes[1] = Node(1, 0.0, 0.0, 0.0)
    mesh.nodes[2] = Node(2, 1.0, 0.0, 0.0)
    mesh.nodes[3] = Node(3, 0.5, 1.0, 0.0)
    mesh.nodes[4] = Node(4, 0.5, 0.5, 1.0)
    mesh.nodes[5] = Node(5, 1.5, 0.5, 0.5)

    # Create elements
    mesh.elements[1] = Element(1, ElementType.TET4, [1, 2, 3, 4])
    mesh.elements[2] = Element(2, ElementType.TET4, [2, 5, 3, 4])

    return mesh


@pytest.fixture
def hex20_mesh():
    """Create a simple HEX20 mesh with 1 element"""
    mesh = MeshData(element_type=ElementType.HEX20)

    # 8 corner nodes
    mesh.nodes[1] = Node(1, 0.0, 0.0, 0.0)
    mesh.nodes[2] = Node(2, 1.0, 0.0, 0.0)
    mesh.nodes[3] = Node(3, 1.0, 1.0, 0.0)
    mesh.nodes[4] = Node(4, 0.0, 1.0, 0.0)
    mesh.nodes[5] = Node(5, 0.0, 0.0, 1.0)
    mesh.nodes[6] = Node(6, 1.0, 0.0, 1.0)
    mesh.nodes[7] = Node(7, 1.0, 1.0, 1.0)
    mesh.nodes[8] = Node(8, 0.0, 1.0, 1.0)

    # 12 mid-edge nodes (9-20)
    mesh.nodes[9] = Node(9, 0.5, 0.0, 0.0)
    mesh.nodes[10] = Node(10, 1.0, 0.5, 0.0)
    mesh.nodes[11] = Node(11, 0.5, 1.0, 0.0)
    mesh.nodes[12] = Node(12, 0.0, 0.5, 0.0)
    mesh.nodes[13] = Node(13, 0.5, 0.0, 1.0)
    mesh.nodes[14] = Node(14, 1.0, 0.5, 1.0)
    mesh.nodes[15] = Node(15, 0.5, 1.0, 1.0)
    mesh.nodes[16] = Node(16, 0.0, 0.5, 1.0)
    mesh.nodes[17] = Node(17, 0.0, 0.0, 0.5)
    mesh.nodes[18] = Node(18, 1.0, 0.0, 0.5)
    mesh.nodes[19] = Node(19, 1.0, 1.0, 0.5)
    mesh.nodes[20] = Node(20, 0.0, 1.0, 0.5)

    # Create element with all 20 nodes
    node_ids = list(range(1, 21))
    mesh.elements[1] = Element(1, ElementType.HEX20, node_ids)

    return mesh


class TestAbaqusWriterInitialization:
    """Test AbaqusWriter initialization"""

    def test_init_default(self, temp_dir):
        """Test default initialization"""
        output_path = temp_dir / "test.inp"
        writer = AbaqusWriter(str(output_path))

        assert writer.output_path == output_path
        assert writer.precision == 8
        assert writer.reduced_integration == False

    def test_init_custom(self, temp_dir):
        """Test custom initialization"""
        output_path = temp_dir / "test.inp"
        writer = AbaqusWriter(str(output_path), precision=10, reduced_integration=True)

        assert writer.precision == 10
        assert writer.reduced_integration == True

    def test_context_manager(self, temp_dir):
        """Test context manager functionality"""
        output_path = temp_dir / "test.inp"

        with AbaqusWriter(str(output_path)) as writer:
            assert writer.file is not None
            writer.write_header("Test Model")

        # File should be closed after context
        assert writer.file.closed
        assert output_path.exists()


class TestAbaqusHeaderAndNodes:
    """Test header and node writing"""

    def test_write_header(self, temp_dir):
        """Test header writing"""
        output_path = temp_dir / "test.inp"

        with AbaqusWriter(str(output_path)) as writer:
            writer.write_header("My Test Model", comments=["Test comment 1", "Test comment 2"])

        content = output_path.read_text()
        assert "*HEADING" in content
        assert "My Test Model" in content
        assert "KooMeshGenerator" in content
        assert "** Test comment 1" in content
        assert "** Test comment 2" in content

    def test_write_nodes_hex8(self, temp_dir, simple_hex8_mesh):
        """Test node writing for HEX8 mesh"""
        output_path = temp_dir / "test.inp"

        with AbaqusWriter(str(output_path), precision=6) as writer:
            writer.write_nodes(simple_hex8_mesh)

        content = output_path.read_text()
        assert "*NODE" in content
        assert "1," in content  # Node 1
        assert "12," in content  # Node 12
        # Check format (precision=6)
        lines = content.split('\n')
        node_lines = [l for l in lines if l and not l.startswith('*')]
        assert len(node_lines) == 12  # 12 nodes

    def test_write_nodes_with_set(self, temp_dir, simple_hex8_mesh):
        """Test node writing with automatic set creation"""
        output_path = temp_dir / "test.inp"

        with AbaqusWriter(str(output_path)) as writer:
            writer.write_nodes(simple_hex8_mesh, node_set="ALL_NODES")

        content = output_path.read_text()
        assert "*NODE" in content
        assert "*NSET, NSET=ALL_NODES" in content


class TestAbaqusElements:
    """Test element writing for different element types"""

    def test_write_hex8_elements(self, temp_dir, simple_hex8_mesh):
        """Test HEX8 element writing"""
        output_path = temp_dir / "test.inp"

        with AbaqusWriter(str(output_path)) as writer:
            writer.write_elements(simple_hex8_mesh, "ELSET1")

        content = output_path.read_text()
        assert "*ELEMENT, TYPE=C3D8, ELSET=ELSET1" in content
        assert "1, 1, 2, 3, 4, 5, 6, 7, 8" in content
        assert "2, 2, 9, 10, 3, 6, 11, 12, 7" in content

    def test_write_hex8r_elements(self, temp_dir, simple_hex8_mesh):
        """Test HEX8R (reduced integration) element writing"""
        output_path = temp_dir / "test.inp"

        with AbaqusWriter(str(output_path), reduced_integration=True) as writer:
            writer.write_elements(simple_hex8_mesh, "ELSET1")

        content = output_path.read_text()
        assert "*ELEMENT, TYPE=C3D8R, ELSET=ELSET1" in content

    def test_write_tet4_elements(self, temp_dir, simple_tet4_mesh):
        """Test TET4 element writing"""
        output_path = temp_dir / "test.inp"

        with AbaqusWriter(str(output_path)) as writer:
            writer.write_elements(simple_tet4_mesh, "TETS")

        content = output_path.read_text()
        assert "*ELEMENT, TYPE=C3D4, ELSET=TETS" in content
        assert "1, 1, 2, 3, 4" in content
        assert "2, 2, 5, 3, 4" in content

    def test_write_hex20_elements(self, temp_dir, hex20_mesh):
        """Test HEX20 element writing (multi-line)"""
        output_path = temp_dir / "test.inp"

        with AbaqusWriter(str(output_path)) as writer:
            writer.write_elements(hex20_mesh, "HEX20S")

        content = output_path.read_text()
        assert "*ELEMENT, TYPE=C3D20, ELSET=HEX20S" in content
        # HEX20 should span multiple lines
        lines = content.split('\n')
        # Find element lines (should be 2 lines for HEX20: first with corners, second with edges)
        elem_lines = [l for l in lines if l and not l.startswith('*') and '1,' in l]
        assert len(elem_lines) >= 1  # At least the first line

    def test_write_prism6_elements(self, temp_dir):
        """Test PRISM6 element writing"""
        mesh = MeshData(element_type=ElementType.PRISM6)

        # Create 6 nodes for prism
        mesh.nodes[1] = Node(1, 0.0, 0.0, 0.0)
        mesh.nodes[2] = Node(2, 1.0, 0.0, 0.0)
        mesh.nodes[3] = Node(3, 0.5, 1.0, 0.0)
        mesh.nodes[4] = Node(4, 0.0, 0.0, 1.0)
        mesh.nodes[5] = Node(5, 1.0, 0.0, 1.0)
        mesh.nodes[6] = Node(6, 0.5, 1.0, 1.0)

        mesh.elements[1] = Element(1, ElementType.PRISM6, [1, 2, 3, 4, 5, 6])

        output_path = temp_dir / "test.inp"

        with AbaqusWriter(str(output_path)) as writer:
            writer.write_elements(mesh, "PRISMS")

        content = output_path.read_text()
        assert "*ELEMENT, TYPE=C3D6, ELSET=PRISMS" in content
        assert "1, 1, 2, 3, 4, 5, 6" in content

    def test_write_pyramid5_elements(self, temp_dir):
        """Test PYRAMID5 element writing"""
        mesh = MeshData(element_type=ElementType.PYRAMID5)

        # Create 5 nodes for pyramid
        mesh.nodes[1] = Node(1, 0.0, 0.0, 0.0)
        mesh.nodes[2] = Node(2, 1.0, 0.0, 0.0)
        mesh.nodes[3] = Node(3, 1.0, 1.0, 0.0)
        mesh.nodes[4] = Node(4, 0.0, 1.0, 0.0)
        mesh.nodes[5] = Node(5, 0.5, 0.5, 1.0)

        mesh.elements[1] = Element(1, ElementType.PYRAMID5, [1, 2, 3, 4, 5])

        output_path = temp_dir / "test.inp"

        with AbaqusWriter(str(output_path)) as writer:
            writer.write_elements(mesh, "PYRAMIDS")

        content = output_path.read_text()
        assert "*ELEMENT, TYPE=C3D5, ELSET=PYRAMIDS" in content
        assert "1, 1, 2, 3, 4, 5" in content


class TestAbaqusSetsAndSections:
    """Test set and section writing"""

    def test_write_node_set(self, temp_dir, simple_hex8_mesh):
        """Test node set writing"""
        output_path = temp_dir / "test.inp"

        with AbaqusWriter(str(output_path)) as writer:
            writer.write_node_set(simple_hex8_mesh, "BOTTOM_NODES", [1, 2, 3, 4])

        content = output_path.read_text()
        assert "*NSET, NSET=BOTTOM_NODES" in content
        assert "1, 2, 3, 4" in content

    def test_write_element_set(self, temp_dir, simple_hex8_mesh):
        """Test element set writing"""
        output_path = temp_dir / "test.inp"

        with AbaqusWriter(str(output_path)) as writer:
            writer.write_element_set(simple_hex8_mesh, "PART1", [1, 2])

        content = output_path.read_text()
        assert "*ELSET, ELSET=PART1" in content
        assert "1, 2" in content

    def test_write_large_set(self, temp_dir, simple_hex8_mesh):
        """Test writing large set (multi-line)"""
        output_path = temp_dir / "test.inp"

        # Create a large list of node IDs (more than 16, which triggers multi-line)
        large_list = list(range(1, 50))

        with AbaqusWriter(str(output_path)) as writer:
            writer.write_node_set(simple_hex8_mesh, "LARGE_SET", large_list)

        content = output_path.read_text()
        assert "*NSET, NSET=LARGE_SET" in content
        # Should have multiple lines (16 nodes per line)
        lines = [l for l in content.split('\n') if l.strip() and not l.startswith('*')]
        assert len(lines) >= 3  # At least 3 lines for 49 nodes

    def test_write_section(self, temp_dir):
        """Test section writing"""
        output_path = temp_dir / "test.inp"

        with AbaqusWriter(str(output_path)) as writer:
            writer.write_section("SEC1", "ALL_ELEMENTS", "STEEL")

        content = output_path.read_text()
        assert "*SOLID SECTION, ELSET=ALL_ELEMENTS, MATERIAL=STEEL" in content

    def test_duplicate_set_warning(self, temp_dir, simple_hex8_mesh):
        """Test warning when writing duplicate sets"""
        output_path = temp_dir / "test.inp"

        with AbaqusWriter(str(output_path)) as writer:
            writer.write_node_set(simple_hex8_mesh, "NODES1", [1, 2])
            # Try to write again - should log warning
            writer.write_node_set(simple_hex8_mesh, "NODES1", [3, 4])

        content = output_path.read_text()
        # Should only appear once
        count = content.count("*NSET, NSET=NODES1")
        assert count == 1


class TestAbaqusMaterial:
    """Test material writing"""

    def test_write_material_full(self, temp_dir):
        """Test material writing with all properties"""
        output_path = temp_dir / "test.inp"

        with AbaqusWriter(str(output_path), precision=6) as writer:
            writer.write_material("STEEL", youngs=210000.0, poisson=0.3, density=7.85e-9)

        content = output_path.read_text()
        assert "*MATERIAL, NAME=STEEL" in content
        assert "*DENSITY" in content
        assert "7.850000e-09" in content
        assert "*ELASTIC" in content
        assert "2.100000e+05, 3.000000e-01" in content

    def test_write_material_elastic_only(self, temp_dir):
        """Test material writing with elastic properties only"""
        output_path = temp_dir / "test.inp"

        with AbaqusWriter(str(output_path)) as writer:
            writer.write_material("ALUMINUM", youngs=70000.0, poisson=0.33)

        content = output_path.read_text()
        assert "*MATERIAL, NAME=ALUMINUM" in content
        assert "*ELASTIC" in content
        assert "*DENSITY" not in content

    def test_write_material_with_comments(self, temp_dir):
        """Test material writing with comments"""
        output_path = temp_dir / "test.inp"

        with AbaqusWriter(str(output_path)) as writer:
            writer.write_material(
                "STEEL",
                youngs=210000.0,
                poisson=0.3,
                comments=["Grade: AISI 1045", "Temperature: 20C"]
            )

        content = output_path.read_text()
        assert "** Grade: AISI 1045" in content
        assert "** Temperature: 20C" in content


class TestAbaqusContactAndSurface:
    """Test contact and surface writing"""

    def test_write_surface(self, temp_dir):
        """Test surface writing"""
        output_path = temp_dir / "test.inp"

        with AbaqusWriter(str(output_path)) as writer:
            writer.write_surface("SURF1", "ELSET1", "S1")

        content = output_path.read_text()
        assert "*SURFACE, NAME=SURF1, TYPE=ELEMENT" in content
        assert "ELSET1, S1" in content

    def test_write_tie_constraint(self, temp_dir):
        """Test tie constraint writing"""
        output_path = temp_dir / "test.inp"

        with AbaqusWriter(str(output_path)) as writer:
            writer.write_tie_constraint("TIE1", "MASTER_SURF", "SLAVE_SURF")

        content = output_path.read_text()
        assert "*TIE, NAME=TIE1" in content
        assert "SLAVE_SURF, MASTER_SURF" in content

    def test_write_contact_pair(self, temp_dir):
        """Test contact pair writing"""
        output_path = temp_dir / "test.inp"

        with AbaqusWriter(str(output_path)) as writer:
            writer.write_contact_pair("CONTACT1", "MASTER", "SLAVE", friction=0.3)

        content = output_path.read_text()
        assert "*CONTACT PAIR, INTERACTION=CONTACT1" in content
        assert "SLAVE, MASTER" in content
        assert "*SURFACE INTERACTION, NAME=CONTACT1" in content
        assert "*FRICTION" in content

    def test_write_contact_pair_no_friction(self, temp_dir):
        """Test contact pair without friction"""
        output_path = temp_dir / "test.inp"

        with AbaqusWriter(str(output_path)) as writer:
            writer.write_contact_pair("CONTACT2", "MASTER", "SLAVE")

        content = output_path.read_text()
        assert "*CONTACT PAIR, INTERACTION=CONTACT2" in content
        assert "*FRICTION" not in content


class TestAbaqusCompleteModel:
    """Test complete model export"""

    def test_write_complete_model_minimal(self, temp_dir, simple_hex8_mesh):
        """Test complete model export with minimal options"""
        output_path = temp_dir / "complete.inp"

        with AbaqusWriter(str(output_path)) as writer:
            writer.write_complete_model(simple_hex8_mesh, model_name="Test Model")

        content = output_path.read_text()
        assert "*HEADING" in content
        assert "Test Model" in content
        assert "*NODE" in content
        assert "*ELEMENT, TYPE=C3D8" in content
        assert "*SOLID SECTION" in content
        assert "End of input file" in content

    def test_write_complete_model_with_material(self, temp_dir, simple_hex8_mesh):
        """Test complete model export with material properties"""
        output_path = temp_dir / "complete.inp"

        with AbaqusWriter(str(output_path)) as writer:
            writer.write_complete_model(
                simple_hex8_mesh,
                model_name="Steel Model",
                material_name="STEEL",
                youngs=210000.0,
                poisson=0.3,
                density=7.85e-9
            )

        content = output_path.read_text()
        assert "*MATERIAL, NAME=STEEL" in content
        assert "*ELASTIC" in content
        assert "*DENSITY" in content

    def test_complete_workflow(self, temp_dir, simple_hex8_mesh):
        """Test complete workflow with all features"""
        output_path = temp_dir / "workflow.inp"

        with AbaqusWriter(str(output_path)) as writer:
            # Header
            writer.write_header("Complete Workflow Test")

            # Nodes
            writer.write_nodes(simple_hex8_mesh)

            # Elements
            writer.write_elements(simple_hex8_mesh, "PART1")

            # Sets
            writer.write_node_set(simple_hex8_mesh, "BOTTOM", [1, 2, 3, 4])
            writer.write_node_set(simple_hex8_mesh, "TOP", [5, 6, 7, 8])
            writer.write_element_set(simple_hex8_mesh, "ALL_ELEM", [1, 2])

            # Section and material
            writer.write_section("SEC1", "PART1", "STEEL")
            writer.write_material("STEEL", youngs=210000.0, poisson=0.3, density=7.85e-9)

            # Surface and contact
            writer.write_surface("BOTTOM_SURF", "PART1", "S1")
            writer.write_surface("TOP_SURF", "PART1", "S2")
            writer.write_tie_constraint("TIE1", "BOTTOM_SURF", "TOP_SURF")

        # Verify all sections are present
        content = output_path.read_text()
        assert "*HEADING" in content
        assert "*NODE" in content
        assert "*ELEMENT" in content
        assert "*NSET, NSET=BOTTOM" in content
        assert "*NSET, NSET=TOP" in content
        assert "*ELSET, ELSET=ALL_ELEM" in content
        assert "*SOLID SECTION" in content
        assert "*MATERIAL, NAME=STEEL" in content
        assert "*SURFACE, NAME=BOTTOM_SURF" in content
        assert "*TIE, NAME=TIE1" in content


class TestAbaqusFileFormat:
    """Test ABAQUS file format compliance"""

    def test_precision_control(self, temp_dir, simple_hex8_mesh):
        """Test precision control in output"""
        output_path = temp_dir / "precision.inp"

        # Test with precision=4
        with AbaqusWriter(str(output_path), precision=4) as writer:
            writer.write_nodes(simple_hex8_mesh)

        content = output_path.read_text()
        # Check that numbers have correct precision (4 decimal places in scientific notation)
        # Example: 1.0000e+00 (4 decimals)
        import re
        matches = re.findall(r'\d\.\d{4}e[+-]\d{2}', content)
        assert len(matches) > 0  # Should find numbers with 4 decimal places

    def test_line_format(self, temp_dir, simple_hex8_mesh):
        """Test that lines are properly formatted"""
        output_path = temp_dir / "format.inp"

        with AbaqusWriter(str(output_path)) as writer:
            writer.write_header("Test")
            writer.write_nodes(simple_hex8_mesh)
            writer.write_elements(simple_hex8_mesh, "ELSET1")

        content = output_path.read_text()
        lines = content.split('\n')

        # Check that keyword lines start with *
        keyword_lines = [l for l in lines if l.startswith('*')]
        assert len(keyword_lines) >= 3  # At least *HEADING, *NODE, *ELEMENT

        # Check that no lines are excessively long (ABAQUS limit is typically 256 chars)
        for line in lines:
            assert len(line) <= 256

    def test_element_type_mapping(self):
        """Test element type mapping to ABAQUS types"""
        from koomesh.export.abaqus_writer import AbaqusWriter

        # Test standard mapping
        assert AbaqusWriter.ELEMENT_TYPE_MAP[ElementType.HEX8] == "C3D8"
        assert AbaqusWriter.ELEMENT_TYPE_MAP[ElementType.HEX20] == "C3D20"
        assert AbaqusWriter.ELEMENT_TYPE_MAP[ElementType.HEX27] == "C3D27"
        assert AbaqusWriter.ELEMENT_TYPE_MAP[ElementType.TET4] == "C3D4"
        assert AbaqusWriter.ELEMENT_TYPE_MAP[ElementType.TET10] == "C3D10"
        assert AbaqusWriter.ELEMENT_TYPE_MAP[ElementType.PRISM6] == "C3D6"
        assert AbaqusWriter.ELEMENT_TYPE_MAP[ElementType.PYRAMID5] == "C3D5"

        # Test reduced integration mapping
        assert AbaqusWriter.ELEMENT_TYPE_MAP_R[ElementType.HEX8] == "C3D8R"
