"""
Material Library Test
=====================

Test material property management and LS-DYNA card generation.
"""

import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_material_library_basic():
    """Test basic material library operations"""
    logger.info("=" * 70)
    logger.info(" " * 20 + "MATERIAL LIBRARY TEST")
    logger.info("=" * 70)

    # Test 1: Create library and load defaults
    logger.info("\n1. Creating material library...")
    from koomesh.materials import MaterialLibrary

    library = MaterialLibrary()
    library.load_default_materials()

    logger.info(f"   ✅ Loaded {len(library.list_materials())} materials")

    # Test 2: Get specific material
    logger.info("\n2. Testing material retrieval...")
    steel = library.get_material("Steel_1045")

    if steel:
        logger.info(f"   ✅ Retrieved: {steel.name}")
        logger.info(f"      - Type: {steel.material_type.value}")
        logger.info(f"      - Density: {steel.density:.0f} kg/m³")
        logger.info(f"      - E: {steel.elastic_modulus/1e9:.0f} GPa")
        logger.info(f"      - Yield: {steel.yield_stress/1e6:.0f} MPa")
    else:
        logger.error("   ❌ Failed to retrieve Steel_1045")
        return False

    # Test 3: Search materials
    logger.info("\n3. Testing material search...")
    steels = library.search_materials("steel")
    logger.info(f"   ✅ Found {len(steels)} steel materials:")
    for mat in steels:
        logger.info(f"      - {mat.name}")

    aluminum_materials = library.search_materials("aluminum")
    logger.info(f"   ✅ Found {len(aluminum_materials)} aluminum materials:")
    for mat in aluminum_materials:
        logger.info(f"      - {mat.name}")

    # Test 4: Calculate derived properties
    logger.info("\n4. Testing derived property calculations...")
    G = steel.get_shear_modulus()
    K = steel.get_bulk_modulus()
    lambda_param = steel.get_lame_lambda()

    logger.info(f"   ✅ Steel_1045 derived properties:")
    logger.info(f"      - Shear modulus (G): {G/1e9:.1f} GPa")
    logger.info(f"      - Bulk modulus (K): {K/1e9:.1f} GPa")
    logger.info(f"      - Lamé lambda: {lambda_param/1e9:.1f} GPa")

    # Test 5: Save and load library
    logger.info("\n5. Testing save/load...")
    output_path = Path("output/test_materials.json")
    output_path.parent.mkdir(exist_ok=True)

    library.save_to_file(output_path)
    logger.info(f"   ✅ Saved to {output_path}")

    # Load it back
    library2 = MaterialLibrary()
    library2.load_from_file(output_path)
    logger.info(f"   ✅ Loaded {len(library2.list_materials())} materials from file")

    # Verify
    steel2 = library2.get_material("Steel_1045")
    if steel2 and steel2.density == steel.density:
        logger.info(f"   ✅ Data integrity verified")
    else:
        logger.error(f"   ❌ Data integrity check failed")
        return False

    # Test 6: Library summary
    logger.info("\n6. Library summary:")
    summary = library.get_summary()
    for line in summary.split('\n'):
        logger.info(f"   {line}")

    return True


def test_lsdyna_material_cards():
    """Test LS-DYNA material card generation"""
    logger.info("\n" + "=" * 70)
    logger.info(" " * 15 + "LS-DYNA MATERIAL CARD TEST")
    logger.info("=" * 70)

    from koomesh.materials import MaterialLibrary
    from koomesh.materials.lsdyna_material import LSDynaMaterialGenerator

    # Create library
    logger.info("\n1. Loading materials...")
    library = MaterialLibrary()
    library.load_default_materials()

    # Create generator
    generator = LSDynaMaterialGenerator()

    # Test 2: Generate elastic material card
    logger.info("\n2. Generating elastic material card (Concrete)...")
    concrete = library.get_material("Concrete_30MPa")
    card = generator.generate_material_card(concrete, mat_id=1)

    logger.info(f"   ✅ Generated MAT_ELASTIC:")
    for line in card.split('\n'):
        logger.info(f"      {line}")

    # Test 3: Generate plastic material card
    logger.info("\n3. Generating plastic material card (Steel_1045)...")
    steel = library.get_material("Steel_1045")
    card = generator.generate_material_card(steel, mat_id=2)

    logger.info(f"   ✅ Generated MAT_PLASTIC_KINEMATIC:")
    for line in card.split('\n'):
        logger.info(f"      {line}")

    # Test 4: Generate rigid material card
    logger.info("\n4. Generating rigid material card...")
    rigid = library.get_material("Rigid")
    card = generator.generate_material_card(rigid, mat_id=3)

    logger.info(f"   ✅ Generated MAT_RIGID:")
    for line in card.split('\n'):
        logger.info(f"      {line}")

    # Test 5: Generate section and part cards
    logger.info("\n5. Generating section and part cards...")
    section = generator.generate_section_solid(1, 2, elem_formulation=10)
    part = generator.generate_part(1, 1, 2, "Steel_Component")

    logger.info(f"   ✅ Generated SECTION_SOLID:")
    for line in section.split('\n'):
        logger.info(f"      {line}")

    logger.info(f"   ✅ Generated PART:")
    for line in part.split('\n'):
        logger.info(f"      {line}")

    # Test 6: Generate complete material deck
    logger.info("\n6. Generating complete material deck...")
    materials = [
        library.get_material("Steel_1045"),
        library.get_material("Aluminum_6061_T6"),
        library.get_material("ABS_Plastic"),
    ]

    deck = generator.generate_complete_material_deck(materials)

    output_file = Path("output/material_deck.k")
    with open(output_file, 'w') as f:
        f.write(deck)

    logger.info(f"   ✅ Complete material deck written to {output_file}")
    logger.info(f"   Size: {output_file.stat().st_size} bytes")

    # Show preview
    lines = deck.split('\n')
    logger.info(f"\n   Preview (first 30 lines):")
    for line in lines[:30]:
        logger.info(f"      {line}")

    return True


def test_custom_material():
    """Test custom material creation"""
    logger.info("\n" + "=" * 70)
    logger.info(" " * 20 + "CUSTOM MATERIAL TEST")
    logger.info("=" * 70)

    from koomesh.materials import Material, MaterialLibrary, MaterialType, UnitSystem

    # Create custom material
    logger.info("\n1. Creating custom material...")
    custom_steel = Material(
        name="Custom_HighStrength_Steel",
        material_type=MaterialType.ELASTIC_PLASTIC,
        density=7900.0,
        elastic_modulus=210e9,
        poisson_ratio=0.28,
        yield_stress=900e6,
        tangent_modulus=5e9,
        failure_strain=0.10,
        unit_system=UnitSystem.SI,
        metadata={
            "description": "Custom high-strength steel for automotive",
            "grade": "Custom-HS900",
            "application": "Crash structures"
        }
    )

    logger.info(f"   ✅ Created: {custom_steel.name}")
    logger.info(f"      - Yield: {custom_steel.yield_stress/1e6:.0f} MPa")
    logger.info(f"      - Application: {custom_steel.metadata['application']}")

    # Add to library
    logger.info("\n2. Adding to library...")
    library = MaterialLibrary()
    library.add_material(custom_steel)

    logger.info(f"   ✅ Added to library")

    # Generate LS-DYNA card
    logger.info("\n3. Generating LS-DYNA card...")
    from koomesh.materials.lsdyna_material import LSDynaMaterialGenerator

    generator = LSDynaMaterialGenerator()
    card = generator.generate_material_card(custom_steel, mat_id=100)

    logger.info(f"   ✅ Generated card:")
    for line in card.split('\n'):
        logger.info(f"      {line}")

    # Save library with custom material
    output_path = Path("output/custom_materials.json")
    library.add_material(custom_steel)
    library.save_to_file(output_path)

    logger.info(f"\n4. Saved custom library to {output_path}")

    return True


if __name__ == "__main__":
    try:
        # Test 1: Basic library operations
        success1 = test_material_library_basic()

        # Test 2: LS-DYNA card generation
        success2 = test_lsdyna_material_cards()

        # Test 3: Custom materials
        success3 = test_custom_material()

        if success1 and success2 and success3:
            logger.info("\n" + "=" * 70)
            logger.info("✅ ALL MATERIAL LIBRARY TESTS PASSED!")
            logger.info("=" * 70)
            logger.info("\nGenerated files:")
            logger.info("  - output/test_materials.json")
            logger.info("  - output/material_deck.k")
            logger.info("  - output/custom_materials.json")
            sys.exit(0)
        else:
            sys.exit(1)

    except Exception as e:
        logger.error(f"\n❌ Material library test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
