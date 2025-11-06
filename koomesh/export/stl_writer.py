"""
STL (STereoLithography) Format Writer
======================================

Writes mesh data to STL format for 3D printing and CAD applications.

STL format stores triangulated surface geometry:
- ASCII format: Human-readable text
- Binary format: Compact binary (not implemented yet)

Author: KooMeshGenerator Team
License: MIT
"""

import logging
import numpy as np
from pathlib import Path
from typing import Optional

from koomesh.meshing.mesh_data import MeshData, ElementType


class STLError(Exception):
    """Exception raised for STL export errors"""
    pass


class STLWriter:
    """
    Writer for STL (STereoLithography) format

    STL is a simple format used for 3D printing and rapid prototyping.
    It represents surfaces as collections of triangles with normal vectors.

    Example:
        >>> from koomesh.export.stl_writer import STLWriter
        >>> writer = STLWriter("model.stl")
        >>> writer.write_surface_mesh(mesh)
    """

    def __init__(self, filepath: str):
        """
        Initialize STL writer

        Args:
            filepath: Path to output STL file
        """
        self.filepath = Path(filepath)
        self.logger = logging.getLogger(__name__)

    def write_surface_mesh(self, mesh: MeshData, solid_name: str = "mesh"):
        """
        Write surface mesh to STL format

        Args:
            mesh: Mesh data to export
            solid_name: Name of the solid in STL file

        Note:
            STL only supports triangular faces. Quad faces are automatically
            split into two triangles.
        """
        if not mesh.elements:
            raise STLError("Cannot export empty mesh")

        triangles = self._extract_surface_triangles(mesh)

        if not triangles:
            raise STLError("No surface triangles found")

        self._write_ascii_stl(triangles, solid_name)
        self.logger.info(f"Wrote {len(triangles)} triangles to {self.filepath}")

    def _extract_surface_triangles(self, mesh: MeshData):
        """
        Extract surface triangles from mesh

        Returns:
            List of (normal, v1, v2, v3) tuples
        """
        triangles = []

        # Face definitions for each element type
        # Returns triangular faces or quads (which we split)
        element_faces = {
            ElementType.HEX8: [
                [0, 3, 2, 1],  # Bottom (quad -> 2 triangles)
                [4, 5, 6, 7],  # Top
                [0, 1, 5, 4],  # Faces
                [2, 3, 7, 6],
                [0, 4, 7, 3],
                [1, 2, 6, 5],
            ],
            ElementType.TET4: [
                [0, 2, 1],  # Triangular faces
                [0, 1, 3],
                [1, 2, 3],
                [2, 0, 3],
            ],
            ElementType.PRISM6: [
                [0, 2, 1],  # Bottom triangle
                [3, 4, 5],  # Top triangle
                [0, 1, 4, 3],  # Quads
                [1, 2, 5, 4],
                [2, 0, 3, 5],
            ],
            ElementType.PYRAMID5: [
                [0, 3, 2, 1],  # Base quad
                [0, 1, 4],  # Triangular faces
                [1, 2, 4],
                [2, 3, 4],
                [3, 0, 4],
            ],
        }

        for element in mesh.elements.values():
            elem_type = element.type

            if elem_type not in element_faces:
                self.logger.warning(f"Unsupported element type for STL: {elem_type}")
                continue

            # Get node coordinates
            nodes = [mesh.nodes[nid] for nid in element.nodes]

            # Process each face
            for face_def in element_faces[elem_type]:
                face_nodes = [nodes[i] for i in face_def]

                if len(face_def) == 3:
                    # Triangle: add directly
                    tri = self._make_triangle(face_nodes[0], face_nodes[1], face_nodes[2])
                    triangles.append(tri)
                elif len(face_def) == 4:
                    # Quad: split into two triangles
                    tri1 = self._make_triangle(face_nodes[0], face_nodes[1], face_nodes[2])
                    tri2 = self._make_triangle(face_nodes[0], face_nodes[2], face_nodes[3])
                    triangles.append(tri1)
                    triangles.append(tri2)

        return triangles

    def _make_triangle(self, n1, n2, n3):
        """
        Create triangle with normal vector

        Args:
            n1, n2, n3: Node objects

        Returns:
            Tuple of (normal, v1, v2, v3)
        """
        # Get vertex coordinates
        v1 = np.array([n1.x, n1.y, n1.z])
        v2 = np.array([n2.x, n2.y, n2.z])
        v3 = np.array([n3.x, n3.y, n3.z])

        # Compute normal using cross product
        edge1 = v2 - v1
        edge2 = v3 - v1
        normal = np.cross(edge1, edge2)

        # Normalize
        norm_length = np.linalg.norm(normal)
        if norm_length > 1e-10:
            normal = normal / norm_length
        else:
            normal = np.array([0.0, 0.0, 1.0])  # Default normal

        return (normal, v1, v2, v3)

    def _write_ascii_stl(self, triangles, solid_name):
        """Write triangles to ASCII STL file"""
        with open(self.filepath, 'w') as f:
            f.write(f"solid {solid_name}\n")

            for normal, v1, v2, v3 in triangles:
                f.write(f"  facet normal {normal[0]:.6e} {normal[1]:.6e} {normal[2]:.6e}\n")
                f.write("    outer loop\n")
                f.write(f"      vertex {v1[0]:.6e} {v1[1]:.6e} {v1[2]:.6e}\n")
                f.write(f"      vertex {v2[0]:.6e} {v2[1]:.6e} {v2[2]:.6e}\n")
                f.write(f"      vertex {v3[0]:.6e} {v3[1]:.6e} {v3[2]:.6e}\n")
                f.write("    endloop\n")
                f.write("  endfacet\n")

            f.write(f"endsolid {solid_name}\n")


def export_to_stl(mesh: MeshData, filepath: str, solid_name: str = "mesh") -> bool:
    """
    Convenience function to export mesh to STL format

    Args:
        mesh: Mesh data to export
        filepath: Path to output STL file
        solid_name: Name of the solid

    Returns:
        True if export successful, False otherwise

    Example:
        >>> success = export_to_stl(mesh, "model.stl")
    """
    try:
        writer = STLWriter(filepath)
        writer.write_surface_mesh(mesh, solid_name=solid_name)
        return True
    except Exception as e:
        logging.error(f"STL export failed: {e}")
        return False
