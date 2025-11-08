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

        Enhanced with:
        - Free edge detection and reporting
        - Gap analysis
        - Adaptive tolerance for difficult cases
        - Multiple sewing passes

        Args:
            shape: Input shape
            tolerance: Sewing tolerance (default: 1e-3)

        Returns:
            Tuple of (healed_shape, gaps_filled)
        """
        try:
            from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Sewing
            from OCC.Core.TopExp import TopExp_Explorer
            from OCC.Core.TopAbs import TopAbs_FACE, TopAbs_EDGE
            from OCC.Core.TopTools import TopTools_IndexedDataMapOfShapeListOfShape
            from OCC.Core.TopExp import TopExp
        except ImportError:
            return shape, 0

        if tolerance is None:
            tolerance = 1e-3

        # Count free edges before healing
        free_edges_before = self._count_free_edges(shape)

        # Create sewing object with options
        sewing = BRepBuilderAPI_Sewing(tolerance)
        sewing.SetTolerance(tolerance)
        sewing.SetMinTolerance(tolerance * 0.1)
        sewing.SetMaxTolerance(tolerance * 10.0)

        # Add all faces
        face_count = 0
        explorer = TopExp_Explorer(shape, TopAbs_FACE)
        while explorer.More():
            face = explorer.Current()
            sewing.Add(face)
            face_count += 1
            explorer.Next()

        self.logger.debug(f"Sewing {face_count} faces with tolerance {tolerance}")

        # Perform sewing
        sewing.Perform()
        sewed_shape = sewing.SewedShape()

        # Count free edges after healing
        free_edges_after = self._count_free_edges(sewed_shape)

        # Calculate gaps filled
        gaps_filled = max(0, free_edges_before - free_edges_after)

        # If still have many free edges, try with larger tolerance
        if free_edges_after > face_count * 0.1 and tolerance < 1.0:
            self.logger.debug(
                f"Still have {free_edges_after} free edges, "
                f"trying with larger tolerance..."
            )

            # Second pass with larger tolerance
            sewing2 = BRepBuilderAPI_Sewing(tolerance * 5.0)
            sewing2.SetTolerance(tolerance * 5.0)

            # Add faces from first sewing result
            explorer2 = TopExp_Explorer(sewed_shape, TopAbs_FACE)
            while explorer2.More():
                sewing2.Add(explorer2.Current())
                explorer2.Next()

            sewing2.Perform()
            sewed_shape_2 = sewing2.SewedShape()

            free_edges_after_2 = self._count_free_edges(sewed_shape_2)

            # Use second result if better
            if free_edges_after_2 < free_edges_after:
                gaps_filled = max(0, free_edges_before - free_edges_after_2)
                sewed_shape = sewed_shape_2
                self.logger.debug(
                    f"Second pass improved: {free_edges_after_2} free edges"
                )

        if gaps_filled > 0:
            self.logger.debug(f"Filled {gaps_filled} gaps during surface healing")

        return sewed_shape, gaps_filled

    def _count_free_edges(self, shape) -> int:
        """
        Count free edges (edges belonging to only one face)

        Args:
            shape: Shape to analyze

        Returns:
            Number of free edges
        """
        try:
            from OCC.Core.TopExp import TopExp
            from OCC.Core.TopTools import TopTools_IndexedDataMapOfShapeListOfShape
            from OCC.Core.TopAbs import TopAbs_EDGE

            edge_map = TopTools_IndexedDataMapOfShapeListOfShape()
            TopExp.MapShapesAndAncestors_s(
                shape, TopAbs_EDGE, TopAbs_FACE, edge_map
            )

            free_edges = 0
            for i in range(1, edge_map.Extent() + 1):
                face_list = edge_map.FindFromIndex(i)
                if face_list.Extent() == 1:  # Edge belongs to only one face
                    free_edges += 1

            return free_edges

        except:
            return 0

    def _remove_small_features(self, shape, min_size: float):
        """
        Remove small features (holes, fillets, etc.)

        Detects and removes:
        - Small holes (circular edges with diameter < min_size)
        - Small fillets (edges with radius < min_size)
        - Small edges (edges with length < min_size)

        Args:
            shape: Input shape
            min_size: Minimum feature size to keep (mm)

        Returns:
            Tuple of (cleaned_shape, features_removed)
        """
        try:
            from OCC.Core.TopExp import TopExp_Explorer
            from OCC.Core.TopAbs import TopAbs_EDGE, TopAbs_FACE
            from OCC.Core.BRep import BRep_Tool
            from OCC.Core.GProp import GProp_GProps
            from OCC.Core.BRepGProp import BRepGProp
            from OCC.Core.BRepAdaptor import BRepAdaptor_Curve
            from OCC.Core.GeomAbs import GeomAbs_Circle
            from OCC.Core.TopoDS import TopoDS_Compound, TopoDS_Builder, TopoDS_Face
            from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Copy
        except ImportError:
            self.logger.warning(
                "PythonOCC not available. Returning shape unchanged."
            )
            return shape, 0

        try:
            features_removed = 0
            faces_to_keep = []

            # Analyze each face
            face_explorer = TopExp_Explorer(shape, TopAbs_FACE)
            while face_explorer.More():
                face = TopoDS_Face.DownCast(face_explorer.Current())
                keep_face = True

                # Analyze edges in this face
                edge_explorer = TopExp_Explorer(face, TopAbs_EDGE)
                small_edges = 0

                while edge_explorer.More():
                    edge = edge_explorer.Current()

                    # Calculate edge length
                    props = GProp_GProps()
                    BRepGProp.LinearProperties_s(edge, props)
                    edge_length = props.Mass()

                    # Check if edge is too small
                    if edge_length < min_size:
                        small_edges += 1

                    # Check if edge is a small circle (hole or fillet)
                    try:
                        curve_adaptor = BRepAdaptor_Curve(edge)
                        if curve_adaptor.GetType() == GeomAbs_Circle:
                            radius = curve_adaptor.Circle().Radius()
                            diameter = 2.0 * radius

                            if diameter < min_size:
                                small_edges += 1
                                self.logger.debug(
                                    f"Found small circular edge: diameter={diameter:.3f} mm"
                                )
                    except:
                        pass  # Edge analysis failed, skip

                    edge_explorer.Next()

                # Count total edges in face
                edge_explorer2 = TopExp_Explorer(face, TopAbs_EDGE)
                total_edges = 0
                while edge_explorer2.More():
                    total_edges += 1
                    edge_explorer2.Next()

                # If more than 30% of edges are small, consider removing face
                if total_edges > 0 and (small_edges / total_edges) > 0.3:
                    keep_face = False
                    features_removed += 1
                    self.logger.debug(
                        f"Removing face with {small_edges}/{total_edges} small edges"
                    )

                if keep_face:
                    faces_to_keep.append(face)

                face_explorer.Next()

            # If no features removed, return original shape
            if features_removed == 0:
                return shape, 0

            # Rebuild shape from kept faces
            builder = TopoDS_Builder()
            compound = TopoDS_Compound()
            builder.MakeCompound(compound)

            for face in faces_to_keep:
                builder.Add(compound, face)

            self.logger.info(f"Removed {features_removed} small features")
            return compound, features_removed

        except Exception as e:
            self.logger.warning(
                f"Small feature removal failed: {str(e)}. "
                "Returning original shape."
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

    # ========================================================================
    # Shape-based methods for pipeline integration
    # ========================================================================

    def remove_duplicate_faces(self, shape, tolerance: float = 1e-6):
        """
        Remove duplicate faces from shape

        Uses geometric comparison to identify and remove duplicate faces.

        Args:
            shape: Input shape (OCC shape object)
            tolerance: Tolerance for duplicate detection (mm)

        Returns:
            Shape with duplicates removed
        """
        try:
            from OCP.TopExp import TopExp_Explorer
            from OCP.TopAbs import TopAbs_FACE
            from OCP.BRep import BRep_Tool
            from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeShape
            from OCP.TopoDS import TopoDS_Compound, TopoDS_Builder

            # Explore all faces
            explorer = TopExp_Explorer(shape, TopAbs_FACE)
            unique_faces = []
            face_signatures = []

            while explorer.More():
                face = explorer.Current()

                # Calculate face signature (center point + area)
                sig = self._calculate_face_signature(face, tolerance)

                # Check if this signature already exists
                is_duplicate = False
                for existing_sig in face_signatures:
                    if self._signatures_match(sig, existing_sig, tolerance):
                        is_duplicate = True
                        break

                if not is_duplicate:
                    unique_faces.append(face)
                    face_signatures.append(sig)

                explorer.Next()

            # If no duplicates found, return original shape
            if len(unique_faces) == self._count_faces(shape):
                return shape

            # Build new shape from unique faces
            num_duplicates = self._count_faces(shape) - len(unique_faces)
            self.logger.info(f"Removed {num_duplicates} duplicate faces")

            # Rebuild shape from unique faces
            try:
                builder = TopoDS_Builder()
                compound = TopoDS_Compound()
                builder.MakeCompound(compound)

                for face in unique_faces:
                    builder.Add(compound, face)

                return compound

            except Exception as e:
                self.logger.warning(
                    f"Failed to rebuild shape from unique faces: {str(e)}. "
                    "Returning original shape."
                )
                return shape

        except ImportError:
            self.logger.warning(
                "PythonOCC not available. Returning shape unchanged."
            )
            return shape
        except Exception as e:
            self.logger.warning(
                f"Duplicate face removal failed: {str(e)}. "
                "Returning original shape."
            )
            return shape

    def _calculate_face_signature(self, face, tolerance: float) -> tuple:
        """
        Calculate a signature for a face

        Args:
            face: Face to analyze
            tolerance: Tolerance for comparison

        Returns:
            Tuple of (center_x, center_y, center_z, area)
        """
        try:
            from OCP.GProp import GProp_GProps
            from OCP.BRepGProp import BRepGProp

            props = GProp_GProps()
            BRepGProp.SurfaceProperties_s(face, props)

            center = props.CentreOfMass()
            area = props.Mass()

            # Round to tolerance to group similar faces
            cx = round(center.X() / tolerance) * tolerance
            cy = round(center.Y() / tolerance) * tolerance
            cz = round(center.Z() / tolerance) * tolerance
            a = round(area / tolerance) * tolerance

            return (cx, cy, cz, a)
        except:
            # If calculation fails, return unique signature
            return (0, 0, 0, 0)

    def _signatures_match(self, sig1: tuple, sig2: tuple, tolerance: float) -> bool:
        """
        Check if two face signatures match within tolerance

        Args:
            sig1: First signature
            sig2: Second signature
            tolerance: Tolerance for comparison

        Returns:
            True if signatures match
        """
        if len(sig1) != len(sig2):
            return False

        for v1, v2 in zip(sig1, sig2):
            if abs(v1 - v2) > tolerance:
                return False

        return True

    def heal_surface(self, shape, tolerance: float = 1e-3):
        """
        Heal surface gaps and discontinuities

        Public wrapper for _heal_surfaces() for pipeline integration.

        Args:
            shape: Input shape (OCC shape object)
            tolerance: Healing tolerance (mm)

        Returns:
            Healed shape
        """
        try:
            healed_shape, gaps_filled = self._heal_surfaces(shape, tolerance)
            if gaps_filled > 0:
                self.logger.info(f"Healed {gaps_filled} gaps in surface")
            return healed_shape
        except Exception as e:
            self.logger.warning(
                f"Surface healing failed: {str(e)}. "
                "Returning original shape."
            )
            return shape

    def remove_small_features(self, shape, min_size: float = 0.1):
        """
        Remove small features (holes, edges) below threshold

        Public wrapper for _remove_small_features() for pipeline integration.

        Args:
            shape: Input shape (OCC shape object)
            min_size: Minimum feature size to keep (mm)

        Returns:
            Shape with small features removed
        """
        try:
            cleaned_shape, features_removed = self._remove_small_features(
                shape, min_size
            )
            if features_removed > 0:
                self.logger.info(
                    f"Removed {features_removed} small features"
                )
            return cleaned_shape
        except Exception as e:
            self.logger.warning(
                f"Small feature removal failed: {str(e)}. "
                "Returning original shape."
            )
            return shape
