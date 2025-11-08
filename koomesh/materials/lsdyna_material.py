"""
LS-DYNA Material Card Generator
================================

Generate LS-DYNA material cards (*MAT_) from Material objects.

Supported material models:
- *MAT_ELASTIC (MAT_001)
- *MAT_PLASTIC_KINEMATIC (MAT_003)
- *MAT_RIGID (MAT_020)

Author: KooMeshGenerator Team
"""

import logging
from typing import Optional
from koomesh.materials.material_library import Material, MaterialType


logger = logging.getLogger(__name__)


class LSDynaMaterialGenerator:
    """
    Generate LS-DYNA material cards

    Converts Material objects to LS-DYNA *MAT_ keyword format.

    Example:
        >>> generator = LSDynaMaterialGenerator()
        >>> mat_card = generator.generate_material_card(steel, mat_id=1)
        >>> print(mat_card)
    """

    def __init__(self):
        """Initialize material card generator"""
        self.logger = logging.getLogger(__name__)

    def generate_material_card(self, material: Material,
                              mat_id: int,
                              title: Optional[str] = None) -> str:
        """
        Generate LS-DYNA material card

        Args:
            material: Material object
            mat_id: Material ID for LS-DYNA
            title: Optional title (uses material name if not provided)

        Returns:
            LS-DYNA material card as string

        Example:
            >>> card = generator.generate_material_card(steel, mat_id=1)
        """
        if title is None:
            title = material.name

        # Select appropriate material model
        if material.material_type == MaterialType.RIGID:
            return self._generate_mat_rigid(material, mat_id, title)
        elif material.material_type == MaterialType.ELASTIC:
            return self._generate_mat_elastic(material, mat_id, title)
        elif material.material_type in [MaterialType.PLASTIC, MaterialType.ELASTIC_PLASTIC]:
            return self._generate_mat_plastic_kinematic(material, mat_id, title)
        else:
            self.logger.warning(
                f"Material type {material.material_type} not fully supported, "
                f"using elastic model"
            )
            return self._generate_mat_elastic(material, mat_id, title)

    def _generate_mat_elastic(self, material: Material,
                              mat_id: int, title: str) -> str:
        """
        Generate *MAT_ELASTIC (MAT_001)

        Isotropic elastic material
        """
        # Convert units if needed (assume SI input, convert to LS-DYNA ton-mm-s-MPa)
        density = material.density * 1e-9  # kg/m³ to ton/mm³
        E = material.elastic_modulus * 1e-6  # Pa to MPa
        nu = material.poisson_ratio

        lines = [
            f"$# Material: {title}",
            "*MAT_ELASTIC",
            f"$#     MID        RO         E        PR",
            f"{mat_id:10d}{density:10.4e}{E:10.3e}{nu:10.3f}",
        ]

        return "\n".join(lines)

    def _generate_mat_plastic_kinematic(self, material: Material,
                                       mat_id: int, title: str) -> str:
        """
        Generate *MAT_PLASTIC_KINEMATIC (MAT_003)

        Isotropic elastic-plastic material with kinematic hardening
        """
        # Convert units (SI to ton-mm-s-MPa)
        density = material.density * 1e-9  # kg/m³ to ton/mm³
        E = material.elastic_modulus * 1e-6  # Pa to MPa
        nu = material.poisson_ratio
        sigy = (material.yield_stress * 1e-6) if material.yield_stress else 0.0  # Pa to MPa
        etan = (material.tangent_modulus * 1e-6) if material.tangent_modulus else 0.0  # Pa to MPa
        fail = material.failure_strain if material.failure_strain else 1.0

        lines = [
            f"$# Material: {title}",
            "*MAT_PLASTIC_KINEMATIC",
            f"$#     MID        RO         E        PR      SIGY      ETAN      BETA       SRC",
            f"{mat_id:10d}{density:10.4e}{E:10.3e}{nu:10.3f}{sigy:10.3e}{etan:10.3e}{0.0:10.3f}{0.0:10.3f}",
            f"$#      C         P      LCSS      LCSR        VP",
            f"  {0.0:10.3f}{0.0:10.3f}{0:10d}{0:10d}{0.0:10.3f}",
        ]

        # Add failure strain if specified
        if fail < 1.0:
            lines.append(f"$# Failure strain: {fail:.3f}")
            lines.append(f"*MAT_ADD_EROSION")
            lines.append(f"$#     MID    EXCL    MXEPS    NUMFIP    NCS    MNEPS")
            lines.append(f"{mat_id:10d}{0:10d}{fail:10.3f}{1:10d}{1:10d}{0.0:10.3f}")

        return "\n".join(lines)

    def _generate_mat_rigid(self, material: Material,
                           mat_id: int, title: str) -> str:
        """
        Generate *MAT_RIGID (MAT_020)

        Rigid material for boundary conditions
        """
        # Convert units
        density = material.density * 1e-9  # kg/m³ to ton/mm³
        E = material.elastic_modulus * 1e-6  # Pa to MPa
        nu = material.poisson_ratio

        lines = [
            f"$# Material: {title} (RIGID)",
            "*MAT_RIGID",
            f"$#     MID        RO         E        PR",
            f"{mat_id:10d}{density:10.4e}{E:10.3e}{nu:10.3f}",
            f"$#     CMO      CON1      CON2",
            f"{1:10d}{0:10d}{0:10d}",
        ]

        return "\n".join(lines)

    def generate_section_solid(self, section_id: int, mat_id: int,
                               elem_formulation: int = 1) -> str:
        """
        Generate *SECTION_SOLID card

        Args:
            section_id: Section ID
            mat_id: Material ID
            elem_formulation: Element formulation
                             1 = constant stress solid (default)
                             2 = fully integrated
                             10 = 1-point corotational

        Returns:
            LS-DYNA section card

        Example:
            >>> section = generator.generate_section_solid(1, 1, elem_formulation=10)
        """
        lines = [
            "*SECTION_SOLID",
            f"$#   SECID    ELFORM       AET",
            f"{section_id:10d}{elem_formulation:10d}{0:10d}",
        ]

        return "\n".join(lines)

    def generate_part(self, part_id: int, section_id: int,
                     mat_id: int, part_name: str) -> str:
        """
        Generate *PART card

        Args:
            part_id: Part ID
            section_id: Section ID
            mat_id: Material ID
            part_name: Part name/description

        Returns:
            LS-DYNA part card

        Example:
            >>> part = generator.generate_part(1, 1, 1, "Steel_Part")
        """
        lines = [
            f"*PART",
            f"${part_name}",
            f"$#     PID     SECID       MID",
            f"{part_id:10d}{section_id:10d}{mat_id:10d}",
        ]

        return "\n".join(lines)

    def generate_complete_material_deck(self, materials: list,
                                       start_mat_id: int = 1) -> str:
        """
        Generate complete material deck for multiple materials

        Args:
            materials: List of Material objects
            start_mat_id: Starting material ID

        Returns:
            Complete LS-DYNA material deck

        Example:
            >>> deck = generator.generate_complete_material_deck([steel, aluminum])
        """
        lines = [
            "$# =========================================================================",
            "$# MATERIAL DEFINITIONS",
            "$# =========================================================================",
            "$#",
            ""
        ]

        for i, material in enumerate(materials):
            mat_id = start_mat_id + i
            mat_card = self.generate_material_card(material, mat_id)
            lines.append(mat_card)
            lines.append("")

        lines.extend([
            "$# =========================================================================",
            "$# SECTION DEFINITIONS",
            "$# =========================================================================",
            "$#",
            ""
        ])

        for i, material in enumerate(materials):
            section_id = start_mat_id + i
            mat_id = start_mat_id + i
            section_card = self.generate_section_solid(section_id, mat_id)
            lines.append(section_card)
            lines.append("")

        return "\n".join(lines)
