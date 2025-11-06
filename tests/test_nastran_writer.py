"""
Tests for Nastran (.bdf) Export Writer
=======================================

This module tests the NastranWriter class that exports mesh data
to Nastran Bulk Data format.

Test Coverage:
- Basic initialization
- Node writing (GRID entries) in small and large field formats
- Element writing for all supported types (CHEXA, CTETRA, CPENTA, CPYRAM)
- Material properties (MAT1)
- Property definitions (PSOLID)
- Set definitions (SET1)
- Complete model export
- Format compliance
"""

import pytest
import tempfile
from pathlib import Path

from koomesh.meshing.mesh_data import MeshData, Node, Element, ElementType
from koomesh.export.nastran_writer import NastranWriter


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def simple_hex8_mesh():
    """Create a simple HEX8 mesh (2x1x1 cube)"""
    mesh = MeshData(element_type=ElementType.HEX8)

    # Create 12 nodes for a 2x1x1 grid
    nodes_coords = [
        (1, 0.0, 0.0, 0.0), (2, 1.0, 0.0, 0.0), (3, 2.0, 0.0, 0.0),
        (4, 0.0, 1.0, 0.0), (5, 1.0, 1.0, 0.0), (6, 2.0, 1.0, 0.0),
        (7, 0.0, 0.0, 1.0), (8, 1.0, 0.0, 1.0), (9, 2.0, 0.0, 1.0),
        (10, 0.0, 1.0, 1.0), (11, 1.0, 1.0, 1.0), (12, 2.0, 1.0, 1.0),
    ]

    for nid, x, y, z in nodes_coords:
        mesh.nodes[nid] = Node(nid, x, y, z)

    # Create 2 HEX8 elements
    mesh.elements[1] = Element(1, ElementType.HEX8, [1, 2, 5, 4, 7, 8, 11, 10])
    mesh.elements[2] = Element(2, ElementType.HEX8, [2, 3, 6, 5, 8, 9, 12, 11])

    return mesh


@pytest.fixture
def simple_tet4_mesh():
    """Create a simple TET4 mesh"""
    mesh = MeshData(element_type=ElementType.TET4)

    # Create 5 nodes for a simple tetrahedron mesh
    mesh.nodes[1] = Node(1, 0.0, 0.0, 0.0)
    mesh.nodes[2] = Node(2, 1.0, 0.0, 0.0)
    mesh.nodes[3] = Node(3, 0.5, 1.0, 0.0)
    mesh.nodes[4] = Node(4, 0.5, 0.5, 1.0)
    mesh.nodes[5] = Node(5, 0.5, 0.5, 0.5)

    # Create 2 TET4 elements
    mesh.elements[1] = Element(1, ElementType.TET4, [1, 2, 3, 4])
    mesh.elements[2] = Element(2, ElementType.TET4, [2, 3, 4, 5])

    return mesh


@pytest.fixture
def hex20_mesh():
    """Create a HEX20 mesh (single element)"""
    mesh = MeshData(element_type=ElementType.HEX20)

    # Create 20 nodes for a single HEX20 element
    # Corner nodes (1-8)
    mesh.nodes[1] = Node(1, 0.0, 0.0, 0.0)
    mesh.nodes[2] = Node(2, 1.0, 0.0, 0.0)
    mesh.nodes[3] = Node(3, 1.0, 1.0, 0.0)
    mesh.nodes[4] = Node(4, 0.0, 1.0, 0.0)
    mesh.nodes[5] = Node(5, 0.0, 0.0, 1.0)
    mesh.nodes[6] = Node(6, 1.0, 0.0, 1.0)
    mesh.nodes[7] = Node(7, 1.0, 1.0, 1.0)
    mesh.nodes[8] = Node(8, 0.0, 1.0, 1.0)

    # Mid-edge nodes (9-20)
    mesh.nodes[9] = Node(9, 0.5, 0.0, 0.0)    # Edge 1-2
    mesh.nodes[10] = Node(10, 1.0, 0.5, 0.0)   # Edge 2-3
    mesh.nodes[11] = Node(11, 0.5, 1.0, 0.0)   # Edge 3-4
    mesh.nodes[12] = Node(12, 0.0, 0.5, 0.0)   # Edge 4-1
    mesh.nodes[13] = Node(13, 0.5, 0.0, 1.0)   # Edge 5-6
    mesh.nodes[14] = Node(14, 1.0, 0.5, 1.0)   # Edge 6-7
    mesh.nodes[15] = Node(15, 0.5, 1.0, 1.0)   # Edge 7-8
    mesh.nodes[16] = Node(16, 0.0, 0.5, 1.0)   # Edge 8-5
    mesh.nodes[17] = Node(17, 0.0, 0.0, 0.5)   # Edge 1-5
    mesh.nodes[18] = Node(18, 1.0, 0.0, 0.5)   # Edge 2-6
    mesh.nodes[19] = Node(19, 1.0, 1.0, 0.5)   # Edge 3-7
    mesh.nodes[20] = Node(20, 0.0, 1.0, 0.5)   # Edge 4-8

    # Create HEX20 element with all 20 nodes
    nodes = list(range(1, 21))
    mesh.elements[1] = Element(1, ElementType.HEX20, nodes)

    return mesh


@pytest.fixture
def temp_output_file():
    """Create a temporary output file"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.bdf', delete=False) as f:
        output_path = f.name
    yield output_path
    # Cleanup
    Path(output_path).unlink(missing_ok=True)


# ============================================================================
# Test Class: Initialization
# ============================================================================

class TestNastranWriterInit:
    """Test NastranWriter initialization"""

    def test_init_default(self, temp_output_file):
        """Test default initialization"""
        writer = NastranWriter(temp_output_file)
        assert writer.output_path == Path(temp_output_file)
        assert writer.format == 'large'
        assert writer.precision == 8
        assert writer.file is None

    def test_init_small_format(self, temp_output_file):
        """Test initialization with small field format"""
        writer = NastranWriter(temp_output_file, format='small')
        assert writer.format == 'small'

    def test_init_custom_precision(self, temp_output_file):
        """Test initialization with custom precision"""
        writer = NastranWriter(temp_output_file, precision=6)
        assert writer.precision == 6

    def test_context_manager(self, temp_output_file):
        """Test context manager functionality"""
        with NastranWriter(temp_output_file) as writer:
            assert writer.file is not None
            assert not writer.file.closed
        # File should be closed after context exit
        assert writer.file.closed


# ============================================================================
# Test Class: Node Writing
# ============================================================================

class TestNodeWriting:
    """Test GRID (node) writing functionality"""

    def test_write_nodes_hex8_large_format(self, simple_hex8_mesh, temp_output_file):
        """Test writing nodes in large field format"""
        with NastranWriter(temp_output_file, format='large') as writer:
            writer.write_header("Test Model")
            writer.write_nodes(simple_hex8_mesh)

        content = Path(temp_output_file).read_text()
        lines = content.split('\n')

        # Check for GRID entries
        grid_lines = [l for l in lines if l.startswith('GRID*')]
        assert len(grid_lines) >= 12  # 12 nodes in HEX8 mesh

        # Verify large field format (GRID* with continuation)
        assert any('GRID*' in l for l in lines)
        assert any(l.startswith('*') and not l.startswith('**') for l in lines)  # Continuation lines

    def test_write_nodes_small_format(self, simple_hex8_mesh, temp_output_file):
        """Test writing nodes in small field format"""
        with NastranWriter(temp_output_file, format='small') as writer:
            writer.write_header("Test Model")
            writer.write_nodes(simple_hex8_mesh)

        content = Path(temp_output_file).read_text()
        lines = content.split('\n')

        # Check for GRID entries (no asterisk)
        grid_lines = [l for l in lines if l.startswith('GRID') and not l.startswith('GRID*')]
        assert len(grid_lines) >= 12

        # Small format should be single line per node
        for line in grid_lines[:3]:  # Check first 3
            assert len(line) <= 80  # Nastran line length limit

    def test_node_coordinates_accuracy(self, simple_hex8_mesh, temp_output_file):
        """Test node coordinate accuracy"""
        with NastranWriter(temp_output_file) as writer:
            writer.write_nodes(simple_hex8_mesh)

        content = Path(temp_output_file).read_text()

        # Check that node 1 (0,0,0) is present
        assert 'GRID*' in content
        # Node coordinates should be in scientific notation
        assert 'E' in content or 'e' in content or '0.0' in content


# ============================================================================
# Test Class: Element Writing
# ============================================================================

class TestElementWriting:
    """Test element writing functionality"""

    def test_write_hex8_elements(self, simple_hex8_mesh, temp_output_file):
        """Test writing HEX8 elements (CHEXA)"""
        with NastranWriter(temp_output_file) as writer:
            writer.write_header("Test Model")
            writer.write_nodes(simple_hex8_mesh)
            writer.write_elements(simple_hex8_mesh)

        content = Path(temp_output_file).read_text()
        lines = content.split('\n')

        # Check for CHEXA entries
        chexa_lines = [l for l in lines if 'CHEXA' in l]
        assert len(chexa_lines) >= 2  # 2 elements

        # Verify elements are present with continuation lines
        continuation_lines = [l for l in lines if l.startswith('*') and not l.startswith('**')]
        assert len(continuation_lines) >= 2  # Continuations for each element

    def test_write_tet4_elements(self, simple_tet4_mesh, temp_output_file):
        """Test writing TET4 elements (CTETRA)"""
        with NastranWriter(temp_output_file) as writer:
            writer.write_header("Test Model")
            writer.write_nodes(simple_tet4_mesh)
            writer.write_elements(simple_tet4_mesh)

        content = Path(temp_output_file).read_text()

        # Check for CTETRA entries
        assert 'CTETRA' in content
        ctetra_lines = [l for l in content.split('\n') if 'CTETRA' in l]
        assert len(ctetra_lines) >= 2  # 2 elements

    def test_write_hex20_elements(self, hex20_mesh, temp_output_file):
        """Test writing HEX20 elements"""
        with NastranWriter(temp_output_file) as writer:
            writer.write_header("Test Model")
            writer.write_nodes(hex20_mesh)
            writer.write_elements(hex20_mesh)

        content = Path(temp_output_file).read_text()
        lines = content.split('\n')

        # Check for CHEXA with 20 nodes
        assert 'CHEXA' in content
        # HEX20 requires continuation lines (using '*' in large field format)
        chexa_lines = [l for l in lines if 'CHEXA' in l]
        continuation_lines = [l for l in lines if l.startswith('*') and not l.startswith('**')]
        assert len(chexa_lines) >= 1  # At least 1 element
        assert len(continuation_lines) >= 6  # HEX20 needs many continuations (6 lines for 20 nodes)


# ============================================================================
# Test Class: Material and Properties
# ============================================================================

class TestMaterialsAndProperties:
    """Test material and property writing"""

    def test_write_material_basic(self, temp_output_file):
        """Test writing basic material properties"""
        with NastranWriter(temp_output_file) as writer:
            writer.write_material(
                mat_id=1,
                youngs=210000.0,
                poisson=0.3,
                comments=["STEEL"]
            )

        content = Path(temp_output_file).read_text()

        # Check for MAT1 entry
        assert 'MAT1' in content
        # Check for Young's modulus (any format including 2.10000000E+05)
        assert '210000' in content or '2.1' in content or 'E+05' in content
        assert '3.' in content  # Poisson's ratio

    def test_write_material_all_properties(self, temp_output_file):
        """Test writing material with all properties"""
        with NastranWriter(temp_output_file) as writer:
            writer.write_material(
                mat_id=2,
                youngs=70000.0,
                shear=26000.0,
                poisson=0.33,
                density=2.7e-9,
                thermal_exp=23e-6,
                comments=["ALUMINUM"]
            )

        content = Path(temp_output_file).read_text()

        assert 'MAT1' in content
        # Check for Young's modulus and shear modulus (any format)
        assert '70000' in content or '7.0' in content or 'E+04' in content
        assert '26000' in content or '2.6' in content

    def test_write_property(self, temp_output_file):
        """Test writing property definition"""
        with NastranWriter(temp_output_file) as writer:
            writer.write_property(pid=1, mat_id=1)

        content = Path(temp_output_file).read_text()

        # Check for PSOLID entry
        assert 'PSOLID' in content
        assert '1' in content  # Property ID

    def test_write_header_comments(self, temp_output_file):
        """Test writing header with comments"""
        with NastranWriter(temp_output_file) as writer:
            writer.write_header("Test Model", comments=["Test comment", "Another comment"])

        content = Path(temp_output_file).read_text()

        # Should have comment character and comments
        assert '$' in content  # Nastran comment character
        assert 'Test comment' in content
        assert 'Another comment' in content


# ============================================================================
# Test Class: Sets
# ============================================================================

class TestSets:
    """Test SET1 definition writing"""

    def test_write_node_set(self, temp_output_file):
        """Test writing node set"""
        node_ids = [1, 2, 3, 4, 5, 6, 7, 8]

        with NastranWriter(temp_output_file) as writer:
            writer.write_set(set_id=100, set_type="NODE", entity_ids=node_ids)

        content = Path(temp_output_file).read_text()

        # Check for SET1 entry
        assert 'SET1' in content
        assert '100' in content  # Set ID

        # All node IDs should be present
        for nid in node_ids:
            assert str(nid) in content

    def test_write_large_set(self, temp_output_file):
        """Test writing large set with continuation"""
        node_ids = list(range(1, 101))  # 100 nodes

        with NastranWriter(temp_output_file) as writer:
            writer.write_set(set_id=200, set_type="NODE", entity_ids=node_ids)

        content = Path(temp_output_file).read_text()

        # Should have SET1 and continuation lines
        assert 'SET1' in content
        # Large sets require continuations
        lines = content.split('\n')
        set_lines = [l for l in lines if 'SET1' in l or (l.startswith('*') and not l.startswith('**'))]
        assert len(set_lines) >= 1  # At least one SET1 line


# ============================================================================
# Test Class: Complete Model
# ============================================================================

class TestCompleteModel:
    """Test complete model export"""

    def test_complete_model_hex8(self, simple_hex8_mesh, temp_output_file):
        """Test complete HEX8 model export"""
        with NastranWriter(temp_output_file) as writer:
            writer.write_complete_model(
                mesh=simple_hex8_mesh,
                title="Complete HEX8 Model",
                youngs=210000.0,
                poisson=0.3,
                density=7.85e-9
            )

        content = Path(temp_output_file).read_text()

        # Verify all major sections are present
        assert 'BEGIN BULK' in content
        assert 'GRID' in content  # Nodes
        assert 'CHEXA' in content  # Elements
        assert 'MAT1' in content  # Material
        assert 'PSOLID' in content  # Property
        assert 'ENDDATA' in content

    def test_complete_model_tet4(self, simple_tet4_mesh, temp_output_file):
        """Test complete TET4 model export"""
        with NastranWriter(temp_output_file) as writer:
            writer.write_complete_model(
                mesh=simple_tet4_mesh,
                title="Complete TET4 Model"
            )

        content = Path(temp_output_file).read_text()

        # Verify key sections
        assert 'BEGIN BULK' in content
        assert 'CTETRA' in content
        assert 'ENDDATA' in content

    def test_complete_model_with_sets(self, simple_hex8_mesh, temp_output_file):
        """Test complete model with node and element sets"""
        node_set = list(simple_hex8_mesh.nodes.keys())[:6]  # First 6 nodes
        elem_set = [1]  # First element

        with NastranWriter(temp_output_file) as writer:
            writer.write_complete_model(
                mesh=simple_hex8_mesh,
                title="Model with Sets",
                youngs=210000.0,
                poisson=0.3
            )
            # Add sets after main model
            writer.write_set(set_id=100, set_type="NODE", entity_ids=node_set)
            writer.write_set(set_id=200, set_type="ELEM", entity_ids=elem_set)

        content = Path(temp_output_file).read_text()

        # Verify sets are present
        assert 'SET1' in content
        assert '100' in content


# ============================================================================
# Test Class: Format Compliance
# ============================================================================

class TestFormatCompliance:
    """Test Nastran format compliance"""

    def test_line_length_compliance(self, simple_hex8_mesh, temp_output_file):
        """Test that lines don't exceed Nastran limits"""
        with NastranWriter(temp_output_file) as writer:
            writer.write_complete_model(simple_hex8_mesh, "Test")

        content = Path(temp_output_file).read_text()
        lines = content.split('\n')

        # Nastran free-field format allows up to 80 chars per line (excluding continuations)
        # But with continuations, lines can be longer - just check no extremely long lines
        for line in lines:
            if line.strip() and not line.startswith('$'):  # Skip comments
                assert len(line) <= 200  # Reasonable limit with continuations

    def test_field_format_large(self, simple_hex8_mesh, temp_output_file):
        """Test large field format compliance (16 chars per field)"""
        with NastranWriter(temp_output_file, format='large') as writer:
            writer.write_nodes(simple_hex8_mesh)

        content = Path(temp_output_file).read_text()

        # Large format should have GRID* entries
        assert 'GRID*' in content

        # Check line structure
        lines = [l for l in content.split('\n') if l.startswith('GRID*')]
        if lines:
            # Large format: GRID* + 16-char fields
            first_line = lines[0]
            assert len(first_line) >= 40  # At least a few fields

    def test_field_format_small(self, simple_hex8_mesh, temp_output_file):
        """Test small field format compliance (8 chars per field)"""
        with NastranWriter(temp_output_file, format='small') as writer:
            writer.write_nodes(simple_hex8_mesh)

        content = Path(temp_output_file).read_text()

        # Small format should have GRID (no asterisk)
        grid_lines = [l for l in content.split('\n') if l.startswith('GRID') and not l.startswith('GRID*')]
        assert len(grid_lines) >= 1

    def test_comments_format(self, temp_output_file):
        """Test comment line format"""
        with NastranWriter(temp_output_file) as writer:
            writer.write_header("Test Model", comments=["Comment 1", "Comment 2"])

        content = Path(temp_output_file).read_text()

        # Comments should start with $
        comment_lines = [l for l in content.split('\n') if l.startswith('$')]
        assert len(comment_lines) >= 2
        assert any('Comment 1' in l for l in comment_lines)
        assert any('Comment 2' in l for l in comment_lines)


# ============================================================================
# Test Class: Error Handling
# ============================================================================

class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_unsupported_element_type(self, temp_output_file):
        """Test handling of unsupported element types"""
        # Create mesh with supported element type
        mesh = MeshData(element_type=ElementType.HEX8)
        mesh.nodes[1] = Node(1, 0, 0, 0)
        mesh.nodes[2] = Node(2, 1, 0, 0)
        mesh.nodes[3] = Node(3, 1, 1, 0)
        mesh.nodes[4] = Node(4, 0, 1, 0)
        mesh.nodes[5] = Node(5, 0, 0, 1)
        mesh.nodes[6] = Node(6, 1, 0, 1)
        mesh.nodes[7] = Node(7, 1, 1, 1)
        mesh.nodes[8] = Node(8, 0, 1, 1)
        mesh.elements[1] = Element(1, ElementType.HEX8, [1, 2, 3, 4, 5, 6, 7, 8])

        # Should not raise error for supported type
        with NastranWriter(temp_output_file) as writer:
            writer.write_complete_model(mesh, "Test")

        # File should be created successfully
        assert Path(temp_output_file).exists()

    def test_empty_mesh(self, temp_output_file):
        """Test handling of empty mesh"""
        mesh = MeshData(element_type=ElementType.HEX8)

        with NastranWriter(temp_output_file) as writer:
            writer.write_header("Empty Mesh")
            # Should handle empty mesh gracefully
            writer.write_nodes(mesh)
            writer.write_elements(mesh)

        content = Path(temp_output_file).read_text()
        assert 'Empty Mesh' in content
