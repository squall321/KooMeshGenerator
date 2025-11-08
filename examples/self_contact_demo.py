"""
Self-Contact Detection Demo
============================

This example demonstrates self-contact detection for crash simulations
and large deformation analysis.

Self-contact occurs when different regions of the same part come into
close proximity during deformation (e.g., folding, crushing, bending).

Features demonstrated:
- Self-contact detection with KD-tree spatial indexing
- Normal angle checking for accurate detection
- Tolerance-based proximity search
- Application to crash and forming scenarios

Typical use cases:
- Vehicle crash simulations (body panel crushing)
- Metal forming (sheet bending, folding)
- Airbag deployment
- Soft tissue deformation
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def demo_crash_scenario():
    """Demo 1: Vehicle crash scenario - thin-walled structure"""
    logger.info("\n" + "=" * 70)
    logger.info("DEMO 1: Crash Scenario - Thin-Walled Structure")
    logger.info("=" * 70)
    logger.info("\nThis simulates a crash absorber that can crush and self-contact")

    import cadquery as cq
    from koomesh.io.step_reader import STEPReader
    from koomesh.meshing.tet_mesher import TetMesher
    from koomesh.utils.contact_detection import ContactSurfaceDetector

    # Create thin-walled tube (typical crash structure)
    logger.info("\n1. Creating crash absorber geometry...")
    outer_radius = 25.0
    inner_radius = 22.0  # 3mm wall thickness
    height = 120.0

    outer = cq.Workplane('XY').circle(outer_radius).extrude(height)
    inner = cq.Workplane('XY').circle(inner_radius).extrude(height)
    tube = outer.cut(inner)

    step_file = Path("output/crash_absorber.step")
    step_file.parent.mkdir(exist_ok=True)
    tube.val().exportStep(str(step_file))

    logger.info(f"   ✅ Crash absorber:")
    logger.info(f"      - Outer diameter: {outer_radius*2}mm")
    logger.info(f"      - Wall thickness: {outer_radius - inner_radius}mm")
    logger.info(f"      - Height: {height}mm")

    # Read and mesh
    logger.info("\n2. Reading STEP and generating mesh...")
    reader = STEPReader()
    shape = reader.read_file(str(step_file))

    mesher = TetMesher(mesh_size=10.0)
    mesh = mesher.mesh_shape(shape)

    logger.info(f"   ✅ Mesh generated:")
    logger.info(f"      - Nodes: {mesh.num_nodes()}")
    logger.info(f"      - Elements: {mesh.num_elements()}")

    # Detect self-contact potential
    logger.info("\n3. Detecting self-contact potential...")
    logger.info("   (Areas where tube walls could contact during crush)")

    detector = ContactSurfaceDetector()

    # Use diameter as tolerance to find opposite walls
    tolerance = inner_radius * 2  # Check across inner diameter

    self_contacts = detector.detect_self_contacts(
        mesh,
        tolerance=tolerance,
        min_angle=120.0  # Walls facing each other
    )

    if self_contacts:
        for sc in self_contacts:
            logger.info(f"\n   ✅ Self-contact zones detected:")
            logger.info(f"      - Part ID: {sc.part_id}")
            logger.info(f"      - Contact pairs: {len(sc.face_pairs)}")
            logger.info(f"      - Min separation: {sc.min_distance:.2f}mm")
            logger.info(f"      - Avg separation: {sc.avg_distance:.2f}mm")
    else:
        logger.info("   ℹ️  No immediate self-contact (expected before deformation)")

    # Export
    logger.info("\n4. Exporting for LS-DYNA...")
    from koomesh.export.lsdyna_writer import LSDynaWriter
    from koomesh.io.hierarchy_parser import HierarchyNode

    output_file = Path("output/crash_absorber.k")
    root = HierarchyNode(name="CrashAbsorber", level=0)

    with LSDynaWriter(str(output_file)) as writer:
        writer.write_complete_model([mesh], [], root)

    logger.info(f"   ✅ Exported: {output_file}")
    logger.info(f"\n💡 In LS-DYNA, add *CONTACT_AUTOMATIC_SINGLE_SURFACE")
    logger.info(f"   to handle self-contact during crush")


def demo_forming_scenario():
    """Demo 2: Metal forming scenario - sheet bending"""
    logger.info("\n" + "=" * 70)
    logger.info("DEMO 2: Metal Forming - Sheet Bending")
    logger.info("=" * 70)
    logger.info("\nThis simulates sheet metal that could fold and self-contact")

    import cadquery as cq
    from koomesh.io.step_reader import STEPReader
    from koomesh.meshing.tet_mesher import TetMesher
    from koomesh.utils.contact_detection import ContactSurfaceDetector

    # Create thin plate that could be bent
    logger.info("\n1. Creating sheet metal geometry...")
    length = 100.0
    width = 50.0
    thickness = 3.0

    sheet = cq.Workplane('XY').box(length, width, thickness)

    step_file = Path("output/sheet_metal.step")
    step_file.parent.mkdir(exist_ok=True)
    sheet.val().exportStep(str(step_file))

    logger.info(f"   ✅ Sheet metal:")
    logger.info(f"      - Dimensions: {length}x{width}x{thickness}mm")

    # Read and mesh
    logger.info("\n2. Meshing...")
    reader = STEPReader()
    shape = reader.read_file(str(step_file))

    mesher = TetMesher(mesh_size=8.0)
    mesh = mesher.mesh_shape(shape)

    logger.info(f"   ✅ Mesh: {mesh.num_nodes()} nodes, {mesh.num_elements()} elements")

    # Check self-contact potential
    logger.info("\n3. Analyzing self-contact potential...")
    logger.info("   (If sheet folds, top and bottom surfaces would contact)")

    detector = ContactSurfaceDetector()

    # Small tolerance - sheet needs to fold significantly
    tolerance = thickness * 3  # Within a few thicknesses

    self_contacts = detector.detect_self_contacts(
        mesh,
        tolerance=tolerance,
        min_angle=90.0  # Top/bottom faces are opposite
    )

    if self_contacts:
        for sc in self_contacts:
            logger.info(f"   ✅ Potential fold zones: {len(sc.face_pairs)} pairs")
    else:
        logger.info("   ℹ️  No self-contact in flat state (expected)")

    # Export
    output_file = Path("output/sheet_metal.k")
    from koomesh.export.lsdyna_writer import LSDynaWriter
    from koomesh.io.hierarchy_parser import HierarchyNode

    root = HierarchyNode(name="SheetMetal", level=0)
    with LSDynaWriter(str(output_file)) as writer:
        writer.write_complete_model([mesh], [], root)

    logger.info(f"\n   ✅ Exported: {output_file}")
    logger.info(f"\n💡 For forming simulation:")
    logger.info(f"   - Use *CONTACT_AUTOMATIC_SINGLE_SURFACE")
    logger.info(f"   - Enable thickness offset for shells")
    logger.info(f"   - Consider friction coefficient (~0.15 for steel)")


def demo_comparison():
    """Demo 3: Compare multi-part vs self-contact"""
    logger.info("\n" + "=" * 70)
    logger.info("DEMO 3: Multi-Part Contact vs Self-Contact")
    logger.info("=" * 70)
    logger.info("\nShowing the difference between the two contact types")

    logger.info("\n📌 Multi-Part Contact:")
    logger.info("   - Between DIFFERENT parts")
    logger.info("   - Example: Bolt in hole, tire on road")
    logger.info("   - Detection: Compare surface faces from part A vs part B")
    logger.info("   - LS-DYNA: *CONTACT_AUTOMATIC_SURFACE_TO_SURFACE")

    logger.info("\n📌 Self-Contact:")
    logger.info("   - Within SAME part")
    logger.info("   - Example: Crushed tube, folded sheet, bent bar")
    logger.info("   - Detection: Compare surface faces within same part")
    logger.info("   - Requirement: Faces must have opposing normals")
    logger.info("   - LS-DYNA: *CONTACT_AUTOMATIC_SINGLE_SURFACE")

    logger.info("\n💡 Best Practices:")
    logger.info("   1. Self-contact tolerance ~ 1-3x element size")
    logger.info("   2. Min angle >= 90° filters parallel faces")
    logger.info("   3. Min angle >= 120° is stricter (more opposing)")
    logger.info("   4. Use KD-tree for performance (O(n log n))")
    logger.info("   5. Check mesh quality before contact detection")


def main():
    """Run all self-contact demos"""
    logger.info("\n" + "=" * 70)
    logger.info("SELF-CONTACT DETECTION DEMONSTRATION")
    logger.info("=" * 70)
    logger.info("\nDemonstrating self-contact detection for crash and forming")

    try:
        # Demo 1: Crash scenario
        demo_crash_scenario()

        # Demo 2: Forming scenario
        demo_forming_scenario()

        # Demo 3: Comparison
        demo_comparison()

        logger.info("\n" + "=" * 70)
        logger.info("✅ ALL DEMOS COMPLETED SUCCESSFULLY!")
        logger.info("=" * 70)
        logger.info("\nGenerated files:")
        logger.info("  - output/crash_absorber.step")
        logger.info("  - output/crash_absorber.k")
        logger.info("  - output/sheet_metal.step")
        logger.info("  - output/sheet_metal.k")

        logger.info("\n📚 Key Takeaways:")
        logger.info("  ✓ Self-contact = same part, different regions")
        logger.info("  ✓ Normal angle checking ensures faces are opposing")
        logger.info("  ✓ KD-tree provides efficient spatial search")
        logger.info("  ✓ Essential for crash and forming simulations")

    except Exception as e:
        logger.error(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
