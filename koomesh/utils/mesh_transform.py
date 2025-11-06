"""
Mesh Transformation Utilities
==============================

Transform mesh geometry (translate, scale, rotate).

Author: KooMeshGenerator Team
"""

import numpy as np
from koomesh.meshing.mesh_data import MeshData


def translate_mesh(mesh: MeshData, dx: float = 0, dy: float = 0, dz: float = 0):
    """
    Translate mesh by offset

    Args:
        mesh: Mesh to translate (modified in place)
        dx, dy, dz: Translation offsets

    Example:
        >>> translate_mesh(mesh, dx=10.0, dy=5.0)
    """
    for node in mesh.nodes.values():
        node.x += dx
        node.y += dy
        node.z += dz


def scale_mesh(mesh: MeshData, sx: float = 1, sy: float = 1, sz: float = 1,
               center: tuple = None):
    """
    Scale mesh

    Args:
        mesh: Mesh to scale (modified in place)
        sx, sy, sz: Scale factors
        center: Center point for scaling (default: origin)

    Example:
        >>> scale_mesh(mesh, sx=2.0, sy=2.0, sz=2.0)  # Double size
    """
    if center is None:
        center = (0, 0, 0)

    cx, cy, cz = center

    for node in mesh.nodes.values():
        node.x = cx + (node.x - cx) * sx
        node.y = cy + (node.y - cy) * sy
        node.z = cz + (node.z - cz) * sz


def center_mesh(mesh: MeshData):
    """
    Center mesh at origin

    Args:
        mesh: Mesh to center (modified in place)

    Example:
        >>> center_mesh(mesh)
    """
    if not mesh.nodes:
        return

    xs = [n.x for n in mesh.nodes.values()]
    ys = [n.y for n in mesh.nodes.values()]
    zs = [n.z for n in mesh.nodes.values()]

    cx = (min(xs) + max(xs)) / 2
    cy = (min(ys) + max(ys)) / 2
    cz = (min(zs) + max(zs)) / 2

    translate_mesh(mesh, -cx, -cy, -cz)


def rotate_mesh_z(mesh: MeshData, angle_degrees: float, center: tuple = None):
    """
    Rotate mesh around Z axis

    Args:
        mesh: Mesh to rotate (modified in place)
        angle_degrees: Rotation angle in degrees
        center: Center point for rotation (default: origin)

    Example:
        >>> rotate_mesh_z(mesh, 90)  # Rotate 90 degrees
    """
    if center is None:
        center = (0, 0, 0)

    cx, cy, cz = center
    angle_rad = np.radians(angle_degrees)
    cos_a = np.cos(angle_rad)
    sin_a = np.sin(angle_rad)

    for node in mesh.nodes.values():
        # Translate to origin
        x = node.x - cx
        y = node.y - cy

        # Rotate
        node.x = cx + x * cos_a - y * sin_a
        node.y = cy + x * sin_a + y * cos_a
        # Z unchanged


def mirror_mesh(mesh: MeshData, axis: str = 'x'):
    """
    Mirror mesh across axis plane

    Args:
        mesh: Mesh to mirror (modified in place)
        axis: Axis to mirror across ('x', 'y', or 'z')

    Example:
        >>> mirror_mesh(mesh, 'x')  # Mirror across YZ plane
    """
    for node in mesh.nodes.values():
        if axis.lower() == 'x':
            node.x = -node.x
        elif axis.lower() == 'y':
            node.y = -node.y
        elif axis.lower() == 'z':
            node.z = -node.z
