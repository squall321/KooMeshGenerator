"""
Adaptive Mesh Refinement Module
================================

This module provides adaptive mesh refinement (AMR) capabilities for KooMeshGenerator.

Features:
- Geometry curvature-based refinement
- User-defined refinement zones (Box, Sphere, Cylinder, Custom)
- Multiple refinement strategies
- Integration with GMSH size fields

Usage:
    >>> from koomesh.meshing.adaptive_refiner import AdaptiveMeshRefiner, BoxZone
    >>> refiner = AdaptiveMeshRefiner()
    >>> refiner.add_refinement_zone(BoxZone(center=(5, 5, 5), size=(2, 2, 2), mesh_size=0.1))
    >>> refiner.enable_curvature_refinement(min_points=10)
    >>> refiner.apply_to_gmsh()
"""

import logging
from typing import List, Tuple, Optional, Dict, Callable
from abc import ABC, abstractmethod
from dataclasses import dataclass
import numpy as np

try:
    import gmsh
    GMSH_AVAILABLE = True
except ImportError:
    GMSH_AVAILABLE = False


class RefinementZone(ABC):
    """
    Abstract base class for refinement zones

    Refinement zones define regions where the mesh should be refined
    (i.e., have smaller elements).
    """

    @abstractmethod
    def to_gmsh_field(self, field_id: int) -> int:
        """
        Convert this zone to a GMSH field

        Args:
            field_id: Starting field ID to use

        Returns:
            Next available field ID
        """
        pass

    @abstractmethod
    def get_description(self) -> str:
        """Get human-readable description of this zone"""
        pass


@dataclass
class BoxZone(RefinementZone):
    """
    Box-shaped refinement zone

    Attributes:
        center: Center point (x, y, z)
        size: Box size (width, height, depth)
        mesh_size: Target mesh size in this zone
        transition_distance: Distance over which to transition to background mesh size
    """
    center: Tuple[float, float, float]
    size: Tuple[float, float, float]
    mesh_size: float
    transition_distance: float = 1.0

    def to_gmsh_field(self, field_id: int) -> int:
        """Convert to GMSH Box field"""
        if not GMSH_AVAILABLE:
            raise RuntimeError("GMSH not available")

        # Create Box field
        gmsh.model.mesh.field.add("Box", field_id)

        # Set box boundaries
        x_min = self.center[0] - self.size[0] / 2
        x_max = self.center[0] + self.size[0] / 2
        y_min = self.center[1] - self.size[1] / 2
        y_max = self.center[1] + self.size[1] / 2
        z_min = self.center[2] - self.size[2] / 2
        z_max = self.center[2] + self.size[2] / 2

        gmsh.model.mesh.field.setNumber(field_id, "VIn", self.mesh_size)
        gmsh.model.mesh.field.setNumber(field_id, "VOut", self.mesh_size * 5)  # Outside size
        gmsh.model.mesh.field.setNumber(field_id, "XMin", x_min)
        gmsh.model.mesh.field.setNumber(field_id, "XMax", x_max)
        gmsh.model.mesh.field.setNumber(field_id, "YMin", y_min)
        gmsh.model.mesh.field.setNumber(field_id, "YMax", y_max)
        gmsh.model.mesh.field.setNumber(field_id, "ZMin", z_min)
        gmsh.model.mesh.field.setNumber(field_id, "ZMax", z_max)
        gmsh.model.mesh.field.setNumber(field_id, "Thickness", self.transition_distance)

        return field_id + 1

    def get_description(self) -> str:
        return (f"Box at {self.center}, size {self.size}, "
                f"mesh size {self.mesh_size}")


@dataclass
class SphereZone(RefinementZone):
    """
    Sphere-shaped refinement zone

    Attributes:
        center: Center point (x, y, z)
        radius: Sphere radius
        mesh_size: Target mesh size in this zone
        transition_distance: Distance over which to transition
    """
    center: Tuple[float, float, float]
    radius: float
    mesh_size: float
    transition_distance: float = 1.0

    def to_gmsh_field(self, field_id: int) -> int:
        """Convert to GMSH Ball (sphere) field"""
        if not GMSH_AVAILABLE:
            raise RuntimeError("GMSH not available")

        # Create Ball field
        gmsh.model.mesh.field.add("Ball", field_id)

        gmsh.model.mesh.field.setNumber(field_id, "VIn", self.mesh_size)
        gmsh.model.mesh.field.setNumber(field_id, "VOut", self.mesh_size * 5)
        gmsh.model.mesh.field.setNumber(field_id, "XCenter", self.center[0])
        gmsh.model.mesh.field.setNumber(field_id, "YCenter", self.center[1])
        gmsh.model.mesh.field.setNumber(field_id, "ZCenter", self.center[2])
        gmsh.model.mesh.field.setNumber(field_id, "Radius", self.radius)
        gmsh.model.mesh.field.setNumber(field_id, "Thickness", self.transition_distance)

        return field_id + 1

    def get_description(self) -> str:
        return (f"Sphere at {self.center}, radius {self.radius}, "
                f"mesh size {self.mesh_size}")


@dataclass
class CylinderZone(RefinementZone):
    """
    Cylinder-shaped refinement zone

    Attributes:
        center: Center point (x, y, z)
        axis: Cylinder axis direction (x, y, z) - will be normalized
        radius: Cylinder radius
        height: Cylinder height
        mesh_size: Target mesh size in this zone
        transition_distance: Distance over which to transition
    """
    center: Tuple[float, float, float]
    axis: Tuple[float, float, float]
    radius: float
    height: float
    mesh_size: float
    transition_distance: float = 1.0

    def to_gmsh_field(self, field_id: int) -> int:
        """Convert to GMSH Cylinder field"""
        if not GMSH_AVAILABLE:
            raise RuntimeError("GMSH not available")

        # Create Cylinder field
        gmsh.model.mesh.field.add("Cylinder", field_id)

        # Normalize axis
        axis_array = np.array(self.axis)
        axis_norm = axis_array / np.linalg.norm(axis_array)

        gmsh.model.mesh.field.setNumber(field_id, "VIn", self.mesh_size)
        gmsh.model.mesh.field.setNumber(field_id, "VOut", self.mesh_size * 5)
        gmsh.model.mesh.field.setNumber(field_id, "XCenter", self.center[0])
        gmsh.model.mesh.field.setNumber(field_id, "YCenter", self.center[1])
        gmsh.model.mesh.field.setNumber(field_id, "ZCenter", self.center[2])
        gmsh.model.mesh.field.setNumber(field_id, "XAxis", axis_norm[0])
        gmsh.model.mesh.field.setNumber(field_id, "YAxis", axis_norm[1])
        gmsh.model.mesh.field.setNumber(field_id, "ZAxis", axis_norm[2])
        gmsh.model.mesh.field.setNumber(field_id, "Radius", self.radius)

        return field_id + 1

    def get_description(self) -> str:
        return (f"Cylinder at {self.center}, axis {self.axis}, "
                f"radius {self.radius}, mesh size {self.mesh_size}")


@dataclass
class DistanceToSurfaceZone(RefinementZone):
    """
    Refinement zone based on distance to specific surfaces

    Attributes:
        surface_tags: List of GMSH surface tags
        mesh_size_near: Mesh size near the surface
        mesh_size_far: Mesh size far from the surface
        distance_near: Distance considered "near"
        distance_far: Distance considered "far"
    """
    surface_tags: List[int]
    mesh_size_near: float
    mesh_size_far: float
    distance_near: float = 0.5
    distance_far: float = 2.0

    def to_gmsh_field(self, field_id: int) -> int:
        """Convert to GMSH Distance field + Threshold field"""
        if not GMSH_AVAILABLE:
            raise RuntimeError("GMSH not available")

        # Create Distance field
        distance_field_id = field_id
        gmsh.model.mesh.field.add("Distance", distance_field_id)
        gmsh.model.mesh.field.setNumbers(distance_field_id, "SurfacesList",
                                        self.surface_tags)

        # Create Threshold field (interpolate based on distance)
        threshold_field_id = field_id + 1
        gmsh.model.mesh.field.add("Threshold", threshold_field_id)
        gmsh.model.mesh.field.setNumber(threshold_field_id, "InField",
                                       distance_field_id)
        gmsh.model.mesh.field.setNumber(threshold_field_id, "SizeMin",
                                       self.mesh_size_near)
        gmsh.model.mesh.field.setNumber(threshold_field_id, "SizeMax",
                                       self.mesh_size_far)
        gmsh.model.mesh.field.setNumber(threshold_field_id, "DistMin",
                                       self.distance_near)
        gmsh.model.mesh.field.setNumber(threshold_field_id, "DistMax",
                                       self.distance_far)

        return field_id + 2

    def get_description(self) -> str:
        return (f"Distance to surfaces {self.surface_tags}, "
                f"near size {self.mesh_size_near}, far size {self.mesh_size_far}")


class AdaptiveMeshRefiner:
    """
    Adaptive Mesh Refinement Manager

    This class manages multiple refinement zones and applies them to GMSH.
    It can combine multiple refinement strategies including:
    - User-defined geometric zones
    - Curvature-based refinement
    - Distance-based refinement

    Example:
        >>> refiner = AdaptiveMeshRefiner(base_mesh_size=1.0)
        >>> refiner.add_refinement_zone(BoxZone((5, 5, 5), (2, 2, 2), 0.1))
        >>> refiner.add_refinement_zone(SphereZone((10, 10, 10), 3.0, 0.2))
        >>> refiner.enable_curvature_refinement(min_points_per_curve=15)
        >>> refiner.apply_to_gmsh()
    """

    def __init__(self, base_mesh_size: float = 1.0):
        """
        Initialize adaptive refiner

        Args:
            base_mesh_size: Background (default) mesh size
        """
        self.logger = logging.getLogger(__name__)
        self.base_mesh_size = base_mesh_size
        self.zones: List[RefinementZone] = []
        self.curvature_enabled = False
        self.curvature_params = {}

        if not GMSH_AVAILABLE:
            self.logger.error("GMSH is not installed")
            raise RuntimeError("GMSH not available")

    def add_refinement_zone(self, zone: RefinementZone):
        """
        Add a refinement zone

        Args:
            zone: RefinementZone object
        """
        self.zones.append(zone)
        self.logger.info(f"Added refinement zone: {zone.get_description()}")

    def enable_curvature_refinement(self,
                                   min_points_per_curve: int = 10,
                                   min_points_per_circle: int = 20):
        """
        Enable curvature-based refinement

        GMSH will automatically refine mesh based on geometry curvature.

        Args:
            min_points_per_curve: Minimum number of points to discretize curves
            min_points_per_circle: Minimum number of points for a full circle
        """
        self.curvature_enabled = True
        self.curvature_params = {
            'min_points_per_curve': min_points_per_curve,
            'min_points_per_circle': min_points_per_circle
        }
        self.logger.info(f"Enabled curvature refinement: "
                        f"{min_points_per_curve} points/curve, "
                        f"{min_points_per_circle} points/circle")

    def apply_to_gmsh(self, combine_strategy: str = "min"):
        """
        Apply all refinement zones to GMSH

        Args:
            combine_strategy: How to combine multiple fields
                - "min": Take minimum mesh size (finest mesh)
                - "max": Take maximum mesh size (coarsest mesh)
                - "mean": Take average mesh size
        """
        if not GMSH_AVAILABLE:
            raise RuntimeError("GMSH not available")

        self.logger.info("Applying adaptive mesh refinement to GMSH...")

        # Set base mesh size
        gmsh.option.setNumber("Mesh.CharacteristicLengthMin",
                             self.base_mesh_size * 0.1)
        gmsh.option.setNumber("Mesh.CharacteristicLengthMax",
                             self.base_mesh_size * 2.0)

        # Apply curvature refinement if enabled
        if self.curvature_enabled:
            gmsh.option.setNumber("Mesh.CharacteristicLengthFromCurvature", 1)
            gmsh.option.setNumber("Mesh.MinimumCircleNodes",
                                 self.curvature_params['min_points_per_circle'])
            gmsh.option.setNumber("Mesh.MinimumCurveNodes",
                                 self.curvature_params['min_points_per_curve'])
            self.logger.info("Applied curvature-based refinement")

        # Apply refinement zones
        if len(self.zones) == 0:
            self.logger.warning("No refinement zones defined")
            return

        # Create GMSH fields for each zone
        field_ids = []
        next_field_id = 1

        for zone in self.zones:
            self.logger.debug(f"Creating field for: {zone.get_description()}")
            next_field_id = zone.to_gmsh_field(next_field_id)
            field_ids.append(next_field_id - 1)  # The last created field

        # Combine all fields using Min/Max/Mean
        if len(field_ids) > 1:
            combine_field_id = next_field_id

            if combine_strategy == "min":
                gmsh.model.mesh.field.add("Min", combine_field_id)
            elif combine_strategy == "max":
                gmsh.model.mesh.field.add("Max", combine_field_id)
            elif combine_strategy == "mean":
                gmsh.model.mesh.field.add("Mean", combine_field_id)
            else:
                raise ValueError(f"Unknown combine strategy: {combine_strategy}")

            gmsh.model.mesh.field.setNumbers(combine_field_id, "FieldsList",
                                            field_ids)

            # Set as background field
            gmsh.model.mesh.field.setAsBackgroundMesh(combine_field_id)
            self.logger.info(f"Combined {len(field_ids)} fields using {combine_strategy}")
        elif len(field_ids) == 1:
            # Only one field, use it directly
            gmsh.model.mesh.field.setAsBackgroundMesh(field_ids[0])
            self.logger.info("Applied single refinement field")

        self.logger.info("Adaptive mesh refinement applied successfully")

    def get_summary(self) -> Dict:
        """
        Get summary of refinement configuration

        Returns:
            Dictionary with refinement summary
        """
        return {
            'base_mesh_size': self.base_mesh_size,
            'num_zones': len(self.zones),
            'zones': [zone.get_description() for zone in self.zones],
            'curvature_enabled': self.curvature_enabled,
            'curvature_params': self.curvature_params if self.curvature_enabled else None
        }

    def clear_zones(self):
        """Clear all refinement zones"""
        self.zones.clear()
        self.logger.info("Cleared all refinement zones")

    def remove_zone(self, index: int):
        """
        Remove a refinement zone by index

        Args:
            index: Zone index (0-based)
        """
        if 0 <= index < len(self.zones):
            zone = self.zones.pop(index)
            self.logger.info(f"Removed zone: {zone.get_description()}")
        else:
            raise IndexError(f"Zone index {index} out of range")


def create_refinement_from_stress_concentrations(
    stress_points: List[Tuple[float, float, float]],
    base_size: float = 1.0,
    fine_size: float = 0.1,
    radius: float = 2.0
) -> AdaptiveMeshRefiner:
    """
    Create refinement configuration from known stress concentration points

    This is useful when you know where high stresses will occur
    (e.g., from a previous analysis or engineering judgment).

    Args:
        stress_points: List of (x, y, z) points where stress concentrates
        base_size: Base mesh size
        fine_size: Fine mesh size at concentration points
        radius: Radius of refinement sphere around each point

    Returns:
        Configured AdaptiveMeshRefiner

    Example:
        >>> points = [(5, 5, 0), (15, 15, 0)]  # Known stress points
        >>> refiner = create_refinement_from_stress_concentrations(points)
        >>> refiner.apply_to_gmsh()
    """
    refiner = AdaptiveMeshRefiner(base_mesh_size=base_size)

    for point in stress_points:
        zone = SphereZone(
            center=point,
            radius=radius,
            mesh_size=fine_size,
            transition_distance=radius * 0.5
        )
        refiner.add_refinement_zone(zone)

    return refiner


def create_boundary_layer_refinement(
    surface_tags: List[int],
    first_layer_size: float = 0.01,
    growth_rate: float = 1.3,
    num_layers: int = 5
) -> AdaptiveMeshRefiner:
    """
    Create refinement for boundary layer meshing

    Useful for CFD or contact simulations where you need fine mesh
    near surfaces.

    Args:
        surface_tags: GMSH surface tags to refine near
        first_layer_size: Size of first element layer
        growth_rate: Growth rate for subsequent layers
        num_layers: Number of boundary layers

    Returns:
        Configured AdaptiveMeshRefiner
    """
    refiner = AdaptiveMeshRefiner(base_mesh_size=1.0)

    # Calculate distances and sizes for each layer
    current_distance = 0.0
    current_size = first_layer_size

    for layer in range(num_layers):
        next_distance = current_distance + current_size
        next_size = current_size * growth_rate

        zone = DistanceToSurfaceZone(
            surface_tags=surface_tags,
            mesh_size_near=current_size,
            mesh_size_far=next_size,
            distance_near=current_distance,
            distance_far=next_distance
        )
        refiner.add_refinement_zone(zone)

        current_distance = next_distance
        current_size = next_size

    return refiner
