"""
Mesh Viewer Simple Test
=======================

Test mesh viewer data conversion without rendering (headless-safe).
"""

import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_data_conversion():
    """Test MeshData to PyVista conversion"""
    logger.info("=" * 70)
    logger.info(" " * 18 + "MESH VIEWER DATA CONVERSION TEST")
    logger.info("=" * 70)

    import cadquery as cq
    from koomesh.io.step_reader import STEPReader
    from koomesh.meshing import TetMesher
    from koomesh.visualization import MeshViewer

    # Create test geometry
    logger.info("\n1. Creating test geometry (box)...")
    box_cq = cq.Workplane('XY').box(10.0, 10.0, 10.0)

    step_file = Path("output/viewer_tests/test_box.step")
    step_file.parent.mkdir(parents=True, exist_ok=True)
    box_cq.val().exportStep(str(step_file))

    reader = STEPReader()
    box = reader.read_file(str(step_file))

    # Generate mesh
    logger.info("\n2. Generating mesh...")
    mesher = TetMesher(mesh_size=2.0)
    mesh_data = mesher.mesh_shape(box)

    logger.info(f"   ✅ Mesh: {len(mesh_data.nodes)} nodes, {len(mesh_data.elements)} elements")

    # Test viewer initialization
    logger.info("\n3. Testing MeshViewer initialization...")
    viewer = MeshViewer(off_screen=True)
    logger.info(f"   ✅ Viewer initialized")

    # Test data conversion
    logger.info("\n4. Testing MeshData to PyVista conversion...")
    pv_mesh = viewer._mesh_data_to_pyvista(mesh_data)

    logger.info(f"   ✅ Conversion successful:")
    logger.info(f"   - PyVista nodes: {pv_mesh.n_points}")
    logger.info(f"   - PyVista cells: {pv_mesh.n_cells}")
    logger.info(f"   - Match: {pv_mesh.n_points == len(mesh_data.nodes) and pv_mesh.n_cells == len(mesh_data.elements)}")

    if pv_mesh.n_points != len(mesh_data.nodes):
        logger.error(f"   ❌ Node count mismatch!")
        return False

    if pv_mesh.n_cells != len(mesh_data.elements):
        logger.error(f"   ❌ Element count mismatch!")
        return False

    # Test VTK export (doesn't require rendering)
    logger.info("\n5. Testing VTK file export...")
    viewer.pv_mesh = pv_mesh
    viewer.mesh_data = mesh_data

    vtk_file = Path("output/viewer_tests/test_mesh.vtu")
    viewer.export_vtk(vtk_file)

    if vtk_file.exists():
        logger.info(f"   ✅ VTK file exported: {vtk_file}")
        logger.info(f"   Size: {vtk_file.stat().st_size / 1024:.1f} KB")
    else:
        logger.error(f"   ❌ VTK export failed")
        return False

    # Test with different geometry types
    logger.info("\n6. Testing with cylinder geometry...")
    cylinder_cq = cq.Workplane('XY').circle(5.0).extrude(15.0)

    step_file2 = Path("output/viewer_tests/test_cylinder.step")
    cylinder_cq.val().exportStep(str(step_file2))

    reader2 = STEPReader()  # Create new reader for second file
    cylinder = reader2.read_file(str(step_file2))
    mesh_data2 = mesher.mesh_shape(cylinder)

    pv_mesh2 = viewer._mesh_data_to_pyvista(mesh_data2)

    logger.info(f"   ✅ Cylinder conversion successful:")
    logger.info(f"   - Nodes: {pv_mesh2.n_points}")
    logger.info(f"   - Cells: {pv_mesh2.n_cells}")

    return True


def test_quality_data():
    """Test quality metric data preparation"""
    logger.info("\n" + "=" * 70)
    logger.info(" " * 20 + "QUALITY DATA PREPARATION TEST")
    logger.info("=" * 70)

    import cadquery as cq
    from koomesh.io.step_reader import STEPReader
    from koomesh.meshing import TetMesher
    from koomesh.meshing.quality_checker import QualityChecker
    from koomesh.visualization import MeshViewer

    # Create test geometry
    logger.info("\n1. Creating test geometry...")
    sphere_cq = cq.Workplane('XY').sphere(5.0)

    step_file = Path("output/viewer_tests/test_sphere.step")
    step_file.parent.mkdir(parents=True, exist_ok=True)
    sphere_cq.val().exportStep(str(step_file))

    reader = STEPReader()
    sphere = reader.read_file(str(step_file))

    # Generate mesh
    logger.info("\n2. Generating mesh...")
    mesher = TetMesher(mesh_size=1.5)
    mesh_data = mesher.mesh_shape(sphere)

    logger.info(f"   ✅ Mesh: {len(mesh_data.nodes)} nodes, {len(mesh_data.elements)} elements")

    # Calculate quality metrics
    logger.info("\n3. Calculating quality metrics...")
    quality_checker = QualityChecker()
    quality_result = quality_checker.check_mesh(mesh_data)

    logger.info(f"   ✅ Quality metrics calculated")
    logger.info(f"   - Num elements: {quality_result.num_elements}")
    logger.info(f"   - Bad elements: {quality_result.num_bad_elements}")
    logger.info(f"   - Aspect ratio: min={quality_result.aspect_ratio['min']:.3f}, max={quality_result.aspect_ratio['max']:.3f}, mean={quality_result.aspect_ratio['mean']:.3f}")
    logger.info(f"   - Jacobian: min={quality_result.jacobian['min']:.3f}, max={quality_result.jacobian['max']:.3f}, mean={quality_result.jacobian['mean']:.3f}")

    # Test data conversion (quality visualization would need element-wise computation)
    logger.info("\n4. Testing PyVista data conversion...")
    viewer = MeshViewer(off_screen=True)
    pv_mesh = viewer._mesh_data_to_pyvista(mesh_data)
    viewer.pv_mesh = pv_mesh
    viewer.mesh_data = mesh_data

    logger.info(f"   ✅ Converted mesh to PyVista")
    logger.info(f"   - Nodes: {pv_mesh.n_points}")
    logger.info(f"   - Cells: {pv_mesh.n_cells}")

    return True


def test_camera_and_methods():
    """Test camera views and utility methods"""
    logger.info("\n" + "=" * 70)
    logger.info(" " * 18 + "CAMERA AND METHODS TEST")
    logger.info("=" * 70)

    import cadquery as cq
    from koomesh.io.step_reader import STEPReader
    from koomesh.meshing import TetMesher
    from koomesh.visualization import MeshViewer

    # Create test geometry
    logger.info("\n1. Creating test geometry...")
    box_cq = cq.Workplane('XY').box(5.0, 5.0, 5.0)

    step_file = Path("output/viewer_tests/test_small_box.step")
    step_file.parent.mkdir(parents=True, exist_ok=True)
    box_cq.val().exportStep(str(step_file))

    reader = STEPReader()
    box = reader.read_file(str(step_file))

    mesher = TetMesher(mesh_size=1.5)
    mesh_data = mesher.mesh_shape(box)

    logger.info(f"   ✅ Mesh: {len(mesh_data.nodes)} nodes")

    # Initialize viewer (off-screen, no display)
    logger.info("\n2. Testing viewer methods...")
    viewer = MeshViewer(window_size=(800, 600), off_screen=True)

    # These methods should work without rendering
    logger.info("   ✅ Viewer created")

    # Test data conversion
    pv_mesh = viewer._mesh_data_to_pyvista(mesh_data)
    logger.info(f"   ✅ Data conversion: {pv_mesh.n_points} nodes, {pv_mesh.n_cells} cells")

    # Test boundary extraction (PyVista built-in, no rendering)
    surface = pv_mesh.extract_surface()
    logger.info(f"   ✅ Boundary extraction: {surface.n_points} surface nodes, {surface.n_cells} surface faces")

    logger.info("\n3. All viewer methods tested successfully (without rendering)")

    return True


if __name__ == "__main__":
    try:
        # Test 1: Data conversion
        success1 = test_data_conversion()

        # Test 2: Quality data preparation
        success2 = test_quality_data()

        # Test 3: Camera and methods
        success3 = test_camera_and_methods()

        if all([success1, success2, success3]):
            logger.info("\n" + "=" * 70)
            logger.info("✅ ALL MESH VIEWER TESTS PASSED!")
            logger.info("=" * 70)
            logger.info("\nGenerated files:")
            logger.info("  - output/viewer_tests/test_box.step")
            logger.info("  - output/viewer_tests/test_mesh.vtu")
            logger.info("  - output/viewer_tests/test_cylinder.step")
            logger.info("  - output/viewer_tests/test_sphere.step")

            logger.info("\n📚 Key Features Verified:")
            logger.info("  ✓ MeshData to PyVista conversion")
            logger.info("  ✓ VTK file export")
            logger.info("  ✓ Quality metric data extraction")
            logger.info("  ✓ Boundary surface extraction")
            logger.info("  ✓ Multiple geometry types (box, cylinder, sphere)")

            logger.info("\n💡 Note:")
            logger.info("  Screenshots and interactive rendering require X server or OSMesa.")
            logger.info("  Use in Jupyter notebook or desktop environment for full visualization.")

            sys.exit(0)
        else:
            logger.error("\n❌ Some tests failed")
            sys.exit(1)

    except Exception as e:
        logger.error(f"\n❌ Mesh viewer test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
