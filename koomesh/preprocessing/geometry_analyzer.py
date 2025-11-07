"""
Geometry Analyzer
=================

Analyze STEP file geometry and provide detailed information.

Features:
- Volume calculation
- Surface area calculation
- Face, edge, vertex counting
- Bounding box computation
- Geometry validation

Author: KooMeshGenerator Team
"""

import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class GeometryInfo:
    """
    Geometry analysis result

    Attributes:
        filename: Input file path
        volume: Total volume
        surface_area: Total surface area
        num_solids: Number of solid bodies
        num_faces: Number of faces
        num_edges: Number of edges
        num_vertices: Number of vertices
        bounding_box: Bounding box (xmin, ymin, zmin, xmax, ymax, zmax)
        is_valid: Geometry validity
        errors: List of validation errors
    """
    filename: str
    volume: float = 0.0
    surface_area: float = 0.0
    num_solids: int = 0
    num_faces: int = 0
    num_edges: int = 0
    num_vertices: int = 0
    bounding_box: Optional[tuple] = None
    is_valid: bool = True
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []

    def print_summary(self):
        """Print geometry information summary"""
        print("\n" + "="*70)
        print("GEOMETRY INFORMATION")
        print("="*70)
        print(f"File: {self.filename}")
        print(f"\nTopology:")
        print(f"  Solids:   {self.num_solids}")
        print(f"  Faces:    {self.num_faces}")
        print(f"  Edges:    {self.num_edges}")
        print(f"  Vertices: {self.num_vertices}")
        print(f"\nMeasurements:")
        print(f"  Volume:        {self.volume:.6f} mm³")
        print(f"  Surface Area:  {self.surface_area:.6f} mm²")

        if self.bounding_box:
            xmin, ymin, zmin, xmax, ymax, zmax = self.bounding_box
            print(f"\nBounding Box:")
            print(f"  X: [{xmin:.3f}, {xmax:.3f}]  (Δ = {xmax-xmin:.3f})")
            print(f"  Y: [{ymin:.3f}, {ymax:.3f}]  (Δ = {ymax-ymin:.3f})")
            print(f"  Z: [{zmin:.3f}, {zmax:.3f}]  (Δ = {zmax-zmin:.3f})")

        print(f"\nValidation:")
        print(f"  Valid: {'✓ Yes' if self.is_valid else '✗ No'}")
        if self.errors:
            print(f"  Errors:")
            for error in self.errors:
                print(f"    - {error}")

        print("="*70)


class GeometryAnalyzer:
    """
    Analyze STEP file geometry

    This class provides tools to analyze STEP files and extract
    geometric information like volume, surface area, topology counts, etc.

    Example:
        >>> analyzer = GeometryAnalyzer()
        >>> info = analyzer.analyze("part.step")
        >>> info.print_summary()
        >>> print(f"Volume: {info.volume} mm³")
    """

    def __init__(self):
        """Initialize geometry analyzer"""
        self.logger = logging.getLogger(__name__)

    def analyze(self, step_file: str) -> GeometryInfo:
        """
        Analyze STEP file geometry

        Args:
            step_file: Path to STEP file

        Returns:
            GeometryInfo with analysis results

        Raises:
            FileNotFoundError: If STEP file doesn't exist
            RuntimeError: If PythonOCC is not available
        """
        filepath = Path(step_file)
        if not filepath.exists():
            raise FileNotFoundError(f"STEP file not found: {step_file}")

        self.logger.info(f"Analyzing geometry: {step_file}")

        # Check if PythonOCC is available
        try:
            from OCC.Core.STEPControl import STEPControl_Reader
            from OCC.Core.BRepGProp import brepgprop_VolumeProperties, brepgprop_SurfaceProperties
            from OCC.Core.GProp import GProp_GProps
            from OCC.Core.TopExp import TopExp_Explorer
            from OCC.Core.TopAbs import TopAbs_SOLID, TopAbs_FACE, TopAbs_EDGE, TopAbs_VERTEX
            from OCC.Core.Bnd import Bnd_Box
            from OCC.Core.BRepBndLib import brepbndlib_Add
            from OCC.Core.BRepCheck import BRepCheck_Analyzer
        except ImportError:
            raise RuntimeError(
                "PythonOCC is required for geometry analysis. "
                "Please install PythonOCC first."
            )

        # Read STEP file
        reader = STEPControl_Reader()
        status = reader.ReadFile(str(filepath))

        if status != 1:  # IFSelect_RetDone
            raise RuntimeError(f"Failed to read STEP file: {step_file}")

        reader.TransferRoots()
        shape = reader.OneShape()

        # Initialize result
        info = GeometryInfo(filename=str(filepath))

        # Count topology
        info.num_solids = self._count_shapes(shape, TopAbs_SOLID)
        info.num_faces = self._count_shapes(shape, TopAbs_FACE)
        info.num_edges = self._count_shapes(shape, TopAbs_EDGE)
        info.num_vertices = self._count_shapes(shape, TopAbs_VERTEX)

        # Calculate volume
        props = GProp_GProps()
        brepgprop_VolumeProperties(shape, props)
        info.volume = props.Mass()

        # Calculate surface area
        surf_props = GProp_GProps()
        brepgprop_SurfaceProperties(shape, surf_props)
        info.surface_area = surf_props.Mass()

        # Get bounding box
        bbox = Bnd_Box()
        brepbndlib_Add(shape, bbox)
        if not bbox.IsVoid():
            xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()
            info.bounding_box = (xmin, ymin, zmin, xmax, ymax, zmax)

        # Validate geometry
        analyzer = BRepCheck_Analyzer(shape)
        info.is_valid = analyzer.IsValid()

        if not info.is_valid:
            info.errors.append("Geometry validation failed")
            # Could add more detailed error analysis here

        self.logger.info(
            f"Analysis complete: {info.num_faces} faces, "
            f"volume={info.volume:.2f}, area={info.surface_area:.2f}"
        )

        return info

    def _count_shapes(self, shape, shape_type) -> int:
        """Count number of shapes of given type"""
        try:
            from OCC.Core.TopExp import TopExp_Explorer
        except ImportError:
            return 0

        count = 0
        explorer = TopExp_Explorer(shape, shape_type)
        while explorer.More():
            count += 1
            explorer.Next()
        return count

    def compare_geometries(
        self,
        file1: str,
        file2: str
    ) -> Dict[str, Any]:
        """
        Compare two STEP files

        Args:
            file1: First STEP file
            file2: Second STEP file

        Returns:
            Dictionary with comparison results
        """
        info1 = self.analyze(file1)
        info2 = self.analyze(file2)

        comparison = {
            'file1': file1,
            'file2': file2,
            'volume_diff': info2.volume - info1.volume,
            'volume_diff_percent': (info2.volume - info1.volume) / info1.volume * 100 if info1.volume > 0 else 0,
            'area_diff': info2.surface_area - info1.surface_area,
            'area_diff_percent': (info2.surface_area - info1.surface_area) / info1.surface_area * 100 if info1.surface_area > 0 else 0,
            'face_diff': info2.num_faces - info1.num_faces,
            'info1': info1,
            'info2': info2,
        }

        return comparison

    def print_comparison(self, comparison: Dict[str, Any]):
        """Print geometry comparison"""
        print("\n" + "="*70)
        print("GEOMETRY COMPARISON")
        print("="*70)
        print(f"\nFile 1: {comparison['file1']}")
        print(f"File 2: {comparison['file2']}")
        print(f"\nVolume:")
        print(f"  File 1: {comparison['info1'].volume:.6f} mm³")
        print(f"  File 2: {comparison['info2'].volume:.6f} mm³")
        print(f"  Difference: {comparison['volume_diff']:.6f} mm³ ({comparison['volume_diff_percent']:.2f}%)")
        print(f"\nSurface Area:")
        print(f"  File 1: {comparison['info1'].surface_area:.6f} mm²")
        print(f"  File 2: {comparison['info2'].surface_area:.6f} mm²")
        print(f"  Difference: {comparison['area_diff']:.6f} mm² ({comparison['area_diff_percent']:.2f}%)")
        print(f"\nFaces:")
        print(f"  File 1: {comparison['info1'].num_faces}")
        print(f"  File 2: {comparison['info2'].num_faces}")
        print(f"  Difference: {comparison['face_diff']}")
        print("="*70)
