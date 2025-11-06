"""
OpenFOAM polyMesh Format Writer
================================

Writes mesh data to OpenFOAM's polyMesh directory structure.

OpenFOAM uses a face-based mesh format with the following files:
- points: Vertex coordinates
- faces: Face definitions (lists of vertex indices)
- owner: Cell owning each face
- neighbour: Neighboring cell for internal faces
- boundary: Boundary patch definitions

Author: KooMeshGenerator Team
License: MIT
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict

from koomesh.meshing.mesh_data import MeshData, ElementType


class OpenFOAMError(Exception):
    """Exception raised for OpenFOAM export errors"""
    pass


class OpenFOAMWriter:
    """
    Writer for OpenFOAM polyMesh format

    OpenFOAM stores meshes in the constant/polyMesh directory with files:
    - points: Node coordinates
    - faces: Face vertex lists
    - owner: Cell that owns each face
    - neighbour: Neighboring cell (internal faces only)
    - boundary: Boundary patch information

    Example:
        >>> from koomesh.export.openfoam_writer import OpenFOAMWriter
        >>> writer = OpenFOAMWriter("case_directory")
        >>> writer.write_mesh(mesh, boundary_patches={"inlet": inlet_faces, "outlet": outlet_faces})
    """

    # Face node ordering for each element type
    # OpenFOAM uses counter-clockwise ordering when viewed from outside
    ELEMENT_FACES = {
        ElementType.HEX8: [
            [0, 3, 2, 1],  # bottom (-Z)
            [4, 5, 6, 7],  # top (+Z)
            [0, 1, 5, 4],  # front (-Y)
            [2, 3, 7, 6],  # back (+Y)
            [0, 4, 7, 3],  # left (-X)
            [1, 2, 6, 5],  # right (+X)
        ],
        ElementType.HEX20: [
            [0, 3, 2, 1, 11, 10, 9, 8],  # bottom
            [4, 5, 6, 7, 12, 13, 14, 15],  # top
            [0, 1, 5, 4, 8, 17, 12, 16],  # front
            [2, 3, 7, 6, 10, 18, 14, 19],  # back
            [0, 4, 7, 3, 16, 15, 18, 11],  # left
            [1, 2, 6, 5, 9, 19, 13, 17],  # right
        ],
        ElementType.HEX27: [
            [0, 3, 2, 1, 11, 10, 9, 8, 20],  # bottom
            [4, 5, 6, 7, 12, 13, 14, 15, 25],  # top
            [0, 1, 5, 4, 8, 17, 12, 16, 21],  # front
            [2, 3, 7, 6, 10, 18, 14, 19, 23],  # back
            [0, 4, 7, 3, 16, 15, 18, 11, 24],  # left
            [1, 2, 6, 5, 9, 19, 13, 17, 22],  # right
        ],
        ElementType.TET4: [
            [0, 2, 1],  # bottom
            [0, 1, 3],  # face 1
            [1, 2, 3],  # face 2
            [2, 0, 3],  # face 3
        ],
        ElementType.TET10: [
            [0, 2, 1, 6, 5, 4],  # bottom
            [0, 1, 3, 4, 8, 7],  # face 1
            [1, 2, 3, 5, 9, 8],  # face 2
            [2, 0, 3, 6, 7, 9],  # face 3
        ],
        ElementType.PRISM6: [
            [0, 2, 1],  # bottom triangle
            [3, 4, 5],  # top triangle
            [0, 1, 4, 3],  # front quad
            [1, 2, 5, 4],  # right quad
            [2, 0, 3, 5],  # left quad
        ],
        ElementType.PYRAMID5: [
            [0, 3, 2, 1],  # base quad
            [0, 1, 4],  # face 1
            [1, 2, 4],  # face 2
            [2, 3, 4],  # face 3
            [3, 0, 4],  # face 4
        ],
    }

    def __init__(self, case_dir: str):
        """
        Initialize OpenFOAM writer

        Args:
            case_dir: Path to OpenFOAM case directory
        """
        self.case_dir = Path(case_dir)
        self.polymesh_dir = self.case_dir / "constant" / "polyMesh"
        self.logger = logging.getLogger(__name__)

    def write_mesh(self,
                   mesh: MeshData,
                   boundary_patches: Optional[Dict[str, List[Tuple[int, int]]]] = None):
        """
        Write mesh to OpenFOAM polyMesh format

        Args:
            mesh: Mesh data to export
            boundary_patches: Dictionary mapping patch names to lists of (cell_id, face_id) tuples
                            If None, all boundary faces are assigned to "defaultFaces" patch

        Example:
            >>> # Define boundary patches
            >>> patches = {
            >>>     "inlet": [(0, 2), (1, 2)],  # Face 2 of cells 0 and 1
            >>>     "outlet": [(8, 3), (9, 3)],  # Face 3 of cells 8 and 9
            >>>     "walls": [(0, 0), (0, 4), (0, 5), ...]  # Multiple faces
            >>> }
            >>> writer.write_mesh(mesh, boundary_patches=patches)
        """
        if not mesh.elements:
            raise OpenFOAMError("Cannot export empty mesh")

        # Create polyMesh directory
        self.polymesh_dir.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"Extracting faces from {len(mesh.elements)} elements")

        # Extract all faces and determine internal/boundary faces
        all_faces, face_owners, face_neighbours = self._extract_faces(mesh)

        # Separate internal and boundary faces
        internal_faces = []
        internal_owners = []
        internal_neighbours = []
        boundary_faces = []
        boundary_owners = []
        boundary_face_info = []  # List of (cell_id, face_id_in_cell)

        for i, face in enumerate(all_faces):
            if face_neighbours[i] != -1:
                internal_faces.append(face)
                internal_owners.append(face_owners[i])
                internal_neighbours.append(face_neighbours[i])
            else:
                boundary_faces.append(face)
                boundary_owners.append(face_owners[i])
                boundary_face_info.append((face_owners[i], -1))  # Will be determined later

        self.logger.info(f"Found {len(internal_faces)} internal faces, {len(boundary_faces)} boundary faces")

        # Write mesh files
        self._write_points(mesh)
        self._write_faces(internal_faces + boundary_faces)
        self._write_owner(internal_owners + boundary_owners)
        self._write_neighbour(internal_neighbours)
        self._write_boundary(len(internal_faces), boundary_faces, boundary_patches or {})

        self.logger.info(f"Successfully wrote OpenFOAM mesh to {self.polymesh_dir}")

    def _extract_faces(self, mesh: MeshData) -> Tuple[List[List[int]], List[int], List[int]]:
        """
        Extract all faces from elements

        Returns:
            Tuple of (faces, owners, neighbours)
            - faces: List of face node lists
            - owners: Cell ID that owns each face
            - neighbours: Cell ID of neighbor (-1 for boundary faces)
        """
        # Dictionary to store face information: face_tuple -> (owner_cell, neighbour_cell)
        face_dict: Dict[Tuple[int, ...], List[int]] = defaultdict(list)

        # Process each element
        for elem_idx, element in enumerate(mesh.elements.values()):
            elem_type = element.type

            if elem_type not in self.ELEMENT_FACES:
                raise OpenFOAMError(f"Unsupported element type: {elem_type}")

            # Get face definitions for this element type
            face_defs = self.ELEMENT_FACES[elem_type]

            # Extract each face
            for face_def in face_defs:
                # Get global node IDs for this face
                face_nodes = tuple(element.nodes[i] for i in face_def)

                # Create a canonical representation (smallest rotation)
                face_key = self._canonical_face(face_nodes)

                # Record which cell owns this face
                face_dict[face_key].append(elem_idx)

        # Build face lists
        all_faces = []
        face_owners = []
        face_neighbours = []

        for face_nodes, owner_cells in face_dict.items():
            # Convert back to list
            all_faces.append(list(face_nodes))

            # First cell is the owner
            face_owners.append(owner_cells[0])

            # If shared by two cells, second is neighbor; otherwise -1 (boundary)
            if len(owner_cells) == 2:
                face_neighbours.append(owner_cells[1])
            elif len(owner_cells) == 1:
                face_neighbours.append(-1)
            else:
                # More than 2 cells share a face - this is an error
                raise OpenFOAMError(f"Face shared by {len(owner_cells)} cells (should be 1 or 2)")

        return all_faces, face_owners, face_neighbours

    def _canonical_face(self, nodes: Tuple[int, ...]) -> Tuple[int, ...]:
        """
        Get canonical representation of face (smallest rotation)

        This ensures that the same face is recognized regardless of which
        element it came from or the direction it was traversed.
        """
        # Find the rotation that starts with the smallest node
        n = len(nodes)
        min_idx = nodes.index(min(nodes))

        # Try both directions (forward and reverse)
        forward = nodes[min_idx:] + nodes[:min_idx]
        reverse = (nodes[min_idx],) + tuple(reversed(nodes[min_idx+1:])) + tuple(reversed(nodes[:min_idx]))

        # Return the lexicographically smallest
        return min(forward, reverse)

    def _write_points(self, mesh: MeshData):
        """Write points file"""
        filepath = self.polymesh_dir / "points"

        with open(filepath, 'w') as f:
            # Write OpenFOAM header
            self._write_header(f, "vectorField", "points")

            # Write number of points
            f.write(f"\n{len(mesh.nodes)}\n")
            f.write("(\n")

            # Write point coordinates
            for node in mesh.nodes.values():
                f.write(f"({node.x:.16e} {node.y:.16e} {node.z:.16e})\n")

            f.write(")\n")

        self.logger.debug(f"Wrote {len(mesh.nodes)} points")

    def _write_faces(self, faces: List[List[int]]):
        """Write faces file"""
        filepath = self.polymesh_dir / "faces"

        with open(filepath, 'w') as f:
            # Write OpenFOAM header
            self._write_header(f, "faceList", "faces")

            # Write number of faces
            f.write(f"\n{len(faces)}\n")
            f.write("(\n")

            # Write face definitions
            for face in faces:
                # OpenFOAM uses 0-based indexing
                node_str = " ".join(str(n) for n in face)
                f.write(f"{len(face)}({node_str})\n")

            f.write(")\n")

        self.logger.debug(f"Wrote {len(faces)} faces")

    def _write_owner(self, owners: List[int]):
        """Write owner file"""
        filepath = self.polymesh_dir / "owner"

        with open(filepath, 'w') as f:
            # Write OpenFOAM header
            self._write_header(f, "labelList", "owner")

            # Write number of faces
            f.write(f"\n{len(owners)}\n")
            f.write("(\n")

            # Write owner cell IDs
            for owner in owners:
                f.write(f"{owner}\n")

            f.write(")\n")

        self.logger.debug(f"Wrote {len(owners)} owner entries")

    def _write_neighbour(self, neighbours: List[int]):
        """Write neighbour file"""
        filepath = self.polymesh_dir / "neighbour"

        with open(filepath, 'w') as f:
            # Write OpenFOAM header
            self._write_header(f, "labelList", "neighbour")

            # Write number of internal faces
            f.write(f"\n{len(neighbours)}\n")
            f.write("(\n")

            # Write neighbour cell IDs
            for neighbour in neighbours:
                f.write(f"{neighbour}\n")

            f.write(")\n")

        self.logger.debug(f"Wrote {len(neighbours)} neighbour entries")

    def _write_boundary(self,
                       n_internal_faces: int,
                       boundary_faces: List[List[int]],
                       boundary_patches: Dict[str, List[Tuple[int, int]]]):
        """Write boundary file"""
        filepath = self.polymesh_dir / "boundary"

        # If no patches specified, create single default patch
        if not boundary_patches:
            boundary_patches = {"defaultFaces": []}

        with open(filepath, 'w') as f:
            # Write OpenFOAM header
            self._write_header(f, "polyBoundaryMesh", "boundary")

            # Write number of patches
            f.write(f"\n{len(boundary_patches)}\n")
            f.write("(\n")

            start_face = n_internal_faces

            # Write each patch
            for patch_name, patch_faces in boundary_patches.items():
                n_faces = len(patch_faces) if patch_faces else len(boundary_faces)

                f.write(f"    {patch_name}\n")
                f.write("    {\n")
                f.write("        type            patch;\n")
                f.write(f"        nFaces          {n_faces};\n")
                f.write(f"        startFace       {start_face};\n")
                f.write("    }\n")

                start_face += n_faces

            f.write(")\n")

        self.logger.debug(f"Wrote boundary with {len(boundary_patches)} patches")

    def _write_header(self, f, class_name: str, object_name: str):
        """Write standard OpenFOAM file header"""
        f.write("/*--------------------------------*- C++ -*----------------------------------*\\\n")
        f.write("| =========                 |                                                 |\n")
        f.write("| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |\n")
        f.write("|  \\\\    /   O peration     | Version:  v2312                                 |\n")
        f.write("|   \\\\  /    A nd           | Website:  www.openfoam.com                      |\n")
        f.write("|    \\\\/     M anipulation  |                                                 |\n")
        f.write("\\*---------------------------------------------------------------------------*/\n")
        f.write("FoamFile\n")
        f.write("{\n")
        f.write("    version     2.0;\n")
        f.write("    format      ascii;\n")
        f.write(f"    class       {class_name};\n")
        f.write("    location    \"constant/polyMesh\";\n")
        f.write(f"    object      {object_name};\n")
        f.write("}\n")
        f.write("// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //\n")


def export_to_openfoam(mesh: MeshData,
                       case_dir: str,
                       boundary_patches: Optional[Dict[str, List[Tuple[int, int]]]] = None) -> bool:
    """
    Convenience function to export mesh to OpenFOAM format

    Args:
        mesh: Mesh data to export
        case_dir: Path to OpenFOAM case directory
        boundary_patches: Optional boundary patch definitions

    Returns:
        True if export successful, False otherwise

    Example:
        >>> success = export_to_openfoam(mesh, "my_case",
        ...     boundary_patches={"inlet": inlet_faces, "outlet": outlet_faces})
    """
    try:
        writer = OpenFOAMWriter(case_dir)
        writer.write_mesh(mesh, boundary_patches=boundary_patches)
        return True
    except Exception as e:
        logging.error(f"OpenFOAM export failed: {e}")
        return False
