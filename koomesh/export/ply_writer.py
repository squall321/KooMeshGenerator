"""
PLY (Polygon File Format) Writer
=================================

Exports surface meshes to PLY format for 3D scanning and point cloud applications.

PLY is a simple format that stores 3D point clouds and polygon meshes.
Supports both ASCII and binary formats.

Author: KooMeshGenerator Team
"""

import struct
from pathlib import Path
from typing import List, Tuple, Optional
import numpy as np

from koomesh.meshing.mesh_data import MeshData, ElementType


class PLYWriter:
    """
    Writer for PLY (Polygon File Format)

    Supports ASCII format for compatibility.

    Example:
        >>> writer = PLYWriter()
        >>> writer.write_mesh(mesh, "output.ply")
    """

    def __init__(self):
        """Initialize PLY writer"""
        pass

    def write_mesh(self, mesh: MeshData, filename: str, ascii_format: bool = True):
        """
        Write mesh to PLY file

        Args:
            mesh: Mesh data to export
            filename: Output PLY file path
            ascii_format: Use ASCII format (True) or binary (False)

        Example:
            >>> writer.write_mesh(mesh, "model.ply")
        """
        filepath = Path(filename)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Extract surface triangles
        triangles = self._extract_surface_triangles(mesh)

        if ascii_format:
            self._write_ascii(filepath, mesh, triangles)
        else:
            self._write_binary(filepath, mesh, triangles)

    def _extract_surface_triangles(self, mesh: MeshData) -> List[List[int]]:
        """Extract triangulated surface from mesh"""
        triangles = []

        for elem in mesh.elements.values():
            if elem.type == ElementType.TRI3:
                triangles.append(elem.nodes)

            elif elem.type == ElementType.QUAD4:
                # Split quad into two triangles
                triangles.append([elem.nodes[0], elem.nodes[1], elem.nodes[2]])
                triangles.append([elem.nodes[0], elem.nodes[2], elem.nodes[3]])

            elif elem.type == ElementType.TET4:
                # Four triangular faces
                triangles.append([elem.nodes[0], elem.nodes[2], elem.nodes[1]])
                triangles.append([elem.nodes[0], elem.nodes[1], elem.nodes[3]])
                triangles.append([elem.nodes[0], elem.nodes[3], elem.nodes[2]])
                triangles.append([elem.nodes[1], elem.nodes[2], elem.nodes[3]])

            elif elem.type in [ElementType.HEX8, ElementType.HEX20, ElementType.HEX27]:
                # Six quad faces -> 12 triangles
                nodes = elem.nodes
                faces = [
                    [nodes[0], nodes[3], nodes[2], nodes[1]],  # bottom
                    [nodes[4], nodes[5], nodes[6], nodes[7]],  # top
                    [nodes[0], nodes[1], nodes[5], nodes[4]],  # front
                    [nodes[2], nodes[3], nodes[7], nodes[6]],  # back
                    [nodes[0], nodes[4], nodes[7], nodes[3]],  # left
                    [nodes[1], nodes[2], nodes[6], nodes[5]],  # right
                ]

                for face in faces:
                    triangles.append([face[0], face[1], face[2]])
                    triangles.append([face[0], face[2], face[3]])

            elif elem.type == ElementType.PRISM6:
                # Two triangular faces + three quad faces
                nodes = elem.nodes
                # Bottom triangle
                triangles.append([nodes[0], nodes[2], nodes[1]])
                # Top triangle
                triangles.append([nodes[3], nodes[4], nodes[5]])
                # Three quad faces
                quads = [
                    [nodes[0], nodes[1], nodes[4], nodes[3]],
                    [nodes[1], nodes[2], nodes[5], nodes[4]],
                    [nodes[2], nodes[0], nodes[3], nodes[5]],
                ]
                for quad in quads:
                    triangles.append([quad[0], quad[1], quad[2]])
                    triangles.append([quad[0], quad[2], quad[3]])

        return triangles

    def _write_ascii(self, filepath: Path, mesh: MeshData, triangles: List[List[int]]):
        """Write ASCII PLY format"""
        # Create node ID to index mapping
        node_map = {nid: idx for idx, nid in enumerate(sorted(mesh.nodes.keys()))}

        with open(filepath, 'w') as f:
            # Header
            f.write("ply\n")
            f.write("format ascii 1.0\n")
            f.write(f"element vertex {len(mesh.nodes)}\n")
            f.write("property float x\n")
            f.write("property float y\n")
            f.write("property float z\n")
            f.write(f"element face {len(triangles)}\n")
            f.write("property list uchar int vertex_indices\n")
            f.write("end_header\n")

            # Vertices
            for nid in sorted(mesh.nodes.keys()):
                node = mesh.nodes[nid]
                f.write(f"{node.x} {node.y} {node.z}\n")

            # Faces
            for tri in triangles:
                indices = [node_map[nid] for nid in tri]
                f.write(f"3 {indices[0]} {indices[1]} {indices[2]}\n")

    def _write_binary(self, filepath: Path, mesh: MeshData, triangles: List[List[int]]):
        """Write binary PLY format (little endian)"""
        # Create node ID to index mapping
        node_map = {nid: idx for idx, nid in enumerate(sorted(mesh.nodes.keys()))}

        with open(filepath, 'wb') as f:
            # ASCII header
            header = []
            header.append("ply\n")
            header.append("format binary_little_endian 1.0\n")
            header.append(f"element vertex {len(mesh.nodes)}\n")
            header.append("property float x\n")
            header.append("property float y\n")
            header.append("property float z\n")
            header.append(f"element face {len(triangles)}\n")
            header.append("property list uchar int vertex_indices\n")
            header.append("end_header\n")

            f.write(''.join(header).encode('ascii'))

            # Binary vertex data
            for nid in sorted(mesh.nodes.keys()):
                node = mesh.nodes[nid]
                f.write(struct.pack('<fff', node.x, node.y, node.z))

            # Binary face data
            for tri in triangles:
                indices = [node_map[nid] for nid in tri]
                f.write(struct.pack('<B', 3))  # vertex count
                f.write(struct.pack('<iii', indices[0], indices[1], indices[2]))


def export_to_ply(mesh: MeshData, filename: str, ascii_format: bool = True) -> bool:
    """
    Convenience function to export mesh to PLY format

    Args:
        mesh: Mesh data to export
        filename: Output PLY file path
        ascii_format: Use ASCII format (True) or binary (False)

    Returns:
        True if successful

    Example:
        >>> export_to_ply(mesh, "model.ply")
    """
    try:
        writer = PLYWriter()
        writer.write_mesh(mesh, filename, ascii_format)
        return True
    except Exception as e:
        print(f"PLY export failed: {e}")
        return False
