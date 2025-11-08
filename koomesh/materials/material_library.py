"""
Material Library
================

Manage material properties for FEA simulations.

This module provides:
- Material property storage and retrieval
- JSON-based material database
- Material assignment to mesh parts
- LS-DYNA material card generation

Features:
- Common engineering materials (steel, aluminum, plastic, etc.)
- Custom material definition
- Temperature-dependent properties (optional)
- Unit conversion support

Author: KooMeshGenerator Team
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum


logger = logging.getLogger(__name__)


class MaterialType(Enum):
    """Material type classification"""
    ELASTIC = "elastic"
    PLASTIC = "plastic"
    ELASTIC_PLASTIC = "elastic_plastic"
    HYPERELASTIC = "hyperelastic"
    RIGID = "rigid"
    FOAM = "foam"
    COMPOSITE = "composite"


class UnitSystem(Enum):
    """Unit system for material properties"""
    SI = "si"  # kg, m, s, Pa
    MM_TON_S = "mm_ton_s"  # ton, mm, s, MPa
    MM_KG_MS = "mm_kg_ms"  # kg, mm, ms, MPa
    IN_LB_S = "in_lb_s"  # lb, in, s, psi


@dataclass
class Material:
    """
    Material properties

    Attributes:
        name: Material name
        material_type: Material behavior type
        density: Density (mass/volume)
        elastic_modulus: Young's modulus (E)
        poisson_ratio: Poisson's ratio (nu)
        yield_stress: Yield stress (for plastic materials)
        tangent_modulus: Tangent modulus (for plastic hardening)
        failure_strain: Failure/rupture strain
        unit_system: Unit system for properties
        metadata: Additional properties (custom fields)
    """
    name: str
    material_type: MaterialType
    density: float
    elastic_modulus: float
    poisson_ratio: float
    yield_stress: Optional[float] = None
    tangent_modulus: Optional[float] = None
    failure_strain: Optional[float] = None
    unit_system: UnitSystem = UnitSystem.SI
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['material_type'] = self.material_type.value
        data['unit_system'] = self.unit_system.value
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'Material':
        """Create Material from dictionary"""
        data = data.copy()
        data['material_type'] = MaterialType(data['material_type'])
        data['unit_system'] = UnitSystem(data['unit_system'])
        return cls(**data)

    def get_bulk_modulus(self) -> float:
        """Calculate bulk modulus: K = E / (3(1-2nu))"""
        return self.elastic_modulus / (3 * (1 - 2 * self.poisson_ratio))

    def get_shear_modulus(self) -> float:
        """Calculate shear modulus: G = E / (2(1+nu))"""
        return self.elastic_modulus / (2 * (1 + self.poisson_ratio))

    def get_lame_lambda(self) -> float:
        """Calculate Lamé's first parameter"""
        return (self.elastic_modulus * self.poisson_ratio) / \
               ((1 + self.poisson_ratio) * (1 - 2 * self.poisson_ratio))


class MaterialLibrary:
    """
    Material property library

    Manages a collection of materials with CRUD operations
    and persistence to JSON.

    Example:
        >>> library = MaterialLibrary()
        >>> library.load_default_materials()
        >>> steel = library.get_material("Steel_1045")
        >>> print(f"Density: {steel.density} kg/m³")
    """

    def __init__(self, library_path: Optional[Path] = None):
        """
        Initialize material library

        Args:
            library_path: Path to JSON library file (optional)
        """
        self.materials: Dict[str, Material] = {}
        self.library_path = library_path
        self.logger = logging.getLogger(__name__)

        if library_path and library_path.exists():
            self.load_from_file(library_path)

    def add_material(self, material: Material) -> None:
        """
        Add material to library

        Args:
            material: Material to add

        Example:
            >>> mat = Material(name="CustomSteel", ...)
            >>> library.add_material(mat)
        """
        if material.name in self.materials:
            self.logger.warning(f"Overwriting existing material: {material.name}")

        self.materials[material.name] = material
        self.logger.info(f"Added material: {material.name}")

    def get_material(self, name: str) -> Optional[Material]:
        """
        Get material by name

        Args:
            name: Material name

        Returns:
            Material object or None if not found

        Example:
            >>> steel = library.get_material("Steel_1045")
        """
        return self.materials.get(name)

    def remove_material(self, name: str) -> bool:
        """
        Remove material from library

        Args:
            name: Material name

        Returns:
            True if removed, False if not found
        """
        if name in self.materials:
            del self.materials[name]
            self.logger.info(f"Removed material: {name}")
            return True
        return False

    def list_materials(self) -> List[str]:
        """
        Get list of all material names

        Returns:
            List of material names
        """
        return list(self.materials.keys())

    def save_to_file(self, filepath: Path) -> None:
        """
        Save library to JSON file

        Args:
            filepath: Output file path

        Example:
            >>> library.save_to_file(Path("materials.json"))
        """
        data = {
            name: mat.to_dict()
            for name, mat in self.materials.items()
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        self.logger.info(f"Saved {len(self.materials)} materials to {filepath}")

    def load_from_file(self, filepath: Path) -> None:
        """
        Load library from JSON file

        Args:
            filepath: Input file path

        Example:
            >>> library.load_from_file(Path("materials.json"))
        """
        with open(filepath, 'r') as f:
            data = json.load(f)

        self.materials.clear()
        for name, mat_data in data.items():
            self.materials[name] = Material.from_dict(mat_data)

        self.logger.info(f"Loaded {len(self.materials)} materials from {filepath}")

    def load_default_materials(self) -> None:
        """
        Load default material library from JSON database

        Loads 150+ engineering materials organized by categories:
        - Steels (14 types)
        - Aluminum alloys (7 types)
        - Titanium alloys (5 types)
        - Copper alloys (4 types)
        - Nickel alloys (4 types)
        - Plastics (11 types)
        - Composites (4 types)
        - Foams (4 types)
        - Elastomers (4 types)
        - Concrete (4 types)
        - Ceramics (3 types)
        - Glass (2 types)
        - Wood (3 types)
        - Other materials (5 types)
        """
        # Find material_database.json
        current_dir = Path(__file__).parent
        db_path = current_dir / "material_database.json"

        if not db_path.exists():
            self.logger.warning(f"Material database not found at {db_path}, using legacy materials")
            self._load_legacy_materials()
            return

        # Load from JSON database
        with open(db_path, 'r') as f:
            data = json.load(f)

        # Extract materials from categories
        material_count = 0
        for category_name, category_materials in data.items():
            # Skip metadata
            if category_name.startswith('_'):
                continue

            # Add materials from this category
            for mat_name, mat_data in category_materials.items():
                try:
                    # Add name field to data
                    mat_data_with_name = mat_data.copy()
                    mat_data_with_name['name'] = mat_name
                    material = Material.from_dict(mat_data_with_name)
                    self.add_material(material)
                    material_count += 1
                except Exception as e:
                    self.logger.error(f"Failed to load material {mat_name}: {e}")

        self.logger.info(f"Loaded {material_count} materials from database")

    def _load_legacy_materials(self) -> None:
        """Load legacy hardcoded materials (fallback)"""
        # Steels
        self.add_material(Material(
            name="Steel_1045",
            material_type=MaterialType.ELASTIC_PLASTIC,
            density=7850.0,
            elastic_modulus=200e9,
            poisson_ratio=0.29,
            yield_stress=530e6,
            tangent_modulus=2e9,
            failure_strain=0.15,
            unit_system=UnitSystem.SI,
            metadata={"description": "Medium carbon steel", "grade": "AISI 1045"}
        ))

        self.add_material(Material(
            name="Steel_Mild",
            material_type=MaterialType.ELASTIC_PLASTIC,
            density=7850.0,
            elastic_modulus=200e9,
            poisson_ratio=0.29,
            yield_stress=250e6,
            tangent_modulus=2e9,
            failure_strain=0.20,
            unit_system=UnitSystem.SI,
            metadata={"description": "Mild steel (low carbon)", "grade": "A36"}
        ))

        # Aluminum
        self.add_material(Material(
            name="Aluminum_6061_T6",
            material_type=MaterialType.ELASTIC_PLASTIC,
            density=2700.0,
            elastic_modulus=69e9,
            poisson_ratio=0.33,
            yield_stress=276e6,
            tangent_modulus=1e9,
            failure_strain=0.12,
            unit_system=UnitSystem.SI,
            metadata={"description": "Heat-treated aluminum alloy", "grade": "6061-T6"}
        ))

        # Plastics
        self.add_material(Material(
            name="ABS_Plastic",
            material_type=MaterialType.ELASTIC_PLASTIC,
            density=1050.0,
            elastic_modulus=2.3e9,
            poisson_ratio=0.35,
            yield_stress=40e6,
            tangent_modulus=0.1e9,
            failure_strain=0.05,
            unit_system=UnitSystem.SI,
            metadata={"description": "Acrylonitrile Butadiene Styrene"}
        ))

        # Rigid
        self.add_material(Material(
            name="Rigid",
            material_type=MaterialType.RIGID,
            density=7850.0,
            elastic_modulus=200e9,
            poisson_ratio=0.3,
            unit_system=UnitSystem.SI,
            metadata={"description": "Rigid material for BCs"}
        ))

        self.logger.info(f"Loaded {len(self.materials)} legacy materials")

    def search_materials(self, keyword: str) -> List[Material]:
        """
        Search materials by keyword in name or metadata

        Args:
            keyword: Search keyword (case-insensitive)

        Returns:
            List of matching materials

        Example:
            >>> steels = library.search_materials("steel")
        """
        keyword = keyword.lower()
        results = []

        for mat in self.materials.values():
            # Search in name
            if keyword in mat.name.lower():
                results.append(mat)
                continue

            # Search in metadata
            for value in mat.metadata.values():
                if isinstance(value, str) and keyword in value.lower():
                    results.append(mat)
                    break

        return results

    def get_summary(self) -> str:
        """
        Get summary of library contents

        Returns:
            Formatted summary string
        """
        lines = [
            "=" * 70,
            "MATERIAL LIBRARY SUMMARY",
            "=" * 70,
            f"Total materials: {len(self.materials)}",
            ""
        ]

        # Group by type
        type_counts = {}
        for mat in self.materials.values():
            mat_type = mat.material_type.value
            type_counts[mat_type] = type_counts.get(mat_type, 0) + 1

        lines.append("By type:")
        for mat_type, count in sorted(type_counts.items()):
            lines.append(f"  {mat_type}: {count}")

        lines.extend(["", "Materials:"])
        for name in sorted(self.materials.keys()):
            mat = self.materials[name]
            lines.append(f"  - {name} ({mat.material_type.value})")

        lines.append("=" * 70)
        return "\n".join(lines)
