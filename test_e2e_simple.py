"""
Simple End-to-End Test
======================

Test basic pipeline: STEP → Mesh → LS-DYNA

This bypasses the full pipeline to test core functionality.
"""

import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_step_creation():
    """Test 1: Create STEP file with CadQuery"""
    logger.info("=" * 60)
    logger.info("Test 1: Creating STEP file with CadQuery")
    logger.info("=" * 60)

    import cadquery as cq

    # Create simple box
    box = cq.Workplane('XY').box(100, 50, 20)

    # Export to STEP
    output = Path("output/test_box.step")
    output.parent.mkdir(exist_ok=True)
    box.val().exportStep(str(output))

    logger.info(f"✅ STEP file created: {output}")
    logger.info(f"   Size: {output.stat().st_size} bytes")

    return output


def test_gmsh_meshing():
    """Test 2: Create mesh with GMSH"""
    logger.info("\n" + "=" * 60)
    logger.info("Test 2: Creating mesh with GMSH")
    logger.info("=" * 60)

    import gmsh
    from koomesh.meshing.mesh_data import MeshData, ElementType

    gmsh.initialize()
    gmsh.model.add("test_box")

    # Create simple box geometry
    gmsh.model.occ.addBox(0, 0, 0, 100, 50, 20, tag=1)
    gmsh.model.occ.synchronize()

    # Set mesh size
    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", 10.0)

    # Generate 3D mesh
    gmsh.model.mesh.generate(3)

    # Get mesh data
    node_tags, node_coords, _ = gmsh.model.mesh.getNodes()
    elem_types, elem_tags, elem_node_tags = gmsh.model.mesh.getElements(3)

    logger.info(f"✅ Mesh generated")
    logger.info(f"   Nodes: {len(node_tags)}")

    if len(elem_types) > 0:
        logger.info(f"   Elements (type {elem_types[0]}): {len(elem_tags[0])}")

    # Create MeshData
    mesh = MeshData(element_type=ElementType.TET4)

    # Add nodes
    coords_3d = node_coords.reshape(-1, 3)
    node_id_map = {}
    for i, node_tag in enumerate(node_tags):
        x, y, z = coords_3d[i]
        node_id_map[node_tag] = mesh.add_node(x, y, z)

    # Add elements (assuming tet4)
    if len(elem_types) > 0 and len(elem_node_tags) > 0:
        node_list = elem_node_tags[0]
        nodes_per_elem = 4 if elem_types[0] == 4 else 8  # 4=tet4, 5=hex8

        for i in range(0, len(node_list), nodes_per_elem):
            gmsh_nodes = node_list[i:i+nodes_per_elem]
            mesh_nodes = [node_id_map[int(n)] for n in gmsh_nodes]
            mesh.add_element(mesh_nodes)

    gmsh.finalize()

    logger.info(f"✅ MeshData created")
    logger.info(f"   Nodes: {mesh.num_nodes()}")
    logger.info(f"   Elements: {mesh.num_elements()}")

    return mesh


def test_lsdyna_export(mesh):
    """Test 3: Export to LS-DYNA format"""
    logger.info("\n" + "=" * 60)
    logger.info("Test 3: Exporting to LS-DYNA format")
    logger.info("=" * 60)

    from koomesh.export.lsdyna_writer import LSDynaWriter
    from koomesh.io.hierarchy_parser import HierarchyNode

    output = Path("output/test_box.k")

    # Create hierarchy
    root = HierarchyNode(name="TestBox", level=0, part_type="solid")

    # Write LS-DYNA file
    with LSDynaWriter(str(output)) as writer:
        writer.write_complete_model([mesh], [], root)

    logger.info(f"✅ LS-DYNA file created: {output}")
    logger.info(f"   Size: {output.stat().st_size} bytes")

    # Check content
    with open(output, 'r') as f:
        lines = f.readlines()
        logger.info(f"   Lines: {len(lines)}")

        # Count keywords
        keywords = [l for l in lines if l.startswith('*')]
        logger.info(f"   Keywords: {len(keywords)}")

    return output


def main():
    """Run all tests"""
    logger.info("\n" + "=" * 70)
    logger.info(" " * 20 + "SIMPLE END-TO-END TEST")
    logger.info("=" * 70)

    try:
        # Test 1: Create STEP
        step_file = test_step_creation()

        # Test 2: Create Mesh
        mesh = test_gmsh_meshing()

        # Test 3: Export LS-DYNA
        lsdyna_file = test_lsdyna_export(mesh)

        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("✅ ALL TESTS PASSED!")
        logger.info("=" * 70)
        logger.info(f"\nGenerated files:")
        logger.info(f"  - {step_file}")
        logger.info(f"  - {lsdyna_file}")
        logger.info("\nNext steps:")
        logger.info("  1. Test full pipeline with STEP file reading")
        logger.info("  2. Fix OCC import issues in step_reader.py")
        logger.info("  3. Test with more complex geometries")

        return True

    except Exception as e:
        logger.error("\n" + "=" * 70)
        logger.error(f"❌ TEST FAILED: {e}")
        logger.error("=" * 70)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
