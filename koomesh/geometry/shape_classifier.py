"""
Shape Classifier Module
========================

This module provides functionality to classify geometric shapes and determine
the optimal mesh type (hexahedral, tetrahedral, or hybrid).

Features:
- Classify shapes based on geometry and topology
- Detect simple shapes (box, cylinder, etc.)
- Identify sweepable geometries
- Determine optimal mesh strategy

Usage:
    >>> from koomesh.geometry.shape_classifier import ShapeClassifier, MeshType
    >>> classifier = ShapeClassifier()
    >>> mesh_type = classifier.classify(shape)
    >>> print(f"Recommended mesh: {mesh_type.value}")
"""

from enum import Enum
from typing import Optional, List, Tuple, Dict
from dataclasses import dataclass, field
import logging
import math

# Try to import PythonOCC
try:
    from OCC.Core.TopoDS import TopoDS_Shape
    from OCC.Core.TopExp import TopExp_Explorer
    from OCC.Core.TopAbs import TopAbs_FACE, TopAbs_EDGE, TopAbs_VERTEX, TopAbs_SOLID
    from OCC.Core.BRepAdaptor import BRepAdaptor_Surface, BRepAdaptor_Curve
    from OCC.Core.GeomAbs import (
        GeomAbs_Plane, GeomAbs_Cylinder, GeomAbs_Sphere,
        GeomAbs_Line, GeomAbs_Circle
    )
    from OCC.Core.GProp import GProp_GProps
    from OCC.Core.BRepGProp import brepgprop_VolumeProperties
    from OCC.Core.BRepBndLib import brepbndlib
    from OCC.Core.Bnd import Bnd_Box
    from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Dir
    PYTHONOCC_AVAILABLE = True
except ImportError:
    PYTHONOCC_AVAILABLE = False
    TopoDS_Shape = object


class MeshType(Enum):
    """
    Mesh type enumeration

    Defines the recommended mesh element type for a geometry.
    """
    HEXAHEDRAL = "hex"       # Structured hexahedral mesh
    TETRAHEDRAL = "tet"      # Unstructured tetrahedral mesh
    HYBRID = "hybrid"        # Combination of hex and tet
    UNKNOWN = "unknown"      # Cannot determine


class ShapeType(Enum):
    """
    Basic shape type enumeration
    """
    BOX = "box"
    CYLINDER = "cylinder"
    SPHERE = "sphere"
    SWEEPABLE = "sweepable"
    COMPLEX = "complex"
    UNKNOWN = "unknown"


@dataclass
class ClassificationResult:
    """
    Result of shape classification

    Attributes:
        mesh_type: Recommended mesh type
        shape_type: Detected basic shape type
        confidence: Confidence level (0-1)
        reasons: List of reasons for classification
        properties: Additional shape properties
    """
    mesh_type: MeshType
    shape_type: ShapeType
    confidence: float = 1.0
    reasons: List[str] = field(default_factory=list)
    properties: Dict = field(default_factory=dict)


class ShapeClassifier:
    """
    Geometric shape classifier

    Analyzes shapes and determines optimal meshing strategy based on
    geometry and topology.

    The classifier uses the following decision tree:
    1. Check for simple shapes (box, cylinder) → HEX
    2. Check for sweepable geometry → HEX
    3. Check for decomposability → HYBRID
    4. Default to tetrahedral → TET

    Example:
        >>> classifier = ShapeClassifier()
        >>> result = classifier.classify(shape)
        >>> if result.mesh_type == MeshType.HEXAHEDRAL:
        ...     print("Use hexahedral mesh")
        >>> print(f"Confidence: {result.confidence}")
    """

    def __init__(self, tolerance: float = 1e-6):
        """
        Initialize shape classifier

        Args:
            tolerance: Geometric tolerance for comparisons
        """
        self.tolerance = tolerance
        self.logger = logging.getLogger(__name__)

        if not PYTHONOCC_AVAILABLE:
            self.logger.warning("PythonOCC not available, classifier functionality limited")

    def classify(self, shape: TopoDS_Shape) -> ClassificationResult:
        """
        Classify a shape and determine optimal mesh type

        Args:
            shape: TopoDS_Shape to classify

        Returns:
            ClassificationResult with mesh type and details

        Example:
            >>> result = classifier.classify(box_shape)
            >>> print(result.mesh_type)  # MeshType.HEXAHEDRAL
        """
        if not PYTHONOCC_AVAILABLE:
            return ClassificationResult(
                mesh_type=MeshType.UNKNOWN,
                shape_type=ShapeType.UNKNOWN,
                confidence=0.0,
                reasons=["PythonOCC not available"]
            )

        self.logger.debug("Classifying shape...")

        # 1. Check for simple box
        if self._is_simple_box(shape):
            return ClassificationResult(
                mesh_type=MeshType.HEXAHEDRAL,
                shape_type=ShapeType.BOX,
                confidence=1.0,
                reasons=["Simple box geometry detected"],
                properties=self._get_box_properties(shape)
            )

        # 2. Check for simple cylinder
        if self._is_simple_cylinder(shape):
            return ClassificationResult(
                mesh_type=MeshType.HEXAHEDRAL,
                shape_type=ShapeType.CYLINDER,
                confidence=0.9,
                reasons=["Simple cylinder geometry detected"],
                properties=self._get_cylinder_properties(shape)
            )

        # 3. Check for sweepable geometry
        if self._is_sweepable(shape):
            return ClassificationResult(
                mesh_type=MeshType.HEXAHEDRAL,
                shape_type=ShapeType.SWEEPABLE,
                confidence=0.8,
                reasons=["Sweepable geometry detected"],
                properties={"sweepable": True}
            )

        # 4. Check for decomposability
        if self._is_decomposable(shape):
            return ClassificationResult(
                mesh_type=MeshType.HYBRID,
                shape_type=ShapeType.COMPLEX,
                confidence=0.6,
                reasons=["Geometry can be decomposed into simpler regions"],
                properties={"decomposable": True}
            )

        # 5. Default to tetrahedral
        return ClassificationResult(
            mesh_type=MeshType.TETRAHEDRAL,
            shape_type=ShapeType.COMPLEX,
            confidence=1.0,
            reasons=["Complex geometry requires tetrahedral mesh"],
            properties={}
        )

    def _is_simple_box(self, shape: TopoDS_Shape) -> bool:
        """
        Check if shape is a simple box

        A simple box has:
        - 6 planar faces
        - 12 straight edges
        - 8 vertices
        - Right angles

        Args:
            shape: Shape to check

        Returns:
            True if shape is a simple box
        """
        if not PYTHONOCC_AVAILABLE:
            return False

        # Count faces
        face_count = 0
        planar_face_count = 0
        exp_face = TopExp_Explorer(shape, TopAbs_FACE)

        while exp_face.More():
            face = exp_face.Current()
            face_count += 1

            # Check if face is planar
            surface = BRepAdaptor_Surface(face)
            if surface.GetType() == GeomAbs_Plane:
                planar_face_count += 1

            exp_face.Next()

        # Box should have exactly 6 planar faces
        if face_count != 6 or planar_face_count != 6:
            return False

        # Count edges
        edge_count = 0
        line_edge_count = 0
        exp_edge = TopExp_Explorer(shape, TopAbs_EDGE)

        while exp_edge.More():
            edge = exp_edge.Current()
            edge_count += 1

            # Check if edge is straight line
            curve = BRepAdaptor_Curve(edge)
            if curve.GetType() == GeomAbs_Line:
                line_edge_count += 1

            exp_edge.Next()

        # Box should have exactly 12 straight edges
        if edge_count != 12 or line_edge_count != 12:
            return False

        # Count vertices
        vertex_count = 0
        exp_vertex = TopExp_Explorer(shape, TopAbs_VERTEX)

        while exp_vertex.More():
            vertex_count += 1
            exp_vertex.Next()

        # Box should have exactly 8 vertices
        if vertex_count != 8:
            return False

        self.logger.debug("Shape identified as simple box")
        return True

    def _is_simple_cylinder(self, shape: TopoDS_Shape) -> bool:
        """
        Check if shape is a simple cylinder

        A simple cylinder has:
        - 2 planar faces (top and bottom)
        - 1 cylindrical face
        - 2 circular edges
        - 1 straight edge (seam edge may or may not be present)

        Args:
            shape: Shape to check

        Returns:
            True if shape is a simple cylinder
        """
        if not PYTHONOCC_AVAILABLE:
            return False

        face_count = 0
        planar_count = 0
        cylindrical_count = 0

        exp_face = TopExp_Explorer(shape, TopAbs_FACE)

        while exp_face.More():
            face = exp_face.Current()
            face_count += 1

            surface = BRepAdaptor_Surface(face)
            surf_type = surface.GetType()

            if surf_type == GeomAbs_Plane:
                planar_count += 1
            elif surf_type == GeomAbs_Cylinder:
                cylindrical_count += 1

            exp_face.Next()

        # Cylinder should have 2 planar faces and 1 cylindrical face
        if face_count == 3 and planar_count == 2 and cylindrical_count == 1:
            self.logger.debug("Shape identified as simple cylinder")
            return True

        return False

    def _is_sweepable(self, shape: TopoDS_Shape) -> bool:
        """
        Check if shape is sweepable (can be generated by extruding a profile)

        A sweepable geometry can be meshed using structured hex elements
        by sweeping a 2D mesh along a path.

        Args:
            shape: Shape to check

        Returns:
            True if shape is sweepable
        """
        if not PYTHONOCC_AVAILABLE:
            return False

        # This is a simplified check
        # A full implementation would:
        # 1. Find potential source/target face pairs
        # 2. Check if faces are similar/parallel
        # 3. Verify sweep direction
        # 4. Check that connecting faces are ruled surfaces

        faces = []
        exp_face = TopExp_Explorer(shape, TopAbs_FACE)

        while exp_face.More():
            faces.append(exp_face.Current())
            exp_face.Next()

        # For now, assume simple geometries with few faces might be sweepable
        if len(faces) <= 6:  # Box-like or simple extrusions
            # Check if there are two parallel planar faces
            planar_faces = []
            for face in faces:
                surface = BRepAdaptor_Surface(face)
                if surface.GetType() == GeomAbs_Plane:
                    planar_faces.append((face, surface))

            if len(planar_faces) >= 2:
                # Check for parallel faces
                for i, (face1, surf1) in enumerate(planar_faces):
                    for face2, surf2 in planar_faces[i+1:]:
                        if self._are_faces_parallel(surf1, surf2):
                            self.logger.debug("Shape identified as sweepable")
                            return True

        return False

    def _are_faces_parallel(self, surf1: 'BRepAdaptor_Surface',
                           surf2: 'BRepAdaptor_Surface') -> bool:
        """
        Check if two planar surfaces are parallel

        Args:
            surf1: First surface
            surf2: Second surface

        Returns:
            True if surfaces are parallel
        """
        if surf1.GetType() != GeomAbs_Plane or surf2.GetType() != GeomAbs_Plane:
            return False

        # Get normals
        pln1 = surf1.Plane()
        pln2 = surf2.Plane()

        normal1 = pln1.Axis().Direction()
        normal2 = pln2.Axis().Direction()

        # Check if normals are parallel (dot product close to ±1)
        dot = abs(normal1.Dot(normal2))

        return abs(dot - 1.0) < self.tolerance

    def _is_decomposable(self, shape: TopoDS_Shape) -> bool:
        """
        Check if shape can be decomposed into simpler regions

        A decomposable shape can be split into multiple regions,
        some of which may be suitable for hex meshing.

        Args:
            shape: Shape to check

        Returns:
            True if shape is decomposable
        """
        if not PYTHONOCC_AVAILABLE:
            return False

        # This is a placeholder implementation
        # Full decomposition would require:
        # 1. Medial axis extraction
        # 2. Feature recognition
        # 3. Boolean operations
        # 4. Complexity analysis

        # For now, return True for moderately complex shapes
        face_count = self._count_faces(shape)

        # Shapes with 7-20 faces might benefit from decomposition
        if 7 <= face_count <= 20:
            self.logger.debug("Shape may be decomposable")
            return True

        return False

    def _count_faces(self, shape: TopoDS_Shape) -> int:
        """Count number of faces in shape"""
        if not PYTHONOCC_AVAILABLE:
            return 0

        count = 0
        exp = TopExp_Explorer(shape, TopAbs_FACE)

        while exp.More():
            count += 1
            exp.Next()

        return count

    def _get_box_properties(self, shape: TopoDS_Shape) -> Dict:
        """Get properties of a box shape"""
        if not PYTHONOCC_AVAILABLE:
            return {}

        # Get bounding box
        bbox = Bnd_Box()
        brepbndlib.Add(shape, bbox)

        xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()

        return {
            'dimensions': {
                'x': xmax - xmin,
                'y': ymax - ymin,
                'z': zmax - zmin
            },
            'center': {
                'x': (xmax + xmin) / 2,
                'y': (ymax + ymin) / 2,
                'z': (zmax + zmin) / 2
            }
        }

    def _get_cylinder_properties(self, shape: TopoDS_Shape) -> Dict:
        """Get properties of a cylinder shape"""
        if not PYTHONOCC_AVAILABLE:
            return {}

        # Find cylindrical face
        exp_face = TopExp_Explorer(shape, TopAbs_FACE)

        while exp_face.More():
            face = exp_face.Current()
            surface = BRepAdaptor_Surface(face)

            if surface.GetType() == GeomAbs_Cylinder:
                cylinder = surface.Cylinder()
                radius = cylinder.Radius()

                # Get bounding box for height
                bbox = Bnd_Box()
                brepbndlib.Add(shape, bbox)
                _, _, zmin, _, _, zmax = bbox.Get()
                height = zmax - zmin

                return {
                    'radius': radius,
                    'height': height,
                    'axis': {
                        'x': cylinder.Axis().Direction().X(),
                        'y': cylinder.Axis().Direction().Y(),
                        'z': cylinder.Axis().Direction().Z()
                    }
                }

            exp_face.Next()

        return {}

    def get_complexity_score(self, shape: TopoDS_Shape) -> float:
        """
        Calculate complexity score for a shape

        Args:
            shape: Shape to analyze

        Returns:
            Complexity score (0-1, higher is more complex)
        """
        if not PYTHONOCC_AVAILABLE:
            return 0.0

        # Count topological entities
        num_faces = self._count_faces(shape)
        num_edges = self._count_edges(shape)

        # Simple heuristic: normalize by typical box counts
        face_complexity = min(num_faces / 20.0, 1.0)
        edge_complexity = min(num_edges / 40.0, 1.0)

        # Weighted average
        complexity = 0.6 * face_complexity + 0.4 * edge_complexity

        return complexity

    def _count_edges(self, shape: TopoDS_Shape) -> int:
        """Count number of edges in shape"""
        if not PYTHONOCC_AVAILABLE:
            return 0

        count = 0
        exp = TopExp_Explorer(shape, TopAbs_EDGE)

        while exp.More():
            count += 1
            exp.Next()

        return count


# Import dataclass after trying PythonOCC imports
from dataclasses import dataclass, field
from typing import Dict
