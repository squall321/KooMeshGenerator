"""
Interactive Mesh Viewer
=======================

PyVista-based interactive 3D mesh visualization with quality metrics display.

Features:
---------
- Interactive rotation, zoom, pan
- Quality metric color mapping (aspect ratio, Jacobian, min angle, etc.)
- Multiple camera presets (isometric, front, side, top)
- Screenshot and VTK export
- Boundary visualization
- Material property display

Author: KooMeshGenerator Team
"""

import logging
from typing import Optional, List, Dict, Tuple, Union
from pathlib import Path
import numpy as np

try:
    import pyvista as pv
except ImportError:
    raise ImportError(
        "PyVista is required for mesh visualization. "
        "Install it with: pip install pyvista"
    )

from koomesh.meshing.mesh_data import MeshData

logger = logging.getLogger(__name__)


class MeshViewer:
    """
    Interactive 3D mesh viewer using PyVista.

    Provides interactive visualization of FE meshes with quality metrics,
    boundary conditions, and material properties.

    Attributes:
        plotter: PyVista plotter object for rendering
        mesh_data: Current MeshData being visualized
        show_edges: Display mesh edges
        color_map: ColorMap for quality visualization

    Example:
        >>> from koomesh.visualization import MeshViewer
        >>> viewer = MeshViewer()
        >>> viewer.show_mesh(mesh_data, show_edges=True)
        >>> viewer.show()
    """

    def __init__(
        self,
        window_size: Tuple[int, int] = (1024, 768),
        theme: str = 'document',
        off_screen: bool = False
    ):
        """
        Initialize mesh viewer.

        Parameters:
            window_size: Window size (width, height) in pixels
            theme: PyVista theme ('document', 'dark', 'paraview')
            off_screen: Render off-screen (for batch processing)
        """
        self.window_size = window_size
        self.theme = theme
        self.off_screen = off_screen

        # Set PyVista theme
        pv.set_plot_theme(theme)

        # Initialize plotter
        self.plotter: Optional[pv.Plotter] = None
        self.mesh_data: Optional[MeshData] = None
        self.pv_mesh: Optional[pv.UnstructuredGrid] = None

        # Visualization settings
        self.show_edges = True
        self.edge_color = 'black'
        self.color_map = 'coolwarm'

        logger.info(f"MeshViewer initialized: {window_size[0]}x{window_size[1]}, theme={theme}")

    def _create_plotter(self) -> pv.Plotter:
        """Create PyVista plotter with standard settings."""
        plotter = pv.Plotter(
            window_size=self.window_size,
            off_screen=self.off_screen
        )

        # Add standard features
        plotter.add_axes()
        plotter.show_grid()

        return plotter

    def _mesh_data_to_pyvista(self, mesh_data: MeshData) -> pv.UnstructuredGrid:
        """
        Convert MeshData to PyVista UnstructuredGrid.

        Parameters:
            mesh_data: Input mesh data

        Returns:
            PyVista unstructured grid
        """
        from koomesh.meshing.mesh_data import ElementType

        # Convert nodes to numpy array (from dict of Node objects)
        # Create node ID to index mapping (VTK uses 0-based indexing)
        node_id_to_index = {}
        node_coords = []

        for idx, (node_id, node) in enumerate(sorted(mesh_data.nodes.items())):
            node_id_to_index[node_id] = idx
            node_coords.append([node.x, node.y, node.z])

        nodes = np.array(node_coords)

        # Build element connectivity
        cells = []
        cell_types = []

        # Map ElementType to VTK cell types
        vtk_cell_type_map = {
            ElementType.TET4: pv.CellType.TETRA,
            ElementType.TET10: pv.CellType.QUADRATIC_TETRA,
            ElementType.HEX8: pv.CellType.HEXAHEDRON,
            ElementType.HEX20: pv.CellType.QUADRATIC_HEXAHEDRON,
            ElementType.HEX27: pv.CellType.QUADRATIC_HEXAHEDRON,
            ElementType.PRISM6: pv.CellType.WEDGE,
            ElementType.PYRAMID5: pv.CellType.PYRAMID,
        }

        for elem_id, element in mesh_data.elements.items():
            # Get number of nodes
            n_nodes = len(element.nodes)

            # Convert node IDs to VTK indices (0-based)
            vtk_connectivity = [node_id_to_index[nid] for nid in element.nodes]

            # Build cell: [num_nodes, node1, node2, ...]
            cell = [n_nodes] + vtk_connectivity
            cells.extend(cell)

            # Get VTK cell type
            cell_type = vtk_cell_type_map.get(element.type, pv.CellType.TETRA)
            cell_types.append(cell_type)

        # Create PyVista mesh
        cells = np.array(cells)
        cell_types = np.array(cell_types)

        pv_mesh = pv.UnstructuredGrid(cells, cell_types, nodes)

        logger.info(f"Converted MeshData to PyVista: {len(nodes)} nodes, {len(mesh_data.elements)} elements")

        return pv_mesh

    def show_mesh(
        self,
        mesh_data: MeshData,
        show_edges: bool = True,
        color: str = 'lightblue',
        opacity: float = 1.0,
        reset_camera: bool = True
    ):
        """
        Display mesh in viewer.

        Parameters:
            mesh_data: Mesh to visualize
            show_edges: Show element edges
            color: Mesh color (if no quality data)
            opacity: Mesh opacity (0.0 to 1.0)
            reset_camera: Reset camera to default view
        """
        self.mesh_data = mesh_data
        self.show_edges = show_edges

        # Convert to PyVista mesh
        self.pv_mesh = self._mesh_data_to_pyvista(mesh_data)

        # Create or reset plotter
        if self.plotter is None:
            self.plotter = self._create_plotter()
        else:
            self.plotter.clear()

        # Add mesh to scene
        self.plotter.add_mesh(
            self.pv_mesh,
            color=color,
            show_edges=show_edges,
            edge_color=self.edge_color,
            opacity=opacity,
            lighting=True
        )

        if reset_camera:
            self.plotter.reset_camera()

        logger.info(f"Displayed mesh: {len(mesh_data.nodes)} nodes, {len(mesh_data.elements)} elements")

    def show_quality(
        self,
        mesh_data: Optional[MeshData] = None,
        metric: str = 'aspect_ratio',
        show_edges: bool = True,
        color_map: str = 'coolwarm',
        show_scalar_bar: bool = True
    ):
        """
        Display mesh with quality metric color mapping.

        Parameters:
            mesh_data: Mesh to visualize (uses current if None)
            metric: Quality metric name ('aspect_ratio', 'min_angle', 'max_angle', 'jacobian', 'volume')
            show_edges: Show element edges
            color_map: Matplotlib colormap name
            show_scalar_bar: Show color scale bar
        """
        if mesh_data is not None:
            self.mesh_data = mesh_data
            self.pv_mesh = self._mesh_data_to_pyvista(mesh_data)

        if self.mesh_data is None:
            raise ValueError("No mesh data available. Call show_mesh() first.")

        # Compute element-wise quality metrics
        from koomesh.meshing.quality_checker import QualityChecker
        from koomesh.meshing.mesh_data import Element

        quality_checker = QualityChecker()

        # Compute metric for each element (in sorted order to match PyVista cells)
        metric_values = []

        for elem_id in sorted(self.mesh_data.elements.keys()):
            element = self.mesh_data.elements[elem_id]

            # Compute quality metric for this element
            if metric == 'aspect_ratio':
                value = quality_checker._compute_aspect_ratio(element, self.mesh_data)
            elif metric == 'jacobian':
                value = quality_checker._compute_jacobian(element, self.mesh_data)
            elif metric == 'skewness':
                value = quality_checker._compute_skewness(element, self.mesh_data)
            elif metric == 'volume':
                # Get node coordinates
                coords = np.array([
                    self.mesh_data.nodes[nid].coordinates()
                    for nid in element.nodes
                ])
                value = quality_checker._compute_volume(coords)
            else:
                raise ValueError(f"Unknown quality metric: {metric}. Supported: 'aspect_ratio', 'jacobian', 'skewness', 'volume'")

            metric_values.append(value)

        metric_values = np.array(metric_values)

        # Add metric as cell data
        self.pv_mesh.cell_data[metric] = metric_values

        # Create or reset plotter
        if self.plotter is None:
            self.plotter = self._create_plotter()
        else:
            self.plotter.clear()

        # Add mesh with quality coloring
        self.plotter.add_mesh(
            self.pv_mesh,
            scalars=metric,
            cmap=color_map,
            show_edges=show_edges,
            edge_color=self.edge_color,
            show_scalar_bar=show_scalar_bar,
            scalar_bar_args={
                'title': metric.replace('_', ' ').title(),
                'n_labels': 5,
                'fmt': '%.2f'
            }
        )

        self.plotter.reset_camera()

        logger.info(f"Displayed quality metric '{metric}': min={metric_values.min():.3f}, max={metric_values.max():.3f}, mean={metric_values.mean():.3f}")

    def show_boundary(
        self,
        show_surface: bool = True,
        surface_color: str = 'lightgreen',
        surface_opacity: float = 0.5
    ):
        """
        Display mesh boundary surface.

        Parameters:
            show_surface: Show surface mesh
            surface_color: Surface color
            surface_opacity: Surface opacity
        """
        if self.pv_mesh is None:
            raise ValueError("No mesh loaded. Call show_mesh() first.")

        # Extract surface
        surface = self.pv_mesh.extract_surface()

        # Create or reset plotter
        if self.plotter is None:
            self.plotter = self._create_plotter()
        else:
            self.plotter.clear()

        # Add volume mesh (wireframe)
        self.plotter.add_mesh(
            self.pv_mesh,
            color='gray',
            style='wireframe',
            opacity=0.3
        )

        # Add surface
        if show_surface:
            self.plotter.add_mesh(
                surface,
                color=surface_color,
                opacity=surface_opacity,
                show_edges=True,
                edge_color='black'
            )

        self.plotter.reset_camera()

        logger.info(f"Displayed boundary: {surface.n_points} surface nodes, {surface.n_cells} surface faces")

    def set_camera_view(self, view: str = 'isometric'):
        """
        Set camera to predefined view.

        Parameters:
            view: View name ('isometric', 'front', 'back', 'left', 'right', 'top', 'bottom')
        """
        if self.plotter is None:
            raise ValueError("No plotter initialized. Call show_mesh() first.")

        view_map = {
            'isometric': (1, 1, 1),
            'front': (0, 0, 1),
            'back': (0, 0, -1),
            'left': (-1, 0, 0),
            'right': (1, 0, 0),
            'top': (0, 1, 0),
            'bottom': (0, -1, 0)
        }

        if view not in view_map:
            raise ValueError(f"Unknown view '{view}'. Choose from: {list(view_map.keys())}")

        self.plotter.view_vector(view_map[view])

        logger.debug(f"Set camera view: {view}")

    def screenshot(self, filename: Union[str, Path], transparent_background: bool = False):
        """
        Save screenshot to file.

        Parameters:
            filename: Output file path (.png, .jpg, .tiff)
            transparent_background: Use transparent background
        """
        if self.plotter is None:
            raise ValueError("No plotter initialized. Call show_mesh() first.")

        filename = Path(filename)
        filename.parent.mkdir(parents=True, exist_ok=True)

        self.plotter.screenshot(
            str(filename),
            transparent_background=transparent_background
        )

        logger.info(f"Screenshot saved: {filename}")

    def export_vtk(self, filename: Union[str, Path]):
        """
        Export mesh to VTK file.

        Parameters:
            filename: Output VTK file path (.vtu, .vtk)
        """
        if self.pv_mesh is None:
            raise ValueError("No mesh loaded. Call show_mesh() first.")

        filename = Path(filename)
        filename.parent.mkdir(parents=True, exist_ok=True)

        self.pv_mesh.save(str(filename))

        logger.info(f"VTK file exported: {filename}")

    def show(self):
        """Display the viewer window (blocking)."""
        if self.plotter is None:
            raise ValueError("No plotter initialized. Call show_mesh() first.")

        logger.info("Displaying viewer window...")
        self.plotter.show()

    def close(self):
        """Close the viewer window."""
        if self.plotter is not None:
            self.plotter.close()
            logger.info("Viewer closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close viewer."""
        self.close()


def quick_view(
    mesh_data: MeshData,
    quality_metric: Optional[str] = None,
    show_edges: bool = True,
    window_size: Tuple[int, int] = (1024, 768)
):
    """
    Quick mesh visualization helper.

    Parameters:
        mesh_data: Mesh to visualize
        quality_metric: Optional quality metric to display
        show_edges: Show element edges
        window_size: Window size (width, height)

    Example:
        >>> from koomesh.visualization import quick_view
        >>> quick_view(mesh_data, quality_metric='aspect_ratio')
    """
    viewer = MeshViewer(window_size=window_size)

    if quality_metric:
        viewer.show_quality(mesh_data, metric=quality_metric, show_edges=show_edges)
    else:
        viewer.show_mesh(mesh_data, show_edges=show_edges)

    viewer.show()
