"""
Mesh Quality Reporter
=====================

This module provides functionality to generate comprehensive mesh quality reports
in HTML and PDF formats.

Features:
- HTML reports with interactive charts and statistics
- PDF reports for documentation and archiving
- Quality metrics visualization
- Element-by-element analysis
- Problem element highlighting

Usage:
    >>> from koomesh.utils.mesh_reporter import MeshReporter
    >>> reporter = MeshReporter()
    >>> reporter.generate_html_report(mesh, "quality_report.html")
    >>> reporter.generate_pdf_report(mesh, "quality_report.pdf")
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict
import tempfile

import numpy as np

from koomesh.meshing.mesh_data import MeshData
from koomesh.meshing.quality_checker import QualityChecker


logger = logging.getLogger(__name__)


class MeshReporter:
    """
    Mesh quality report generator

    This class generates comprehensive quality reports in HTML and PDF formats,
    including statistics, visualizations, and element-by-element analysis.

    Example:
        >>> reporter = MeshReporter()
        >>> reporter.generate_html_report(mesh, "report.html")
        >>> reporter.generate_pdf_report(mesh, "report.pdf")
    """

    def __init__(self, quality_checker: Optional[QualityChecker] = None):
        """
        Initialize mesh reporter

        Args:
            quality_checker: Optional QualityChecker instance (creates default if None)
        """
        self.quality_checker = quality_checker or QualityChecker()
        self.logger = logging.getLogger(__name__)

    def generate_html_report(
        self,
        mesh: MeshData,
        output_path: str,
        include_charts: bool = True,
        max_bad_elements: int = 50
    ) -> str:
        """
        Generate HTML quality report

        Args:
            mesh: MeshData to analyze
            output_path: Output HTML file path
            include_charts: Whether to include quality charts
            max_bad_elements: Maximum number of bad elements to detail

        Returns:
            Path to generated HTML file
        """
        self.logger.info(f"Generating HTML quality report: {output_path}")

        # Check mesh quality
        quality_report = self.quality_checker.check_mesh(mesh)
        quality_distribution = self.quality_checker.get_quality_distribution(mesh)

        # Generate charts if requested
        charts = {}
        if include_charts:
            charts = self._generate_charts(mesh, quality_report, output_path)

        # Get element details for bad elements
        element_details = {}
        if quality_report.bad_elements:
            for elem_id in quality_report.bad_elements[:max_bad_elements]:
                try:
                    elem_report = self.quality_checker.get_element_report(elem_id, mesh)
                    element_details[elem_id] = elem_report
                except Exception as e:
                    self.logger.warning(f"Failed to get report for element {elem_id}: {e}")

        # Prepare template data
        template_data = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'mesh_info': {
                'element_type': mesh.element_type.code,
                'num_elements': mesh.num_elements(),
                'num_nodes': mesh.num_nodes(),
                'num_bad_elements': quality_report.num_bad_elements,
            },
            'quality_report': quality_report,
            'quality_distribution': quality_distribution,
            'element_details': element_details,
            'charts': charts,
        }

        # Render HTML
        html_content = self._render_html_template(template_data)

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        self.logger.info(f"HTML report generated: {output_path}")
        return output_path

    def generate_pdf_report(
        self,
        mesh: MeshData,
        output_path: str,
        include_charts: bool = True
    ) -> str:
        """
        Generate PDF quality report

        Args:
            mesh: MeshData to analyze
            output_path: Output PDF file path
            include_charts: Whether to include quality charts

        Returns:
            Path to generated PDF file
        """
        self.logger.info(f"Generating PDF quality report: {output_path}")

        try:
            from weasyprint import HTML
        except ImportError:
            raise ImportError(
                "WeasyPrint is required for PDF generation. "
                "Install with: pip install weasyprint"
            )

        # Generate HTML first
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp:
            tmp_html_path = tmp.name

        try:
            self.generate_html_report(
                mesh, tmp_html_path,
                include_charts=include_charts
            )

            # Convert HTML to PDF
            HTML(tmp_html_path).write_pdf(output_path)

            self.logger.info(f"PDF report generated: {output_path}")
            return output_path

        finally:
            # Clean up temporary HTML file
            if os.path.exists(tmp_html_path):
                os.unlink(tmp_html_path)

    def _generate_charts(
        self,
        mesh: MeshData,
        quality_report,
        output_path: str
    ) -> Dict[str, str]:
        """
        Generate quality visualization charts

        Args:
            mesh: MeshData to analyze
            quality_report: Quality report from QualityChecker
            output_path: Base output path for charts

        Returns:
            Dictionary mapping chart names to file paths
        """
        try:
            import matplotlib
            matplotlib.use('Agg')  # Non-interactive backend
            import matplotlib.pyplot as plt
        except ImportError:
            self.logger.warning("Matplotlib not available, skipping chart generation")
            return {}

        charts = {}
        output_dir = Path(output_path).parent
        base_name = Path(output_path).stem

        try:
            # 1. Quality Distribution Pie Chart
            chart_path = output_dir / f"{base_name}_quality_distribution.png"
            self._plot_quality_distribution(mesh, chart_path)
            charts['Quality Distribution'] = str(chart_path.name)

            # 2. Jacobian Histogram
            chart_path = output_dir / f"{base_name}_jacobian_hist.png"
            self._plot_metric_histogram(mesh, 'jacobian', 'Jacobian', chart_path)
            charts['Jacobian Distribution'] = str(chart_path.name)

            # 3. Aspect Ratio Histogram
            chart_path = output_dir / f"{base_name}_aspect_ratio_hist.png"
            self._plot_metric_histogram(mesh, 'aspect_ratio', 'Aspect Ratio', chart_path)
            charts['Aspect Ratio Distribution'] = str(chart_path.name)

            # 4. Skewness Histogram
            chart_path = output_dir / f"{base_name}_skewness_hist.png"
            self._plot_metric_histogram(mesh, 'skewness', 'Skewness', chart_path)
            charts['Skewness Distribution'] = str(chart_path.name)

            # 5. Metrics Box Plot
            chart_path = output_dir / f"{base_name}_metrics_boxplot.png"
            self._plot_metrics_boxplot(mesh, chart_path)
            charts['Metrics Overview'] = str(chart_path.name)

        except Exception as e:
            self.logger.error(f"Error generating charts: {e}")

        return charts

    def _plot_quality_distribution(self, mesh: MeshData, output_path: Path):
        """Plot quality grade distribution pie chart"""
        import matplotlib.pyplot as plt

        distribution = self.quality_checker.get_quality_distribution(mesh)

        # Filter out zero counts
        labels = []
        sizes = []
        colors = []
        color_map = {
            'Excellent': '#27ae60',
            'Good': '#2ecc71',
            'Fair': '#f39c12',
            'Poor': '#e67e22',
            'Bad': '#e74c3c'
        }

        for grade in ['Excellent', 'Good', 'Fair', 'Poor', 'Bad']:
            count = distribution[grade]
            if count > 0:
                labels.append(f'{grade}\n({count})')
                sizes.append(count)
                colors.append(color_map[grade])

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
               startangle=90, textprops={'fontsize': 12})
        ax.set_title('Element Quality Distribution', fontsize=16, fontweight='bold', pad=20)
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()

    def _plot_metric_histogram(self, mesh: MeshData, metric: str, title: str, output_path: Path):
        """Plot histogram for a quality metric"""
        import matplotlib.pyplot as plt

        hist_data = self.quality_checker.get_quality_histogram(mesh, metric, bins=30)
        bin_edges = np.array(hist_data['bin_edges'])
        counts = np.array(hist_data['counts'])

        # Calculate bin centers
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.bar(bin_centers, counts, width=(bin_edges[1] - bin_edges[0]) * 0.9,
               color='#3498db', edgecolor='#2c3e50', alpha=0.7)

        ax.set_xlabel(title, fontsize=12)
        ax.set_ylabel('Number of Elements', fontsize=12)
        ax.set_title(f'{title} Distribution', fontsize=16, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--')

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()

    def _plot_metrics_boxplot(self, mesh: MeshData, output_path: Path):
        """Plot box plots for multiple metrics"""
        import matplotlib.pyplot as plt

        # Collect metric values
        jacobians = []
        aspects = []
        skewnesses = []

        for elem in mesh.elements.values():
            jacobians.append(self.quality_checker._compute_jacobian(elem, mesh))
            aspects.append(self.quality_checker._compute_aspect_ratio(elem, mesh))
            skewnesses.append(self.quality_checker._compute_skewness(elem, mesh))

        fig, axes = plt.subplots(1, 3, figsize=(15, 5))

        # Jacobian
        bp = axes[0].boxplot([jacobians])
        axes[0].set_xticklabels(['Jacobian'])
        axes[0].set_ylabel('Value')
        axes[0].set_title('Jacobian', fontweight='bold')
        axes[0].grid(True, alpha=0.3)

        # Aspect Ratio
        bp = axes[1].boxplot([aspects])
        axes[1].set_xticklabels(['Aspect Ratio'])
        axes[1].set_ylabel('Value')
        axes[1].set_title('Aspect Ratio', fontweight='bold')
        axes[1].grid(True, alpha=0.3)

        # Skewness
        bp = axes[2].boxplot([skewnesses])
        axes[2].set_xticklabels(['Skewness'])
        axes[2].set_ylabel('Value')
        axes[2].set_title('Skewness', fontweight='bold')
        axes[2].grid(True, alpha=0.3)

        fig.suptitle('Quality Metrics Overview', fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()

    def _render_html_template(self, template_data: Dict) -> str:
        """
        Render HTML template with data

        Args:
            template_data: Dictionary with template variables

        Returns:
            Rendered HTML string
        """
        try:
            from jinja2 import Environment, FileSystemLoader, select_autoescape
        except ImportError:
            raise ImportError(
                "Jinja2 is required for HTML generation. "
                "Install with: pip install jinja2"
            )

        # Get template directory
        template_dir = Path(__file__).parent / 'templates'

        # Create Jinja2 environment
        env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )

        # Load and render template
        template = env.get_template('quality_report.html')
        html_content = template.render(**template_data)

        return html_content

    def generate_summary_text(self, mesh: MeshData) -> str:
        """
        Generate plain text summary of mesh quality

        Args:
            mesh: MeshData to analyze

        Returns:
            Plain text quality summary
        """
        quality_report = self.quality_checker.check_mesh(mesh)
        distribution = self.quality_checker.get_quality_distribution(mesh)

        lines = [
            "="*70,
            "MESH QUALITY SUMMARY",
            "="*70,
            "",
            f"Element Type:    {mesh.element_type.code}",
            f"Total Elements:  {mesh.num_elements()}",
            f"Total Nodes:     {mesh.num_nodes()}",
            f"Bad Elements:    {quality_report.num_bad_elements}",
            f"Status:          {'PASS' if quality_report.is_valid() else 'FAIL'}",
            "",
            "Quality Distribution:",
            "-"*70,
        ]

        for grade in ['Excellent', 'Good', 'Fair', 'Poor', 'Bad']:
            count = distribution[grade]
            percentage = (count / mesh.num_elements() * 100) if mesh.num_elements() > 0 else 0
            bar = "█" * int(percentage / 2)
            lines.append(f"{grade:10s}: {count:5d} ({percentage:5.1f}%) {bar}")

        lines.extend([
            "",
            "Key Metrics:",
            "-"*70,
            f"Jacobian:        Min={quality_report.jacobian['min']:.6f}, "
            f"Max={quality_report.jacobian['max']:.6f}, "
            f"Mean={quality_report.jacobian['mean']:.6f}",
            f"Aspect Ratio:    Min={quality_report.aspect_ratio['min']:.3f}, "
            f"Max={quality_report.aspect_ratio['max']:.3f}, "
            f"Mean={quality_report.aspect_ratio['mean']:.3f}",
            f"Skewness:        Min={quality_report.skewness['min']:.3f}, "
            f"Max={quality_report.skewness['max']:.3f}, "
            f"Mean={quality_report.skewness['mean']:.3f}",
            "",
            "="*70,
        ])

        return "\n".join(lines)
