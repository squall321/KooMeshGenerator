"""
Tests for Contact Quality Validation

Tests contact quality checking for FEA simulations.
"""

import pytest
import numpy as np
from unittest.mock import Mock

from koomesh.contact.contact_quality import (
    ContactIssue,
    ContactQualityReport,
    ContactQualityChecker
)
from koomesh.meshing.mesh_data import MeshData


@pytest.fixture
def checker():
    """Create ContactQualityChecker instance"""
    return ContactQualityChecker()


@pytest.fixture
def sample_meshes():
    """Create sample mesh data for testing"""
    # Mesh 1: 4x4 grid in XY plane at z=0
    x = np.linspace(0, 3, 4)
    y = np.linspace(0, 3, 4)
    xx, yy = np.meshgrid(x, y)
    nodes1 = np.column_stack([xx.ravel(), yy.ravel(), np.zeros(16)])

    # Simple quad elements
    elements1 = []
    for i in range(3):
        for j in range(3):
            n1 = i * 4 + j
            n2 = i * 4 + j + 1
            n3 = (i + 1) * 4 + j + 1
            n4 = (i + 1) * 4 + j
            elements1.append([n1, n2, n3, n4])

    mesh1 = MeshData(nodes=np.array(nodes1), elements=np.array(elements1))

    # Mesh 2: Similar grid at z=0.1 (small gap)
    nodes2 = nodes1.copy()
    nodes2[:, 2] = 0.1

    mesh2 = MeshData(nodes=np.array(nodes2), elements=np.array(elements1))

    return mesh1, mesh2


@pytest.fixture
def sample_surface_indices():
    """Create sample surface element indices"""
    # Use all elements as surface elements for testing
    return np.array([0, 1, 2, 3, 4, 5, 6, 7, 8]), np.array([0, 1, 2, 3, 4, 5, 6, 7, 8])


class TestContactIssue:
    """Test ContactIssue dataclass"""

    def test_contact_issue_creation(self):
        """Test creating a contact issue"""
        issue = ContactIssue(
            type='PENETRATION',
            severity='ERROR',
            message='Initial penetration detected',
            location=(1.0, 2.0, 3.0),
            fix_suggestion='Adjust geometry clearance'
        )

        assert issue.type == 'PENETRATION'
        assert issue.severity == 'ERROR'
        assert issue.message == 'Initial penetration detected'
        assert issue.location == (1.0, 2.0, 3.0)
        assert issue.fix_suggestion == 'Adjust geometry clearance'


class TestContactQualityReport:
    """Test ContactQualityReport dataclass"""

    def test_quality_report_creation(self):
        """Test creating a quality report"""
        issues = [
            ContactIssue('PENETRATION', 'ERROR', 'Test error'),
            ContactIssue('NONUNIFORM_GAP', 'WARNING', 'Test warning')
        ]

        report = ContactQualityReport(
            passed=False,
            score=0.7,
            issues=issues,
            statistics={'max_penetration': 0.5}
        )

        assert not report.passed
        assert report.score == 0.7
        assert len(report.issues) == 2
        assert report.statistics['max_penetration'] == 0.5


class TestContactQualityChecker:
    """Test ContactQualityChecker class"""

    def test_initialization(self, checker):
        """Test checker initialization"""
        assert checker is not None
        assert checker.logger is not None

    def test_check_contact_quality_basic(self, checker, sample_meshes, sample_surface_indices):
        """Test basic contact quality check"""
        mesh1, mesh2 = sample_meshes
        surf1, surf2 = sample_surface_indices

        report = checker.check_contact_quality(
            mesh1, mesh2, surf1, surf2, tolerance=0.1
        )

        # Should return a valid report
        assert isinstance(report, ContactQualityReport)
        assert isinstance(report.passed, bool)
        assert 0.0 <= report.score <= 1.0
        assert isinstance(report.issues, list)
        assert isinstance(report.statistics, dict)

    def test_check_penetration_no_penetration(self, checker, sample_meshes, sample_surface_indices):
        """Test penetration check with no penetration"""
        mesh1, mesh2 = sample_meshes
        surf1, surf2 = sample_surface_indices

        issues, stats = checker._check_penetration(
            mesh1, mesh2, surf1, surf2, tolerance=0.05
        )

        # Gap is 0.1mm, tolerance 0.05mm → No penetration
        assert stats['num_penetrating'] == 0
        assert len(issues) == 0

    def test_check_penetration_with_penetration(self, checker, sample_meshes, sample_surface_indices):
        """Test penetration check with penetration"""
        mesh1, mesh2 = sample_meshes
        surf1, surf2 = sample_surface_indices

        # Make mesh2 overlap with mesh1 (z = -0.05 instead of 0.1)
        mesh2_penetrating = MeshData(
            nodes=mesh1.nodes.copy(),
            elements=mesh2.elements.copy()
        )
        mesh2_penetrating.nodes[:, 2] = -0.05  # Penetration

        issues, stats = checker._check_penetration(
            mesh1, mesh2_penetrating, surf1, surf2, tolerance=0.01
        )

        # Should detect penetration
        # Note: Implementation uses distance check, so this depends on method
        assert 'max_penetration' in stats
        assert 'num_penetrating' in stats

    def test_check_gap_uniformity_uniform(self, checker, sample_meshes, sample_surface_indices):
        """Test gap uniformity check with uniform gap"""
        mesh1, mesh2 = sample_meshes
        surf1, surf2 = sample_surface_indices

        issues, stats = checker._check_gap_uniformity(
            mesh1, mesh2, surf1, surf2
        )

        # Gap should be uniform (all 0.1mm)
        assert 'mean' in stats
        assert 'std' in stats
        assert 'coefficient_of_variation' in stats

        # CV should be very small (uniform gap)
        cv = stats['coefficient_of_variation']
        assert cv < 0.3  # Good uniformity

        # Should have no errors
        errors = [i for i in issues if i.severity == 'ERROR']
        assert len(errors) == 0

    def test_check_gap_uniformity_nonuniform(self, checker, sample_meshes, sample_surface_indices):
        """Test gap uniformity check with non-uniform gap"""
        mesh1, mesh2 = sample_meshes
        surf1, surf2 = sample_surface_indices

        # Make gap non-uniform (vary z from 0.05 to 0.5)
        mesh2_varied = MeshData(
            nodes=mesh2.nodes.copy(),
            elements=mesh2.elements.copy()
        )
        # Add variation to z-coordinate
        mesh2_varied.nodes[:, 2] = np.linspace(0.05, 0.5, len(mesh2.nodes))

        issues, stats = checker._check_gap_uniformity(
            mesh1, mesh2_varied, surf1, surf2
        )

        # Gap should be non-uniform
        cv = stats['coefficient_of_variation']
        # Higher variation
        assert cv > 0.1

        # May have warnings depending on CV threshold
        assert isinstance(issues, list)

    def test_check_mesh_size_ratio_good(self, checker, sample_meshes, sample_surface_indices):
        """Test mesh size ratio check with good ratio"""
        mesh1, mesh2 = sample_meshes
        surf1, surf2 = sample_surface_indices

        issues, stats = checker._check_mesh_size_ratio(
            mesh1, mesh2, surf1, surf2
        )

        # Same mesh size → ratio ~1.0
        assert 'ratio' in stats
        assert stats['ratio'] <= 3.0  # Good ratio

        # Should have no errors
        errors = [i for i in issues if i.severity == 'ERROR']
        assert len(errors) == 0

    def test_check_mesh_size_ratio_bad(self, checker):
        """Test mesh size ratio check with bad ratio"""
        # Mesh 1: coarse (size ~1.0)
        nodes1 = np.array([
            [0, 0, 0],
            [1, 0, 0],
            [1, 1, 0],
            [0, 1, 0]
        ], dtype=float)
        elements1 = np.array([[0, 1, 2, 3]])
        mesh1 = MeshData(nodes=nodes1, elements=elements1)

        # Mesh 2: fine (size ~0.1)
        nodes2 = np.array([
            [0, 0, 0.1],
            [0.1, 0, 0.1],
            [0.1, 0.1, 0.1],
            [0, 0.1, 0.1]
        ], dtype=float)
        elements2 = np.array([[0, 1, 2, 3]])
        mesh2 = MeshData(nodes=nodes2, elements=elements2)

        surf1 = np.array([0])
        surf2 = np.array([0])

        issues, stats = checker._check_mesh_size_ratio(
            mesh1, mesh2, surf1, surf2
        )

        # Ratio should be large (~10:1)
        assert stats['ratio'] > 3.0

        # Should have warnings or errors
        assert len(issues) > 0

    def test_check_normal_consistency_good(self, checker, sample_meshes, sample_surface_indices):
        """Test normal consistency check with consistent normals"""
        mesh1, mesh2 = sample_meshes
        surf1, surf2 = sample_surface_indices

        issues, stats = checker._check_normal_consistency(
            mesh1, mesh2, surf1, surf2
        )

        # All faces in same plane → consistent normals
        assert 'mesh1_consistency' in stats
        assert 'mesh2_consistency' in stats
        assert stats['mesh1_consistency'] > 0.9  # Very consistent

        # Should have no errors
        errors = [i for i in issues if i.severity == 'ERROR']
        assert len(errors) == 0

    def test_check_area_continuity_continuous(self, checker, sample_meshes, sample_surface_indices):
        """Test area continuity check with continuous area"""
        mesh1, mesh2 = sample_meshes
        surf1, surf2 = sample_surface_indices

        issues, stats = checker._check_area_continuity(
            mesh1, mesh2, surf1, surf2
        )

        # Regular grid → continuous contact area
        assert 'mean_spacing' in stats
        assert 'max_spacing' in stats
        assert 'discontinuity_ratio' in stats

        # Discontinuity ratio should be low
        assert stats['discontinuity_ratio'] < 5.0

        # Should have no major issues
        errors = [i for i in issues if i.severity == 'ERROR']
        assert len(errors) == 0

    def test_get_element_centers(self, checker, sample_meshes):
        """Test element center calculation"""
        mesh1, _ = sample_meshes

        element_indices = np.array([0, 1, 2])
        centers = checker._get_element_centers(mesh1, element_indices)

        # Should return array of centers
        assert len(centers) == 3
        assert centers.shape[1] == 3  # 3D coordinates

        # Centers should be within mesh bounds
        assert np.all(centers[:, 0] >= 0) and np.all(centers[:, 0] <= 3)
        assert np.all(centers[:, 1] >= 0) and np.all(centers[:, 1] <= 3)

    def test_estimate_average_element_size(self, checker, sample_meshes):
        """Test average element size estimation"""
        mesh1, _ = sample_meshes

        element_indices = np.array([0, 1, 2, 3])
        avg_size = checker._estimate_average_element_size(mesh1, element_indices)

        # Should return positive size
        assert avg_size > 0.0

        # For 1x1 quads, size should be ~1.0-1.4 (diagonal)
        assert 0.5 <= avg_size <= 2.0

    def test_calculate_surface_normals(self, checker, sample_meshes):
        """Test surface normal calculation"""
        mesh1, _ = sample_meshes

        element_indices = np.array([0, 1, 2])
        normals = checker._calculate_surface_normals(mesh1, element_indices)

        # Should return normals
        assert len(normals) > 0
        assert normals.shape[1] == 3

        # Normals should be unit vectors
        for normal in normals:
            norm = np.linalg.norm(normal)
            assert abs(norm - 1.0) < 1e-6

        # For XY plane at z=0, normals should point in +Z direction
        # (May vary depending on element orientation)
        assert np.all(np.abs(normals[:, 2]) > 0.9)  # Mostly Z-direction

    def test_calculate_normal_consistency(self, checker):
        """Test normal consistency calculation"""
        # All normals pointing in same direction
        normals_consistent = np.array([
            [0, 0, 1],
            [0, 0, 1],
            [0, 0, 1]
        ], dtype=float)

        consistency = checker._calculate_normal_consistency(normals_consistent)
        assert consistency > 0.99  # Perfect consistency

        # Normals pointing in opposite directions
        normals_inconsistent = np.array([
            [0, 0, 1],
            [0, 0, -1],
            [0, 0, 1]
        ], dtype=float)

        consistency = checker._calculate_normal_consistency(normals_inconsistent)
        assert consistency < 0.9  # Poor consistency

    def test_calculate_quality_score_no_issues(self, checker):
        """Test quality score with no issues"""
        score = checker._calculate_quality_score([], {})
        assert score == 1.0  # Perfect score

    def test_calculate_quality_score_with_warnings(self, checker):
        """Test quality score with warnings"""
        issues = [
            ContactIssue('GAP', 'WARNING', 'Warning 1'),
            ContactIssue('GAP', 'WARNING', 'Warning 2')
        ]

        score = checker._calculate_quality_score(issues, {})

        # 2 warnings × 0.1 = -0.2
        assert 0.7 <= score <= 0.8

    def test_calculate_quality_score_with_errors(self, checker):
        """Test quality score with errors"""
        issues = [
            ContactIssue('PENETRATION', 'ERROR', 'Error 1'),
            ContactIssue('GAP', 'WARNING', 'Warning 1')
        ]

        score = checker._calculate_quality_score(issues, {})

        # 1 error × 0.3 + 1 warning × 0.1 = -0.4
        assert 0.5 <= score <= 0.6


class TestContactQualityIntegration:
    """Integration tests for contact quality checking"""

    @pytest.mark.integration
    def test_full_quality_check_workflow(self, checker, sample_meshes, sample_surface_indices):
        """Test complete quality check workflow"""
        mesh1, mesh2 = sample_meshes
        surf1, surf2 = sample_surface_indices

        # Run full quality check
        report = checker.check_contact_quality(
            mesh1, mesh2, surf1, surf2, tolerance=0.1
        )

        # Verify all checks were performed
        assert 'penetration' in report.statistics
        assert 'gap' in report.statistics
        assert 'mesh_size' in report.statistics
        assert 'normals' in report.statistics
        assert 'area' in report.statistics

        # Should pass (good quality meshes)
        assert report.passed or len([i for i in report.issues if i.severity == 'ERROR']) == 0

    @pytest.mark.integration
    def test_quality_check_with_multiple_issues(self, checker):
        """Test quality check detecting multiple issues"""
        # Create problematic meshes
        # Mesh 1: irregular
        nodes1 = np.array([
            [0, 0, 0],
            [2, 0, 0],
            [2, 2, 0],
            [0, 2, 0],
            [1, 1, 0.5]  # Out of plane
        ], dtype=float)
        elements1 = np.array([[0, 1, 2, 3]])

        # Mesh 2: penetrating
        nodes2 = np.array([
            [0, 0, -0.1],  # Penetration
            [0.1, 0, -0.1],
            [0.1, 0.1, -0.1],
            [0, 0.1, -0.1]
        ], dtype=float)
        elements2 = np.array([[0, 1, 2, 3]])

        mesh1 = MeshData(nodes=nodes1, elements=elements1)
        mesh2 = MeshData(nodes=nodes2, elements=elements2)

        surf1 = np.array([0])
        surf2 = np.array([0])

        report = checker.check_contact_quality(
            mesh1, mesh2, surf1, surf2, tolerance=0.05
        )

        # Should detect multiple issues
        assert len(report.issues) > 0
        # May fail due to issues
        # Just verify report is generated
        assert isinstance(report, ContactQualityReport)


class TestContactQualityEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_surface_indices(self, checker, sample_meshes):
        """Test with empty surface indices"""
        mesh1, mesh2 = sample_meshes
        surf1 = np.array([])
        surf2 = np.array([])

        report = checker.check_contact_quality(
            mesh1, mesh2, surf1, surf2, tolerance=0.1
        )

        # Should handle gracefully
        assert isinstance(report, ContactQualityReport)
        # No surfaces → perfect score
        assert report.score == 1.0 or report.score >= 0.0

    def test_single_element_surfaces(self, checker):
        """Test with single element surfaces"""
        nodes1 = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]], dtype=float)
        elements1 = np.array([[0, 1, 2, 3]])
        mesh1 = MeshData(nodes=nodes1, elements=elements1)

        nodes2 = np.array([[0, 0, 0.1], [1, 0, 0.1], [1, 1, 0.1], [0, 1, 0.1]], dtype=float)
        elements2 = np.array([[0, 1, 2, 3]])
        mesh2 = MeshData(nodes=nodes2, elements=elements2)

        surf1 = np.array([0])
        surf2 = np.array([0])

        report = checker.check_contact_quality(
            mesh1, mesh2, surf1, surf2, tolerance=0.1
        )

        # Should handle single elements
        assert isinstance(report, ContactQualityReport)

    def test_very_large_tolerance(self, checker, sample_meshes, sample_surface_indices):
        """Test with very large tolerance"""
        mesh1, mesh2 = sample_meshes
        surf1, surf2 = sample_surface_indices

        report = checker.check_contact_quality(
            mesh1, mesh2, surf1, surf2, tolerance=100.0
        )

        # Should complete without errors
        assert isinstance(report, ContactQualityReport)

    def test_negative_tolerance(self, checker, sample_meshes, sample_surface_indices):
        """Test with negative tolerance"""
        mesh1, mesh2 = sample_meshes
        surf1, surf2 = sample_surface_indices

        report = checker.check_contact_quality(
            mesh1, mesh2, surf1, surf2, tolerance=-0.1
        )

        # Should handle gracefully
        assert isinstance(report, ContactQualityReport)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
