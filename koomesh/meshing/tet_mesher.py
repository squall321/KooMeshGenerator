"""
Tetrahedral Mesh Generator
===========================

This module provides functionality to generate unstructured tetrahedral meshes.

Features:
- Automatic tetrahedral meshing for complex geometries
- Delaunay and Frontal algorithms
- Mesh size control
- Boundary layer meshing support

Usage:
    >>> from koomesh.meshing.tet_mesher import TetMesher
    >>> mesher = TetMesher(mesh_size=1.0)
    >>> mesh = mesher.mesh_shape(shape)
"""

import logging
from typing import Optional, List, Dict
import numpy as np

try:
    from OCP.TopoDS import TopoDS_Shape
    from OCP.BRepBndLib import BRepBndLib
    from OCP.Bnd import Bnd_Box
    PYTHONOCC_AVAILABLE = True
    USE_OCP = True
except ImportError:
    try:
        from OCC.Core.TopoDS import TopoDS_Shape
        from OCC.Core.BRepBndLib import brepbndlib as BRepBndLib
        from OCC.Core.Bnd import Bnd_Box
        PYTHONOCC_AVAILABLE = True
        USE_OCP = False
    except ImportError:
        PYTHONOCC_AVAILABLE = False
        USE_OCP = False
        TopoDS_Shape = object
        BRepBndLib = object

from koomesh.meshing.mesh_data import MeshData, ElementType
from koomesh.meshing.gmsh_utils import GmshWrapper, GmshError


class TetMesher:
    """
    Tetrahedral mesh generator

    This class generates unstructured tetrahedral meshes for arbitrary
    3D geometries using GMSH.

    Attributes:
        mesh_size: Target element size
        min_size: Minimum element size
        max_size: Maximum element size
        algorithm: Meshing algorithm ("delaunay", "frontal", "mmg3d", "hxt")
        optimize: Enable mesh optimization
        logger: Logger instance

    Example:
        >>> mesher = TetMesher(mesh_size=1.0, algorithm="delaunay")
        >>> mesh = mesher.mesh_shape(complex_shape)
        >>> print(f"Generated {mesh.num_elements()} tet elements")
    """

    def __init__(self,
                 mesh_size: float = 1.0,
                 min_size: Optional[float] = None,
                 max_size: Optional[float] = None,
                 algorithm: str = "delaunay",
                 optimize: bool = True):
        """
        Initialize tetrahedral mesher

        Args:
            mesh_size: Target mesh element size
            min_size: Minimum element size (default: mesh_size * 0.5)
            max_size: Maximum element size (default: mesh_size * 2.0)
            algorithm: Meshing algorithm
            optimize: Enable mesh optimization
        """
        self.mesh_size = mesh_size
        self.min_size = min_size if min_size is not None else mesh_size * 0.5
        self.max_size = max_size if max_size is not None else mesh_size * 2.0
        self.algorithm = algorithm
        self.optimize = optimize

        self.logger = logging.getLogger(__name__)

        if not PYTHONOCC_AVAILABLE:
            self.logger.warning("PythonOCC not available")

    def mesh_shape(self, shape: TopoDS_Shape,
                  element_order: int = 1) -> MeshData:
        """
        Generate tetrahedral mesh for arbitrary shape

        Args:
            shape: TopoDS_Shape to mesh
            element_order: Element order (1=linear, 2=quadratic)

        Returns:
            MeshData with tetrahedral mesh

        Example:
            >>> mesh = mesher.mesh_shape(shape, element_order=1)
        """
        if not PYTHONOCC_AVAILABLE:
            raise RuntimeError("PythonOCC is required for meshing")

        self.logger.info(f"Generating tetrahedral mesh with {self.algorithm} algorithm")

        # Get bounding box for info
        bbox = Bnd_Box()
        if USE_OCP:
            BRepBndLib.Add_s(shape, bbox)
        else:
            BRepBndLib.Add(shape, bbox)
        xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()
        dimensions = (xmax - xmin, ymax - ymin, zmax - zmin)

        self.logger.debug(f"Shape dimensions: {dimensions}")
        self.logger.debug(f"Mesh size: {self.mesh_size} (min: {self.min_size}, max: {self.max_size})")

        try:
            with GmshWrapper() as gmsh_wrapper:
                gmsh_wrapper.new_model("tet_mesh")

                # Import shape
                shape_tag = gmsh_wrapper.import_occ_shape(shape)

                # Set mesh size
                gmsh_wrapper.set_mesh_size(
                    self.mesh_size,
                    min_size=self.min_size,
                    max_size=self.max_size
                )

                # Set algorithm
                gmsh_wrapper.set_algorithm(self.algorithm, dimension=3)

                # Set element order
                import gmsh
                gmsh.option.setNumber("Mesh.ElementOrder", element_order)

                # Generate mesh
                gmsh_wrapper.generate_mesh(3)

                # Optimize if requested
                if self.optimize:
                    gmsh_wrapper.optimize_mesh("Netgen")

                # Get mesh statistics
                stats = gmsh_wrapper.get_mesh_statistics()
                self.logger.info(
                    f"Generated mesh: {stats['num_nodes']} nodes, "
                    f"{stats['num_elements']} elements"
                )

                if stats['quality']:
                    self.logger.info(
                        f"Quality: min={stats['quality']['min']:.3f}, "
                        f"mean={stats['quality']['mean']:.3f}"
                    )

                # Extract mesh
                element_type = ElementType.TET10 if element_order == 2 else ElementType.TET4
                mesh_data = gmsh_wrapper.extract_mesh(element_type)

                return mesh_data

        except GmshError as e:
            self.logger.error(f"GMSH meshing failed: {e}")
            raise

    def mesh_with_size_field(self, shape: TopoDS_Shape,
                            size_function) -> MeshData:
        """
        Generate tetrahedral mesh with custom size field

        Args:
            shape: TopoDS_Shape to mesh
            size_function: Function that returns mesh size for (x, y, z) point

        Returns:
            MeshData with tetrahedral mesh
        """
        self.logger.info("Generating tet mesh with custom size field")

        # This would require more advanced GMSH features
        # For now, fall back to uniform meshing
        self.logger.warning("Custom size fields not yet fully implemented")

        return self.mesh_shape(shape)

    def mesh_with_boundary_layer(self, shape: TopoDS_Shape,
                                 layer_thickness: float,
                                 num_layers: int = 3) -> MeshData:
        """
        Generate tetrahedral mesh with boundary layer

        Useful for CFD applications where fine resolution near walls is needed.

        Args:
            shape: TopoDS_Shape to mesh
            layer_thickness: Total thickness of boundary layer
            num_layers: Number of boundary layers

        Returns:
            MeshData with tetrahedral mesh and boundary layers
        """
        self.logger.info(
            f"Generating tet mesh with boundary layer: "
            f"{num_layers} layers, thickness={layer_thickness}"
        )

        try:
            with GmshWrapper() as gmsh_wrapper:
                gmsh_wrapper.new_model("tet_mesh_bl")

                # Import shape
                shape_tag = gmsh_wrapper.import_occ_shape(shape)

                # Set mesh size
                gmsh_wrapper.set_mesh_size(self.mesh_size, self.min_size, self.max_size)

                # Set algorithm
                gmsh_wrapper.set_algorithm(self.algorithm, dimension=3)

                # Configure boundary layer
                import gmsh

                # Get all surfaces for boundary layer
                surfaces = gmsh.model.getEntities(2)
                surface_tags = [tag for dim, tag in surfaces]

                # Add boundary layer field
                # Note: This is a simplified implementation
                field_id = gmsh.model.mesh.field.add("BoundaryLayer")
                gmsh.model.mesh.field.setNumbers(field_id, "FacesList", surface_tags)
                gmsh.model.mesh.field.setNumber(field_id, "Size", layer_thickness / num_layers)
                gmsh.model.mesh.field.setNumber(field_id, "Ratio", 1.2)
                gmsh.model.mesh.field.setNumber(field_id, "Quads", 0)  # Use triangles

                # Set as background field
                gmsh.model.mesh.field.setAsBackgroundMesh(field_id)

                # Generate mesh
                gmsh_wrapper.generate_mesh(3)

                if self.optimize:
                    gmsh_wrapper.optimize_mesh()

                # Extract mesh
                mesh_data = gmsh_wrapper.extract_mesh(ElementType.TET4)

                self.logger.info(
                    f"Generated boundary layer mesh: "
                    f"{mesh_data.num_nodes()} nodes, {mesh_data.num_elements()} elements"
                )

                return mesh_data

        except GmshError as e:
            self.logger.error(f"Boundary layer meshing failed: {e}")
            # Fall back to regular meshing
            return self.mesh_shape(shape)

    def mesh_multi_material(self, shapes: List[TopoDS_Shape],
                           part_ids: List[int]) -> MeshData:
        """
        Generate tetrahedral mesh for multi-material/multi-part geometry

        Args:
            shapes: List of TopoDS_Shape objects (one per material)
            part_ids: List of part IDs corresponding to shapes

        Returns:
            MeshData with tetrahedral mesh
        """
        self.logger.info(f"Generating multi-material tet mesh for {len(shapes)} parts")

        if len(shapes) != len(part_ids):
            raise ValueError("Number of shapes must match number of part IDs")

        try:
            with GmshWrapper() as gmsh_wrapper:
                gmsh_wrapper.new_model("tet_mesh_multi")

                # Import all shapes
                shape_tags = []
                for i, shape in enumerate(shapes):
                    tag = gmsh_wrapper.import_occ_shape(shape)
                    shape_tags.append(tag)
                    self.logger.debug(f"Imported shape {i+1} with tag {tag}")

                # Set mesh size
                gmsh_wrapper.set_mesh_size(self.mesh_size, self.min_size, self.max_size)

                # Set algorithm
                gmsh_wrapper.set_algorithm(self.algorithm, dimension=3)

                # Generate mesh
                gmsh_wrapper.generate_mesh(3)

                if self.optimize:
                    gmsh_wrapper.optimize_mesh()

                # Extract mesh
                mesh_data = gmsh_wrapper.extract_mesh(ElementType.TET4)

                # Assign part IDs
                # Note: This is simplified; proper implementation would
                # track which elements belong to which shape
                self.logger.warning("Part ID assignment not yet fully implemented")

                return mesh_data

        except GmshError as e:
            self.logger.error(f"Multi-material meshing failed: {e}")
            raise

    def refine_mesh(self, mesh: MeshData,
                   refinement_regions: Optional[List] = None) -> MeshData:
        """
        Refine tetrahedral mesh

        Args:
            mesh: Input mesh to refine
            refinement_regions: Optional list of regions to refine

        Returns:
            Refined MeshData
        """
        self.logger.info("Refining tetrahedral mesh")

        # For now, return original mesh (refinement to be implemented)
        self.logger.warning("Mesh refinement not yet fully implemented")

        return mesh

    def coarsen_mesh(self, mesh: MeshData, coarsening_factor: float = 0.5) -> MeshData:
        """
        Coarsen tetrahedral mesh using vertex clustering

        This method reduces the number of elements by clustering nearby vertices
        and merging them. The coarsening_factor controls how aggressive the
        coarsening is.

        Args:
            mesh: Input mesh to coarsen
            coarsening_factor: Factor by which to coarsen (0.5 = half as many elements)
                             Smaller values = more aggressive coarsening

        Returns:
            Coarsened MeshData

        Example:
            >>> coarsened = mesher.coarsen_mesh(mesh, coarsening_factor=0.3)
        """
        self.logger.info(f"Coarsening tetrahedral mesh by factor {coarsening_factor}")

        if coarsening_factor >= 1.0:
            self.logger.warning("Coarsening factor >= 1.0, returning original mesh")
            return mesh

        if mesh.num_nodes() == 0 or mesh.num_elements() == 0:
            self.logger.warning("Empty mesh, returning original")
            return mesh

        # Calculate bounding box
        coords = mesh.get_node_coordinates()
        min_coords = np.min(coords, axis=0)
        max_coords = np.max(coords, axis=0)
        bbox_size = max_coords - min_coords

        # Determine grid cell size based on coarsening factor
        # Smaller coarsening_factor -> larger cells -> more aggressive coarsening
        avg_bbox = np.mean(bbox_size)
        num_cells_per_dim = int(np.power(mesh.num_nodes() * coarsening_factor, 1/3))
        num_cells_per_dim = max(num_cells_per_dim, 2)  # At least 2 cells per dimension

        cell_size = bbox_size / num_cells_per_dim

        self.logger.debug(
            f"Grid: {num_cells_per_dim}^3 cells, "
            f"cell size: [{cell_size[0]:.3f}, {cell_size[1]:.3f}, {cell_size[2]:.3f}]"
        )

        # Assign each node to a grid cell and cluster
        node_to_cluster = {}  # Maps old node ID to cluster ID
        cluster_nodes = {}    # Maps cluster ID to list of node IDs in that cluster
        cluster_centers = {}  # Maps cluster ID to center coordinates

        for node_id, node in mesh.nodes.items():
            # Compute grid cell indices
            cell_i = int((node.x - min_coords[0]) / cell_size[0])
            cell_j = int((node.y - min_coords[1]) / cell_size[1])
            cell_k = int((node.z - min_coords[2]) / cell_size[2])

            # Handle edge case where node is exactly at max boundary
            cell_i = min(cell_i, num_cells_per_dim - 1)
            cell_j = min(cell_j, num_cells_per_dim - 1)
            cell_k = min(cell_k, num_cells_per_dim - 1)

            # Create cluster ID from cell indices
            cluster_id = (cell_i, cell_j, cell_k)

            node_to_cluster[node_id] = cluster_id

            if cluster_id not in cluster_nodes:
                cluster_nodes[cluster_id] = []
            cluster_nodes[cluster_id].append(node_id)

        # Compute cluster centers (average of all nodes in cluster)
        for cluster_id, node_ids in cluster_nodes.items():
            center = np.zeros(3)
            for nid in node_ids:
                node = mesh.nodes[nid]
                center += np.array([node.x, node.y, node.z])
            center /= len(node_ids)
            cluster_centers[cluster_id] = center

        self.logger.debug(f"Created {len(cluster_nodes)} clusters from {mesh.num_nodes()} nodes")

        # Create new mesh with clustered nodes
        new_mesh = MeshData(element_type=mesh.element_type)
        cluster_to_new_node = {}  # Maps cluster ID to new node ID

        # Add clustered nodes
        for cluster_id, center in cluster_centers.items():
            new_node_id = new_mesh.add_node(center[0], center[1], center[2])
            cluster_to_new_node[cluster_id] = new_node_id

        # Map old node IDs to new node IDs
        old_to_new_node = {}
        for old_node_id, cluster_id in node_to_cluster.items():
            old_to_new_node[old_node_id] = cluster_to_new_node[cluster_id]

        # Add elements with updated connectivity
        num_degenerate = 0
        for elem_id, elem in mesh.elements.items():
            # Map old node IDs to new node IDs
            new_node_ids = [old_to_new_node[nid] for nid in elem.nodes]

            # Check for degenerate elements (elements with duplicate nodes)
            if len(set(new_node_ids)) < len(new_node_ids):
                num_degenerate += 1
                continue  # Skip degenerate elements

            # Add element with new connectivity
            new_mesh.add_element(
                new_node_ids,
                element_type=elem.type,
                part_id=elem.part_id,
                metadata=elem.metadata.copy()
            )

        # Copy metadata
        new_mesh.metadata = mesh.metadata.copy()

        self.logger.info(
            f"Coarsening complete: {mesh.num_nodes()} -> {new_mesh.num_nodes()} nodes, "
            f"{mesh.num_elements()} -> {new_mesh.num_elements()} elements"
        )
        if num_degenerate > 0:
            self.logger.debug(f"Removed {num_degenerate} degenerate elements")

        return new_mesh


class AdaptiveTetMesher(TetMesher):
    """
    Adaptive tetrahedral mesher

    Extends TetMesher with adaptive mesh refinement capabilities.
    """

    def __init__(self, **kwargs):
        """Initialize adaptive tet mesher"""
        super().__init__(**kwargs)

    def mesh_adaptive(self, shape: TopoDS_Shape,
                     error_estimator=None,
                     max_iterations: int = 5) -> MeshData:
        """
        Generate adaptively refined tetrahedral mesh

        Args:
            shape: TopoDS_Shape to mesh
            error_estimator: Function to estimate mesh error
            max_iterations: Maximum refinement iterations

        Returns:
            MeshData with adaptively refined mesh
        """
        self.logger.info(f"Generating adaptive tet mesh (max {max_iterations} iterations)")

        # Start with initial mesh
        mesh = self.mesh_shape(shape)

        # Adaptive refinement loop
        for iteration in range(max_iterations):
            self.logger.debug(f"Adaptive iteration {iteration + 1}")

            # Estimate error (placeholder)
            if error_estimator is not None:
                errors = error_estimator(mesh)
                # Refine high-error regions
                # (To be implemented)

            # For now, just return initial mesh
            break

        self.logger.info(f"Adaptive meshing complete: {mesh.num_elements()} elements")

        return mesh
