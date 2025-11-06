"""
Mesh Combination Utilities
===========================

Combine multiple meshes into one.

Author: KooMeshGenerator Team
"""

from koomesh.meshing.mesh_data import MeshData, ElementType


def combine_meshes(meshes: list, offset_nodes: bool = True) -> MeshData:
    """
    Combine multiple meshes into single mesh

    Args:
        meshes: List of MeshData objects to combine
        offset_nodes: Offset node IDs to avoid conflicts

    Returns:
        Combined mesh

    Example:
        >>> mesh1 = create_mesh1()
        >>> mesh2 = create_mesh2()
        >>> combined = combine_meshes([mesh1, mesh2])
    """
    if not meshes:
        raise ValueError("No meshes to combine")

    # Use first mesh's element type
    combined = MeshData(element_type=meshes[0].element_type)

    node_offset = 0
    elem_offset = 0

    for mesh in meshes:
        # Add nodes with offset
        node_map = {}
        for old_nid, node in mesh.nodes.items():
            new_nid = combined.add_node(node.x, node.y, node.z)
            node_map[old_nid] = new_nid

        # Add elements with remapped node IDs
        for elem in mesh.elements.values():
            new_nodes = [node_map[nid] for nid in elem.nodes]
            combined.add_element(
                new_nodes,
                element_type=elem.type,
                part_id=elem.part_id
            )

    return combined


def append_mesh(base_mesh: MeshData, mesh_to_add: MeshData):
    """
    Append mesh to existing base mesh

    Args:
        base_mesh: Base mesh (modified in place)
        mesh_to_add: Mesh to append

    Example:
        >>> append_mesh(mesh1, mesh2)  # mesh2 added to mesh1
    """
    # Add nodes
    node_map = {}
    for old_nid, node in mesh_to_add.nodes.items():
        new_nid = base_mesh.add_node(node.x, node.y, node.z)
        node_map[old_nid] = new_nid

    # Add elements
    for elem in mesh_to_add.elements.values():
        new_nodes = [node_map[nid] for nid in elem.nodes]
        base_mesh.add_element(
            new_nodes,
            element_type=elem.type,
            part_id=elem.part_id
        )
