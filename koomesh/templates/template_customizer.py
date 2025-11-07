"""
Template Customizer
===================

Tools for customizing and modifying simulation templates.

Features:
- Parameter adjustment
- Material substitution
- Refinement strategies
- Template merging

Author: KooMeshGenerator Team
"""

import logging
import copy
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .template_manager import SimulationTemplate, AnalysisType, TemplateCategory
from ..materials.material_library import Material, MaterialLibrary


logger = logging.getLogger(__name__)


@dataclass
class CustomizationProfile:
    """Customization profile for batch modifications"""
    name: str
    description: str
    scale_element_size: Optional[float] = None  # Multiplier for element sizes
    material_substitutions: Dict[str, str] = None  # Old mat -> new mat
    adjust_timestep: Optional[float] = None  # Multiplier for timestep
    adjust_duration: Optional[float] = None  # Multiplier for duration
    override_solver: Optional[str] = None


class TemplateCustomizer:
    """
    Customize simulation templates

    Example:
        >>> customizer = TemplateCustomizer()
        >>> template = load_template("automotive_crash_frontal")
        >>> refined = customizer.refine_mesh(template, factor=2.0)
        >>> print(f"Element size reduced from {template.target_element_size} "
        ...       f"to {refined.target_element_size}")
    """

    def __init__(self, material_library: Optional[MaterialLibrary] = None):
        """
        Initialize customizer

        Args:
            material_library: Material library for material operations
        """
        self.material_library = material_library or MaterialLibrary()
        if not self.material_library.materials:
            self.material_library.load_default_materials()

        self.logger = logging.getLogger(__name__)

    def refine_mesh(self, template: SimulationTemplate, factor: float = 2.0,
                    name_suffix: str = "_refined") -> SimulationTemplate:
        """
        Refine mesh by reducing element sizes

        Args:
            template: Original template
            factor: Refinement factor (2.0 = half the element size)
            name_suffix: Suffix to add to template name

        Returns:
            Refined template
        """
        refined = copy.deepcopy(template)
        refined.name = template.name + name_suffix

        # Reduce element sizes
        refined.target_element_size = template.target_element_size / factor
        refined.min_element_size = template.min_element_size / factor
        refined.max_element_size = template.max_element_size / factor

        # May need to reduce timestep for explicit analysis
        if template.solver_type == "explicit" and template.timestep:
            refined.timestep = template.timestep / factor
            self.logger.info(
                f"Reduced timestep from {template.timestep} to {refined.timestep} "
                "for mesh refinement"
            )

        refined.description = f"Refined version of {template.name} ({factor}x)"
        refined.tags = template.tags + ["refined"]

        self.logger.info(
            f"Refined mesh: element size {template.target_element_size} -> "
            f"{refined.target_element_size}"
        )

        return refined

    def coarsen_mesh(self, template: SimulationTemplate, factor: float = 2.0,
                     name_suffix: str = "_coarse") -> SimulationTemplate:
        """
        Coarsen mesh by increasing element sizes

        Args:
            template: Original template
            factor: Coarsening factor (2.0 = double the element size)
            name_suffix: Suffix to add to template name

        Returns:
            Coarsened template
        """
        coarse = copy.deepcopy(template)
        coarse.name = template.name + name_suffix

        # Increase element sizes
        coarse.target_element_size = template.target_element_size * factor
        coarse.min_element_size = template.min_element_size * factor
        coarse.max_element_size = template.max_element_size * factor

        # May increase timestep for explicit analysis
        if template.solver_type == "explicit" and template.timestep:
            coarse.timestep = template.timestep * factor

        coarse.description = f"Coarsened version of {template.name} ({factor}x)"
        coarse.tags = template.tags + ["coarse", "fast"]

        self.logger.info(
            f"Coarsened mesh: element size {template.target_element_size} -> "
            f"{coarse.target_element_size}"
        )

        return coarse

    def substitute_material(self, template: SimulationTemplate,
                            old_material: str, new_material: str) -> SimulationTemplate:
        """
        Substitute one material with another

        Args:
            template: Original template
            old_material: Material to replace
            new_material: Replacement material

        Returns:
            Modified template
        """
        modified = copy.deepcopy(template)

        # Check if new material exists
        if not self.material_library.get_material(new_material):
            self.logger.warning(
                f"Material '{new_material}' not found in library. "
                "Template modified but may be invalid."
            )

        # Replace in recommended materials
        if old_material in modified.materials:
            idx = modified.materials.index(old_material)
            modified.materials[idx] = new_material

        # Replace in material assignments
        for part_name, mat_name in modified.material_assignments.items():
            if mat_name == old_material:
                modified.material_assignments[part_name] = new_material

        modified.description += f" (substituted {old_material} with {new_material})"

        self.logger.info(f"Substituted material: {old_material} -> {new_material}")

        return modified

    def adjust_analysis_duration(self, template: SimulationTemplate,
                                  duration_multiplier: float = 1.0,
                                  new_duration: Optional[float] = None) -> SimulationTemplate:
        """
        Adjust analysis duration

        Args:
            template: Original template
            duration_multiplier: Multiplier for duration (2.0 = twice as long)
            new_duration: Set specific duration (overrides multiplier)

        Returns:
            Modified template
        """
        modified = copy.deepcopy(template)

        if template.analysis_duration is None:
            self.logger.warning("Template has no duration to modify")
            return modified

        if new_duration is not None:
            modified.analysis_duration = new_duration
        else:
            modified.analysis_duration = template.analysis_duration * duration_multiplier

        modified.description += f" (duration: {modified.analysis_duration}s)"

        self.logger.info(
            f"Adjusted duration: {template.analysis_duration} -> "
            f"{modified.analysis_duration}"
        )

        return modified

    def convert_solver_type(self, template: SimulationTemplate,
                            new_solver: str) -> SimulationTemplate:
        """
        Convert template to different solver type

        Args:
            template: Original template
            new_solver: New solver type (explicit/implicit)

        Returns:
            Modified template
        """
        modified = copy.deepcopy(template)
        old_solver = template.solver_type

        valid_solvers = ["explicit", "implicit", "hybrid"]
        if new_solver not in valid_solvers:
            raise ValueError(
                f"Invalid solver type: {new_solver}. "
                f"Valid options: {valid_solvers}"
            )

        modified.solver_type = new_solver
        modified.description += f" (converted to {new_solver} solver)"

        # Adjust parameters for solver change
        if old_solver == "implicit" and new_solver == "explicit":
            # Converting to explicit: need timestep
            if modified.timestep is None:
                # Estimate reasonable timestep
                if modified.analysis_duration:
                    modified.timestep = modified.analysis_duration / 10000
                    self.logger.info(
                        f"Set timestep to {modified.timestep}s for explicit solver"
                    )

        elif old_solver == "explicit" and new_solver == "implicit":
            # Converting to implicit: timestep less critical
            self.logger.info("Converted to implicit solver. Review analysis settings.")

        self.logger.info(f"Converted solver: {old_solver} -> {new_solver}")

        return modified

    def adjust_output_frequency(self, template: SimulationTemplate,
                                 frequency_multiplier: float = 1.0,
                                 new_frequency: Optional[int] = None) -> SimulationTemplate:
        """
        Adjust output frequency

        Args:
            template: Original template
            frequency_multiplier: Multiplier for frequency (2.0 = half as frequent)
            new_frequency: Set specific frequency (overrides multiplier)

        Returns:
            Modified template
        """
        modified = copy.deepcopy(template)

        if new_frequency is not None:
            modified.output_frequency = new_frequency
        else:
            modified.output_frequency = int(template.output_frequency * frequency_multiplier)

        self.logger.info(
            f"Adjusted output frequency: {template.output_frequency} -> "
            f"{modified.output_frequency}"
        )

        return modified

    def add_output_variables(self, template: SimulationTemplate,
                             variables: List[str]) -> SimulationTemplate:
        """
        Add output variables

        Args:
            template: Original template
            variables: Variables to add

        Returns:
            Modified template
        """
        modified = copy.deepcopy(template)

        for var in variables:
            if var not in modified.output_variables:
                modified.output_variables.append(var)

        self.logger.info(f"Added output variables: {variables}")

        return modified

    def create_parametric_study(self, template: SimulationTemplate,
                                 parameter: str,
                                 values: List[Any]) -> List[SimulationTemplate]:
        """
        Create parametric study variants

        Args:
            template: Base template
            parameter: Parameter to vary (e.g., 'target_element_size')
            values: List of values to study

        Returns:
            List of template variants
        """
        variants = []

        for i, value in enumerate(values):
            variant = copy.deepcopy(template)
            variant.name = f"{template.name}_param_{i}"

            # Set parameter value
            if hasattr(variant, parameter):
                setattr(variant, parameter, value)
                variant.description = (
                    f"Parametric study variant: {parameter}={value}"
                )
                variant.tags = template.tags + ["parametric", f"param_{i}"]
                variants.append(variant)

                self.logger.info(
                    f"Created variant {i}: {parameter}={value}"
                )
            else:
                self.logger.warning(
                    f"Parameter '{parameter}' not found in template"
                )

        return variants

    def merge_templates(self, template1: SimulationTemplate,
                        template2: SimulationTemplate,
                        prefer_template1: bool = True) -> SimulationTemplate:
        """
        Merge two templates

        Args:
            template1: First template
            template2: Second template
            prefer_template1: Which template's values to prefer for conflicts

        Returns:
            Merged template
        """
        if prefer_template1:
            merged = copy.deepcopy(template1)
            source = template2
        else:
            merged = copy.deepcopy(template2)
            source = template1

        # Merge materials
        for mat in source.materials:
            if mat not in merged.materials:
                merged.materials.append(mat)

        # Merge material assignments
        for part, mat in source.material_assignments.items():
            if part not in merged.material_assignments:
                merged.material_assignments[part] = mat

        # Merge output variables
        for var in source.output_variables:
            if var not in merged.output_variables:
                merged.output_variables.append(var)

        # Merge tags
        for tag in source.tags:
            if tag not in merged.tags:
                merged.tags.append(tag)

        merged.name = f"{template1.name}_merged_{template2.name}"
        merged.description = f"Merged: {template1.name} + {template2.name}"

        self.logger.info(
            f"Merged templates: {template1.name} + {template2.name}"
        )

        return merged

    def apply_profile(self, template: SimulationTemplate,
                      profile: CustomizationProfile) -> SimulationTemplate:
        """
        Apply customization profile

        Args:
            template: Original template
            profile: Customization profile

        Returns:
            Customized template
        """
        customized = copy.deepcopy(template)

        # Scale element size
        if profile.scale_element_size:
            customized.target_element_size *= profile.scale_element_size
            customized.min_element_size *= profile.scale_element_size
            customized.max_element_size *= profile.scale_element_size

        # Material substitutions
        if profile.material_substitutions:
            for old_mat, new_mat in profile.material_substitutions.items():
                customized = self.substitute_material(customized, old_mat, new_mat)

        # Adjust timestep
        if profile.adjust_timestep and customized.timestep:
            customized.timestep *= profile.adjust_timestep

        # Adjust duration
        if profile.adjust_duration and customized.analysis_duration:
            customized.analysis_duration *= profile.adjust_duration

        # Override solver
        if profile.override_solver:
            customized.solver_type = profile.override_solver

        customized.name = f"{template.name}_{profile.name}"
        customized.description += f" (profile: {profile.description})"

        self.logger.info(f"Applied profile '{profile.name}' to {template.name}")

        return customized

    def optimize_for_speed(self, template: SimulationTemplate) -> SimulationTemplate:
        """
        Optimize template for faster computation

        Args:
            template: Original template

        Returns:
            Optimized template
        """
        fast = copy.deepcopy(template)
        fast.name = template.name + "_fast"

        # Coarsen mesh (larger elements)
        fast.target_element_size = template.target_element_size * 1.5
        fast.min_element_size = template.min_element_size * 1.5
        fast.max_element_size = template.max_element_size * 1.5

        # Reduce output frequency
        fast.output_frequency = template.output_frequency * 2

        # Increase timestep if explicit
        if template.solver_type == "explicit" and template.timestep:
            fast.timestep = template.timestep * 1.3

        fast.description = f"Fast variant of {template.name}"
        fast.tags = template.tags + ["fast", "optimized"]

        self.logger.info(f"Created fast variant: {fast.name}")

        return fast

    def optimize_for_accuracy(self, template: SimulationTemplate) -> SimulationTemplate:
        """
        Optimize template for higher accuracy

        Args:
            template: Original template

        Returns:
            Optimized template
        """
        accurate = copy.deepcopy(template)
        accurate.name = template.name + "_accurate"

        # Refine mesh (smaller elements)
        accurate.target_element_size = template.target_element_size / 1.5
        accurate.min_element_size = template.min_element_size / 1.5
        accurate.max_element_size = template.max_element_size / 1.5

        # Increase output frequency
        accurate.output_frequency = max(template.output_frequency // 2, 10)

        # Reduce timestep if explicit
        if template.solver_type == "explicit" and template.timestep:
            accurate.timestep = template.timestep / 1.5

        # Enable refinement options
        accurate.curvature_refinement = True

        accurate.description = f"High-accuracy variant of {template.name}"
        accurate.tags = template.tags + ["accurate", "refined"]

        self.logger.info(f"Created accurate variant: {accurate.name}")

        return accurate


# Predefined customization profiles
PREDEFINED_PROFILES = {
    "quick_preview": CustomizationProfile(
        name="quick_preview",
        description="Quick preview with coarse mesh",
        scale_element_size=2.0,
        adjust_timestep=2.0,
        adjust_duration=0.5
    ),
    "production_quality": CustomizationProfile(
        name="production_quality",
        description="Production-quality settings",
        scale_element_size=0.8,
        adjust_timestep=0.7
    ),
    "lightweight_materials": CustomizationProfile(
        name="lightweight",
        description="Substitute with lightweight materials",
        material_substitutions={
            "Steel_Mild_A36": "Aluminum_6061_T6",
            "Steel_1045": "Aluminum_7075_T6"
        }
    ),
    "high_strength": CustomizationProfile(
        name="high_strength",
        description="Substitute with high-strength materials",
        material_substitutions={
            "Steel_Mild_A36": "Steel_4340",
            "Aluminum_6061_T6": "Titanium_Ti6Al4V"
        }
    ),
}


def get_profile(name: str) -> Optional[CustomizationProfile]:
    """Get predefined customization profile by name"""
    return PREDEFINED_PROFILES.get(name)
