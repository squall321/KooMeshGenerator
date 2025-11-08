"""
Mesh Copy Utilities
===================

Create deep copies of mesh data with optional transformations.

Author: KooMeshGenerator Team
"""

import copy
from koomesh.meshing.mesh_data import MeshData


def copy_mesh(mesh: MeshData, deep: bool = True) -> MeshData:
    """
    Create a copy of the mesh

    Args:
        mesh: Mesh to copy
        deep: If True, create deep copy (default). If False, shallow copy.

    Returns:
        Copied MeshData

    Example:
        >>> mesh_copy = copy_mesh(original_mesh)
        >>> # Now you can modify mesh_copy without affecting original_mesh
    """
    if deep:
        # Create new mesh with same element type
        new_mesh = MeshData(element_type=mesh.element_type)

        # Copy all nodes
        for node_id, node in mesh.nodes.items():
            new_mesh.add_node(
                node.x, node.y, node.z,
                node_id=node_id,
                metadata=copy.deepcopy(node.metadata)
            )

        # Copy all elements
        for elem_id, elem in mesh.elements.items():
            new_mesh.add_element(
                elem.nodes.copy(),
                element_id=elem_id,
                element_type=elem.type,
                part_id=elem.part_id,
                metadata=copy.deepcopy(elem.metadata)
            )

        # Copy node sets
        for name, node_set in mesh.node_sets.items():
            new_mesh.node_sets[name] = node_set.copy()

        # Copy element sets
        for name, elem_set in mesh.element_sets.items():
            new_mesh.element_sets[name] = elem_set.copy()

        # Copy metadata
        new_mesh.metadata = copy.deepcopy(mesh.metadata)

        return new_mesh
    else:
        # Shallow copy (references same objects)
        return copy.copy(mesh)


def copy_mesh_subset(mesh: MeshData, element_ids: list) -> MeshData:
    """
    Create a copy of mesh containing only specified elements

    This creates a new mesh with only the specified elements and their
    associated nodes. Node IDs are preserved.

    Args:
        mesh: Source mesh
        element_ids: List of element IDs to include

    Returns:
        New MeshData with subset of elements

    Example:
        >>> # Copy only first 10 elements
        >>> subset = copy_mesh_subset(mesh, list(range(1, 11)))
    """
    new_mesh = MeshData(element_type=mesh.element_type)

    # Collect all nodes used by specified elements
    used_nodes = set()
    for elem_id in element_ids:
        if elem_id in mesh.elements:
            elem = mesh.elements[elem_id]
            used_nodes.update(elem.nodes)

    # Copy used nodes
    for node_id in used_nodes:
        if node_id in mesh.nodes:
            node = mesh.nodes[node_id]
            new_mesh.add_node(
                node.x, node.y, node.z,
                node_id=node_id,
                metadata=copy.deepcopy(node.metadata)
            )

    # Copy specified elements
    for elem_id in element_ids:
        if elem_id in mesh.elements:
            elem = mesh.elements[elem_id]
            new_mesh.add_element(
                elem.nodes.copy(),
                element_id=elem_id,
                element_type=elem.type,
                part_id=elem.part_id,
                metadata=copy.deepcopy(elem.metadata)
            )

    # Copy metadata
    new_mesh.metadata = copy.deepcopy(mesh.metadata)

    return new_mesh


def copy_mesh_part(mesh: MeshData, part_id: int) -> MeshData:
    """
    Create a copy of mesh containing only elements from specified part

    Args:
        mesh: Source mesh
        part_id: Part ID to extract

    Returns:
        New MeshData with only elements from specified part

    Example:
        >>> part1_mesh = copy_mesh_part(mesh, part_id=1)
    """
    # Find all elements with the specified part_id
    element_ids = [
        elem_id for elem_id, elem in mesh.elements.items()
        if elem.part_id == part_id
    ]

    return copy_mesh_subset(mesh, element_ids)
