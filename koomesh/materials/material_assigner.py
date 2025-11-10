"""
Automatic Material Assignment

Assigns materials based on geometry properties, filenames, and templates.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import fnmatch
import logging

from koomesh.materials.material_library import MaterialLibrary


class GeometryBasedMaterialAssigner:
    """
    Automatically assign materials based on geometry characteristics.

    Assignment strategies:
    1. Filename pattern matching
    2. Geometry properties (thickness, volume)
    3. Assembly hierarchy
    4. Template-based rules

    Example:
        >>> assigner = GeometryBasedMaterialAssigner()
        >>> assignments = assigner.assign_by_filename(
        ...     parts, rules={'*hood*.step': 'Aluminum_5052'}
        ... )
        >>> assignments = assigner.assign_by_geometry(parts)
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.material_library = MaterialLibrary()

    def assign_by_filename(
        self,
        part_files: List[Path],
        rules: Dict[str, str]
    ) -> Dict[int, str]:
        """
        Assign materials based on filename patterns.

        Args:
            part_files: List of part file paths
            rules: Dictionary of {pattern: material_name}
                   e.g., {'*hood*.step': 'Aluminum_5052'}

        Returns:
            Dictionary of {part_index: material_name}

        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If assignment fails

        Example Rules:
            {
                '*steel*.step': 'Steel_Mild',
                '*aluminum*.step': 'Aluminum_6061',
                'hood*.step': 'Aluminum_5052',
                'floor*.step': 'Steel_HighStrength',
                'bumper*.step': 'Plastic_PP'
            }
        """
        # Input validation
        if part_files is None or not isinstance(part_files, list):
            raise TypeError("part_files must be a list")

        if len(part_files) == 0:
            raise ValueError("part_files list is empty")

        if rules is None or not isinstance(rules, dict):
            raise TypeError("rules must be a dictionary")

        if len(rules) == 0:
            self.logger.warning("No rules provided - no assignments will be made")
            return {}

        try:
            assignments = {}

            for i, filepath in enumerate(part_files):
                filename = filepath.name.lower()

                # Try each rule in order
                for pattern, material in rules.items():
                    if fnmatch.fnmatch(filename, pattern.lower()):
                        assignments[i] = material
                        self.logger.info(
                            f"Assigned {material} to {filepath.name} "
                            f"(matched pattern '{pattern}')"
                        )
                        break

            self.logger.info(
                f"Filename-based assignment: {len(assignments)}/{len(part_files)} parts"
            )

            return assignments

        except Exception as e:
            self.logger.error(f"Filename-based assignment failed: {e}")
            raise RuntimeError(f"Material assignment by filename failed: {e}") from e

    def assign_by_geometry(
        self,
        geometries: List[Any],
        part_names: List[str]
    ) -> Dict[int, str]:
        """
        Assign materials based on geometry characteristics.

        Rules:
        - Thin shells (thickness < 2mm) → Sheet metal
        - Small parts (volume < 100cm³) → Fasteners
        - Large parts (volume > 10000cm³) → Structural
        - Medium parts → Standard steel

        Args:
            geometries: List of OCC TopoDS_Shape objects
            part_names: Names of parts

        Returns:
            Dictionary of {part_index: material_name}
        """
        assignments = {}

        for i, (geometry, name) in enumerate(zip(geometries, part_names)):
            # Estimate geometry properties
            thickness = self._estimate_thickness(geometry)
            volume = self._calculate_volume(geometry)

            # Apply rules
            if thickness > 0 and thickness < 2.0:
                # Sheet metal
                if volume < 1000:  # cm³
                    material = 'Steel_HighStrength'  # Thin high-strength
                else:
                    material = 'Steel_Mild'  # Larger panels

            elif volume < 100:
                # Small parts - fasteners
                material = 'Steel_Fastener'

            elif volume > 10000:
                # Large structural parts - use lighter material
                material = 'Aluminum_Structure'

            else:
                # Medium parts - standard steel
                material = 'Steel_Mild'

            assignments[i] = material

            self.logger.info(
                f"Assigned {material} to {name} "
                f"(thickness={thickness:.2f}mm, volume={volume:.0f}cm³)"
            )

        return assignments

    def assign_by_template(
        self,
        part_names: List[str],
        template_rules: Dict[str, str]
    ) -> Dict[int, str]:
        """
        Assign materials based on template rules.

        Args:
            part_names: List of part names
            template_rules: Dictionary of {part_pattern: material_name}

        Returns:
            Dictionary of {part_index: material_name}

        Example Template Rules (automotive_crash):
            {
                'bumper': 'Plastic_PP',
                'hood': 'Aluminum_5052',
                'door_outer': 'Steel_Mild',
                'door_inner': 'Steel_HighStrength',
                'floor': 'Steel_HighStrength',
                'pillar': 'Steel_UltraHighStrength',
                'roof': 'Steel_Mild'
            }
        """
        assignments = {}

        for i, name in enumerate(part_names):
            name_lower = name.lower()

            # Check each template rule
            for pattern, material in template_rules.items():
                if pattern.lower() in name_lower:
                    assignments[i] = material
                    self.logger.info(
                        f"Assigned {material} to {name} "
                        f"(template rule '{pattern}')"
                    )
                    break

        self.logger.info(
            f"Template-based assignment: {len(assignments)}/{len(part_names)} parts"
        )

        return assignments

    def _estimate_thickness(self, geometry: Any) -> float:
        """
        Estimate thickness of geometry.

        For shells, returns minimum dimension of bounding box.
        """
        try:
            from OCC.Core.Bnd import Bnd_Box
            from OCC.Core.BRepBndLib import brepbndlib

            bbox = Bnd_Box()
            brepbndlib.Add(geometry, bbox)

            xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()

            # Dimensions
            dx = xmax - xmin
            dy = ymax - ymin
            dz = zmax - zmin

            # Thickness = minimum dimension
            thickness = min(dx, dy, dz)

            return thickness

        except:
            return 0.0

    def _calculate_volume(self, geometry: Any) -> float:
        """
        Calculate volume of geometry (cm³).
        """
        try:
            from OCC.Core.GProp import GProp_GProps
            from OCC.Core.BRepGProp import brepgprop_VolumeProperties

            props = GProp_GProps()
            brepgprop_VolumeProperties(geometry, props)

            # Volume in mm³, convert to cm³
            volume_mm3 = props.Mass()
            volume_cm3 = volume_mm3 / 1000.0

            return volume_cm3

        except:
            return 0.0


class MaterialRuleEngine:
    """
    Material assignment rules for different industries.
    """

    @staticmethod
    def get_automotive_rules() -> Dict[str, str]:
        """
        Material rules for automotive parts.

        Based on typical automotive BIW (Body-In-White) construction.
        """
        return {
            # Exterior panels
            'bumper': 'Plastic_PP',
            'hood': 'Aluminum_5052',
            'fender': 'Aluminum_5052',
            'door_outer': 'Steel_Mild',
            'roof': 'Steel_Mild',
            'decklid': 'Aluminum_5052',
            'tailgate': 'Aluminum_5052',

            # Structural
            'floor': 'Steel_HighStrength',
            'rocker': 'Steel_HighStrength',
            'sill': 'Steel_HighStrength',
            'rail': 'Steel_HighStrength',
            'tunnel': 'Steel_HighStrength',

            # Pillars (critical strength)
            'pillar_a': 'Steel_UltraHighStrength',
            'pillar_b': 'Steel_UltraHighStrength',
            'pillar_c': 'Steel_HighStrength',
            'a_pillar': 'Steel_UltraHighStrength',
            'b_pillar': 'Steel_UltraHighStrength',
            'c_pillar': 'Steel_HighStrength',

            # Inner panels
            'door_inner': 'Steel_HighStrength',
            'door_beam': 'Steel_UltraHighStrength',

            # Interior
            'dashboard': 'Plastic_ABS',
            'console': 'Plastic_ABS',
            'seat_frame': 'Steel_HighStrength',
            'seat_cushion': 'Foam_Polyurethane',

            # Fasteners
            'bolt': 'Steel_Fastener',
            'nut': 'Steel_Fastener',
            'screw': 'Steel_Fastener',
            'rivet': 'Aluminum_Rivet'
        }

    @staticmethod
    def get_aerospace_rules() -> Dict[str, str]:
        """Material rules for aerospace parts."""
        return {
            'skin': 'Aluminum_2024',
            'spar': 'Aluminum_7075',
            'rib': 'Aluminum_2024',
            'frame': 'Aluminum_7075',
            'stringer': 'Aluminum_7075',
            'bulkhead': 'Aluminum_7075',
            'panel': 'Aluminum_2024',
            'bracket': 'Titanium_Ti6Al4V',
            'fitting': 'Steel_HighStrength'
        }

    @staticmethod
    def get_forming_rules() -> Dict[str, str]:
        """Material rules for metal forming."""
        return {
            'blank': 'Aluminum_5052',  # Formable
            'punch': 'Tool_Steel',
            'die': 'Tool_Steel',
            'binder': 'Tool_Steel',
            'pad': 'Rubber_Natural'
        }

    @staticmethod
    def get_drop_test_rules() -> Dict[str, str]:
        """Material rules for drop test."""
        return {
            'product': 'Plastic_ABS',
            'housing': 'Plastic_PC',
            'floor': 'Concrete',
            'internal': 'Aluminum_6061'
        }


def load_rules_from_yaml(filepath: str) -> Dict[str, str]:
    """
    Load material assignment rules from YAML file.

    Example YAML:
        rules:
          bumper: Plastic_PP
          hood: Aluminum_5052
          floor: Steel_HighStrength

    Args:
        filepath: Path to YAML file

    Returns:
        Dictionary of {pattern: material_name}
    """
    import yaml

    with open(filepath, 'r') as f:
        data = yaml.safe_load(f)

    return data.get('rules', {})


def assign_materials_auto(
    part_files: List[Path],
    geometries: List[Any],
    template_name: Optional[str] = None,
    custom_rules: Optional[Dict[str, str]] = None
) -> Dict[int, str]:
    """
    Convenience function for automatic material assignment.

    Tries multiple strategies in order:
    1. Custom rules (if provided)
    2. Template rules (if template specified)
    3. Filename patterns
    4. Geometry analysis

    Args:
        part_files: List of part file paths
        geometries: List of OCC geometries
        template_name: Optional template name (e.g., 'automotive_crash')
        custom_rules: Optional custom rules dictionary

    Returns:
        Dictionary of {part_index: material_name}
    """
    assigner = GeometryBasedMaterialAssigner()
    part_names = [f.stem for f in part_files]

    assignments = {}

    # Strategy 1: Custom rules
    if custom_rules:
        assignments.update(
            assigner.assign_by_filename(part_files, custom_rules)
        )

    # Strategy 2: Template rules
    if template_name:
        template_rules = MaterialRuleEngine.get_automotive_rules()  # TODO: load from template
        template_assignments = assigner.assign_by_template(part_names, template_rules)

        for idx, mat in template_assignments.items():
            if idx not in assignments:
                assignments[idx] = mat

    # Strategy 3: Geometry analysis (fallback for unassigned)
    geom_assignments = assigner.assign_by_geometry(geometries, part_names)

    for idx, mat in geom_assignments.items():
        if idx not in assignments:
            assignments[idx] = mat

    return assignments
