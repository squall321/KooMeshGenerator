"""
Quality Command
===============

Mesh quality checking and reporting CLI command.

Usage:
    koomesh quality mesh.k --report html --output report.html
    koomesh quality mesh.k --report json --parallel
    koomesh quality mesh.k --report text

Author: KooMeshGenerator Team
"""

import click
import sys
import json
import logging
from pathlib import Path
from typing import Optional

from koomesh.io.lsdyna_reader import LSDynaReader
from koomesh.meshing.quality_checker import QualityChecker
from koomesh.parallel import ParallelQualityChecker
from koomesh.utils.mesh_reporter import MeshReporter

logger = logging.getLogger(__name__)


@click.command()
@click.argument('mesh_file', type=click.Path(exists=True))
@click.option(
    '--report', '-r',
    type=click.Choice(['text', 'json', 'html'], case_sensitive=False),
    default='text',
    help='Report format (default: text)'
)
@click.option(
    '--output', '-o',
    type=click.Path(),
    help='Output file path (default: stdout for text, mesh_quality.{ext} for others)'
)
@click.option(
    '--parallel/--no-parallel',
    default=False,
    help='Use parallel processing for large meshes (default: false)'
)
@click.option(
    '--threshold-aspect-ratio',
    type=float,
    default=10.0,
    help='Aspect ratio threshold for bad elements (default: 10.0)'
)
@click.option(
    '--threshold-jacobian',
    type=float,
    default=0.1,
    help='Jacobian threshold for bad elements (default: 0.1)'
)
@click.option(
    '--threshold-skewness',
    type=float,
    default=0.8,
    help='Skewness threshold for bad elements (default: 0.8)'
)
@click.option(
    '--jobs', '-j',
    type=int,
    default=-1,
    help='Number of parallel workers (default: -1 = all cores)'
)
@click.option(
    '--include-charts/--no-charts',
    default=True,
    help='Include quality charts in HTML report (default: true)'
)
@click.pass_context
def quality(
    ctx,
    mesh_file: str,
    report: str,
    output: Optional[str],
    parallel: bool,
    threshold_aspect_ratio: float,
    threshold_jacobian: float,
    threshold_skewness: float,
    jobs: int,
    include_charts: bool
):
    """
    Check mesh quality and generate reports

    Analyzes mesh quality metrics including aspect ratio, Jacobian,
    and skewness. Generates reports in text, JSON, or HTML format.

    Examples:

    \b
    # Text report to console
    koomesh quality mesh.k

    \b
    # HTML report with charts
    koomesh quality mesh.k --report html --output quality_report.html

    \b
    # JSON report for automation
    koomesh quality mesh.k --report json --output quality.json

    \b
    # Parallel processing for large meshes
    koomesh quality large_mesh.k --parallel --jobs 8
    """
    logger = ctx.obj.get('logger', logging.getLogger(__name__))

    try:
        # Read mesh file
        click.echo(f"Reading mesh file: {mesh_file}")
        mesh_data = _read_mesh_file(mesh_file)

        click.echo(
            f"Loaded mesh: {mesh_data.num_nodes()} nodes, "
            f"{mesh_data.num_elements()} elements, "
            f"type={mesh_data.element_type.code}"
        )

        # Create quality checker
        if parallel:
            click.echo(f"Using parallel quality checking with {jobs} workers...")
            checker = ParallelQualityChecker(
                n_jobs=jobs,
                aspect_ratio_threshold=threshold_aspect_ratio,
                jacobian_threshold=threshold_jacobian,
                skewness_threshold=threshold_skewness
            )
        else:
            checker = QualityChecker(
                aspect_ratio_threshold=threshold_aspect_ratio,
                jacobian_threshold=threshold_jacobian,
                skewness_threshold=threshold_skewness
            )

        # Check quality
        click.echo("Checking mesh quality...")
        quality_result = checker.check_mesh(mesh_data)

        # Generate report based on format
        if report == 'text':
            _generate_text_report(mesh_data, quality_result, output)

        elif report == 'json':
            _generate_json_report(mesh_data, quality_result, output, mesh_file)

        elif report == 'html':
            _generate_html_report(
                mesh_data,
                quality_result,
                output,
                mesh_file,
                include_charts,
                checker
            )

        # Exit with success/failure based on quality
        if quality_result.is_valid():
            click.echo("\n✓ Mesh quality check PASSED")
            sys.exit(0)
        else:
            click.echo(f"\n✗ Mesh quality check FAILED: {quality_result.num_bad_elements} bad elements")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Error during quality check: {e}")
        click.echo(f"Error: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def _read_mesh_file(filepath: str):
    """Read mesh file based on extension"""
    path = Path(filepath)
    ext = path.suffix.lower()

    if ext == '.k':
        # LS-DYNA keyword file
        reader = LSDynaReader()
        return reader.read_file(filepath)

    elif ext == '.vtk':
        # VTK file - not yet implemented
        raise NotImplementedError("VTK file reading not yet implemented")

    else:
        # Try LS-DYNA reader as default
        logger.warning(f"Unknown file extension {ext}, trying LS-DYNA reader")
        reader = LSDynaReader()
        return reader.read_file(filepath)


def _generate_text_report(mesh_data, quality_result, output_path: Optional[str]):
    """Generate plain text report"""
    reporter = MeshReporter()
    summary_text = reporter.generate_summary_text(mesh_data)

    if output_path:
        with open(output_path, 'w') as f:
            f.write(summary_text)
        click.echo(f"\n✓ Text report saved: {output_path}")
    else:
        # Print to console
        click.echo("\n" + summary_text)


def _generate_json_report(mesh_data, quality_result, output_path: Optional[str], mesh_file: str):
    """Generate JSON report"""
    # Build JSON data
    report_data = {
        'mesh_file': str(mesh_file),
        'mesh_info': {
            'element_type': mesh_data.element_type.code,
            'num_nodes': mesh_data.num_nodes(),
            'num_elements': mesh_data.num_elements(),
        },
        'quality_summary': {
            'is_valid': quality_result.is_valid(),
            'num_bad_elements': quality_result.num_bad_elements,
            'bad_elements': quality_result.bad_elements[:100] if quality_result.bad_elements else [],  # Limit to 100
        },
        'metrics': {
            'aspect_ratio': {
                'min': quality_result.aspect_ratio['min'],
                'max': quality_result.aspect_ratio['max'],
                'mean': quality_result.aspect_ratio['mean'],
                'std': quality_result.aspect_ratio['std'],
            },
            'jacobian': {
                'min': quality_result.jacobian['min'],
                'max': quality_result.jacobian['max'],
                'mean': quality_result.jacobian['mean'],
                'std': quality_result.jacobian['std'],
            },
            'skewness': {
                'min': quality_result.skewness['min'],
                'max': quality_result.skewness['max'],
                'mean': quality_result.skewness['mean'],
                'std': quality_result.skewness['std'],
            },
        },
        'quality_distribution': {}
    }

    # Add quality distribution
    try:
        from koomesh.meshing.quality_checker import QualityChecker
        checker = QualityChecker()
        distribution = checker.get_quality_distribution(mesh_data)
        report_data['quality_distribution'] = distribution
    except Exception as e:
        logger.warning(f"Could not get quality distribution: {e}")

    # Determine output path
    if output_path is None:
        output_path = Path(mesh_file).with_suffix('.quality.json')

    # Write JSON
    with open(output_path, 'w') as f:
        json.dump(report_data, f, indent=2)

    click.echo(f"\n✓ JSON report saved: {output_path}")


def _generate_html_report(
    mesh_data,
    quality_result,
    output_path: Optional[str],
    mesh_file: str,
    include_charts: bool,
    checker
):
    """Generate HTML report"""
    # Determine output path
    if output_path is None:
        output_path = Path(mesh_file).with_suffix('.quality.html')

    # Use MeshReporter to generate HTML
    reporter = MeshReporter(quality_checker=checker)

    try:
        reporter.generate_html_report(
            mesh=mesh_data,
            output_path=str(output_path),
            include_charts=include_charts
        )

        click.echo(f"\n✓ HTML report saved: {output_path}")

        if include_charts:
            click.echo("  Charts generated:")
            output_dir = Path(output_path).parent
            base_name = Path(output_path).stem
            for chart_type in ['quality_distribution', 'jacobian_hist', 'aspect_ratio_hist', 'skewness_hist', 'metrics_boxplot']:
                chart_path = output_dir / f"{base_name}_{chart_type}.png"
                if chart_path.exists():
                    click.echo(f"  - {chart_path.name}")

    except ImportError as e:
        if 'jinja2' in str(e).lower():
            click.echo("\n⚠ HTML report generation requires Jinja2", err=True)
            click.echo("Install with: pip install jinja2", err=True)
        elif 'matplotlib' in str(e).lower():
            click.echo("\n⚠ Chart generation requires matplotlib", err=True)
            click.echo("Install with: pip install matplotlib", err=True)
        else:
            raise

        sys.exit(1)
