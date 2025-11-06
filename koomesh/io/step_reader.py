"""
STEP File Reader Module
========================

This module provides functionality to read and import STEP files using
PythonOCC (OpenCASCADE).

Features:
- Read STEP files (ISO 10303)
- Extract geometric shapes
- Handle assemblies and parts
- Support for metadata extraction

Usage:
    >>> from koomesh.io.step_reader import STEPReader
    >>> reader = STEPReader()
    >>> shape = reader.read_file('model.step')
    >>> shapes = reader.get_all_shapes()
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

# Try to import OCC modules (through OCP - cadquery-ocp)
try:
    from OCP.STEPControl import STEPControl_Reader
    from OCP.IFSelect import IFSelect_RetDone, IFSelect_ItemsByEntity
    from OCP.TopoDS import TopoDS_Shape
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopAbs import (
        TopAbs_SOLID, TopAbs_FACE, TopAbs_EDGE,
        TopAbs_VERTEX, TopAbs_SHELL, TopAbs_COMPOUND
    )
    from OCP.GProp import GProp_GProps
    from OCP.BRepGProp import BRepGProp
    PYTHONOCC_AVAILABLE = True
except ImportError:
    # Fall back to old PythonOCC if available
    try:
        from OCC.Core.STEPControl import STEPControl_Reader
        from OCC.Core.IFSelect import IFSelect_RetDone, IFSelect_ItemsByEntity
        from OCC.Core.TopoDS import TopoDS_Shape
        from OCC.Core.TopExp import TopExp_Explorer
        from OCC.Core.TopAbs import (
            TopAbs_SOLID, TopAbs_FACE, TopAbs_EDGE,
            TopAbs_VERTEX, TopAbs_SHELL, TopAbs_COMPOUND
        )
        from OCC.Core.GProp import GProp_GProps
        from OCC.Core.BRepGProp import (
            brepgprop_VolumeProperties,
            brepgprop_SurfaceProperties
        )
        PYTHONOCC_AVAILABLE = True
    except ImportError:
        PYTHONOCC_AVAILABLE = False
        # Define dummy classes for type hints when neither is available
        class TopoDS_Shape:
            pass


class STEPReaderError(Exception):
    """Exception raised for STEP reader errors"""
    pass


class STEPReader:
    """
    STEP file reader using PythonOCC

    This class provides methods to read STEP files and extract geometric
    information using the OpenCASCADE kernel through PythonOCC bindings.

    Attributes:
        logger: Logger instance for this module
        reader: STEPControl_Reader instance (if PythonOCC available)
        shapes: List of loaded shapes

    Example:
        >>> reader = STEPReader()
        >>> shape = reader.read_file('assembly.step')
        >>> info = reader.get_shape_info(shape)
        >>> print(f"Volume: {info['volume']}")
    """

    def __init__(self):
        """Initialize STEP reader"""
        self.logger = logging.getLogger(__name__)

        if not PYTHONOCC_AVAILABLE:
            self.logger.warning(
                "PythonOCC is not installed. STEP reading functionality is disabled."
            )
            self.reader = None
            self.shapes = []
            return

        self.reader = STEPControl_Reader()
        self.shapes: List[TopoDS_Shape] = []

        self.logger.debug("STEPReader initialized")

    def read_file(self, filepath: str) -> Optional[TopoDS_Shape]:
        """
        Read STEP file and return the main shape

        Args:
            filepath: Path to STEP file (.step or .stp)

        Returns:
            TopoDS_Shape if successful, None otherwise

        Raises:
            STEPReaderError: If file cannot be read or PythonOCC is not available
            FileNotFoundError: If file does not exist

        Example:
            >>> reader = STEPReader()
            >>> shape = reader.read_file('model.step')
        """
        if not PYTHONOCC_AVAILABLE:
            raise STEPReaderError(
                "PythonOCC is not installed. Please build and install PythonOCC first."
            )

        # Check file existence
        file_path = Path(filepath)
        if not file_path.exists():
            raise FileNotFoundError(f"STEP file not found: {filepath}")

        # Check file extension
        if file_path.suffix.lower() not in ['.step', '.stp']:
            self.logger.warning(
                f"File extension '{file_path.suffix}' is not standard for STEP files"
            )

        self.logger.info(f"Reading STEP file: {filepath}")

        # Read the file
        status = self.reader.ReadFile(str(file_path))

        if status != IFSelect_RetDone:
            raise STEPReaderError(f"Failed to read STEP file: {filepath}")

        self.logger.debug("STEP file read successfully, transferring roots...")

        # Transfer roots to get shapes
        nb_roots = self.reader.TransferRoots()
        self.logger.debug(f"Transferred {nb_roots} root(s)")

        # Get the main shape
        shape = self.reader.OneShape()

        if shape.IsNull():
            raise STEPReaderError("No valid shape found in STEP file")

        # Store all shapes
        self.shapes = self.get_all_shapes()

        self.logger.info(
            f"Successfully loaded STEP file with {len(self.shapes)} shape(s)"
        )

        return shape

    def get_all_shapes(self) -> List[TopoDS_Shape]:
        """
        Get all shapes from the loaded STEP file

        Returns:
            List of TopoDS_Shape objects

        Example:
            >>> shapes = reader.get_all_shapes()
            >>> print(f"Found {len(shapes)} shapes")
        """
        if not PYTHONOCC_AVAILABLE or self.reader is None:
            return []

        shapes = []
        nb_shapes = self.reader.NbShapes()

        for i in range(1, nb_shapes + 1):  # OCCT uses 1-based indexing
            shape = self.reader.Shape(i)
            if not shape.IsNull():
                shapes.append(shape)

        return shapes

    def get_shape_info(self, shape: TopoDS_Shape) -> Dict[str, Any]:
        """
        Extract information about a shape

        Args:
            shape: TopoDS_Shape to analyze

        Returns:
            Dictionary with shape information:
            - type: Shape type (SOLID, COMPOUND, etc.)
            - num_solids: Number of solids
            - num_faces: Number of faces
            - num_edges: Number of edges
            - num_vertices: Number of vertices
            - volume: Total volume (if applicable)
            - surface_area: Total surface area

        Example:
            >>> info = reader.get_shape_info(shape)
            >>> print(f"Type: {info['type']}, Faces: {info['num_faces']}")
        """
        if not PYTHONOCC_AVAILABLE:
            return {}

        info = {
            'type': self._get_shape_type(shape),
            'num_solids': self._count_shapes(shape, TopAbs_SOLID),
            'num_faces': self._count_shapes(shape, TopAbs_FACE),
            'num_edges': self._count_shapes(shape, TopAbs_EDGE),
            'num_vertices': self._count_shapes(shape, TopAbs_VERTEX),
        }

        # Calculate volume for solids
        try:
            props = GProp_GProps()
            BRepGProp.VolumeProperties_s(shape, props)
            info['volume'] = props.Mass()
        except Exception as e:
            self.logger.debug(f"Could not calculate volume: {e}")
            info['volume'] = None

        # Calculate surface area
        try:
            props = GProp_GProps()
            BRepGProp.SurfaceProperties_s(shape, props)
            info['surface_area'] = props.Mass()
        except Exception as e:
            self.logger.debug(f"Could not calculate surface area: {e}")
            info['surface_area'] = None

        return info

    def _get_shape_type(self, shape: TopoDS_Shape) -> str:
        """Get human-readable shape type"""
        if not PYTHONOCC_AVAILABLE:
            return "UNKNOWN"

        shape_type = shape.ShapeType()

        type_map = {
            TopAbs_COMPOUND: "COMPOUND",
            TopAbs_SOLID: "SOLID",
            TopAbs_SHELL: "SHELL",
            TopAbs_FACE: "FACE",
            TopAbs_EDGE: "EDGE",
            TopAbs_VERTEX: "VERTEX",
        }

        return type_map.get(shape_type, f"UNKNOWN({shape_type})")

    def _count_shapes(self, shape: TopoDS_Shape, shape_type) -> int:
        """Count number of sub-shapes of given type"""
        if not PYTHONOCC_AVAILABLE:
            return 0

        count = 0
        explorer = TopExp_Explorer(shape, shape_type)

        while explorer.More():
            count += 1
            explorer.Next()

        return count

    def extract_solids(self, shape: TopoDS_Shape) -> List[TopoDS_Shape]:
        """
        Extract all solid sub-shapes from a shape

        Args:
            shape: TopoDS_Shape to extract solids from

        Returns:
            List of solid shapes

        Example:
            >>> solids = reader.extract_solids(shape)
            >>> for solid in solids:
            ...     info = reader.get_shape_info(solid)
            ...     print(f"Solid volume: {info['volume']}")
        """
        if not PYTHONOCC_AVAILABLE:
            return []

        solids = []
        explorer = TopExp_Explorer(shape, TopAbs_SOLID)

        while explorer.More():
            solid = explorer.Current()
            solids.append(solid)
            explorer.Next()

        self.logger.debug(f"Extracted {len(solids)} solid(s)")

        return solids

    def extract_faces(self, shape: TopoDS_Shape) -> List[TopoDS_Shape]:
        """
        Extract all face sub-shapes from a shape

        Args:
            shape: TopoDS_Shape to extract faces from

        Returns:
            List of face shapes
        """
        if not PYTHONOCC_AVAILABLE:
            return []

        faces = []
        explorer = TopExp_Explorer(shape, TopAbs_FACE)

        while explorer.More():
            face = explorer.Current()
            faces.append(face)
            explorer.Next()

        return faces

    def is_valid_shape(self, shape: TopoDS_Shape) -> bool:
        """
        Check if a shape is valid

        Args:
            shape: TopoDS_Shape to validate

        Returns:
            True if shape is valid, False otherwise
        """
        if not PYTHONOCC_AVAILABLE:
            return False

        return not shape.IsNull()

    def print_file_info(self, filepath: str):
        """
        Print information about a STEP file

        Args:
            filepath: Path to STEP file

        Example:
            >>> reader = STEPReader()
            >>> reader.print_file_info('assembly.step')
            File: assembly.step
            Number of shapes: 5
            Total solids: 3
            Total faces: 18
        """
        shape = self.read_file(filepath)

        if shape is None:
            print("Failed to read file")
            return

        info = self.get_shape_info(shape)

        print(f"\nFile: {filepath}")
        print(f"  Type: {info['type']}")
        print(f"  Number of shapes: {len(self.shapes)}")
        print(f"  Solids: {info['num_solids']}")
        print(f"  Faces: {info['num_faces']}")
        print(f"  Edges: {info['num_edges']}")
        print(f"  Vertices: {info['num_vertices']}")

        if info['volume'] is not None:
            print(f"  Volume: {info['volume']:.6f}")

        if info['surface_area'] is not None:
            print(f"  Surface Area: {info['surface_area']:.6f}")


def check_pythonocc_available() -> bool:
    """
    Check if PythonOCC is available

    Returns:
        True if PythonOCC can be imported, False otherwise
    """
    return PYTHONOCC_AVAILABLE
