"""
Mesh Quality Checker
====================

This module provides functionality to check and evaluate mesh quality.

Quality Metrics:
- Jacobian (determinant)
- Aspect ratio
- Skewness
- Warpage (for hex elements)
- Minimum/maximum angles
- Volume/area

Usage:
    >>> from koomesh.meshing.quality_checker import QualityChecker
    >>> checker = QualityChecker()
    >>> report = checker.check_mesh(mesh)
    >>> print(f"Min Jacobian: {report.jacobian['min']}")
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import numpy as np

from koomesh.meshing.mesh_data import MeshData, Element, ElementType


@dataclass
class QualityReport:
    """
    Mesh quality report

    Attributes:
        num_elements: Total number of elements
        num_bad_elements: Number of elements below quality threshold
        jacobian: Jacobian statistics
        aspect_ratio: Aspect ratio statistics
        skewness: Skewness statistics
        warpage: Warpage statistics (hex only)
        element_size: Element size statistics
        bad_elements: List of bad element IDs
    """
    num_elements: int = 0
    num_bad_elements: int = 0
    jacobian: Dict = field(default_factory=dict)
    aspect_ratio: Dict = field(default_factory=dict)
    skewness: Dict = field(default_factory=dict)
    warpage: Dict = field(default_factory=dict)
    element_size: Dict = field(default_factory=dict)
    bad_elements: List[int] = field(default_factory=list)

    def is_valid(self) -> bool:
        """Check if mesh passes quality criteria"""
        # Check for negative Jacobians
        if self.jacobian.get('negative_elements', 0) > 0:
            return False

        # Check for extreme aspect ratios
        if self.aspect_ratio.get('max', 0) > 100:
            return False

        return True

    def summary(self) -> str:
        """Get quality report summary as string"""
        lines = [
            f"Mesh Quality Report",
            f"=" * 60,
            f"Total Elements: {self.num_elements}",
            f"Bad Elements: {self.num_bad_elements}",
            f"",
            f"Jacobian:",
            f"  Min: {self.jacobian.get('min', 0):.6f}",
            f"  Max: {self.jacobian.get('max', 0):.6f}",
            f"  Mean: {self.jacobian.get('mean', 0):.6f}",
            f"  Negative: {self.jacobian.get('negative_elements', 0)}",
            f"",
            f"Aspect Ratio:",
            f"  Min: {self.aspect_ratio.get('min', 0):.3f}",
            f"  Max: {self.aspect_ratio.get('max', 0):.3f}",
            f"  Mean: {self.aspect_ratio.get('mean', 0):.3f}",
            f"  Bad (>10): {self.aspect_ratio.get('bad_elements', 0)}",
            f"",
            f"Skewness:",
            f"  Min: {self.skewness.get('min', 0):.3f}",
            f"  Max: {self.skewness.get('max', 0):.3f}",
            f"  Mean: {self.skewness.get('mean', 0):.3f}",
        ]

        if self.warpage:
            lines.extend([
                f"",
                f"Warpage:",
                f"  Max: {self.warpage.get('max', 0):.3f}",
                f"  Mean: {self.warpage.get('mean', 0):.3f}",
            ])

        lines.extend([
            f"",
            f"Element Size:",
            f"  Min: {self.element_size.get('min', 0):.6f}",
            f"  Max: {self.element_size.get('max', 0):.6f}",
            f"  Mean: {self.element_size.get('mean', 0):.6f}",
            f"",
            f"Status: {'PASS' if self.is_valid() else 'FAIL'}",
            f"=" * 60,
        ])

        return "\n".join(lines)


class QualityChecker:
    """
    Mesh quality checker

    This class provides methods to evaluate mesh quality metrics including
    Jacobian, aspect ratio, skewness, and other quality measures.

    Example:
        >>> checker = QualityChecker(jacobian_threshold=0.1)
        >>> report = checker.check_mesh(mesh)
        >>> if not report.is_valid():
        ...     print("Mesh has quality issues!")
        ...     print(report.summary())
    """

    def __init__(self,
                 jacobian_threshold: float = 0.1,
                 aspect_ratio_threshold: float = 10.0,
                 skewness_threshold: float = 0.8):
        """
        Initialize quality checker

        Args:
            jacobian_threshold: Minimum acceptable Jacobian
            aspect_ratio_threshold: Maximum acceptable aspect ratio
            skewness_threshold: Maximum acceptable skewness
        """
        self.jacobian_threshold = jacobian_threshold
        self.aspect_ratio_threshold = aspect_ratio_threshold
        self.skewness_threshold = skewness_threshold

        self.logger = logging.getLogger(__name__)

    def check_mesh(self, mesh: MeshData) -> QualityReport:
        """
        Check mesh quality

        Args:
            mesh: MeshData to check

        Returns:
            QualityReport with quality statistics
        """
        self.logger.info("Checking mesh quality...")

        report = QualityReport()
        report.num_elements = mesh.num_elements()

        # Check Jacobian
        report.jacobian = self._check_jacobian(mesh)

        # Check aspect ratio
        report.aspect_ratio = self._check_aspect_ratio(mesh)

        # Check skewness
        report.skewness = self._check_skewness(mesh)

        # Check warpage (for hex elements)
        if mesh.element_type.is_hex():
            report.warpage = self._check_warpage(mesh)

        # Check element size
        report.element_size = self._check_element_size(mesh)

        # Identify bad elements
        report.bad_elements = self._identify_bad_elements(mesh, report)
        report.num_bad_elements = len(report.bad_elements)

        self.logger.info(f"Quality check complete: {report.num_bad_elements} bad elements found")

        return report

    def _check_jacobian(self, mesh: MeshData) -> Dict:
        """
        Check Jacobian (determinant) for all elements

        Returns:
            Dictionary with Jacobian statistics
        """
        jacobians = []

        for elem in mesh.elements.values():
            jac = self._compute_jacobian(elem, mesh)
            jacobians.append(jac)

        jacobians = np.array(jacobians)
        negative = np.sum(jacobians < 0)

        return {
            'min': float(np.min(jacobians)),
            'max': float(np.max(jacobians)),
            'mean': float(np.mean(jacobians)),
            'median': float(np.median(jacobians)),
            'std': float(np.std(jacobians)),
            'negative_elements': int(negative),
            'below_threshold': int(np.sum(jacobians < self.jacobian_threshold))
        }

    def _compute_jacobian(self, elem: Element, mesh: MeshData) -> float:
        """
        Compute Jacobian for a single element

        Args:
            elem: Element to check
            mesh: Parent mesh

        Returns:
            Jacobian value (minimum across all integration points)
        """
        # Get node coordinates
        coords = np.array([
            mesh.get_node(nid).coordinates() for nid in elem.nodes
        ])

        if elem.type == ElementType.TET4:
            return self._jacobian_tet4(coords)
        elif elem.type == ElementType.HEX8:
            return self._jacobian_hex8(coords)
        else:
            # Default: compute volume as proxy for Jacobian
            return self._compute_volume(coords)

    def _jacobian_tet4(self, coords: np.ndarray) -> float:
        """Compute Jacobian for 4-node tetrahedron"""
        # Jacobian = det([[x1-x0, x2-x0, x3-x0],
        #                  [y1-y0, y2-y0, y3-y0],
        #                  [z1-z0, z2-z0, z3-z0]]) / 6

        v1 = coords[1] - coords[0]
        v2 = coords[2] - coords[0]
        v3 = coords[3] - coords[0]

        jacobian_matrix = np.column_stack([v1, v2, v3])
        det = np.linalg.det(jacobian_matrix)

        return det / 6.0

    def _jacobian_hex8(self, coords: np.ndarray) -> float:
        """Compute minimum Jacobian for 8-node hexahedron"""
        # Check Jacobian at all 8 corner nodes
        # This is a simplified check; full implementation would check at integration points

        min_jac = float('inf')

        # Natural coordinates of corner nodes
        xi_corners = [
            [-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
            [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]
        ]

        for xi in xi_corners:
            jac = self._jacobian_hex8_at_point(coords, xi)
            min_jac = min(min_jac, jac)

        return min_jac

    def _jacobian_hex8_at_point(self, coords: np.ndarray, xi: List[float]) -> float:
        """
        Compute Jacobian of hex8 at natural coordinate xi

        Args:
            coords: Node coordinates (8, 3) - 8 nodes with x, y, z
            xi: Natural coordinates [r, s, t] in [-1, 1]

        Returns:
            Jacobian determinant
        """
        # Shape function derivatives with respect to natural coordinates
        # dN_dxi shape: (3, 8) - derivatives for each natural coord
        dN_dxi = self._hex8_shape_derivatives(xi)

        # Jacobian matrix J = dN/dxi @ coords
        # (3, 8) @ (8, 3) = (3, 3)
        J = dN_dxi @ coords

        # Return determinant
        return np.linalg.det(J)

    def _hex8_shape_derivatives(self, xi: List[float]) -> np.ndarray:
        """Compute shape function derivatives for hex8"""
        r, s, t = xi

        dN = np.array([
            [-(1-s)*(1-t), (1-s)*(1-t), (1+s)*(1-t), -(1+s)*(1-t),
             -(1-s)*(1+t), (1-s)*(1+t), (1+s)*(1+t), -(1+s)*(1+t)],
            [-(1-r)*(1-t), -(1+r)*(1-t), (1+r)*(1-t), (1-r)*(1-t),
             -(1-r)*(1+t), -(1+r)*(1+t), (1+r)*(1+t), (1-r)*(1+t)],
            [-(1-r)*(1-s), -(1+r)*(1-s), -(1+r)*(1+s), -(1-r)*(1+s),
             (1-r)*(1-s), (1+r)*(1-s), (1+r)*(1+s), (1-r)*(1+s)]
        ]) / 8.0

        return dN

    def _check_aspect_ratio(self, mesh: MeshData) -> Dict:
        """
        Check aspect ratio for all elements

        Aspect ratio = max_edge_length / min_edge_length

        Returns:
            Dictionary with aspect ratio statistics
        """
        ratios = []

        for elem in mesh.elements.values():
            ratio = self._compute_aspect_ratio(elem, mesh)
            ratios.append(ratio)

        ratios = np.array(ratios)

        return {
            'min': float(np.min(ratios)),
            'max': float(np.max(ratios)),
            'mean': float(np.mean(ratios)),
            'median': float(np.median(ratios)),
            'std': float(np.std(ratios)),
            'bad_elements': int(np.sum(ratios > self.aspect_ratio_threshold))
        }

    def _compute_aspect_ratio(self, elem: Element, mesh: MeshData) -> float:
        """Compute aspect ratio for a single element"""
        # Get node coordinates
        coords = np.array([
            mesh.get_node(nid).coordinates() for nid in elem.nodes
        ])

        # Compute all edge lengths
        edge_lengths = []

        if elem.type == ElementType.TET4:
            # 6 edges for tetrahedron
            edges = [(0, 1), (1, 2), (2, 0), (0, 3), (1, 3), (2, 3)]
        elif elem.type == ElementType.HEX8:
            # 12 edges for hexahedron
            edges = [
                (0, 1), (1, 2), (2, 3), (3, 0),  # Bottom face
                (4, 5), (5, 6), (6, 7), (7, 4),  # Top face
                (0, 4), (1, 5), (2, 6), (3, 7)   # Vertical edges
            ]
        else:
            # Default: all pairs
            edges = [(i, j) for i in range(len(elem.nodes)) for j in range(i+1, len(elem.nodes))]

        for i, j in edges:
            length = np.linalg.norm(coords[i] - coords[j])
            edge_lengths.append(length)

        if not edge_lengths:
            return 1.0

        max_length = max(edge_lengths)
        min_length = min(edge_lengths)

        if min_length < 1e-10:
            return float('inf')

        return max_length / min_length

    def _check_skewness(self, mesh: MeshData) -> Dict:
        """
        Check skewness for all elements

        Skewness measures deviation from ideal element shape

        Returns:
            Dictionary with skewness statistics
        """
        skewness_values = []

        for elem in mesh.elements.values():
            skew = self._compute_skewness(elem, mesh)
            skewness_values.append(skew)

        skewness_values = np.array(skewness_values)

        return {
            'min': float(np.min(skewness_values)),
            'max': float(np.max(skewness_values)),
            'mean': float(np.mean(skewness_values)),
            'median': float(np.median(skewness_values)),
            'bad_elements': int(np.sum(skewness_values > self.skewness_threshold))
        }

    def _compute_skewness(self, elem: Element, mesh: MeshData) -> float:
        """Compute skewness for a single element"""
        # Simplified skewness calculation
        # Real implementation would be more sophisticated

        # Get aspect ratio as proxy for skewness
        aspect_ratio = self._compute_aspect_ratio(elem, mesh)

        # Normalize to 0-1 range (0 = ideal, 1 = worst)
        skewness = (aspect_ratio - 1.0) / (aspect_ratio + 1.0)

        return max(0.0, min(1.0, skewness))

    def _check_warpage(self, mesh: MeshData) -> Dict:
        """
        Check warpage for hexahedral elements

        Warpage measures out-of-plane distortion of faces

        Returns:
            Dictionary with warpage statistics
        """
        warpage_values = []

        for elem in mesh.elements.values():
            if elem.type.is_hex():
                warp = self._compute_warpage(elem, mesh)
                warpage_values.append(warp)

        if not warpage_values:
            return {}

        warpage_values = np.array(warpage_values)

        return {
            'max': float(np.max(warpage_values)),
            'mean': float(np.mean(warpage_values)),
            'bad_elements': int(np.sum(warpage_values > 0.1))  # 10% threshold
        }

    def _compute_warpage(self, elem: Element, mesh: MeshData) -> float:
        """Compute warpage for a hexahedral element"""
        # Simplified warpage calculation
        # Check planarity of each face

        max_warpage = 0.0

        for face_id in range(elem.num_faces()):
            face_nodes = elem.get_face_nodes(face_id)
            coords = np.array([
                mesh.get_node(nid).coordinates() for nid in face_nodes
            ])

            # Compute face warpage
            if len(coords) == 4:  # Quadrilateral face
                # Check if all 4 points are coplanar
                # Distance from 4th point to plane defined by first 3 points
                v1 = coords[1] - coords[0]
                v2 = coords[2] - coords[0]
                normal = np.cross(v1, v2)
                normal = normal / np.linalg.norm(normal)

                d = abs(np.dot(coords[3] - coords[0], normal))

                # Normalize by face size
                face_size = max(np.linalg.norm(v1), np.linalg.norm(v2))
                warpage = d / face_size if face_size > 1e-10 else 0.0

                max_warpage = max(max_warpage, warpage)

        return max_warpage

    def _check_element_size(self, mesh: MeshData) -> Dict:
        """
        Check element size distribution

        Returns:
            Dictionary with element size statistics
        """
        sizes = []

        for elem in mesh.elements.values():
            size = self._compute_element_size(elem, mesh)
            sizes.append(size)

        sizes = np.array(sizes)

        return {
            'min': float(np.min(sizes)),
            'max': float(np.max(sizes)),
            'mean': float(np.mean(sizes)),
            'median': float(np.median(sizes)),
            'std': float(np.std(sizes)),
            'ratio': float(np.max(sizes) / np.min(sizes)) if np.min(sizes) > 0 else float('inf')
        }

    def _compute_element_size(self, elem: Element, mesh: MeshData) -> float:
        """Compute characteristic size of element"""
        # Use cube root of volume for 3D elements
        coords = np.array([
            mesh.get_node(nid).coordinates() for nid in elem.nodes
        ])

        volume = self._compute_volume(coords)
        return volume ** (1.0/3.0)

    def _compute_volume(self, coords: np.ndarray) -> float:
        """Compute element volume"""
        # Simplified volume calculation
        if len(coords) == 4:  # Tetrahedron
            v1 = coords[1] - coords[0]
            v2 = coords[2] - coords[0]
            v3 = coords[3] - coords[0]
            return abs(np.dot(v1, np.cross(v2, v3))) / 6.0

        elif len(coords) == 8:  # Hexahedron (approximate)
            # Use bounding box volume as approximation
            bbox_min = coords.min(axis=0)
            bbox_max = coords.max(axis=0)
            return np.prod(bbox_max - bbox_min)

        else:
            # Default: use bounding box
            bbox_min = coords.min(axis=0)
            bbox_max = coords.max(axis=0)
            return np.prod(bbox_max - bbox_min)

    def _identify_bad_elements(self, mesh: MeshData, report: QualityReport) -> List[int]:
        """
        Identify elements that fail quality criteria

        Args:
            mesh: Mesh to check
            report: Quality report with statistics

        Returns:
            List of bad element IDs
        """
        bad_elements = []

        for elem in mesh.elements.values():
            # Check Jacobian
            jac = self._compute_jacobian(elem, mesh)
            if jac < self.jacobian_threshold:
                bad_elements.append(elem.id)
                continue

            # Check aspect ratio
            ar = self._compute_aspect_ratio(elem, mesh)
            if ar > self.aspect_ratio_threshold:
                bad_elements.append(elem.id)
                continue

            # Check skewness
            skew = self._compute_skewness(elem, mesh)
            if skew > self.skewness_threshold:
                bad_elements.append(elem.id)
                continue

        return bad_elements
