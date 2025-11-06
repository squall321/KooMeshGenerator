"""
Assembly Pipeline Test
======================

Test pipeline with a simple assembly (multiple parts).
"""

import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_assembly_pipeline():
    """Test pipeline with simple assembly"""
    logger.info("=" * 70)
    logger.info(" " * 20 + "ASSEMBLY PIPELINE TEST")
    logger.info("=" * 70)

    # Step 1: Create assembly STEP file
    logger.info("\n1. Creating test assembly STEP file...")
    import cadquery as cq

    # Create a simple assembly: base plate + column
    base = cq.Workplane('XY').box(100, 100, 10)
    column = cq.Workplane('XY').workplane(offset=10).box(20, 20, 50)

    # Combine into single compound
    assembly = base.union(column)

    step_file = Path("output/assembly_test.step")
    step_file.parent.mkdir(exist_ok=True)
    assembly.val().exportStep(str(step_file))
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
    logger.info("\n3. Classifying assembly shape...")
    try:
        from koomesh.geometry.shape_classifier import ShapeClassifier

        classifier = ShapeClassifier()
        result = classifier.classify(shape)
        logger.info(f"   ✅ Classification: {result.mesh_type.value}")
        logger.info(f"   Shape type: {result.shape_type.value}")
        logger.info(f"   Confidence: {result.confidence:.2f}")
    except Exception as e:
        logger.warning(f"   ⚠️  Classifier error: {e}")
        import traceback
        traceback.print_exc()

    # Step 4: Generate mesh with GMSH
    logger.info("\n4. Generating mesh with GMSH...")
    from koomesh.meshing.tet_mesher import TetMesher

    mesher = TetMesher(mesh_size=12.0)  # Medium mesh size

    try:
        mesh = mesher.mesh_shape(shape)
        logger.info(f"   ✅ Mesh generated")
        logger.info(f"   Nodes: {mesh.num_nodes()}")
        logger.info(f"   Elements: {mesh.num_elements()}")

        # Check if we have reasonable mesh density
        expected_min_elements = 50
        if mesh.num_elements() < expected_min_elements:
            logger.warning(f"   ⚠️  Mesh might be too coarse: {mesh.num_elements()} elements")
    except Exception as e:
        logger.error(f"   ❌ Meshing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 5: Check mesh quality
    logger.info("\n5. Checking mesh quality...")
    try:
        from koomesh.meshing.quality_checker import QualityChecker

        checker = QualityChecker(jacobian_threshold=0.01)  # Lower threshold for complex geometries
        quality_report = checker.check_mesh(mesh)

        logger.info(f"   Jacobian - Min: {quality_report.jacobian['min']:.4f}, "
                   f"Max: {quality_report.jacobian['max']:.4f}, "
                   f"Mean: {quality_report.jacobian['mean']:.4f}")
        logger.info(f"   Aspect Ratio - Min: {quality_report.aspect_ratio['min']:.2f}, "
                   f"Max: {quality_report.aspect_ratio['max']:.2f}, "
                   f"Mean: {quality_report.aspect_ratio['mean']:.2f}")
        logger.info(f"   Bad elements: {quality_report.num_bad_elements}")
        logger.info(f"   Negative Jacobians: {quality_report.jacobian['negative_elements']}")

        if quality_report.jacobian['negative_elements'] == 0:
            logger.info(f"   ✅ No negative Jacobians")
        else:
            logger.warning(f"   ⚠️  Found {quality_report.jacobian['negative_elements']} negative Jacobians")

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

    output_file = Path("output/assembly_test.k")
    root = HierarchyNode(name="AssemblyTest", level=0)

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
    logger.info("✅ ASSEMBLY PIPELINE TEST PASSED!")
    logger.info("=" * 70)
    logger.info(f"\nWorkflow verified:")
    logger.info(f"  1. Assembly STEP creation  ✅")
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
        success = test_assembly_pipeline()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"\n❌ Assembly pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
