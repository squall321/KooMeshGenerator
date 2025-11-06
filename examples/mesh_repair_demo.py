"""
Mesh Repair Demo
================

Demonstrates mesh repair utilities for fixing common issues.

Author: KooMeshGenerator Team
"""

from koomesh.meshing.mesh_data import MeshData, ElementType
from koomesh.utils.mesh_repair import MeshRepair, repair_mesh
from koomesh.utils.mesh_info import print_mesh_info


def demo_duplicate_nodes():
    """Repair mesh with duplicate nodes"""
    print("\n" + "="*60)
    print("Demo 1: Remove Duplicate Nodes")
    print("="*60)

    mesh = MeshData(element_type=ElementType.TET4)

    # Create mesh with duplicates
    n1 = mesh.add_node(0.0, 0.0, 0.0)
    n2 = mesh.add_node(1.0, 0.0, 0.0)
    n3 = mesh.add_node(0.0, 1.0, 0.0)
    n4 = mesh.add_node(0.0, 0.0, 1.0)
    n5 = mesh.add_node(0.0, 0.0, 0.0)  # Duplicate of n1
    n6 = mesh.add_node(1.0, 0.0, 0.0)  # Duplicate of n2

    mesh.add_element([n1, n2, n3, n4])
    mesh.add_element([n5, n6, n3, n4])

    print(f"Before repair: {len(mesh.nodes)} nodes, {len(mesh.elements)} elements")

    repair = MeshRepair(mesh)
    count = repair.remove_duplicate_nodes()

    print(f"After repair: {len(mesh.nodes)} nodes, {len(mesh.elements)} elements")
    print(f"✓ Removed {count} duplicate nodes")


def demo_degenerate_elements():
    """Remove degenerate elements"""
    print("\n" + "="*60)
    print("Demo 2: Remove Degenerate Elements")
    print("="*60)

    mesh = MeshData(element_type=ElementType.TET4)

    n1 = mesh.add_node(0.0, 0.0, 0.0)
    n2 = mesh.add_node(1.0, 0.0, 0.0)
    n3 = mesh.add_node(0.0, 1.0, 0.0)
    n4 = mesh.add_node(0.0, 0.0, 1.0)

    mesh.add_element([n1, n2, n3, n4])  # Good
    mesh.add_element([n1, n1, n2, n3])  # Degenerate
    mesh.add_element([n2, n2, n2, n2])  # Very degenerate

    print(f"Before repair: {len(mesh.elements)} elements")

    repair = MeshRepair(mesh)
    count = repair.remove_degenerate_elements()

    print(f"After repair: {len(mesh.elements)} elements")
    print(f"✓ Removed {count} degenerate elements")


def demo_unused_nodes():
    """Remove unused nodes"""
    print("\n" + "="*60)
    print("Demo 3: Remove Unused Nodes")
    print("="*60)

    mesh = MeshData(element_type=ElementType.TET4)

    n1 = mesh.add_node(0.0, 0.0, 0.0)
    n2 = mesh.add_node(1.0, 0.0, 0.0)
    n3 = mesh.add_node(0.0, 1.0, 0.0)
    n4 = mesh.add_node(0.0, 0.0, 1.0)
    
    # Add many unused nodes
    for i in range(10):
        mesh.add_node(10.0 + float(i), 10.0, 10.0)

    mesh.add_element([n1, n2, n3, n4])

    print(f"Before repair: {len(mesh.nodes)} nodes")

    repair = MeshRepair(mesh)
    count = repair.remove_unused_nodes()

    print(f"After repair: {len(mesh.nodes)} nodes")
    print(f"✓ Removed {count} unused nodes")


def demo_comprehensive_repair():
    """Comprehensive mesh repair"""
    print("\n" + "="*60)
    print("Demo 4: Comprehensive Repair")
    print("="*60)

    mesh = MeshData(element_type=ElementType.TET4)

    # Create problematic mesh
    n1 = mesh.add_node(0.0, 0.0, 0.0)
    n2 = mesh.add_node(1.0, 0.0, 0.0)
    n3 = mesh.add_node(0.0, 1.0, 0.0)
    n4 = mesh.add_node(0.0, 0.0, 1.0)
    n5 = mesh.add_node(0.0, 0.0, 0.0)  # Duplicate
    n6 = mesh.add_node(10.0, 10.0, 10.0)  # Unused

    mesh.add_element([n1, n2, n3, n4])
    mesh.add_element([n1, n1, n2, n3])  # Degenerate

    print_mesh_info(mesh, "Before Repair")

    # Use convenience function
    results = repair_mesh(mesh)

    print_mesh_info(mesh, "After Repair")
    print(f"\nTotal fixes: {results['total']}")


def demo_merge_coincident():
    """Merge coincident nodes"""
    print("\n" + "="*60)
    print("Demo 5: Merge Coincident Nodes")
    print("="*60)

    mesh = MeshData(element_type=ElementType.HEX8)

    # Create nodes that are very close but not exactly duplicate
    node_ids = []
    for i in range(2):
        for j in range(2):
            for k in range(2):
                # Add small random offset
                dx = 1e-7 if i == 1 else 0
                dy = 1e-7 if j == 1 else 0
                node_ids.append(mesh.add_node(float(i) + dx, float(j) + dy, float(k)))

    mesh.add_element([node_ids[0], node_ids[1], node_ids[3], node_ids[2],
                     node_ids[4], node_ids[5], node_ids[7], node_ids[6]])

    print(f"Before merge: {len(mesh.nodes)} nodes")

    repair = MeshRepair(mesh)
    count = repair.merge_coincident_nodes(tolerance=1e-5)

    print(f"After merge: {len(mesh.nodes)} nodes")
    print(f"✓ Merged {count} coincident nodes (tolerance=1e-5)")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("MESH REPAIR DEMONSTRATIONS")
    print("="*60)

    demo_duplicate_nodes()
    demo_degenerate_elements()
    demo_unused_nodes()
    demo_comprehensive_repair()
    demo_merge_coincident()

    print("\n" + "="*60)
    print("All demos completed!")
    print("="*60)
    print("\nCommon mesh issues fixed:")
    print("  - Duplicate nodes (exact coordinates)")
    print("  - Coincident nodes (within tolerance)")
    print("  - Degenerate elements (repeated nodes)")
    print("  - Unused nodes (not referenced by elements)")
    print("  - Bad connectivity (invalid node references)")
