"""
Tests for Extended Mesh Quality Checker ([007])
===============================================

This module tests the extended quality checking features including:
- Element grading (Excellent/Good/Fair/Poor/Bad)
- Angle quality metrics
- Edge length ratios
- Quality distributions
- CSV/JSON export
- Detailed reporting
"""

import pytest
import numpy as np
import tempfile
import json
import csv
from pathlib import Path

from koomesh.meshing.mesh_data import MeshData, ElementType
from koomesh.meshing.quality_checker import QualityChecker


@pytest.fixture
def perfect_hex_mesh():
    """Create a perfect unit cube hex mesh"""
    mesh = MeshData(element_type=ElementType.HEX8)

    # Perfect unit cube
    coords = [
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [1.0, 1.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
        [1.0, 0.0, 1.0],
        [1.0, 1.0, 1.0],
        [0.0, 1.0, 1.0],
    ]

    node_ids = [mesh.add_node(x, y, z) for x, y, z in coords]
    mesh.add_element(node_ids)

    return mesh


@pytest.fixture
def distorted_hex_mesh():
    """Create a distorted hex mesh with poor quality"""
    mesh = MeshData(element_type=ElementType.HEX8)

    # Distorted cube - severely stretched
    coords = [
        [0.0, 0.0, 0.0],
        [10.0, 0.0, 0.0],  # Stretched in x
        [10.0, 0.5, 0.0],  # Small y dimension
        [0.0, 0.5, 0.0],
        [0.0, 0.0, 0.5],   # Small z dimension
        [10.0, 0.0, 0.5],
        [10.0, 0.5, 0.5],
        [0.0, 0.5, 0.5],
    ]

    node_ids = [mesh.add_node(x, y, z) for x, y, z in coords]
    mesh.add_element(node_ids)

    return mesh


@pytest.fixture
def multi_element_mesh():
    """Create mesh with multiple elements of varying quality"""
    mesh = MeshData(element_type=ElementType.HEX8)

    # Element 1: Good quality
    coords1 = [
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [1.0, 1.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
        [1.0, 0.0, 1.0],
        [1.0, 1.0, 1.0],
        [0.0, 1.0, 1.0],
    ]

    # Element 2: Fair quality (slightly distorted)
    coords2 = [
        [2.0, 0.0, 0.0],
        [3.2, 0.0, 0.0],
        [3.2, 1.2, 0.0],
        [2.0, 1.2, 0.0],
        [2.0, 0.0, 0.8],
        [3.2, 0.0, 0.8],
        [3.2, 1.2, 0.8],
        [2.0, 1.2, 0.8],
    ]

    # Element 3: Poor quality (heavily distorted)
    coords3 = [
        [4.0, 0.0, 0.0],
        [8.0, 0.0, 0.0],  # Very stretched
        [8.0, 0.5, 0.0],
        [4.0, 0.5, 0.0],
        [4.0, 0.0, 0.5],
        [8.0, 0.0, 0.5],
        [8.0, 0.5, 0.5],
        [4.0, 0.5, 0.5],
    ]

    # Add all elements
    for coords in [coords1, coords2, coords3]:
        node_ids = [mesh.add_node(x, y, z) for x, y, z in coords]
        mesh.add_element(node_ids)

    return mesh


class TestElementGrading:
    """Test element quality grading functionality"""

    def test_grade_perfect_element(self, perfect_hex_mesh):
        """Test grading of perfect cube element"""
        checker = QualityChecker()
        elem = perfect_hex_mesh.get_element(1)

        grade = checker.grade_element(elem, perfect_hex_mesh)

        assert grade in ['Excellent', 'Good'], \
            "Perfect cube should be Excellent or Good quality"

    def test_grade_distorted_element(self, distorted_hex_mesh):
        """Test grading of distorted element"""
        checker = QualityChecker()
        elem = distorted_hex_mesh.get_element(1)

        grade = checker.grade_element(elem, distorted_hex_mesh)

        assert grade in ['Poor', 'Bad'], \
            "Distorted element should be Poor or Bad quality"

    def test_grade_all_levels(self, multi_element_mesh):
        """Test that we can distinguish different quality levels"""
        checker = QualityChecker()

        grades = []
        for elem_id in multi_element_mesh.elements.keys():
            elem = multi_element_mesh.get_element(elem_id)
            grade = checker.grade_element(elem, multi_element_mesh)
            grades.append(grade)

        # Should have at least 2 different grades
        unique_grades = set(grades)
        assert len(unique_grades) >= 2, \
            "Multi-element mesh should have multiple quality grades"


class TestAngleMetrics:
    """Test angle quality metrics"""

    def test_angles_perfect_cube(self, perfect_hex_mesh):
        """Test angle metrics for perfect cube"""
        checker = QualityChecker()
        report = checker.check_mesh(perfect_hex_mesh)

        # Perfect cube should have all 90-degree angles
        assert 'min' in report.angles
        assert 'max' in report.angles
        assert 'mean' in report.angles

        # Allow small tolerance for numerical errors
        assert abs(report.angles['min'] - 90.0) < 1.0, \
            f"Min angle should be ~90° but got {report.angles['min']}"
        assert abs(report.angles['max'] - 90.0) < 1.0, \
            f"Max angle should be ~90° but got {report.angles['max']}"

    def test_angles_distorted_element(self, distorted_hex_mesh):
        """Test angle metrics for distorted element"""
        checker = QualityChecker()
        report = checker.check_mesh(distorted_hex_mesh)

        # Distorted element should have angles far from 90°
        assert report.angles['min'] < 80.0 or report.angles['max'] > 100.0, \
            "Distorted element should have non-ideal angles"

    def test_angle_statistics(self, multi_element_mesh):
        """Test angle statistics across multiple elements"""
        checker = QualityChecker()
        report = checker.check_mesh(multi_element_mesh)

        assert report.angles['min'] > 0.0
        assert report.angles['max'] < 180.0
        assert report.angles['min'] <= report.angles['mean'] <= report.angles['max']


class TestEdgeLengthRatio:
    """Test edge length ratio metrics"""

    def test_edge_ratio_perfect_cube(self, perfect_hex_mesh):
        """Test edge length ratio for perfect cube"""
        checker = QualityChecker()
        report = checker.check_mesh(perfect_hex_mesh)

        assert 'min' in report.edge_length_ratio
        assert 'max' in report.edge_length_ratio
        assert 'mean' in report.edge_length_ratio

        # Perfect cube should have ratio close to 1.0
        assert abs(report.edge_length_ratio['mean'] - 1.0) < 0.1, \
            "Perfect cube should have edge ratio ~1.0"

    def test_edge_ratio_distorted_element(self, distorted_hex_mesh):
        """Test edge length ratio for distorted element"""
        checker = QualityChecker()
        report = checker.check_mesh(distorted_hex_mesh)

        # Distorted element should have high edge length ratio
        assert report.edge_length_ratio['max'] > 5.0, \
            "Distorted element should have high edge length ratio"

    def test_edge_ratio_range(self, multi_element_mesh):
        """Test edge length ratio range"""
        checker = QualityChecker()
        report = checker.check_mesh(multi_element_mesh)

        assert report.edge_length_ratio['min'] >= 1.0, \
            "Edge length ratio should be >= 1.0"
        assert report.edge_length_ratio['min'] <= report.edge_length_ratio['max']


class TestQualityDistribution:
    """Test quality distribution functionality"""

    def test_distribution_perfect_mesh(self, perfect_hex_mesh):
        """Test quality distribution for perfect mesh"""
        checker = QualityChecker()
        report = checker.check_mesh(perfect_hex_mesh)

        assert 'Excellent' in report.quality_distribution or \
               'Good' in report.quality_distribution

        # Should have 1 element total
        total = sum(report.quality_distribution.values())
        assert total == 1, "Should have exactly 1 element"

    def test_distribution_multi_element(self, multi_element_mesh):
        """Test quality distribution for multi-element mesh"""
        checker = QualityChecker()
        report = checker.check_mesh(multi_element_mesh)

        # Should have 3 elements total
        total = sum(report.quality_distribution.values())
        assert total == 3, "Should have exactly 3 elements"

        # Should have at least 2 different grades
        grades_present = sum(1 for count in report.quality_distribution.values() if count > 0)
        assert grades_present >= 2, "Should have multiple quality grades"

    def test_distribution_categories(self, multi_element_mesh):
        """Test that all quality categories are present in distribution"""
        checker = QualityChecker()
        report = checker.check_mesh(multi_element_mesh)

        expected_categories = ['Excellent', 'Good', 'Fair', 'Poor', 'Bad']
        for category in expected_categories:
            assert category in report.quality_distribution, \
                f"Category '{category}' should be present in distribution"


class TestElementReport:
    """Test detailed element reporting"""

    def test_element_report_structure(self, perfect_hex_mesh):
        """Test structure of element report"""
        checker = QualityChecker()
        elem = perfect_hex_mesh.get_element(1)

        elem_report = checker.get_element_report(elem, perfect_hex_mesh)

        # Check required fields
        assert 'element_id' in elem_report
        assert 'quality_grade' in elem_report
        assert 'jacobian' in elem_report
        assert 'aspect_ratio' in elem_report
        assert 'min_angle' in elem_report
        assert 'max_angle' in elem_report
        assert 'edge_length_ratio' in elem_report

    def test_element_report_values(self, perfect_hex_mesh):
        """Test values in element report"""
        checker = QualityChecker()
        elem = perfect_hex_mesh.get_element(1)

        elem_report = checker.get_element_report(elem, perfect_hex_mesh)

        assert elem_report['element_id'] == 1
        assert elem_report['jacobian'] > 0
        assert elem_report['aspect_ratio'] >= 1.0
        assert 0 < elem_report['min_angle'] < 180
        assert 0 < elem_report['max_angle'] < 180


class TestHistogram:
    """Test histogram generation"""

    def test_histogram_jacobian(self, multi_element_mesh):
        """Test histogram for Jacobian metric"""
        checker = QualityChecker()

        hist = checker.get_quality_histogram(multi_element_mesh, 'jacobian', bins=5)

        assert 'bins' in hist
        assert 'counts' in hist
        assert 'bin_edges' in hist
        assert len(hist['bins']) == len(hist['counts'])

    def test_histogram_aspect_ratio(self, multi_element_mesh):
        """Test histogram for aspect ratio metric"""
        checker = QualityChecker()

        hist = checker.get_quality_histogram(multi_element_mesh, 'aspect_ratio', bins=5)

        # Sum of counts should equal number of elements
        total_count = sum(hist['counts'])
        assert total_count == multi_element_mesh.num_elements()

    def test_histogram_invalid_metric(self, multi_element_mesh):
        """Test histogram with invalid metric name"""
        checker = QualityChecker()

        with pytest.raises(ValueError):
            checker.get_quality_histogram(multi_element_mesh, 'invalid_metric')


class TestCSVExport:
    """Test CSV export functionality"""

    def test_csv_export_basic(self, perfect_hex_mesh):
        """Test basic CSV export"""
        checker = QualityChecker()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            csv_path = f.name

        try:
            checker.export_to_csv(perfect_hex_mesh, csv_path)

            # Verify file exists and has content
            assert Path(csv_path).exists()
            assert Path(csv_path).stat().st_size > 0

            # Read and verify CSV structure
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

                assert len(rows) == 1  # One element

                # Check required columns
                required_cols = ['element_id', 'quality_grade', 'jacobian',
                               'aspect_ratio', 'min_angle', 'max_angle']
                for col in required_cols:
                    assert col in rows[0], f"Column '{col}' missing from CSV"

        finally:
            Path(csv_path).unlink(missing_ok=True)

    def test_csv_export_multi_element(self, multi_element_mesh):
        """Test CSV export with multiple elements"""
        checker = QualityChecker()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            csv_path = f.name

        try:
            checker.export_to_csv(multi_element_mesh, csv_path)

            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

                assert len(rows) == 3  # Three elements

                # Verify element IDs
                elem_ids = [int(row['element_id']) for row in rows]
                assert sorted(elem_ids) == [1, 2, 3]

        finally:
            Path(csv_path).unlink(missing_ok=True)


class TestJSONExport:
    """Test JSON export functionality"""

    def test_json_export_basic(self, perfect_hex_mesh):
        """Test basic JSON export"""
        checker = QualityChecker()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json_path = f.name

        try:
            checker.export_to_json(perfect_hex_mesh, json_path)

            # Verify file exists and has content
            assert Path(json_path).exists()
            assert Path(json_path).stat().st_size > 0

            # Read and verify JSON structure
            with open(json_path, 'r') as f:
                data = json.load(f)

                assert 'summary' in data
                assert 'elements' in data

                assert data['summary']['num_elements'] == 1
                assert len(data['elements']) == 1

                # Check element structure
                elem = data['elements'][0]
                assert 'element_id' in elem
                assert 'quality_grade' in elem
                assert 'metrics' in elem

        finally:
            Path(json_path).unlink(missing_ok=True)

    def test_json_export_multi_element(self, multi_element_mesh):
        """Test JSON export with multiple elements"""
        checker = QualityChecker()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json_path = f.name

        try:
            checker.export_to_json(multi_element_mesh, json_path)

            with open(json_path, 'r') as f:
                data = json.load(f)

                assert data['summary']['num_elements'] == 3
                assert len(data['elements']) == 3

                # Verify quality distribution
                assert 'quality_distribution' in data['summary']

        finally:
            Path(json_path).unlink(missing_ok=True)


class TestDetailedReport:
    """Test detailed report generation"""

    def test_detailed_report_content(self, perfect_hex_mesh):
        """Test detailed report content"""
        checker = QualityChecker()

        report_text = checker.get_detailed_report(perfect_hex_mesh)

        # Should contain various sections
        assert "Mesh Quality Report" in report_text
        assert "Overall Statistics" in report_text
        assert "Quality Distribution" in report_text
        assert "Element Details" in report_text

    def test_detailed_report_multi_element(self, multi_element_mesh):
        """Test detailed report with multiple elements"""
        checker = QualityChecker()

        report_text = checker.get_detailed_report(multi_element_mesh)

        # Should contain all element IDs
        assert "Element 1:" in report_text
        assert "Element 2:" in report_text
        assert "Element 3:" in report_text

    def test_detailed_report_format(self, perfect_hex_mesh):
        """Test detailed report formatting"""
        checker = QualityChecker()

        report_text = checker.get_detailed_report(perfect_hex_mesh)

        # Should have separator lines
        assert "=" in report_text
        assert "-" in report_text

        # Should be non-empty
        assert len(report_text) > 100


class TestIntegrationWithReport:
    """Test integration with QualityReport"""

    def test_summary_includes_new_metrics(self, perfect_hex_mesh):
        """Test that summary includes new metrics"""
        checker = QualityChecker()
        report = checker.check_mesh(perfect_hex_mesh)

        summary_text = report.summary()

        # Should include angle information
        assert "Angles:" in summary_text

        # Should include edge length ratio
        assert "Edge Length Ratio:" in summary_text

        # Should include quality distribution
        assert "Quality Distribution:" in summary_text

    def test_all_new_fields_populated(self, multi_element_mesh):
        """Test that all new fields are populated"""
        checker = QualityChecker()
        report = checker.check_mesh(multi_element_mesh)

        # Check angles field
        assert report.angles
        assert 'min' in report.angles
        assert 'max' in report.angles
        assert 'mean' in report.angles

        # Check edge_length_ratio field
        assert report.edge_length_ratio
        assert 'min' in report.edge_length_ratio
        assert 'max' in report.edge_length_ratio

        # Check quality_distribution field
        assert report.quality_distribution
        assert sum(report.quality_distribution.values()) == report.num_elements


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
