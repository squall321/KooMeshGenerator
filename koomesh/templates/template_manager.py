"""
Template Manager
================

Manage industry-specific simulation templates for mesh generation.

This module provides:
- Template loading and validation
- Industry-specific presets
- Template customization
- YAML-based template storage

Author: KooMeshGenerator Team
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum

from pydantic import BaseModel, Field, validator


logger = logging.getLogger(__name__)


class TemplateCategory(Enum):
    """Template category classification"""
    AUTOMOTIVE = "automotive"
    AEROSPACE = "aerospace"
    BIOMEDICAL = "biomedical"
    CONSTRUCTION = "construction"
    MANUFACTURING = "manufacturing"
    MARINE = "marine"
    ENERGY = "energy"
    ELECTRONICS = "electronics"
    DEFENSE = "defense"
    CONSUMER = "consumer"
    GENERAL = "general"


class AnalysisType(Enum):
    """FEA analysis type"""
    STATIC = "static"
    DYNAMIC = "dynamic"
    CRASH = "crash"
    IMPACT = "impact"
    THERMAL = "thermal"
    FLUID = "fluid"
    FATIGUE = "fatigue"
    MODAL = "modal"
    NONLINEAR = "nonlinear"


@dataclass
class MeshingParameters:
    """Meshing parameters for template"""
    element_type: str = "solid"  # solid, shell, beam
    element_formulation: str = "hex8"  # hex8, tet4, tet10, shell4, etc.
    target_element_size: float = 5.0  # mm
    min_element_size: float = 1.0  # mm
    max_element_size: float = 20.0  # mm
    growth_rate: float = 1.2
    curvature_refinement: bool = True
    proximity_refinement: bool = True
    defeaturing_tolerance: float = 0.5  # mm
    mesh_quality_target: float = 0.3  # min Jacobian


@dataclass
class MaterialAssignment:
    """Material assignment for parts"""
    part_name: str
    material_name: str
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BoundaryCondition:
    """Boundary condition specification"""
    bc_type: str  # fixed, prescribed_motion, pressure, etc.
    location: str  # part name or set name
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LoadCase:
    """Load case specification"""
    name: str
    loads: List[Dict[str, Any]] = field(default_factory=list)
    boundary_conditions: List[BoundaryCondition] = field(default_factory=list)
    duration: Optional[float] = None
    timestep: Optional[float] = None


class SimulationTemplate(BaseModel):
    """
    Simulation template with validation

    Defines a complete FEA simulation setup including:
    - Meshing parameters
    - Material assignments
    - Boundary conditions
    - Analysis settings
    """
    name: str = Field(..., description="Template name")
    category: TemplateCategory = Field(..., description="Industry category")
    analysis_type: AnalysisType = Field(..., description="Analysis type")
    description: str = Field("", description="Template description")

    # Meshing
    element_type: str = Field("solid", description="Element type")
    element_formulation: str = Field("hex8", description="Element formulation")
    target_element_size: float = Field(5.0, gt=0, description="Target element size (mm)")
    min_element_size: float = Field(1.0, gt=0, description="Minimum element size (mm)")
    max_element_size: float = Field(20.0, gt=0, description="Maximum element size (mm)")
    growth_rate: float = Field(1.2, gt=1.0, le=2.0, description="Mesh growth rate")
    curvature_refinement: bool = Field(True, description="Enable curvature refinement")

    # Materials
    materials: List[str] = Field(default_factory=list, description="Recommended materials")
    material_assignments: Dict[str, str] = Field(default_factory=dict, description="Part-material map")

    # Analysis settings
    solver_type: str = Field("explicit", description="Solver type (explicit/implicit)")
    analysis_duration: Optional[float] = Field(None, gt=0, description="Analysis duration (s)")
    timestep: Optional[float] = Field(None, gt=0, description="Initial timestep (s)")
    termination_time: Optional[float] = Field(None, gt=0, description="Termination time (s)")

    # Contact
    contact_algorithm: str = Field("penalty", description="Contact algorithm")
    friction_coefficient: float = Field(0.2, ge=0, le=1, description="Friction coefficient")

    # Output
    output_frequency: int = Field(100, gt=0, description="Output every N steps")
    output_variables: List[str] = Field(
        default_factory=lambda: ["displacement", "stress", "strain"],
        description="Output variables"
    )

    # Metadata
    tags: List[str] = Field(default_factory=list, description="Search tags")
    author: str = Field("KooMeshGenerator", description="Template author")
    version: str = Field("1.0", description="Template version")

    class Config:
        use_enum_values = True

    @validator('max_element_size')
    def validate_element_sizes(cls, v, values):
        """Ensure max > min element size"""
        if 'min_element_size' in values and v <= values['min_element_size']:
            raise ValueError('max_element_size must be greater than min_element_size')
        return v

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return self.dict()

    def to_yaml(self) -> str:
        """Convert to YAML string"""
        return yaml.dump(self.dict(), default_flow_style=False, sort_keys=False)

    @classmethod
    def from_yaml(cls, yaml_str: str) -> 'SimulationTemplate':
        """Load from YAML string"""
        data = yaml.safe_load(yaml_str)
        return cls(**data)


class TemplateManager:
    """
    Manage simulation templates

    Example:
        >>> manager = TemplateManager()
        >>> manager.load_builtin_templates()
        >>> template = manager.get_template("automotive_crash_test")
        >>> print(template.description)
    """

    def __init__(self, template_dir: Optional[Path] = None):
        """
        Initialize template manager

        Args:
            template_dir: Directory containing template files
        """
        self.templates: Dict[str, SimulationTemplate] = {}
        self.template_dir = template_dir or (Path(__file__).parent / "templates")
        self.logger = logging.getLogger(__name__)

    def add_template(self, template: SimulationTemplate) -> None:
        """
        Add template to library

        Args:
            template: Template to add
        """
        if template.name in self.templates:
            self.logger.warning(f"Overwriting existing template: {template.name}")

        self.templates[template.name] = template
        self.logger.info(f"Added template: {template.name}")

    def get_template(self, name: str) -> Optional[SimulationTemplate]:
        """
        Get template by name

        Args:
            name: Template name

        Returns:
            Template or None if not found
        """
        return self.templates.get(name)

    def list_templates(self, category: Optional[TemplateCategory] = None) -> List[str]:
        """
        List available templates

        Args:
            category: Filter by category (optional)

        Returns:
            List of template names
        """
        if category is None:
            return list(self.templates.keys())

        return [
            name for name, template in self.templates.items()
            if template.category == category
        ]

    def search_templates(self, keyword: str) -> List[SimulationTemplate]:
        """
        Search templates by keyword

        Args:
            keyword: Search keyword

        Returns:
            List of matching templates
        """
        keyword = keyword.lower()
        results = []

        for template in self.templates.values():
            # Search in name
            if keyword in template.name.lower():
                results.append(template)
                continue

            # Search in description
            if keyword in template.description.lower():
                results.append(template)
                continue

            # Search in tags
            if any(keyword in tag.lower() for tag in template.tags):
                results.append(template)

        return results

    def save_template(self, template: SimulationTemplate, filepath: Path) -> None:
        """
        Save template to YAML file

        Args:
            template: Template to save
            filepath: Output file path
        """
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w') as f:
            f.write(template.to_yaml())

        self.logger.info(f"Saved template to {filepath}")

    def load_template(self, filepath: Path) -> SimulationTemplate:
        """
        Load template from YAML file

        Args:
            filepath: Input file path

        Returns:
            Loaded template
        """
        with open(filepath, 'r') as f:
            yaml_str = f.read()

        template = SimulationTemplate.from_yaml(yaml_str)
        self.add_template(template)

        return template

    def load_builtin_templates(self) -> None:
        """Load all built-in templates"""
        self._load_automotive_templates()
        self._load_aerospace_templates()
        self._load_biomedical_templates()
        self._load_construction_templates()
        self._load_manufacturing_templates()
        self._load_other_templates()

        self.logger.info(f"Loaded {len(self.templates)} built-in templates")

    def _load_automotive_templates(self) -> None:
        """Load automotive industry templates"""
        # Crash test
        self.add_template(SimulationTemplate(
            name="automotive_crash_frontal",
            category=TemplateCategory.AUTOMOTIVE,
            analysis_type=AnalysisType.CRASH,
            description="Frontal crash test simulation (NCAP/IIHS)",
            element_type="solid",
            element_formulation="hex8",
            target_element_size=5.0,
            min_element_size=2.0,
            max_element_size=15.0,
            materials=["Steel_DP600", "Steel_DP980", "Aluminum_6061_T6"],
            solver_type="explicit",
            analysis_duration=0.150,  # 150 ms
            timestep=1e-6,
            contact_algorithm="penalty",
            friction_coefficient=0.3,
            output_frequency=100,
            tags=["crash", "automotive", "safety", "ncap"]
        ))

        # Side impact
        self.add_template(SimulationTemplate(
            name="automotive_crash_side",
            category=TemplateCategory.AUTOMOTIVE,
            analysis_type=AnalysisType.CRASH,
            description="Side impact crash test (FMVSS 214)",
            element_type="solid",
            element_formulation="hex8",
            target_element_size=5.0,
            materials=["Steel_DP980", "Steel_TRIP780", "Aluminum_7075_T6"],
            solver_type="explicit",
            analysis_duration=0.100,
            timestep=1e-6,
            tags=["crash", "side impact", "automotive"]
        ))

        # Roof crush
        self.add_template(SimulationTemplate(
            name="automotive_roof_crush",
            category=TemplateCategory.AUTOMOTIVE,
            analysis_type=AnalysisType.STATIC,
            description="Roof crush strength test (FMVSS 216)",
            element_type="shell",
            element_formulation="shell4",
            target_element_size=10.0,
            materials=["Steel_HSLA_50", "Steel_DP600"],
            solver_type="implicit",
            tags=["roof", "strength", "automotive"]
        ))

        # NVH modal analysis
        self.add_template(SimulationTemplate(
            name="automotive_nvh_modal",
            category=TemplateCategory.AUTOMOTIVE,
            analysis_type=AnalysisType.MODAL,
            description="NVH modal analysis for body-in-white",
            element_type="shell",
            element_formulation="shell4",
            target_element_size=20.0,
            materials=["Steel_Mild_A36", "Aluminum_6061_T6"],
            solver_type="implicit",
            tags=["nvh", "modal", "vibration", "automotive"]
        ))

        # Suspension durability
        self.add_template(SimulationTemplate(
            name="automotive_suspension_durability",
            category=TemplateCategory.AUTOMOTIVE,
            analysis_type=AnalysisType.FATIGUE,
            description="Suspension component durability analysis",
            element_type="solid",
            element_formulation="tet10",
            target_element_size=3.0,
            materials=["Steel_4340", "Steel_Spring_5160", "Aluminum_7075_T6"],
            solver_type="implicit",
            tags=["suspension", "fatigue", "durability", "automotive"]
        ))

    def _load_aerospace_templates(self) -> None:
        """Load aerospace industry templates"""
        # Bird strike
        self.add_template(SimulationTemplate(
            name="aerospace_bird_strike",
            category=TemplateCategory.AEROSPACE,
            analysis_type=AnalysisType.IMPACT,
            description="Bird strike impact on engine/windshield",
            element_type="solid",
            element_formulation="hex8",
            target_element_size=2.0,
            materials=["Titanium_Ti6Al4V", "Polycarbonate_PC"],
            solver_type="explicit",
            analysis_duration=0.010,
            timestep=5e-7,
            tags=["bird strike", "impact", "aerospace"]
        ))

        # Wing structural analysis
        self.add_template(SimulationTemplate(
            name="aerospace_wing_structural",
            category=TemplateCategory.AEROSPACE,
            analysis_type=AnalysisType.STATIC,
            description="Wing structural analysis under aerodynamic loads",
            element_type="shell",
            element_formulation="shell4",
            target_element_size=50.0,
            materials=["Aluminum_7075_T6", "Titanium_Ti6Al4V", "CarbonFiber_Epoxy_UD"],
            solver_type="implicit",
            tags=["wing", "structural", "aerospace"]
        ))

        # Engine mount vibration
        self.add_template(SimulationTemplate(
            name="aerospace_engine_mount_modal",
            category=TemplateCategory.AEROSPACE,
            analysis_type=AnalysisType.MODAL,
            description="Engine mount modal and vibration analysis",
            element_type="solid",
            element_formulation="tet10",
            target_element_size=5.0,
            materials=["Titanium_Ti6Al4V", "Inconel_718", "Rubber_Neoprene"],
            solver_type="implicit",
            tags=["engine", "vibration", "modal", "aerospace"]
        ))

        # Landing gear impact
        self.add_template(SimulationTemplate(
            name="aerospace_landing_gear_impact",
            category=TemplateCategory.AEROSPACE,
            analysis_type=AnalysisType.IMPACT,
            description="Landing gear impact and energy absorption",
            element_type="solid",
            element_formulation="hex8",
            target_element_size=10.0,
            materials=["Steel_4340", "Aluminum_7050_T7451", "Titanium_Ti6Al4V"],
            solver_type="explicit",
            analysis_duration=0.500,
            timestep=1e-5,
            tags=["landing gear", "impact", "aerospace"]
        ))

    def _load_biomedical_templates(self) -> None:
        """Load biomedical industry templates"""
        # Hip implant stress
        self.add_template(SimulationTemplate(
            name="biomedical_hip_implant_stress",
            category=TemplateCategory.BIOMEDICAL,
            analysis_type=AnalysisType.STATIC,
            description="Hip implant stress analysis under gait loading",
            element_type="solid",
            element_formulation="tet10",
            target_element_size=1.0,
            min_element_size=0.3,
            materials=["Titanium_Ti6Al4V_ELI", "CoCrMo_Alloy", "PEEK"],
            solver_type="implicit",
            tags=["implant", "hip", "biomedical", "orthopedic"]
        ))

        # Dental implant
        self.add_template(SimulationTemplate(
            name="biomedical_dental_implant",
            category=TemplateCategory.BIOMEDICAL,
            analysis_type=AnalysisType.STATIC,
            description="Dental implant stress analysis under mastication",
            element_type="solid",
            element_formulation="tet10",
            target_element_size=0.5,
            materials=["Titanium_Grade_2", "Zirconia_ZrO2"],
            solver_type="implicit",
            tags=["dental", "implant", "biomedical"]
        ))

        # Stent expansion
        self.add_template(SimulationTemplate(
            name="biomedical_stent_expansion",
            category=TemplateCategory.BIOMEDICAL,
            analysis_type=AnalysisType.NONLINEAR,
            description="Coronary stent expansion simulation",
            element_type="solid",
            element_formulation="hex8",
            target_element_size=0.2,
            materials=["Stainless_316", "Nitinol_SMA"],
            solver_type="implicit",
            tags=["stent", "cardiovascular", "biomedical"]
        ))

    def _load_construction_templates(self) -> None:
        """Load construction industry templates"""
        # Building seismic
        self.add_template(SimulationTemplate(
            name="construction_building_seismic",
            category=TemplateCategory.CONSTRUCTION,
            analysis_type=AnalysisType.DYNAMIC,
            description="Building seismic response analysis",
            element_type="beam",
            element_formulation="beam3d",
            target_element_size=500.0,
            materials=["Steel_Mild_A36", "Concrete_40MPa"],
            solver_type="implicit",
            analysis_duration=30.0,
            timestep=0.01,
            tags=["seismic", "building", "construction"]
        ))

        # Bridge load test
        self.add_template(SimulationTemplate(
            name="construction_bridge_load",
            category=TemplateCategory.CONSTRUCTION,
            analysis_type=AnalysisType.STATIC,
            description="Bridge static load test analysis",
            element_type="shell",
            element_formulation="shell4",
            target_element_size=200.0,
            materials=["Steel_HSLA_50", "Concrete_60MPa"],
            solver_type="implicit",
            tags=["bridge", "load test", "construction"]
        ))

    def _load_manufacturing_templates(self) -> None:
        """Load manufacturing process templates"""
        # Sheet metal forming
        self.add_template(SimulationTemplate(
            name="manufacturing_sheet_forming",
            category=TemplateCategory.MANUFACTURING,
            analysis_type=AnalysisType.NONLINEAR,
            description="Sheet metal stamping/forming simulation",
            element_type="shell",
            element_formulation="shell4",
            target_element_size=5.0,
            materials=["Steel_DP600", "Aluminum_6061_T6"],
            solver_type="explicit",
            analysis_duration=0.500,
            friction_coefficient=0.15,
            tags=["forming", "stamping", "manufacturing"]
        ))

        # Drop test
        self.add_template(SimulationTemplate(
            name="manufacturing_package_drop",
            category=TemplateCategory.MANUFACTURING,
            analysis_type=AnalysisType.IMPACT,
            description="Package drop test simulation (ASTM D5276)",
            element_type="solid",
            element_formulation="hex8",
            target_element_size=10.0,
            materials=["ABS_Plastic", "PP_Polypropylene", "Foam_EPS_25"],
            solver_type="explicit",
            analysis_duration=0.050,
            timestep=1e-6,
            tags=["drop test", "packaging", "manufacturing"]
        ))

    def _load_other_templates(self) -> None:
        """Load other industry templates"""
        # Marine propeller
        self.add_template(SimulationTemplate(
            name="marine_propeller_fatigue",
            category=TemplateCategory.MARINE,
            analysis_type=AnalysisType.FATIGUE,
            description="Marine propeller fatigue analysis",
            element_type="solid",
            element_formulation="tet10",
            target_element_size=20.0,
            materials=["Bronze_C90700", "Stainless_316"],
            solver_type="implicit",
            tags=["propeller", "fatigue", "marine"]
        ))

        # Wind turbine blade
        self.add_template(SimulationTemplate(
            name="energy_wind_turbine_blade",
            category=TemplateCategory.ENERGY,
            analysis_type=AnalysisType.STATIC,
            description="Wind turbine blade structural analysis",
            element_type="shell",
            element_formulation="shell4",
            target_element_size=100.0,
            materials=["GlassFiber_Epoxy", "CarbonFiber_Epoxy_Woven"],
            solver_type="implicit",
            tags=["wind", "turbine", "energy", "renewable"]
        ))

        # Electronics PCB drop
        self.add_template(SimulationTemplate(
            name="electronics_pcb_drop",
            category=TemplateCategory.ELECTRONICS,
            analysis_type=AnalysisType.IMPACT,
            description="PCB drop test for mobile devices",
            element_type="solid",
            element_formulation="hex8",
            target_element_size=2.0,
            materials=["Copper_C11000", "Glass_Soda_Lime", "ABS_Plastic"],
            solver_type="explicit",
            analysis_duration=0.010,
            tags=["pcb", "drop", "electronics", "mobile"]
        ))

        # Ballistic impact
        self.add_template(SimulationTemplate(
            name="defense_ballistic_impact",
            category=TemplateCategory.DEFENSE,
            analysis_type=AnalysisType.IMPACT,
            description="Ballistic impact on armor plates",
            element_type="solid",
            element_formulation="hex8",
            target_element_size=1.0,
            materials=["Kevlar_Epoxy", "Alumina_Al2O3", "Steel_Maraging_300"],
            solver_type="explicit",
            analysis_duration=0.001,
            timestep=1e-7,
            tags=["ballistic", "armor", "defense"]
        ))

        # Consumer product compression
        self.add_template(SimulationTemplate(
            name="consumer_product_compression",
            category=TemplateCategory.CONSUMER,
            analysis_type=AnalysisType.STATIC,
            description="Consumer product compression test",
            element_type="solid",
            element_formulation="tet4",
            target_element_size=5.0,
            materials=["ABS_Plastic", "Polycarbonate_PC", "PMMA_Acrylic"],
            solver_type="implicit",
            tags=["compression", "consumer", "product"]
        ))

        # Smartphone drop test
        self.add_template(SimulationTemplate(
            name="consumer_smartphone_drop",
            category=TemplateCategory.CONSUMER,
            analysis_type=AnalysisType.IMPACT,
            description="Smartphone drop test (1.5m height)",
            element_type="solid",
            element_formulation="hex8",
            target_element_size=1.5,
            materials=["Glass_Soda_Lime", "Aluminum_6061_T6", "ABS_Plastic"],
            solver_type="explicit",
            analysis_duration=0.020,
            timestep=5e-7,
            tags=["smartphone", "drop", "consumer", "mobile"]
        ))

        # Helmet impact test
        self.add_template(SimulationTemplate(
            name="consumer_helmet_impact",
            category=TemplateCategory.CONSUMER,
            analysis_type=AnalysisType.IMPACT,
            description="Helmet impact test (DOT/ECE standards)",
            element_type="solid",
            element_formulation="hex8",
            target_element_size=3.0,
            materials=["ABS_Plastic", "Polycarbonate_PC", "Foam_EPS_25"],
            solver_type="explicit",
            analysis_duration=0.015,
            timestep=1e-6,
            tags=["helmet", "impact", "safety", "consumer"]
        ))

        # Automotive foam compression
        self.add_template(SimulationTemplate(
            name="automotive_foam_compression",
            category=TemplateCategory.AUTOMOTIVE,
            analysis_type=AnalysisType.NONLINEAR,
            description="Automotive foam seat compression analysis",
            element_type="solid",
            element_formulation="hex8",
            target_element_size=8.0,
            materials=["Foam_PU_Rigid_50", "Foam_PU_Rigid_100"],
            solver_type="implicit",
            tags=["foam", "compression", "seat", "automotive"]
        ))

        # Bumper impact
        self.add_template(SimulationTemplate(
            name="automotive_bumper_impact",
            category=TemplateCategory.AUTOMOTIVE,
            analysis_type=AnalysisType.IMPACT,
            description="Low-speed bumper impact (FMVSS 581)",
            element_type="solid",
            element_formulation="hex8",
            target_element_size=5.0,
            materials=["PP_Polypropylene", "Steel_Mild_A36", "Foam_PU_Rigid_100"],
            solver_type="explicit",
            analysis_duration=0.100,
            timestep=1e-6,
            tags=["bumper", "impact", "automotive", "low-speed"]
        ))

        # Fuel tank sloshing
        self.add_template(SimulationTemplate(
            name="aerospace_fuel_tank_sloshing",
            category=TemplateCategory.AEROSPACE,
            analysis_type=AnalysisType.DYNAMIC,
            description="Aircraft fuel tank sloshing analysis",
            element_type="solid",
            element_formulation="hex8",
            target_element_size=20.0,
            materials=["Aluminum_2024_T3", "Aluminum_7075_T6"],
            solver_type="explicit",
            analysis_duration=10.0,
            timestep=1e-4,
            tags=["fuel", "sloshing", "aerospace", "dynamics"]
        ))

        # Composite panel impact
        self.add_template(SimulationTemplate(
            name="aerospace_composite_impact",
            category=TemplateCategory.AEROSPACE,
            analysis_type=AnalysisType.IMPACT,
            description="Composite panel low-velocity impact",
            element_type="shell",
            element_formulation="shell4",
            target_element_size=5.0,
            materials=["CarbonFiber_Epoxy_UD", "CarbonFiber_Epoxy_Woven"],
            solver_type="explicit",
            analysis_duration=0.010,
            timestep=5e-7,
            tags=["composite", "impact", "aerospace", "panel"]
        ))

        # Knee implant
        self.add_template(SimulationTemplate(
            name="biomedical_knee_implant",
            category=TemplateCategory.BIOMEDICAL,
            analysis_type=AnalysisType.STATIC,
            description="Knee implant stress analysis under gait loading",
            element_type="solid",
            element_formulation="tet10",
            target_element_size=2.0,
            min_element_size=0.5,
            materials=["Titanium_Ti6Al4V_ELI", "CoCrMo_Alloy", "PEEK"],
            solver_type="implicit",
            tags=["implant", "knee", "biomedical", "orthopedic"]
        ))

        # Spinal implant
        self.add_template(SimulationTemplate(
            name="biomedical_spinal_implant",
            category=TemplateCategory.BIOMEDICAL,
            analysis_type=AnalysisType.STATIC,
            description="Spinal fusion implant stress analysis",
            element_type="solid",
            element_formulation="tet10",
            target_element_size=1.5,
            min_element_size=0.3,
            materials=["Titanium_Ti6Al4V_ELI", "PEEK"],
            solver_type="implicit",
            tags=["implant", "spine", "biomedical", "orthopedic"]
        ))

        # Ship hull impact
        self.add_template(SimulationTemplate(
            name="marine_hull_impact",
            category=TemplateCategory.MARINE,
            analysis_type=AnalysisType.IMPACT,
            description="Ship hull impact with floating object",
            element_type="shell",
            element_formulation="shell4",
            target_element_size=50.0,
            materials=["Steel_Mild_A36", "Steel_HSLA_50"],
            solver_type="explicit",
            analysis_duration=0.500,
            timestep=1e-5,
            tags=["ship", "hull", "impact", "marine"]
        ))

        # Wave loading
        self.add_template(SimulationTemplate(
            name="marine_wave_loading",
            category=TemplateCategory.MARINE,
            analysis_type=AnalysisType.DYNAMIC,
            description="Marine structure wave loading analysis",
            element_type="shell",
            element_formulation="shell4",
            target_element_size=100.0,
            materials=["Steel_Mild_A36", "Stainless_316"],
            solver_type="implicit",
            analysis_duration=60.0,
            timestep=0.1,
            tags=["wave", "loading", "marine", "offshore"]
        ))

        # Solar panel structural
        self.add_template(SimulationTemplate(
            name="energy_solar_panel_structural",
            category=TemplateCategory.ENERGY,
            analysis_type=AnalysisType.STATIC,
            description="Solar panel structural analysis under wind load",
            element_type="shell",
            element_formulation="shell4",
            target_element_size=30.0,
            materials=["Aluminum_6061_T6", "Glass_Soda_Lime"],
            solver_type="implicit",
            tags=["solar", "panel", "energy", "renewable"]
        ))

        # Battery cell impact
        self.add_template(SimulationTemplate(
            name="energy_battery_impact",
            category=TemplateCategory.ENERGY,
            analysis_type=AnalysisType.IMPACT,
            description="Lithium-ion battery cell impact test",
            element_type="solid",
            element_formulation="hex8",
            target_element_size=2.0,
            materials=["Aluminum_6061_T6", "Copper_C11000", "Steel_Mild_A36"],
            solver_type="explicit",
            analysis_duration=0.010,
            timestep=5e-7,
            tags=["battery", "impact", "energy", "ev"]
        ))

        # Deep drawing
        self.add_template(SimulationTemplate(
            name="manufacturing_deep_drawing",
            category=TemplateCategory.MANUFACTURING,
            analysis_type=AnalysisType.NONLINEAR,
            description="Sheet metal deep drawing simulation",
            element_type="shell",
            element_formulation="shell4",
            target_element_size=3.0,
            materials=["Steel_DP600", "Aluminum_6061_T6"],
            solver_type="explicit",
            analysis_duration=2.0,
            friction_coefficient=0.12,
            tags=["deep drawing", "forming", "manufacturing"]
        ))

        # Tube bending
        self.add_template(SimulationTemplate(
            name="manufacturing_tube_bending",
            category=TemplateCategory.MANUFACTURING,
            analysis_type=AnalysisType.NONLINEAR,
            description="Tube bending process simulation",
            element_type="shell",
            element_formulation="shell4",
            target_element_size=5.0,
            materials=["Steel_Mild_A36", "Aluminum_6061_T6", "Stainless_304"],
            solver_type="implicit",
            tags=["bending", "tube", "manufacturing"]
        ))

        # Blast loading
        self.add_template(SimulationTemplate(
            name="construction_blast_loading",
            category=TemplateCategory.CONSTRUCTION,
            analysis_type=AnalysisType.DYNAMIC,
            description="Building blast loading analysis",
            element_type="shell",
            element_formulation="shell4",
            target_element_size=200.0,
            materials=["Steel_Mild_A36", "Concrete_40MPa"],
            solver_type="explicit",
            analysis_duration=0.500,
            timestep=1e-5,
            tags=["blast", "explosion", "construction", "defense"]
        ))

        # Earthquake response
        self.add_template(SimulationTemplate(
            name="construction_earthquake_response",
            category=TemplateCategory.CONSTRUCTION,
            analysis_type=AnalysisType.DYNAMIC,
            description="Building earthquake response (time-history)",
            element_type="beam",
            element_formulation="beam3d",
            target_element_size=1000.0,
            materials=["Steel_Mild_A36", "Concrete_40MPa"],
            solver_type="implicit",
            analysis_duration=40.0,
            timestep=0.01,
            tags=["earthquake", "seismic", "construction", "dynamic"]
        ))


# Module-level convenience functions
_global_manager = None


def get_manager() -> TemplateManager:
    """Get global template manager instance"""
    global _global_manager
    if _global_manager is None:
        _global_manager = TemplateManager()
        _global_manager.load_builtin_templates()
    return _global_manager


def load_template(name: str) -> Optional[SimulationTemplate]:
    """Load template by name"""
    return get_manager().get_template(name)


def list_templates(category: Optional[TemplateCategory] = None) -> List[str]:
    """List available templates"""
    return get_manager().list_templates(category)


def search_templates(keyword: str) -> List[SimulationTemplate]:
    """Search templates by keyword"""
    return get_manager().search_templates(keyword)
