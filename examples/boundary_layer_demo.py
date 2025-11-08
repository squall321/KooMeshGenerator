"""
Boundary Layer Mesh Demo
========================

This example demonstrates boundary layer mesh generation for CFD applications.
Boundary layers are crucial for accurate flow simulation near walls.

Features demonstrated:
- Boundary layer mesh creation with Distance + Threshold fields
- Automatic fine-to-coarse mesh transition
- Quality validation
- Surface-specific boundary layer application

Typical use cases:
- Aerodynamic simulations (airfoils, vehicles)
- Fluid flow analysis (pipes, channels)
- Heat transfer problems
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def demo_boundary_layer_all_surfaces():
    """Demo 1: Apply boundary layer to all surfaces"""
    logger.info("\n" + "=" * 70)
    logger.info("DEMO 1: Boundary Layer on All Surfaces")
    logger.info("=" * 70)

    import cadquery as cq
    from koomesh.io.step_reader import STEPReader
    from koomesh.meshing.tet_mesher import TetMesher
    from koomesh.meshing.quality_checker import QualityChecker

    # Create a simple pipe geometry
    logger.info("\n1. Creating pipe geometry...")
    outer_radius = 15.0
    inner_radius = 12.0
    height = 60.0

    outer = cq.Workplane('XY').circle(outer_radius).extrude(height)
    inner = cq.Workplane('XY').circle(inner_radius).extrude(height)
    pipe = outer.cut(inner)

    step_file = Path("output/bl_demo_pipe.step")
    step_file.parent.mkdir(exist_ok=True)
    pipe.val().exportStep(str(step_file))
    logger.info(f"   ✅ Created pipe: OD={outer_radius*2}, ID={inner_radius*2}, H={height}")

    # Read STEP file
    logger.info("\n2. Reading STEP file...")
    reader = STEPReader()
    shape = reader.read_file(str(step_file))
    info = reader.get_shape_info(shape)
    logger.info(f"   ✅ Volume: {info['volume']:.2f}, Surfaces: {info['num_faces']}")

    # Generate boundary layer mesh (all surfaces)
    logger.info("\n3. Generating boundary layer mesh...")
    logger.info("   Configuration:")
    logger.info("   - Layer thickness: 1.5 mm")
    logger.info("   - Number of layers: 5")
    logger.info("   - Base mesh size: 4.0 mm")
    logger.info("   - Applying to: ALL surfaces")

    mesher = TetMesher(mesh_size=4.0)
    mesh = mesher.mesh_with_boundary_layer(
        shape,
        layer_thickness=1.5,
        num_layers=5
    )

    logger.info(f"   ✅ Generated: {mesh.num_nodes()} nodes, {mesh.num_elements()} elements")

    # Check quality
    logger.info("\n4. Checking mesh quality...")
    checker = QualityChecker()
    report = checker.check_mesh(mesh)

    logger.info(f"   Jacobian: min={report.jacobian['min']:.4f}, max={report.jacobian['max']:.4f}")
    logger.info(f"   Aspect Ratio: min={report.aspect_ratio['min']:.2f}, max={report.aspect_ratio['max']:.2f}")
    logger.info(f"   ✅ Quality: {report.num_bad_elements} bad elements")

    # Export
    logger.info("\n5. Exporting to LS-DYNA...")
    from koomesh.export.lsdyna_writer import LSDynaWriter
    from koomesh.io.hierarchy_parser import HierarchyNode

    output_file = Path("output/bl_demo_pipe.k")
    root = HierarchyNode(name="Pipe_BL_Demo", level=0)

    with LSDynaWriter(str(output_file)) as writer:
        writer.write_complete_model([mesh], [], root)

    logger.info(f"   ✅ Exported: {output_file} ({output_file.stat().st_size} bytes)")


def demo_boundary_layer_selective():
    """Demo 2: Apply boundary layer to specific surfaces only"""
    logger.info("\n" + "=" * 70)
    logger.info("DEMO 2: Selective Boundary Layer Application")
    logger.info("=" * 70)
    logger.info("\n💡 This demonstrates how to apply boundary layer to specific surfaces")
    logger.info("   (e.g., only inner wall of pipe for internal flow simulation)")

    import cadquery as cq
    from koomesh.io.step_reader import STEPReader
    from koomesh.meshing.tet_mesher import TetMesher

    # Create geometry
    logger.info("\n1. Creating box with hole...")
    box = cq.Workplane('XY').box(40, 40, 20).faces(">Z").workplane().hole(15)

    step_file = Path("output/bl_demo_box.step")
    step_file.parent.mkdir(exist_ok=True)
    box.val().exportStep(str(step_file))
    logger.info(f"   ✅ Created box with hole")

    # Read STEP
    logger.info("\n2. Reading STEP file...")
    reader = STEPReader()
    shape = reader.read_file(str(step_file))
    logger.info(f"   ✅ STEP file loaded")

    # Mesh with boundary layer on all surfaces
    logger.info("\n3. Generating mesh with boundary layer...")
    logger.info("   Note: In practice, you would identify and specify surface tags")
    logger.info("   for selective application (e.g., only hole surface)")

    mesher = TetMesher(mesh_size=4.0)
    mesh = mesher.mesh_with_boundary_layer(
        shape,
        layer_thickness=1.0,
        num_layers=4,
        # surface_tags=[1, 2, 3]  # Example: apply to specific surfaces
    )

    logger.info(f"   ✅ Generated: {mesh.num_nodes()} nodes, {mesh.num_elements()} elements")

    # Export
    output_file = Path("output/bl_demo_box.k")
    from koomesh.export.lsdyna_writer import LSDynaWriter
    from koomesh.io.hierarchy_parser import HierarchyNode

    root = HierarchyNode(name="Box_BL_Demo", level=0)
    with LSDynaWriter(str(output_file)) as writer:
        writer.write_complete_model([mesh], [], root)

    logger.info(f"   ✅ Exported: {output_file}")


def main():
    """Run all boundary layer demos"""
    logger.info("\n" + "=" * 70)
    logger.info("BOUNDARY LAYER MESH GENERATION DEMO")
    logger.info("=" * 70)
    logger.info("\nThis demo shows how to create boundary layer meshes for CFD")
    logger.info("applications using the KooMeshGenerator.")

    try:
        # Demo 1: All surfaces
        demo_boundary_layer_all_surfaces()

        # Demo 2: Selective application
        demo_boundary_layer_selective()

        logger.info("\n" + "=" * 70)
        logger.info("✅ ALL DEMOS COMPLETED SUCCESSFULLY!")
        logger.info("=" * 70)
        logger.info("\nGenerated files:")
        logger.info("  - output/bl_demo_pipe.step")
        logger.info("  - output/bl_demo_pipe.k")
        logger.info("  - output/bl_demo_box.step")
        logger.info("  - output/bl_demo_box.k")

        logger.info("\n💡 Tips for using boundary layers:")
        logger.info("  1. Layer thickness should be ~1-5% of characteristic length")
        logger.info("  2. Use 3-10 layers depending on flow complexity")
        logger.info("  3. Growth ratio 1.1-1.3 is typical for most applications")
        logger.info("  4. Always check mesh quality after generation")

    except Exception as e:
        logger.error(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
