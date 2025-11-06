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
        angles: Angle statistics (min/max angles) [Added in [007]]
        edge_length_ratio: Edge length ratio statistics [Added in [007]]
        quality_distribution: Distribution of quality grades [Added in [007]]
        bad_elements: List of bad element IDs
    """
    num_elements: int = 0
    num_bad_elements: int = 0
    jacobian: Dict = field(default_factory=dict)
    aspect_ratio: Dict = field(default_factory=dict)
    skewness: Dict = field(default_factory=dict)
    warpage: Dict = field(default_factory=dict)
    element_size: Dict = field(default_factory=dict)
    angles: Dict = field(default_factory=dict)  # Added for [007]
    edge_length_ratio: Dict = field(default_factory=dict)  # Added for [007]
    quality_distribution: Dict = field(default_factory=dict)  # Added for [007]
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
        ])

        # Add angle information if available (added in [007])
        if self.angles:
            lines.extend([
                f"",
                f"Angles:",
                f"  Min: {self.angles.get('min', 0):.2f}°",
                f"  Max: {self.angles.get('max', 0):.2f}°",
                f"  Mean: {self.angles.get('mean', 0):.2f}°",
            ])

        # Add edge length ratio if available (added in [007])
        if self.edge_length_ratio:
            lines.extend([
                f"",
                f"Edge Length Ratio:",
                f"  Min: {self.edge_length_ratio.get('min', 0):.3f}",
                f"  Max: {self.edge_length_ratio.get('max', 0):.3f}",
                f"  Mean: {self.edge_length_ratio.get('mean', 0):.3f}",
            ])

        # Add quality distribution if available (added in [007])
        if self.quality_distribution:
            lines.extend([
                f"",
                f"Quality Distribution:",
                f"  Excellent: {self.quality_distribution.get('Excellent', 0)}",
                f"  Good: {self.quality_distribution.get('Good', 0)}",
                f"  Fair: {self.quality_distribution.get('Fair', 0)}",
                f"  Poor: {self.quality_distribution.get('Poor', 0)}",
                f"  Bad: {self.quality_distribution.get('Bad', 0)}",
            ])

        lines.extend([
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

        # Check angles (added in [007])
        report.angles = self._check_angles(mesh)

        # Check edge length ratio (added in [007])
        report.edge_length_ratio = self._check_edge_length_ratio(mesh)

        # Identify bad elements
        report.bad_elements = self._identify_bad_elements(mesh, report)
        report.num_bad_elements = len(report.bad_elements)

        # Get quality distribution (added in [007])
        report.quality_distribution = self.get_quality_distribution(mesh)

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
        elif elem.type == ElementType.TET10:
            return self._jacobian_tet10(coords)
        elif elem.type == ElementType.HEX8:
            return self._jacobian_hex8(coords)
        elif elem.type == ElementType.HEX20:
            return self._jacobian_hex20(coords)
        elif elem.type == ElementType.HEX27:
            return self._jacobian_hex27(coords)
        elif elem.type == ElementType.PRISM6:
            return self._jacobian_prism6(coords)
        elif elem.type == ElementType.PYRAMID5:
            return self._jacobian_pyramid5(coords)
        else:
            # Default: compute volume as proxy for Jacobian
            self.logger.warning(f"Jacobian not implemented for {elem.type.code}, using volume")
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

    def _jacobian_tet10(self, coords: np.ndarray) -> float:
        """Compute minimum Jacobian for 10-node tetrahedron"""
        from koomesh.meshing.shape_functions import tet10_shape_derivatives

        min_jac = float('inf')

        # Check at corner nodes and mid-side nodes
        # Natural coordinates for sampling points
        sampling_points = [
            [0.0, 0.0, 0.0],  # Node 0
            [1.0, 0.0, 0.0],  # Node 1
            [0.0, 1.0, 0.0],  # Node 2
            [0.0, 0.0, 1.0],  # Node 3
            [0.5, 0.0, 0.0],  # Edge 0-1
            [0.5, 0.5, 0.0],  # Edge 1-2
            [0.0, 0.5, 0.0],  # Edge 2-0
            [0.0, 0.0, 0.5],  # Edge 0-3
            [0.5, 0.0, 0.5],  # Edge 1-3
            [0.0, 0.5, 0.5],  # Edge 2-3
            [0.25, 0.25, 0.25],  # Center
        ]

        for xi, eta, zeta in sampling_points:
            dN_dxi = tet10_shape_derivatives(xi, eta, zeta)
            J = dN_dxi @ coords
            det_J = np.linalg.det(J)
            min_jac = min(min_jac, det_J)

        return min_jac

    def _jacobian_hex20(self, coords: np.ndarray) -> float:
        """Compute minimum Jacobian for 20-node hexahedron"""
        from koomesh.meshing.shape_functions import hex20_shape_derivatives

        min_jac = float('inf')

        # Check at corner nodes and some mid-side points
        # Natural coordinates of corner nodes
        sampling_points = [
            [-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
            [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1],
            # Mid-side points
            [0, -1, -1], [1, 0, -1], [0, 1, -1], [-1, 0, -1],
            [0, -1, 1], [1, 0, 1], [0, 1, 1], [-1, 0, 1],
            [-1, -1, 0], [1, -1, 0], [1, 1, 0], [-1, 1, 0],
            [0, 0, 0],  # Center
        ]

        for xi, eta, zeta in sampling_points:
            dN_dxi = hex20_shape_derivatives(xi, eta, zeta)
            J = dN_dxi @ coords
            det_J = np.linalg.det(J)
            min_jac = min(min_jac, det_J)

        return min_jac

    def _jacobian_hex27(self, coords: np.ndarray) -> float:
        """Compute minimum Jacobian for 27-node hexahedron"""
        from koomesh.meshing.shape_functions import hex27_shape_derivatives

        min_jac = float('inf')

        # Check at corner nodes, mid-side, face centers, and volume center
        sampling_points = [
            # Corner nodes
            [-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
            [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1],
            # Mid-side edge nodes
            [0, -1, -1], [1, 0, -1], [0, 1, -1], [-1, 0, -1],
            [0, -1, 1], [1, 0, 1], [0, 1, 1], [-1, 0, 1],
            [-1, -1, 0], [1, -1, 0], [1, 1, 0], [-1, 1, 0],
            # Face center nodes
            [0, 0, -1], [0, 0, 1], [0, -1, 0], [0, 1, 0], [-1, 0, 0], [1, 0, 0],
            # Volume center
            [0, 0, 0],
        ]

        for xi, eta, zeta in sampling_points:
            dN_dxi = hex27_shape_derivatives(xi, eta, zeta)
            J = dN_dxi @ coords
            det_J = np.linalg.det(J)
            min_jac = min(min_jac, det_J)

        return min_jac

    def _jacobian_prism6(self, coords: np.ndarray) -> float:
        """Compute minimum Jacobian for 6-node prism"""
        from koomesh.meshing.shape_functions import prism6_shape_derivatives

        min_jac = float('inf')

        # Check at corner nodes and mid-points
        sampling_points = [
            # Bottom triangle corners
            [0.0, 0.0, -1.0], [1.0, 0.0, -1.0], [0.0, 1.0, -1.0],
            # Top triangle corners
            [0.0, 0.0, 1.0], [1.0, 0.0, 1.0], [0.0, 1.0, 1.0],
            # Mid-height points
            [0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0],
            # Center points
            [0.33, 0.33, -1.0], [0.33, 0.33, 0.0], [0.33, 0.33, 1.0],
        ]

        for xi, eta, zeta in sampling_points:
            dN_dxi = prism6_shape_derivatives(xi, eta, zeta)
            J = dN_dxi @ coords
            det_J = np.linalg.det(J)
            min_jac = min(min_jac, det_J)

        return min_jac

    def _jacobian_pyramid5(self, coords: np.ndarray) -> float:
        """Compute minimum Jacobian for 5-node pyramid"""
        from koomesh.meshing.shape_functions import pyramid5_shape_derivatives

        min_jac = float('inf')

        # Check at base corners and mid-height points
        # Note: Avoid apex (zeta=1) where derivatives are undefined
        sampling_points = [
            # Base corners
            [-1.0, -1.0, 0.0], [1.0, -1.0, 0.0], [1.0, 1.0, 0.0], [-1.0, 1.0, 0.0],
            # Mid-height points
            [-0.5, -0.5, 0.5], [0.5, -0.5, 0.5], [0.5, 0.5, 0.5], [-0.5, 0.5, 0.5],
            # Base center
            [0.0, 0.0, 0.0],
            # Mid-height center
            [0.0, 0.0, 0.5],
            # Near apex (but not at apex to avoid singularity)
            [0.0, 0.0, 0.9],
        ]

        for xi, eta, zeta in sampling_points:
            dN_dxi = pyramid5_shape_derivatives(xi, eta, zeta)
            J = dN_dxi @ coords
            det_J = np.linalg.det(J)
            min_jac = min(min_jac, det_J)

        return min_jac

    # ========================================================================
    # Extended Quality Metrics (Added for [007])
    # ========================================================================

    def _check_angles(self, mesh: MeshData) -> Dict:
        """
        Check element angles

        Returns:
            Dictionary with angle statistics (in degrees)
        """
        all_angles = []

        for elem in mesh.elements.values():
            coords = np.array([
                mesh.get_node(nid).coordinates() for nid in elem.nodes
            ])

            min_ang, max_ang = self._compute_angles(elem.type, coords)
            all_angles.append(min_ang)
            all_angles.append(max_ang)

        all_angles = np.array(all_angles)

        return {
            'min': float(np.min(all_angles)),
            'max': float(np.max(all_angles)),
            'mean': float(np.mean(all_angles)),
            'median': float(np.median(all_angles)),
        }

    def _compute_angles(self, elem_type: ElementType, coords: np.ndarray) -> tuple:
        """
        Compute minimum and maximum angles in element

        Returns:
            Tuple of (min_angle, max_angle) in degrees
        """
        angles = []
        num_nodes = len(coords)

        if num_nodes == 8:  # HEX8
            # Define faces and compute angles at corners
            # Each corner has 3 edges meeting
            corner_edges = [
                [(0, 1), (0, 3), (0, 4)],  # Node 0
                [(1, 0), (1, 2), (1, 5)],  # Node 1
                [(2, 1), (2, 3), (2, 6)],  # Node 2
                [(3, 0), (3, 2), (3, 7)],  # Node 3
                [(4, 0), (4, 5), (4, 7)],  # Node 4
                [(5, 1), (5, 4), (5, 6)],  # Node 5
                [(6, 2), (6, 5), (6, 7)],  # Node 6
                [(7, 3), (7, 4), (7, 6)],  # Node 7
            ]

            for node_idx, edge_list in enumerate(corner_edges):
                # Compute all pairwise angles between edges at this node
                for i in range(len(edge_list)):
                    for j in range(i + 1, len(edge_list)):
                        from_node1, to_node1 = edge_list[i]
                        from_node2, to_node2 = edge_list[j]

                        v1 = coords[to_node1] - coords[from_node1]
                        v2 = coords[to_node2] - coords[from_node2]

                        v1_norm = np.linalg.norm(v1)
                        v2_norm = np.linalg.norm(v2)

                        if v1_norm > 1e-10 and v2_norm > 1e-10:
                            cos_angle = np.dot(v1, v2) / (v1_norm * v2_norm)
                            cos_angle = np.clip(cos_angle, -1.0, 1.0)
                            angle = np.arccos(cos_angle) * 180 / np.pi
                            angles.append(angle)

        elif num_nodes == 6:  # PRISM6
            # Triangular faces have 60° angles, quad faces have 90° angles
            # Check angles at each vertex
            faces = [
                [0, 1, 2],  # Bottom triangle
                [3, 4, 5],  # Top triangle
                [0, 1, 4, 3],  # Quad face
                [1, 2, 5, 4],  # Quad face
                [2, 0, 3, 5],  # Quad face
            ]

            for face in faces:
                n = len(face)
                for i in range(n):
                    v1 = coords[face[(i-1) % n]] - coords[face[i]]
                    v2 = coords[face[(i+1) % n]] - coords[face[i]]

                    v1_norm = np.linalg.norm(v1)
                    v2_norm = np.linalg.norm(v2)

                    if v1_norm > 1e-10 and v2_norm > 1e-10:
                        cos_angle = np.dot(v1, v2) / (v1_norm * v2_norm)
                        cos_angle = np.clip(cos_angle, -1.0, 1.0)
                        angle = np.arccos(cos_angle) * 180 / np.pi
                        angles.append(angle)

        elif num_nodes == 5:  # PYRAMID5
            # Check base angles
            for i in range(4):
                v1 = coords[(i-1) % 4] - coords[i]
                v2 = coords[(i+1) % 4] - coords[i]

                v1_norm = np.linalg.norm(v1)
                v2_norm = np.linalg.norm(v2)

                if v1_norm > 1e-10 and v2_norm > 1e-10:
                    cos_angle = np.dot(v1, v2) / (v1_norm * v2_norm)
                    cos_angle = np.clip(cos_angle, -1.0, 1.0)
                    angle = np.arccos(cos_angle) * 180 / np.pi
                    angles.append(angle)

            # Check apex angles
            for i in range(4):
                v1 = coords[i] - coords[4]
                v2 = coords[(i+1) % 4] - coords[4]

                v1_norm = np.linalg.norm(v1)
                v2_norm = np.linalg.norm(v2)

                if v1_norm > 1e-10 and v2_norm > 1e-10:
                    cos_angle = np.dot(v1, v2) / (v1_norm * v2_norm)
                    cos_angle = np.clip(cos_angle, -1.0, 1.0)
                    angle = np.arccos(cos_angle) * 180 / np.pi
                    angles.append(angle)

        elif elem_type.is_tet():
            # Tetrahedral elements - check all edges
            edges = [
                (0, 1), (0, 2), (0, 3),
                (1, 2), (1, 3), (2, 3)
            ]

            for i, (e1_start, e1_end) in enumerate(edges):
                v1 = coords[e1_end] - coords[e1_start]
                v1_norm = np.linalg.norm(v1)

                if v1_norm > 1e-10:
                    for j, (e2_start, e2_end) in enumerate(edges):
                        if i < j and (e1_start == e2_start or e1_start == e2_end or
                                     e1_end == e2_start or e1_end == e2_end):
                            v2 = coords[e2_end] - coords[e2_start]
                            v2_norm = np.linalg.norm(v2)

                            if v2_norm > 1e-10:
                                cos_angle = np.dot(v1, v2) / (v1_norm * v2_norm)
                                cos_angle = np.clip(cos_angle, -1.0, 1.0)
                                angle = np.arccos(abs(cos_angle)) * 180 / np.pi
                                angles.append(angle)

        if len(angles) == 0:
            return (90.0, 90.0)

        return (float(np.min(angles)), float(np.max(angles)))

    def _check_edge_length_ratio(self, mesh: MeshData) -> Dict:
        """
        Check edge length ratios

        Returns:
            Dictionary with edge length ratio statistics
        """
        ratios = []

        for elem in mesh.elements.values():
            coords = np.array([
                mesh.get_node(nid).coordinates() for nid in elem.nodes
            ])

            ratio = self._compute_edge_length_ratio(coords)
            ratios.append(ratio)

        ratios = np.array(ratios)

        return {
            'min': float(np.min(ratios)),
            'max': float(np.max(ratios)),
            'mean': float(np.mean(ratios)),
            'median': float(np.median(ratios)),
            'bad_elements': int(np.sum(ratios > 10))  # Ratio > 10 is bad
        }

    def _compute_edge_length_ratio(self, coords: np.ndarray) -> float:
        """
        Compute edge length ratio (max/min) for element edges only

        Returns:
            Edge length ratio
        """
        edge_lengths = []
        num_nodes = len(coords)

        # Define element edges based on element type
        if num_nodes == 8:  # HEX8
            # 12 edges of hex element
            edges = [
                (0, 1), (1, 2), (2, 3), (3, 0),  # Bottom face
                (4, 5), (5, 6), (6, 7), (7, 4),  # Top face
                (0, 4), (1, 5), (2, 6), (3, 7),  # Vertical edges
            ]
        elif num_nodes == 4:  # TET4
            # 6 edges of tet
            edges = [
                (0, 1), (0, 2), (0, 3),
                (1, 2), (1, 3), (2, 3)
            ]
        elif num_nodes == 6:  # PRISM6
            # 9 edges of prism
            edges = [
                (0, 1), (1, 2), (2, 0),  # Bottom triangle
                (3, 4), (4, 5), (5, 3),  # Top triangle
                (0, 3), (1, 4), (2, 5),  # Vertical edges
            ]
        elif num_nodes == 5:  # PYRAMID5
            # 8 edges of pyramid
            edges = [
                (0, 1), (1, 2), (2, 3), (3, 0),  # Base
                (0, 4), (1, 4), (2, 4), (3, 4),  # Apex edges
            ]
        else:
            # Default: compute all pairwise distances
            edges = [(i, j) for i in range(num_nodes) for j in range(i+1, num_nodes)]

        # Compute edge lengths
        for i, j in edges:
            if i < num_nodes and j < num_nodes:
                length = np.linalg.norm(coords[j] - coords[i])
                if length > 1e-10:
                    edge_lengths.append(length)

        if len(edge_lengths) == 0:
            return 1.0

        min_length = min(edge_lengths)
        max_length = max(edge_lengths)

        if min_length > 1e-10:
            return max_length / min_length
        else:
            return 1000.0  # Very bad

    def grade_element(self, elem_or_id, mesh: MeshData) -> str:
        """
        Grade element quality

        Args:
            elem_or_id: Element object or element ID (int)
            mesh: Mesh data

        Returns:
            Quality grade: 'Excellent', 'Good', 'Fair', 'Poor', or 'Bad'
        """
        # Accept either Element object or element ID
        if isinstance(elem_or_id, int):
            elem = mesh.get_element(elem_or_id)
        else:
            elem = elem_or_id

        coords = np.array([
            mesh.get_node(nid).coordinates() for nid in elem.nodes
        ])

        # Compute metrics
        jac = self._compute_jacobian(elem, mesh)
        aspect = self._compute_aspect_ratio(elem, mesh)
        skew = self._compute_skewness(elem, mesh)

        # Grading criteria
        # Note: Jacobian threshold is element-size dependent
        # For normalized grading, we use aspect ratio and skewness as primary indicators
        if jac <= 0:
            return 'Bad'  # Inverted or degenerate element
        elif aspect > 50 or skew > 0.95:
            return 'Bad'
        elif aspect > 20 or skew > 0.85:
            return 'Poor'
        elif aspect > 10 or skew > 0.7:
            return 'Fair'
        elif aspect > 3 or skew > 0.4:
            return 'Good'
        else:
            return 'Excellent'

    def get_element_report(self, elem_or_id, mesh: MeshData) -> Dict:
        """
        Get detailed quality report for a single element

        Args:
            elem_or_id: Element object or element ID (int)
            mesh: Mesh data

        Returns:
            Dictionary with element quality metrics
        """
        # Accept either Element object or element ID
        if isinstance(elem_or_id, int):
            elem = mesh.get_element(elem_or_id)
            elem_id = elem_or_id
        else:
            elem = elem_or_id
            elem_id = elem.id

        coords = np.array([
            mesh.get_node(nid).coordinates() for nid in elem.nodes
        ])

        # Compute angles
        min_angle, max_angle = self._compute_angles(elem.type, coords)

        report = {
            'element_id': elem_id,
            'element_type': elem.type.code,
            'num_nodes': len(elem.nodes),
            'jacobian': self._compute_jacobian(elem, mesh),
            'aspect_ratio': self._compute_aspect_ratio(elem, mesh),
            'skewness': self._compute_skewness(elem, mesh),
            'size': self._compute_element_size(elem, mesh),
            'min_angle': min_angle,
            'max_angle': max_angle,
            'edge_length_ratio': self._compute_edge_length_ratio(coords),
            'quality_grade': self.grade_element(elem, mesh)
        }

        # Add warpage for hex elements
        if elem.type.is_hex():
            report['warpage'] = self._compute_warpage(elem, mesh)

        return report

    def get_quality_histogram(self, mesh: MeshData, metric: str = 'jacobian',
                             bins: int = 20) -> Dict:
        """
        Get quality histogram for specified metric

        Args:
            mesh: Mesh data
            metric: Metric name ('jacobian', 'aspect_ratio', 'skewness')
            bins: Number of histogram bins

        Returns:
            Dictionary with histogram data: 'bins', 'counts', 'bin_edges'
        """
        values = []

        for elem in mesh.elements.values():
            if metric == 'jacobian':
                value = self._compute_jacobian(elem, mesh)
            elif metric == 'aspect_ratio':
                value = self._compute_aspect_ratio(elem, mesh)
            elif metric == 'skewness':
                value = self._compute_skewness(elem, mesh)
            elif metric == 'size':
                value = self._compute_element_size(elem, mesh)
            else:
                raise ValueError(f"Unknown metric: {metric}")

            values.append(value)

        counts, bin_edges = np.histogram(values, bins=bins)

        # Create bin labels
        bin_labels = []
        for i in range(len(bin_edges) - 1):
            label = f"{bin_edges[i]:.3f}-{bin_edges[i+1]:.3f}"
            bin_labels.append(label)

        return {
            'bins': bin_labels,
            'counts': counts.tolist(),
            'bin_edges': bin_edges.tolist()
        }

    def get_quality_distribution(self, mesh: MeshData) -> Dict:
        """
        Get distribution of element quality grades

        Returns:
            Dictionary with count of each grade
        """
        distribution = {
            'Excellent': 0,
            'Good': 0,
            'Fair': 0,
            'Poor': 0,
            'Bad': 0
        }

        for elem_id in mesh.elements.keys():
            grade = self.grade_element(elem_id, mesh)
            distribution[grade] += 1

        return distribution

    def export_to_csv(self, mesh: MeshData, filepath: str):
        """
        Export element quality metrics to CSV file

        Args:
            mesh: Mesh data
            filepath: Output CSV file path
        """
        import csv

        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)

            # Header
            writer.writerow([
                'element_id', 'element_type', 'jacobian', 'aspect_ratio',
                'skewness', 'size', 'min_angle', 'max_angle',
                'edge_length_ratio', 'quality_grade'
            ])

            # Data rows
            for elem_id in mesh.elements.keys():
                report = self.get_element_report(elem_id, mesh)
                writer.writerow([
                    report['element_id'],
                    report['element_type'],
                    f"{report['jacobian']:.6f}",
                    f"{report['aspect_ratio']:.3f}",
                    f"{report['skewness']:.3f}",
                    f"{report['size']:.6f}",
                    f"{report.get('min_angle', 0):.2f}",
                    f"{report.get('max_angle', 0):.2f}",
                    f"{report.get('edge_length_ratio', 0):.3f}",
                    report['quality_grade']
                ])

        self.logger.info(f"Exported quality metrics to {filepath}")

    def export_to_json(self, mesh: MeshData, filepath: str):
        """
        Export element quality metrics to JSON file

        Args:
            mesh: Mesh data
            filepath: Output JSON file path
        """
        import json

        # Get quality report and distribution
        quality_report = self.check_mesh(mesh)
        distribution = self.get_quality_distribution(mesh)

        data = {
            'summary': {
                'num_elements': mesh.num_elements(),
                'num_nodes': mesh.num_nodes(),
                'num_bad_elements': quality_report.num_bad_elements,
                'element_type': mesh.element_type.code,
                'quality_distribution': distribution
            },
            'elements': []
        }

        for elem_id in mesh.elements.keys():
            elem = mesh.get_element(elem_id)
            elem_report = self.get_element_report(elem_id, mesh)

            # Restructure for JSON (separate metrics)
            element_data = {
                'element_id': elem_report['element_id'],
                'quality_grade': elem_report['quality_grade'],
                'metrics': {
                    'jacobian': elem_report['jacobian'],
                    'aspect_ratio': elem_report['aspect_ratio'],
                    'skewness': elem_report['skewness'],
                    'size': elem_report['size'],
                    'min_angle': elem_report['min_angle'],
                    'max_angle': elem_report['max_angle'],
                    'edge_length_ratio': elem_report['edge_length_ratio']
                }
            }

            if 'warpage' in elem_report:
                element_data['metrics']['warpage'] = elem_report['warpage']

            data['elements'].append(element_data)

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        self.logger.info(f"Exported quality metrics to {filepath}")

    def get_detailed_report(self, mesh: MeshData) -> str:
        """
        Get comprehensive quality report with all metrics

        Returns:
            Detailed report string
        """
        report = self.check_mesh(mesh)
        distribution = self.get_quality_distribution(mesh)

        lines = [
            "="*70,
            "COMPREHENSIVE MESH QUALITY REPORT",
            "="*70,
            "",
            "Mesh Quality Report",
            "-"*70,
            f"Mesh Information:",
            f"  Total Elements: {mesh.num_elements()}",
            f"  Total Nodes: {mesh.num_nodes()}",
            f"  Element Type: {mesh.element_type.code}",
            "",
            "Overall Statistics",
            "-"*70,
            report.summary(),
            "",
            "Quality Distribution",
            "-"*70,
            f"  Excellent: {distribution['Excellent']:6d} ({distribution['Excellent']/mesh.num_elements()*100:5.1f}%)",
            f"  Good:      {distribution['Good']:6d} ({distribution['Good']/mesh.num_elements()*100:5.1f}%)",
            f"  Fair:      {distribution['Fair']:6d} ({distribution['Fair']/mesh.num_elements()*100:5.1f}%)",
            f"  Poor:      {distribution['Poor']:6d} ({distribution['Poor']/mesh.num_elements()*100:5.1f}%)",
            f"  Bad:       {distribution['Bad']:6d} ({distribution['Bad']/mesh.num_elements()*100:5.1f}%)",
            "",
            "="*70,
        ]

        # Add worst elements
        if report.bad_elements:
            lines.extend([
                "WORST ELEMENTS (First 10):",
                "="*70,
            ])

            for elem_id in report.bad_elements[:10]:
                elem_report = self.get_element_report(elem_id, mesh)
                lines.append(
                    f"  Element {elem_id}: "
                    f"Jacobian={elem_report['jacobian']:.4f}, "
                    f"Aspect={elem_report['aspect_ratio']:.2f}, "
                    f"Grade={elem_report['quality_grade']}"
                )

            lines.append("")

        # Add element details section
        lines.extend([
            "="*70,
            "Element Details",
            "="*70,
        ])

        for elem_id in sorted(mesh.elements.keys()):
            elem_report = self.get_element_report(elem_id, mesh)
            lines.extend([
                f"",
                f"Element {elem_id}:",
                f"  Quality Grade: {elem_report['quality_grade']}",
                f"  Jacobian:      {elem_report['jacobian']:.6f}",
                f"  Aspect Ratio:  {elem_report['aspect_ratio']:.3f}",
                f"  Skewness:      {elem_report['skewness']:.3f}",
                f"  Min Angle:     {elem_report['min_angle']:.2f}°",
                f"  Max Angle:     {elem_report['max_angle']:.2f}°",
            ])

        lines.append("")
        lines.append("="*70)

        return "\n".join(lines)
