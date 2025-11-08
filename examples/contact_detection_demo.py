"""
Contact Surface Detection Demonstration
========================================

This demo shows how to detect contact surfaces between mesh parts.

Author: KooMeshGenerator Team
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from koomesh.meshing.mesh_data import MeshData, ElementType
from koomesh.utils.contact_detection import ContactSurfaceDetector, detect_and_report_contacts

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_two_part_mesh():
    """Create a mesh with two parts in proximity"""
    mesh = MeshData(element_type=ElementType.HEX8)

    # Part 1: Bottom cube (0 to 1 in Z)
    # Bottom face
    n1 = mesh.add_node(0.0, 0.0, 0.0)
    n2 = mesh.add_node(1.0, 0.0, 0.0)
    n3 = mesh.add_node(1.0, 1.0, 0.0)
    n4 = mesh.add_node(0.0, 1.0, 0.0)
    # Top face
    n5 = mesh.add_node(0.0, 0.0, 1.0)
    n6 = mesh.add_node(1.0, 0.0, 1.0)
    n7 = mesh.add_node(1.0, 1.0, 1.0)
    n8 = mesh.add_node(0.0, 1.0, 1.0)

    # Add element for part 1
    mesh.add_element([n1, n2, n3, n4, n5, n6, n7, n8], part_id=1)

    # Part 2: Top cube (1.05 to 2.05 in Z) - small gap
    # Bottom face
    n9 = mesh.add_node(0.0, 0.0, 1.05)
    n10 = mesh.add_node(1.0, 0.0, 1.05)
    n11 = mesh.add_node(1.0, 1.0, 1.05)
    n12 = mesh.add_node(0.0, 1.0, 1.05)
    # Top face
    n13 = mesh.add_node(0.0, 0.0, 2.05)
    n14 = mesh.add_node(1.0, 0.0, 2.05)
    n15 = mesh.add_node(1.0, 1.0, 2.05)
    n16 = mesh.add_node(0.0, 1.0, 2.05)

    # Add element for part 2
    mesh.add_element([n9, n10, n11, n12, n13, n14, n15, n16], part_id=2)

    return mesh


def demo_contact_detection():
    """Demonstrate contact surface detection"""
    logger.info("=" * 60)
    logger.info("Contact Surface Detection Demonstration")
    logger.info("=" * 60)

    # Create mesh with two parts
    logger.info("\n1. Creating two-part mesh...")
    mesh = create_two_part_mesh()
    logger.info(f"   Created mesh: {mesh.num_nodes()} nodes, {mesh.num_elements()} elements")

    # Count parts
    part_ids = set(elem.part_id for elem in mesh.elements.values())
    logger.info(f"   Parts: {sorted(part_ids)}")

    # Detect contacts with tolerance
    logger.info("\n2. Detecting contact surfaces...")
    logger.info("   Gap between parts: 0.05")
    logger.info("   Testing with tolerance: 0.1")

    detector = ContactSurfaceDetector()
    contacts = detector.detect_contacts(mesh, tolerance=0.1, min_faces=1)

    if contacts:
        logger.info(f"\n3. Found {len(contacts)} contact pair(s):")
        for i, contact in enumerate(contacts):
            logger.info(f"\n   Contact {i+1}:")
            logger.info(f"     Part 1 ID: {contact.part1_id}")
            logger.info(f"     Part 2 ID: {contact.part2_id}")
            logger.info(f"     Part 1 faces: {len(contact.part1_faces)}")
            logger.info(f"     Part 2 faces: {len(contact.part2_faces)}")
            logger.info(f"     Average distance: {contact.avg_distance:.4f}")
    else:
        logger.info("\n3. No contact surfaces detected")

    # Test with smaller tolerance (should not detect)
    logger.info("\n4. Testing with smaller tolerance (0.01)...")
    contacts_small = detector.detect_contacts(mesh, tolerance=0.01, min_faces=1)
    if contacts_small:
        logger.info(f"   Found {len(contacts_small)} contact pair(s)")
    else:
        logger.info("   No contacts detected (gap is larger than tolerance)")

    # Export contact definitions
    if contacts:
        Path("output").mkdir(exist_ok=True)
        logger.info("\n5. Exporting contact definitions...")
        detector.export_contact_pairs(contacts, "output/contacts.inp", format="abaqus")
        logger.info("   Exported: output/contacts.inp (Abaqus format)")
        detector.export_contact_pairs(contacts, "output/contacts.k", format="lsdyna")
        logger.info("   Exported: output/contacts.k (LS-DYNA format)")

    logger.info("\n" + "=" * 60)
    logger.info("Contact Detection Demo Complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    demo_contact_detection()
