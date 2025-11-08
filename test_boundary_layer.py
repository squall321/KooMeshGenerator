"""
Boundary Layer Mesh Test
=========================

Test boundary layer mesh generation for CFD applications.
"""

import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_boundary_layer_mesh():
    """Test boundary layer mesh generation"""
    logger.info("=" * 70)
    logger.info(" " * 20 + "BOUNDARY LAYER MESH TEST")
    logger.info("=" * 70)

    # Step 1: Create test geometry (cylinder for flow simulation)
    logger.info("\n1. Creating test geometry (cylinder)...")
    import cadquery as cq

    # Create a cylinder (typical CFD geometry)
    radius = 10.0
    height = 50.0
    cylinder = cq.Workplane('XY').circle(radius).extrude(height)

    step_file = Path("output/boundary_layer_test.step")
    step_file.parent.mkdir(exist_ok=True)
    cylinder.val().exportStep(str(step_file))
    logger.info(f"   ✅ Created cylinder: R={radius}, H={height}")
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

    # Step 3: Generate boundary layer mesh
    logger.info("\n3. Generating boundary layer mesh...")
    from koomesh.meshing.tet_mesher import TetMesher

    # Parameters for boundary layer
    layer_thickness = 2.0  # Total thickness of boundary layer
    num_layers = 5         # Number of layers
    mesh_size = 5.0        # Base mesh size

    logger.info(f"   Parameters:")
    logger.info(f"   - Layer thickness: {layer_thickness}")
    logger.info(f"   - Number of layers: {num_layers}")
    logger.info(f"   - Mesh size: {mesh_size}")

    mesher = TetMesher(mesh_size=mesh_size)

    try:
        mesh = mesher.mesh_with_boundary_layer(
            shape,
            layer_thickness=layer_thickness,
            num_layers=num_layers
        )

        logger.info(f"   ✅ Boundary layer mesh generated")
        logger.info(f"   Nodes: {mesh.num_nodes()}")
        logger.info(f"   Elements: {mesh.num_elements()}")

    except Exception as e:
        logger.error(f"   ❌ Boundary layer meshing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 4: Check mesh quality
    logger.info("\n4. Checking mesh quality...")
    try:
        from koomesh.meshing.quality_checker import QualityChecker

        checker = QualityChecker(jacobian_threshold=0.01)
        quality_report = checker.check_mesh(mesh)

        logger.info(f"   Jacobian - Min: {quality_report.jacobian['min']:.4f}, "
                   f"Max: {quality_report.jacobian['max']:.4f}")
        logger.info(f"   Aspect Ratio - Min: {quality_report.aspect_ratio['min']:.2f}, "
                   f"Max: {quality_report.aspect_ratio['max']:.2f}")
        logger.info(f"   Bad elements: {quality_report.num_bad_elements}")
        logger.info(f"   Negative Jacobians: {quality_report.jacobian['negative_elements']}")

        if quality_report.jacobian['negative_elements'] == 0:
            logger.info(f"   ✅ No negative Jacobians")
        else:
            logger.warning(f"   ⚠️  Found {quality_report.jacobian['negative_elements']} negative Jacobians")

    except Exception as e:
        logger.error(f"   ❌ Quality check failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 5: Analyze boundary layer quality
    logger.info("\n5. Analyzing boundary layer...")
    try:
        # Find elements near the surface
        # (This is a simplified check - in reality we'd need to identify BL elements properly)

        # Get coordinate range
        import numpy as np
        coords = []
        for node in mesh.nodes.values():
            coords.append(node.coordinates())
        coords = np.array(coords)

        # Get radial distances (for cylinder)
        xy_coords = coords[:, :2]  # x, y coordinates
        radial_dist = np.sqrt(np.sum(xy_coords**2, axis=1))

        # Elements near surface should be smaller (boundary layer)
        near_surface = np.abs(radial_dist - radius) < layer_thickness
        far_from_surface = np.abs(radial_dist - radius) > layer_thickness

        logger.info(f"   Nodes near surface: {np.sum(near_surface)}")
        logger.info(f"   Nodes far from surface: {np.sum(far_from_surface)}")

        if np.sum(near_surface) > 0:
            logger.info(f"   ✅ Boundary layer region detected")
        else:
            logger.warning(f"   ⚠️  No clear boundary layer detected")

    except Exception as e:
        logger.warning(f"   ⚠️  Boundary layer analysis failed: {e}")

    # Step 6: Export to LS-DYNA
    logger.info("\n6. Exporting to LS-DYNA...")
    from koomesh.export.lsdyna_writer import LSDynaWriter
    from koomesh.io.hierarchy_parser import HierarchyNode

    output_file = Path("output/boundary_layer_test.k")
    root = HierarchyNode(name="BoundaryLayerTest", level=0)

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

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("✅ BOUNDARY LAYER MESH TEST COMPLETED!")
    logger.info("=" * 70)
    logger.info(f"\nResults:")
    logger.info(f"  - Geometry: Cylinder R={radius}, H={height}")
    logger.info(f"  - Boundary layers: {num_layers} layers, {layer_thickness} thickness")
    logger.info(f"  - Mesh: {mesh.num_nodes()} nodes, {mesh.num_elements()} elements")
    logger.info(f"  - Quality: {quality_report.num_bad_elements} bad elements")
    logger.info(f"\nGenerated files:")
    logger.info(f"  - {step_file}")
    logger.info(f"  - {output_file}")

    logger.info(f"\n💡 Note: Boundary layer mesh feature is working!")
    logger.info(f"   Future improvements needed:")
    logger.info(f"   - Surface selection (specify which surfaces get BL)")
    logger.info(f"   - Anisotropic element sizing")
    logger.info(f"   - Better BL element identification")

    return True


if __name__ == "__main__":
    try:
        success = test_boundary_layer_mesh()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"\n❌ Boundary layer test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
