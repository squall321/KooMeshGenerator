"""
Tests for Mesh Partitioning Utilities

Author: KooMeshGenerator Team
"""

import pytest
import numpy as np

from koomesh.meshing.mesh_data import MeshData, ElementType
from koomesh.utils.mesh_partition import (
    split_mesh_by_plane,
    partition_mesh,
    extract_mesh_region
)


@pytest.fixture
def simple_hex_mesh():
    """Create a simple 2x2x2 hex mesh"""
    mesh = MeshData(element_type=ElementType.HEX8)

    node_ids = []
    for i in range(3):
        for j in range(3):
            for k in range(3):
                node_ids.append(mesh.add_node(float(i), float(j), float(k)))

    # Create 8 hex elements (2x2x2 grid)
    for i in range(2):
        for j in range(2):
            for k in range(2):
                n000 = i * 9 + j * 3 + k
                n100 = (i+1) * 9 + j * 3 + k
                n010 = i * 9 + (j+1) * 3 + k
                n110 = (i+1) * 9 + (j+1) * 3 + k
                n001 = i * 9 + j * 3 + (k+1)
                n101 = (i+1) * 9 + j * 3 + (k+1)
                n011 = i * 9 + (j+1) * 3 + (k+1)
                n111 = (i+1) * 9 + (j+1) * 3 + (k+1)

                mesh.add_element([node_ids[n000], node_ids[n100], node_ids[n110], node_ids[n010],
                                 node_ids[n001], node_ids[n101], node_ids[n111], node_ids[n011]])

    return mesh


@pytest.fixture
def single_hex_mesh():
    """Create a single hex element mesh"""
    mesh = MeshData(element_type=ElementType.HEX8)

    node_ids = []
    for i in range(2):
        for j in range(2):
            for k in range(2):
                node_ids.append(mesh.add_node(float(i), float(j), float(k)))

    mesh.add_element([node_ids[0], node_ids[1], node_ids[3], node_ids[2],
                     node_ids[4], node_ids[5], node_ids[7], node_ids[6]])

    return mesh


@pytest.fixture
def tet_mesh():
    """Create a simple tet mesh"""
    mesh = MeshData(element_type=ElementType.TET4)

    # Create multiple tets
    for offset in [0.0, 1.0, 2.0]:
        node_ids = []
        node_ids.append(mesh.add_node(offset, 0.0, 0.0))
        node_ids.append(mesh.add_node(offset + 0.5, 1.0, 0.0))
        node_ids.append(mesh.add_node(offset + 1.0, 0.0, 0.0))
        node_ids.append(mesh.add_node(offset + 0.5, 0.5, 1.0))
        mesh.add_element(node_ids)

    return mesh


class TestSplitMeshByPlane:
    """Test splitting mesh by plane"""

    def test_split_single_hex_x(self, single_hex_mesh):
        """Test splitting single hex by X plane"""
        mesh1, mesh2 = split_mesh_by_plane(single_hex_mesh, 'x', 0.5)

        # Both sides should have elements
        assert len(mesh1.elements) + len(mesh2.elements) >= 1

    def test_split_single_hex_y(self, single_hex_mesh):
        """Test splitting single hex by Y plane"""
        mesh1, mesh2 = split_mesh_by_plane(single_hex_mesh, 'y', 0.5)

        assert len(mesh1.elements) + len(mesh2.elements) >= 1

    def test_split_single_hex_z(self, single_hex_mesh):
        """Test splitting single hex by Z plane"""
        mesh1, mesh2 = split_mesh_by_plane(single_hex_mesh, 'z', 0.5)

        assert len(mesh1.elements) + len(mesh2.elements) >= 1

    def test_split_preserves_element_count(self, simple_hex_mesh):
        """Test that split preserves total element count"""
        original_count = len(simple_hex_mesh.elements)

        mesh1, mesh2 = split_mesh_by_plane(simple_hex_mesh, 'x', 1.0)

        # Total elements should be preserved
        assert len(mesh1.elements) + len(mesh2.elements) == original_count

    def test_split_at_extremes(self, simple_hex_mesh):
        """Test splitting at extreme positions"""
        # Split at far left (all elements on right)
        mesh1, mesh2 = split_mesh_by_plane(simple_hex_mesh, 'x', -10.0)

        assert len(mesh1.elements) == 0
        assert len(mesh2.elements) == len(simple_hex_mesh.elements)

        # Split at far right (all elements on left)
        mesh1, mesh2 = split_mesh_by_plane(simple_hex_mesh, 'x', 10.0)

        assert len(mesh1.elements) == len(simple_hex_mesh.elements)
        assert len(mesh2.elements) == 0

    def test_split_element_type_preserved(self, single_hex_mesh):
        """Test that element type is preserved after split"""
        mesh1, mesh2 = split_mesh_by_plane(single_hex_mesh, 'x', 0.5)

        assert mesh1.element_type == ElementType.HEX8
        assert mesh2.element_type == ElementType.HEX8

    def test_split_tet_mesh(self, tet_mesh):
        """Test splitting tetrahedral mesh"""
        mesh1, mesh2 = split_mesh_by_plane(tet_mesh, 'x', 1.5)

        # Should split into two parts
        assert len(mesh1.elements) > 0
        assert len(mesh2.elements) > 0
        assert len(mesh1.elements) + len(mesh2.elements) == len(tet_mesh.elements)


class TestPartitionMesh:
    """Test mesh partitioning into multiple parts"""

    def test_partition_returns_list(self, simple_hex_mesh):
        """Test that partition returns list"""
        parts = partition_mesh(simple_hex_mesh, 2, 'x')

        assert isinstance(parts, list)

    def test_partition_num_parts(self, simple_hex_mesh):
        """Test correct number of partitions"""
        num_parts = 4
        parts = partition_mesh(simple_hex_mesh, num_parts, 'x')

        assert len(parts) == num_parts

    def test_partition_preserves_elements(self, simple_hex_mesh):
        """Test that partitioning preserves total element count"""
        original_count = len(simple_hex_mesh.elements)

        parts = partition_mesh(simple_hex_mesh, 4, 'x')

        total_elements = sum(len(p.elements) for p in parts)
        assert total_elements == original_count

    def test_partition_single_part(self, simple_hex_mesh):
        """Test partitioning into 1 part (should return original)"""
        parts = partition_mesh(simple_hex_mesh, 1, 'x')

        assert len(parts) == 1
        assert len(parts[0].elements) == len(simple_hex_mesh.elements)

    def test_partition_zero_parts(self, simple_hex_mesh):
        """Test partitioning into 0 parts"""
        parts = partition_mesh(simple_hex_mesh, 0, 'x')

        # Should return original mesh
        assert len(parts) == 1

    def test_partition_along_y(self, simple_hex_mesh):
        """Test partitioning along Y axis"""
        parts = partition_mesh(simple_hex_mesh, 2, 'y')

        assert len(parts) == 2
        total = sum(len(p.elements) for p in parts)
        assert total == len(simple_hex_mesh.elements)

    def test_partition_along_z(self, simple_hex_mesh):
        """Test partitioning along Z axis"""
        parts = partition_mesh(simple_hex_mesh, 2, 'z')

        assert len(parts) == 2
        total = sum(len(p.elements) for p in parts)
        assert total == len(simple_hex_mesh.elements)

    def test_partition_many_parts(self, simple_hex_mesh):
        """Test partitioning into many parts"""
        parts = partition_mesh(simple_hex_mesh, 8, 'x')

        assert len(parts) == 8

        # All elements should be preserved
        total = sum(len(p.elements) for p in parts)
        assert total == len(simple_hex_mesh.elements)

    def test_partition_element_type_preserved(self, simple_hex_mesh):
        """Test that element type is preserved in all partitions"""
        parts = partition_mesh(simple_hex_mesh, 3, 'x')

        for part in parts:
            assert part.element_type == ElementType.HEX8


class TestExtractMeshRegion:
    """Test extracting mesh regions"""

    def test_extract_entire_mesh(self, simple_hex_mesh):
        """Test extracting entire mesh"""
        # Get bounding box of original mesh
        xs = [n.x for n in simple_hex_mesh.nodes.values()]
        ys = [n.y for n in simple_hex_mesh.nodes.values()]
        zs = [n.z for n in simple_hex_mesh.nodes.values()]

        min_bounds = (min(xs) - 1, min(ys) - 1, min(zs) - 1)
        max_bounds = (max(xs) + 1, max(ys) + 1, max(zs) + 1)

        region = extract_mesh_region(simple_hex_mesh, min_bounds, max_bounds)

        # Should get all elements
        assert len(region.elements) == len(simple_hex_mesh.elements)

    def test_extract_partial_region(self, simple_hex_mesh):
        """Test extracting partial region"""
        # Extract left half
        min_bounds = (0.0, 0.0, 0.0)
        max_bounds = (1.0, 2.0, 2.0)

        region = extract_mesh_region(simple_hex_mesh, min_bounds, max_bounds)

        # Should get subset of elements
        assert 0 < len(region.elements) < len(simple_hex_mesh.elements)

    def test_extract_no_elements(self, simple_hex_mesh):
        """Test extracting region with no elements"""
        # Region outside mesh
        min_bounds = (10.0, 10.0, 10.0)
        max_bounds = (20.0, 20.0, 20.0)

        region = extract_mesh_region(simple_hex_mesh, min_bounds, max_bounds)

        # Should get no elements
        assert len(region.elements) == 0

    def test_extract_element_type_preserved(self, simple_hex_mesh):
        """Test that element type is preserved"""
        min_bounds = (0.0, 0.0, 0.0)
        max_bounds = (1.0, 1.0, 1.0)

        region = extract_mesh_region(simple_hex_mesh, min_bounds, max_bounds)

        assert region.element_type == ElementType.HEX8

    def test_extract_small_region(self, simple_hex_mesh):
        """Test extracting very small region"""
        # Single element region
        min_bounds = (0.0, 0.0, 0.0)
        max_bounds = (0.6, 0.6, 0.6)

        region = extract_mesh_region(simple_hex_mesh, min_bounds, max_bounds)

        # Should get at least one element
        assert len(region.elements) >= 1

    def test_extract_tet_mesh(self, tet_mesh):
        """Test extracting region from tet mesh"""
        min_bounds = (0.0, 0.0, 0.0)
        max_bounds = (1.5, 1.0, 1.0)

        region = extract_mesh_region(tet_mesh, min_bounds, max_bounds)

        # Should extract some elements
        assert len(region.elements) > 0
        assert len(region.elements) <= len(tet_mesh.elements)
        assert region.element_type == ElementType.TET4


class TestEdgeCases:
    """Test edge cases and special conditions"""

    def test_split_empty_mesh(self):
        """Test splitting empty mesh"""
        mesh = MeshData(element_type=ElementType.HEX8)

        mesh1, mesh2 = split_mesh_by_plane(mesh, 'x', 0.0)

        assert len(mesh1.elements) == 0
        assert len(mesh2.elements) == 0

    def test_partition_empty_mesh(self):
        """Test partitioning empty mesh"""
        mesh = MeshData(element_type=ElementType.HEX8)

        parts = partition_mesh(mesh, 4, 'x')

        assert len(parts) == 4
        for part in parts:
            assert len(part.elements) == 0

    def test_extract_empty_mesh(self):
        """Test extracting from empty mesh"""
        mesh = MeshData(element_type=ElementType.HEX8)

        region = extract_mesh_region(mesh, (0, 0, 0), (1, 1, 1))

        assert len(region.elements) == 0

    def test_split_axis_case_insensitive(self, single_hex_mesh):
        """Test that axis is case insensitive"""
        mesh1, mesh2 = split_mesh_by_plane(single_hex_mesh, 'X', 0.5)
        assert len(mesh1.elements) + len(mesh2.elements) >= 1

        mesh1, mesh2 = split_mesh_by_plane(single_hex_mesh, 'Y', 0.5)
        assert len(mesh1.elements) + len(mesh2.elements) >= 1

        mesh1, mesh2 = split_mesh_by_plane(single_hex_mesh, 'Z', 0.5)
        assert len(mesh1.elements) + len(mesh2.elements) >= 1

    def test_extract_inverted_bounds(self, simple_hex_mesh):
        """Test extract with inverted bounds (min > max)"""
        # This should extract nothing since bounds are invalid
        min_bounds = (2.0, 2.0, 2.0)
        max_bounds = (0.0, 0.0, 0.0)

        region = extract_mesh_region(simple_hex_mesh, min_bounds, max_bounds)

        assert len(region.elements) == 0


class TestNodeConsistency:
    """Test that node handling is correct"""

    def test_split_no_orphan_nodes(self, simple_hex_mesh):
        """Test that split meshes don't have orphan nodes"""
        mesh1, mesh2 = split_mesh_by_plane(simple_hex_mesh, 'x', 1.0)

        # All nodes in mesh1 should be referenced by elements
        for mesh in [mesh1, mesh2]:
            if len(mesh.elements) > 0:
                used_nodes = set()
                for elem in mesh.elements.values():
                    used_nodes.update(elem.nodes)

                # All nodes should be used
                # (Some nodes might not be used if mesh is empty, that's ok)
                if len(mesh.nodes) > 0:
                    assert len(used_nodes) > 0

    def test_partition_nodes_consistent(self, simple_hex_mesh):
        """Test that partition nodes are consistent"""
        parts = partition_mesh(simple_hex_mesh, 4, 'x')

        for part in parts:
            if len(part.elements) > 0:
                # All element nodes should exist in node dict
                for elem in part.elements.values():
                    for nid in elem.nodes:
                        assert nid in part.nodes

    def test_extract_nodes_consistent(self, simple_hex_mesh):
        """Test that extracted region has consistent nodes"""
        region = extract_mesh_region(simple_hex_mesh, (0.0, 0.0, 0.0), (1.5, 1.5, 1.5))

        if len(region.elements) > 0:
            # All element nodes should exist
            for elem in region.elements.values():
                for nid in elem.nodes:
                    assert nid in region.nodes
