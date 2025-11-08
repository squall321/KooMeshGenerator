"""
Mesh Coarsening Demonstration
==============================

This demo shows how to coarsen tetrahedral meshes using vertex clustering.

Author: KooMeshGenerator Team
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from koomesh.meshing.tet_mesher import TetMesher
from koomesh.meshing.mesh_data import MeshData, ElementType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_simple_tet_mesh():
    """Create a simple tetrahedral mesh for testing"""
    mesh = MeshData(element_type=ElementType.TET4)

    # Create a simple grid of nodes
    node_ids = {}
    for i in range(3):
        for j in range(3):
            for k in range(3):
                x, y, z = float(i), float(j), float(k)
                nid = mesh.add_node(x, y, z)
                node_ids[(i, j, k)] = nid

    # Create tetrahedral elements
    # Divide each cube into 5 tetrahedra
    for i in range(2):
        for j in range(2):
            for k in range(2):
                # Get 8 corners of cube
                n000 = node_ids[(i, j, k)]
                n100 = node_ids[(i+1, j, k)]
                n010 = node_ids[(i, j+1, k)]
                n110 = node_ids[(i+1, j+1, k)]
                n001 = node_ids[(i, j, k+1)]
                n101 = node_ids[(i+1, j, k+1)]
                n011 = node_ids[(i, j+1, k+1)]
                n111 = node_ids[(i+1, j+1, k+1)]

                # 5 tetrahedra per cube (standard decomposition)
                mesh.add_element([n000, n100, n110, n101])
                mesh.add_element([n000, n110, n010, n011])
                mesh.add_element([n000, n101, n001, n011])
                mesh.add_element([n101, n110, n111, n011])
                mesh.add_element([n000, n110, n101, n011])

    return mesh


def demo_mesh_coarsening():
    """Demonstrate mesh coarsening"""
    logger.info("=" * 60)
    logger.info("Mesh Coarsening Demonstration")
    logger.info("=" * 60)

    # Create a simple test mesh
    logger.info("\n1. Creating test tetrahedral mesh...")
    mesh = create_simple_tet_mesh()
    logger.info(f"   Original mesh: {mesh.num_nodes()} nodes, {mesh.num_elements()} elements")

    # Initialize mesher
    mesher = TetMesher()

    # Test different coarsening factors
    coarsening_factors = [0.7, 0.5, 0.3]

    for factor in coarsening_factors:
        logger.info(f"\n2. Coarsening mesh with factor {factor}...")
        coarsened_mesh = mesher.coarsen_mesh(mesh, coarsening_factor=factor)

        logger.info(f"   Coarsened mesh: {coarsened_mesh.num_nodes()} nodes, "
                   f"{coarsened_mesh.num_elements()} elements")

        reduction_nodes = (1 - coarsened_mesh.num_nodes() / mesh.num_nodes()) * 100
        reduction_elems = (1 - coarsened_mesh.num_elements() / mesh.num_elements()) * 100

        logger.info(f"   Reduction: {reduction_nodes:.1f}% nodes, {reduction_elems:.1f}% elements")

    # Summary
    logger.info("\n3. Summary:")
    logger.info(f"   Mesh coarsening successfully reduces mesh size")
    logger.info(f"   Lower coarsening factor = more aggressive reduction")
    logger.info(f"   Degenerate elements are automatically removed")

    logger.info("\n" + "=" * 60)
    logger.info("Mesh Coarsening Demo Complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    demo_mesh_coarsening()
