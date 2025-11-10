"""
Material Validation and Recommendation

Validates material assignments and recommends suitable materials.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging

from koomesh.materials.material_library import MaterialLibrary, Material


@dataclass
class MaterialIssue:
    """Represents a material assignment issue"""
    part_index: int
    part_name: str
    severity: str  # ERROR, WARNING, INFO
    message: str
    suggestion: str


@dataclass
class MaterialValidationReport:
    """Material validation results"""
    valid: bool
    issues: List[MaterialIssue]
    statistics: Dict[str, Any]


class MaterialValidator:
    """
    Validate material assignments for simulations.

    Checks:
    1. Simulation type compatibility
    2. Required property completeness
    3. Physical reasonableness
    4. Material combination compatibility

    Example:
        >>> validator = MaterialValidator()
        >>> report = validator.validate_assignment(
        ...     part, 'Steel_Mild', simulation_type='crash'
        ... )
        >>> if not report.valid:
        ...     for issue in report.issues:
        ...         print(f"{issue.severity}: {issue.message}")
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.material_library = MaterialLibrary()

    def validate_assignment(
        self,
        part_name: str,
        material_name: str,
        simulation_type: str = "crash",
        part_volume: Optional[float] = None
    ) -> MaterialValidationReport:
        """
        Validate material assignment for a part.

        Args:
            part_name: Name of the part
            material_name: Assigned material name
            simulation_type: Type of simulation
            part_volume: Optional part volume (cm³)

        Returns:
            MaterialValidationReport

        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If validation fails
        """
        # Input validation
        if part_name is None or not isinstance(part_name, str):
            raise TypeError("part_name must be a string")

        if not part_name.strip():
            raise ValueError("part_name cannot be empty")

        if material_name is None or not isinstance(material_name, str):
            raise TypeError("material_name must be a string")

        if not material_name.strip():
            raise ValueError("material_name cannot be empty")

        if simulation_type not in ['crash', 'forming', 'impact', 'drop_test']:
            self.logger.warning(f"Unknown simulation_type: {simulation_type}")

        if part_volume is not None and part_volume <= 0:
            raise ValueError(f"part_volume must be positive, got {part_volume}")

        try:
            issues = []

            # Get material from library
            material = self.material_library.get_material(material_name)

            if material is None:
                issues.append(MaterialIssue(
                    part_index=0,
                    part_name=part_name,
                    severity='ERROR',
                    message=f'Material "{material_name}" not found in library',
                    suggestion='Check material name or add to library'
                ))
                return MaterialValidationReport(
                    valid=False,
                    issues=issues,
                    statistics={}
                )

            # Check 1: Simulation type compatibility
            sim_issues = self._check_simulation_compatibility(
                part_name, material, simulation_type
            )
            issues.extend(sim_issues)

            # Check 2: Property completeness
            prop_issues = self._check_property_completeness(
                part_name, material, simulation_type
            )
            issues.extend(prop_issues)

            # Check 3: Physical reasonableness
            phys_issues = self._check_physical_reasonableness(
                part_name, material
            )
            issues.extend(phys_issues)

            # Check 4: Practical concerns
            if part_volume:
                pract_issues = self._check_practical_concerns(
                    part_name, material, part_volume
                )
                issues.extend(pract_issues)

            # Determine validity
            has_errors = any(issue.severity == 'ERROR' for issue in issues)
            valid = not has_errors

            statistics = {
                'num_errors': sum(1 for i in issues if i.severity == 'ERROR'),
                'num_warnings': sum(1 for i in issues if i.severity == 'WARNING'),
                'material_category': material.category,
                'material_density': material.density
            }

            return MaterialValidationReport(
                valid=valid,
                issues=issues,
                statistics=statistics
            )

        except Exception as e:
            self.logger.error(f"Material validation failed: {e}")
            raise RuntimeError(f"Material validation failed: {e}") from e

    def _check_simulation_compatibility(
        self,
        part_name: str,
        material: Material,
        simulation_type: str
    ) -> List[MaterialIssue]:
        """Check if material is suitable for simulation type."""
        issues = []

        if simulation_type == 'crash':
            # Crash requires failure model for some materials
            if material.category in ['Metal', 'Composite']:
                if not hasattr(material, 'failure_strain') or material.failure_strain is None:
                    issues.append(MaterialIssue(
                        part_index=0,
                        part_name=part_name,
                        severity='WARNING',
                        message=f'{material.name} has no failure model for crash simulation',
                        suggestion=f'Consider adding failure strain or using material with failure data'
                    ))

        elif simulation_type == 'forming':
            # Forming requires good formability
            if material.category == 'Metal':
                # Check if material is too hard
                if hasattr(material, 'yield_strength') and material.yield_strength > 600:
                    issues.append(MaterialIssue(
                        part_index=0,
                        part_name=part_name,
                        severity='WARNING',
                        message=f'{material.name} may have poor formability (σy={material.yield_strength}MPa)',
                        suggestion='Consider softer aluminum alloy (5xxx series) or annealed steel'
                    ))

        elif simulation_type == 'impact':
            # Impact requires good energy absorption
            if material.category == 'Brittle':
                issues.append(MaterialIssue(
                    part_index=0,
                    part_name=part_name,
                    severity='WARNING',
                    message=f'{material.name} is brittle and may not absorb impact well',
                    suggestion='Consider ductile materials like steel or tough plastics'
                ))

        return issues

    def _check_property_completeness(
        self,
        part_name: str,
        material: Material,
        simulation_type: str
    ) -> List[MaterialIssue]:
        """Check if material has all required properties."""
        issues = []

        # Essential properties for all simulations
        required_basic = ['density', 'youngs_modulus', 'poissons_ratio']

        missing_basic = []
        for prop in required_basic:
            if not hasattr(material, prop) or getattr(material, prop) is None:
                missing_basic.append(prop)

        if missing_basic:
            issues.append(MaterialIssue(
                part_index=0,
                part_name=part_name,
                severity='ERROR',
                message=f'Missing essential properties: {", ".join(missing_basic)}',
                suggestion='Add missing properties to material definition'
            ))

        # Simulation-specific properties
        if simulation_type == 'crash':
            required = ['yield_strength']
            for prop in required:
                if not hasattr(material, prop) or getattr(material, prop) is None:
                    issues.append(MaterialIssue(
                        part_index=0,
                        part_name=part_name,
                        severity='WARNING',
                        message=f'Missing {prop} for crash simulation',
                        suggestion=f'Add {prop} or use default values'
                    ))

        return issues

    def _check_physical_reasonableness(
        self,
        part_name: str,
        material: Material
    ) -> List[MaterialIssue]:
        """Check if material properties are physically reasonable."""
        issues = []

        # Check Young's modulus
        if hasattr(material, 'youngs_modulus') and material.youngs_modulus:
            E = material.youngs_modulus

            if E < 0.1:
                issues.append(MaterialIssue(
                    part_index=0,
                    part_name=part_name,
                    severity='ERROR',
                    message=f'Unreasonably low Young\'s modulus: {E:.2f} MPa',
                    suggestion='Check units (should be MPa)'
                ))
            elif E < 100:
                issues.append(MaterialIssue(
                    part_index=0,
                    part_name=part_name,
                    severity='WARNING',
                    message=f'Very low Young\'s modulus: {E:.2f} MPa',
                    suggestion='Verify material properties (typical range: 1000-200000 MPa)'
                ))
            elif E > 500000:
                issues.append(MaterialIssue(
                    part_index=0,
                    part_name=part_name,
                    severity='WARNING',
                    message=f'Very high Young\'s modulus: {E:.0f} MPa',
                    suggestion='Verify material properties (diamond = ~1,000,000 MPa)'
                ))

        # Check density
        if hasattr(material, 'density') and material.density:
            rho = material.density

            if rho < 0.001:
                issues.append(MaterialIssue(
                    part_index=0,
                    part_name=part_name,
                    severity='ERROR',
                    message=f'Unreasonably low density: {rho:.6f} kg/m³',
                    suggestion='Check units (should be kg/m³ or tonne/mm³)'
                ))
            elif rho > 30000:
                issues.append(MaterialIssue(
                    part_index=0,
                    part_name=part_name,
                    severity='WARNING',
                    message=f'Very high density: {rho:.0f} kg/m³',
                    suggestion='Verify density (osmium = ~22,600 kg/m³)'
                ))

        # Check Poisson's ratio
        if hasattr(material, 'poissons_ratio') and material.poissons_ratio:
            nu = material.poissons_ratio

            if nu < 0.0 or nu > 0.5:
                issues.append(MaterialIssue(
                    part_index=0,
                    part_name=part_name,
                    severity='ERROR',
                    message=f'Invalid Poisson\'s ratio: {nu:.3f} (must be 0.0-0.5)',
                    suggestion='Correct Poisson\'s ratio to valid range'
                ))

        return issues

    def _check_practical_concerns(
        self,
        part_name: str,
        material: Material,
        part_volume: float
    ) -> List[MaterialIssue]:
        """Check practical manufacturing/cost concerns."""
        issues = []

        if hasattr(material, 'density') and material.density:
            # Calculate part mass
            mass_kg = part_volume * material.density / 1000  # volume in cm³, density in kg/m³

            # Very heavy parts
            if mass_kg > 1000:  # > 1 tonne
                issues.append(MaterialIssue(
                    part_index=0,
                    part_name=part_name,
                    severity='INFO',
                    message=f'Part is very heavy: {mass_kg:.1f} kg with {material.name}',
                    suggestion='Consider lighter material if weight is critical'
                ))

        return issues


class MaterialRecommender:
    """
    Recommend suitable materials based on requirements.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.material_library = MaterialLibrary()

    def recommend_materials(
        self,
        part_name: str,
        simulation_type: str = "crash",
        constraints: Optional[Dict[str, Any]] = None,
        top_n: int = 5
    ) -> List[Tuple[Material, float, str]]:
        """
        Recommend suitable materials.

        Args:
            part_name: Name of part
            simulation_type: Type of simulation
            constraints: Optional constraints dict with keys:
                - min_strength: Minimum yield strength (MPa)
                - max_density: Maximum density (kg/m³)
                - formability: 'required' or 'preferred'
                - max_cost: Maximum cost index
            top_n: Number of recommendations to return

        Returns:
            List of (Material, score, reason) tuples
        """
        constraints = constraints or {}

        # Get all materials
        all_materials = self.material_library.list_materials()

        # Filter and score
        candidates = []

        for mat_name in all_materials:
            material = self.material_library.get_material(mat_name)

            if material is None:
                continue

            # Apply constraints
            if not self._meets_constraints(material, constraints):
                continue

            # Calculate suitability score
            score = self._calculate_suitability_score(
                material, simulation_type, constraints
            )

            # Get recommendation reason
            reason = self._get_recommendation_reason(
                material, simulation_type, constraints
            )

            candidates.append((material, score, reason))

        # Sort by score
        candidates.sort(key=lambda x: x[1], reverse=True)

        # Return top N
        return candidates[:top_n]

    def _meets_constraints(
        self,
        material: Material,
        constraints: Dict[str, Any]
    ) -> bool:
        """Check if material meets hard constraints."""

        # Minimum strength
        if 'min_strength' in constraints:
            if not hasattr(material, 'yield_strength') or material.yield_strength is None:
                return False
            if material.yield_strength < constraints['min_strength']:
                return False

        # Maximum density
        if 'max_density' in constraints:
            if not hasattr(material, 'density') or material.density is None:
                return False
            if material.density > constraints['max_density']:
                return False

        # Formability required
        if constraints.get('formability') == 'required':
            # Only soft metals and some plastics
            if material.category == 'Metal':
                if hasattr(material, 'yield_strength') and material.yield_strength > 400:
                    return False

        return True

    def _calculate_suitability_score(
        self,
        material: Material,
        simulation_type: str,
        constraints: Dict[str, Any]
    ) -> float:
        """Calculate suitability score (0-1)."""
        score = 0.5  # Base score

        # Simulation type bonus
        if simulation_type == 'crash':
            if material.category == 'Metal':
                score += 0.2
            if hasattr(material, 'yield_strength') and material.yield_strength:
                if 200 <= material.yield_strength <= 600:
                    score += 0.1  # Good range for crash

        elif simulation_type == 'forming':
            if material.category == 'Metal':
                score += 0.2
            if hasattr(material, 'yield_strength') and material.yield_strength:
                if material.yield_strength < 300:
                    score += 0.2  # Soft = formable

        # Density bonus (lighter is often better)
        if hasattr(material, 'density') and material.density:
            if material.density < 5000:  # Lightweight
                score += 0.1

        # Completeness bonus
        required_props = ['density', 'youngs_modulus', 'poissons_ratio', 'yield_strength']
        completeness = sum(
            1 for prop in required_props
            if hasattr(material, prop) and getattr(material, prop) is not None
        ) / len(required_props)
        score += completeness * 0.1

        return min(1.0, score)

    def _get_recommendation_reason(
        self,
        material: Material,
        simulation_type: str,
        constraints: Dict[str, Any]
    ) -> str:
        """Get human-readable reason for recommendation."""
        reasons = []

        if material.category == 'Metal':
            reasons.append("Good structural properties")

        if hasattr(material, 'density') and material.density < 5000:
            reasons.append("Lightweight")

        if hasattr(material, 'yield_strength') and material.yield_strength:
            if simulation_type == 'forming' and material.yield_strength < 300:
                reasons.append("Excellent formability")
            elif simulation_type == 'crash' and 200 <= material.yield_strength <= 600:
                reasons.append("Good crash energy absorption")

        if not reasons:
            reasons.append("Meets basic requirements")

        return ", ".join(reasons)
