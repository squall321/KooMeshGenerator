"""
Mesh Quality Metrics
====================

Compute and analyze mesh quality metrics for FEA elements.

Metrics include:
- Jacobian (normalized)
- Aspect ratio
- Skewness
- Warping
- Element size
- Edge length ratio

Author: KooMeshGenerator Team
"""

import numpy as np
import logging
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


logger = logging.getLogger(__name__)


class QualityMetric(Enum):
    """Quality metric types"""
    JACOBIAN = "jacobian"
    ASPECT_RATIO = "aspect_ratio"
    SKEWNESS = "skewness"
    WARPING = "warping"
    EDGE_RATIO = "edge_ratio"
    VOLUME = "volume"
    ORTHOGONALITY = "orthogonality"


@dataclass
class ElementQuality:
    """Quality metrics for a single element"""
    element_id: int
    element_type: str  # hex8, tet4, shell4, etc.

    # Quality metrics (0-1, where 1 is best)
    jacobian: float = 0.0
    aspect_ratio_quality: float = 0.0  # Inverse of aspect ratio
    skewness_quality: float = 0.0  # 1 - skewness
    warping_quality: float = 1.0
    edge_ratio_quality: float = 0.0

    # Raw values
    min_jacobian: float = 0.0
    max_aspect_ratio: float = 1.0
    max_skewness: float = 0.0
    max_warping: float = 0.0
    max_edge_ratio: float = 1.0

    # Overall quality
    overall_quality: float = 0.0

    # Flags
    is_acceptable: bool = True
    needs_refinement: bool = False

    def compute_overall_quality(self, weights: Optional[Dict[str, float]] = None) -> float:
        """
        Compute weighted overall quality

        Args:
            weights: Weights for each metric (default: equal weights)

        Returns:
            Overall quality (0-1)
        """
        if weights is None:
            weights = {
                'jacobian': 0.3,
                'aspect_ratio': 0.25,
                'skewness': 0.25,
                'warping': 0.1,
                'edge_ratio': 0.1,
            }

        self.overall_quality = (
            weights.get('jacobian', 0.3) * self.jacobian +
            weights.get('aspect_ratio', 0.25) * self.aspect_ratio_quality +
            weights.get('skewness', 0.25) * self.skewness_quality +
            weights.get('warping', 0.1) * self.warping_quality +
            weights.get('edge_ratio', 0.1) * self.edge_ratio_quality
        )

        return self.overall_quality


@dataclass
class MeshQualityMetrics:
    """Quality metrics for entire mesh"""
    total_elements: int = 0

    # Jacobian statistics
    min_jacobian: float = 1.0
    max_jacobian: float = 1.0
    avg_jacobian: float = 1.0
    std_jacobian: float = 0.0

    # Aspect ratio statistics
    min_aspect_ratio: float = 1.0
    max_aspect_ratio: float = 1.0
    avg_aspect_ratio: float = 1.0
    std_aspect_ratio: float = 0.0

    # Skewness statistics
    min_skewness: float = 0.0
    max_skewness: float = 0.0
    avg_skewness: float = 0.0
    std_skewness: float = 0.0

    # Overall quality
    avg_overall_quality: float = 0.0

    # Element counts by quality
    excellent_count: int = 0  # Quality > 0.8
    good_count: int = 0  # Quality 0.6-0.8
    fair_count: int = 0  # Quality 0.4-0.6
    poor_count: int = 0  # Quality 0.2-0.4
    bad_count: int = 0  # Quality < 0.2

    # Elements needing refinement
    elements_to_refine: List[int] = field(default_factory=list)

    def get_quality_distribution(self) -> Dict[str, float]:
        """Get percentage distribution of quality levels"""
        if self.total_elements == 0:
            return {}

        return {
            'excellent': 100.0 * self.excellent_count / self.total_elements,
            'good': 100.0 * self.good_count / self.total_elements,
            'fair': 100.0 * self.fair_count / self.total_elements,
            'poor': 100.0 * self.poor_count / self.total_elements,
            'bad': 100.0 * self.bad_count / self.total_elements,
        }

    def get_summary(self) -> str:
        """Get formatted summary"""
        dist = self.get_quality_distribution()

        lines = [
            "=" * 70,
            "MESH QUALITY SUMMARY",
            "=" * 70,
            f"Total elements: {self.total_elements:,}",
            "",
            "Jacobian:",
            f"  Min: {self.min_jacobian:.4f}",
            f"  Max: {self.max_jacobian:.4f}",
            f"  Avg: {self.avg_jacobian:.4f} ± {self.std_jacobian:.4f}",
            "",
            "Aspect Ratio:",
            f"  Min: {self.min_aspect_ratio:.2f}",
            f"  Max: {self.max_aspect_ratio:.2f}",
            f"  Avg: {self.avg_aspect_ratio:.2f} ± {self.std_aspect_ratio:.2f}",
            "",
            "Skewness:",
            f"  Min: {self.min_skewness:.4f}",
            f"  Max: {self.max_skewness:.4f}",
            f"  Avg: {self.avg_skewness:.4f} ± {self.std_skewness:.4f}",
            "",
            f"Average Overall Quality: {self.avg_overall_quality:.4f}",
            "",
            "Quality Distribution:",
            f"  Excellent (>0.8): {dist.get('excellent', 0):.1f}% ({self.excellent_count:,})",
            f"  Good (0.6-0.8):  {dist.get('good', 0):.1f}% ({self.good_count:,})",
            f"  Fair (0.4-0.6):  {dist.get('fair', 0):.1f}% ({self.fair_count:,})",
            f"  Poor (0.2-0.4):  {dist.get('poor', 0):.1f}% ({self.poor_count:,})",
            f"  Bad  (<0.2):     {dist.get('bad', 0):.1f}% ({self.bad_count:,})",
            "",
            f"Elements needing refinement: {len(self.elements_to_refine):,}",
            "=" * 70,
        ]

        return "\n".join(lines)


class QualityAnalyzer:
    """
    Analyze mesh quality

    Example:
        >>> analyzer = QualityAnalyzer()
        >>> element_qualities = analyzer.analyze_mesh(nodes, elements)
        >>> metrics = analyzer.compute_mesh_metrics(element_qualities)
        >>> print(metrics.get_summary())
    """

    def __init__(self, quality_thresholds: Optional[Dict[str, float]] = None):
        """
        Initialize quality analyzer

        Args:
            quality_thresholds: Thresholds for quality metrics
        """
        self.logger = logging.getLogger(__name__)

        # Default thresholds
        if quality_thresholds is None:
            quality_thresholds = {
                'min_jacobian': 0.3,
                'max_aspect_ratio': 10.0,
                'max_skewness': 0.7,
                'max_warping': 15.0,  # degrees
                'overall_quality': 0.4,
            }

        self.quality_thresholds = quality_thresholds

    def analyze_element(self, element_id: int, element_type: str,
                        nodes: np.ndarray) -> ElementQuality:
        """
        Analyze quality of single element

        Args:
            element_id: Element ID
            element_type: Element type (hex8, tet4, etc.)
            nodes: Node coordinates (N x 3)

        Returns:
            Element quality metrics
        """
        quality = ElementQuality(element_id=element_id, element_type=element_type)

        # Compute metrics based on element type
        if element_type in ['hex8', 'hex20']:
            quality = self._analyze_hex(quality, nodes)
        elif element_type in ['tet4', 'tet10']:
            quality = self._analyze_tet(quality, nodes)
        elif element_type in ['shell3', 'shell4']:
            quality = self._analyze_shell(quality, nodes)
        else:
            self.logger.warning(f"Unsupported element type: {element_type}")

        # Compute overall quality
        quality.compute_overall_quality()

        # Check acceptability
        quality.is_acceptable = self._check_acceptability(quality)
        quality.needs_refinement = not quality.is_acceptable

        return quality

    def _analyze_hex(self, quality: ElementQuality, nodes: np.ndarray) -> ElementQuality:
        """Analyze hexahedral element"""
        # Compute Jacobian at center
        quality.min_jacobian = compute_jacobian_hex(nodes)
        quality.jacobian = max(0.0, quality.min_jacobian)

        # Compute aspect ratio
        quality.max_aspect_ratio = compute_aspect_ratio_hex(nodes)
        quality.aspect_ratio_quality = 1.0 / max(1.0, quality.max_aspect_ratio / 10.0)

        # Compute skewness
        quality.max_skewness = compute_skewness_hex(nodes)
        quality.skewness_quality = 1.0 - quality.max_skewness

        # Compute warping
        quality.max_warping = compute_warping_hex(nodes)
        quality.warping_quality = max(0.0, 1.0 - quality.max_warping / 30.0)

        # Edge ratio
        quality.max_edge_ratio = compute_edge_ratio(nodes)
        quality.edge_ratio_quality = 1.0 / max(1.0, quality.max_edge_ratio / 10.0)

        return quality

    def _analyze_tet(self, quality: ElementQuality, nodes: np.ndarray) -> ElementQuality:
        """Analyze tetrahedral element"""
        # Jacobian
        quality.min_jacobian = compute_jacobian_tet(nodes)
        quality.jacobian = max(0.0, quality.min_jacobian)

        # Aspect ratio
        quality.max_aspect_ratio = compute_aspect_ratio_tet(nodes)
        quality.aspect_ratio_quality = 1.0 / max(1.0, quality.max_aspect_ratio / 5.0)

        # Skewness
        quality.max_skewness = compute_skewness_tet(nodes)
        quality.skewness_quality = 1.0 - quality.max_skewness

        return quality

    def _analyze_shell(self, quality: ElementQuality, nodes: np.ndarray) -> ElementQuality:
        """Analyze shell element"""
        # Jacobian
        quality.min_jacobian = compute_jacobian_shell(nodes)
        quality.jacobian = max(0.0, quality.min_jacobian)

        # Aspect ratio
        quality.max_aspect_ratio = compute_aspect_ratio_shell(nodes)
        quality.aspect_ratio_quality = 1.0 / max(1.0, quality.max_aspect_ratio / 5.0)

        # Skewness
        quality.max_skewness = compute_skewness_shell(nodes)
        quality.skewness_quality = 1.0 - quality.max_skewness

        # Warping
        quality.max_warping = compute_warping_shell(nodes)
        quality.warping_quality = max(0.0, 1.0 - quality.max_warping / 20.0)

        return quality

    def _check_acceptability(self, quality: ElementQuality) -> bool:
        """Check if element quality is acceptable"""
        if quality.min_jacobian < self.quality_thresholds.get('min_jacobian', 0.3):
            return False

        if quality.max_aspect_ratio > self.quality_thresholds.get('max_aspect_ratio', 10.0):
            return False

        if quality.max_skewness > self.quality_thresholds.get('max_skewness', 0.7):
            return False

        if quality.overall_quality < self.quality_thresholds.get('overall_quality', 0.4):
            return False

        return True

    def compute_mesh_metrics(self, element_qualities: List[ElementQuality]) -> MeshQualityMetrics:
        """
        Compute mesh-level quality metrics

        Args:
            element_qualities: List of element qualities

        Returns:
            Mesh quality metrics
        """
        if not element_qualities:
            return MeshQualityMetrics()

        metrics = MeshQualityMetrics(total_elements=len(element_qualities))

        # Extract arrays
        jacobians = np.array([eq.min_jacobian for eq in element_qualities])
        aspect_ratios = np.array([eq.max_aspect_ratio for eq in element_qualities])
        skewnesses = np.array([eq.max_skewness for eq in element_qualities])
        overall_qualities = np.array([eq.overall_quality for eq in element_qualities])

        # Compute statistics
        metrics.min_jacobian = float(np.min(jacobians))
        metrics.max_jacobian = float(np.max(jacobians))
        metrics.avg_jacobian = float(np.mean(jacobians))
        metrics.std_jacobian = float(np.std(jacobians))

        metrics.min_aspect_ratio = float(np.min(aspect_ratios))
        metrics.max_aspect_ratio = float(np.max(aspect_ratios))
        metrics.avg_aspect_ratio = float(np.mean(aspect_ratios))
        metrics.std_aspect_ratio = float(np.std(aspect_ratios))

        metrics.min_skewness = float(np.min(skewnesses))
        metrics.max_skewness = float(np.max(skewnesses))
        metrics.avg_skewness = float(np.mean(skewnesses))
        metrics.std_skewness = float(np.std(skewnesses))

        metrics.avg_overall_quality = float(np.mean(overall_qualities))

        # Count quality levels
        for eq in element_qualities:
            q = eq.overall_quality
            if q > 0.8:
                metrics.excellent_count += 1
            elif q > 0.6:
                metrics.good_count += 1
            elif q > 0.4:
                metrics.fair_count += 1
            elif q > 0.2:
                metrics.poor_count += 1
            else:
                metrics.bad_count += 1

            if eq.needs_refinement:
                metrics.elements_to_refine.append(eq.element_id)

        return metrics


# Helper functions for quality computation

def compute_jacobian_hex(nodes: np.ndarray) -> float:
    """Compute minimum Jacobian for hex element"""
    # Simplified: compute at element center
    # In practice, should check at all integration points
    center = np.mean(nodes, axis=0)

    # Compute edge vectors
    v1 = nodes[1] - nodes[0]
    v2 = nodes[3] - nodes[0]
    v3 = nodes[4] - nodes[0]

    # Jacobian = det([v1, v2, v3])
    J = np.abs(np.linalg.det(np.column_stack([v1, v2, v3])))

    # Normalize by edge lengths
    L1 = np.linalg.norm(v1)
    L2 = np.linalg.norm(v2)
    L3 = np.linalg.norm(v3)

    if L1 * L2 * L3 > 1e-12:
        J_normalized = J / (L1 * L2 * L3)
    else:
        J_normalized = 0.0

    return J_normalized


def compute_jacobian_tet(nodes: np.ndarray) -> float:
    """Compute Jacobian for tet element"""
    v1 = nodes[1] - nodes[0]
    v2 = nodes[2] - nodes[0]
    v3 = nodes[3] - nodes[0]

    J = np.abs(np.linalg.det(np.column_stack([v1, v2, v3])))

    L1 = np.linalg.norm(v1)
    L2 = np.linalg.norm(v2)
    L3 = np.linalg.norm(v3)

    if L1 * L2 * L3 > 1e-12:
        J_normalized = J / (L1 * L2 * L3)
    else:
        J_normalized = 0.0

    return J_normalized


def compute_jacobian_shell(nodes: np.ndarray) -> float:
    """Compute Jacobian for shell element"""
    if len(nodes) == 3:  # Tri shell
        v1 = nodes[1] - nodes[0]
        v2 = nodes[2] - nodes[0]
        area = 0.5 * np.linalg.norm(np.cross(v1, v2))
        edge_avg = (np.linalg.norm(v1) + np.linalg.norm(v2)) / 2.0
        if edge_avg > 1e-12:
            return area / (edge_avg ** 2)
        return 0.0
    else:  # Quad shell
        return compute_jacobian_hex(nodes[:4])  # Use 2D version


def compute_aspect_ratio_hex(nodes: np.ndarray) -> float:
    """Compute aspect ratio for hex element"""
    edges = [
        np.linalg.norm(nodes[1] - nodes[0]),
        np.linalg.norm(nodes[2] - nodes[1]),
        np.linalg.norm(nodes[3] - nodes[2]),
        np.linalg.norm(nodes[0] - nodes[3]),
        np.linalg.norm(nodes[5] - nodes[4]),
        np.linalg.norm(nodes[6] - nodes[5]),
        np.linalg.norm(nodes[7] - nodes[6]),
        np.linalg.norm(nodes[4] - nodes[7]),
        np.linalg.norm(nodes[4] - nodes[0]),
        np.linalg.norm(nodes[5] - nodes[1]),
        np.linalg.norm(nodes[6] - nodes[2]),
        np.linalg.norm(nodes[7] - nodes[3]),
    ]

    max_edge = max(edges)
    min_edge = min(edges)

    if min_edge > 1e-12:
        return max_edge / min_edge
    return 1000.0  # Very large aspect ratio


def compute_aspect_ratio_tet(nodes: np.ndarray) -> float:
    """Compute aspect ratio for tet element"""
    edges = [
        np.linalg.norm(nodes[1] - nodes[0]),
        np.linalg.norm(nodes[2] - nodes[0]),
        np.linalg.norm(nodes[3] - nodes[0]),
        np.linalg.norm(nodes[2] - nodes[1]),
        np.linalg.norm(nodes[3] - nodes[1]),
        np.linalg.norm(nodes[3] - nodes[2]),
    ]

    max_edge = max(edges)
    min_edge = min(edges)

    if min_edge > 1e-12:
        return max_edge / min_edge
    return 1000.0


def compute_aspect_ratio_shell(nodes: np.ndarray) -> float:
    """Compute aspect ratio for shell element"""
    if len(nodes) == 3:
        edges = [
            np.linalg.norm(nodes[1] - nodes[0]),
            np.linalg.norm(nodes[2] - nodes[1]),
            np.linalg.norm(nodes[0] - nodes[2]),
        ]
    else:
        edges = [
            np.linalg.norm(nodes[1] - nodes[0]),
            np.linalg.norm(nodes[2] - nodes[1]),
            np.linalg.norm(nodes[3] - nodes[2]),
            np.linalg.norm(nodes[0] - nodes[3]),
        ]

    max_edge = max(edges)
    min_edge = min(edges)

    if min_edge > 1e-12:
        return max_edge / min_edge
    return 1000.0


def compute_skewness_hex(nodes: np.ndarray) -> float:
    """Compute skewness for hex element (0-1)"""
    # Simplified: check angle deviation from 90 degrees
    v1 = nodes[1] - nodes[0]
    v2 = nodes[3] - nodes[0]

    cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-12)
    angle_deg = np.degrees(np.arccos(np.clip(cos_angle, -1.0, 1.0)))

    # Skewness: deviation from 90 degrees
    skewness = abs(angle_deg - 90.0) / 90.0

    return min(skewness, 1.0)


def compute_skewness_tet(nodes: np.ndarray) -> float:
    """Compute skewness for tet element"""
    # Similar to hex but for tetrahedral angles
    v1 = nodes[1] - nodes[0]
    v2 = nodes[2] - nodes[0]

    cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-12)
    angle_deg = np.degrees(np.arccos(np.clip(cos_angle, -1.0, 1.0)))

    # Ideal tet angle is ~70.5 degrees
    skewness = abs(angle_deg - 70.5) / 70.5

    return min(skewness, 1.0)


def compute_skewness_shell(nodes: np.ndarray) -> float:
    """Compute skewness for shell element"""
    return compute_skewness_hex(nodes)


def compute_warping_hex(nodes: np.ndarray) -> float:
    """Compute warping angle for hex element (degrees)"""
    # Check planarity of faces
    # Simplified: check top face
    normal1 = np.cross(nodes[5] - nodes[4], nodes[7] - nodes[4])
    normal2 = np.cross(nodes[6] - nodes[5], nodes[7] - nodes[5])

    cos_angle = np.dot(normal1, normal2) / (np.linalg.norm(normal1) * np.linalg.norm(normal2) + 1e-12)
    angle_deg = np.degrees(np.arccos(np.clip(cos_angle, -1.0, 1.0)))

    return abs(angle_deg)


def compute_warping_shell(nodes: np.ndarray) -> float:
    """Compute warping for shell element"""
    if len(nodes) == 3:
        return 0.0  # Triangles are always planar

    # For quad, check diagonal split planarity
    normal1 = np.cross(nodes[1] - nodes[0], nodes[2] - nodes[0])
    normal2 = np.cross(nodes[3] - nodes[0], nodes[2] - nodes[0])

    cos_angle = np.dot(normal1, normal2) / (np.linalg.norm(normal1) * np.linalg.norm(normal2) + 1e-12)
    angle_deg = np.degrees(np.arccos(np.clip(cos_angle, -1.0, 1.0)))

    return abs(angle_deg)


def compute_edge_ratio(nodes: np.ndarray) -> float:
    """Compute edge length ratio"""
    edges = []
    n = len(nodes)
    for i in range(n):
        for j in range(i + 1, n):
            edges.append(np.linalg.norm(nodes[j] - nodes[i]))

    if edges:
        return max(edges) / (min(edges) + 1e-12)
    return 1.0


# Module-level convenience functions
def compute_jacobian(nodes: np.ndarray, element_type: str) -> float:
    """Compute Jacobian for any element type"""
    if element_type in ['hex8', 'hex20']:
        return compute_jacobian_hex(nodes)
    elif element_type in ['tet4', 'tet10']:
        return compute_jacobian_tet(nodes)
    elif element_type in ['shell3', 'shell4']:
        return compute_jacobian_shell(nodes)
    return 0.0


def compute_aspect_ratio(nodes: np.ndarray, element_type: str) -> float:
    """Compute aspect ratio for any element type"""
    if element_type in ['hex8', 'hex20']:
        return compute_aspect_ratio_hex(nodes)
    elif element_type in ['tet4', 'tet10']:
        return compute_aspect_ratio_tet(nodes)
    elif element_type in ['shell3', 'shell4']:
        return compute_aspect_ratio_shell(nodes)
    return 1.0


def compute_skewness(nodes: np.ndarray, element_type: str) -> float:
    """Compute skewness for any element type"""
    if element_type in ['hex8', 'hex20']:
        return compute_skewness_hex(nodes)
    elif element_type in ['tet4', 'tet10']:
        return compute_skewness_tet(nodes)
    elif element_type in ['shell3', 'shell4']:
        return compute_skewness_shell(nodes)
    return 0.0
