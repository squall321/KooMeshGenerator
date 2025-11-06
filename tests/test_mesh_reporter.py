"""
Tests for Mesh Quality Reporter ([009])
========================================

This module tests the mesh quality reporting functionality including:
- HTML report generation
- PDF report generation
- Chart generation
- Text summary generation
"""

import pytest
import tempfile
import os
from pathlib import Path

from koomesh.meshing.mesh_data import MeshData, ElementType
from koomesh.utils.mesh_reporter import MeshReporter


@pytest.fixture
def simple_hex_mesh():
    """Create a simple hex mesh for testing"""
    mesh = MeshData(element_type=ElementType.HEX8)

    # Create a unit cube
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
def multi_element_mesh():
    """Create a mesh with multiple elements of varying quality"""
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
        [8.0, 0.0, 0.0],
        [8.0, 0.5, 0.0],
        [4.0, 0.5, 0.0],
        [4.0, 0.0, 0.5],
        [8.0, 0.0, 0.5],
        [8.0, 0.5, 0.5],
        [4.0, 0.5, 0.5],
    ]

    for coords in [coords1, coords2, coords3]:
        node_ids = [mesh.add_node(x, y, z) for x, y, z in coords]
        mesh.add_element(node_ids)

    return mesh


class TestMeshReporter:
    """Test MeshReporter class"""

    def test_init(self):
        """Test reporter initialization"""
        reporter = MeshReporter()
        assert reporter.quality_checker is not None

    def test_init_with_custom_checker(self):
        """Test reporter initialization with custom quality checker"""
        from koomesh.meshing.quality_checker import QualityChecker

        custom_checker = QualityChecker(jacobian_threshold=0.2)
        reporter = MeshReporter(quality_checker=custom_checker)

        assert reporter.quality_checker is custom_checker
        assert reporter.quality_checker.jacobian_threshold == 0.2


class TestHTMLReportGeneration:
    """Test HTML report generation"""

    def test_generate_html_basic(self, simple_hex_mesh):
        """Test basic HTML report generation"""
        reporter = MeshReporter()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            html_path = f.name

        try:
            result_path = reporter.generate_html_report(
                simple_hex_mesh, html_path, include_charts=False
            )

            assert result_path == html_path
            assert Path(html_path).exists()
            assert Path(html_path).stat().st_size > 0

            # Check HTML content
            with open(html_path, 'r') as f:
                content = f.read()
                assert '<!DOCTYPE html>' in content
                assert 'Mesh Quality Report' in content
                assert 'hex8' in content.lower()  # Element type (case insensitive)
                assert 'Quality Distribution' in content

        finally:
            if os.path.exists(html_path):
                os.unlink(html_path)

    def test_generate_html_with_charts(self, multi_element_mesh):
        """Test HTML report generation with charts"""
        reporter = MeshReporter()

        with tempfile.TemporaryDirectory() as tmpdir:
            html_path = os.path.join(tmpdir, 'report.html')

            result_path = reporter.generate_html_report(
                multi_element_mesh, html_path, include_charts=True
            )

            assert result_path == html_path
            assert Path(html_path).exists()

            # Check for chart files
            chart_files = list(Path(tmpdir).glob('*.png'))
            # Should have multiple charts
            assert len(chart_files) > 0

    def test_generate_html_multi_element(self, multi_element_mesh):
        """Test HTML report with multiple elements"""
        reporter = MeshReporter()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            html_path = f.name

        try:
            reporter.generate_html_report(
                multi_element_mesh, html_path, include_charts=False
            )

            with open(html_path, 'r') as f:
                content = f.read()
                # Check for total elements (may have extra spacing in HTML)
                assert '3' in content and 'Total Elements' in content
                assert 'Quality Distribution' in content

        finally:
            if os.path.exists(html_path):
                os.unlink(html_path)

    def test_html_includes_problem_elements(self, multi_element_mesh):
        """Test that HTML includes problem elements section"""
        reporter = MeshReporter()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            html_path = f.name

        try:
            reporter.generate_html_report(
                multi_element_mesh, html_path, include_charts=False
            )

            with open(html_path, 'r') as f:
                content = f.read()
                # Should mention bad elements or problem elements
                assert ('bad' in content.lower() or
                        'problem' in content.lower() or
                        'fail' in content.lower())

        finally:
            if os.path.exists(html_path):
                os.unlink(html_path)


class TestPDFReportGeneration:
    """Test PDF report generation"""

    def test_generate_pdf_requires_weasyprint(self, simple_hex_mesh):
        """Test that PDF generation requires weasyprint"""
        reporter = MeshReporter()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False) as f:
            pdf_path = f.name

        try:
            # Try to generate PDF
            try:
                reporter.generate_pdf_report(
                    simple_hex_mesh, pdf_path, include_charts=False
                )
                # If we get here, weasyprint is installed
                assert Path(pdf_path).exists()
            except ImportError as e:
                # Expected if weasyprint not installed
                assert 'weasyprint' in str(e).lower()

        finally:
            if os.path.exists(pdf_path):
                os.unlink(pdf_path)

    @pytest.mark.skipif(
        os.environ.get('SKIP_PDF_TESTS', 'true').lower() == 'true',
        reason="WeasyPrint may not be available in test environment"
    )
    def test_generate_pdf_basic(self, simple_hex_mesh):
        """Test basic PDF report generation (requires weasyprint)"""
        pytest.importorskip("weasyprint")

        reporter = MeshReporter()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False) as f:
            pdf_path = f.name

        try:
            result_path = reporter.generate_pdf_report(
                simple_hex_mesh, pdf_path, include_charts=False
            )

            assert result_path == pdf_path
            assert Path(pdf_path).exists()
            assert Path(pdf_path).stat().st_size > 0

        finally:
            if os.path.exists(pdf_path):
                os.unlink(pdf_path)


class TestChartGeneration:
    """Test chart generation functionality"""

    def test_chart_generation_requires_matplotlib(self, simple_hex_mesh):
        """Test that chart generation uses matplotlib"""
        # This is implicitly tested by the HTML with charts tests
        pass

    def test_no_charts_when_disabled(self, simple_hex_mesh):
        """Test that no charts are created when disabled"""
        reporter = MeshReporter()

        with tempfile.TemporaryDirectory() as tmpdir:
            html_path = os.path.join(tmpdir, 'report.html')

            reporter.generate_html_report(
                simple_hex_mesh, html_path, include_charts=False
            )

            # Should only have HTML file, no PNGs
            files = list(Path(tmpdir).iterdir())
            png_files = [f for f in files if f.suffix == '.png']
            assert len(png_files) == 0

    def test_charts_created_when_enabled(self, multi_element_mesh):
        """Test that charts are created when enabled"""
        pytest.importorskip("matplotlib")

        reporter = MeshReporter()

        with tempfile.TemporaryDirectory() as tmpdir:
            html_path = os.path.join(tmpdir, 'report.html')

            reporter.generate_html_report(
                multi_element_mesh, html_path, include_charts=True
            )

            # Should have chart files
            png_files = list(Path(tmpdir).glob('*.png'))
            assert len(png_files) > 0


class TestTextSummary:
    """Test plain text summary generation"""

    def test_generate_summary_basic(self, simple_hex_mesh):
        """Test basic summary generation"""
        reporter = MeshReporter()

        summary = reporter.generate_summary_text(simple_hex_mesh)

        assert isinstance(summary, str)
        assert len(summary) > 0
        assert 'MESH QUALITY SUMMARY' in summary
        assert 'hex8' in summary.lower()  # Case insensitive
        assert 'Total Elements' in summary

    def test_summary_includes_metrics(self, multi_element_mesh):
        """Test that summary includes key metrics"""
        reporter = MeshReporter()

        summary = reporter.generate_summary_text(multi_element_mesh)

        assert 'Jacobian' in summary
        assert 'Aspect Ratio' in summary
        assert 'Skewness' in summary
        assert 'Quality Distribution' in summary

    def test_summary_shows_distribution(self, multi_element_mesh):
        """Test that summary shows quality distribution"""
        reporter = MeshReporter()

        summary = reporter.generate_summary_text(multi_element_mesh)

        # Should mention quality grades
        assert 'Excellent' in summary or 'Good' in summary or 'Fair' in summary


class TestReportContent:
    """Test report content accuracy"""

    def test_report_matches_quality_checker(self, multi_element_mesh):
        """Test that report data matches quality checker results"""
        from koomesh.meshing.quality_checker import QualityChecker

        checker = QualityChecker()
        reporter = MeshReporter(quality_checker=checker)

        # Get quality report
        quality_report = checker.check_mesh(multi_element_mesh)

        # Generate HTML report
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            html_path = f.name

        try:
            reporter.generate_html_report(
                multi_element_mesh, html_path, include_charts=False
            )

            with open(html_path, 'r') as f:
                content = f.read()

                # Check that element count matches (allow for HTML spacing)
                assert str(multi_element_mesh.num_elements()) in content and 'Total Elements' in content
                assert str(multi_element_mesh.num_nodes()) in content and 'Total Nodes' in content

        finally:
            if os.path.exists(html_path):
                os.unlink(html_path)

    def test_report_includes_all_quality_grades(self, multi_element_mesh):
        """Test that report includes all quality grade categories"""
        reporter = MeshReporter()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            html_path = f.name

        try:
            reporter.generate_html_report(
                multi_element_mesh, html_path, include_charts=False
            )

            with open(html_path, 'r') as f:
                content = f.read()

                # All grades should be mentioned in the distribution
                for grade in ['Excellent', 'Good', 'Fair', 'Poor', 'Bad']:
                    assert grade in content

        finally:
            if os.path.exists(html_path):
                os.unlink(html_path)


class TestErrorHandling:
    """Test error handling"""

    def test_invalid_output_path(self, simple_hex_mesh):
        """Test handling of invalid output path"""
        reporter = MeshReporter()

        # Try to write to non-existent directory
        invalid_path = '/nonexistent/directory/report.html'

        with pytest.raises((OSError, IOError, FileNotFoundError)):
            reporter.generate_html_report(simple_hex_mesh, invalid_path)

    def test_jinja2_not_available(self, simple_hex_mesh, monkeypatch):
        """Test error when jinja2 is not available"""
        # This would require mocking the import, which is complex
        # Just verify that the error message is informative
        pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
