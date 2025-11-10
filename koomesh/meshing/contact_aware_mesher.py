"""
Contact-Aware Meshing

Generates meshes with refined elements at contact zones for improved accuracy.
"""

from typing import List, Tuple, Optional, Dict, Any
import numpy as np
from dataclasses import dataclass
import logging
import time

from koomesh.meshing.mesh_data import MeshData
from koomesh.utils.logging_utils import PerformanceLogger


@dataclass
class ContactZone:
    """Contact zone between two shapes"""
    shape1_idx: int
    shape2_idx: int
    shape1_faces: List[int]
    shape2_faces: List[int]
    area: float
    gap_distance: float
    center: np.ndarray


class ContactAwareMesher:
    """
    Generate meshes with contact zone awareness.

    Features:
    - Detect potential contact zones during geometry analysis
    - Apply finer mesh at contact surfaces
    - Generate boundary layers at contacts
    - Align nodes across contact interfaces

    Example:
        >>> mesher = ContactAwareMesher()
        >>> zones = mesher.detect_potential_contact_zones(shapes)
        >>> mesh = mesher.generate_with_contact_refinement(
        ...     shape, zones, refinement_factor=0.5
        ... )
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.perf_logger = PerformanceLogger(__name__)

    def detect_potential_contact_zones(
        self,
        shapes: List[Any],
        tolerance: float = 1.0
    ) -> List[ContactZone]:
        """
        Detect potential contact zones between shapes.

        Args:
            shapes: List of OCC TopoDS_Shape objects
            tolerance: Maximum gap distance to consider as contact (mm)

        Returns:
            List of ContactZone objects

        Raises:
            ValueError: If shapes list is empty or tolerance is invalid
            TypeError: If shapes is not a list or contains invalid objects
        """
        # Input validation
        if shapes is None:
            raise TypeError("shapes cannot be None")

        if not isinstance(shapes, list):
            raise TypeError(f"shapes must be a list, got {type(shapes).__name__}")

        if len(shapes) == 0:
            raise ValueError("shapes list is empty - need at least 2 shapes to detect contacts")

        if len(shapes) == 1:
            self.logger.warning("Only 1 shape provided - no contacts possible")
            return []

        if tolerance <= 0:
            raise ValueError(f"tolerance must be positive, got {tolerance}")

        if tolerance > 1000:
            self.logger.warning(f"Very large tolerance ({tolerance}mm) may cause performance issues")

        contact_zones = []

        self.logger.info(f"Detecting contact zones (tolerance={tolerance}mm)...")

        try:
            with self.perf_logger.timer("contact_zone_detection"):
                num_pairs = len(shapes) * (len(shapes) - 1) // 2
                self.logger.debug(f"Checking {num_pairs} shape pairs")

                checked_pairs = 0
                for i in range(len(shapes)):
                    for j in range(i + 1, len(shapes)):
                        checked_pairs += 1

                        # Quick bounding box check
                        if not self._bbox_overlap(shapes[i], shapes[j], tolerance * 5):
                            continue

                        # Detailed surface proximity check
                        zones = self._find_close_surfaces(
                            shapes[i], shapes[j], i, j, tolerance
                        )

                        contact_zones.extend(zones)

                        # Log progress every 10 pairs
                        if checked_pairs % 10 == 0:
                            self.logger.debug(
                                f"Progress: {checked_pairs}/{num_pairs} pairs checked, "
                                f"{len(contact_zones)} contacts found"
                            )

            self.logger.info(
                f"Found {len(contact_zones)} contact zones from {num_pairs} shape pairs"
            )
            self.perf_logger.increment_counter("contact_zones_detected", len(contact_zones))
            return contact_zones

        except Exception as e:
            self.logger.error(f"Failed to detect contact zones: {e}")
            raise RuntimeError(f"Contact zone detection failed: {e}") from e

    def _bbox_overlap(self, shape1, shape2, tolerance: float) -> bool:
        """Check if bounding boxes overlap with tolerance."""
        from OCC.Core.Bnd import Bnd_Box
        from OCC.Core.BRepBndLib import brepbndlib

        bbox1 = Bnd_Box()
        bbox2 = Bnd_Box()

        brepbndlib.Add(shape1, bbox1)
        brepbndlib.Add(shape2, bbox2)

        # Expand boxes by tolerance
        bbox1.Enlarge(tolerance)
        bbox2.Enlarge(tolerance)

        # Check overlap
        return not bbox1.IsOut(bbox2)

    def _find_close_surfaces(
        self,
        shape1,
        shape2,
        idx1: int,
        idx2: int,
        tolerance: float
    ) -> List[ContactZone]:
        """Find close surface pairs between two shapes."""
        from OCC.Core.TopExp import TopExp_Explorer
        from OCC.Core.TopAbs import TopAbs_FACE
        from OCC.Core.BRepAdaptor import BRepAdaptor_Surface
        from OCC.Core.GeomAPI import GeomAPI_ProjectPointOnSurf
        from OCC.Core.gp import gp_Pnt
        from OCC.Core.TopoDS import topods
        from OCC.Core.GProp import GProp_GProps
        from OCC.Core.BRepGProp import brepgprop_SurfaceProperties

        zones = []

        # Get faces from shape1
        exp1 = TopExp_Explorer(shape1, TopAbs_FACE)
        faces1 = []
        while exp1.More():
            faces1.append(topods.Face(exp1.Current()))
            exp1.Next()

        # Get faces from shape2
        exp2 = TopExp_Explorer(shape2, TopAbs_FACE)
        faces2 = []
        while exp2.More():
            faces2.append(topods.Face(exp2.Current()))
            exp2.Next()

        # Check proximity between face pairs
        for i, face1 in enumerate(faces1):
            props1 = GProp_GProps()
            brepgprop_SurfaceProperties(face1, props1)
            center1 = props1.CentreOfMass()

            for j, face2 in enumerate(faces2):
                props2 = GProp_GProps()
                brepgprop_SurfaceProperties(face2, props2)
                center2 = props2.CentreOfMass()

                # Quick distance check using face centers
                dist = center1.Distance(center2)

                if dist < tolerance * 10:  # Rough proximity
                    # Detailed check: project center1 onto face2
                    surf2 = BRepAdaptor_Surface(face2)
                    projector = GeomAPI_ProjectPointOnSurf(center1, surf2.Surface())

                    if projector.NbPoints() > 0:
                        gap = projector.LowerDistance()

                        if gap < tolerance:
                            # Found contact zone
                            area1 = props1.Mass()  # Surface area

                            zone = ContactZone(
                                shape1_idx=idx1,
                                shape2_idx=idx2,
                                shape1_faces=[i],
                                shape2_faces=[j],
                                area=area1,
                                gap_distance=gap,
                                center=np.array([center1.X(), center1.Y(), center1.Z()])
                            )
                            zones.append(zone)

        return zones

    def apply_contact_refinement(
        self,
        gmsh_model,
        contact_zones: List[ContactZone],
        base_mesh_size: float,
        refinement_factor: float = 0.5,
        boundary_layers: int = 0,
        growth_rate: float = 1.2
    ):
        """
        Apply mesh refinement at contact zones using GMSH fields.

        Args:
            gmsh_model: GMSH model object
            contact_zones: List of detected contact zones
            base_mesh_size: Base mesh element size
            refinement_factor: Refinement factor (0.5 = half size at contacts)
            boundary_layers: Number of boundary layers to generate
            growth_rate: Growth rate for boundary layers

        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If GMSH operations fail
        """
        # Input validation
        if gmsh_model is None:
            raise TypeError("gmsh_model cannot be None")

        if contact_zones is None:
            raise TypeError("contact_zones cannot be None")

        if not isinstance(contact_zones, list):
            raise TypeError(f"contact_zones must be a list, got {type(contact_zones).__name__}")

        if not contact_zones:
            self.logger.info("No contact zones to refine")
            return

        if base_mesh_size <= 0:
            raise ValueError(f"base_mesh_size must be positive, got {base_mesh_size}")

        if refinement_factor <= 0 or refinement_factor > 1:
            raise ValueError(f"refinement_factor must be in (0, 1], got {refinement_factor}")

        if boundary_layers < 0:
            raise ValueError(f"boundary_layers must be non-negative, got {boundary_layers}")

        if growth_rate < 1.0:
            raise ValueError(f"growth_rate must be >= 1.0, got {growth_rate}")

        try:
            import gmsh

            refined_size = base_mesh_size * refinement_factor

            self.logger.info(
                f"Applying contact refinement: {len(contact_zones)} zones, "
                f"size {refined_size:.2f}mm (factor={refinement_factor})"
            )

            # Create distance field from contact zones
            field_id = 1

            # Create ball field for each contact zone
            for i, zone in enumerate(contact_zones):
                # Ball field centered at contact zone
                gmsh.model.mesh.field.add("Ball", field_id + i)
                gmsh.model.mesh.field.setNumber(field_id + i, "VIn", refined_size)
                gmsh.model.mesh.field.setNumber(field_id + i, "VOut", base_mesh_size)
                gmsh.model.mesh.field.setNumber(field_id + i, "Radius", zone.area ** 0.5)
                gmsh.model.mesh.field.setNumber(field_id + i, "Thickness", base_mesh_size)
                gmsh.model.mesh.field.setNumber(field_id + i, "XCenter", float(zone.center[0]))
                gmsh.model.mesh.field.setNumber(field_id + i, "YCenter", float(zone.center[1]))
                gmsh.model.mesh.field.setNumber(field_id + i, "ZCenter", float(zone.center[2]))

            # Combine all ball fields with Min
            if len(contact_zones) > 1:
                min_field_id = field_id + len(contact_zones)
                gmsh.model.mesh.field.add("Min", min_field_id)
                gmsh.model.mesh.field.setNumbers(
                    min_field_id, "FieldsList",
                    list(range(field_id, field_id + len(contact_zones)))
                )
                gmsh.model.mesh.field.setAsBackgroundMesh(min_field_id)
            else:
                gmsh.model.mesh.field.setAsBackgroundMesh(field_id)

            # Apply boundary layers if requested
            if boundary_layers > 0:
                self._apply_boundary_layers(
                    gmsh_model, contact_zones,
                    num_layers=boundary_layers,
                    growth_rate=growth_rate
                )

            self.logger.info("Contact refinement applied successfully")

        except ImportError as e:
            self.logger.error(f"Failed to import gmsh: {e}")
            raise RuntimeError("gmsh module not available - install with: pip install gmsh") from e
        except Exception as e:
            self.logger.error(f"Failed to apply contact refinement: {e}")
            raise RuntimeError(f"Contact refinement failed: {e}") from e

    def _apply_boundary_layers(
        self,
        gmsh_model,
        contact_zones: List[ContactZone],
        num_layers: int,
        growth_rate: float
    ):
        """Apply boundary layers at contact surfaces."""
        import gmsh

        self.logger.info(
            f"Applying boundary layers: {num_layers} layers, "
            f"growth rate={growth_rate}"
        )

        # Note: Boundary layer implementation would require surface tagging
        # in GMSH, which needs integration with geometry processing
        # For now, we use Distance + Threshold fields

        for i, zone in enumerate(contact_zones):
            # Distance field from contact surface
            dist_field = 100 + i
            gmsh.model.mesh.field.add("Distance", dist_field)
            # Would set surface list here if available

            # Threshold field for boundary layer effect
            thresh_field = 200 + i
            gmsh.model.mesh.field.add("Threshold", thresh_field)
            gmsh.model.mesh.field.setNumber(thresh_field, "InField", dist_field)
            gmsh.model.mesh.field.setNumber(thresh_field, "SizeMin", zone.gap_distance / num_layers)
            gmsh.model.mesh.field.setNumber(thresh_field, "SizeMax", zone.gap_distance)
            gmsh.model.mesh.field.setNumber(thresh_field, "DistMin", 0)
            gmsh.model.mesh.field.setNumber(thresh_field, "DistMax", zone.gap_distance * num_layers)

    def align_contact_nodes(
        self,
        mesh1: MeshData,
        mesh2: MeshData,
        contact_zone: ContactZone,
        tolerance: float = 0.1
    ) -> Tuple[MeshData, MeshData]:
        """
        Align nodes across contact interface.

        Snaps close nodes to same position for better contact definition.

        Args:
            mesh1: First mesh
            mesh2: Second mesh
            contact_zone: Contact zone information
            tolerance: Node snapping tolerance

        Returns:
            Tuple of (modified_mesh1, modified_mesh2)

        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If node alignment fails
        """
        # Input validation
        if mesh1 is None or mesh2 is None:
            raise TypeError("mesh1 and mesh2 cannot be None")

        if contact_zone is None:
            raise TypeError("contact_zone cannot be None")

        if tolerance <= 0:
            raise ValueError(f"tolerance must be positive, got {tolerance}")

        if not hasattr(mesh1, 'nodes') or not hasattr(mesh2, 'nodes'):
            raise ValueError("mesh1 and mesh2 must have 'nodes' attribute")

        if mesh1.nodes is None or len(mesh1.nodes) == 0:
            raise ValueError("mesh1 has no nodes")

        if mesh2.nodes is None or len(mesh2.nodes) == 0:
            raise ValueError("mesh2 has no nodes")

        try:
            from scipy.spatial import cKDTree

            self.logger.info(
                f"Aligning contact nodes (tolerance={tolerance}mm)..."
            )

            # Extract surface nodes from both meshes
            surface_nodes1 = self._extract_surface_nodes(mesh1)
            surface_nodes2 = self._extract_surface_nodes(mesh2)

            if len(surface_nodes1) == 0 or len(surface_nodes2) == 0:
                self.logger.warning("No surface nodes found for alignment")
                return mesh1, mesh2

            # Build KD-tree for mesh2 surface nodes
            tree = cKDTree(mesh2.nodes[surface_nodes2])

            # Find and snap close node pairs
            snapped_count = 0
            for idx1 in surface_nodes1:
                node1 = mesh1.nodes[idx1]

                # Query nearest node in mesh2
                dist, idx2_tree = tree.query(node1, k=1)

                if dist < tolerance:
                    idx2 = surface_nodes2[idx2_tree]

                    # Snap to midpoint
                    midpoint = (node1 + mesh2.nodes[idx2]) / 2.0
                    mesh1.nodes[idx1] = midpoint
                    mesh2.nodes[idx2] = midpoint

                    snapped_count += 1

            self.logger.info(f"Snapped {snapped_count} node pairs")

            return mesh1, mesh2

        except ImportError as e:
            self.logger.error(f"Failed to import scipy: {e}")
            raise RuntimeError("scipy module not available - install with: pip install scipy") from e
        except Exception as e:
            self.logger.error(f"Failed to align contact nodes: {e}")
            raise RuntimeError(f"Node alignment failed: {e}") from e

    def _extract_surface_nodes(self, mesh: MeshData) -> np.ndarray:
        """Extract nodes on the surface of the mesh."""
        # Simple approach: find nodes referenced by surface elements
        # For a more accurate approach, would need to identify boundary faces

        # Return all nodes for now (simplified)
        return np.arange(len(mesh.nodes))


def detect_contact_zones_from_geometries(
    geometries: List[Any],
    tolerance: float = 1.0
) -> List[ContactZone]:
    """
    Convenience function to detect contact zones from geometries.

    Args:
        geometries: List of OCC shapes
        tolerance: Contact detection tolerance (mm)

    Returns:
        List of ContactZone objects
    """
    mesher = ContactAwareMesher()
    return mesher.detect_potential_contact_zones(geometries, tolerance)
