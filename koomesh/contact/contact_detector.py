"""
Contact Detector
================

This module provides functionality to automatically detect contact interfaces
between mesh surfaces.

Features:
- Spatial proximity detection
- Surface element extraction
- KD-tree based efficient search
- Gap distance calculation

Usage:
    >>> from koomesh.contact.contact_detector import ContactDetector
    >>> detector = ContactDetector(tolerance=0.01)
    >>> contacts = detector.detect_contacts([mesh1, mesh2], hierarchy)
"""

import logging
from typing import List, Tuple, Dict, Optional
import numpy as np
from scipy.spatial import cKDTree

from koomesh.meshing.mesh_data import MeshData
from koomesh.io.hierarchy_parser import HierarchyNode
from koomesh.contact.contact_data import (
    ContactPair, ContactSurface, ContactType, ContactManager
)


class ContactDetector:
    """
    Automatic contact detection between mesh surfaces

    This class uses spatial proximity search to identify surfaces that
    are in contact or near contact.

    Attributes:
        tolerance: Distance tolerance for contact detection
        logger: Logger instance

    Example:
        >>> detector = ContactDetector(tolerance=0.01)
        >>> contacts = detector.detect_contacts(meshes, hierarchy)
        >>> print(f"Found {len(contacts)} contact pairs")
    """

    def __init__(self, tolerance: float = 1e-4):
        """
        Initialize contact detector

        Args:
            tolerance: Distance tolerance for considering surfaces in contact
        """
        self.tolerance = tolerance
        self.logger = logging.getLogger(__name__)

    def detect_contacts(self,
                       meshes: List[MeshData],
                       hierarchy: HierarchyNode,
                       contact_manager: Optional[ContactManager] = None) -> List[ContactPair]:
        """
        Detect contact pairs between multiple meshes

        Args:
            meshes: List of MeshData objects
            hierarchy: Hierarchy tree
            contact_manager: Optional contact manager to add contacts to

        Returns:
            List of detected contact pairs
        """
        if contact_manager is None:
            contact_manager = ContactManager()

        self.logger.info(f"Detecting contacts between {len(meshes)} meshes...")

        # Flatten hierarchy to get all nodes
        nodes = self._flatten_hierarchy(hierarchy)

        if len(nodes) != len(meshes):
            self.logger.warning(
                f"Hierarchy has {len(nodes)} nodes but {len(meshes)} meshes provided"
            )

        contacts = []

        # Compare each pair of meshes
        for i in range(len(meshes)):
            for j in range(i + 1, len(meshes)):
                mesh1 = meshes[i]
                mesh2 = meshes[j]
                node1 = nodes[i] if i < len(nodes) else None
                node2 = nodes[j] if j < len(nodes) else None

                # Check if meshes are spatially close
                if self._are_meshes_close(mesh1, mesh2):
                    # Detect contact between this pair
                    contact_pair = self._detect_contact_pair(
                        mesh1, mesh2, node1, node2, i, j
                    )

                    if contact_pair:
                        contacts.append(contact_pair)
                        contact_manager.add_contact(contact_pair)

        self.logger.info(f"Detected {len(contacts)} contact pairs")

        return contacts

    def _flatten_hierarchy(self, root: HierarchyNode) -> List[HierarchyNode]:
        """
        Flatten hierarchy tree to list

        Args:
            root: Root node

        Returns:
            List of all nodes in depth-first order
        """
        result = [root]
        for child in root.children:
            result.extend(self._flatten_hierarchy(child))
        return result

    def _are_meshes_close(self, mesh1: MeshData, mesh2: MeshData) -> bool:
        """
        Quick check if two meshes are spatially close

        Uses bounding box overlap test.

        Args:
            mesh1, mesh2: Meshes to check

        Returns:
            True if bounding boxes overlap (with tolerance)
        """
        # Get bounding boxes
        bbox1_min, bbox1_max = mesh1.get_bounding_box()
        bbox2_min, bbox2_max = mesh2.get_bounding_box()

        # Check for overlap in all dimensions
        tolerance_vec = np.array([self.tolerance] * 3)

        # Expand bounding boxes by tolerance
        bbox1_min_exp = bbox1_min - tolerance_vec
        bbox1_max_exp = bbox1_max + tolerance_vec
        bbox2_min_exp = bbox2_min - tolerance_vec
        bbox2_max_exp = bbox2_max + tolerance_vec

        # Check overlap
        overlap = np.all(bbox1_max_exp >= bbox2_min_exp) and \
                 np.all(bbox2_max_exp >= bbox1_min_exp)

        return overlap

    def _detect_contact_pair(self,
                            mesh1: MeshData,
                            mesh2: MeshData,
                            node1: Optional[HierarchyNode],
                            node2: Optional[HierarchyNode],
                            part_id1: int,
                            part_id2: int) -> Optional[ContactPair]:
        """
        Detect contact between two specific meshes

        Args:
            mesh1, mesh2: Meshes to check
            node1, node2: Hierarchy nodes (optional)
            part_id1, part_id2: Part IDs

        Returns:
            ContactPair if contact detected, None otherwise
        """
        # Extract surface elements
        surface1 = self._extract_surface(mesh1, part_id1,
                                        node1.name if node1 else f"Part{part_id1}")
        surface2 = self._extract_surface(mesh2, part_id2,
                                        node2.name if node2 else f"Part{part_id2}")

        if not surface1.element_ids or not surface2.element_ids:
            return None

        # Find close surface elements
        close_pairs = self._find_close_surfaces(mesh1, mesh2, surface1, surface2)

        if not close_pairs:
            return None

        # Create contact pair
        contact_pair = ContactPair(
            master_surface=surface1,
            slave_surface=surface2,
            contact_type=ContactType.SURFACE_TO_SURFACE,
            gap=close_pairs[0]['distance']  # Minimum gap
        )

        self.logger.debug(
            f"Contact detected: {surface1.part_name} <-> {surface2.part_name}, "
            f"gap={contact_pair.gap:.6f}"
        )

        return contact_pair

    def _extract_surface(self, mesh: MeshData, part_id: int, part_name: str) -> ContactSurface:
        """
        Extract surface elements from mesh

        Args:
            mesh: Mesh to extract surface from
            part_id: Part ID
            part_name: Part name

        Returns:
            ContactSurface with surface element IDs
        """
        # Find all surface elements (elements with faces not shared with neighbors)
        surface_faces = mesh.find_surface_elements()

        # Extract unique element IDs
        element_ids = list(set([elem_id for elem_id, face_id in surface_faces]))

        # Extract surface nodes
        node_ids = set()
        for elem_id, face_id in surface_faces:
            elem = mesh.get_element(elem_id)
            face_nodes = elem.get_face_nodes(face_id)
            node_ids.update(face_nodes)

        surface = ContactSurface(
            part_name=part_name,
            part_id=part_id,
            element_ids=element_ids,
            face_ids=[face_id for _, face_id in surface_faces],
            node_ids=list(node_ids)
        )

        self.logger.debug(
            f"Extracted surface for {part_name}: "
            f"{len(element_ids)} elements, {len(node_ids)} nodes"
        )

        return surface

    def _find_close_surfaces(self,
                           mesh1: MeshData,
                           mesh2: MeshData,
                           surface1: ContactSurface,
                           surface2: ContactSurface) -> List[Dict]:
        """
        Find close surface pairs using KD-tree

        Args:
            mesh1, mesh2: Meshes
            surface1, surface2: Surface definitions

        Returns:
            List of dictionaries with close pairs and distances
        """
        # Get surface node coordinates
        coords1 = np.array([
            mesh1.get_node(nid).coordinates() for nid in surface1.node_ids
        ])
        coords2 = np.array([
            mesh2.get_node(nid).coordinates() for nid in surface2.node_ids
        ])

        if len(coords1) == 0 or len(coords2) == 0:
            return []

        # Build KD-tree for surface2
        tree2 = cKDTree(coords2)

        # Query for close points
        distances, indices = tree2.query(coords1, k=1, distance_upper_bound=self.tolerance * 10)

        # Find pairs within tolerance
        close_pairs = []
        for i, (dist, idx) in enumerate(zip(distances, indices)):
            if dist <= self.tolerance * 10 and idx < len(coords2):
                close_pairs.append({
                    'node1': surface1.node_ids[i],
                    'node2': surface2.node_ids[idx],
                    'distance': dist
                })

        self.logger.debug(
            f"Found {len(close_pairs)} close node pairs "
            f"(tolerance={self.tolerance * 10:.6f})"
        )

        return close_pairs

    def detect_self_contact(self, mesh: MeshData) -> Optional[ContactPair]:
        """
        Detect self-contact within a single mesh

        Args:
            mesh: Mesh to check for self-contact

        Returns:
            ContactPair for self-contact, or None
        """
        self.logger.info("Detecting self-contact...")

        # Extract surface
        surface = self._extract_surface(mesh, 1, "Self")

        if len(surface.node_ids) < 2:
            return None

        # Get surface coordinates
        coords = np.array([
            mesh.get_node(nid).coordinates() for nid in surface.node_ids
        ])

        # Build KD-tree
        tree = cKDTree(coords)

        # Find pairs of points closer than tolerance (excluding self)
        pairs = tree.query_pairs(self.tolerance * 10)

        if len(pairs) == 0:
            self.logger.debug("No self-contact detected")
            return None

        # Create self-contact pair
        contact_pair = ContactPair(
            master_surface=surface,
            slave_surface=surface,
            contact_type=ContactType.AUTOMATIC
        )

        contact_pair.metadata['self_contact'] = True
        contact_pair.metadata['num_close_pairs'] = len(pairs)

        self.logger.info(f"Self-contact detected with {len(pairs)} close pairs")

        return contact_pair

    def refine_contact_surface(self,
                               contact: ContactPair,
                               mesh1: MeshData,
                               mesh2: MeshData,
                               max_gap: Optional[float] = None) -> ContactPair:
        """
        Refine contact surface by removing elements beyond max gap

        Args:
            contact: Contact pair to refine
            mesh1: Master mesh
            mesh2: Slave mesh
            max_gap: Maximum gap distance (uses tolerance if not specified)

        Returns:
            Refined contact pair
        """
        if max_gap is None:
            max_gap = self.tolerance

        self.logger.debug(f"Refining contact surface with max_gap={max_gap}")

        # Get element centroids for master surface
        master_centroids = []
        for elem_id in contact.master_surface.element_ids:
            elem = mesh1.get_element(elem_id)
            coords = np.array([
                mesh1.get_node(nid).coordinates() for nid in elem.nodes
            ])
            centroid = coords.mean(axis=0)
            master_centroids.append((elem_id, centroid))

        # Get element centroids for slave surface
        slave_centroids = []
        for elem_id in contact.slave_surface.element_ids:
            elem = mesh2.get_element(elem_id)
            coords = np.array([
                mesh2.get_node(nid).coordinates() for nid in elem.nodes
            ])
            centroid = coords.mean(axis=0)
            slave_centroids.append((elem_id, centroid))

        # Build KD-tree for slave centroids
        slave_coords = np.array([c[1] for c in slave_centroids])
        tree = cKDTree(slave_coords)

        # Find master elements within max_gap of any slave element
        refined_master_ids = []
        for elem_id, centroid in master_centroids:
            distances, _ = tree.query(centroid, k=1)
            if distances <= max_gap:
                refined_master_ids.append(elem_id)

        # Similarly for slave elements
        master_coords = np.array([c[1] for c in master_centroids])
        tree = cKDTree(master_coords)

        refined_slave_ids = []
        for elem_id, centroid in slave_centroids:
            distances, _ = tree.query(centroid, k=1)
            if distances <= max_gap:
                refined_slave_ids.append(elem_id)

        # Update contact surfaces
        contact.master_surface.element_ids = refined_master_ids
        contact.slave_surface.element_ids = refined_slave_ids

        self.logger.debug(
            f"Refined contact: master={len(refined_master_ids)} elements, "
            f"slave={len(refined_slave_ids)} elements"
        )

        return contact

    def compute_contact_gap(self,
                           contact: ContactPair,
                           mesh1: MeshData,
                           mesh2: MeshData) -> float:
        """
        Compute average gap distance for contact

        Args:
            contact: Contact pair
            mesh1: Master mesh
            mesh2: Slave mesh

        Returns:
            Average gap distance
        """
        # Sample points from master surface
        master_points = []
        for elem_id in contact.master_surface.element_ids[:100]:  # Sample first 100
            elem = mesh1.get_element(elem_id)
            coords = np.array([
                mesh1.get_node(nid).coordinates() for nid in elem.nodes
            ])
            centroid = coords.mean(axis=0)
            master_points.append(centroid)

        if not master_points:
            return 0.0

        master_points = np.array(master_points)

        # Sample points from slave surface
        slave_points = []
        for elem_id in contact.slave_surface.element_ids[:100]:  # Sample first 100
            elem = mesh2.get_element(elem_id)
            coords = np.array([
                mesh2.get_node(nid).coordinates() for nid in elem.nodes
            ])
            centroid = coords.mean(axis=0)
            slave_points.append(centroid)

        if not slave_points:
            return 0.0

        slave_points = np.array(slave_points)

        # Build KD-tree and find nearest distances
        tree = cKDTree(slave_points)
        distances, _ = tree.query(master_points, k=1)

        # Return mean distance
        mean_gap = float(np.mean(distances))

        self.logger.debug(f"Computed contact gap: {mean_gap:.6f}")

        return mean_gap
