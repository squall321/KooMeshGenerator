"""
Visualize Command
=================

Mesh visualization and screenshot generation CLI command.

Usage:
    koomesh visualize mesh.k --screenshot output.png
    koomesh visualize mesh.k --metric aspect_ratio --view isometric
    koomesh visualize mesh.k --export-vtk mesh.vtu

Author: KooMeshGenerator Team
"""

import click
import sys
import logging
from pathlib import Path
from typing import Optional

from koomesh.io.lsdyna_reader import LSDynaReader
from koomesh.visualization import MeshViewer

logger = logging.getLogger(__name__)


@click.command()
@click.argument('mesh_file', type=click.Path(exists=True))
@click.option(
    '--screenshot', '-s',
    type=click.Path(),
    help='Output screenshot file path'
)
@click.option(
    '--metric', '-m',
    type=click.Choice(['aspect_ratio', 'jacobian', 'skewness', 'volume', 'none'], case_sensitive=False),
    default='none',
    help='Quality metric to visualize (default: none - solid color)'
)
@click.option(
    '--view', '-v',
    type=click.Choice(['isometric', 'front', 'back', 'left', 'right', 'top', 'bottom'], case_sensitive=False),
    default='isometric',
    help='Camera view angle (default: isometric)'
)
@click.option(
    '--boundary/--no-boundary',
    default=False,
    help='Show only boundary surfaces (default: false)'
)
@click.option(
    '--export-vtk',
    type=click.Path(),
    help='Export to VTK file (.vtu format)'
)
@click.option(
    '--window-size',
    type=(int, int),
    default=(1920, 1080),
    help='Screenshot window size in pixels (default: 1920x1080)'
)
@click.option(
    '--show-edges/--no-edges',
    default=True,
    help='Show element edges (default: true)'
)
@click.option(
    '--cmap',
    type=str,
    default='rainbow',
    help='Colormap for quality metrics (default: rainbow)'
)
@click.pass_context
def visualize(
    ctx,
    mesh_file: str,
    screenshot: Optional[str],
    metric: str,
    view: str,
    boundary: bool,
    export_vtk: Optional[str],
    window_size: tuple,
    show_edges: bool,
    cmap: str
):
    """
    Visualize mesh and generate screenshots

    Creates 3D visualizations of mesh with optional quality metric
    coloring. Supports off-screen rendering for CLI environments.

    Examples:

    \b
    # Generate screenshot with default view
    koomesh visualize mesh.k --screenshot mesh.png

    \b
    # Visualize aspect ratio with isometric view
    koomesh visualize mesh.k \\
        --metric aspect_ratio \\
        --view isometric \\
        --screenshot quality.png

    \b
    # Show boundary surfaces only
    koomesh visualize mesh.k \\
        --boundary \\
        --screenshot boundary.png

    \b
    # Export to VTK format for ParaView
    koomesh visualize mesh.k --export-vtk mesh.vtu

    \b
    # High-resolution screenshot
    koomesh visualize mesh.k \\
        --screenshot hires.png \\
        --window-size 3840 2160
    """
    logger = ctx.obj.get('logger', logging.getLogger(__name__))

    try:
        # Check if PyVista is available
        try:
            import pyvista as pv
        except ImportError:
            click.echo("Error: PyVista is required for visualization", err=True)
            click.echo("Install with: pip install pyvista", err=True)
            sys.exit(1)

        # Read mesh file
        click.echo(f"Reading mesh file: {mesh_file}")
        mesh_data = _read_mesh_file(mesh_file)

        click.echo(
            f"Loaded mesh: {mesh_data.num_nodes()} nodes, "
            f"{mesh_data.num_elements()} elements"
        )

        # Create mesh viewer (off-screen for CLI)
        click.echo("Creating visualization...")
        viewer = MeshViewer(mesh_data, off_screen=True)

        # Set window size
        if screenshot and window_size != (1920, 1080):
            click.echo(f"Using window size: {window_size[0]}x{window_size[1]}")

        # Visualize based on options
        if boundary:
            click.echo("Extracting boundary surfaces...")
            _visualize_boundary(viewer, screenshot, view, window_size, show_edges)

        elif metric != 'none':
            click.echo(f"Computing {metric} quality metric...")
            _visualize_quality(viewer, metric, screenshot, view, window_size, show_edges, cmap)

        else:
            click.echo("Visualizing mesh...")
            _visualize_mesh(viewer, screenshot, view, window_size, show_edges)

        # Export VTK if requested
        if export_vtk:
            click.echo(f"Exporting to VTK format: {export_vtk}")
            viewer.export_vtk(export_vtk)
            click.echo(f"✓ VTK file exported: {export_vtk}")

        if screenshot:
            click.echo(f"✓ Screenshot saved: {screenshot}")

        click.echo("\n✓ Visualization completed")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Error during visualization: {e}")
        click.echo(f"Error: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def _read_mesh_file(filepath: str):
    """Read mesh file based on extension"""
    path = Path(filepath)
    ext = path.suffix.lower()

    if ext == '.k':
        reader = LSDynaReader()
        return reader.read_file(filepath)
    else:
        logger.warning(f"Unknown file extension {ext}, trying LS-DYNA reader")
        reader = LSDynaReader()
        return reader.read_file(filepath)


def _visualize_mesh(viewer: MeshViewer, screenshot: Optional[str], view: str, window_size: tuple, show_edges: bool):
    """Visualize mesh with solid color"""
    import pyvista as pv

    plotter = pv.Plotter(off_screen=True, window_size=window_size)

    # Add mesh
    mesh_actor = plotter.add_mesh(
        viewer.mesh,
        color='lightblue',
        show_edges=show_edges,
        edge_color='black',
        line_width=1
    )

    # Set camera view
    _set_camera_view(plotter, view)

    # Save screenshot
    if screenshot:
        plotter.screenshot(screenshot)

    plotter.close()


def _visualize_quality(
    viewer: MeshViewer,
    metric: str,
    screenshot: Optional[str],
    view: str,
    window_size: tuple,
    show_edges: bool,
    cmap: str
):
    """Visualize mesh with quality metric coloring"""
    import pyvista as pv
    from koomesh.meshing.quality_checker import QualityChecker

    # Compute quality metric for each element
    click.echo(f"Computing {metric} for all elements...")

    quality_checker = QualityChecker()
    quality_values = []

    for elem_id in sorted(viewer.mesh_data.elements.keys()):
        element = viewer.mesh_data.elements[elem_id]

        if metric == 'aspect_ratio':
            value = quality_checker._compute_aspect_ratio(element, viewer.mesh_data)
        elif metric == 'jacobian':
            value = quality_checker._compute_jacobian(element, viewer.mesh_data)
        elif metric == 'skewness':
            value = quality_checker._compute_skewness(element, viewer.mesh_data)
        elif metric == 'volume':
            value = quality_checker._compute_volume(element, viewer.mesh_data)
        else:
            value = 1.0

        quality_values.append(value)

    # Add quality data to mesh
    viewer.mesh.cell_data[metric] = quality_values

    # Create plotter
    plotter = pv.Plotter(off_screen=True, window_size=window_size)

    # Add mesh with quality coloring
    plotter.add_mesh(
        viewer.mesh,
        scalars=metric,
        show_edges=show_edges,
        edge_color='black',
        line_width=0.5,
        cmap=cmap,
        show_scalar_bar=True,
        scalar_bar_args={
            'title': metric.replace('_', ' ').title(),
            'vertical': True,
            'height': 0.7,
            'width': 0.05,
            'position_x': 0.90,
            'position_y': 0.15,
            'title_font_size': 16,
            'label_font_size': 12,
        }
    )

    # Set camera view
    _set_camera_view(plotter, view)

    # Save screenshot
    if screenshot:
        plotter.screenshot(screenshot)

    plotter.close()


def _visualize_boundary(viewer: MeshViewer, screenshot: Optional[str], view: str, window_size: tuple, show_edges: bool):
    """Visualize boundary surfaces only"""
    import pyvista as pv

    # Extract boundary
    boundary = viewer.mesh.extract_surface()

    # Create plotter
    plotter = pv.Plotter(off_screen=True, window_size=window_size)

    # Add boundary mesh
    plotter.add_mesh(
        boundary,
        color='lightgreen',
        show_edges=show_edges,
        edge_color='black',
        line_width=1
    )

    # Set camera view
    _set_camera_view(plotter, view)

    # Save screenshot
    if screenshot:
        plotter.screenshot(screenshot)

    plotter.close()


def _set_camera_view(plotter, view: str):
    """Set camera to specific view"""
    if view == 'isometric':
        plotter.view_isometric()
    elif view == 'front':
        plotter.view_yz()
    elif view == 'back':
        plotter.view_yz()
        plotter.camera.azimuth = 180
    elif view == 'left':
        plotter.view_xz()
    elif view == 'right':
        plotter.view_xz()
        plotter.camera.azimuth = 180
    elif view == 'top':
        plotter.view_xy()
    elif view == 'bottom':
        plotter.view_xy()
        plotter.camera.elevation = 180

    # Reset camera to show full scene
    plotter.reset_camera()
