"""
Mesh Partitioning Utilities
============================

Split and partition meshes for parallel processing.

Author: KooMeshGenerator Team
"""

import numpy as np
from typing import List, Tuple
from koomesh.meshing.mesh_data import MeshData


def split_mesh_by_plane(mesh: MeshData, axis: str = 'x', position: float = 0.0) -> Tuple[MeshData, MeshData]:
    """
    Split mesh by plane

    Args:
        mesh: Mesh to split
        axis: Axis perpendicular to split plane ('x', 'y', or 'z')
        position: Position of split plane

    Returns:
        Tuple of (mesh1, mesh2)

    Example:
        >>> left, right = split_mesh_by_plane(mesh, 'x', 0.0)
    """
    mesh1 = MeshData(element_type=mesh.element_type)
    mesh2 = MeshData(element_type=mesh.element_type)

    # Determine which side each element is on
    for elem in mesh.elements.values():
        nodes = [mesh.nodes[nid] for nid in elem.nodes]

        # Get center position
        if axis.lower() == 'x':
            center = np.mean([n.x for n in nodes])
        elif axis.lower() == 'y':
            center = np.mean([n.y for n in nodes])
        else:  # z
            center = np.mean([n.z for n in nodes])

        # Add to appropriate mesh
        target_mesh = mesh1 if center < position else mesh2

        # Add nodes - find or create
        node_map = {}
        for nid in elem.nodes:
            node = mesh.nodes[nid]

            # Check if node already exists by coordinates
            found = False
            for existing_nid, existing_node in target_mesh.nodes.items():
                if (abs(existing_node.x - node.x) < 1e-10 and
                    abs(existing_node.y - node.y) < 1e-10 and
                    abs(existing_node.z - node.z) < 1e-10):
                    node_map[nid] = existing_nid
                    found = True
                    break

            # Add new node if not found
            if not found:
                new_nid = target_mesh.add_node(node.x, node.y, node.z)
                node_map[nid] = new_nid

        # Add element with mapped nodes
        new_nodes = [node_map[nid] for nid in elem.nodes]
        target_mesh.add_element(new_nodes, element_type=elem.type)

    return mesh1, mesh2


def partition_mesh(mesh: MeshData, num_parts: int, axis: str = 'x') -> List[MeshData]:
    """
    Partition mesh into multiple parts

    Args:
        mesh: Mesh to partition
        num_parts: Number of partitions
        axis: Axis along which to partition

    Returns:
        List of mesh partitions

    Example:
        >>> parts = partition_mesh(mesh, 4, 'x')
    """
    if num_parts < 2:
        return [mesh]

    # Handle empty mesh
    if not mesh.nodes:
        return [MeshData(element_type=mesh.element_type) for _ in range(num_parts)]

    # Get bounding box
    if axis.lower() == 'x':
        coords = [n.x for n in mesh.nodes.values()]
    elif axis.lower() == 'y':
        coords = [n.y for n in mesh.nodes.values()]
    else:
        coords = [n.z for n in mesh.nodes.values()]

    min_coord = min(coords)
    max_coord = max(coords)

    # Create split positions
    step = (max_coord - min_coord) / num_parts
    positions = [min_coord + i * step for i in range(1, num_parts)]

    # Recursively split
    current_meshes = [mesh]

    for pos in positions:
        new_meshes = []
        for m in current_meshes[:-1]:
            new_meshes.append(m)

        # Split the last mesh
        m1, m2 = split_mesh_by_plane(current_meshes[-1], axis, pos)
        new_meshes.append(m1)
        new_meshes.append(m2)

        current_meshes = new_meshes

    return current_meshes


def extract_mesh_region(mesh: MeshData, min_bounds: Tuple[float, float, float],
                        max_bounds: Tuple[float, float, float]) -> MeshData:
    """
    Extract mesh region within bounding box

    Args:
        mesh: Source mesh
        min_bounds: (x_min, y_min, z_min)
        max_bounds: (x_max, y_max, z_max)

    Returns:
        New mesh with elements in region

    Example:
        >>> region = extract_mesh_region(mesh, (0, 0, 0), (10, 10, 10))
    """
    result = MeshData(element_type=mesh.element_type)

    x_min, y_min, z_min = min_bounds
    x_max, y_max, z_max = max_bounds

    # Find elements in region
    for elem in mesh.elements.values():
        nodes = [mesh.nodes[nid] for nid in elem.nodes]

        # Check if element center is in bounds
        cx = np.mean([n.x for n in nodes])
        cy = np.mean([n.y for n in nodes])
        cz = np.mean([n.z for n in nodes])

        if (x_min <= cx <= x_max and
            y_min <= cy <= y_max and
            z_min <= cz <= z_max):

            # Add nodes
            node_map = {}
            for nid in elem.nodes:
                node = mesh.nodes[nid]
                new_nid = result.add_node(node.x, node.y, node.z)
                node_map[nid] = new_nid

            # Add element
            new_nodes = [node_map[nid] for nid in elem.nodes]
            result.add_element(new_nodes, element_type=elem.type)

    return result
