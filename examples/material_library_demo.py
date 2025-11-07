"""
Material Library Demo
=====================

This example demonstrates material property management and
LS-DYNA material card generation.

Features demonstrated:
- Material library creation and management
- Default material database (10+ common materials)
- Material search and retrieval
- Custom material definition
- LS-DYNA material card generation (*MAT_)
- Complete material deck export

Typical use cases:
- Defining materials for crash simulations
- Multi-material assemblies
- Material property database management
- Automated LS-DYNA model generation

Author: KooMeshGenerator Team
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def demo_material_library_basics():
    """Demo 1: Material library basics"""
    logger.info("\n" + "=" * 70)
    logger.info("DEMO 1: Material Library Basics")
    logger.info("=" * 70)
    logger.info("\nLoading and browsing the default material database")

    from koomesh.materials import MaterialLibrary

    # Create library and load defaults
    logger.info("\n1. Creating material library...")
    library = MaterialLibrary()
    library.load_default_materials()

    logger.info(f"   ✅ Loaded {len(library.list_materials())} materials")

    # Show summary
    logger.info("\n2. Library contents:")
    summary = library.get_summary()
    for line in summary.split('\n'):
        logger.info(f"   {line}")

    # Get specific materials
    logger.info("\n3. Retrieving specific materials...")

    steel = library.get_material("Steel_1045")
    logger.info(f"\n   Steel_1045:")
    logger.info(f"   - Density: {steel.density:.0f} kg/m³")
    logger.info(f"   - Elastic modulus: {steel.elastic_modulus/1e9:.0f} GPa")
    logger.info(f"   - Yield stress: {steel.yield_stress/1e6:.0f} MPa")
    logger.info(f"   - Poisson's ratio: {steel.poisson_ratio:.2f}")

    aluminum = library.get_material("Aluminum_6061_T6")
    logger.info(f"\n   Aluminum_6061_T6:")
    logger.info(f"   - Density: {aluminum.density:.0f} kg/m³")
    logger.info(f"   - Elastic modulus: {aluminum.elastic_modulus/1e9:.0f} GPa")
    logger.info(f"   - Yield stress: {aluminum.yield_stress/1e6:.0f} MPa")

    # Search materials
    logger.info("\n4. Searching materials...")
    steels = library.search_materials("steel")
    logger.info(f"\n   Found {len(steels)} steel materials:")
    for mat in steels:
        logger.info(f"   - {mat.name}: {mat.metadata.get('description', 'N/A')}")

    # Derived properties
    logger.info("\n5. Calculating derived properties...")
    G = steel.get_shear_modulus()
    K = steel.get_bulk_modulus()

    logger.info(f"\n   Steel_1045 derived properties:")
    logger.info(f"   - Shear modulus (G): {G/1e9:.1f} GPa")
    logger.info(f"   - Bulk modulus (K): {K/1e9:.1f} GPa")

    logger.info(f"\n💡 The library includes steels, aluminum, plastics, and concrete")


def demo_lsdyna_cards():
    """Demo 2: LS-DYNA material card generation"""
    logger.info("\n" + "=" * 70)
    logger.info("DEMO 2: LS-DYNA Material Card Generation")
    logger.info("=" * 70)
    logger.info("\nGenerating LS-DYNA *MAT_ cards from materials")

    from koomesh.materials import MaterialLibrary
    from koomesh.materials.lsdyna_material import LSDynaMaterialGenerator

    # Load materials
    library = MaterialLibrary()
    library.load_default_materials()

    generator = LSDynaMaterialGenerator()

    # Generate different material types
    logger.info("\n1. Elastic material (Concrete)...")
    concrete = library.get_material("Concrete_30MPa")
    card = generator.generate_material_card(concrete, mat_id=1)

    logger.info(f"\n{card}\n")

    # Elastic-plastic material
    logger.info("\n2. Elastic-plastic material (Steel)...")
    steel = library.get_material("Steel_1045")
    card = generator.generate_material_card(steel, mat_id=2)

    logger.info(f"\n{card}\n")

    # Complete deck for multi-material model
    logger.info("\n3. Complete material deck for assembly...")
    materials = [
        library.get_material("Steel_1045"),          # Body structure
        library.get_material("Aluminum_6061_T6"),    # Panels
        library.get_material("ABS_Plastic"),         # Interior
    ]

    deck = generator.generate_complete_material_deck(materials, start_mat_id=1)

    output_file = Path("output/assembly_materials.k")
    output_file.parent.mkdir(exist_ok=True)
    with open(output_file, 'w') as f:
        f.write(deck)

    logger.info(f"   ✅ Material deck saved to {output_file}")
    logger.info(f"   Contains: Steel, Aluminum, ABS Plastic")

    logger.info(f"\n💡 These cards can be directly included in LS-DYNA models")


def demo_custom_materials():
    """Demo 3: Custom material creation"""
    logger.info("\n" + "=" * 70)
    logger.info("DEMO 3: Custom Material Definition")
    logger.info("=" * 70)
    logger.info("\nCreating custom materials for specific applications")

    from koomesh.materials import Material, MaterialLibrary, MaterialType, UnitSystem
    from koomesh.materials.lsdyna_material import LSDynaMaterialGenerator

    # Create custom crash-rated steel
    logger.info("\n1. Creating custom crash-rated steel...")
    crash_steel = Material(
        name="CrashSteel_1200MPa",
        material_type=MaterialType.ELASTIC_PLASTIC,
        density=7900.0,  # kg/m³
        elastic_modulus=210e9,  # Pa
        poisson_ratio=0.28,
        yield_stress=1200e6,  # Pa
        tangent_modulus=8e9,  # Pa
        failure_strain=0.08,
        unit_system=UnitSystem.SI,
        metadata={
            "description": "Ultra-high-strength steel for crash structures",
            "grade": "UHSS-1200",
            "application": "B-pillar, door beams",
            "manufacturer": "Custom",
        }
    )

    logger.info(f"   ✅ Created: {crash_steel.name}")
    logger.info(f"   Properties:")
    logger.info(f"   - Yield: {crash_steel.yield_stress/1e6:.0f} MPa")
    logger.info(f"   - Failure strain: {crash_steel.failure_strain:.2%}")
    logger.info(f"   - Application: {crash_steel.metadata['application']}")

    # Create custom foam (for airbag simulation)
    logger.info("\n2. Creating custom foam material...")
    foam = Material(
        name="Airbag_Foam",
        material_type=MaterialType.FOAM,
        density=50.0,  # kg/m³ - very light
        elastic_modulus=10e6,  # Pa - soft
        poisson_ratio=0.1,
        unit_system=UnitSystem.SI,
        metadata={
            "description": "Low-density foam for airbag model",
            "application": "Airbag deployment",
        }
    )

    logger.info(f"   ✅ Created: {foam.name}")
    logger.info(f"   - Density: {foam.density:.0f} kg/m³ (very light)")
    logger.info(f"   - E: {foam.elastic_modulus/1e6:.0f} MPa (very soft)")

    # Add to library and save
    logger.info("\n3. Creating custom material library...")
    custom_lib = MaterialLibrary()
    custom_lib.add_material(crash_steel)
    custom_lib.add_material(foam)

    output_json = Path("output/custom_materials_demo.json")
    custom_lib.save_to_file(output_json)

    logger.info(f"   ✅ Saved to {output_json}")

    # Generate LS-DYNA cards
    logger.info("\n4. Generating LS-DYNA cards...")
    generator = LSDynaMaterialGenerator()

    card = generator.generate_material_card(crash_steel, mat_id=100)
    logger.info(f"\n{card}\n")

    logger.info(f"💡 Custom materials allow precise control for specific simulations")


def demo_material_comparison():
    """Demo 4: Material comparison"""
    logger.info("\n" + "=" * 70)
    logger.info("DEMO 4: Material Comparison")
    logger.info("=" * 70)
    logger.info("\nComparing different materials for design decisions")

    from koomesh.materials import MaterialLibrary

    library = MaterialLibrary()
    library.load_default_materials()

    # Compare steels
    logger.info("\n1. Steel comparison:")
    logger.info(f"   {'Material':<25} {'Density':<12} {'E (GPa)':<10} {'Yield (MPa)':<12}")
    logger.info(f"   {'-'*60}")

    for name in ["Steel_Mild", "Steel_1045", "Steel_HighStrength"]:
        mat = library.get_material(name)
        logger.info(f"   {name:<25} {mat.density:<12.0f} {mat.elastic_modulus/1e9:<10.0f} {mat.yield_stress/1e6:<12.0f}")

    # Compare aluminum vs steel (weight savings)
    logger.info("\n2. Weight comparison (Steel vs Aluminum):")
    steel = library.get_material("Steel_1045")
    aluminum = library.get_material("Aluminum_6061_T6")

    weight_ratio = steel.density / aluminum.density
    strength_ratio = steel.yield_stress / aluminum.yield_stress

    logger.info(f"   Steel density: {steel.density:.0f} kg/m³")
    logger.info(f"   Aluminum density: {aluminum.density:.0f} kg/m³")
    logger.info(f"   Weight savings: {(1 - 1/weight_ratio)*100:.1f}% lighter")
    logger.info(f"   Strength ratio: {strength_ratio:.2f}x (steel is stronger)")

    # Specific strength (strength-to-weight ratio)
    logger.info("\n3. Specific strength (strength/density):")
    steel_specific = (steel.yield_stress / steel.density) / 1000
    aluminum_specific = (aluminum.yield_stress / aluminum.density) / 1000

    logger.info(f"   Steel: {steel_specific:.1f} kN·m/kg")
    logger.info(f"   Aluminum: {aluminum_specific:.1f} kN·m/kg")

    if aluminum_specific > steel_specific:
        logger.info(f"   ✅ Aluminum has {aluminum_specific/steel_specific:.2f}x better specific strength")
    else:
        logger.info(f"   ✅ Steel has {steel_specific/aluminum_specific:.2f}x better specific strength")

    logger.info(f"\n💡 Material selection depends on application requirements")


def main():
    """Run all material library demos"""
    logger.info("\n" + "=" * 70)
    logger.info("MATERIAL LIBRARY DEMONSTRATION")
    logger.info("=" * 70)
    logger.info("\nComprehensive material property management for FEA")

    try:
        # Demo 1: Basics
        demo_material_library_basics()

        # Demo 2: LS-DYNA cards
        demo_lsdyna_cards()

        # Demo 3: Custom materials
        demo_custom_materials()

        # Demo 4: Comparison
        demo_material_comparison()

        logger.info("\n" + "=" * 70)
        logger.info("✅ ALL DEMOS COMPLETED SUCCESSFULLY!")
        logger.info("=" * 70)
        logger.info("\nGenerated files:")
        logger.info("  - output/assembly_materials.k")
        logger.info("  - output/custom_materials_demo.json")

        logger.info("\n📚 Key Takeaways:")
        logger.info("  ✓ 10+ common materials included (steel, aluminum, plastic, concrete)")
        logger.info("  ✓ Easy material search and retrieval")
        logger.info("  ✓ Automatic LS-DYNA card generation")
        logger.info("  ✓ Custom material definition support")
        logger.info("  ✓ JSON-based persistence")
        logger.info("  ✓ Derived property calculations (G, K, lambda)")

        logger.info("\n💡 Next steps:")
        logger.info("  - Assign materials to mesh parts")
        logger.info("  - Generate complete LS-DYNA models")
        logger.info("  - Add temperature-dependent properties")
        logger.info("  - Create industry-specific material databases")

    except Exception as e:
        logger.error(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
