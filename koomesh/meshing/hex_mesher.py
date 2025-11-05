"""
Hexahedral Mesh Generator
==========================

This module provides functionality to generate structured hexahedral meshes.

Features:
- Box mesh generation
- Cylinder mesh generation
- Sweepable geometry meshing
- Transfinite meshing for structured grids

Usage:
    >>> from koomesh.meshing.hex_mesher import HexMesher
    >>> mesher = HexMesher(mesh_size=1.0)
    >>> mesh = mesher.mesh_box(shape)
"""

import logging
from typing import Optional, Tuple, List
import numpy as np

try:
    from OCC.Core.TopoDS import TopoDS_Shape
    from OCC.Core.BRepBndLib import brepbndlib
    from OCC.Core.Bnd import Bnd_Box
    from OCC.Core.GProp import GProp_GProps
    from OCC.Core.BRepGProp import brepgprop_VolumeProperties
    PYTHONOCC_AVAILABLE = True
except ImportError:
    PYTHONOCC_AVAILABLE = False
    TopoDS_Shape = object

from koomesh.meshing.mesh_data import MeshData, ElementType
from koomesh.meshing.gmsh_utils import GmshWrapper, GmshError


class HexMesher:
    """
    Hexahedral mesh generator

    This class generates structured hexahedral meshes for suitable geometries:
    - Simple boxes
    - Simple cylinders
    - Sweepable geometries (extrusions)

    Attributes:
        mesh_size: Target element size
        logger: Logger instance

    Example:
        >>> mesher = HexMesher(mesh_size=1.0)
        >>> mesh = mesher.mesh_box(box_shape)
        >>> print(f"Generated {mesh.num_elements()} hex elements")
    """

    def __init__(self, mesh_size: float = 1.0):
        """
        Initialize hexahedral mesher

        Args:
            mesh_size: Target mesh element size
        """
        self.mesh_size = mesh_size
        self.logger = logging.getLogger(__name__)

        if not PYTHONOCC_AVAILABLE:
            self.logger.warning("PythonOCC not available")

    def mesh_box(self, shape: TopoDS_Shape,
                 divisions: Optional[Tuple[int, int, int]] = None) -> MeshData:
        """
        Generate hexahedral mesh for box geometry

        Args:
            shape: Box-shaped TopoDS_Shape
            divisions: Optional (nx, ny, nz) divisions

        Returns:
            MeshData with hexahedral mesh

        Example:
            >>> mesh = mesher.mesh_box(box_shape, divisions=(10, 10, 10))
        """
        if not PYTHONOCC_AVAILABLE:
            raise RuntimeError("PythonOCC is required for meshing")

        self.logger.info("Generating hexahedral mesh for box geometry")

        # Get bounding box
        bbox = Bnd_Box()
        brepbndlib.Add(shape, bbox)
        xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()

        dimensions = (xmax - xmin, ymax - ymin, zmax - zmin)
        self.logger.debug(f"Box dimensions: {dimensions}")

        # Calculate divisions if not provided
        if divisions is None:
            nx = max(2, int(dimensions[0] / self.mesh_size))
            ny = max(2, int(dimensions[1] / self.mesh_size))
            nz = max(2, int(dimensions[2] / self.mesh_size))
            divisions = (nx, ny, nz)

        self.logger.debug(f"Mesh divisions: {divisions}")

        # Use GMSH for meshing
        try:
            with GmshWrapper() as gmsh_wrapper:
                gmsh_wrapper.new_model("box_mesh")

                # Import shape
                shape_tag = gmsh_wrapper.import_occ_shape(shape)

                # Set mesh size
                gmsh_wrapper.set_mesh_size(self.mesh_size)

                # Enable recombination for hex mesh
                gmsh_wrapper.set_recombine(True)

                # Set transfinite meshing for structured grid
                gmsh_wrapper.set_transfinite(shape_tag)

                # Generate mesh
                gmsh_wrapper.generate_mesh(3)

                # Optimize
                gmsh_wrapper.optimize_mesh("Relocate3D")

                # Extract mesh
                mesh_data = gmsh_wrapper.extract_mesh(ElementType.HEX8)

                self.logger.info(
                    f"Generated box mesh: {mesh_data.num_nodes()} nodes, "
                    f"{mesh_data.num_elements()} elements"
                )

                return mesh_data

        except GmshError as e:
            self.logger.error(f"GMSH meshing failed: {e}")
            # Fallback to manual box mesh generation
            return self._generate_box_mesh_manual(dimensions, divisions)

    def _generate_box_mesh_manual(self,
                                  dimensions: Tuple[float, float, float],
                                  divisions: Tuple[int, int, int]) -> MeshData:
        """
        Generate box mesh manually (fallback method)

        Args:
            dimensions: Box dimensions (width, height, depth)
            divisions: Number of divisions (nx, ny, nz)

        Returns:
            MeshData with hexahedral mesh
        """
        self.logger.info("Generating box mesh manually")

        width, height, depth = dimensions
        nx, ny, nz = divisions

        mesh = MeshData(ElementType.HEX8)

        # Generate nodes
        dx = width / nx
        dy = height / ny
        dz = depth / nz

        # Create structured grid of nodes
        node_map = {}  # (i, j, k) -> node_id

        for k in range(nz + 1):
            for j in range(ny + 1):
                for i in range(nx + 1):
                    x = i * dx
                    y = j * dy
                    z = k * dz

                    node_id = mesh.add_node(x, y, z)
                    node_map[(i, j, k)] = node_id

        # Generate elements
        for k in range(nz):
            for j in range(ny):
                for i in range(nx):
                    # Hex8 node connectivity (in LS-DYNA order)
                    # Bottom face (z), top face (z+1)
                    nodes = [
                        node_map[(i, j, k)],         # 1
                        node_map[(i+1, j, k)],       # 2
                        node_map[(i+1, j+1, k)],     # 3
                        node_map[(i, j+1, k)],       # 4
                        node_map[(i, j, k+1)],       # 5
                        node_map[(i+1, j, k+1)],     # 6
                        node_map[(i+1, j+1, k+1)],   # 7
                        node_map[(i, j+1, k+1)],     # 8
                    ]

                    mesh.add_element(nodes)

        self.logger.info(
            f"Manual box mesh: {mesh.num_nodes()} nodes, {mesh.num_elements()} elements"
        )

        return mesh

    def mesh_cylinder(self, shape: TopoDS_Shape,
                     radial_divisions: Optional[int] = None,
                     circumferential_divisions: Optional[int] = None,
                     axial_divisions: Optional[int] = None) -> MeshData:
        """
        Generate hexahedral mesh for cylinder geometry

        Args:
            shape: Cylinder-shaped TopoDS_Shape
            radial_divisions: Number of divisions in radial direction
            circumferential_divisions: Number of divisions around circumference
            axial_divisions: Number of divisions along axis

        Returns:
            MeshData with hexahedral mesh
        """
        if not PYTHONOCC_AVAILABLE:
            raise RuntimeError("PythonOCC is required for meshing")

        self.logger.info("Generating hexahedral mesh for cylinder geometry")

        # Get bounding box for dimensions
        bbox = Bnd_Box()
        brepbndlib.Add(shape, bbox)
        xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()

        # Estimate radius and height
        radius = (xmax - xmin) / 2.0
        height = zmax - zmin

        self.logger.debug(f"Cylinder: radius={radius:.3f}, height={height:.3f}")

        # Calculate divisions if not provided
        if radial_divisions is None:
            radial_divisions = max(2, int(radius / self.mesh_size))

        if circumferential_divisions is None:
            circumferential_divisions = max(8, int(2 * np.pi * radius / self.mesh_size))

        if axial_divisions is None:
            axial_divisions = max(2, int(height / self.mesh_size))

        self.logger.debug(
            f"Cylinder divisions: r={radial_divisions}, "
            f"θ={circumferential_divisions}, z={axial_divisions}"
        )

        # Use GMSH for cylinder meshing
        try:
            with GmshWrapper() as gmsh_wrapper:
                gmsh_wrapper.new_model("cylinder_mesh")

                # Import shape
                shape_tag = gmsh_wrapper.import_occ_shape(shape)

                # Set mesh size
                gmsh_wrapper.set_mesh_size(self.mesh_size)

                # Enable recombination
                gmsh_wrapper.set_recombine(True)

                # Generate mesh
                gmsh_wrapper.generate_mesh(3)
                gmsh_wrapper.optimize_mesh()

                # Extract mesh
                mesh_data = gmsh_wrapper.extract_mesh(ElementType.HEX8)

                self.logger.info(
                    f"Generated cylinder mesh: {mesh_data.num_nodes()} nodes, "
                    f"{mesh_data.num_elements()} elements"
                )

                return mesh_data

        except GmshError as e:
            self.logger.error(f"GMSH cylinder meshing failed: {e}")
            raise

    def mesh_sweepable(self, shape: TopoDS_Shape,
                      num_layers: Optional[int] = None) -> MeshData:
        """
        Generate hexahedral mesh for sweepable geometry

        A sweepable geometry can be meshed by extruding a 2D mesh along a path.

        Args:
            shape: Sweepable TopoDS_Shape
            num_layers: Number of layers in sweep direction

        Returns:
            MeshData with hexahedral mesh
        """
        if not PYTHONOCC_AVAILABLE:
            raise RuntimeError("PythonOCC is required for meshing")

        self.logger.info("Generating hexahedral mesh for sweepable geometry")

        # Get bounding box
        bbox = Bnd_Box()
        brepbndlib.Add(shape, bbox)
        xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()

        # Estimate sweep distance (typically max dimension)
        sweep_distance = max(xmax - xmin, ymax - ymin, zmax - zmin)

        # Calculate number of layers if not provided
        if num_layers is None:
            num_layers = max(2, int(sweep_distance / self.mesh_size))

        self.logger.debug(f"Sweep layers: {num_layers}")

        # Use GMSH for sweepable meshing
        try:
            with GmshWrapper() as gmsh_wrapper:
                gmsh_wrapper.new_model("sweep_mesh")

                # Import shape
                shape_tag = gmsh_wrapper.import_occ_shape(shape)

                # Set mesh size
                gmsh_wrapper.set_mesh_size(self.mesh_size)

                # Enable recombination for hex mesh
                gmsh_wrapper.set_recombine(True)

                # Set algorithm suitable for sweeping
                gmsh_wrapper.set_algorithm("frontal", 3)

                # Generate mesh
                gmsh_wrapper.generate_mesh(3)
                gmsh_wrapper.optimize_mesh()

                # Extract mesh
                mesh_data = gmsh_wrapper.extract_mesh(ElementType.HEX8)

                self.logger.info(
                    f"Generated sweep mesh: {mesh_data.num_nodes()} nodes, "
                    f"{mesh_data.num_elements()} elements"
                )

                return mesh_data

        except GmshError as e:
            self.logger.error(f"GMSH sweep meshing failed: {e}")
            raise

    def mesh_shape(self, shape: TopoDS_Shape,
                  shape_type: str = "auto") -> MeshData:
        """
        Generate hexahedral mesh for a shape (auto-detect type)

        Args:
            shape: TopoDS_Shape to mesh
            shape_type: Shape type hint ("auto", "box", "cylinder", "sweepable")

        Returns:
            MeshData with hexahedral mesh
        """
        if shape_type == "box":
            return self.mesh_box(shape)
        elif shape_type == "cylinder":
            return self.mesh_cylinder(shape)
        elif shape_type == "sweepable":
            return self.mesh_sweepable(shape)
        else:
            # Auto-detect shape type
            from koomesh.geometry.shape_classifier import ShapeClassifier, ShapeType

            classifier = ShapeClassifier()
            result = classifier.classify(shape)

            if result.shape_type == ShapeType.BOX:
                return self.mesh_box(shape)
            elif result.shape_type == ShapeType.CYLINDER:
                return self.mesh_cylinder(shape)
            elif result.shape_type == ShapeType.SWEEPABLE:
                return self.mesh_sweepable(shape)
            else:
                # Default to generic approach
                self.logger.warning(
                    f"Shape type {result.shape_type} may not be optimal for hex meshing"
                )
                return self.mesh_sweepable(shape)

    def refine_mesh(self, mesh: MeshData, factor: int = 2) -> MeshData:
        """
        Refine hexahedral mesh

        Args:
            mesh: Input mesh to refine
            factor: Refinement factor (2 = split each element into 8)

        Returns:
            Refined MeshData
        """
        self.logger.info(f"Refining hex mesh by factor {factor}")

        # For now, return original mesh (refinement to be implemented)
        self.logger.warning("Mesh refinement not yet fully implemented")

        return mesh


def create_structured_box_mesh(width: float, height: float, depth: float,
                               nx: int, ny: int, nz: int) -> MeshData:
    """
    Create a simple structured box mesh

    This is a utility function for quick box mesh generation.

    Args:
        width, height, depth: Box dimensions
        nx, ny, nz: Number of divisions in each direction

    Returns:
        MeshData with hex8 mesh

    Example:
        >>> mesh = create_structured_box_mesh(10, 10, 10, 10, 10, 10)
        >>> print(f"Elements: {mesh.num_elements()}")
    """
    mesher = HexMesher()
    dimensions = (width, height, depth)
    divisions = (nx, ny, nz)

    return mesher._generate_box_mesh_manual(dimensions, divisions)
