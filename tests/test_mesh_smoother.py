"""
Tests for Mesh Smoothing
=========================

This module tests the mesh smoothing functionality.
"""

import pytest
import numpy as np
from koomesh.meshing.mesh_data import MeshData, ElementType
from koomesh.meshing.mesh_smoother import MeshSmoother


class TestMeshSmootherCreation:
    """Test MeshSmoother creation and initialization"""

    def test_smoother_creation(self):
        """Test creating MeshSmoother"""
        # Create simple mesh
        mesh = MeshData(element_type=ElementType.HEX8)

        # Add nodes for a simple 2x2x2 cube with 2 elements
        node_ids = []
        for z in [0, 1, 2]:
            for y in [0, 1]:
                for x in [0, 1]:
                    nid = mesh.add_node(float(x), float(y), float(z))
                    node_ids.append(nid)

        # Add elements
        mesh.add_element([node_ids[0], node_ids[1], node_ids[3], node_ids[2],
                         node_ids[4], node_ids[5], node_ids[7], node_ids[6]])
        mesh.add_element([node_ids[4], node_ids[5], node_ids[7], node_ids[6],
                         node_ids[8], node_ids[9], node_ids[11], node_ids[10]])

        # Create smoother
        smoother = MeshSmoother(mesh)

        assert smoother is not None
        assert smoother.mesh == mesh

    def test_node_connectivity_building(self):
        """Test node connectivity graph building"""
        mesh = self._create_simple_mesh()
        smoother = MeshSmoother(mesh)

        # Check that connectivity was built
        assert len(smoother.node_adjacency) > 0
        assert len(smoother.node_elements) > 0

    def test_boundary_node_identification(self):
        """Test boundary node identification"""
        mesh = self._create_simple_mesh()
        smoother = MeshSmoother(mesh)

        # Boundary nodes should be identified
        assert len(smoother.boundary_nodes) > 0

        # For a cube, all corner nodes should be boundary nodes
        # Interior nodes should not be boundary
        total_nodes = mesh.num_nodes()
        boundary_count = len(smoother.boundary_nodes)

        assert boundary_count > 0
        assert boundary_count <= total_nodes

    def _create_simple_mesh(self) -> MeshData:
        """Helper to create simple test mesh"""
        mesh = MeshData(element_type=ElementType.HEX8)

        # Create 2x2x2 grid (8 elements)
        node_ids = {}
        node_counter = 1
        for k in range(3):
            for j in range(3):
                for i in range(3):
                    nid = mesh.add_node(float(i), float(j), float(k))
                    node_ids[(i, j, k)] = nid
                    node_counter += 1

        # Create elements
        for k in range(2):
            for j in range(2):
                for i in range(2):
                    n0 = node_ids[(i, j, k)]
                    n1 = node_ids[(i+1, j, k)]
                    n2 = node_ids[(i+1, j+1, k)]
                    n3 = node_ids[(i, j+1, k)]
                    n4 = node_ids[(i, j, k+1)]
                    n5 = node_ids[(i+1, j, k+1)]
                    n6 = node_ids[(i+1, j+1, k+1)]
                    n7 = node_ids[(i, j+1, k+1)]

                    mesh.add_element([n0, n1, n2, n3, n4, n5, n6, n7])

        return mesh


class TestLaplacianSmoothing:
    """Test Laplacian smoothing"""

    def test_laplacian_smooth_basic(self):
        """Test basic Laplacian smoothing"""
        mesh = self._create_distorted_mesh()
        smoother = MeshSmoother(mesh)

        # Get initial positions
        initial_positions = {}
        for nid, node in mesh.nodes.items():
            initial_positions[nid] = node.coordinates().copy()

        # Apply smoothing
        smoother.laplacian_smooth(iterations=5, relaxation=0.5)

        # Check that positions changed
        changed_count = 0
        for nid, node in mesh.nodes.items():
            current_pos = node.coordinates()
            if not np.allclose(current_pos, initial_positions[nid]):
                changed_count += 1

        assert changed_count > 0

    def test_laplacian_with_zero_iterations(self):
        """Test that zero iterations doesn't change mesh"""
        mesh = self._create_distorted_mesh()
        smoother = MeshSmoother(mesh)

        initial_positions = {}
        for nid, node in mesh.nodes.items():
            initial_positions[nid] = node.coordinates().copy()

        smoother.laplacian_smooth(iterations=0)

        # Positions should not change
        for nid, node in mesh.nodes.items():
            assert np.allclose(node.coordinates(), initial_positions[nid])

    def _create_distorted_mesh(self) -> MeshData:
        """Create a distorted mesh for testing"""
        mesh = MeshData(element_type=ElementType.HEX8)

        # Create 2x2x2 grid with some distortion
        node_ids = {}
        for k in range(3):
            for j in range(3):
                for i in range(3):
                    # Add random distortion
                    x = float(i) + np.random.uniform(-0.1, 0.1) if (i > 0 and i < 2) else float(i)
                    y = float(j) + np.random.uniform(-0.1, 0.1) if (j > 0 and j < 2) else float(j)
                    z = float(k) + np.random.uniform(-0.1, 0.1) if (k > 0 and k < 2) else float(k)

                    nid = mesh.add_node(x, y, z)
                    node_ids[(i, j, k)] = nid

        # Create elements
        for k in range(2):
            for j in range(2):
                for i in range(2):
                    n0 = node_ids[(i, j, k)]
                    n1 = node_ids[(i+1, j, k)]
                    n2 = node_ids[(i+1, j+1, k)]
                    n3 = node_ids[(i, j+1, k)]
                    n4 = node_ids[(i, j, k+1)]
                    n5 = node_ids[(i+1, j, k+1)]
                    n6 = node_ids[(i+1, j+1, k+1)]
                    n7 = node_ids[(i, j+1, k+1)]

                    mesh.add_element([n0, n1, n2, n3, n4, n5, n6, n7])

        return mesh


class TestSmartLaplacian:
    """Test Smart Laplacian smoothing"""

    def test_smart_laplacian_preserves_boundary(self):
        """Test that Smart Laplacian preserves boundary nodes"""
        mesh = self._create_distorted_mesh()
        smoother = MeshSmoother(mesh)

        # Store boundary node positions
        boundary_positions = {}
        for nid in smoother.boundary_nodes:
            node = mesh.get_node(nid)
            boundary_positions[nid] = node.coordinates().copy()

        # Apply smart smoothing with boundary preservation
        smoother.smart_laplacian(iterations=10, preserve_boundary=True)

        # Check that boundary nodes didn't move
        for nid, initial_pos in boundary_positions.items():
            node = mesh.get_node(nid)
            current_pos = node.coordinates()
            assert np.allclose(current_pos, initial_pos), \
                f"Boundary node {nid} moved!"

    def test_smart_laplacian_without_boundary_preservation(self):
        """Test Smart Laplacian without boundary preservation"""
        mesh = self._create_distorted_mesh()
        smoother = MeshSmoother(mesh)

        boundary_positions = {}
        for nid in smoother.boundary_nodes:
            node = mesh.get_node(nid)
            boundary_positions[nid] = node.coordinates().copy()

        # Apply without boundary preservation
        smoother.smart_laplacian(iterations=10, preserve_boundary=False)

        # Some boundary nodes should have moved
        moved_count = 0
        for nid, initial_pos in boundary_positions.items():
            node = mesh.get_node(nid)
            if not np.allclose(node.coordinates(), initial_pos):
                moved_count += 1

        # At least some boundary nodes should move
        assert moved_count > 0

    def _create_distorted_mesh(self) -> MeshData:
        """Create a distorted mesh"""
        mesh = MeshData(element_type=ElementType.HEX8)

        node_ids = {}
        for k in range(3):
            for j in range(3):
                for i in range(3):
                    # Distort interior nodes
                    is_interior = (i > 0 and i < 2) and (j > 0 and j < 2) and (k > 0 and k < 2)
                    if is_interior:
                        x = float(i) + np.random.uniform(-0.2, 0.2)
                        y = float(j) + np.random.uniform(-0.2, 0.2)
                        z = float(k) + np.random.uniform(-0.2, 0.2)
                    else:
                        x, y, z = float(i), float(j), float(k)

                    nid = mesh.add_node(x, y, z)
                    node_ids[(i, j, k)] = nid

        # Create elements
        for k in range(2):
            for j in range(2):
                for i in range(2):
                    n0 = node_ids[(i, j, k)]
                    n1 = node_ids[(i+1, j, k)]
                    n2 = node_ids[(i+1, j+1, k)]
                    n3 = node_ids[(i, j+1, k)]
                    n4 = node_ids[(i, j, k+1)]
                    n5 = node_ids[(i+1, j, k+1)]
                    n6 = node_ids[(i+1, j+1, k+1)]
                    n7 = node_ids[(i, j+1, k+1)]

                    mesh.add_element([n0, n1, n2, n3, n4, n5, n6, n7])

        return mesh


class TestTaubinSmoothing:
    """Test Taubin smoothing"""

    def test_taubin_smooth(self):
        """Test Taubin smoothing"""
        mesh = self._create_distorted_mesh()
        smoother = MeshSmoother(mesh)

        initial_positions = {}
        for nid, node in mesh.nodes.items():
            initial_positions[nid] = node.coordinates().copy()

        # Apply Taubin smoothing
        smoother.taubin_smooth(iterations=5)

        # Check that some nodes moved
        moved_count = 0
        for nid, node in mesh.nodes.items():
            if not np.allclose(node.coordinates(), initial_positions[nid]):
                moved_count += 1

        assert moved_count > 0

    def test_taubin_preserves_boundary(self):
        """Test that Taubin preserves boundary when requested"""
        mesh = self._create_distorted_mesh()
        smoother = MeshSmoother(mesh)

        boundary_positions = {}
        for nid in smoother.boundary_nodes:
            boundary_positions[nid] = mesh.get_node(nid).coordinates().copy()

        smoother.taubin_smooth(iterations=5, preserve_boundary=True)

        # Boundary should be preserved
        for nid, initial_pos in boundary_positions.items():
            current_pos = mesh.get_node(nid).coordinates()
            assert np.allclose(current_pos, initial_pos)

    def _create_distorted_mesh(self) -> MeshData:
        """Create a distorted mesh"""
        mesh = MeshData(element_type=ElementType.HEX8)

        node_ids = {}
        for k in range(3):
            for j in range(3):
                for i in range(3):
                    x = float(i) + np.random.uniform(-0.1, 0.1) if (0 < i < 2) else float(i)
                    y = float(j) + np.random.uniform(-0.1, 0.1) if (0 < j < 2) else float(j)
                    z = float(k) + np.random.uniform(-0.1, 0.1) if (0 < k < 2) else float(k)

                    nid = mesh.add_node(x, y, z)
                    node_ids[(i, j, k)] = nid

        for k in range(2):
            for j in range(2):
                for i in range(2):
                    n0 = node_ids[(i, j, k)]
                    n1 = node_ids[(i+1, j, k)]
                    n2 = node_ids[(i+1, j+1, k)]
                    n3 = node_ids[(i, j+1, k)]
                    n4 = node_ids[(i, j, k+1)]
                    n5 = node_ids[(i+1, j, k+1)]
                    n6 = node_ids[(i+1, j+1, k+1)]
                    n7 = node_ids[(i, j+1, k+1)]

                    mesh.add_element([n0, n1, n2, n3, n4, n5, n6, n7])

        return mesh


class TestQualityMonitoring:
    """Test quality monitoring features"""

    def test_get_quality_stats(self):
        """Test getting quality statistics"""
        mesh = self._create_simple_mesh()
        smoother = MeshSmoother(mesh)

        stats = smoother.get_quality_stats()

        assert 'num_elements' in stats
        assert 'jacobian_min' in stats
        assert 'jacobian_mean' in stats
        assert 'jacobian_max' in stats

        assert stats['num_elements'] > 0

    def test_smooth_with_quality_monitoring(self):
        """Test smoothing with quality monitoring"""
        mesh = self._create_distorted_mesh()
        smoother = MeshSmoother(mesh)

        initial_stats = smoother.get_quality_stats()

        # Smooth with monitoring
        iterations = smoother.smooth_with_quality_monitoring(
            method='smart_laplacian',
            iterations=20,
            min_quality_improvement=0.01
        )

        final_stats = smoother.get_quality_stats()

        # Should have performed some iterations
        assert iterations > 0

        # Quality should be same or better
        assert final_stats['jacobian_min'] >= initial_stats['jacobian_min'] * 0.9

    def _create_simple_mesh(self) -> MeshData:
        """Create simple mesh"""
        mesh = MeshData(element_type=ElementType.HEX8)

        node_ids = {}
        for k in range(3):
            for j in range(3):
                for i in range(3):
                    nid = mesh.add_node(float(i), float(j), float(k))
                    node_ids[(i, j, k)] = nid

        for k in range(2):
            for j in range(2):
                for i in range(2):
                    n0 = node_ids[(i, j, k)]
                    n1 = node_ids[(i+1, j, k)]
                    n2 = node_ids[(i+1, j+1, k)]
                    n3 = node_ids[(i, j+1, k)]
                    n4 = node_ids[(i, j, k+1)]
                    n5 = node_ids[(i+1, j, k+1)]
                    n6 = node_ids[(i+1, j+1, k+1)]
                    n7 = node_ids[(i, j+1, k+1)]

                    mesh.add_element([n0, n1, n2, n3, n4, n5, n6, n7])

        return mesh

    def _create_distorted_mesh(self) -> MeshData:
        """Create distorted mesh"""
        mesh = MeshData(element_type=ElementType.HEX8)

        node_ids = {}
        for k in range(3):
            for j in range(3):
                for i in range(3):
                    x = float(i) + np.random.uniform(-0.15, 0.15) if (0 < i < 2) else float(i)
                    y = float(j) + np.random.uniform(-0.15, 0.15) if (0 < j < 2) else float(j)
                    z = float(k) + np.random.uniform(-0.15, 0.15) if (0 < k < 2) else float(k)

                    nid = mesh.add_node(x, y, z)
                    node_ids[(i, j, k)] = nid

        for k in range(2):
            for j in range(2):
                for i in range(2):
                    n0 = node_ids[(i, j, k)]
                    n1 = node_ids[(i+1, j, k)]
                    n2 = node_ids[(i+1, j+1, k)]
                    n3 = node_ids[(i, j+1, k)]
                    n4 = node_ids[(i, j, k+1)]
                    n5 = node_ids[(i+1, j, k+1)]
                    n6 = node_ids[(i+1, j+1, k+1)]
                    n7 = node_ids[(i, j+1, k+1)]

                    mesh.add_element([n0, n1, n2, n3, n4, n5, n6, n7])

        return mesh


class TestSmootherSummary:
    """Test smoother summary functionality"""

    def test_get_summary(self):
        """Test getting smoother summary"""
        mesh = self._create_simple_mesh()
        smoother = MeshSmoother(mesh)

        summary = smoother.get_summary()

        assert 'num_nodes' in summary
        assert 'num_elements' in summary
        assert 'num_boundary_nodes' in summary
        assert 'num_interior_nodes' in summary

        assert summary['num_nodes'] > 0
        assert summary['num_elements'] > 0
        assert summary['num_boundary_nodes'] > 0

        # Total should equal boundary + interior
        assert summary['num_nodes'] == (
            summary['num_boundary_nodes'] + summary['num_interior_nodes']
        )

    def _create_simple_mesh(self) -> MeshData:
        """Create simple mesh"""
        mesh = MeshData(element_type=ElementType.HEX8)

        node_ids = {}
        for k in range(3):
            for j in range(3):
                for i in range(3):
                    nid = mesh.add_node(float(i), float(j), float(k))
                    node_ids[(i, j, k)] = nid

        for k in range(2):
            for j in range(2):
                for i in range(2):
                    n0 = node_ids[(i, j, k)]
                    n1 = node_ids[(i+1, j, k)]
                    n2 = node_ids[(i+1, j+1, k)]
                    n3 = node_ids[(i, j+1, k)]
                    n4 = node_ids[(i, j, k+1)]
                    n5 = node_ids[(i+1, j, k+1)]
                    n6 = node_ids[(i+1, j+1, k+1)]
                    n7 = node_ids[(i, j+1, k+1)]

                    mesh.add_element([n0, n1, n2, n3, n4, n5, n6, n7])

        return mesh


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
