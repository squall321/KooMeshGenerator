#!/usr/bin/env python3
"""
Expand material database
"""

import json
from pathlib import Path

# Load current database
db_path = Path("/home/user/KooMeshGenerator/koomesh/materials/material_database.json")
with open(db_path, 'r') as f:
    data = json.load(f)

# Add more steels
data["steels"]["Steel_A572_Grade_50"] = {
    "material_type": "elastic_plastic",
    "density": 7850.0,
    "elastic_modulus": 200e9,
    "poisson_ratio": 0.30,
    "yield_stress": 345e6,
    "tangent_modulus": 2.5e9,
    "failure_strain": 0.18,
    "unit_system": "si",
    "metadata": {
        "description": "ASTM A572 Grade 50 structural steel",
        "grade": "A572-50",
        "applications": ["structural", "bridges", "buildings"]
    }
}

data["steels"]["Steel_HY80"] = {
    "material_type": "elastic_plastic",
    "density": 7850.0,
    "elastic_modulus": 207e9,
    "poisson_ratio": 0.30,
    "yield_stress": 550e6,
    "tangent_modulus": 3.5e9,
    "failure_strain": 0.18,
    "unit_system": "si",
    "metadata": {
        "description": "HY-80 naval steel",
        "grade": "HY-80",
        "applications": ["naval", "submarine", "defense"],
        "high_strength": True
    }
}

data["steels"]["Steel_HY100"] = {
    "material_type": "elastic_plastic",
    "density": 7850.0,
    "elastic_modulus": 207e9,
    "poisson_ratio": 0.30,
    "yield_stress": 690e6,
    "tangent_modulus": 4e9,
    "failure_strain": 0.15,
    "unit_system": "si",
    "metadata": {
        "description": "HY-100 high-strength naval steel",
        "grade": "HY-100",
        "applications": ["naval", "submarine", "defense"],
        "high_strength": True
    }
}

# Add more aluminum alloys
data["aluminum_alloys"]["Aluminum_1100_O"] = {
    "material_type": "elastic_plastic",
    "density": 2710.0,
    "elastic_modulus": 69e9,
    "poisson_ratio": 0.33,
    "yield_stress": 34e6,
    "tangent_modulus": 500e6,
    "failure_strain": 0.35,
    "unit_system": "si",
    "metadata": {
        "description": "Commercially pure aluminum (annealed)",
        "grade": "1100-O",
        "applications": ["chemical equipment", "food containers"],
        "excellent_corrosion_resistance": True
    }
}

data["aluminum_alloys"]["Aluminum_5083_H321"] = {
    "material_type": "elastic_plastic",
    "density": 2660.0,
    "elastic_modulus": 72e9,
    "poisson_ratio": 0.33,
    "yield_stress": 228e6,
    "tangent_modulus": 900e6,
    "failure_strain": 0.16,
    "unit_system": "si",
    "metadata": {
        "description": "Marine-grade aluminum alloy",
        "grade": "5083-H321",
        "applications": ["marine", "shipbuilding", "offshore"],
        "corrosion_resistant": True,
        "weldable": True
    }
}

# Add more titanium alloys
data["titanium_alloys"]["Titanium_Beta_C"] = {
    "material_type": "elastic_plastic",
    "density": 4820.0,
    "elastic_modulus": 100e9,
    "poisson_ratio": 0.33,
    "yield_stress": 1100e6,
    "tangent_modulus": 2.5e9,
    "failure_strain": 0.10,
    "unit_system": "si",
    "metadata": {
        "description": "Beta titanium alloy (Ti-3Al-8V-6Cr-4Mo-4Zr)",
        "grade": "Beta-C",
        "applications": ["aerospace", "medical", "springs"],
        "high_strength": True
    }
}

# Add more plastics
data["plastics"]["PLA"] = {
    "material_type": "elastic_plastic",
    "density": 1240.0,
    "elastic_modulus": 3500e6,
    "poisson_ratio": 0.36,
    "yield_stress": 60e6,
    "tangent_modulus": 200e6,
    "failure_strain": 0.06,
    "unit_system": "si",
    "metadata": {
        "description": "Polylactic Acid (biodegradable)",
        "applications": ["3D printing", "packaging", "medical"],
        "biodegradable": True
    }
}

data["plastics"]["PETG"] = {
    "material_type": "elastic_plastic",
    "density": 1270.0,
    "elastic_modulus": 2100e6,
    "poisson_ratio": 0.38,
    "yield_stress": 50e6,
    "tangent_modulus": 150e6,
    "failure_strain": 0.15,
    "unit_system": "si",
    "metadata": {
        "description": "Glycol-modified PET",
        "applications": ["3D printing", "packaging", "displays"],
        "impact_resistant": True
    }
}

data["plastics"]["PSU_Polysulfone"] = {
    "material_type": "elastic_plastic",
    "density": 1240.0,
    "elastic_modulus": 2480e6,
    "poisson_ratio": 0.37,
    "yield_stress": 70e6,
    "tangent_modulus": 180e6,
    "failure_strain": 0.50,
    "unit_system": "si",
    "metadata": {
        "description": "Polysulfone high-performance thermoplastic",
        "applications": ["medical", "food service", "automotive"],
        "high_temperature": True,
        "temperature_max_c": 170
    }
}

data["plastics"]["PEI_Ultem"] = {
    "material_type": "elastic_plastic",
    "density": 1270.0,
    "elastic_modulus": 3200e6,
    "poisson_ratio": 0.40,
    "yield_stress": 105e6,
    "tangent_modulus": 250e6,
    "failure_strain": 0.06,
    "unit_system": "si",
    "metadata": {
        "description": "Polyetherimide (Ultem)",
        "applications": ["aerospace", "automotive", "electronics"],
        "high_performance": True,
        "temperature_max_c": 217,
        "flame_resistant": True
    }
}

# Add more composites
data["composites"]["Fiberglass_SMC"] = {
    "material_type": "elastic",
    "density": 1800.0,
    "elastic_modulus": 13e9,
    "poisson_ratio": 0.30,
    "yield_stress": None,
    "unit_system": "si",
    "metadata": {
        "description": "Sheet Molding Compound (fiberglass/polyester)",
        "fiber_volume": 0.30,
        "applications": ["automotive body panels", "electrical"],
        "cost_effective": True
    }
}

data["composites"]["Boron_Epoxy"] = {
    "material_type": "elastic",
    "density": 2000.0,
    "elastic_modulus": 210e9,
    "poisson_ratio": 0.21,
    "yield_stress": None,
    "unit_system": "si",
    "metadata": {
        "description": "Boron fiber/epoxy composite",
        "fiber_volume": 0.50,
        "applications": ["aerospace", "military"],
        "very_high_stiffness": True
    }
}

# Add more elastomers
data["elastomers"]["EPDM_Rubber"] = {
    "material_type": "hyperelastic",
    "density": 1150.0,
    "elastic_modulus": 1800e3,
    "poisson_ratio": 0.49,
    "yield_stress": None,
    "unit_system": "si",
    "metadata": {
        "description": "Ethylene Propylene Diene Monomer rubber",
        "hardness_shore_a": 60,
        "applications": ["automotive seals", "roofing", "electrical"],
        "weather_resistant": True,
        "ozone_resistant": True
    }
}

data["elastomers"]["Viton_FKM"] = {
    "material_type": "hyperelastic",
    "density": 1850.0,
    "elastic_modulus": 3000e3,
    "poisson_ratio": 0.49,
    "yield_stress": None,
    "unit_system": "si",
    "metadata": {
        "description": "Fluoroelastomer (Viton)",
        "hardness_shore_a": 75,
        "applications": ["aerospace", "automotive", "chemical"],
        "chemical_resistant": True,
        "temperature_max_c": 230
    }
}

# Add new category: magnesium alloys
data["magnesium_alloys"] = {
    "Magnesium_AZ31B": {
        "material_type": "elastic_plastic",
        "density": 1770.0,
        "elastic_modulus": 45e9,
        "poisson_ratio": 0.35,
        "yield_stress": 220e6,
        "tangent_modulus": 800e6,
        "failure_strain": 0.15,
        "unit_system": "si",
        "metadata": {
            "description": "Magnesium-aluminum-zinc alloy",
            "grade": "AZ31B",
            "applications": ["automotive", "aerospace", "electronics"],
            "lightweight": True
        }
    },
    "Magnesium_AZ80A_T5": {
        "material_type": "elastic_plastic",
        "density": 1800.0,
        "elastic_modulus": 45e9,
        "poisson_ratio": 0.35,
        "yield_stress": 275e6,
        "tangent_modulus": 1000e6,
        "failure_strain": 0.11,
        "unit_system": "si",
        "metadata": {
            "description": "High-strength magnesium alloy",
            "grade": "AZ80A-T5",
            "applications": ["aerospace", "automotive"],
            "high_strength": True
        }
    },
    "Magnesium_WE43": {
        "material_type": "elastic_plastic",
        "density": 1840.0,
        "elastic_modulus": 44e9,
        "poisson_ratio": 0.27,
        "yield_stress": 170e6,
        "tangent_modulus": 700e6,
        "failure_strain": 0.20,
        "unit_system": "si",
        "metadata": {
            "description": "Rare-earth magnesium alloy",
            "grade": "WE43",
            "applications": ["aerospace", "medical implants"],
            "biocompatible": True,
            "high_temperature": True
        }
    }
}

# Add more concrete types
data["concrete"]["Concrete_50MPa"] = {
    "material_type": "elastic",
    "density": 2450.0,
    "elastic_modulus": 37e9,
    "poisson_ratio": 0.20,
    "yield_stress": None,
    "unit_system": "si",
    "metadata": {
        "description": "High-strength concrete",
        "compressive_strength": 50e6,
        "applications": ["high-rise", "heavy infrastructure"]
    }
}

data["concrete"]["Concrete_80MPa_UHPC"] = {
    "material_type": "elastic",
    "density": 2500.0,
    "elastic_modulus": 50e9,
    "poisson_ratio": 0.19,
    "yield_stress": None,
    "unit_system": "si",
    "metadata": {
        "description": "Ultra-high-performance concrete",
        "compressive_strength": 80e6,
        "applications": ["bridges", "special structures"],
        "uhpc": True
    }
}

data["concrete"]["Lightweight_Concrete"] = {
    "material_type": "elastic",
    "density": 1850.0,
    "elastic_modulus": 17e9,
    "poisson_ratio": 0.20,
    "yield_stress": None,
    "unit_system": "si",
    "metadata": {
        "description": "Lightweight aggregate concrete",
        "compressive_strength": 25e6,
        "applications": ["non-structural", "insulation"],
        "lightweight": True
    }
}

# Add more ceramics
data["ceramics"]["Silicon_Nitride_Si3N4"] = {
    "material_type": "elastic",
    "density": 3200.0,
    "elastic_modulus": 310e9,
    "poisson_ratio": 0.27,
    "yield_stress": None,
    "unit_system": "si",
    "metadata": {
        "description": "Silicon nitride ceramic",
        "applications": ["bearings", "cutting tools", "turbines"],
        "high_temperature": True,
        "wear_resistant": True
    }
}

data["ceramics"]["Boron_Carbide_B4C"] = {
    "material_type": "elastic",
    "density": 2520.0,
    "elastic_modulus": 450e9,
    "poisson_ratio": 0.21,
    "yield_stress": None,
    "unit_system": "si",
    "metadata": {
        "description": "Boron carbide (extremely hard)",
        "applications": ["armor", "abrasives", "nuclear"],
        "hardness_high": True,
        "third_hardest_material": True
    }
}

# Add more foams
data["foams"]["Foam_PU_Flexible_30"] = {
    "material_type": "foam",
    "density": 30.0,
    "elastic_modulus": 150e3,
    "poisson_ratio": 0.10,
    "yield_stress": 15e3,
    "unit_system": "si",
    "metadata": {
        "description": "Flexible polyurethane foam",
        "applications": ["seating", "cushioning", "packaging"]
    }
}

data["foams"]["Foam_Polystyrene_40"] = {
    "material_type": "foam",
    "density": 40.0,
    "elastic_modulus": 5e6,
    "poisson_ratio": 0.10,
    "yield_stress": 120e3,
    "unit_system": "si",
    "metadata": {
        "description": "Expanded polystyrene foam",
        "applications": ["insulation", "packaging", "construction"]
    }
}

# Add more wood types
data["wood"]["Bamboo"] = {
    "material_type": "elastic",
    "density": 700.0,
    "elastic_modulus": 15e9,
    "poisson_ratio": 0.35,
    "yield_stress": None,
    "unit_system": "si",
    "metadata": {
        "description": "Bamboo (along grain)",
        "applications": ["construction", "furniture", "sustainable"],
        "sustainable": True,
        "high_strength_to_weight": True
    }
}

data["wood"]["Birch_Plywood"] = {
    "material_type": "elastic",
    "density": 680.0,
    "elastic_modulus": 10e9,
    "poisson_ratio": 0.32,
    "yield_stress": None,
    "unit_system": "si",
    "metadata": {
        "description": "Birch plywood (high-quality)",
        "applications": ["furniture", "cabinetry", "structural"]
    }
}

# Add metals category
data["other_metals"] = {
    "Cobalt_Chrome_CoCr": {
        "material_type": "elastic_plastic",
        "density": 8300.0,
        "elastic_modulus": 210e9,
        "poisson_ratio": 0.30,
        "yield_stress": 450e6,
        "tangent_modulus": 2500e6,
        "failure_strain": 0.20,
        "unit_system": "si",
        "metadata": {
            "description": "Cobalt-chromium alloy",
            "applications": ["medical implants", "dental", "aerospace"],
            "biocompatible": True,
            "wear_resistant": True
        }
    },
    "Nitinol_NiTi": {
        "material_type": "elastic_plastic",
        "density": 6450.0,
        "elastic_modulus": 83e9,
        "poisson_ratio": 0.33,
        "yield_stress": 195e6,
        "tangent_modulus": 1000e6,
        "failure_strain": 0.08,
        "unit_system": "si",
        "metadata": {
            "description": "Nickel-titanium shape memory alloy",
            "applications": ["medical devices", "actuators", "aerospace"],
            "shape_memory": True,
            "superelastic": True
        }
    }
}

# Update metadata
data["_metadata"]["total_materials"] = sum(
    len(v) for k, v in data.items() if k != "_metadata" and isinstance(v, dict)
)
data["_metadata"]["version"] = "2.1.0"
data["_metadata"]["categories"].extend(["magnesium_alloys", "other_metals"])

# Save updated database
with open(db_path, 'w') as f:
    json.dump(data, f, indent=2)

print(f"✓ Material database expanded to {data['_metadata']['total_materials']} materials")
