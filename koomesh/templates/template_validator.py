"""
Template Validator
==================

Validation system for simulation templates.

Validates:
- Template completeness
- Parameter consistency
- Material availability
- Physical constraints

Author: KooMeshGenerator Team
"""

import logging
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field

from .template_manager import SimulationTemplate, AnalysisType
from ..materials.material_library import MaterialLibrary


logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Template validation result"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    info: List[str] = field(default_factory=list)

    def add_error(self, message: str) -> None:
        """Add validation error"""
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str) -> None:
        """Add validation warning"""
        self.warnings.append(message)

    def add_info(self, message: str) -> None:
        """Add validation info"""
        self.info.append(message)

    def get_summary(self) -> str:
        """Get validation summary"""
        lines = []

        if self.is_valid:
            lines.append("✓ Template validation PASSED")
        else:
            lines.append("✗ Template validation FAILED")

        if self.errors:
            lines.append(f"\nErrors ({len(self.errors)}):")
            for err in self.errors:
                lines.append(f"  ✗ {err}")

        if self.warnings:
            lines.append(f"\nWarnings ({len(self.warnings)}):")
            for warn in self.warnings:
                lines.append(f"  ⚠ {warn}")

        if self.info:
            lines.append(f"\nInfo ({len(self.info)}):")
            for info_msg in self.info:
                lines.append(f"  ℹ {info_msg}")

        return "\n".join(lines)


class TemplateValidator:
    """
    Validate simulation templates

    Example:
        >>> validator = TemplateValidator(material_library)
        >>> result = validator.validate(template)
        >>> if not result.is_valid:
        >>>     print(result.get_summary())
    """

    def __init__(self, material_library: Optional[MaterialLibrary] = None):
        """
        Initialize validator

        Args:
            material_library: Material library for material validation
        """
        self.material_library = material_library or MaterialLibrary()
        if not self.material_library.materials:
            self.material_library.load_default_materials()

        self.logger = logging.getLogger(__name__)

    def validate(self, template: SimulationTemplate) -> ValidationResult:
        """
        Validate template

        Args:
            template: Template to validate

        Returns:
            Validation result
        """
        result = ValidationResult(is_valid=True)

        # Run all validation checks
        self._validate_meshing_parameters(template, result)
        self._validate_materials(template, result)
        self._validate_analysis_settings(template, result)
        self._validate_contact_parameters(template, result)
        self._validate_output_settings(template, result)
        self._validate_consistency(template, result)

        return result

    def _validate_meshing_parameters(self, template: SimulationTemplate,
                                     result: ValidationResult) -> None:
        """Validate meshing parameters"""
        # Element size consistency
        if template.target_element_size < template.min_element_size:
            result.add_error(
                f"target_element_size ({template.target_element_size}) < "
                f"min_element_size ({template.min_element_size})"
            )

        if template.target_element_size > template.max_element_size:
            result.add_error(
                f"target_element_size ({template.target_element_size}) > "
                f"max_element_size ({template.max_element_size})"
            )

        # Growth rate
        if template.growth_rate < 1.05:
            result.add_warning(
                f"Very low growth rate ({template.growth_rate}) may result in excessive elements"
            )

        if template.growth_rate > 1.5:
            result.add_warning(
                f"High growth rate ({template.growth_rate}) may result in poor quality transitions"
            )

        # Element type compatibility
        valid_element_types = ["solid", "shell", "beam", "membrane"]
        if template.element_type not in valid_element_types:
            result.add_error(
                f"Invalid element_type: {template.element_type}. "
                f"Valid options: {valid_element_types}"
            )

        # Element formulation compatibility
        solid_formulations = ["hex8", "tet4", "tet10", "hex20"]
        shell_formulations = ["shell3", "shell4", "shell6"]
        beam_formulations = ["beam2", "beam3d"]

        if template.element_type == "solid" and template.element_formulation not in solid_formulations:
            result.add_warning(
                f"Element formulation '{template.element_formulation}' may not be compatible "
                f"with element type 'solid'. Typical solid formulations: {solid_formulations}"
            )

        result.add_info(f"Element type: {template.element_type} ({template.element_formulation})")
        result.add_info(f"Element size: {template.min_element_size}-{template.max_element_size} mm "
                        f"(target: {template.target_element_size} mm)")

    def _validate_materials(self, template: SimulationTemplate,
                            result: ValidationResult) -> None:
        """Validate material specifications"""
        if not template.materials:
            result.add_warning("No recommended materials specified")
            return

        # Check material availability
        available_materials = set(self.material_library.list_materials())
        missing_materials = []

        for mat_name in template.materials:
            if mat_name not in available_materials:
                missing_materials.append(mat_name)

        if missing_materials:
            result.add_error(
                f"Materials not found in library: {missing_materials}"
            )

        # Validate material assignments
        for part_name, mat_name in template.material_assignments.items():
            if mat_name not in available_materials:
                result.add_error(
                    f"Material '{mat_name}' assigned to part '{part_name}' not found in library"
                )

        result.add_info(f"Recommended materials: {len(template.materials)}")

    def _validate_analysis_settings(self, template: SimulationTemplate,
                                     result: ValidationResult) -> None:
        """Validate analysis settings"""
        # Solver type
        valid_solvers = ["explicit", "implicit", "hybrid"]
        if template.solver_type not in valid_solvers:
            result.add_error(
                f"Invalid solver_type: {template.solver_type}. "
                f"Valid options: {valid_solvers}"
            )

        # Analysis type vs solver compatibility
        explicit_analysis = [AnalysisType.CRASH, AnalysisType.IMPACT, AnalysisType.DYNAMIC]
        implicit_analysis = [AnalysisType.STATIC, AnalysisType.MODAL, AnalysisType.THERMAL]

        # Convert string to enum for comparison if needed
        analysis_type_enum = template.analysis_type
        if isinstance(template.analysis_type, str):
            try:
                analysis_type_enum = AnalysisType(template.analysis_type)
            except ValueError:
                pass

        if analysis_type_enum in explicit_analysis and template.solver_type == "implicit":
            analysis_type_val = template.analysis_type if isinstance(template.analysis_type, str) else template.analysis_type.value
            result.add_warning(
                f"{analysis_type_val} analysis typically uses explicit solver"
            )

        if analysis_type_enum in implicit_analysis and template.solver_type == "explicit":
            analysis_type_val = template.analysis_type if isinstance(template.analysis_type, str) else template.analysis_type.value
            result.add_warning(
                f"{analysis_type_val} analysis typically uses implicit solver"
            )

        # Duration and timestep for dynamic analyses
        if analysis_type_enum in [AnalysisType.CRASH, AnalysisType.IMPACT, AnalysisType.DYNAMIC]:
            if template.analysis_duration is None:
                result.add_error("analysis_duration required for dynamic analysis")

            if template.timestep is None and template.solver_type == "explicit":
                result.add_warning("timestep not specified for explicit dynamic analysis")

            # Typical crash duration check
            if analysis_type_enum == AnalysisType.CRASH:
                if template.analysis_duration and template.analysis_duration > 0.5:
                    result.add_warning(
                        f"Crash duration ({template.analysis_duration}s) seems long. "
                        "Typical crash tests are 0.05-0.15s"
                    )

            # Impact timestep check
            if analysis_type_enum == AnalysisType.IMPACT:
                if template.timestep and template.timestep > 1e-5:
                    result.add_warning(
                        f"Timestep ({template.timestep}s) may be too large for impact analysis"
                    )

        # Handle both enum and string values
        analysis_type = template.analysis_type if isinstance(template.analysis_type, str) else template.analysis_type.value
        result.add_info(f"Analysis: {analysis_type} ({template.solver_type})")

    def _validate_contact_parameters(self, template: SimulationTemplate,
                                      result: ValidationResult) -> None:
        """Validate contact parameters"""
        # Contact algorithm
        valid_algorithms = ["penalty", "lagrange", "kinematic"]
        if template.contact_algorithm not in valid_algorithms:
            result.add_warning(
                f"Unusual contact_algorithm: {template.contact_algorithm}. "
                f"Common options: {valid_algorithms}"
            )

        # Friction coefficient
        if template.friction_coefficient < 0 or template.friction_coefficient > 1:
            result.add_error(
                f"Invalid friction_coefficient: {template.friction_coefficient}. "
                "Must be between 0 and 1"
            )

        # Typical friction ranges
        if template.friction_coefficient > 0.8:
            result.add_warning(
                f"Very high friction coefficient ({template.friction_coefficient}). "
                "Typical values are 0.1-0.6"
            )

        result.add_info(f"Contact: {template.contact_algorithm} (μ={template.friction_coefficient})")

    def _validate_output_settings(self, template: SimulationTemplate,
                                   result: ValidationResult) -> None:
        """Validate output settings"""
        # Output frequency
        if template.output_frequency <= 0:
            result.add_error("output_frequency must be positive")

        if template.output_frequency < 10:
            result.add_warning(
                f"Very frequent output ({template.output_frequency} steps) may generate "
                "large result files"
            )

        # Output variables
        if not template.output_variables:
            result.add_warning("No output variables specified")

        valid_variables = [
            "displacement", "velocity", "acceleration",
            "stress", "strain", "plastic_strain",
            "force", "energy", "damage"
        ]

        for var in template.output_variables:
            if var not in valid_variables:
                result.add_info(f"Uncommon output variable: {var}")

        result.add_info(f"Output: {len(template.output_variables)} variables "
                        f"every {template.output_frequency} steps")

    def _validate_consistency(self, template: SimulationTemplate,
                               result: ValidationResult) -> None:
        """Validate overall consistency"""
        # Name and description
        if not template.name:
            result.add_error("Template name is empty")

        if not template.description:
            result.add_warning("Template description is empty")

        # Tags
        if not template.tags:
            result.add_warning("No search tags specified")

        # Category consistency
        category_keywords = {
            "automotive": ["crash", "vehicle", "car", "automotive"],
            "aerospace": ["aircraft", "wing", "aerospace", "aviation"],
            "biomedical": ["implant", "medical", "biomedical", "bone"],
            "construction": ["building", "bridge", "construction", "structure"],
        }

        category_val = template.category if isinstance(template.category, str) else template.category.value
        if category_val in category_keywords:
            keywords = category_keywords[category_val]
            has_keyword = any(
                kw in template.name.lower() or
                kw in template.description.lower() or
                any(kw in tag.lower() for tag in template.tags)
                for kw in keywords
            )

            if not has_keyword:
                result.add_warning(
                    f"Template category is '{category_val}' but no related "
                    f"keywords found in name/description/tags"
                )


class TemplateCompatibilityChecker:
    """Check template compatibility with geometry/requirements"""

    def check_geometry_compatibility(self, template: SimulationTemplate,
                                      geometry_info: Dict[str, Any]) -> ValidationResult:
        """
        Check if template is compatible with geometry

        Args:
            template: Template to check
            geometry_info: Geometry information (size, complexity, etc.)

        Returns:
            Validation result
        """
        result = ValidationResult(is_valid=True)

        # Check geometry size vs element size
        if "bounding_box" in geometry_info:
            bbox = geometry_info["bounding_box"]
            min_dimension = min(bbox["length"], bbox["width"], bbox["height"])

            if template.max_element_size > min_dimension / 2:
                result.add_warning(
                    f"Max element size ({template.max_element_size} mm) is large compared to "
                    f"minimum geometry dimension ({min_dimension} mm)"
                )

            # Estimate element count
            volume = bbox["length"] * bbox["width"] * bbox["height"]
            avg_element_volume = template.target_element_size ** 3
            estimated_elements = volume / avg_element_volume

            result.add_info(f"Estimated element count: ~{estimated_elements:,.0f}")

            if estimated_elements > 10000000:  # 10M elements
                result.add_warning(
                    f"Estimated element count ({estimated_elements:,.0f}) is very high. "
                    "Consider increasing element size"
                )

        return result

    def check_computational_requirements(self, template: SimulationTemplate,
                                          element_count: int) -> Dict[str, Any]:
        """
        Estimate computational requirements

        Args:
            template: Template
            element_count: Estimated element count

        Returns:
            Dictionary with computational estimates
        """
        requirements = {}

        # Memory estimate (rule of thumb: ~1 KB per element for explicit, ~5 KB for implicit)
        if template.solver_type == "explicit":
            memory_per_element = 1.0  # KB
        else:
            memory_per_element = 5.0  # KB

        estimated_memory_gb = (element_count * memory_per_element) / (1024 * 1024)
        requirements["estimated_memory_gb"] = estimated_memory_gb

        # CPU time estimate (very rough)
        if template.analysis_type in [AnalysisType.CRASH, AnalysisType.IMPACT]:
            # Explicit: ~1-10 hours per million elements
            cpu_hours_per_million = 5.0
        else:
            # Implicit: ~0.1-2 hours per million elements per iteration
            cpu_hours_per_million = 1.0

        estimated_cpu_hours = (element_count / 1000000) * cpu_hours_per_million
        requirements["estimated_cpu_hours"] = estimated_cpu_hours

        # Recommended cores
        if element_count < 100000:
            recommended_cores = 4
        elif element_count < 1000000:
            recommended_cores = 16
        else:
            recommended_cores = 32

        requirements["recommended_cores"] = recommended_cores

        return requirements
