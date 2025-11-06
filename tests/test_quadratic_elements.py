"""
Tests for Quadratic Element Support
=====================================

This module tests the implementation of quadratic elements (HEX20, HEX27, TET10)
"""

import pytest
import numpy as np
from koomesh.meshing.mesh_data import MeshData, ElementType, Element
from koomesh.meshing.shape_functions import (
    hex20_shape_functions, hex20_shape_derivatives,
    hex27_shape_functions, hex27_shape_derivatives,
    tet10_shape_functions, tet10_shape_derivatives,
    get_shape_functions, compute_jacobian
)


class TestElementTypes:
    """Test element type definitions"""

    def test_element_types_exist(self):
        """Test that all quadratic element types are defined"""
        assert ElementType.HEX20 is not None
        assert ElementType.HEX27 is not None
        assert ElementType.TET10 is not None

    def test_element_node_counts(self):
        """Test correct node counts for each element type"""
        assert ElementType.HEX20.num_nodes == 20
        assert ElementType.HEX27.num_nodes == 27
        assert ElementType.TET10.num_nodes == 10

    def test_is_hex_methods(self):
        """Test element type classification"""
        assert ElementType.HEX20.is_hex()
        assert ElementType.HEX27.is_hex()
        assert not ElementType.TET10.is_hex()

        assert ElementType.TET10.is_tet()
        assert not ElementType.HEX20.is_tet()


class TestShapeFunctions:
    """Test shape functions"""

    def test_hex20_shape_functions_partition_of_unity(self):
        """Test HEX20 shape functions sum to 1"""
        # At center
        N = hex20_shape_functions(0.0, 0.0, 0.0)
        assert len(N) == 20
        assert np.isclose(np.sum(N), 1.0)

        # At corner
        N = hex20_shape_functions(-1.0, -1.0, -1.0)
        assert np.isclose(np.sum(N), 1.0)

    def test_hex27_shape_functions_partition_of_unity(self):
        """Test HEX27 shape functions sum to 1"""
        N = hex27_shape_functions(0.0, 0.0, 0.0)
        assert len(N) == 27
        assert np.isclose(np.sum(N), 1.0)

        N = hex27_shape_functions(0.5, 0.5, 0.5)
        assert np.isclose(np.sum(N), 1.0)

    def test_tet10_shape_functions_partition_of_unity(self):
        """Test TET10 shape functions sum to 1"""
        N = tet10_shape_functions(0.25, 0.25, 0.25)
        assert len(N) == 10
        assert np.isclose(np.sum(N), 1.0)

        N = tet10_shape_functions(0.0, 0.0, 0.0)
        assert np.isclose(np.sum(N), 1.0)

    def test_hex20_shape_derivatives_shape(self):
        """Test HEX20 derivatives have correct shape"""
        dN = hex20_shape_derivatives(0.0, 0.0, 0.0)
        assert dN.shape == (3, 20)

    def test_hex27_shape_derivatives_shape(self):
        """Test HEX27 derivatives have correct shape"""
        dN = hex27_shape_derivatives(0.0, 0.0, 0.0)
        assert dN.shape == (3, 27)

    def test_tet10_shape_derivatives_shape(self):
        """Test TET10 derivatives have correct shape"""
        dN = tet10_shape_derivatives(0.25, 0.25, 0.25)
        assert dN.shape == (3, 10)

    def test_get_shape_functions(self):
        """Test shape function getter"""
        shape_func, shape_deriv = get_shape_functions('hex20')
        assert callable(shape_func)
        assert callable(shape_deriv)

        N = shape_func(0.0, 0.0, 0.0)
        assert len(N) == 20

    def test_compute_jacobian_hex20(self):
        """Test Jacobian computation for HEX20"""
        # Create a unit cube HEX20 element
        # Corner nodes
        coords = np.array([
            [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],  # Bottom
            [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1],  # Top
            # Mid-side nodes on bottom edges
            [0.5, 0, 0], [1, 0.5, 0], [0.5, 1, 0], [0, 0.5, 0],
            # Mid-side nodes on top edges
            [0.5, 0, 1], [1, 0.5, 1], [0.5, 1, 1], [0, 0.5, 1],
            # Mid-side nodes on vertical edges
            [0, 0, 0.5], [1, 0, 0.5], [1, 1, 0.5], [0, 1, 0.5],
        ])

        dN = hex20_shape_derivatives(0.0, 0.0, 0.0)
        J, det_J = compute_jacobian(coords, dN)

        assert J.shape == (3, 3)
        assert det_J > 0  # Positive Jacobian for valid element


class TestMeshData:
    """Test mesh data with quadratic elements"""

    def test_create_hex20_element(self):
        """Test creating HEX20 element"""
        mesh = MeshData(element_type=ElementType.HEX20)

        # Add 20 nodes
        node_ids = []
        for i in range(20):
            nid = mesh.add_node(float(i), 0.0, 0.0)
            node_ids.append(nid)

        # Add element
        eid = mesh.add_element(node_ids, element_type=ElementType.HEX20)

        assert mesh.num_elements() == 1
        elem = mesh.get_element(eid)
        assert elem.type == ElementType.HEX20
        assert len(elem.nodes) == 20

    def test_create_hex27_element(self):
        """Test creating HEX27 element"""
        mesh = MeshData(element_type=ElementType.HEX27)

        node_ids = []
        for i in range(27):
            nid = mesh.add_node(float(i), 0.0, 0.0)
            node_ids.append(nid)

        eid = mesh.add_element(node_ids, element_type=ElementType.HEX27)

        elem = mesh.get_element(eid)
        assert elem.type == ElementType.HEX27
        assert len(elem.nodes) == 27

    def test_create_tet10_element(self):
        """Test creating TET10 element"""
        mesh = MeshData(element_type=ElementType.TET10)

        node_ids = []
        for i in range(10):
            nid = mesh.add_node(float(i), 0.0, 0.0)
            node_ids.append(nid)

        eid = mesh.add_element(node_ids, element_type=ElementType.TET10)

        elem = mesh.get_element(eid)
        assert elem.type == ElementType.TET10
        assert len(elem.nodes) == 10

    def test_element_validation(self):
        """Test element node count validation"""
        mesh = MeshData(element_type=ElementType.HEX20)

        # Try to add element with wrong number of nodes
        with pytest.raises(ValueError, match="requires 20 nodes"):
            mesh.add_element([1, 2, 3, 4, 5, 6, 7, 8], element_type=ElementType.HEX20)


class TestFaceNodes:
    """Test face node extraction for quadratic elements"""

    def test_hex20_face_nodes(self):
        """Test HEX20 face node extraction"""
        mesh = MeshData(element_type=ElementType.HEX20)

        node_ids = list(range(1, 21))
        for i, nid in enumerate(node_ids):
            mesh.add_node(float(i), 0.0, 0.0, node_id=nid)

        elem = Element(id=1, type=ElementType.HEX20, nodes=node_ids)

        # Each HEX20 face should have 8 nodes
        face_nodes = elem.get_face_nodes(0)
        assert len(face_nodes) == 8

    def test_hex27_face_nodes(self):
        """Test HEX27 face node extraction"""
        mesh = MeshData(element_type=ElementType.HEX27)

        node_ids = list(range(1, 28))
        for i, nid in enumerate(node_ids):
            mesh.add_node(float(i), 0.0, 0.0, node_id=nid)

        elem = Element(id=1, type=ElementType.HEX27, nodes=node_ids)

        # Each HEX27 face should have 9 nodes
        face_nodes = elem.get_face_nodes(0)
        assert len(face_nodes) == 9

    def test_tet10_face_nodes(self):
        """Test TET10 face node extraction"""
        mesh = MeshData(element_type=ElementType.TET10)

        node_ids = list(range(1, 11))
        for i, nid in enumerate(node_ids):
            mesh.add_node(float(i), 0.0, 0.0, node_id=nid)

        elem = Element(id=1, type=ElementType.TET10, nodes=node_ids)

        # Each TET10 face should have 6 nodes
        face_nodes = elem.get_face_nodes(0)
        assert len(face_nodes) == 6


class TestLSDynaExport:
    """Test LS-DYNA export for quadratic elements"""

    def test_hex20_export_format(self):
        """Test HEX20 LS-DYNA format"""
        from koomesh.export.lsdyna_writer import LSDynaWriter
        import tempfile

        mesh = MeshData(element_type=ElementType.HEX20)

        # Create a HEX20 element
        node_ids = []
        for i in range(20):
            nid = mesh.add_node(float(i), float(i), float(i))
            node_ids.append(nid)

        mesh.add_element(node_ids, element_type=ElementType.HEX20)

        # Write to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.k', delete=False) as f:
            temp_path = f.name

        with LSDynaWriter(temp_path) as writer:
            writer.write_header()
            writer.write_nodes(mesh)
            writer.write_elements(mesh)

        # Read file and check format
        with open(temp_path, 'r') as f:
            content = f.read()

        assert '*ELEMENT_SOLID' in content
        assert 'HEX20' in content
        assert content.count('\n') > 40  # Should have multiple lines per element

        # Cleanup
        import os
        os.unlink(temp_path)

    def test_hex27_export_format(self):
        """Test HEX27 LS-DYNA format"""
        from koomesh.export.lsdyna_writer import LSDynaWriter
        import tempfile

        mesh = MeshData(element_type=ElementType.HEX27)

        node_ids = []
        for i in range(27):
            nid = mesh.add_node(float(i), float(i), float(i))
            node_ids.append(nid)

        mesh.add_element(node_ids, element_type=ElementType.HEX27)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.k', delete=False) as f:
            temp_path = f.name

        with LSDynaWriter(temp_path) as writer:
            writer.write_header()
            writer.write_nodes(mesh)
            writer.write_elements(mesh)

        with open(temp_path, 'r') as f:
            content = f.read()

        assert '*ELEMENT_SOLID' in content
        assert 'HEX27' in content

        import os
        os.unlink(temp_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
