"""
Mesh Utilities Demonstration
=============================

This demo shows mesh copy, merge, and transform utilities.

Author: KooMeshGenerator Team
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from koomesh.meshing.mesh_data import MeshData, ElementType
from koomesh.utils.mesh_copy import copy_mesh, copy_mesh_subset, copy_mesh_part
from koomesh.utils.mesh_merge import merge_meshes, merge_meshes_with_tolerance
from koomesh.utils.mesh_transform import translate_mesh, scale_mesh

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_sample_mesh(offset_x=0, offset_y=0, part_id=1):
    """Create a simple tetrahedral mesh for testing"""
    mesh = MeshData(element_type=ElementType.TET4)

    # Create 4 nodes for a single tetrahedron
    n1 = mesh.add_node(0.0 + offset_x, 0.0 + offset_y, 0.0)
    n2 = mesh.add_node(1.0 + offset_x, 0.0 + offset_y, 0.0)
    n3 = mesh.add_node(0.5 + offset_x, 1.0 + offset_y, 0.0)
    n4 = mesh.add_node(0.5 + offset_x, 0.5 + offset_y, 1.0)

    # Create tetrahedral element
    mesh.add_element([n1, n2, n3, n4], part_id=part_id)

    return mesh


def demo_copy_utilities():
    """Demonstrate mesh copying utilities"""
    logger.info("=" * 60)
    logger.info("Mesh Copy Utilities Demo")
    logger.info("=" * 60)

    # Create original mesh
    logger.info("\n1. Creating original mesh...")
    mesh = create_sample_mesh()
    logger.info(f"   Original: {mesh.num_nodes()} nodes, {mesh.num_elements()} elements")

    # Deep copy
    logger.info("\n2. Creating deep copy...")
    mesh_copy = copy_mesh(mesh, deep=True)
    logger.info(f"   Copy: {mesh_copy.num_nodes()} nodes, {mesh_copy.num_elements()} elements")

    # Modify copy
    translate_mesh(mesh_copy, dx=5.0)
    logger.info("   Translated copy by dx=5.0")
    logger.info(f"   Original node 1 position: ({mesh.nodes[1].x:.1f}, {mesh.nodes[1].y:.1f}, {mesh.nodes[1].z:.1f})")
    logger.info(f"   Copy node 1 position: ({mesh_copy.nodes[1].x:.1f}, {mesh_copy.nodes[1].y:.1f}, {mesh_copy.nodes[1].z:.1f})")


def demo_merge_utilities():
    """Demonstrate mesh merging utilities"""
    logger.info("\n" + "=" * 60)
    logger.info("Mesh Merge Utilities Demo")
    logger.info("=" * 60)

    # Create multiple meshes
    logger.info("\n1. Creating multiple meshes...")
    mesh1 = create_sample_mesh(offset_x=0, offset_y=0, part_id=1)
    mesh2 = create_sample_mesh(offset_x=2, offset_y=0, part_id=2)
    mesh3 = create_sample_mesh(offset_x=4, offset_y=0, part_id=3)

    logger.info(f"   Mesh 1: {mesh1.num_nodes()} nodes, {mesh1.num_elements()} elements")
    logger.info(f"   Mesh 2: {mesh2.num_nodes()} nodes, {mesh2.num_elements()} elements")
    logger.info(f"   Mesh 3: {mesh3.num_nodes()} nodes, {mesh3.num_elements()} elements")

    # Merge meshes
    logger.info("\n2. Merging meshes...")
    merged = merge_meshes([mesh1, mesh2, mesh3], renumber=True, preserve_parts=True)
    logger.info(f"   Merged: {merged.num_nodes()} nodes, {merged.num_elements()} elements")

    # Check part IDs
    part_ids = set(elem.part_id for elem in merged.elements.values())
    logger.info(f"   Part IDs in merged mesh: {sorted(part_ids)}")


def demo_merge_with_tolerance():
    """Demonstrate merge with tolerance (eliminating duplicate nodes)"""
    logger.info("\n" + "=" * 60)
    logger.info("Merge with Tolerance Demo")
    logger.info("=" * 60)

    # Create meshes with overlapping nodes
    logger.info("\n1. Creating meshes with overlapping boundary...")
    mesh1 = create_sample_mesh(offset_x=0, offset_y=0, part_id=1)
    mesh2 = create_sample_mesh(offset_x=1, offset_y=0, part_id=2)  # Shares edge with mesh1

    # Simple merge (keeps duplicates)
    logger.info("\n2. Simple merge (keeps duplicate nodes)...")
    merged_simple = merge_meshes([mesh1, mesh2])
    logger.info(f"   Result: {merged_simple.num_nodes()} nodes, {merged_simple.num_elements()} elements")

    # Merge with tolerance (eliminates duplicates)
    logger.info("\n3. Merge with tolerance (eliminates duplicate nodes)...")
    merged_tol = merge_meshes_with_tolerance([mesh1, mesh2], tolerance=1e-6)
    logger.info(f"   Result: {merged_tol.num_nodes()} nodes, {merged_tol.num_elements()} elements")


def demo_transform_utilities():
    """Demonstrate mesh transformation utilities"""
    logger.info("\n" + "=" * 60)
    logger.info("Mesh Transform Utilities Demo")
    logger.info("=" * 60)

    # Create mesh
    logger.info("\n1. Creating mesh...")
    mesh = create_sample_mesh()
    logger.info(f"   Original node 1: ({mesh.nodes[1].x:.2f}, {mesh.nodes[1].y:.2f}, {mesh.nodes[1].z:.2f})")

    # Translate
    logger.info("\n2. Translating mesh...")
    translate_mesh(mesh, dx=10.0, dy=5.0, dz=2.0)
    logger.info(f"   After translate: ({mesh.nodes[1].x:.2f}, {mesh.nodes[1].y:.2f}, {mesh.nodes[1].z:.2f})")

    # Scale
    logger.info("\n3. Scaling mesh by 2x...")
    scale_mesh(mesh, sx=2.0, sy=2.0, sz=2.0, center=(10.0, 5.0, 2.0))
    logger.info(f"   After scale: ({mesh.nodes[1].x:.2f}, {mesh.nodes[1].y:.2f}, {mesh.nodes[1].z:.2f})")


if __name__ == "__main__":
    demo_copy_utilities()
    demo_merge_utilities()
    demo_merge_with_tolerance()
    demo_transform_utilities()

    logger.info("\n" + "=" * 60)
    logger.info("All Mesh Utilities Demos Complete!")
    logger.info("=" * 60)
