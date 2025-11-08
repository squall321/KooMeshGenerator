"""
Contact Surface Detection
=========================

Detect contact surfaces between mesh parts for contact analysis.

This module provides tools to:
- Identify potential contact surfaces between parts
- Find faces in proximity
- Create contact pairs for FEA

Author: KooMeshGenerator Team
"""

import logging
import numpy as np
from typing import List, Tuple, Dict, Set
from dataclasses import dataclass
from koomesh.meshing.mesh_data import MeshData, Element


logger = logging.getLogger(__name__)


@dataclass
class ContactPair:
    """
    Represents a pair of potentially contacting surfaces

    Attributes:
        part1_id: First part ID
        part2_id: Second part ID
        part1_faces: Set of face IDs from part 1
        part2_faces: Set of face IDs from part 2
        avg_distance: Average distance between surfaces
    """
    part1_id: int
    part2_id: int
    part1_faces: Set[int]
    part2_faces: Set[int]
    avg_distance: float


@dataclass
class SelfContactPair:
    """
    Represents self-contact within a single part

    Self-contact occurs when different regions of the same part
    come into close proximity (e.g., during large deformations).

    Attributes:
        part_id: Part ID
        face_pairs: List of (face_idx1, face_idx2) tuples that are in contact
        avg_distance: Average distance between contacting face pairs
        min_distance: Minimum distance found
    """
    part_id: int
    face_pairs: List[Tuple[int, int]]
    avg_distance: float
    min_distance: float


class ContactSurfaceDetector:
    """
    Detect contact surfaces between mesh parts

    This class analyzes a mesh with multiple parts and identifies
    surfaces that are in close proximity, which may require contact
    definitions in FEA simulations.

    Example:
        >>> detector = ContactSurfaceDetector()
        >>> contacts = detector.detect_contacts(mesh, tolerance=0.1)
        >>> for contact in contacts:
        ...     print(f"Contact between parts {contact.part1_id} and {contact.part2_id}")
    """

    def __init__(self):
        """Initialize contact surface detector"""
        self.logger = logging.getLogger(__name__)

    def detect_contacts(self, mesh: MeshData,
                       tolerance: float = 0.1,
                       min_faces: int = 1) -> List[ContactPair]:
        """
        Detect potential contact surfaces between parts

        Args:
            mesh: Mesh with multiple parts
            tolerance: Maximum distance to consider as potential contact
            min_faces: Minimum number of faces required for a contact pair

        Returns:
            List of ContactPair objects

        Example:
            >>> contacts = detector.detect_contacts(mesh, tolerance=0.1)
        """
        self.logger.info(f"Detecting contact surfaces (tolerance={tolerance})...")

        # Get all unique part IDs
        part_ids = set(elem.part_id for elem in mesh.elements.values())
        self.logger.debug(f"Found {len(part_ids)} parts: {sorted(part_ids)}")

        if len(part_ids) < 2:
            self.logger.warning("Less than 2 parts found, no contacts possible")
            return []

        # Get surface faces for each part
        part_faces = self._extract_surface_faces(mesh)

        # Find contact pairs
        contact_pairs = []

        # Check each pair of parts
        for i, part1 in enumerate(sorted(part_ids)):
            for part2 in sorted(part_ids)[i+1:]:
                self.logger.debug(f"Checking parts {part1} and {part2}...")

                if part1 not in part_faces or part2 not in part_faces:
                    continue

                # Find faces in proximity
                close_faces1, close_faces2, avg_dist = self._find_close_faces(
                    mesh, part_faces[part1], part_faces[part2], tolerance
                )

                if len(close_faces1) >= min_faces and len(close_faces2) >= min_faces:
                    contact_pair = ContactPair(
                        part1_id=part1,
                        part2_id=part2,
                        part1_faces=close_faces1,
                        part2_faces=close_faces2,
                        avg_distance=avg_dist
                    )
                    contact_pairs.append(contact_pair)
                    self.logger.info(
                        f"Found contact: Parts {part1}-{part2}, "
                        f"{len(close_faces1)} and {len(close_faces2)} faces, "
                        f"avg dist={avg_dist:.3f}"
                    )

        self.logger.info(f"Detected {len(contact_pairs)} contact pairs")
        return contact_pairs

    def _extract_surface_faces(self, mesh: MeshData) -> Dict[int, List[Tuple]]:
        """
        Extract surface faces for each part

        A face is on the surface if it belongs to only one element.

        Args:
            mesh: Input mesh

        Returns:
            Dictionary mapping part_id to list of surface face tuples
            Each face tuple: (element_id, face_index, [node_ids])
        """
        # Track which faces appear and in which elements
        face_count = {}  # face_signature -> [(elem_id, face_idx)]

        for elem_id, elem in mesh.elements.items():
            num_faces = elem.num_faces()
            for face_idx in range(num_faces):
                face_nodes = elem.get_face_nodes(face_idx)
                # Create unique signature (sorted node IDs)
                face_sig = tuple(sorted(face_nodes))

                if face_sig not in face_count:
                    face_count[face_sig] = []
                face_count[face_sig].append((elem_id, face_idx, elem.part_id))

        # Surface faces appear only once (or on boundaries between parts)
        part_faces = {}

        for face_sig, occurrences in face_count.items():
            if len(occurrences) == 1:
                # Exterior surface face
                elem_id, face_idx, part_id = occurrences[0]
                if part_id not in part_faces:
                    part_faces[part_id] = []
                part_faces[part_id].append((elem_id, face_idx, list(face_sig)))
            elif len(occurrences) == 2:
                # Check if it's between different parts
                elem_id1, face_idx1, part_id1 = occurrences[0]
                elem_id2, face_idx2, part_id2 = occurrences[1]

                if part_id1 != part_id2:
                    # Interface face between parts
                    if part_id1 not in part_faces:
                        part_faces[part_id1] = []
                    part_faces[part_id1].append((elem_id1, face_idx1, list(face_sig)))

                    if part_id2 not in part_faces:
                        part_faces[part_id2] = []
                    part_faces[part_id2].append((elem_id2, face_idx2, list(face_sig)))

        return part_faces

    def _find_close_faces(self, mesh: MeshData,
                         faces1: List[Tuple],
                         faces2: List[Tuple],
                         tolerance: float) -> Tuple[Set[int], Set[int], float]:
        """
        Find faces from two sets that are within tolerance distance

        Args:
            mesh: Mesh data
            faces1: List of faces from part 1
            faces2: List of faces from part 2
            tolerance: Distance tolerance

        Returns:
            Tuple of (close_face_indices1, close_face_indices2, avg_distance)
        """
        close_faces1 = set()
        close_faces2 = set()
        distances = []

        # Compute face centers
        def get_face_center(face_nodes):
            coords = np.array([
                [mesh.nodes[nid].x, mesh.nodes[nid].y, mesh.nodes[nid].z]
                for nid in face_nodes
            ])
            return np.mean(coords, axis=0)

        # For each face in faces1, find closest face in faces2
        for i, (elem_id1, face_idx1, nodes1) in enumerate(faces1):
            center1 = get_face_center(nodes1)

            min_dist = float('inf')
            closest_j = -1

            for j, (elem_id2, face_idx2, nodes2) in enumerate(faces2):
                center2 = get_face_center(nodes2)
                dist = np.linalg.norm(center1 - center2)

                if dist < min_dist:
                    min_dist = dist
                    closest_j = j

            # If within tolerance, add to close faces
            if min_dist <= tolerance:
                close_faces1.add(i)
                close_faces2.add(closest_j)
                distances.append(min_dist)

        avg_dist = np.mean(distances) if distances else 0.0

        return close_faces1, close_faces2, avg_dist

    def export_contact_pairs(self, contacts: List[ContactPair],
                            filename: str,
                            format: str = "abaqus"):
        """
        Export contact pairs to file

        Args:
            contacts: List of ContactPair objects
            filename: Output filename
            format: Output format ("abaqus" or "lsdyna")

        Example:
            >>> detector.export_contact_pairs(contacts, "contacts.inp", "abaqus")
        """
        self.logger.info(f"Exporting {len(contacts)} contact pairs to {filename}")

        if format.lower() == "abaqus":
            self._export_abaqus_contacts(contacts, filename)
        elif format.lower() == "lsdyna":
            self._export_lsdyna_contacts(contacts, filename)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _export_abaqus_contacts(self, contacts: List[ContactPair], filename: str):
        """Export contacts in Abaqus format"""
        with open(filename, 'w') as f:
            f.write("** Contact definitions\n")
            f.write("** Generated by KooMeshGenerator\n")
            f.write("**\n")

            for i, contact in enumerate(contacts):
                f.write(f"** Contact pair {i+1}: Parts {contact.part1_id} - {contact.part2_id}\n")
                f.write(f"*Contact Pair, interaction=Contact{i+1}, type=SURFACE TO SURFACE\n")
                f.write(f"Part{contact.part1_id}_Surf, Part{contact.part2_id}_Surf\n")
                f.write("**\n")

        self.logger.info(f"Exported Abaqus contact definitions")

    def _export_lsdyna_contacts(self, contacts: List[ContactPair], filename: str):
        """Export contacts in LS-DYNA format"""
        with open(filename, 'w') as f:
            f.write("$# Contact definitions\n")
            f.write("$# Generated by KooMeshGenerator\n")
            f.write("$\n")

            for i, contact in enumerate(contacts):
                f.write(f"$# Contact {i+1}: Parts {contact.part1_id} - {contact.part2_id}\n")
                f.write("*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE\n")
                f.write(f"$# SSID      MSID      SSTYP     MSTYP\n")
                f.write(f"{contact.part1_id:10d}{contact.part2_id:10d}         3         3\n")
                f.write("$\n")

        self.logger.info(f"Exported LS-DYNA contact definitions")

    def detect_self_contacts(self, mesh: MeshData,
                             tolerance: float = 0.1,
                             min_angle: float = 120.0,
                             part_id: int = None) -> List[SelfContactPair]:
        """
        Detect self-contact within a part

        Self-contact occurs when different regions of the same part are in
        close proximity with opposing normals (e.g., folding, crushing).

        Args:
            mesh: Mesh to analyze
            tolerance: Maximum distance to consider as potential contact
            min_angle: Minimum angle (degrees) between face normals to consider
                      as potential contact (180° = exactly opposite)
            part_id: Specific part ID to analyze (None = analyze all parts)

        Returns:
            List of SelfContactPair objects

        Example:
            >>> detector = ContactSurfaceDetector()
            >>> self_contacts = detector.detect_self_contacts(mesh, tolerance=0.5)
            >>> for sc in self_contacts:
            ...     print(f"Part {sc.part_id}: {len(sc.face_pairs)} self-contact pairs")
        """
        self.logger.info(f"Detecting self-contacts (tolerance={tolerance}, min_angle={min_angle}°)...")

        # Get parts to analyze
        if part_id is not None:
            part_ids = [part_id]
        else:
            part_ids = list(set(elem.part_id for elem in mesh.elements.values()))

        self.logger.debug(f"Analyzing {len(part_ids)} parts for self-contact")

        # Get surface faces for each part
        part_faces_dict = self._extract_surface_faces(mesh)

        self_contact_pairs = []

        for pid in part_ids:
            if pid not in part_faces_dict:
                continue

            faces = part_faces_dict[pid]
            self.logger.debug(f"Part {pid}: {len(faces)} surface faces")

            if len(faces) < 2:
                continue

            # Find self-contacting face pairs
            face_pairs, distances = self._find_self_contact_faces(
                mesh, faces, tolerance, min_angle
            )

            if face_pairs:
                avg_dist = np.mean(distances)
                min_dist = np.min(distances)

                self_contact = SelfContactPair(
                    part_id=pid,
                    face_pairs=face_pairs,
                    avg_distance=avg_dist,
                    min_distance=min_dist
                )
                self_contact_pairs.append(self_contact)

                self.logger.info(
                    f"Part {pid}: {len(face_pairs)} self-contact pairs, "
                    f"avg dist={avg_dist:.3f}, min dist={min_dist:.3f}"
                )

        self.logger.info(f"Detected self-contact in {len(self_contact_pairs)} parts")
        return self_contact_pairs

    def _find_self_contact_faces(self, mesh: MeshData,
                                 faces: List[Tuple],
                                 tolerance: float,
                                 min_angle: float) -> Tuple[List[Tuple[int, int]], List[float]]:
        """
        Find self-contacting face pairs within a set of faces

        Args:
            mesh: Mesh data
            faces: List of face tuples (elem_id, face_idx, node_ids)
            tolerance: Distance tolerance
            min_angle: Minimum angle between normals (degrees)

        Returns:
            Tuple of (face_pairs, distances)
            face_pairs: List of (face_idx1, face_idx2) tuples
            distances: Corresponding distances
        """
        from scipy.spatial import KDTree

        # Compute face centers and normals
        face_centers = []
        face_normals = []

        for elem_id, face_idx, node_ids in faces:
            # Get face center
            coords = np.array([
                [mesh.nodes[nid].x, mesh.nodes[nid].y, mesh.nodes[nid].z]
                for nid in node_ids
            ])
            center = np.mean(coords, axis=0)
            face_centers.append(center)

            # Compute face normal (for triangular or quad faces)
            if len(node_ids) >= 3:
                v1 = coords[1] - coords[0]
                v2 = coords[2] - coords[0]
                normal = np.cross(v1, v2)
                norm_length = np.linalg.norm(normal)
                if norm_length > 1e-10:
                    normal = normal / norm_length
                else:
                    normal = np.array([0, 0, 1])  # Default normal
            else:
                normal = np.array([0, 0, 1])

            face_normals.append(normal)

        face_centers = np.array(face_centers)
        face_normals = np.array(face_normals)

        # Build KD-tree for efficient spatial queries
        kdtree = KDTree(face_centers)

        # Find face pairs within tolerance
        face_pairs = []
        distances = []

        # Convert min_angle to radians
        min_angle_rad = np.radians(min_angle)

        # For each face, find nearby faces
        for i in range(len(faces)):
            # Query faces within tolerance
            indices = kdtree.query_ball_point(face_centers[i], tolerance)

            for j in indices:
                # Skip self and already processed pairs
                if j <= i:
                    continue

                # Check distance
                dist = np.linalg.norm(face_centers[i] - face_centers[j])

                if dist < tolerance:
                    # Check if normals are opposing
                    # Dot product close to -1 means opposite directions
                    dot_product = np.dot(face_normals[i], face_normals[j])
                    angle = np.arccos(np.clip(dot_product, -1.0, 1.0))

                    # If angle >= min_angle, faces are approaching/opposing
                    if angle >= min_angle_rad:
                        face_pairs.append((i, j))
                        distances.append(dist)

        return face_pairs, distances


def detect_and_report_contacts(mesh: MeshData,
                               tolerance: float = 0.1) -> List[ContactPair]:
    """
    Convenience function to detect and report contacts

    Args:
        mesh: Mesh to analyze
        tolerance: Distance tolerance for contact detection

    Returns:
        List of ContactPair objects

    Example:
        >>> contacts = detect_and_report_contacts(mesh, tolerance=0.1)
    """
    detector = ContactSurfaceDetector()
    contacts = detector.detect_contacts(mesh, tolerance=tolerance)

    if contacts:
        logger.info("\nContact Surface Report:")
        logger.info("=" * 60)
        for i, contact in enumerate(contacts):
            logger.info(f"Contact {i+1}:")
            logger.info(f"  Parts: {contact.part1_id} <-> {contact.part2_id}")
            logger.info(f"  Faces: {len(contact.part1_faces)} <-> {len(contact.part2_faces)}")
            logger.info(f"  Avg distance: {contact.avg_distance:.4f}")
        logger.info("=" * 60)
    else:
        logger.info("No contact surfaces detected")

    return contacts
