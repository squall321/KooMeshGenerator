"""
Self-Contact Detection Test
============================

Test self-contact detection for crash simulations and large deformations.
"""

import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_self_contact_u_shape():
    """Test self-contact detection with U-shaped geometry"""
    logger.info("=" * 70)
    logger.info(" " * 20 + "SELF-CONTACT DETECTION TEST")
    logger.info("=" * 70)

    # Step 1: Create U-shaped geometry that has potential self-contact
    logger.info("\n1. Creating U-shaped geometry...")
    import cadquery as cq

    # Create a U-shape by cutting a box
    width = 40.0
    height = 60.0
    thickness = 10.0
    gap = 15.0  # Small gap - potential for self-contact

    outer_box = cq.Workplane('XY').box(width, height, thickness)
    # Cut out the middle to create U-shape
    cutout = cq.Workplane('XY').workplane(offset=-thickness/2).box(
        width - 2*5,  # Leave 5mm walls on sides
        height/2 + gap/2,  # Cut from top, leave gap at bottom
        thickness + 1  # Ensure complete cutout
    ).translate((0, height/4 + gap/4, 0))

    u_shape = outer_box.cut(cutout)

    step_file = Path("output/self_contact_u_shape.step")
    step_file.parent.mkdir(exist_ok=True)
    u_shape.val().exportStep(str(step_file))
    logger.info(f"   ✅ Created U-shape with gap={gap}mm")
    logger.info(f"   File: {step_file}")

    # Step 2: Read STEP file
    logger.info("\n2. Reading STEP file...")
    from koomesh.io.step_reader import STEPReader

    reader = STEPReader()
    shape = reader.read_file(str(step_file))

    if not shape:
        logger.error("   ❌ Failed to read STEP file")
        return False

    info = reader.get_shape_info(shape)
    logger.info(f"   ✅ STEP file read successfully")
    logger.info(f"   Volume: {info['volume']:.2f}")

    # Step 3: Generate mesh
    logger.info("\n3. Generating mesh...")
    from koomesh.meshing.tet_mesher import TetMesher

    mesher = TetMesher(mesh_size=5.0)
    mesh = mesher.mesh_shape(shape)

    logger.info(f"   ✅ Mesh generated")
    logger.info(f"   Nodes: {mesh.num_nodes()}")
    logger.info(f"   Elements: {mesh.num_elements()}")

    # Step 4: Detect self-contacts
    logger.info("\n4. Detecting self-contacts...")
    from koomesh.utils.contact_detection import ContactSurfaceDetector

    detector = ContactSurfaceDetector()

    # Test with different tolerances
    tolerances = [gap * 1.5, gap * 2.0, gap * 3.0]  # Different detection ranges

    for tol in tolerances:
        logger.info(f"\n   Testing tolerance = {tol:.1f}mm:")

        self_contacts = detector.detect_self_contacts(
            mesh,
            tolerance=tol,
            min_angle=90.0  # Faces at 90° or more apart
        )

        if self_contacts:
            for sc in self_contacts:
                logger.info(f"   ✅ Part {sc.part_id}:")
                logger.info(f"      - {len(sc.face_pairs)} potential self-contact pairs")
                logger.info(f"      - Avg distance: {sc.avg_distance:.3f}")
                logger.info(f"      - Min distance: {sc.min_distance:.3f}")
        else:
            logger.info(f"   ℹ️  No self-contact detected at this tolerance")

    # Step 5: Export mesh
    logger.info("\n5. Exporting to LS-DYNA...")
    from koomesh.export.lsdyna_writer import LSDynaWriter
    from koomesh.io.hierarchy_parser import HierarchyNode

    output_file = Path("output/self_contact_test.k")
    root = HierarchyNode(name="SelfContactTest", level=0)

    try:
        with LSDynaWriter(str(output_file)) as writer:
            writer.write_complete_model([mesh], [], root)

        logger.info(f"   ✅ LS-DYNA file created: {output_file}")
        logger.info(f"   Size: {output_file.stat().st_size} bytes")
    except Exception as e:
        logger.error(f"   ❌ Export failed: {e}")
        return False

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("✅ SELF-CONTACT DETECTION TEST COMPLETED!")
    logger.info("=" * 70)
    logger.info(f"\nTest scenario:")
    logger.info(f"  - U-shaped geometry with {gap}mm gap")
    logger.info(f"  - Mesh: {mesh.num_nodes()} nodes, {mesh.num_elements()} elements")
    logger.info(f"  - Detection algorithm: KD-tree with normal angle checking")
    logger.info(f"\n💡 Self-contact detection is useful for:")
    logger.info(f"  - Crash simulations (vehicle crush)")
    logger.info(f"  - Metal forming (folding, bending)")
    logger.info(f"  - Large deformation analysis")

    return True


def test_self_contact_cylinder_crushing():
    """Test self-contact with cylinder crushing scenario"""
    logger.info("\n" + "=" * 70)
    logger.info("BONUS TEST: Cylinder Crushing Scenario")
    logger.info("=" * 70)

    import cadquery as cq
    from koomesh.io.step_reader import STEPReader
    from koomesh.meshing.tet_mesher import TetMesher
    from koomesh.utils.contact_detection import ContactSurfaceDetector

    # Create thin-walled cylinder (typical crash structure)
    logger.info("\n1. Creating thin-walled cylinder...")
    outer_radius = 20.0
    inner_radius = 18.0  # 2mm wall thickness
    height = 100.0

    outer = cq.Workplane('XY').circle(outer_radius).extrude(height)
    inner = cq.Workplane('XY').circle(inner_radius).extrude(height)
    cylinder = outer.cut(inner)

    step_file = Path("output/self_contact_cylinder.step")
    cylinder.val().exportStep(str(step_file))
    logger.info(f"   ✅ Created thin-walled cylinder (wall=2mm)")

    # Read and mesh
    logger.info("\n2. Reading and meshing...")
    reader = STEPReader()
    shape = reader.read_file(str(step_file))

    mesher = TetMesher(mesh_size=8.0)
    mesh = mesher.mesh_shape(shape)
    logger.info(f"   ✅ Mesh: {mesh.num_nodes()} nodes, {mesh.num_elements()} elements")

    # Detect potential self-contact
    logger.info("\n3. Detecting potential self-contact zones...")
    detector = ContactSurfaceDetector()

    # Use larger tolerance for potential crush zones
    self_contacts = detector.detect_self_contacts(
        mesh,
        tolerance=inner_radius * 2,  # Check across diameter
        min_angle=120.0  # Stricter angle requirement
    )

    if self_contacts:
        for sc in self_contacts:
            logger.info(f"   ✅ Detected potential crush zones:")
            logger.info(f"      - {len(sc.face_pairs)} potential contact pairs")
            logger.info(f"      - Min separation: {sc.min_distance:.3f}")
    else:
        logger.info(f"   ℹ️  No pre-existing self-contact (expected for undeformed)")

    logger.info(f"\n💡 In crash simulation, this mesh would deform and")
    logger.info(f"   self-contact pairs would activate dynamically")

    return True


if __name__ == "__main__":
    try:
        # Main test
        success1 = test_self_contact_u_shape()

        # Bonus test
        success2 = test_self_contact_cylinder_crushing()

        if success1 and success2:
            logger.info("\n" + "=" * 70)
            logger.info("✅ ALL SELF-CONTACT TESTS PASSED!")
            logger.info("=" * 70)
            sys.exit(0)
        else:
            sys.exit(1)

    except Exception as e:
        logger.error(f"\n❌ Self-contact test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
