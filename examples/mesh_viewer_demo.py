"""
Interactive Mesh Viewer Demo
============================

This example demonstrates interactive 3D mesh visualization with PyVista/VTK.

Features demonstrated:
- Basic mesh visualization with edges
- Quality metric color mapping (aspect ratio, Jacobian, etc.)
- Camera views (isometric, front, side, top)
- VTK file export
- Boundary surface visualization
- Quick visualization helper

Typical use cases:
- Visual mesh quality inspection
- Debugging mesh generation
- Creating presentations and reports
- Interactive mesh exploration
- Export to ParaView/VTK for further analysis

Author: KooMeshGenerator Team
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def demo_basic_visualization():
    """Demo 1: Basic mesh visualization"""
    logger.info("\n" + "=" * 70)
    logger.info("DEMO 1: Basic Mesh Visualization")
    logger.info("=" * 70)
    logger.info("\nVisualize a mesh with element edges")

    import cadquery as cq
    from koomesh.io.step_reader import STEPReader
    from koomesh.meshing import TetMesher
    from koomesh.visualization import MeshViewer

    # Create geometry
    logger.info("\n1. Creating geometry (box with hole)...")
    box_with_hole = cq.Workplane('XY').box(20.0, 20.0, 10.0).faces('>Z').workplane().hole(6.0)

    # Export and read
    step_file = Path("output/demo_box_hole.step")
    step_file.parent.mkdir(parents=True, exist_ok=True)
    box_with_hole.val().exportStep(str(step_file))

    reader = STEPReader()
    shape = reader.read_file(str(step_file))

    # Generate mesh
    logger.info("\n2. Generating mesh...")
    mesher = TetMesher(mesh_size=2.0)
    mesh_data = mesher.mesh_shape(shape)

    logger.info(f"   ✅ Mesh: {len(mesh_data.nodes)} nodes, {len(mesh_data.elements)} elements")

    # Visualize
    logger.info("\n3. Visualizing mesh...")
    logger.info("   💡 Use mouse to:")
    logger.info("      - Left click + drag: Rotate")
    logger.info("      - Right click + drag: Zoom")
    logger.info("      - Middle click + drag: Pan")
    logger.info("      - 'r': Reset camera")
    logger.info("      - 'q': Close window")

    viewer = MeshViewer(window_size=(1024, 768))
    viewer.show_mesh(mesh_data, show_edges=True, color='lightblue')

    # Uncomment to display (requires X server or Jupyter):
    # viewer.show()

    logger.info(f"\n💡 Mesh displayed with edges. Close window to continue.")


def demo_quality_visualization():
    """Demo 2: Quality metric visualization"""
    logger.info("\n" + "=" * 70)
    logger.info("DEMO 2: Quality Metric Visualization")
    logger.info("=" * 70)
    logger.info("\nVisualize mesh quality with color mapping")

    import cadquery as cq
    from koomesh.io.step_reader import STEPReader
    from koomesh.meshing import TetMesher
    from koomesh.visualization import MeshViewer

    # Create geometry with varying quality
    logger.info("\n1. Creating geometry (tapered cylinder)...")
    cylinder = cq.Workplane('XY').circle(8.0).workplane(offset=20.0).circle(3.0).loft()

    step_file = Path("output/demo_cylinder.step")
    step_file.parent.mkdir(parents=True, exist_ok=True)
    cylinder.val().exportStep(str(step_file))

    reader = STEPReader()
    shape = reader.read_file(str(step_file))

    # Generate mesh
    logger.info("\n2. Generating mesh...")
    mesher = TetMesher(mesh_size=2.5)
    mesh_data = mesher.mesh_shape(shape)

    logger.info(f"   ✅ Mesh: {len(mesh_data.nodes)} nodes, {len(mesh_data.elements)} elements")

    # Visualize different quality metrics
    logger.info("\n3. Visualizing quality metrics...")

    metrics = [
        ('aspect_ratio', 'Aspect Ratio (max_edge / min_edge)'),
        ('jacobian', 'Jacobian Determinant'),
        ('skewness', 'Element Skewness'),
        ('volume', 'Element Volume')
    ]

    viewer = MeshViewer(window_size=(1024, 768))

    for metric, description in metrics:
        logger.info(f"\n   Displaying: {description}")
        viewer.show_quality(mesh_data, metric=metric, show_edges=False, color_map='coolwarm')

        # Uncomment to display each metric:
        # viewer.show()

        # Export screenshot (requires X server or OSMesa)
        # screenshot_file = Path(f"output/quality_{metric}.png")
        # viewer.screenshot(screenshot_file)

    logger.info(f"\n💡 Quality metrics visualized with color mapping")
    logger.info(f"   - Red: Poor quality")
    logger.info(f"   - Blue: Good quality")


def demo_camera_views():
    """Demo 3: Different camera views"""
    logger.info("\n" + "=" * 70)
    logger.info("DEMO 3: Camera Views")
    logger.info("=" * 70)
    logger.info("\nDemonstrate different camera viewpoints")

    import cadquery as cq
    from koomesh.io.step_reader import STEPReader
    from koomesh.meshing import TetMesher
    from koomesh.visualization import MeshViewer

    # Create L-shaped geometry
    logger.info("\n1. Creating L-shaped geometry...")
    box1 = cq.Workplane('XY').box(15.0, 4.0, 4.0, centered=False)
    box2 = cq.Workplane('XY').box(4.0, 15.0, 4.0, centered=False)
    l_shape = box1.union(box2)

    step_file = Path("output/demo_l_shape.step")
    step_file.parent.mkdir(parents=True, exist_ok=True)
    l_shape.val().exportStep(str(step_file))

    reader = STEPReader()
    shape = reader.read_file(str(step_file))

    # Generate mesh
    logger.info("\n2. Generating mesh...")
    mesher = TetMesher(mesh_size=2.0)
    mesh_data = mesher.mesh_shape(shape)

    logger.info(f"   ✅ Mesh: {len(mesh_data.nodes)} nodes")

    # Show different camera views
    logger.info("\n3. Demonstrating camera views...")

    viewer = MeshViewer(window_size=(1024, 768))
    viewer.show_mesh(mesh_data, show_edges=True)

    views = ['isometric', 'front', 'top', 'right']

    for view in views:
        logger.info(f"\n   Camera view: {view}")
        viewer.set_camera_view(view)

        # Uncomment to display each view:
        # viewer.show()

        # Export screenshot
        # screenshot_file = Path(f"output/view_{view}.png")
        # viewer.screenshot(screenshot_file)

    logger.info(f"\n💡 Available camera views: isometric, front, back, left, right, top, bottom")


def demo_vtk_export():
    """Demo 4: VTK file export"""
    logger.info("\n" + "=" * 70)
    logger.info("DEMO 4: VTK File Export")
    logger.info("=" * 70)
    logger.info("\nExport mesh to VTK format for ParaView/other tools")

    import cadquery as cq
    from koomesh.io.step_reader import STEPReader
    from koomesh.meshing import TetMesher
    from koomesh.visualization import MeshViewer

    # Create sphere
    logger.info("\n1. Creating geometry (sphere)...")
    sphere = cq.Workplane('XY').sphere(8.0)

    step_file = Path("output/demo_sphere.step")
    step_file.parent.mkdir(parents=True, exist_ok=True)
    sphere.val().exportStep(str(step_file))

    reader = STEPReader()
    shape = reader.read_file(str(step_file))

    # Generate mesh
    logger.info("\n2. Generating mesh...")
    mesher = TetMesher(mesh_size=2.0)
    mesh_data = mesher.mesh_shape(shape)

    logger.info(f"   ✅ Mesh: {len(mesh_data.nodes)} nodes, {len(mesh_data.elements)} elements")

    # Export to VTK
    logger.info("\n3. Exporting to VTK...")
    viewer = MeshViewer()
    viewer.show_mesh(mesh_data)

    vtk_file = Path("output/sphere_mesh.vtu")
    viewer.export_vtk(vtk_file)

    logger.info(f"   ✅ Exported to: {vtk_file}")
    logger.info(f"   Size: {vtk_file.stat().st_size / 1024:.1f} KB")

    logger.info(f"\n💡 VTK files can be opened in ParaView for advanced visualization:")
    logger.info(f"   - Load .vtu file in ParaView")
    logger.info(f"   - Apply filters (clip, slice, threshold, etc.)")
    logger.info(f"   - Create animations and high-quality renders")


def demo_boundary_visualization():
    """Demo 5: Boundary surface visualization"""
    logger.info("\n" + "=" * 70)
    logger.info("DEMO 5: Boundary Surface Visualization")
    logger.info("=" * 70)
    logger.info("\nVisualize only the boundary surface of a mesh")

    import cadquery as cq
    from koomesh.io.step_reader import STEPReader
    from koomesh.meshing import TetMesher
    from koomesh.visualization import MeshViewer

    # Create hollow cylinder
    logger.info("\n1. Creating geometry (hollow cylinder)...")
    hollow_cylinder = (cq.Workplane('XY')
                       .circle(8.0)
                       .circle(5.0)
                       .extrude(15.0))

    step_file = Path("output/demo_hollow_cylinder.step")
    step_file.parent.mkdir(parents=True, exist_ok=True)
    hollow_cylinder.val().exportStep(str(step_file))

    reader = STEPReader()
    shape = reader.read_file(str(step_file))

    # Generate mesh
    logger.info("\n2. Generating mesh...")
    mesher = TetMesher(mesh_size=2.0)
    mesh_data = mesher.mesh_shape(shape)

    logger.info(f"   ✅ Mesh: {len(mesh_data.nodes)} nodes, {len(mesh_data.elements)} elements")

    # Visualize boundary
    logger.info("\n3. Visualizing boundary surface...")
    viewer = MeshViewer(window_size=(1024, 768))
    viewer.show_mesh(mesh_data)
    viewer.show_boundary(show_surface=True, surface_color='lightgreen', surface_opacity=0.7)

    # Uncomment to display:
    # viewer.show()

    logger.info(f"\n💡 Boundary visualization shows only the outer surface")
    logger.info(f"   Useful for checking surface mesh quality and BC application")


def demo_quick_view():
    """Demo 6: Quick view helper"""
    logger.info("\n" + "=" * 70)
    logger.info("DEMO 6: Quick View Helper")
    logger.info("=" * 70)
    logger.info("\nRapid mesh inspection with one function call")

    import cadquery as cq
    from koomesh.io.step_reader import STEPReader
    from koomesh.meshing import TetMesher
    from koomesh.visualization import quick_view

    # Create geometry
    logger.info("\n1. Creating geometry...")
    cone = cq.Workplane('XY').circle(6.0).workplane(offset=12.0).circle(2.0).loft()

    step_file = Path("output/demo_cone.step")
    step_file.parent.mkdir(parents=True, exist_ok=True)
    cone.val().exportStep(str(step_file))

    reader = STEPReader()
    shape = reader.read_file(str(step_file))

    # Generate mesh
    logger.info("\n2. Generating mesh...")
    mesher = TetMesher(mesh_size=1.5)
    mesh_data = mesher.mesh_shape(shape)

    logger.info(f"   ✅ Mesh: {len(mesh_data.nodes)} nodes")

    # Quick view
    logger.info("\n3. Using quick_view...")

    # Quick view with aspect ratio coloring (uncomment to display):
    # quick_view(mesh_data, quality_metric='aspect_ratio')

    # Or just basic view:
    # quick_view(mesh_data)

    logger.info(f"\n💡 quick_view() is perfect for rapid debugging:")
    logger.info(f"   - One line of code")
    logger.info(f"   - Immediate visual feedback")
    logger.info(f"   - Optional quality coloring")


def main():
    """Run all mesh viewer demos"""
    logger.info("\n" + "=" * 70)
    logger.info("INTERACTIVE MESH VIEWER DEMONSTRATION")
    logger.info("=" * 70)
    logger.info("\nComprehensive 3D mesh visualization with PyVista/VTK")

    try:
        # Demo 1: Basic visualization
        demo_basic_visualization()

        # Demo 2: Quality metrics
        demo_quality_visualization()

        # Demo 3: Camera views
        demo_camera_views()

        # Demo 4: VTK export
        demo_vtk_export()

        # Demo 5: Boundary visualization
        demo_boundary_visualization()

        # Demo 6: Quick view
        demo_quick_view()

        logger.info("\n" + "=" * 70)
        logger.info("✅ ALL DEMOS COMPLETED SUCCESSFULLY!")
        logger.info("=" * 70)
        logger.info("\nGenerated files:")
        logger.info("  - output/demo_box_hole.step")
        logger.info("  - output/demo_cylinder.step")
        logger.info("  - output/demo_l_shape.step")
        logger.info("  - output/sphere_mesh.vtu")
        logger.info("  - output/demo_hollow_cylinder.step")

        logger.info("\n📚 Key Takeaways:")
        logger.info("  ✓ Interactive 3D mesh visualization")
        logger.info("  ✓ Quality metric color mapping (aspect ratio, Jacobian, etc.)")
        logger.info("  ✓ Multiple camera views (isometric, orthographic)")
        logger.info("  ✓ VTK export for ParaView")
        logger.info("  ✓ Boundary surface extraction")
        logger.info("  ✓ Mouse controls (rotate, zoom, pan)")

        logger.info("\n💡 Next steps:")
        logger.info("  - Uncomment viewer.show() calls to see interactive visualizations")
        logger.info("  - Requires X server (desktop) or Jupyter notebook")
        logger.info("  - Use OSMesa for headless rendering")
        logger.info("  - Export VTK files for advanced ParaView analysis")

        logger.info("\n🎯 Typical workflows:")
        logger.info("  1. Generate mesh → quick_view() for rapid check")
        logger.info("  2. Visualize quality → identify problem areas")
        logger.info("  3. Export VTK → detailed analysis in ParaView")
        logger.info("  4. Create screenshots → documentation and reports")

    except Exception as e:
        logger.error(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
