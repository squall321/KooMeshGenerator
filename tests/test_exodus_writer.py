"""
Test Suite for Exodus II Writer
================================

This module contains comprehensive tests for the Exodus II format export functionality.

Test Categories:
1. Basic Functionality Tests
2. Element Type Tests
3. Element Block Tests
4. Node Set Tests
5. Side Set Tests
6. Error Handling Tests
7. File Format Compliance Tests

Author: KooMeshGenerator Team
License: MIT
"""

import pytest
import tempfile
from pathlib import Path
import numpy as np

# Try to import netCDF4
try:
    from netCDF4 import Dataset
    NETCDF4_AVAILABLE = True
except ImportError:
    NETCDF4_AVAILABLE = False

from koomesh.meshing.mesh_data import MeshData, ElementType
from koomesh.export.exodus_writer import (
    ExodusWriter,
    ExodusError,
    export_to_exodus
)


# Skip all tests if netCDF4 is not available
pytestmark = pytest.mark.skipif(
    not NETCDF4_AVAILABLE,
    reason="netCDF4 library not available"
)


@pytest.fixture
def temp_exodus_file():
    """Create a temporary Exodus file path"""
    with tempfile.NamedTemporaryFile(suffix='.exo', delete=False) as f:
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
    """Test basic Exodus writer functionality"""

    def test_writer_initialization(self, temp_exodus_file):
        """Test ExodusWriter can be initialized"""
        writer = ExodusWriter(temp_exodus_file)
        assert writer.filepath == Path(temp_exodus_file)
        assert writer.title == "KooMesh Generated"

    def test_writer_context_manager(self, temp_exodus_file, simple_hex_mesh):
        """Test ExodusWriter works as context manager"""
        with ExodusWriter(temp_exodus_file) as writer:
            writer.write_mesh(simple_hex_mesh)

        # Verify file was created
        assert Path(temp_exodus_file).exists()
        assert Path(temp_exodus_file).stat().st_size > 0

    def test_export_convenience_function(self, temp_exodus_file, simple_hex_mesh):
        """Test export_to_exodus convenience function"""
        success = export_to_exodus(simple_hex_mesh, temp_exodus_file)
        assert success is True
        assert Path(temp_exodus_file).exists()

    def test_custom_title(self, temp_exodus_file, simple_hex_mesh):
        """Test custom mesh title"""
        title = "My Test Mesh"
        with ExodusWriter(temp_exodus_file, title=title) as writer:
            writer.write_mesh(simple_hex_mesh)

        # Read back and verify title
        with Dataset(temp_exodus_file, 'r') as ncfile:
            assert ncfile.title == title

    def test_file_extension_warning(self, caplog):
        """Test warning for non-standard file extension"""
        with tempfile.NamedTemporaryFile(suffix='.txt') as f:
            writer = ExodusWriter(f.name)
            assert "non-standard" in caplog.text.lower()


# =============================================================================
# 2. Element Type Tests
# =============================================================================

class TestElementTypes:
    """Test support for different element types"""

    def test_hex8_export(self, temp_exodus_file, simple_hex_mesh):
        """Test HEX8 element export"""
        with ExodusWriter(temp_exodus_file) as writer:
            writer.write_mesh(simple_hex_mesh)

        # Verify in file
        with Dataset(temp_exodus_file, 'r') as ncfile:
            connect = ncfile.variables['connect1']
            assert connect.elem_type == 'HEX'
            assert connect.shape == (1, 8)

    def test_tet4_export(self, temp_exodus_file, simple_tet_mesh):
        """Test TET4 element export"""
        with ExodusWriter(temp_exodus_file) as writer:
            writer.write_mesh(simple_tet_mesh)

        # Verify in file
        with Dataset(temp_exodus_file, 'r') as ncfile:
            connect = ncfile.variables['connect1']
            assert connect.elem_type == 'TETRA4'
            assert connect.shape == (1, 4)

    def test_hex20_export(self, temp_exodus_file):
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

        with ExodusWriter(temp_exodus_file) as writer:
            writer.write_mesh(mesh)

        # Verify
        with Dataset(temp_exodus_file, 'r') as ncfile:
            connect = ncfile.variables['connect1']
            assert connect.elem_type == 'HEX20'
            assert connect.shape == (1, 20)

    def test_prism6_export(self, temp_exodus_file):
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

        with ExodusWriter(temp_exodus_file) as writer:
            writer.write_mesh(mesh)

        # Verify
        with Dataset(temp_exodus_file, 'r') as ncfile:
            connect = ncfile.variables['connect1']
            assert connect.elem_type == 'WEDGE6'
            assert connect.shape == (1, 6)

    def test_pyramid5_export(self, temp_exodus_file):
        """Test PYRAMID5 element export"""
        mesh = MeshData(element_type=ElementType.PYRAMID5)

        # Create 5 nodes for PYRAMID5
        mesh.add_node(0.0, 0.0, 0.0, node_id=1)
        mesh.add_node(1.0, 0.0, 0.0, node_id=2)
        mesh.add_node(1.0, 1.0, 0.0, node_id=3)
        mesh.add_node(0.0, 1.0, 0.0, node_id=4)
        mesh.add_node(0.5, 0.5, 1.0, node_id=5)

        mesh.add_element([1, 2, 3, 4, 5], element_id=1)

        with ExodusWriter(temp_exodus_file) as writer:
            writer.write_mesh(mesh)

        # Verify
        with Dataset(temp_exodus_file, 'r') as ncfile:
            connect = ncfile.variables['connect1']
            assert connect.elem_type == 'PYRAMID5'
            assert connect.shape == (1, 5)


# =============================================================================
# 3. Element Block Tests
# =============================================================================

class TestElementBlocks:
    """Test element block functionality"""

    def test_auto_element_blocks(self, temp_exodus_file, mixed_element_mesh):
        """Test automatic element block creation by type"""
        with ExodusWriter(temp_exodus_file) as writer:
            writer.write_mesh(mixed_element_mesh)

        # Verify two element blocks created
        with Dataset(temp_exodus_file, 'r') as ncfile:
            assert ncfile.dimensions['num_el_blk'].size == 2

            # Verify block 1 (HEX8)
            connect1 = ncfile.variables['connect1']
            assert connect1.elem_type == 'HEX'

            # Verify block 2 (TET4)
            connect2 = ncfile.variables['connect2']
            assert connect2.elem_type == 'TETRA4'

    def test_custom_element_blocks(self, temp_exodus_file, multi_element_mesh):
        """Test custom element block specification"""
        element_blocks = {
            "block_a": [1],
            "block_b": [2]
        }

        with ExodusWriter(temp_exodus_file) as writer:
            writer.write_mesh(multi_element_mesh, element_blocks=element_blocks)

        # Verify two element blocks created
        with Dataset(temp_exodus_file, 'r') as ncfile:
            assert ncfile.dimensions['num_el_blk'].size == 2

            # Verify block sizes
            assert ncfile.dimensions['num_el_in_blk1'].size == 1
            assert ncfile.dimensions['num_el_in_blk2'].size == 1

    def test_single_element_block(self, temp_exodus_file, multi_element_mesh):
        """Test all elements in single block"""
        element_blocks = {
            "all_elements": [1, 2]
        }

        with ExodusWriter(temp_exodus_file) as writer:
            writer.write_mesh(multi_element_mesh, element_blocks=element_blocks)

        # Verify single block with 2 elements
        with Dataset(temp_exodus_file, 'r') as ncfile:
            assert ncfile.dimensions['num_el_blk'].size == 1
            assert ncfile.dimensions['num_el_in_blk1'].size == 2

    def test_element_block_names(self, temp_exodus_file, multi_element_mesh):
        """Test element block names are preserved"""
        element_blocks = {
            "steel": [1],
            "aluminum": [2]
        }

        with ExodusWriter(temp_exodus_file) as writer:
            writer.write_mesh(multi_element_mesh, element_blocks=element_blocks)

        # Read back names
        with Dataset(temp_exodus_file, 'r') as ncfile:
            eb_names = ncfile.variables['eb_names']

            # Decode block names
            name1 = b''.join(eb_names[0, :]).decode('ascii').rstrip('\x00')
            name2 = b''.join(eb_names[1, :]).decode('ascii').rstrip('\x00')

            assert name1 == "steel"
            assert name2 == "aluminum"


# =============================================================================
# 4. Node Set Tests
# =============================================================================

class TestNodeSets:
    """Test node set functionality"""

    def test_single_node_set(self, temp_exodus_file, simple_hex_mesh):
        """Test single node set export"""
        node_sets = {
            "bottom": [1, 2, 3, 4]
        }

        with ExodusWriter(temp_exodus_file) as writer:
            writer.write_mesh(simple_hex_mesh, node_sets=node_sets)

        # Verify node set
        with Dataset(temp_exodus_file, 'r') as ncfile:
            assert ncfile.dimensions['num_node_sets'].size == 1
            assert ncfile.dimensions['num_nod_ns1'].size == 4

            node_list = ncfile.variables['node_ns1'][:]
            assert np.array_equal(node_list, [1, 2, 3, 4])

    def test_multiple_node_sets(self, temp_exodus_file, simple_hex_mesh):
        """Test multiple node sets"""
        node_sets = {
            "bottom": [1, 2, 3, 4],
            "top": [5, 6, 7, 8],
            "front": [1, 2, 5, 6]
        }

        with ExodusWriter(temp_exodus_file) as writer:
            writer.write_mesh(simple_hex_mesh, node_sets=node_sets)

        # Verify node sets
        with Dataset(temp_exodus_file, 'r') as ncfile:
            assert ncfile.dimensions['num_node_sets'].size == 3

    def test_node_set_names(self, temp_exodus_file, simple_hex_mesh):
        """Test node set names are preserved"""
        node_sets = {
            "boundary_left": [1, 4, 5, 8],
            "boundary_right": [2, 3, 6, 7]
        }

        with ExodusWriter(temp_exodus_file) as writer:
            writer.write_mesh(simple_hex_mesh, node_sets=node_sets)

        # Read back names
        with Dataset(temp_exodus_file, 'r') as ncfile:
            ns_names = ncfile.variables['ns_names']

            name1 = b''.join(ns_names[0, :]).decode('ascii').rstrip('\x00')
            name2 = b''.join(ns_names[1, :]).decode('ascii').rstrip('\x00')

            assert name1 == "boundary_left"
            assert name2 == "boundary_right"


# =============================================================================
# 5. Side Set Tests
# =============================================================================

class TestSideSets:
    """Test side set functionality"""

    def test_single_side_set(self, temp_exodus_file, simple_hex_mesh):
        """Test single side set export"""
        side_sets = {
            "bottom_face": [(1, 1)]  # Element 1, Side 1
        }

        with ExodusWriter(temp_exodus_file) as writer:
            writer.write_mesh(simple_hex_mesh, side_sets=side_sets)

        # Verify side set
        with Dataset(temp_exodus_file, 'r') as ncfile:
            assert ncfile.dimensions['num_side_sets'].size == 1
            assert ncfile.dimensions['num_side_ss1'].size == 1

            elem_list = ncfile.variables['elem_ss1'][:]
            side_list = ncfile.variables['side_ss1'][:]

            assert elem_list[0] == 1
            assert side_list[0] == 1

    def test_multiple_side_sets(self, temp_exodus_file, multi_element_mesh):
        """Test multiple side sets"""
        side_sets = {
            "left": [(1, 1)],
            "right": [(2, 2)],
            "bottom": [(1, 5), (2, 5)]
        }

        with ExodusWriter(temp_exodus_file) as writer:
            writer.write_mesh(multi_element_mesh, side_sets=side_sets)

        # Verify side sets
        with Dataset(temp_exodus_file, 'r') as ncfile:
            assert ncfile.dimensions['num_side_sets'].size == 3

            # Verify bottom side set has 2 sides
            assert ncfile.dimensions['num_side_ss3'].size == 2


# =============================================================================
# 6. Error Handling Tests
# =============================================================================

class TestErrorHandling:
    """Test error handling"""

    def test_empty_mesh_error(self, temp_exodus_file):
        """Test error with empty mesh"""
        mesh = MeshData()

        with pytest.raises(ExodusError, match="no nodes"):
            with ExodusWriter(temp_exodus_file) as writer:
                writer.write_mesh(mesh)

    def test_mesh_without_elements_error(self, temp_exodus_file):
        """Test error with mesh that has nodes but no elements"""
        mesh = MeshData()
        mesh.add_node(0.0, 0.0, 0.0)

        with pytest.raises(ExodusError, match="no elements"):
            with ExodusWriter(temp_exodus_file) as writer:
                writer.write_mesh(mesh)

    def test_file_not_open_error(self, temp_exodus_file, simple_hex_mesh):
        """Test error when trying to write without opening file"""
        writer = ExodusWriter(temp_exodus_file)

        with pytest.raises(ExodusError, match="not open"):
            writer.write_mesh(simple_hex_mesh)

    def test_mixed_types_in_block_error(self, temp_exodus_file, mixed_element_mesh):
        """Test error when element block contains mixed element types"""
        # Try to put both HEX8 and TET4 in same block
        element_blocks = {
            "mixed_block": [1, 2]  # 1 is HEX8, 2 is TET4
        }

        with pytest.raises(ExodusError, match="mixed element types"):
            with ExodusWriter(temp_exodus_file) as writer:
                writer.write_mesh(mixed_element_mesh, element_blocks=element_blocks)


# =============================================================================
# 7. File Format Compliance Tests
# =============================================================================

class TestFormatCompliance:
    """Test Exodus II format compliance"""

    def test_netcdf_format(self, temp_exodus_file, simple_hex_mesh):
        """Test file is valid netCDF format"""
        with ExodusWriter(temp_exodus_file) as writer:
            writer.write_mesh(simple_hex_mesh)

        # Should be able to open with netCDF4
        with Dataset(temp_exodus_file, 'r') as ncfile:
            assert ncfile is not None

    def test_required_dimensions(self, temp_exodus_file, simple_hex_mesh):
        """Test required dimensions are present"""
        with ExodusWriter(temp_exodus_file) as writer:
            writer.write_mesh(simple_hex_mesh)

        with Dataset(temp_exodus_file, 'r') as ncfile:
            required_dims = ['num_nodes', 'num_dim', 'num_elem', 'num_el_blk']
            for dim in required_dims:
                assert dim in ncfile.dimensions

    def test_required_variables(self, temp_exodus_file, simple_hex_mesh):
        """Test required variables are present"""
        with ExodusWriter(temp_exodus_file) as writer:
            writer.write_mesh(simple_hex_mesh)

        with Dataset(temp_exodus_file, 'r') as ncfile:
            required_vars = ['coordx', 'coordy', 'coordz', 'eb_status', 'eb_prop1']
            for var in required_vars:
                assert var in ncfile.variables

    def test_global_attributes(self, temp_exodus_file, simple_hex_mesh):
        """Test required global attributes"""
        with ExodusWriter(temp_exodus_file) as writer:
            writer.write_mesh(simple_hex_mesh)

        with Dataset(temp_exodus_file, 'r') as ncfile:
            assert hasattr(ncfile, 'api_version')
            assert hasattr(ncfile, 'version')
            assert hasattr(ncfile, 'title')
            assert hasattr(ncfile, 'floating_point_word_size')

    def test_qa_records(self, temp_exodus_file, simple_hex_mesh):
        """Test QA records are written"""
        with ExodusWriter(temp_exodus_file) as writer:
            writer.write_mesh(simple_hex_mesh)

        with Dataset(temp_exodus_file, 'r') as ncfile:
            assert 'num_qa_rec' in ncfile.dimensions
            assert 'qa_records' in ncfile.variables
            assert ncfile.dimensions['num_qa_rec'].size == 1

    def test_coordinate_system(self, temp_exodus_file, simple_hex_mesh):
        """Test 3D coordinate system"""
        with ExodusWriter(temp_exodus_file) as writer:
            writer.write_mesh(simple_hex_mesh)

        with Dataset(temp_exodus_file, 'r') as ncfile:
            assert ncfile.dimensions['num_dim'].size == 3
            assert 'coor_names' in ncfile.variables

    def test_node_coordinates_values(self, temp_exodus_file, simple_hex_mesh):
        """Test node coordinate values are correct"""
        with ExodusWriter(temp_exodus_file) as writer:
            writer.write_mesh(simple_hex_mesh)

        with Dataset(temp_exodus_file, 'r') as ncfile:
            coordx = ncfile.variables['coordx'][:]
            coordy = ncfile.variables['coordy'][:]
            coordz = ncfile.variables['coordz'][:]

            # Verify first node (0, 0, 0)
            assert coordx[0] == 0.0
            assert coordy[0] == 0.0
            assert coordz[0] == 0.0

            # Verify second node (1, 0, 0)
            assert coordx[1] == 1.0
            assert coordy[1] == 0.0
            assert coordz[1] == 0.0

    def test_connectivity_indexing(self, temp_exodus_file, simple_hex_mesh):
        """Test connectivity uses 1-based indexing"""
        with ExodusWriter(temp_exodus_file) as writer:
            writer.write_mesh(simple_hex_mesh)

        with Dataset(temp_exodus_file, 'r') as ncfile:
            connect = ncfile.variables['connect1'][:]

            # Exodus uses 1-based indexing
            assert np.min(connect) == 1
            assert np.max(connect) == 8  # 8 nodes in HEX8


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
