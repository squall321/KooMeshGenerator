"""
Mesh Information Utility
=========================

Quick mesh info display utility.

Author: KooMeshGenerator Team
"""

from koomesh.meshing.mesh_data import MeshData


def print_mesh_info(mesh: MeshData, name: str = "Mesh"):
    """
    Print quick mesh information

    Args:
        mesh: Mesh data
        name: Name to display

    Example:
        >>> print_mesh_info(mesh, "My Model")
    """
    print(f"\n{name} Information:")
    print(f"  Nodes:    {len(mesh.nodes):,}")
    print(f"  Elements: {len(mesh.elements):,}")
    print(f"  Type:     {mesh.element_type}")

    if mesh.nodes:
        # Quick bounding box
        xs = [n.x for n in mesh.nodes.values()]
        ys = [n.y for n in mesh.nodes.values()]
        zs = [n.z for n in mesh.nodes.values()]
        print(f"  Bounds:   X[{min(xs):.2f}, {max(xs):.2f}] "
              f"Y[{min(ys):.2f}, {max(ys):.2f}] "
              f"Z[{min(zs):.2f}, {max(zs):.2f}]")


def get_mesh_summary(mesh: MeshData) -> str:
    """
    Get one-line mesh summary

    Returns:
        Summary string

    Example:
        >>> summary = get_mesh_summary(mesh)
        >>> print(summary)
    """
    return f"{len(mesh.nodes)} nodes, {len(mesh.elements)} {mesh.element_type} elements"
