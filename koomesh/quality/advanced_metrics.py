"""
Advanced Mesh Quality Metrics
==============================

Extended quality metrics: Jacobian, Skewness, Aspect Ratio, Warping, etc.

Author: KooMeshGenerator Team
"""

import numpy as np
from typing import Dict, List, Tuple
from koomesh.meshing.mesh_data import MeshData, ElementType


class AdvancedQualityMetrics:
    """Advanced mesh quality metrics calculator"""

    def __init__(self, mesh: MeshData):
        self.mesh = mesh

    def compute_jacobian_ratio(self, element_id: int) -> float:
        """
        Compute Jacobian ratio (min/max determinant)

        Returns:
            Jacobian ratio (0-1, 1 is perfect)
        """
        elem = self.mesh.elements[element_id]
        if elem.type not in [ElementType.HEX8, ElementType.TET4]:
            return 1.0

        nodes = [self.mesh.nodes[nid] for nid in elem.nodes]
        coords = np.array([[n.x, n.y, n.z] for n in nodes])

        if elem.type == ElementType.TET4:
            # Single Jacobian for tet
            v1 = coords[1] - coords[0]
            v2 = coords[2] - coords[0]
            v3 = coords[3] - coords[0]
            J = np.array([v1, v2, v3]).T
            det = np.linalg.det(J)
            return 1.0 if det > 0 else 0.0

        elif elem.type == ElementType.HEX8:
            # Sample at element corners
            dets = []
            for i in range(8):
                # Simplified: use edge vectors
                v1 = coords[(i+1) % 8] - coords[i]
                v2 = coords[(i+2) % 8] - coords[i]
                v3 = coords[(i+4) % 8] - coords[i]
                J = np.array([v1, v2, v3]).T
                det = np.linalg.det(J)
                if abs(det) > 1e-10:
                    dets.append(det)

            if not dets:
                return 0.0

            min_det = min(dets)
            max_det = max(dets)

            if max_det <= 0:
                return 0.0

            return min_det / max_det if min_det > 0 else 0.0

        return 1.0

    def compute_skewness(self, element_id: int) -> float:
        """
        Compute element skewness

        Returns:
            Skewness (0-1, 0 is perfect)
        """
        elem = self.mesh.elements[element_id]
        nodes = [self.mesh.nodes[nid] for nid in elem.nodes]
        coords = np.array([[n.x, n.y, n.z] for n in nodes])

        if elem.type == ElementType.TET4:
            # Measure deviation from equilateral
            edges = []
            for i in range(4):
                for j in range(i+1, 4):
                    edge_len = np.linalg.norm(coords[i] - coords[j])
                    edges.append(edge_len)

            if not edges or max(edges) < 1e-10:
                return 1.0

            min_edge = min(edges)
            max_edge = max(edges)

            return 1.0 - (min_edge / max_edge)

        elif elem.type == ElementType.HEX8:
            # Measure angle deviation from 90 degrees
            angles = []
            for i in range(8):
                v1 = coords[(i+1) % 8] - coords[i]
                v2 = coords[(i+3) % 8] - coords[i]

                norm1 = np.linalg.norm(v1)
                norm2 = np.linalg.norm(v2)

                if norm1 > 1e-10 and norm2 > 1e-10:
                    cos_angle = np.dot(v1, v2) / (norm1 * norm2)
                    cos_angle = np.clip(cos_angle, -1, 1)
                    angle = np.arccos(cos_angle)
                    deviation = abs(angle - np.pi/2)
                    angles.append(deviation)

            if not angles:
                return 0.0

            max_deviation = max(angles)
            return max_deviation / (np.pi/2)

        return 0.0

    def compute_aspect_ratio(self, element_id: int) -> float:
        """
        Compute aspect ratio (max/min characteristic length)

        Returns:
            Aspect ratio (>=1, 1 is perfect)
        """
        elem = self.mesh.elements[element_id]
        nodes = [self.mesh.nodes[nid] for nid in elem.nodes]
        coords = np.array([[n.x, n.y, n.z] for n in nodes])

        # Compute all edge lengths
        edges = []
        n = len(coords)
        for i in range(n):
            for j in range(i+1, n):
                edge_len = np.linalg.norm(coords[i] - coords[j])
                if edge_len > 1e-10:
                    edges.append(edge_len)

        if not edges:
            return 1.0

        return max(edges) / min(edges)

    def compute_all_metrics(self) -> Dict[str, List[float]]:
        """
        Compute all quality metrics for all elements

        Returns:
            Dictionary of metric names to value lists
        """
        jacobian = []
        skewness = []
        aspect_ratio = []

        for eid in self.mesh.elements.keys():
            jacobian.append(self.compute_jacobian_ratio(eid))
            skewness.append(self.compute_skewness(eid))
            aspect_ratio.append(self.compute_aspect_ratio(eid))

        return {
            'jacobian_ratio': jacobian,
            'skewness': skewness,
            'aspect_ratio': aspect_ratio
        }

    def generate_report(self) -> str:
        """Generate quality metrics report"""
        metrics = self.compute_all_metrics()

        lines = []
        lines.append("="*60)
        lines.append("ADVANCED MESH QUALITY METRICS")
        lines.append("="*60)

        for metric_name, values in metrics.items():
            if not values:
                continue

            lines.append(f"\n{metric_name.replace('_', ' ').title()}:")
            lines.append(f"  Min:  {min(values):.4f}")
            lines.append(f"  Max:  {max(values):.4f}")
            lines.append(f"  Mean: {np.mean(values):.4f}")
            lines.append(f"  Std:  {np.std(values):.4f}")

            # Quality assessment
            if 'jacobian' in metric_name:
                good = sum(1 for v in values if v > 0.3)
                lines.append(f"  Good elements (>0.3): {good}/{len(values)} ({100*good/len(values):.1f}%)")
            elif 'skewness' in metric_name:
                good = sum(1 for v in values if v < 0.5)
                lines.append(f"  Good elements (<0.5): {good}/{len(values)} ({100*good/len(values):.1f}%)")
            elif 'aspect' in metric_name:
                good = sum(1 for v in values if v < 3)
                lines.append(f"  Good elements (<3): {good}/{len(values)} ({100*good/len(values):.1f}%)")

        lines.append("\n" + "="*60)

        return "\n".join(lines)


def analyze_mesh_quality(mesh: MeshData, print_report: bool = True) -> Dict:
    """
    Convenience function for quality analysis

    Args:
        mesh: Mesh to analyze
        print_report: Print report to console

    Returns:
        Dictionary of metrics

    Example:
        >>> metrics = analyze_mesh_quality(mesh)
    """
    analyzer = AdvancedQualityMetrics(mesh)

    if print_report:
        print(analyzer.generate_report())

    return analyzer.compute_all_metrics()
