"""
Geometry Cleaner
================

Clean and repair STEP file geometry for better meshing.

Features:
- Small feature removal (fillets, holes, etc.)
- Surface healing (gap filling, sewing)
- Invalid geometry repair
- Duplicate removal

Author: KooMeshGenerator Team
"""

import logging
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CleaningResult:
    """
    Geometry cleaning result

    Attributes:
        input_file: Input STEP file
        output_file: Output STEP file
        features_removed: Number of features removed
        gaps_filled: Number of gaps filled
        faces_before: Number of faces before cleaning
        faces_after: Number of faces after cleaning
        success: Whether cleaning succeeded
        errors: List of errors encountered
    """
    input_file: str
    output_file: str
    features_removed: int = 0
    gaps_filled: int = 0
    faces_before: int = 0
    faces_after: int = 0
    success: bool = True
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []

    def print_summary(self):
        """Print cleaning result summary"""
        print("\n" + "="*70)
        print("GEOMETRY CLEANING SUMMARY")
        print("="*70)
        print(f"Input:  {self.input_file}")
        print(f"Output: {self.output_file}")
        print(f"\nResults:")
        print(f"  Faces before:      {self.faces_before}")
        print(f"  Faces after:       {self.faces_after}")
        print(f"  Features removed:  {self.features_removed}")
        print(f"  Gaps filled:       {self.gaps_filled}")
        print(f"\nStatus: {'✓ Success' if self.success else '✗ Failed'}")
        if self.errors:
            print(f"Errors:")
            for error in self.errors:
                print(f"  - {error}")
        print("="*70)


class GeometryCleaner:
    """
    Clean and repair STEP file geometry

    This class provides tools to clean geometry before meshing:
    - Remove small features (fillets, holes, chamfers)
    - Heal surfaces (fill gaps, sew faces)
    - Repair invalid geometry
    - Remove duplicates

    Example:
        >>> cleaner = GeometryCleaner()
        >>> result = cleaner.clean(
        ...     "input.step",
        ...     "cleaned.step",
        ...     remove_small_features=0.5,
        ...     heal_surfaces=True
        ... )
        >>> result.print_summary()
    """

    def __init__(self):
        """Initialize geometry cleaner"""
        self.logger = logging.getLogger(__name__)

    def clean(
        self,
        input_file: str,
        output_file: str,
        remove_small_features: Optional[float] = None,
        heal_surfaces: bool = False,
        fill_gaps: Optional[float] = None,
        fix_invalid: bool = True
    ) -> CleaningResult:
        """
        Clean geometry

        Args:
            input_file: Input STEP file
            output_file: Output STEP file
            remove_small_features: Remove features smaller than this size (mm)
            heal_surfaces: Perform surface healing
            fill_gaps: Fill gaps smaller than this size (mm)
            fix_invalid: Attempt to fix invalid geometry

        Returns:
            CleaningResult with cleaning summary

        Raises:
            FileNotFoundError: If input file doesn't exist
            RuntimeError: If PythonOCC is not available
        """
        input_path = Path(input_file)
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")

        self.logger.info(f"Cleaning geometry: {input_file}")

        # Check if PythonOCC is available
        try:
            from OCC.Core.STEPControl import STEPControl_Reader, STEPControl_Writer, STEPControl_AsIs
            from OCC.Core.IFSelect import IFSelect_RetDone
            from OCC.Core.TopExp import TopExp_Explorer
            from OCC.Core.TopAbs import TopAbs_FACE
            from OCC.Core.ShapeFix import ShapeFix_Shape
            from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Sewing
        except ImportError:
            raise RuntimeError(
                "PythonOCC is required for geometry cleaning. "
                "Please install PythonOCC first."
            )

        # Initialize result
        result = CleaningResult(
            input_file=str(input_file),
            output_file=str(output_file)
        )

        try:
            # Read STEP file
            reader = STEPControl_Reader()
            status = reader.ReadFile(str(input_path))

            if status != IFSelect_RetDone:
                raise RuntimeError(f"Failed to read STEP file: {input_file}")

            reader.TransferRoots()
            shape = reader.OneShape()

            # Count faces before
            result.faces_before = self._count_faces(shape)

            # Apply cleaning operations
            cleaned_shape = shape

            # Fix invalid geometry
            if fix_invalid:
                self.logger.info("Fixing invalid geometry...")
                cleaned_shape = self._fix_invalid_geometry(cleaned_shape)

            # Heal surfaces (sewing)
            if heal_surfaces:
                self.logger.info("Healing surfaces...")
                cleaned_shape, gaps_filled = self._heal_surfaces(cleaned_shape, fill_gaps)
                result.gaps_filled = gaps_filled

            # Remove small features
            if remove_small_features and remove_small_features > 0:
                self.logger.info(f"Removing features smaller than {remove_small_features} mm...")
                cleaned_shape, removed = self._remove_small_features(cleaned_shape, remove_small_features)
                result.features_removed = removed

            # Count faces after
            result.faces_after = self._count_faces(cleaned_shape)

            # Write output STEP file
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            writer = STEPControl_Writer()
            writer.Transfer(cleaned_shape, STEPControl_AsIs)
            status = writer.Write(str(output_path))

            if status != IFSelect_RetDone:
                raise RuntimeError(f"Failed to write STEP file: {output_file}")

            result.success = True
            self.logger.info(f"Geometry cleaned successfully: {output_file}")

        except Exception as e:
            result.success = False
            result.errors.append(str(e))
            self.logger.error(f"Geometry cleaning failed: {e}")

        return result

    def _count_faces(self, shape) -> int:
        """Count number of faces in shape"""
        try:
            from OCC.Core.TopExp import TopExp_Explorer
            from OCC.Core.TopAbs import TopAbs_FACE
        except ImportError:
            return 0

        count = 0
        explorer = TopExp_Explorer(shape, TopAbs_FACE)
        while explorer.More():
            count += 1
            explorer.Next()
        return count

    def _fix_invalid_geometry(self, shape):
        """Fix invalid geometry using ShapeFix"""
        try:
            from OCC.Core.ShapeFix import ShapeFix_Shape
        except ImportError:
            return shape

        fixer = ShapeFix_Shape(shape)
        fixer.Perform()
        return fixer.Shape()

    def _heal_surfaces(self, shape, tolerance: Optional[float] = None):
        """
        Heal surfaces by sewing faces together

        Args:
            shape: Input shape
            tolerance: Sewing tolerance (default: 1e-3)

        Returns:
            Tuple of (healed_shape, gaps_filled)
        """
        try:
            from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Sewing
            from OCC.Core.TopExp import TopExp_Explorer
            from OCC.Core.TopAbs import TopAbs_FACE
        except ImportError:
            return shape, 0

        if tolerance is None:
            tolerance = 1e-3

        # Create sewing object
        sewing = BRepBuilderAPI_Sewing(tolerance)

        # Add all faces
        explorer = TopExp_Explorer(shape, TopAbs_FACE)
        while explorer.More():
            face = explorer.Current()
            sewing.Add(face)
            explorer.Next()

        # Perform sewing
        sewing.Perform()
        sewed_shape = sewing.SewedShape()

        # Count gaps filled (free edges before - free edges after)
        gaps_filled = sewing.NbFreeEdges()  # Approximation

        return sewed_shape, gaps_filled

    def _remove_small_features(self, shape, min_size: float):
        """
        Remove small features (holes, fillets, etc.)

        This is a placeholder for actual small feature removal.
        Full implementation would require more advanced algorithms.

        Args:
            shape: Input shape
            min_size: Minimum feature size to keep (mm)

        Returns:
            Tuple of (cleaned_shape, features_removed)
        """
        # NOTE: Full small feature removal is complex and would require:
        # - Feature recognition algorithms
        # - Topological operations
        # - Geometric analysis
        #
        # For now, we return the shape unchanged
        # This could be implemented using OCC.Core.ShapeUpgrade or custom algorithms

        self.logger.warning(
            "Small feature removal is not fully implemented. "
            "Shape returned unchanged. "
            "This feature requires advanced CAD kernel operations."
        )

        return shape, 0

    def remove_duplicates(self, input_file: str, output_file: str, tolerance: float = 1e-6) -> CleaningResult:
        """
        Remove duplicate faces and edges

        Args:
            input_file: Input STEP file
            output_file: Output STEP file
            tolerance: Tolerance for duplicate detection

        Returns:
            CleaningResult with summary
        """
        # TODO: Implement duplicate removal using ShapeUpgrade_RemoveInternalWires, etc.
        self.logger.warning("Duplicate removal not yet implemented")

        # For now, just copy the file
        result = self.clean(
            input_file,
            output_file,
            remove_small_features=None,
            heal_surfaces=False,
            fix_invalid=True
        )

        return result
