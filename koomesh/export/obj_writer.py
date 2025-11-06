"""
OBJ (Wavefront) Format Writer
==============================

Exports surface meshes to OBJ format, a universal 3D model format.

OBJ is widely supported by 3D modeling software, game engines, and viewers.

Author: KooMeshGenerator Team
"""

from pathlib import Path
from typing import List, Optional
import numpy as np

from koomesh.meshing.mesh_data import MeshData, ElementType


class OBJWriter:
    """
    Writer for Wavefront OBJ format

    Example:
        >>> writer = OBJWriter()
        >>> writer.write_mesh(mesh, "model.obj")
    """

    def __init__(self):
        """Initialize OBJ writer"""
        pass

    def write_mesh(self, mesh: MeshData, filename: str, object_name: str = "mesh"):
        """
        Write mesh to OBJ file

        Args:
            mesh: Mesh data to export
            filename: Output OBJ file path
            object_name: Name for the object in OBJ file

        Example:
            >>> writer.write_mesh(mesh, "model.obj", "MyModel")
        """
        filepath = Path(filename)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Extract surface faces
        faces = self._extract_surface_faces(mesh)

        self._write_obj(filepath, mesh, faces, object_name)

    def _extract_surface_faces(self, mesh: MeshData) -> List[List[int]]:
        """Extract surface faces from mesh (as triangles and quads)"""
        faces = []

        for elem in mesh.elements.values():
            if elem.type == ElementType.TRI3:
                faces.append(elem.nodes)

            elif elem.type == ElementType.QUAD4:
                faces.append(elem.nodes)

            elif elem.type == ElementType.TET4:
                # Four triangular faces
                faces.append([elem.nodes[0], elem.nodes[2], elem.nodes[1]])
                faces.append([elem.nodes[0], elem.nodes[1], elem.nodes[3]])
                faces.append([elem.nodes[0], elem.nodes[3], elem.nodes[2]])
                faces.append([elem.nodes[1], elem.nodes[2], elem.nodes[3]])

            elif elem.type in [ElementType.HEX8, ElementType.HEX20, ElementType.HEX27]:
                # Six quad faces
                nodes = elem.nodes
                faces.append([nodes[0], nodes[1], nodes[2], nodes[3]])  # bottom
                faces.append([nodes[4], nodes[5], nodes[6], nodes[7]])  # top
                faces.append([nodes[0], nodes[1], nodes[5], nodes[4]])  # front
                faces.append([nodes[2], nodes[3], nodes[7], nodes[6]])  # back
                faces.append([nodes[0], nodes[4], nodes[7], nodes[3]])  # left
                faces.append([nodes[1], nodes[2], nodes[6], nodes[5]])  # right

            elif elem.type == ElementType.PRISM6:
                # Two triangular faces + three quad faces
                nodes = elem.nodes
                faces.append([nodes[0], nodes[2], nodes[1]])  # bottom triangle
                faces.append([nodes[3], nodes[4], nodes[5]])  # top triangle
                faces.append([nodes[0], nodes[1], nodes[4], nodes[3]])  # quad
                faces.append([nodes[1], nodes[2], nodes[5], nodes[4]])  # quad
                faces.append([nodes[2], nodes[0], nodes[3], nodes[5]])  # quad

            elif elem.type == ElementType.PYRAMID5:
                # One quad base + four triangular faces
                nodes = elem.nodes
                faces.append([nodes[0], nodes[1], nodes[2], nodes[3]])  # base
                faces.append([nodes[0], nodes[4], nodes[1]])
                faces.append([nodes[1], nodes[4], nodes[2]])
                faces.append([nodes[2], nodes[4], nodes[3]])
                faces.append([nodes[3], nodes[4], nodes[0]])

        return faces

    def _compute_normals(self, mesh: MeshData, faces: List[List[int]]) -> List[np.ndarray]:
        """Compute face normals"""
        normals = []

        for face in faces:
            if len(face) < 3:
                normals.append(np.array([0.0, 0.0, 1.0]))
                continue

            # Get first three vertices
            v0 = mesh.nodes[face[0]]
            v1 = mesh.nodes[face[1]]
            v2 = mesh.nodes[face[2]]

            p0 = np.array([v0.x, v0.y, v0.z])
            p1 = np.array([v1.x, v1.y, v1.z])
            p2 = np.array([v2.x, v2.y, v2.z])

            # Compute normal using cross product
            edge1 = p1 - p0
            edge2 = p2 - p0
            normal = np.cross(edge1, edge2)

            # Normalize
            norm_length = np.linalg.norm(normal)
            if norm_length > 1e-10:
                normal = normal / norm_length
            else:
                normal = np.array([0.0, 0.0, 1.0])

            normals.append(normal)

        return normals

    def _write_obj(self, filepath: Path, mesh: MeshData, faces: List[List[int]], object_name: str):
        """Write OBJ format"""
        # Create node ID to index mapping (OBJ uses 1-based indexing)
        node_map = {nid: idx + 1 for idx, nid in enumerate(sorted(mesh.nodes.keys()))}

        # Compute normals
        normals = self._compute_normals(mesh, faces)

        with open(filepath, 'w') as f:
            # Header
            f.write(f"# OBJ file generated by KooMeshGenerator\n")
            f.write(f"# Vertices: {len(mesh.nodes)}\n")
            f.write(f"# Faces: {len(faces)}\n")
            f.write(f"\n")

            # Object name
            f.write(f"o {object_name}\n")
            f.write(f"\n")

            # Vertices
            for nid in sorted(mesh.nodes.keys()):
                node = mesh.nodes[nid]
                f.write(f"v {node.x:.6f} {node.y:.6f} {node.z:.6f}\n")

            f.write(f"\n")

            # Normals
            for normal in normals:
                f.write(f"vn {normal[0]:.6f} {normal[1]:.6f} {normal[2]:.6f}\n")

            f.write(f"\n")

            # Faces (with normals)
            for face_idx, face in enumerate(faces):
                indices = [node_map[nid] for nid in face]
                normal_idx = face_idx + 1

                # OBJ face format: f v1//vn1 v2//vn2 v3//vn3 ...
                face_str = "f "
                for idx in indices:
                    face_str += f"{idx}//{normal_idx} "
                f.write(face_str.strip() + "\n")


def export_to_obj(mesh: MeshData, filename: str, object_name: str = "mesh") -> bool:
    """
    Convenience function to export mesh to OBJ format

    Args:
        mesh: Mesh data to export
        filename: Output OBJ file path
        object_name: Name for the object

    Returns:
        True if successful

    Example:
        >>> export_to_obj(mesh, "model.obj", "MyModel")
    """
    try:
        writer = OBJWriter()
        writer.write_mesh(mesh, filename, object_name)
        return True
    except Exception as e:
        print(f"OBJ export failed: {e}")
        return False
