"""
Tests for Prism and Pyramid Element Support
============================================

This module tests the implementation of prism and pyramid elements (PRISM6, PYRAMID5)
"""

import pytest
import numpy as np
from koomesh.meshing.mesh_data import MeshData, ElementType, Element
from koomesh.meshing.shape_functions import (
    prism6_shape_functions, prism6_shape_derivatives,
    pyramid5_shape_functions, pyramid5_shape_derivatives,
    get_shape_functions, compute_jacobian
)


class TestElementTypes:
    """Test element type definitions"""

    def test_element_types_exist(self):
        """Test that prism and pyramid element types are defined"""
        assert ElementType.PRISM6 is not None
        assert ElementType.PYRAMID5 is not None

    def test_element_node_counts(self):
        """Test correct node counts for each element type"""
        assert ElementType.PRISM6.num_nodes == 6
        assert ElementType.PYRAMID5.num_nodes == 5

    def test_element_classifications(self):
        """Test element type classification"""
        assert not ElementType.PRISM6.is_hex()
        assert not ElementType.PRISM6.is_tet()

        assert not ElementType.PYRAMID5.is_hex()
        assert not ElementType.PYRAMID5.is_tet()


class TestPRISM6ShapeFunctions:
    """Test PRISM6 (wedge) shape functions"""

    def test_prism6_shape_functions_partition_of_unity(self):
        """Test PRISM6 shape functions sum to 1"""
        # At center of bottom triangle
        N = prism6_shape_functions(0.33, 0.33, 0.0)
        assert len(N) == 6
        assert np.isclose(np.sum(N), 1.0)

        # At bottom corner
        N = prism6_shape_functions(0.0, 0.0, -1.0)
        assert np.isclose(np.sum(N), 1.0)

        # At top corner
        N = prism6_shape_functions(1.0, 0.0, 1.0)
        assert np.isclose(np.sum(N), 1.0)

        # Mid-height
        N = prism6_shape_functions(0.5, 0.5, 0.0)
        assert np.isclose(np.sum(N), 1.0)

    def test_prism6_corner_nodes(self):
        """Test PRISM6 shape functions at corner nodes"""
        # Bottom corner node 0: (0, 0, -1)
        N = prism6_shape_functions(0.0, 0.0, -1.0)
        assert np.isclose(N[0], 1.0)
        for i in range(1, 6):
            assert np.isclose(N[i], 0.0)

        # Bottom corner node 1: (1, 0, -1)
        N = prism6_shape_functions(1.0, 0.0, -1.0)
        assert np.isclose(N[1], 1.0)
        assert np.isclose(N[0], 0.0)

        # Top corner node 3: (0, 0, 1)
        N = prism6_shape_functions(0.0, 0.0, 1.0)
        assert np.isclose(N[3], 1.0)
        for i in [0, 1, 2, 4, 5]:
            assert np.isclose(N[i], 0.0)

    def test_prism6_shape_derivatives_shape(self):
        """Test PRISM6 derivatives have correct shape"""
        dN = prism6_shape_derivatives(0.33, 0.33, 0.0)
        assert dN.shape == (3, 6)

    def test_prism6_jacobian(self):
        """Test Jacobian computation for PRISM6"""
        # Create a unit prism element
        coords = np.array([
            [0, 0, 0],    # Bottom triangle
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1],    # Top triangle
            [1, 0, 1],
            [0, 1, 1],
        ])

        dN = prism6_shape_derivatives(0.33, 0.33, 0.0)
        J, det_J = compute_jacobian(coords, dN)

        assert J.shape == (3, 3)
        assert det_J > 0  # Positive Jacobian for valid element


class TestPYRAMID5ShapeFunctions:
    """Test PYRAMID5 shape functions"""

    def test_pyramid5_shape_functions_partition_of_unity(self):
        """Test PYRAMID5 shape functions sum to 1"""
        # At base center
        N = pyramid5_shape_functions(0.0, 0.0, 0.0)
        assert len(N) == 5
        assert np.isclose(np.sum(N), 1.0), f"Sum at base center: {np.sum(N)}"

        # Mid-height
        N = pyramid5_shape_functions(0.0, 0.0, 0.5)
        assert np.isclose(np.sum(N), 1.0), f"Sum at mid-height: {np.sum(N)}"

        # Near apex (not exactly at apex to avoid singularity)
        N = pyramid5_shape_functions(0.0, 0.0, 0.9)
        assert np.isclose(np.sum(N), 1.0), f"Sum near apex: {np.sum(N)}"

        # At apex
        N = pyramid5_shape_functions(0.0, 0.0, 1.0)
        assert np.isclose(np.sum(N), 1.0), f"Sum at apex: {np.sum(N)}"

    def test_pyramid5_corner_nodes(self):
        """Test PYRAMID5 shape functions at corner nodes"""
        # Base corner node 0: (-1, -1, 0)
        N = pyramid5_shape_functions(-1.0, -1.0, 0.0)
        assert np.isclose(N[0], 1.0)
        for i in range(1, 5):
            assert np.isclose(N[i], 0.0)

        # Base corner node 1: (1, -1, 0)
        N = pyramid5_shape_functions(1.0, -1.0, 0.0)
        assert np.isclose(N[1], 1.0)
        assert np.isclose(N[0], 0.0)

        # Apex node 4: (0, 0, 1)
        N = pyramid5_shape_functions(0.0, 0.0, 1.0)
        assert np.isclose(N[4], 1.0)
        for i in range(4):
            assert np.isclose(N[i], 0.0)

    def test_pyramid5_shape_derivatives_shape(self):
        """Test PYRAMID5 derivatives have correct shape"""
        dN = pyramid5_shape_derivatives(0.0, 0.0, 0.5)
        assert dN.shape == (3, 5)

    def test_pyramid5_jacobian(self):
        """Test Jacobian computation for PYRAMID5"""
        # Create a unit pyramid element
        coords = np.array([
            [-1, -1, 0],  # Base corners
            [1, -1, 0],
            [1, 1, 0],
            [-1, 1, 0],
            [0, 0, 1],    # Apex
        ])

        # Test at base center (avoid apex where derivatives are undefined)
        dN = pyramid5_shape_derivatives(0.0, 0.0, 0.0)
        J, det_J = compute_jacobian(coords, dN)

        assert J.shape == (3, 3)
        assert det_J > 0  # Positive Jacobian for valid element


class TestShapeFunctionGetters:
    """Test shape function utility functions"""

    def test_get_shape_functions_prism6(self):
        """Test getting PRISM6 shape functions"""
        shape_func, shape_deriv = get_shape_functions('prism6')
        assert callable(shape_func)
        assert callable(shape_deriv)

        N = shape_func(0.33, 0.33, 0.0)
        assert len(N) == 6
        assert np.isclose(np.sum(N), 1.0)

    def test_get_shape_functions_pyramid5(self):
        """Test getting PYRAMID5 shape functions"""
        shape_func, shape_deriv = get_shape_functions('pyramid5')
        assert callable(shape_func)
        assert callable(shape_deriv)

        N = shape_func(0.0, 0.0, 0.5)
        assert len(N) == 5
        assert np.isclose(np.sum(N), 1.0)


class TestMeshData:
    """Test mesh data with prism and pyramid elements"""

    def test_create_prism6_element(self):
        """Test creating PRISM6 element"""
        mesh = MeshData(element_type=ElementType.PRISM6)

        # Add 6 nodes
        node_ids = []
        for i in range(6):
            nid = mesh.add_node(float(i), 0.0, 0.0)
            node_ids.append(nid)

        # Add element
        eid = mesh.add_element(node_ids, element_type=ElementType.PRISM6)

        assert mesh.num_elements() == 1
        elem = mesh.get_element(eid)
        assert elem.type == ElementType.PRISM6
        assert len(elem.nodes) == 6

    def test_create_pyramid5_element(self):
        """Test creating PYRAMID5 element"""
        mesh = MeshData(element_type=ElementType.PYRAMID5)

        node_ids = []
        for i in range(5):
            nid = mesh.add_node(float(i), 0.0, 0.0)
            node_ids.append(nid)

        eid = mesh.add_element(node_ids, element_type=ElementType.PYRAMID5)

        elem = mesh.get_element(eid)
        assert elem.type == ElementType.PYRAMID5
        assert len(elem.nodes) == 5

    def test_prism6_element_validation(self):
        """Test PRISM6 node count validation"""
        mesh = MeshData(element_type=ElementType.PRISM6)

        # Create nodes first
        for i in range(1, 5):
            mesh.add_node(float(i), 0.0, 0.0, node_id=i)

        # Try to add element with wrong number of nodes
        with pytest.raises(ValueError, match="requires 6 nodes"):
            mesh.add_element([1, 2, 3, 4], element_type=ElementType.PRISM6)

    def test_pyramid5_element_validation(self):
        """Test PYRAMID5 node count validation"""
        mesh = MeshData(element_type=ElementType.PYRAMID5)

        # Create nodes first
        for i in range(1, 4):
            mesh.add_node(float(i), 0.0, 0.0, node_id=i)

        # Try to add element with wrong number of nodes
        with pytest.raises(ValueError, match="requires 5 nodes"):
            mesh.add_element([1, 2, 3], element_type=ElementType.PYRAMID5)


class TestFaceNodes:
    """Test face node extraction for prism and pyramid elements"""

    def test_prism6_face_nodes(self):
        """Test PRISM6 face node extraction"""
        mesh = MeshData(element_type=ElementType.PRISM6)

        node_ids = list(range(1, 7))
        for i, nid in enumerate(node_ids):
            mesh.add_node(float(i), 0.0, 0.0, node_id=nid)

        elem = Element(id=1, type=ElementType.PRISM6, nodes=node_ids)

        # PRISM6 has 5 faces
        # Face 0: bottom triangle (3 nodes)
        face0 = elem.get_face_nodes(0)
        assert len(face0) == 3

        # Face 1: top triangle (3 nodes)
        face1 = elem.get_face_nodes(1)
        assert len(face1) == 3

        # Faces 2-4: rectangular sides (4 nodes each)
        for face_id in [2, 3, 4]:
            face = elem.get_face_nodes(face_id)
            assert len(face) == 4

    def test_pyramid5_face_nodes(self):
        """Test PYRAMID5 face node extraction"""
        mesh = MeshData(element_type=ElementType.PYRAMID5)

        node_ids = list(range(1, 6))
        for i, nid in enumerate(node_ids):
            mesh.add_node(float(i), 0.0, 0.0, node_id=nid)

        elem = Element(id=1, type=ElementType.PYRAMID5, nodes=node_ids)

        # PYRAMID5 has 5 faces
        # Face 0: base (square, 4 nodes)
        face0 = elem.get_face_nodes(0)
        assert len(face0) == 4

        # Faces 1-4: triangular sides (3 nodes each)
        for face_id in [1, 2, 3, 4]:
            face = elem.get_face_nodes(face_id)
            assert len(face) == 3


class TestLSDynaExport:
    """Test LS-DYNA export for prism and pyramid elements"""

    def test_prism6_export_format(self):
        """Test PRISM6 LS-DYNA format"""
        from koomesh.export.lsdyna_writer import LSDynaWriter
        import tempfile
        import os

        mesh = MeshData(element_type=ElementType.PRISM6)

        # Create a PRISM6 element
        node_ids = []
        for i in range(6):
            nid = mesh.add_node(float(i), float(i), float(i))
            node_ids.append(nid)

        mesh.add_element(node_ids, element_type=ElementType.PRISM6)

        # Write to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.k', delete=False) as f:
            temp_path = f.name

        try:
            with LSDynaWriter(temp_path) as writer:
                writer.write_header()
                writer.write_nodes(mesh)
                writer.write_elements(mesh)

            # Read file and check format
            with open(temp_path, 'r') as f:
                content = f.read()

            assert '*ELEMENT_SOLID' in content
            assert 'PRISM6' in content
            # PRISM6 elements should be padded to 8 nodes per line
            assert len(content.split('\n')) > 10

        finally:
            # Cleanup
            os.unlink(temp_path)

    def test_pyramid5_export_format(self):
        """Test PYRAMID5 LS-DYNA format"""
        from koomesh.export.lsdyna_writer import LSDynaWriter
        import tempfile
        import os

        mesh = MeshData(element_type=ElementType.PYRAMID5)

        node_ids = []
        for i in range(5):
            nid = mesh.add_node(float(i), float(i), float(i))
            node_ids.append(nid)

        mesh.add_element(node_ids, element_type=ElementType.PYRAMID5)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.k', delete=False) as f:
            temp_path = f.name

        try:
            with LSDynaWriter(temp_path) as writer:
                writer.write_header()
                writer.write_nodes(mesh)
                writer.write_elements(mesh)

            with open(temp_path, 'r') as f:
                content = f.read()

            assert '*ELEMENT_SOLID' in content
            assert 'PYRAMID5' in content

        finally:
            os.unlink(temp_path)


class TestQualityChecker:
    """Test quality checking for prism and pyramid elements"""

    def test_prism6_quality(self):
        """Test quality checking for PRISM6 elements"""
        from koomesh.meshing.quality_checker import QualityChecker

        mesh = MeshData(element_type=ElementType.PRISM6)

        # Create a valid unit prism
        coords = [
            [0, 0, 0], [1, 0, 0], [0, 1, 0],  # Bottom triangle
            [0, 0, 1], [1, 0, 1], [0, 1, 1],  # Top triangle
        ]
        node_ids = []
        for x, y, z in coords:
            nid = mesh.add_node(x, y, z)
            node_ids.append(nid)

        mesh.add_element(node_ids, element_type=ElementType.PRISM6)

        checker = QualityChecker()
        report = checker.check_mesh(mesh)

        assert report.jacobian is not None
        assert report.jacobian['min'] > 0  # Valid element should have positive Jacobian
        assert report.num_elements == 1

    def test_pyramid5_quality(self):
        """Test quality checking for PYRAMID5 elements"""
        from koomesh.meshing.quality_checker import QualityChecker

        mesh = MeshData(element_type=ElementType.PYRAMID5)

        # Create a valid unit pyramid
        coords = [
            [-1, -1, 0], [1, -1, 0], [1, 1, 0], [-1, 1, 0],  # Base
            [0, 0, 1],  # Apex
        ]
        node_ids = []
        for x, y, z in coords:
            nid = mesh.add_node(x, y, z)
            node_ids.append(nid)

        mesh.add_element(node_ids, element_type=ElementType.PYRAMID5)

        checker = QualityChecker()
        report = checker.check_mesh(mesh)

        assert report.jacobian is not None
        assert report.jacobian['min'] > 0
        assert report.num_elements == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
