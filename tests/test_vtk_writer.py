"""
Tests for VTK Export Writer
============================

This module tests the VTKWriter class that exports mesh data
to VTK formats (.vtu and .vtk).

Test Coverage:
- Basic initialization
- XML format (.vtu) writing
- Legacy format (.vtk) writing
- ASCII and binary encoding (XML)
- Point data (scalar and vector fields)
- All supported element types
- Format compliance
"""

import pytest
import tempfile
from pathlib import Path
import xml.etree.ElementTree as ET

from koomesh.meshing.mesh_data import MeshData, Node, Element, ElementType
from koomesh.export.vtk_writer import VTKWriter


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
    with tempfile.NamedTemporaryFile(mode='w', suffix='.vtu', delete=False) as f:
        output_path = f.name
    yield output_path
    # Cleanup
    Path(output_path).unlink(missing_ok=True)


# ============================================================================
# Test Class: Initialization
# ============================================================================

class TestVTKWriterInit:
    """Test VTKWriter initialization"""

    def test_init_default(self, temp_output_file):
        """Test default initialization (XML format)"""
        writer = VTKWriter(temp_output_file)
        assert writer.output_path == Path(temp_output_file)
        assert writer.format == 'xml'
        assert writer.encoding == 'ascii'

    def test_init_legacy_format(self, temp_output_file):
        """Test initialization with legacy format"""
        writer = VTKWriter(temp_output_file, format='legacy')
        assert writer.format == 'legacy'

    def test_init_binary_encoding(self, temp_output_file):
        """Test initialization with binary encoding"""
        writer = VTKWriter(temp_output_file, encoding='binary')
        assert writer.encoding == 'binary'

    def test_init_invalid_format(self, temp_output_file):
        """Test initialization with invalid format"""
        with pytest.raises(ValueError, match="Format must be"):
            VTKWriter(temp_output_file, format='invalid')

    def test_init_invalid_encoding(self, temp_output_file):
        """Test initialization with invalid encoding"""
        with pytest.raises(ValueError, match="Encoding must be"):
            VTKWriter(temp_output_file, encoding='invalid')

    def test_context_manager(self, temp_output_file):
        """Test context manager functionality"""
        with VTKWriter(temp_output_file) as writer:
            assert writer.file is not None
            assert not writer.file.closed
        # File should be closed after context exit
        assert writer.file.closed


# ============================================================================
# Test Class: XML Format (.vtu)
# ============================================================================

class TestXMLFormat:
    """Test VTK XML format (.vtu) writing"""

    def test_write_hex8_xml_ascii(self, simple_hex8_mesh, temp_output_file):
        """Test writing HEX8 mesh in XML ASCII format"""
        with VTKWriter(temp_output_file, format='xml', encoding='ascii') as writer:
            writer.write_mesh(simple_hex8_mesh)

        # Verify file exists
        assert Path(temp_output_file).exists()

        # Parse XML
        tree = ET.parse(temp_output_file)
        root = tree.getroot()

        # Check root element
        assert root.tag == 'VTKFile'
        assert root.get('type') == 'UnstructuredGrid'

        # Check piece
        piece = root.find('.//Piece')
        assert piece is not None
        assert piece.get('NumberOfPoints') == '12'
        assert piece.get('NumberOfCells') == '2'

    def test_write_tet4_xml_ascii(self, simple_tet4_mesh, temp_output_file):
        """Test writing TET4 mesh in XML ASCII format"""
        with VTKWriter(temp_output_file, format='xml', encoding='ascii') as writer:
            writer.write_mesh(simple_tet4_mesh)

        # Parse XML
        tree = ET.parse(temp_output_file)
        root = tree.getroot()

        piece = root.find('.//Piece')
        assert piece.get('NumberOfPoints') == '5'
        assert piece.get('NumberOfCells') == '2'

    def test_xml_points_data(self, simple_hex8_mesh, temp_output_file):
        """Test points data in XML format"""
        with VTKWriter(temp_output_file, format='xml') as writer:
            writer.write_mesh(simple_hex8_mesh)

        tree = ET.parse(temp_output_file)
        root = tree.getroot()

        # Find points data array
        points_data = root.find('.//Points/DataArray')
        assert points_data is not None
        assert points_data.get('type') == 'Float64'
        assert points_data.get('NumberOfComponents') == '3'

        # Check coordinates exist
        coords_text = points_data.text.strip()
        coords = coords_text.split()
        assert len(coords) == 12 * 3  # 12 nodes, 3 coords each

    def test_xml_cells_data(self, simple_hex8_mesh, temp_output_file):
        """Test cells data in XML format"""
        with VTKWriter(temp_output_file, format='xml') as writer:
            writer.write_mesh(simple_hex8_mesh)

        tree = ET.parse(temp_output_file)
        root = tree.getroot()

        # Check connectivity
        connectivity = root.find('.//Cells/DataArray[@Name="connectivity"]')
        assert connectivity is not None

        # Check offsets
        offsets = root.find('.//Cells/DataArray[@Name="offsets"]')
        assert offsets is not None
        offsets_values = [int(x) for x in offsets.text.strip().split()]
        assert offsets_values == [8, 16]  # 8 nodes per HEX8, cumulative

        # Check cell types
        types = root.find('.//Cells/DataArray[@Name="types"]')
        assert types is not None
        type_values = [int(x) for x in types.text.strip().split()]
        assert all(t == 12 for t in type_values)  # VTK_HEXAHEDRON = 12

    def test_xml_with_scalar_data(self, simple_hex8_mesh, temp_output_file):
        """Test XML format with scalar data"""
        # Create scalar data (e.g., temperature at each node)
        scalar_data = {
            'Temperature': [100.0 + i * 10.0 for i in range(12)]
        }

        with VTKWriter(temp_output_file, format='xml') as writer:
            writer.write_mesh(simple_hex8_mesh, scalar_data=scalar_data)

        tree = ET.parse(temp_output_file)
        root = tree.getroot()

        # Check point data exists
        point_data = root.find('.//PointData')
        assert point_data is not None

        # Check scalar array
        scalar_array = root.find('.//PointData/DataArray[@Name="Temperature"]')
        assert scalar_array is not None
        assert scalar_array.get('type') == 'Float64'

        values = [float(x) for x in scalar_array.text.strip().split()]
        assert len(values) == 12

    def test_xml_with_vector_data(self, simple_hex8_mesh, temp_output_file):
        """Test XML format with vector data"""
        # Create vector data (e.g., displacement at each node)
        vector_data = {
            'Displacement': [[i * 0.1, i * 0.2, i * 0.3] for i in range(12)]
        }

        with VTKWriter(temp_output_file, format='xml') as writer:
            writer.write_mesh(simple_hex8_mesh, vector_data=vector_data)

        tree = ET.parse(temp_output_file)
        root = tree.getroot()

        # Check vector array
        vector_array = root.find('.//PointData/DataArray[@Name="Displacement"]')
        assert vector_array is not None
        assert vector_array.get('NumberOfComponents') == '3'

        values = [float(x) for x in vector_array.text.strip().split()]
        assert len(values) == 12 * 3  # 12 nodes, 3 components each

    def test_xml_binary_encoding(self, simple_hex8_mesh, temp_output_file):
        """Test XML format with binary encoding"""
        with VTKWriter(temp_output_file, format='xml', encoding='binary') as writer:
            writer.write_mesh(simple_hex8_mesh)

        # File should still be valid XML
        tree = ET.parse(temp_output_file)
        root = tree.getroot()

        # Check that data arrays exist (they'll contain base64 encoded data)
        points_data = root.find('.//Points/DataArray')
        assert points_data is not None
        # Binary data should be base64 encoded
        assert points_data.text is not None
        assert len(points_data.text.strip()) > 0


# ============================================================================
# Test Class: Legacy Format (.vtk)
# ============================================================================

class TestLegacyFormat:
    """Test VTK legacy format (.vtk) writing"""

    def test_write_hex8_legacy(self, simple_hex8_mesh):
        """Test writing HEX8 mesh in legacy format"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.vtk', delete=False) as f:
            output_path = f.name

        try:
            with VTKWriter(output_path, format='legacy') as writer:
                writer.write_mesh(simple_hex8_mesh)

            # Read and check content
            content = Path(output_path).read_text()

            # Check header
            assert '# vtk DataFile Version' in content
            assert 'DATASET UNSTRUCTURED_GRID' in content

            # Check points
            assert 'POINTS 12 double' in content

            # Check cells
            assert 'CELLS 2' in content

            # Check cell types
            assert 'CELL_TYPES 2' in content
            lines = content.split('\n')
            cell_type_idx = next(i for i, line in enumerate(lines) if 'CELL_TYPES' in line)
            # Next 2 lines should be cell types (12 = VTK_HEXAHEDRON)
            assert '12' in lines[cell_type_idx + 1]

        finally:
            Path(output_path).unlink(missing_ok=True)

    def test_write_tet4_legacy(self, simple_tet4_mesh):
        """Test writing TET4 mesh in legacy format"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.vtk', delete=False) as f:
            output_path = f.name

        try:
            with VTKWriter(output_path, format='legacy') as writer:
                writer.write_mesh(simple_tet4_mesh)

            content = Path(output_path).read_text()

            # Check structure
            assert 'POINTS 5 double' in content
            assert 'CELLS 2' in content

            # Check cell type (10 = VTK_TETRA)
            assert 'CELL_TYPES 2' in content
            lines = content.split('\n')
            cell_type_idx = next(i for i, line in enumerate(lines) if 'CELL_TYPES' in line)
            assert '10' in lines[cell_type_idx + 1]

        finally:
            Path(output_path).unlink(missing_ok=True)

    def test_legacy_with_scalar_data(self, simple_hex8_mesh):
        """Test legacy format with scalar data"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.vtk', delete=False) as f:
            output_path = f.name

        try:
            scalar_data = {
                'Pressure': [1000.0 + i * 100.0 for i in range(12)]
            }

            with VTKWriter(output_path, format='legacy') as writer:
                writer.write_mesh(simple_hex8_mesh, scalar_data=scalar_data)

            content = Path(output_path).read_text()

            # Check point data section
            assert 'POINT_DATA 12' in content
            assert 'SCALARS Pressure double 1' in content
            assert 'LOOKUP_TABLE default' in content

        finally:
            Path(output_path).unlink(missing_ok=True)

    def test_legacy_with_vector_data(self, simple_hex8_mesh):
        """Test legacy format with vector data"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.vtk', delete=False) as f:
            output_path = f.name

        try:
            vector_data = {
                'Velocity': [[i * 1.0, i * 2.0, i * 3.0] for i in range(12)]
            }

            with VTKWriter(output_path, format='legacy') as writer:
                writer.write_mesh(simple_hex8_mesh, vector_data=vector_data)

            content = Path(output_path).read_text()

            # Check vector data section
            assert 'POINT_DATA 12' in content
            assert 'VECTORS Velocity double' in content

        finally:
            Path(output_path).unlink(missing_ok=True)


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

        with tempfile.NamedTemporaryFile(mode='w', suffix='.vtu', delete=False) as f:
            output_path = f.name

        try:
            with VTKWriter(output_path) as writer:
                writer.write_mesh(mesh)

            tree = ET.parse(output_path)
            root = tree.getroot()

            # Check cell type (13 = VTK_WEDGE)
            types = root.find('.//Cells/DataArray[@Name="types"]')
            type_values = [int(x) for x in types.text.strip().split()]
            assert type_values[0] == 13

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

        with tempfile.NamedTemporaryFile(mode='w', suffix='.vtu', delete=False) as f:
            output_path = f.name

        try:
            with VTKWriter(output_path) as writer:
                writer.write_mesh(mesh)

            tree = ET.parse(output_path)
            root = tree.getroot()

            # Check cell type (14 = VTK_PYRAMID)
            types = root.find('.//Cells/DataArray[@Name="types"]')
            type_values = [int(x) for x in types.text.strip().split()]
            assert type_values[0] == 14

        finally:
            Path(output_path).unlink(missing_ok=True)


# ============================================================================
# Test Class: Convenience Methods
# ============================================================================

class TestConvenienceMethods:
    """Test convenience methods"""

    def test_write_simple_xml(self, simple_hex8_mesh):
        """Test write_simple method with XML format"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.vtu', delete=False) as f:
            output_path = f.name

        try:
            VTKWriter.write_simple(simple_hex8_mesh, output_path, format='xml')

            # Verify file exists and is valid
            assert Path(output_path).exists()
            tree = ET.parse(output_path)
            root = tree.getroot()
            assert root.tag == 'VTKFile'

        finally:
            Path(output_path).unlink(missing_ok=True)

    def test_write_simple_legacy(self, simple_hex8_mesh):
        """Test write_simple method with legacy format"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.vtk', delete=False) as f:
            output_path = f.name

        try:
            VTKWriter.write_simple(simple_hex8_mesh, output_path, format='legacy')

            # Verify file exists
            assert Path(output_path).exists()
            content = Path(output_path).read_text()
            assert 'DATASET UNSTRUCTURED_GRID' in content

        finally:
            Path(output_path).unlink(missing_ok=True)


# ============================================================================
# Test Class: Error Handling
# ============================================================================

class TestErrorHandling:
    """Test error handling"""

    def test_unsupported_element_type(self):
        """Test error for unsupported element type (if any exist)"""
        # All current element types are supported
        # This test is placeholder for future element types
        pass

    def test_empty_mesh(self):
        """Test handling of empty mesh"""
        mesh = MeshData(element_type=ElementType.HEX8)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.vtu', delete=False) as f:
            output_path = f.name

        try:
            with VTKWriter(output_path) as writer:
                writer.write_mesh(mesh)

            # Should create valid file with 0 points/cells
            tree = ET.parse(output_path)
            root = tree.getroot()
            piece = root.find('.//Piece')
            assert piece.get('NumberOfPoints') == '0'
            assert piece.get('NumberOfCells') == '0'

        finally:
            Path(output_path).unlink(missing_ok=True)
