"""
Contact Quality Validation

Checks and validates contact definitions for simulation readiness.
"""

from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
import numpy as np
import logging

from koomesh.meshing.mesh_data import MeshData


@dataclass
class ContactIssue:
    """Represents a contact quality issue"""
    type: str  # PENETRATION, NONUNIFORM_GAP, MESH_SIZE_MISMATCH, etc.
    severity: str  # ERROR, WARNING, INFO
    message: str
    location: Any = None
    fix_suggestion: str = ""


@dataclass
class ContactQualityReport:
    """Contact quality check results"""
    passed: bool
    score: float  # 0.0 to 1.0
    issues: List[ContactIssue]
    statistics: Dict[str, Any]


class ContactQualityChecker:
    """
    Validate contact quality for FEA simulations.

    Checks:
    1. Initial penetration
    2. Gap uniformity
    3. Mesh size ratio (master/slave)
    4. Surface normal consistency
    5. Contact area continuity

    Example:
        >>> checker = ContactQualityChecker()
        >>> report = checker.check_contact_quality(
        ...     mesh1, mesh2, contact_pair, tolerance=0.1
        ... )
        >>> if not report.passed:
        ...     for issue in report.issues:
        ...         print(f"{issue.severity}: {issue.message}")
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def check_contact_quality(
        self,
        mesh1: MeshData,
        mesh2: MeshData,
        contact_surfaces1: np.ndarray,
        contact_surfaces2: np.ndarray,
        tolerance: float = 0.1
    ) -> ContactQualityReport:
        """
        Perform comprehensive contact quality checks.

        Args:
            mesh1: First mesh
            mesh2: Second mesh
            contact_surfaces1: Surface element indices in mesh1
            contact_surfaces2: Surface element indices in mesh2
            tolerance: General tolerance for checks (mm)

        Returns:
            ContactQualityReport with all findings

        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If quality checks fail
        """
        # Input validation
        if mesh1 is None or mesh2 is None:
            raise TypeError("mesh1 and mesh2 cannot be None")

        if contact_surfaces1 is None or contact_surfaces2 is None:
            raise TypeError("contact_surfaces cannot be None")

        if not isinstance(contact_surfaces1, np.ndarray) or not isinstance(contact_surfaces2, np.ndarray):
            raise TypeError("contact_surfaces must be numpy arrays")

        if len(contact_surfaces1) == 0 or len(contact_surfaces2) == 0:
            raise ValueError("contact_surfaces cannot be empty")

        if tolerance <= 0:
            raise ValueError(f"tolerance must be positive, got {tolerance}")

        if not hasattr(mesh1, 'nodes') or not hasattr(mesh2, 'nodes'):
            raise ValueError("meshes must have 'nodes' attribute")

        try:
            self.logger.info("Checking contact quality...")

            issues = []
            statistics = {}

            # Check 1: Penetration
            pen_issues, pen_stats = self._check_penetration(
                mesh1, mesh2, contact_surfaces1, contact_surfaces2, tolerance
            )
            issues.extend(pen_issues)
            statistics['penetration'] = pen_stats

            # Check 2: Gap uniformity
            gap_issues, gap_stats = self._check_gap_uniformity(
                mesh1, mesh2, contact_surfaces1, contact_surfaces2
            )
            issues.extend(gap_issues)
            statistics['gap'] = gap_stats

            # Check 3: Mesh size ratio
            ratio_issues, ratio_stats = self._check_mesh_size_ratio(
                mesh1, mesh2, contact_surfaces1, contact_surfaces2
            )
            issues.extend(ratio_issues)
            statistics['mesh_size'] = ratio_stats

            # Check 4: Surface normals
            normal_issues, normal_stats = self._check_normal_consistency(
                mesh1, mesh2, contact_surfaces1, contact_surfaces2
            )
            issues.extend(normal_issues)
            statistics['normals'] = normal_stats

            # Check 5: Contact area continuity
            area_issues, area_stats = self._check_area_continuity(
                mesh1, mesh2, contact_surfaces1, contact_surfaces2
            )
            issues.extend(area_issues)
            statistics['area'] = area_stats

            # Calculate overall quality score
            score = self._calculate_quality_score(issues, statistics)

            # Determine pass/fail
            has_errors = any(issue.severity == 'ERROR' for issue in issues)
            passed = not has_errors

            self.logger.info(
                f"Contact quality check complete: "
                f"{'PASSED' if passed else 'FAILED'}, score={score:.2f}"
            )

            return ContactQualityReport(
                passed=passed,
                score=score,
                issues=issues,
                statistics=statistics
            )

        except Exception as e:
            self.logger.error(f"Contact quality check failed: {e}")
            raise RuntimeError(f"Contact quality check failed: {e}") from e

    def _check_penetration(
        self,
        mesh1: MeshData,
        mesh2: MeshData,
        surfaces1: np.ndarray,
        surfaces2: np.ndarray,
        tolerance: float
    ) -> Tuple[List[ContactIssue], Dict]:
        """Check for initial penetration between surfaces."""
        issues = []

        # Get surface element centers
        centers1 = self._get_element_centers(mesh1, surfaces1)
        centers2 = self._get_element_centers(mesh2, surfaces2)

        if len(centers1) == 0 or len(centers2) == 0:
            return issues, {'max_penetration': 0.0, 'num_penetrating': 0}

        # Use KD-tree for fast nearest neighbor search
        from scipy.spatial import cKDTree
        tree = cKDTree(centers2)

        distances, indices = tree.query(centers1, k=1)

        # Check for penetration (negative distance or very small positive)
        penetration_threshold = -tolerance  # Negative = penetration
        penetrating = distances < penetration_threshold

        num_penetrating = np.sum(penetrating)
        max_penetration = abs(np.min(distances)) if len(distances) > 0 else 0.0

        statistics = {
            'max_penetration': max_penetration,
            'num_penetrating': int(num_penetrating),
            'avg_distance': float(np.mean(distances))
        }

        if num_penetrating > 0:
            issues.append(ContactIssue(
                type='PENETRATION',
                severity='ERROR',
                message=f'Initial penetration detected: {max_penetration:.3f}mm at {num_penetrating} locations',
                fix_suggestion='Adjust geometry clearance or use SOFT=2 (soft constraint penalty)'
            ))

        return issues, statistics

    def _check_gap_uniformity(
        self,
        mesh1: MeshData,
        mesh2: MeshData,
        surfaces1: np.ndarray,
        surfaces2: np.ndarray
    ) -> Tuple[List[ContactIssue], Dict]:
        """Check uniformity of gap distribution."""
        issues = []

        centers1 = self._get_element_centers(mesh1, surfaces1)
        centers2 = self._get_element_centers(mesh2, surfaces2)

        if len(centers1) == 0 or len(centers2) == 0:
            return issues, {}

        from scipy.spatial import cKDTree
        tree = cKDTree(centers2)
        distances, _ = tree.query(centers1, k=1)

        mean_gap = np.mean(distances)
        std_gap = np.std(distances)
        min_gap = np.min(distances)
        max_gap = np.max(distances)

        statistics = {
            'mean': float(mean_gap),
            'std': float(std_gap),
            'min': float(min_gap),
            'max': float(max_gap),
            'coefficient_of_variation': float(std_gap / mean_gap) if mean_gap > 0 else 0.0
        }

        # Check if gap variation is too large (CV > 0.3 = warning, > 0.5 = error)
        cv = std_gap / mean_gap if mean_gap > 0 else 0

        if cv > 0.5:
            issues.append(ContactIssue(
                type='NONUNIFORM_GAP',
                severity='ERROR',
                message=f'Gap highly non-uniform: CV={cv:.2f}, range=[{min_gap:.3f}, {max_gap:.3f}]mm',
                fix_suggestion='Refine mesh in areas with varying gap or check geometry quality'
            ))
        elif cv > 0.3:
            issues.append(ContactIssue(
                type='NONUNIFORM_GAP',
                severity='WARNING',
                message=f'Gap moderately non-uniform: CV={cv:.2f}, std={std_gap:.3f}mm',
                fix_suggestion='Consider local mesh refinement for better contact accuracy'
            ))

        return issues, statistics

    def _check_mesh_size_ratio(
        self,
        mesh1: MeshData,
        mesh2: MeshData,
        surfaces1: np.ndarray,
        surfaces2: np.ndarray
    ) -> Tuple[List[ContactIssue], Dict]:
        """Check mesh size ratio between master and slave surfaces."""
        issues = []

        size1 = self._estimate_average_element_size(mesh1, surfaces1)
        size2 = self._estimate_average_element_size(mesh2, surfaces2)

        if size1 == 0 or size2 == 0:
            return issues, {}

        ratio = max(size1, size2) / min(size1, size2)

        statistics = {
            'mesh1_size': float(size1),
            'mesh2_size': float(size2),
            'ratio': float(ratio),
            'coarser_mesh': 1 if size1 > size2 else 2
        }

        # Recommended ratio < 3:1
        if ratio > 5.0:
            issues.append(ContactIssue(
                type='MESH_SIZE_MISMATCH',
                severity='ERROR',
                message=f'Mesh size ratio {ratio:.1f}:1 > 5:1 (recommended < 3:1)',
                fix_suggestion='Refine coarser mesh or coarsen finer mesh to ratio < 3:1'
            ))
        elif ratio > 3.0:
            issues.append(ContactIssue(
                type='MESH_SIZE_MISMATCH',
                severity='WARNING',
                message=f'Mesh size ratio {ratio:.1f}:1 > 3:1 (recommended < 3:1)',
                fix_suggestion='Consider adjusting mesh sizes for better contact resolution'
            ))

        return issues, statistics

    def _check_normal_consistency(
        self,
        mesh1: MeshData,
        mesh2: MeshData,
        surfaces1: np.ndarray,
        surfaces2: np.ndarray
    ) -> Tuple[List[ContactIssue], Dict]:
        """Check consistency of surface normals."""
        issues = []

        normals1 = self._calculate_surface_normals(mesh1, surfaces1)
        normals2 = self._calculate_surface_normals(mesh2, surfaces2)

        if len(normals1) == 0 or len(normals2) == 0:
            return issues, {}

        # Check if normals are pointing outward consistently
        # Simplified check: measure variation in normal directions
        normal_consistency1 = self._calculate_normal_consistency(normals1)
        normal_consistency2 = self._calculate_normal_consistency(normals2)

        statistics = {
            'mesh1_consistency': float(normal_consistency1),
            'mesh2_consistency': float(normal_consistency2),
            'min_consistency': float(min(normal_consistency1, normal_consistency2))
        }

        min_consistency = min(normal_consistency1, normal_consistency2)

        if min_consistency < 0.7:
            issues.append(ContactIssue(
                type='NORMAL_INCONSISTENT',
                severity='ERROR',
                message=f'Surface normals inconsistent (consistency={min_consistency:.2f})',
                fix_suggestion='Check element orientation and fix inverted elements'
            ))
        elif min_consistency < 0.9:
            issues.append(ContactIssue(
                type='NORMAL_INCONSISTENT',
                severity='WARNING',
                message=f'Surface normals somewhat inconsistent (consistency={min_consistency:.2f})',
                fix_suggestion='Review element quality and orientation'
            ))

        return issues, statistics

    def _check_area_continuity(
        self,
        mesh1: MeshData,
        mesh2: MeshData,
        surfaces1: np.ndarray,
        surfaces2: np.ndarray
    ) -> Tuple[List[ContactIssue], Dict]:
        """Check if contact area is continuous (no large gaps)."""
        issues = []

        centers1 = self._get_element_centers(mesh1, surfaces1)

        if len(centers1) < 2:
            return issues, {}

        # Calculate distances to nearest neighbors within same surface
        from scipy.spatial import cKDTree
        tree = cKDTree(centers1)
        distances, _ = tree.query(centers1, k=2)  # k=2 to get distance to nearest neighbor (excluding self)

        nearest_distances = distances[:, 1]  # Second column is nearest neighbor
        mean_spacing = np.mean(nearest_distances)
        max_spacing = np.max(nearest_distances)

        statistics = {
            'mean_spacing': float(mean_spacing),
            'max_spacing': float(max_spacing),
            'discontinuity_ratio': float(max_spacing / mean_spacing) if mean_spacing > 0 else 0.0
        }

        # Check for large gaps (discontinuities)
        if max_spacing > mean_spacing * 5:
            issues.append(ContactIssue(
                type='DISCONTINUOUS_AREA',
                severity='WARNING',
                message=f'Contact area may be discontinuous: max gap {max_spacing:.2f}mm vs avg {mean_spacing:.2f}mm',
                fix_suggestion='Check if contact zone should be split into multiple contact pairs'
            ))

        return issues, statistics

    def _get_element_centers(
        self,
        mesh: MeshData,
        element_indices: np.ndarray
    ) -> np.ndarray:
        """Calculate centers of specified elements."""
        if len(element_indices) == 0:
            return np.array([])

        centers = []
        for idx in element_indices:
            if idx < len(mesh.elements):
                elem = mesh.elements[idx]
                elem_nodes = mesh.nodes[elem]
                center = np.mean(elem_nodes, axis=0)
                centers.append(center)

        return np.array(centers) if centers else np.array([])

    def _estimate_average_element_size(
        self,
        mesh: MeshData,
        element_indices: np.ndarray
    ) -> float:
        """Estimate average element size from elements."""
        if len(element_indices) == 0:
            return 0.0

        sizes = []
        for idx in element_indices[:min(100, len(element_indices))]:  # Sample first 100
            if idx < len(mesh.elements):
                elem = mesh.elements[idx]
                elem_nodes = mesh.nodes[elem]

                # Calculate characteristic length (max edge length)
                max_edge = 0.0
                for i in range(len(elem_nodes)):
                    for j in range(i + 1, len(elem_nodes)):
                        edge_length = np.linalg.norm(elem_nodes[i] - elem_nodes[j])
                        max_edge = max(max_edge, edge_length)

                sizes.append(max_edge)

        return np.mean(sizes) if sizes else 0.0

    def _calculate_surface_normals(
        self,
        mesh: MeshData,
        element_indices: np.ndarray
    ) -> np.ndarray:
        """Calculate normal vectors for surface elements."""
        normals = []

        for idx in element_indices[:min(100, len(element_indices))]:
            if idx < len(mesh.elements):
                elem = mesh.elements[idx]
                if len(elem) >= 3:
                    # Use first 3 nodes to calculate normal
                    nodes = mesh.nodes[elem[:3]]
                    v1 = nodes[1] - nodes[0]
                    v2 = nodes[2] - nodes[0]
                    normal = np.cross(v1, v2)

                    norm = np.linalg.norm(normal)
                    if norm > 1e-10:
                        normal = normal / norm
                        normals.append(normal)

        return np.array(normals) if normals else np.array([])

    def _calculate_normal_consistency(self, normals: np.ndarray) -> float:
        """Calculate consistency score for normal vectors (0-1)."""
        if len(normals) < 2:
            return 1.0

        # Calculate average normal
        avg_normal = np.mean(normals, axis=0)
        avg_normal = avg_normal / np.linalg.norm(avg_normal)

        # Calculate dot products with average
        dots = np.dot(normals, avg_normal)

        # Consistency = average of absolute dot products
        consistency = np.mean(np.abs(dots))

        return float(consistency)

    def _calculate_quality_score(
        self,
        issues: List[ContactIssue],
        statistics: Dict
    ) -> float:
        """Calculate overall quality score (0-1)."""
        if not issues:
            return 1.0

        # Count errors and warnings
        num_errors = sum(1 for issue in issues if issue.severity == 'ERROR')
        num_warnings = sum(1 for issue in issues if issue.severity == 'WARNING')

        # Score calculation: start at 1.0, subtract for issues
        score = 1.0
        score -= num_errors * 0.3  # Each error: -0.3
        score -= num_warnings * 0.1  # Each warning: -0.1

        return max(0.0, min(1.0, score))
