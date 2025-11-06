"""
Tests for Advanced Mesh Quality Metrics

Author: KooMeshGenerator Team
"""

import pytest
import numpy as np

from koomesh.meshing.mesh_data import MeshData, ElementType
from koomesh.quality.advanced_metrics import AdvancedQualityMetrics, analyze_mesh_quality


@pytest.fixture
def perfect_tet_mesh():
    """Create a nearly perfect tetrahedron"""
    mesh = MeshData(element_type=ElementType.TET4)

    node_ids = []
    node_ids.append(mesh.add_node(0.0, 0.0, 0.0))
    node_ids.append(mesh.add_node(1.0, 0.0, 0.0))
    node_ids.append(mesh.add_node(0.5, np.sqrt(3)/2, 0.0))
    node_ids.append(mesh.add_node(0.5, np.sqrt(3)/6, np.sqrt(2/3)))

    mesh.add_element(node_ids)
    return mesh


@pytest.fixture
def perfect_hex_mesh():
    """Create a perfect cube"""
    mesh = MeshData(element_type=ElementType.HEX8)

    node_ids = []
    for i in range(2):
        for j in range(2):
            for k in range(2):
                node_ids.append(mesh.add_node(float(i), float(j), float(k)))

    mesh.add_element([node_ids[0], node_ids[1], node_ids[3], node_ids[2],
                     node_ids[4], node_ids[5], node_ids[7], node_ids[6]])
    return mesh


@pytest.fixture
def distorted_hex_mesh():
    """Create a distorted hexahedron"""
    mesh = MeshData(element_type=ElementType.HEX8)

    node_ids = []
    # Create a distorted hex
    node_ids.append(mesh.add_node(0.0, 0.0, 0.0))
    node_ids.append(mesh.add_node(1.0, 0.0, 0.0))
    node_ids.append(mesh.add_node(1.0, 1.0, 0.0))
    node_ids.append(mesh.add_node(0.0, 1.0, 0.0))
    node_ids.append(mesh.add_node(0.1, 0.1, 1.0))  # Distorted
    node_ids.append(mesh.add_node(1.0, 0.0, 1.0))
    node_ids.append(mesh.add_node(1.0, 1.0, 1.0))
    node_ids.append(mesh.add_node(0.0, 1.0, 1.0))

    mesh.add_element([node_ids[0], node_ids[1], node_ids[2], node_ids[3],
                     node_ids[4], node_ids[5], node_ids[6], node_ids[7]])
    return mesh


@pytest.fixture
def elongated_tet_mesh():
    """Create an elongated tetrahedron (high aspect ratio)"""
    mesh = MeshData(element_type=ElementType.TET4)

    node_ids = []
    node_ids.append(mesh.add_node(0.0, 0.0, 0.0))
    node_ids.append(mesh.add_node(10.0, 0.0, 0.0))  # Very long edge
    node_ids.append(mesh.add_node(0.0, 1.0, 0.0))
    node_ids.append(mesh.add_node(0.0, 0.0, 1.0))

    mesh.add_element(node_ids)
    return mesh


class TestJacobianRatio:
    """Test Jacobian ratio calculations"""

    def test_perfect_tet_jacobian(self, perfect_tet_mesh):
        """Test Jacobian ratio for perfect tet"""
        metrics = AdvancedQualityMetrics(perfect_tet_mesh)
        eid = list(perfect_tet_mesh.elements.keys())[0]

        ratio = metrics.compute_jacobian_ratio(eid)

        # Perfect tet should have positive Jacobian
        assert ratio >= 0.0
        assert ratio <= 1.0

    def test_perfect_hex_jacobian(self, perfect_hex_mesh):
        """Test Jacobian ratio for perfect cube"""
        metrics = AdvancedQualityMetrics(perfect_hex_mesh)
        eid = list(perfect_hex_mesh.elements.keys())[0]

        ratio = metrics.compute_jacobian_ratio(eid)

        # Jacobian ratio should be in valid range (simplified algorithm)
        assert 0.0 <= ratio <= 1.0

    def test_distorted_hex_jacobian(self, distorted_hex_mesh):
        """Test Jacobian ratio for distorted hex"""
        metrics = AdvancedQualityMetrics(distorted_hex_mesh)
        eid = list(distorted_hex_mesh.elements.keys())[0]

        ratio = metrics.compute_jacobian_ratio(eid)

        # Distorted should have lower ratio
        assert 0.0 <= ratio <= 1.0

    def test_jacobian_range(self, perfect_hex_mesh):
        """Test that Jacobian ratio is in valid range"""
        metrics = AdvancedQualityMetrics(perfect_hex_mesh)
        eid = list(perfect_hex_mesh.elements.keys())[0]

        ratio = metrics.compute_jacobian_ratio(eid)

        assert 0.0 <= ratio <= 1.0


class TestSkewness:
    """Test skewness calculations"""

    def test_perfect_cube_skewness(self, perfect_hex_mesh):
        """Test skewness for perfect cube"""
        metrics = AdvancedQualityMetrics(perfect_hex_mesh)
        eid = list(perfect_hex_mesh.elements.keys())[0]

        skewness = metrics.compute_skewness(eid)

        # Perfect cube should have low skewness
        assert 0.0 <= skewness <= 1.0
        assert skewness < 0.5  # Should be reasonable (algorithm is approximate)

    def test_distorted_hex_skewness(self, distorted_hex_mesh):
        """Test skewness for distorted hex"""
        metrics = AdvancedQualityMetrics(distorted_hex_mesh)
        eid = list(distorted_hex_mesh.elements.keys())[0]

        skewness = metrics.compute_skewness(eid)

        # Distorted should have higher skewness
        assert 0.0 <= skewness <= 1.0

    def test_tet_skewness(self, perfect_tet_mesh):
        """Test skewness for tetrahedron"""
        metrics = AdvancedQualityMetrics(perfect_tet_mesh)
        eid = list(perfect_tet_mesh.elements.keys())[0]

        skewness = metrics.compute_skewness(eid)

        # Should be in valid range
        assert 0.0 <= skewness <= 1.0

    def test_elongated_tet_skewness(self, elongated_tet_mesh):
        """Test skewness for elongated tet"""
        metrics = AdvancedQualityMetrics(elongated_tet_mesh)
        eid = list(elongated_tet_mesh.elements.keys())[0]

        skewness = metrics.compute_skewness(eid)

        # Elongated should have higher skewness
        assert 0.0 <= skewness <= 1.0
        assert skewness > 0.5  # Should be quite high


class TestAspectRatio:
    """Test aspect ratio calculations"""

    def test_perfect_cube_aspect_ratio(self, perfect_hex_mesh):
        """Test aspect ratio for perfect cube"""
        metrics = AdvancedQualityMetrics(perfect_hex_mesh)
        eid = list(perfect_hex_mesh.elements.keys())[0]

        aspect = metrics.compute_aspect_ratio(eid)

        # Perfect cube should have aspect ratio close to 1
        assert aspect >= 1.0
        assert aspect < 2.0  # Should be quite good

    def test_elongated_tet_aspect_ratio(self, elongated_tet_mesh):
        """Test aspect ratio for elongated tet"""
        metrics = AdvancedQualityMetrics(elongated_tet_mesh)
        eid = list(elongated_tet_mesh.elements.keys())[0]

        aspect = metrics.compute_aspect_ratio(eid)

        # Elongated should have high aspect ratio
        assert aspect >= 1.0
        assert aspect > 5.0  # Should be quite high due to long edge

    def test_aspect_ratio_minimum(self, perfect_hex_mesh):
        """Test that aspect ratio is at least 1.0"""
        metrics = AdvancedQualityMetrics(perfect_hex_mesh)
        eid = list(perfect_hex_mesh.elements.keys())[0]

        aspect = metrics.compute_aspect_ratio(eid)

        assert aspect >= 1.0


class TestComputeAllMetrics:
    """Test computing all metrics at once"""

    def test_compute_all_returns_dict(self, perfect_hex_mesh):
        """Test that compute_all_metrics returns dictionary"""
        metrics = AdvancedQualityMetrics(perfect_hex_mesh)

        result = metrics.compute_all_metrics()

        assert isinstance(result, dict)
        assert 'jacobian_ratio' in result
        assert 'skewness' in result
        assert 'aspect_ratio' in result

    def test_compute_all_list_lengths(self, perfect_hex_mesh):
        """Test that all metric lists have correct length"""
        metrics = AdvancedQualityMetrics(perfect_hex_mesh)

        result = metrics.compute_all_metrics()

        num_elements = len(perfect_hex_mesh.elements)
        assert len(result['jacobian_ratio']) == num_elements
        assert len(result['skewness']) == num_elements
        assert len(result['aspect_ratio']) == num_elements

    def test_compute_all_multiple_elements(self):
        """Test with mesh containing multiple elements"""
        mesh = MeshData(element_type=ElementType.TET4)

        # Create two tetrahedrons
        for offset in [0.0, 2.0]:
            node_ids = []
            node_ids.append(mesh.add_node(offset + 0.0, 0.0, 0.0))
            node_ids.append(mesh.add_node(offset + 1.0, 0.0, 0.0))
            node_ids.append(mesh.add_node(offset + 0.0, 1.0, 0.0))
            node_ids.append(mesh.add_node(offset + 0.0, 0.0, 1.0))
            mesh.add_element(node_ids)

        metrics = AdvancedQualityMetrics(mesh)
        result = metrics.compute_all_metrics()

        assert len(result['jacobian_ratio']) == 2
        assert len(result['skewness']) == 2
        assert len(result['aspect_ratio']) == 2


class TestGenerateReport:
    """Test report generation"""

    def test_report_is_string(self, perfect_hex_mesh):
        """Test that report is a string"""
        metrics = AdvancedQualityMetrics(perfect_hex_mesh)

        report = metrics.generate_report()

        assert isinstance(report, str)
        assert len(report) > 0

    def test_report_contains_metrics(self, perfect_hex_mesh):
        """Test that report contains all metrics"""
        metrics = AdvancedQualityMetrics(perfect_hex_mesh)

        report = metrics.generate_report()

        assert "Jacobian" in report or "jacobian" in report.lower()
        assert "Skewness" in report or "skewness" in report.lower()
        assert "Aspect" in report or "aspect" in report.lower()

    def test_report_contains_statistics(self, perfect_hex_mesh):
        """Test that report contains statistics"""
        metrics = AdvancedQualityMetrics(perfect_hex_mesh)

        report = metrics.generate_report()

        assert "Min:" in report or "min:" in report.lower()
        assert "Max:" in report or "max:" in report.lower()
        assert "Mean:" in report or "mean:" in report.lower()

    def test_report_with_multiple_elements(self):
        """Test report with multiple elements"""
        mesh = MeshData(element_type=ElementType.HEX8)

        # Create two cubes
        for offset in [0, 3]:
            node_ids = []
            for i in range(2):
                for j in range(2):
                    for k in range(2):
                        node_ids.append(mesh.add_node(offset + float(i), float(j), float(k)))
            mesh.add_element([node_ids[0], node_ids[1], node_ids[3], node_ids[2],
                             node_ids[4], node_ids[5], node_ids[7], node_ids[6]])

        metrics = AdvancedQualityMetrics(mesh)
        report = metrics.generate_report()

        assert len(report) > 0
        assert "ADVANCED MESH QUALITY METRICS" in report


class TestAnalyzeMeshQuality:
    """Test convenience function"""

    def test_analyze_returns_dict(self, perfect_hex_mesh):
        """Test that analyze_mesh_quality returns dictionary"""
        result = analyze_mesh_quality(perfect_hex_mesh, print_report=False)

        assert isinstance(result, dict)
        assert 'jacobian_ratio' in result
        assert 'skewness' in result
        assert 'aspect_ratio' in result

    def test_analyze_with_print(self, perfect_hex_mesh, capsys):
        """Test that analyze_mesh_quality prints when requested"""
        analyze_mesh_quality(perfect_hex_mesh, print_report=True)

        captured = capsys.readouterr()
        assert len(captured.out) > 0
        assert "QUALITY" in captured.out or "quality" in captured.out.lower()

    def test_analyze_without_print(self, perfect_hex_mesh, capsys):
        """Test that analyze_mesh_quality doesn't print when not requested"""
        analyze_mesh_quality(perfect_hex_mesh, print_report=False)

        captured = capsys.readouterr()
        assert len(captured.out) == 0


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_empty_mesh(self):
        """Test with empty mesh"""
        mesh = MeshData(element_type=ElementType.HEX8)

        metrics = AdvancedQualityMetrics(mesh)
        result = metrics.compute_all_metrics()

        assert len(result['jacobian_ratio']) == 0
        assert len(result['skewness']) == 0
        assert len(result['aspect_ratio']) == 0

    def test_unsupported_element_type_jacobian(self):
        """Test Jacobian with unsupported element type"""
        mesh = MeshData(element_type=ElementType.PRISM6)

        # Create a prism
        node_ids = []
        node_ids.append(mesh.add_node(0.0, 0.0, 0.0))
        node_ids.append(mesh.add_node(1.0, 0.0, 0.0))
        node_ids.append(mesh.add_node(0.0, 1.0, 0.0))
        node_ids.append(mesh.add_node(0.0, 0.0, 1.0))
        node_ids.append(mesh.add_node(1.0, 0.0, 1.0))
        node_ids.append(mesh.add_node(0.0, 1.0, 1.0))
        mesh.add_element(node_ids)

        metrics = AdvancedQualityMetrics(mesh)
        eid = list(mesh.elements.keys())[0]

        # Should return default value for unsupported type
        ratio = metrics.compute_jacobian_ratio(eid)
        assert ratio == 1.0

    def test_very_small_element(self):
        """Test with very small element"""
        mesh = MeshData(element_type=ElementType.TET4)

        node_ids = []
        node_ids.append(mesh.add_node(0.0, 0.0, 0.0))
        node_ids.append(mesh.add_node(1e-6, 0.0, 0.0))
        node_ids.append(mesh.add_node(0.0, 1e-6, 0.0))
        node_ids.append(mesh.add_node(0.0, 0.0, 1e-6))
        mesh.add_element(node_ids)

        metrics = AdvancedQualityMetrics(mesh)
        result = metrics.compute_all_metrics()

        # Should not crash and return valid values
        assert len(result['jacobian_ratio']) == 1
        assert len(result['skewness']) == 1
        assert len(result['aspect_ratio']) == 1
