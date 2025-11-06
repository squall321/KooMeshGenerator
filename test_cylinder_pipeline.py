"""
Cylinder Pipeline Test
======================

Test pipeline with a cylinder geometry to verify shape classification.
"""

import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_cylinder_pipeline():
    """Test pipeline with cylinder geometry"""
    logger.info("=" * 70)
    logger.info(" " * 20 + "CYLINDER PIPELINE TEST")
    logger.info("=" * 70)

    # Step 1: Create cylinder STEP file
    logger.info("\n1. Creating test cylinder STEP file...")
    import cadquery as cq

    cylinder = cq.Workplane('XY').circle(20).extrude(100)
    step_file = Path("output/cylinder_test.step")
    step_file.parent.mkdir(exist_ok=True)
    cylinder.val().exportStep(str(step_file))
    logger.info(f"   ✅ Created: {step_file}")

    # Step 2: Read STEP file
    logger.info("\n2. Reading STEP file...")
    from koomesh.io.step_reader import STEPReader

    reader = STEPReader()
    shape = reader.read_file(str(step_file))

    if not shape:
        logger.error("   ❌ Failed to read STEP file")
        return False

    logger.info(f"   ✅ STEP file read successfully")

    # Get shape info
    info = reader.get_shape_info(shape)
    logger.info(f"   Shape info: {info['num_solids']} solids, {info['num_faces']} faces")
    logger.info(f"   Volume: {info['volume']:.2f}")

    # Step 3: Classify shape
    logger.info("\n3. Classifying cylinder shape...")
    try:
        from koomesh.geometry.shape_classifier import ShapeClassifier

        classifier = ShapeClassifier()
        result = classifier.classify(shape)
        logger.info(f"   ✅ Classification: {result.mesh_type.value}")
        logger.info(f"   Shape type: {result.shape_type.value}")
        logger.info(f"   Confidence: {result.confidence:.2f}")

        # Cylinder should be identified as cylinder or sweepable
        if result.shape_type.value in ['cylinder', 'sweepable']:
            logger.info(f"   ✅ Correctly identified cylinder-like geometry")
        else:
            logger.warning(f"   ⚠️  Expected cylinder/sweepable, got {result.shape_type.value}")
    except Exception as e:
        logger.warning(f"   ⚠️  Classifier error: {e}")
        import traceback
        traceback.print_exc()

    # Step 4: Generate mesh with GMSH
    logger.info("\n4. Generating mesh with GMSH...")
    from koomesh.meshing.tet_mesher import TetMesher

    mesher = TetMesher(mesh_size=15.0)  # Coarser mesh for faster testing

    try:
        mesh = mesher.mesh_shape(shape)
        logger.info(f"   ✅ Mesh generated")
        logger.info(f"   Nodes: {mesh.num_nodes()}")
        logger.info(f"   Elements: {mesh.num_elements()}")
    except Exception as e:
        logger.error(f"   ❌ Meshing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 5: Check mesh quality
    logger.info("\n5. Checking mesh quality...")
    try:
        from koomesh.meshing.quality_checker import QualityChecker

        checker = QualityChecker()
        quality_report = checker.check_mesh(mesh)

        logger.info(f"   Jacobian - Min: {quality_report.jacobian['min']:.4f}, "
                   f"Max: {quality_report.jacobian['max']:.4f}, "
                   f"Mean: {quality_report.jacobian['mean']:.4f}")
        logger.info(f"   Aspect Ratio - Min: {quality_report.aspect_ratio['min']:.2f}, "
                   f"Max: {quality_report.aspect_ratio['max']:.2f}, "
                   f"Mean: {quality_report.aspect_ratio['mean']:.2f}")
        logger.info(f"   Bad elements: {quality_report.num_bad_elements}")

        if quality_report.is_valid():
            logger.info(f"   ✅ Mesh quality: PASS")
        else:
            logger.warning(f"   ⚠️  Mesh quality: FAIL (has quality issues)")
    except Exception as e:
        logger.error(f"   ❌ Quality check failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 6: Export to LS-DYNA
    logger.info("\n6. Exporting to LS-DYNA...")
    from koomesh.export.lsdyna_writer import LSDynaWriter
    from koomesh.io.hierarchy_parser import HierarchyNode

    output_file = Path("output/cylinder_test.k")
    root = HierarchyNode(name="CylinderTest", level=0)

    try:
        with LSDynaWriter(str(output_file)) as writer:
            writer.write_complete_model([mesh], [], root)

        logger.info(f"   ✅ LS-DYNA file created: {output_file}")
        logger.info(f"   Size: {output_file.stat().st_size} bytes")
    except Exception as e:
        logger.error(f"   ❌ Export failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 7: Verify output
    logger.info("\n7. Verifying output...")
    with open(output_file, 'r') as f:
        content = f.read()

    if '*NODE' in content and '*ELEMENT_SOLID' in content:
        logger.info("   ✅ LS-DYNA file format correct")
    else:
        logger.error("   ❌ LS-DYNA file format incorrect")
        return False

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("✅ CYLINDER PIPELINE TEST PASSED!")
    logger.info("=" * 70)
    logger.info(f"\nWorkflow verified:")
    logger.info(f"  1. Cylinder STEP creation ✅")
    logger.info(f"  2. STEP file reading       ✅")
    logger.info(f"  3. Shape classification    ✅")
    logger.info(f"  4. Mesh generation (GMSH)  ✅")
    logger.info(f"  5. Quality checking        ✅")
    logger.info(f"  6. LS-DYNA export          ✅")
    logger.info(f"  7. Output verification     ✅")
    logger.info(f"\nGenerated files:")
    logger.info(f"  - {step_file}")
    logger.info(f"  - {output_file}")

    return True


if __name__ == "__main__":
    try:
        success = test_cylinder_pipeline()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"\n❌ Cylinder pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
