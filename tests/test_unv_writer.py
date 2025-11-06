"""
Tests for Universal File Format (UNV) Export Writer
====================================================

This module tests the UNVWriter class that exports mesh data
to Universal File Format (.unv).

Test Coverage:
- Basic initialization
- Dataset writing (units, nodes, elements, groups)
- Complete model export
- Format compliance
- All supported element types
"""

import pytest
import tempfile
from pathlib import Path

from koomesh.meshing.mesh_data import MeshData, Node, Element, ElementType
from koomesh.export.unv_writer import UNVWriter


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def simple_hex8_mesh():
    """Create a simple HEX8 mesh (2 elements)"""
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

    # Create elements
    mesh.elements[1] = Element(1, ElementType.HEX8, [1, 2, 3, 4, 5, 6, 7, 8])
    mesh.elements[2] = Element(2, ElementType.HEX8, [2, 9, 10, 3, 6, 11, 12, 7])

    return mesh


@pytest.fixture
def simple_tet4_mesh():
    """Create a simple TET4 mesh"""
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
def temp_output_file():
    """Create a temporary output file"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.unv', delete=False) as f:
        output_path = f.name
    yield output_path
    # Cleanup
    Path(output_path).unlink(missing_ok=True)


# ============================================================================
# Test Class: Initialization
# ============================================================================

class TestUNVWriterInit:
    """Test UNVWriter initialization"""

    def test_init_default(self, temp_output_file):
        """Test default initialization"""
        writer = UNVWriter(temp_output_file)
        assert writer.output_path == Path(temp_output_file)
        assert writer.units == "SI"

    def test_init_imperial_units(self, temp_output_file):
        """Test initialization with Imperial units"""
        writer = UNVWriter(temp_output_file, units="Imperial")
        assert writer.units == "Imperial"

    def test_context_manager(self, temp_output_file):
        """Test context manager functionality"""
        with UNVWriter(temp_output_file) as writer:
            assert writer.file is not None
            assert not writer.file.closed
        # File should be closed after context exit
        assert writer.file.closed


# ============================================================================
# Test Class: Dataset Writing
# ============================================================================

class TestDatasetWriting:
    """Test individual dataset writing"""

    def test_write_header(self, temp_output_file):
        """Test writing file header"""
        with UNVWriter(temp_output_file) as writer:
            writer.write_header("Test Model", comments=["Comment 1", "Comment 2"])

        content = Path(temp_output_file).read_text()

        # Check header comments
        assert "$ Test Model" in content
        assert "$ Comment 1" in content
        assert "$ Comment 2" in content
        assert "$ Generated:" in content

    def test_write_units(self, temp_output_file):
        """Test writing units dataset (164)"""
        with UNVWriter(temp_output_file) as writer:
            writer.write_units(unit_code=1)

        content = Path(temp_output_file).read_text()
        lines = content.split('\n')

        # Check dataset markers
        assert '    -1' in content
        assert '  164' in content

        # Check for unit factors (1.0 in scientific notation)
        assert 'E+00' in content

    def test_write_nodes_hex8(self, simple_hex8_mesh, temp_output_file):
        """Test writing nodes dataset (2411)"""
        with UNVWriter(temp_output_file) as writer:
            writer.write_nodes(simple_hex8_mesh)

        content = Path(temp_output_file).read_text()

        # Check dataset header
        assert '  2411' in content

        # Check that we have node data (12 nodes, 4 lines each)
        lines = [l for l in content.split('\n') if l.strip()]
        # Should have dataset markers + node data
        assert len(lines) >= 12 * 4  # 4 lines per node minimum

        # Check for scientific notation in coordinates
        assert 'E' in content or 'e' in content or '0.000000' in content

    def test_write_elements_hex8(self, simple_hex8_mesh, temp_output_file):
        """Test writing elements dataset (2412)"""
        with UNVWriter(temp_output_file) as writer:
            writer.write_elements(simple_hex8_mesh)

        content = Path(temp_output_file).read_text()

        # Check dataset header
        assert '  2412' in content

        # Check element type code (115 for HEX8)
        assert '       115' in content

        # Check that we have element data (2 elements)
        lines = [l for l in content.split('\n') if l.strip() and not l.startswith('$')]
        # Should have element definitions
        assert len(lines) >= 6  # At least 2 elements with headers

    def test_write_elements_tet4(self, simple_tet4_mesh, temp_output_file):
        """Test writing TET4 elements"""
        with UNVWriter(temp_output_file) as writer:
            writer.write_elements(simple_tet4_mesh)

        content = Path(temp_output_file).read_text()

        # Check element type code (111 for TET4)
        assert '       111' in content

    def test_write_groups(self, temp_output_file):
        """Test writing groups dataset (2467)"""
        node_ids = [1, 2, 3, 4, 5]

        with UNVWriter(temp_output_file) as writer:
            writer.write_groups("TEST_GROUP", "NODE", node_ids)

        content = Path(temp_output_file).read_text()

        # Check dataset header
        assert '  2467' in content

        # Check group name
        assert 'TEST_GROUP' in content

        # Check for node entity codes
        assert 'N' in content  # Node indicator


# ============================================================================
# Test Class: Complete Model
# ============================================================================

class TestCompleteModel:
    """Test complete model export"""

    def test_complete_model_hex8(self, simple_hex8_mesh, temp_output_file):
        """Test complete HEX8 model export"""
        with UNVWriter(temp_output_file) as writer:
            writer.write_complete_model(simple_hex8_mesh, title="Complete HEX8 Model")

        # Verify file exists
        assert Path(temp_output_file).exists()

        content = Path(temp_output_file).read_text()

        # Check all major datasets are present
        assert '  164' in content  # Units
        assert '  2411' in content  # Nodes
        assert '  2412' in content  # Elements

        # Check header
        assert '$ Complete HEX8 Model' in content

        # Check dataset markers
        assert content.count('    -1') >= 6  # At least 3 datasets (start+end for each)

    def test_complete_model_tet4(self, simple_tet4_mesh, temp_output_file):
        """Test complete TET4 model export"""
        with UNVWriter(temp_output_file) as writer:
            writer.write_complete_model(simple_tet4_mesh, title="TET4 Model")

        content = Path(temp_output_file).read_text()

        # Check key elements
        assert '$ TET4 Model' in content
        assert '  2411' in content
        assert '  2412' in content
        assert '       111' in content  # TET4 element type

    def test_complete_model_with_groups(self, simple_hex8_mesh, temp_output_file):
        """Test complete model with groups"""
        with UNVWriter(temp_output_file) as writer:
            writer.write_complete_model(simple_hex8_mesh)

            # Add node group
            node_ids = [1, 2, 3, 4]
            writer.write_groups("BOUNDARY_NODES", "NODE", node_ids)

            # Add element group
            elem_ids = [1]
            writer.write_groups("PART_1", "ELEMENT", elem_ids)

        content = Path(temp_output_file).read_text()

        # Check groups are present
        assert 'BOUNDARY_NODES' in content
        assert 'PART_1' in content
        assert '  2467' in content


# ============================================================================
# Test Class: Element Types
# ============================================================================

class TestElementTypes:
    """Test different element types"""

    def test_prism6_element(self):
        """Test PRISM6 element export"""
        mesh = MeshData(element_type=ElementType.PRISM6)

        # Create 6 nodes for prism
        mesh.nodes[1] = Node(1, 0.0, 0.0, 0.0)
        mesh.nodes[2] = Node(2, 1.0, 0.0, 0.0)
        mesh.nodes[3] = Node(3, 0.5, 1.0, 0.0)
        mesh.nodes[4] = Node(4, 0.0, 0.0, 1.0)
        mesh.nodes[5] = Node(5, 1.0, 0.0, 1.0)
        mesh.nodes[6] = Node(6, 0.5, 1.0, 1.0)

        mesh.elements[1] = Element(1, ElementType.PRISM6, [1, 2, 3, 4, 5, 6])

        with tempfile.NamedTemporaryFile(mode='w', suffix='.unv', delete=False) as f:
            output_path = f.name

        try:
            with UNVWriter(output_path) as writer:
                writer.write_complete_model(mesh)

            content = Path(output_path).read_text()

            # Check element type code (112 for PRISM6/WEDGE)
            assert '       112' in content

        finally:
            Path(output_path).unlink(missing_ok=True)

    def test_pyramid5_element(self):
        """Test PYRAMID5 element export"""
        mesh = MeshData(element_type=ElementType.PYRAMID5)

        # Create 5 nodes for pyramid
        mesh.nodes[1] = Node(1, 0.0, 0.0, 0.0)
        mesh.nodes[2] = Node(2, 1.0, 0.0, 0.0)
        mesh.nodes[3] = Node(3, 1.0, 1.0, 0.0)
        mesh.nodes[4] = Node(4, 0.0, 1.0, 0.0)
        mesh.nodes[5] = Node(5, 0.5, 0.5, 1.0)

        mesh.elements[1] = Element(1, ElementType.PYRAMID5, [1, 2, 3, 4, 5])

        with tempfile.NamedTemporaryFile(mode='w', suffix='.unv', delete=False) as f:
            output_path = f.name

        try:
            with UNVWriter(output_path) as writer:
                writer.write_complete_model(mesh)

            content = Path(output_path).read_text()

            # Check element type code (117 for PYRAMID5)
            assert '       117' in content

        finally:
            Path(output_path).unlink(missing_ok=True)

    def test_hex20_element(self):
        """Test HEX20 element export"""
        mesh = MeshData(element_type=ElementType.HEX20)

        # Create 20 nodes
        # 8 corner nodes
        for i in range(8):
            x = float(i % 2)
            y = float((i // 2) % 2)
            z = float(i // 4)
            mesh.nodes[i+1] = Node(i+1, x, y, z)

        # 12 mid-edge nodes (simplified)
        for i in range(12):
            mesh.nodes[i+9] = Node(i+9, 0.5, 0.5, 0.5)

        mesh.elements[1] = Element(1, ElementType.HEX20, list(range(1, 21)))

        with tempfile.NamedTemporaryFile(mode='w', suffix='.unv', delete=False) as f:
            output_path = f.name

        try:
            with UNVWriter(output_path) as writer:
                writer.write_complete_model(mesh)

            content = Path(output_path).read_text()

            # Check element type code (116 for HEX20)
            assert '       116' in content

        finally:
            Path(output_path).unlink(missing_ok=True)


# ============================================================================
# Test Class: Format Compliance
# ============================================================================

class TestFormatCompliance:
    """Test UNV format compliance"""

    def test_dataset_markers(self, simple_hex8_mesh, temp_output_file):
        """Test dataset markers (-1)"""
        with UNVWriter(temp_output_file) as writer:
            writer.write_complete_model(simple_hex8_mesh)

        content = Path(temp_output_file).read_text()
        lines = content.split('\n')

        # Count -1 markers (should be even - start and end for each dataset)
        marker_count = sum(1 for line in lines if line.strip() == '-1')
        assert marker_count % 2 == 0
        assert marker_count >= 6  # At least 3 datasets

    def test_node_format(self, simple_hex8_mesh, temp_output_file):
        """Test node format compliance"""
        with UNVWriter(temp_output_file) as writer:
            writer.write_nodes(simple_hex8_mesh)

        content = Path(temp_output_file).read_text()
        lines = [l for l in content.split('\n') if l.strip() and not l.startswith('$') and l.strip() != '-1']

        # After dataset header, should have 4 lines per node (1 header + 3 coords)
        # Skip dataset markers
        data_lines = [l for l in lines if not l.strip().startswith('2411')]

        # Should have groups of 4 lines (1 + 3)
        assert len(data_lines) % 4 == 0

    def test_element_format(self, simple_hex8_mesh, temp_output_file):
        """Test element format compliance"""
        with UNVWriter(temp_output_file) as writer:
            writer.write_elements(simple_hex8_mesh)

        content = Path(temp_output_file).read_text()

        # Should have element headers with proper formatting
        # Element type 115, 10-character fields
        assert '       115' in content


# ============================================================================
# Test Class: Convenience Methods
# ============================================================================

class TestConvenienceMethods:
    """Test convenience methods"""

    def test_write_simple(self, simple_hex8_mesh):
        """Test write_simple method"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.unv', delete=False) as f:
            output_path = f.name

        try:
            UNVWriter.write_simple(simple_hex8_mesh, output_path, title="Simple Test")

            # Verify file exists and has content
            assert Path(output_path).exists()
            content = Path(output_path).read_text()

            assert '$ Simple Test' in content
            assert '  2411' in content
            assert '  2412' in content

        finally:
            Path(output_path).unlink(missing_ok=True)


# ============================================================================
# Test Class: Error Handling
# ============================================================================

class TestErrorHandling:
    """Test error handling"""

    def test_empty_mesh(self):
        """Test handling of empty mesh"""
        mesh = MeshData(element_type=ElementType.HEX8)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.unv', delete=False) as f:
            output_path = f.name

        try:
            with UNVWriter(output_path) as writer:
                writer.write_complete_model(mesh)

            # Should create valid file even with no data
            assert Path(output_path).exists()
            content = Path(output_path).read_text()

            # Should have units dataset at least
            assert '  164' in content

        finally:
            Path(output_path).unlink(missing_ok=True)
