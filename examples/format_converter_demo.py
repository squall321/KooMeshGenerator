"""
Format Converter Demonstration
===============================

This demo shows how to convert meshes between different file formats.

Author: KooMeshGenerator Team
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from koomesh.meshing.mesh_data import MeshData, ElementType
from koomesh.io.format_converter import MeshFormatConverter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_sample_mesh():
    """Create a simple sample mesh"""
    mesh = MeshData(element_type=ElementType.TET4)

    # Create nodes for two tetrahedra
    n1 = mesh.add_node(0.0, 0.0, 0.0)
    n2 = mesh.add_node(1.0, 0.0, 0.0)
    n3 = mesh.add_node(0.5, 1.0, 0.0)
    n4 = mesh.add_node(0.5, 0.5, 1.0)
    n5 = mesh.add_node(1.5, 0.5, 0.5)

    # Create elements
    mesh.add_element([n1, n2, n3, n4], part_id=1)
    mesh.add_element([n2, n3, n4, n5], part_id=2)

    return mesh


def demo_format_conversion():
    """Demonstrate format conversion"""
    logger.info("=" * 60)
    logger.info("Format Converter Demonstration")
    logger.info("=" * 60)

    # Create output directory
    Path("output").mkdir(exist_ok=True)

    # Create sample mesh
    logger.info("\n1. Creating sample mesh...")
    mesh = create_sample_mesh()
    logger.info(f"   Created mesh: {mesh.num_nodes()} nodes, {mesh.num_elements()} elements")

    # Initialize converter
    converter = MeshFormatConverter()

    # Export to VTK
    logger.info("\n2. Exporting to VTK format...")
    converter.export_vtk(mesh, "output/sample.vtk")
    logger.info("   Exported: output/sample.vtk")

    # Export to Abaqus
    logger.info("\n3. Exporting to Abaqus INP format...")
    converter.export_abaqus(mesh, "output/sample.inp", part_name="TestPart")
    logger.info("   Exported: output/sample.inp")

    # Export to Nastran
    logger.info("\n4. Exporting to Nastran BDF format...")
    converter.export_nastran(mesh, "output/sample.bdf")
    logger.info("   Exported: output/sample.bdf")

    # Try importing VTK back
    logger.info("\n5. Importing from VTK...")
    try:
        imported_mesh = converter.import_from_vtk("output/sample.vtk")
        logger.info(f"   Imported: {imported_mesh.num_nodes()} nodes, "
                   f"{imported_mesh.num_elements()} elements")
        logger.info("   Round-trip successful!")
    except Exception as e:
        logger.error(f"   Import failed: {e}")

    logger.info("\n" + "=" * 60)
    logger.info("Format Converter Demo Complete!")
    logger.info("=" * 60)
    logger.info("\nGenerated files:")
    logger.info("  - output/sample.vtk (VTK format)")
    logger.info("  - output/sample.inp (Abaqus format)")
    logger.info("  - output/sample.bdf (Nastran format)")


if __name__ == "__main__":
    demo_format_conversion()
