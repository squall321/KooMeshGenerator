"""
GMSH Utility Functions
=======================

This module provides utility functions for working with GMSH mesh generator.

Features:
- Convert OCC shapes to GMSH
- Extract mesh data from GMSH
- Configure GMSH options
- Mesh quality control

Usage:
    >>> from koomesh.meshing.gmsh_utils import GmshWrapper
    >>> wrapper = GmshWrapper()
    >>> wrapper.initialize()
    >>> wrapper.import_occ_shape(shape)
    >>> wrapper.generate_mesh(3)
    >>> mesh_data = wrapper.extract_mesh()
    >>> wrapper.finalize()
"""

import tempfile
import logging
from pathlib import Path
from typing import Optional, Tuple, List, Dict
import numpy as np

# Try to import GMSH
try:
    import gmsh
    GMSH_AVAILABLE = True
except ImportError:
    GMSH_AVAILABLE = False

# Try to import OCC modules (OCP first, then fall back to PythonOCC)
try:
    from OCP.TopoDS import TopoDS_Shape
    from OCP.STEPControl import STEPControl_Writer, STEPControl_AsIs
    from OCP.IFSelect import IFSelect_RetDone
    PYTHONOCC_AVAILABLE = True
    USE_OCP = True
except ImportError:
    try:
        from OCC.Core.TopoDS import TopoDS_Shape
        from OCC.Extend.DataExchange import write_step_file
        PYTHONOCC_AVAILABLE = True
        USE_OCP = False
    except ImportError:
        PYTHONOCC_AVAILABLE = False
        USE_OCP = False
        TopoDS_Shape = object


from koomesh.meshing.mesh_data import MeshData, ElementType

# Import AMR module
try:
    from koomesh.meshing.adaptive_refiner import AdaptiveMeshRefiner
    AMR_AVAILABLE = True
except ImportError:
    AMR_AVAILABLE = False
    AdaptiveMeshRefiner = object


class GmshError(Exception):
    """Exception raised for GMSH errors"""
    pass


class GmshWrapper:
    """
    Wrapper for GMSH mesh generator

    This class provides a high-level interface to GMSH functionality,
    including geometry import, mesh generation, and data extraction.

    Example:
        >>> wrapper = GmshWrapper()
        >>> wrapper.initialize()
        >>> wrapper.import_occ_shape(shape)
        >>> wrapper.set_mesh_size(1.0)
        >>> wrapper.generate_mesh(3)  # 3D mesh
        >>> mesh = wrapper.extract_mesh()
        >>> wrapper.finalize()
    """

    def __init__(self):
        """Initialize GMSH wrapper"""
        self.logger = logging.getLogger(__name__)
        self.initialized = False
        self.model_name = "koomesh_model"

        if not GMSH_AVAILABLE:
            self.logger.error("GMSH is not installed")
            raise GmshError("GMSH is not available. Please install GMSH.")

    def initialize(self, verbose: bool = False):
        """
        Initialize GMSH

        Args:
            verbose: Enable verbose output
        """
        if self.initialized:
            self.logger.warning("GMSH already initialized")
            return

        gmsh.initialize()
        self.initialized = True

        # Set verbosity
        if not verbose:
            gmsh.option.setNumber("General.Terminal", 0)

        self.logger.debug("GMSH initialized")

    def finalize(self):
        """Finalize GMSH and clean up"""
        if self.initialized:
            gmsh.finalize()
            self.initialized = False
            self.logger.debug("GMSH finalized")

    def __enter__(self):
        """Context manager entry"""
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.finalize()

    def new_model(self, name: Optional[str] = None):
        """
        Create a new GMSH model

        Args:
            name: Model name (uses default if not provided)
        """
        if name is None:
            name = self.model_name

        gmsh.model.add(name)
        self.logger.debug(f"Created GMSH model: {name}")

    def import_occ_shape(self, shape: TopoDS_Shape) -> int:
        """
        Import OCC shape into GMSH

        Args:
            shape: TopoDS_Shape to import

        Returns:
            GMSH shape tag

        Raises:
            GmshError: If import fails
        """
        if not PYTHONOCC_AVAILABLE:
            raise GmshError("PythonOCC is not available")

        # Create temporary STEP file
        with tempfile.NamedTemporaryFile(suffix='.step', delete=False) as f:
            temp_path = f.name

        try:
            # Write shape to STEP file
            if USE_OCP:
                # Use OCP STEPControl_Writer
                writer = STEPControl_Writer()
                writer.Transfer(shape, STEPControl_AsIs)
                status = writer.Write(temp_path)
                if status != IFSelect_RetDone:
                    raise GmshError(f"Failed to write STEP file: status={status}")
            else:
                # Use PythonOCC write_step_file
                write_step_file(shape, temp_path)

            # Import into GMSH
            gmsh.model.occ.importShapes(temp_path)
            gmsh.model.occ.synchronize()

            self.logger.debug(f"Imported OCC shape from {temp_path}")

            # Get the imported shape tag
            # Typically, the first volume
            volumes = gmsh.model.occ.getEntities(3)
            if volumes:
                return volumes[0][1]
            return 0

        finally:
            # Clean up temporary file
            Path(temp_path).unlink(missing_ok=True)

    def set_mesh_size(self, size: float,
                     min_size: Optional[float] = None,
                     max_size: Optional[float] = None):
        """
        Set mesh size parameters

        Args:
            size: Target mesh size
            min_size: Minimum element size (default: size * 0.5)
            max_size: Maximum element size (default: size * 2.0)
        """
        if min_size is None:
            min_size = size * 0.5
        if max_size is None:
            max_size = size * 2.0

        gmsh.option.setNumber("Mesh.CharacteristicLengthMin", min_size)
        gmsh.option.setNumber("Mesh.CharacteristicLengthMax", max_size)
        gmsh.option.setNumber("Mesh.CharacteristicLengthFactor", 1.0)

        self.logger.debug(f"Set mesh size: {size} (min: {min_size}, max: {max_size})")

    def set_algorithm(self, algorithm: str, dimension: int = 3):
        """
        Set meshing algorithm

        Args:
            algorithm: Algorithm name
                2D: "meshadapt", "auto", "delaunay", "frontal"
                3D: "delaunay", "frontal", "mmg3d", "hxt"
            dimension: Dimension (2 or 3)
        """
        algorithm_map_2d = {
            "meshadapt": 1,
            "auto": 2,
            "delaunay": 5,
            "frontal": 6,
        }

        algorithm_map_3d = {
            "delaunay": 1,
            "frontal": 4,
            "mmg3d": 7,
            "hxt": 10,
        }

        if dimension == 2:
            algo_id = algorithm_map_2d.get(algorithm.lower(), 2)
            gmsh.option.setNumber("Mesh.Algorithm", algo_id)
        elif dimension == 3:
            algo_id = algorithm_map_3d.get(algorithm.lower(), 1)
            gmsh.option.setNumber("Mesh.Algorithm3D", algo_id)

        self.logger.debug(f"Set {dimension}D mesh algorithm: {algorithm}")

    def set_element_order(self, order: int = 1):
        """
        Set element order (1=linear, 2=quadratic)

        Args:
            order: Element order (1 or 2)

        Notes:
            Order 1: Linear elements (TET4, HEX8)
            Order 2: Quadratic elements (TET10, HEX20, HEX27)
        """
        if order not in [1, 2]:
            raise ValueError("Element order must be 1 (linear) or 2 (quadratic)")

        gmsh.option.setNumber("Mesh.ElementOrder", order)
        self.logger.debug(f"Set element order: {order} ({'quadratic' if order == 2 else 'linear'})")

    def set_recombine(self, enable: bool = True):
        """
        Enable/disable recombination (convert triangles to quads, tets to hexes)

        Args:
            enable: Enable recombination
        """
        if enable:
            gmsh.option.setNumber("Mesh.RecombineAll", 1)
            gmsh.option.setNumber("Mesh.Recombine3DAll", 1)
            self.logger.debug("Enabled mesh recombination")
        else:
            gmsh.option.setNumber("Mesh.RecombineAll", 0)
            gmsh.option.setNumber("Mesh.Recombine3DAll", 0)
            self.logger.debug("Disabled mesh recombination")

    def set_transfinite(self, volume_tag: int, num_layers: Optional[int] = None):
        """
        Set transfinite meshing for structured hex mesh

        Args:
            volume_tag: Volume to mesh
            num_layers: Number of layers (auto if not provided)
        """
        # Get surfaces of volume
        surfaces = gmsh.model.getBoundary([(3, volume_tag)], combined=False)

        # Set transfinite on all surfaces
        for dim, tag in surfaces:
            gmsh.model.mesh.setTransfiniteSurface(tag)

        # Set transfinite on volume
        gmsh.model.mesh.setTransfiniteVolume(volume_tag)

        # Recombine to get quads/hexes
        for dim, tag in surfaces:
            gmsh.model.mesh.setRecombine(2, tag)

        self.logger.debug(f"Set transfinite meshing for volume {volume_tag}")

    def set_adaptive_refinement(self, refiner: 'AdaptiveMeshRefiner'):
        """
        Apply adaptive mesh refinement

        Args:
            refiner: AdaptiveMeshRefiner object with configured zones

        Example:
            >>> from koomesh.meshing.adaptive_refiner import AdaptiveMeshRefiner, BoxZone
            >>> refiner = AdaptiveMeshRefiner(base_mesh_size=1.0)
            >>> refiner.add_refinement_zone(BoxZone((5, 5, 5), (2, 2, 2), 0.1))
            >>> wrapper.set_adaptive_refinement(refiner)
        """
        if not AMR_AVAILABLE:
            raise GmshError("Adaptive refinement module not available")

        refiner.apply_to_gmsh()
        self.logger.info("Applied adaptive mesh refinement")

    def generate_mesh(self, dimension: int = 3):
        """
        Generate mesh

        Args:
            dimension: Mesh dimension (1=1D, 2=2D, 3=3D)
        """
        self.logger.info(f"Generating {dimension}D mesh...")
        gmsh.model.mesh.generate(dimension)
        self.logger.info("Mesh generation complete")

    def optimize_mesh(self, method: str = "Netgen"):
        """
        Optimize mesh quality

        Args:
            method: Optimization method ("Netgen", "Relocate2D", "Relocate3D")
        """
        self.logger.info(f"Optimizing mesh using {method}...")
        gmsh.model.mesh.optimize(method)
        self.logger.info("Mesh optimization complete")

    def extract_mesh(self, element_type: ElementType = ElementType.HEX8) -> MeshData:
        """
        Extract mesh data from GMSH

        Args:
            element_type: Target element type

        Returns:
            MeshData object with extracted mesh
        """
        self.logger.info("Extracting mesh data from GMSH...")

        mesh_data = MeshData(element_type=element_type)

        # Extract nodes
        node_tags, node_coords, _ = gmsh.model.mesh.getNodes()

        # Add nodes to mesh
        num_nodes = len(node_tags)
        for i in range(num_nodes):
            node_id = int(node_tags[i])
            x = node_coords[i * 3]
            y = node_coords[i * 3 + 1]
            z = node_coords[i * 3 + 2]

            mesh_data.add_node(x, y, z, node_id=node_id)

        self.logger.debug(f"Extracted {num_nodes} nodes")

        # Extract elements
        elem_types, elem_tags, elem_node_tags = gmsh.model.mesh.getElements(dim=3)

        total_elements = 0

        for i, elem_type in enumerate(elem_types):
            # Map GMSH element type to our ElementType
            our_type = self._gmsh_type_to_element_type(elem_type)

            if our_type is None:
                self.logger.warning(f"Unknown GMSH element type: {elem_type}")
                continue

            # Get element tags and connectivity
            elem_ids = elem_tags[i]
            node_ids = elem_node_tags[i]

            # Number of nodes per element
            nodes_per_elem = our_type.num_nodes

            # Process each element
            num_elems = len(elem_ids)
            for j in range(num_elems):
                elem_id = int(elem_ids[j])

                # Extract node IDs for this element
                start_idx = j * nodes_per_elem
                end_idx = start_idx + nodes_per_elem
                elem_nodes = [int(node_ids[k]) for k in range(start_idx, end_idx)]

                mesh_data.add_element(
                    elem_nodes,
                    element_id=elem_id,
                    element_type=our_type
                )

            total_elements += num_elems

        self.logger.info(f"Extracted {total_elements} elements")

        return mesh_data

    def _gmsh_type_to_element_type(self, gmsh_type: int) -> Optional[ElementType]:
        """
        Convert GMSH element type to ElementType

        GMSH element types (reference: GMSH documentation):
        - 4: 4-node tetrahedron (TET4)
        - 5: 8-node hexahedron (HEX8)
        - 6: 6-node prism/wedge (PRISM6)
        - 7: 5-node pyramid (PYRAMID5)
        - 11: 10-node tetrahedron (TET10)
        - 17: 20-node hexahedron (HEX20)
        - 92: 27-node hexahedron (HEX27)
        """
        mapping = {
            4: ElementType.TET4,
            5: ElementType.HEX8,
            6: ElementType.PRISM6,
            7: ElementType.PYRAMID5,
            11: ElementType.TET10,
            17: ElementType.HEX20,
            92: ElementType.HEX27,
        }

        return mapping.get(gmsh_type)

    def save_mesh(self, filepath: str, format: str = "msh"):
        """
        Save mesh to file

        Args:
            filepath: Output file path
            format: File format ("msh", "vtk", "stl", etc.)
        """
        gmsh.write(filepath)
        self.logger.info(f"Saved mesh to: {filepath}")

    def get_mesh_statistics(self) -> Dict:
        """
        Get mesh statistics from GMSH

        Returns:
            Dictionary with mesh statistics
        """
        # Get node count
        node_tags, _, _ = gmsh.model.mesh.getNodes()
        num_nodes = len(node_tags)

        # Get element count
        elem_types, elem_tags, _ = gmsh.model.mesh.getElements(dim=3)
        num_elements = sum(len(tags) for tags in elem_tags)

        # Get quality statistics
        # Note: GMSH quality metrics may vary
        quality_stats = {}

        try:
            # Get element qualities (0-1, 1 is best)
            qualities = gmsh.model.mesh.getElementQualities()
            if qualities:
                quality_stats = {
                    'min': float(np.min(qualities)),
                    'max': float(np.max(qualities)),
                    'mean': float(np.mean(qualities)),
                    'median': float(np.median(qualities))
                }
        except:
            pass

        return {
            'num_nodes': num_nodes,
            'num_elements': num_elements,
            'quality': quality_stats
        }


def check_gmsh_available() -> bool:
    """
    Check if GMSH is available

    Returns:
        True if GMSH can be imported
    """
    return GMSH_AVAILABLE


def get_gmsh_version() -> str:
    """
    Get GMSH version string

    Returns:
        Version string
    """
    if not GMSH_AVAILABLE:
        return "Not installed"

    try:
        gmsh.initialize()
        version = gmsh.option.getString("General.Version")
        gmsh.finalize()
        return version
    except:
        return "Unknown"


def create_box_mesh(width: float, height: float, depth: float,
                   mesh_size: float,
                   recombine: bool = True) -> MeshData:
    """
    Create a simple box mesh for testing

    Args:
        width, height, depth: Box dimensions
        mesh_size: Target mesh size
        recombine: Create hex mesh if True, tet mesh if False

    Returns:
        MeshData with box mesh

    Example:
        >>> mesh = create_box_mesh(10, 10, 10, mesh_size=1.0)
        >>> print(f"Created box mesh with {mesh.num_elements()} elements")
    """
    if not GMSH_AVAILABLE:
        raise GmshError("GMSH is not available")

    with GmshWrapper() as wrapper:
        wrapper.new_model("box")

        # Create box
        box = gmsh.model.occ.addBox(0, 0, 0, width, height, depth)
        gmsh.model.occ.synchronize()

        # Set mesh size
        wrapper.set_mesh_size(mesh_size)

        # Recombine for hex mesh
        if recombine:
            wrapper.set_recombine(True)
            wrapper.set_algorithm("delaunay", 3)
        else:
            wrapper.set_algorithm("delaunay", 3)

        # Generate mesh
        wrapper.generate_mesh(3)

        # Optimize
        wrapper.optimize_mesh()

        # Extract
        element_type = ElementType.HEX8 if recombine else ElementType.TET4
        mesh_data = wrapper.extract_mesh(element_type)

    return mesh_data
