#!/usr/bin/env python3
"""
STL Export Demonstration
=========================

Demonstrates STL format export for 3D printing and CAD.

Author: KooMeshGenerator Team
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from koomesh.meshing.mesh_data import MeshData, ElementType
from koomesh.export.stl_writer import export_to_stl


def demo_1_simple_tetrahedron():
    """Demo 1: Simple tetrahedron"""
    print("\n" + "="*60)
    print("Demo 1: Simple Tetrahedron")
    print("="*60)

    mesh = MeshData(element_type=ElementType.TET4)
    n1 = mesh.add_node(0.0, 0.0, 0.0)
    n2 = mesh.add_node(10.0, 0.0, 0.0)
    n3 = mesh.add_node(5.0, 10.0, 0.0)
    n4 = mesh.add_node(5.0, 5.0, 10.0)
    mesh.add_element([n1, n2, n3, n4])

    Path("stl_export_examples").mkdir(exist_ok=True)
    success = export_to_stl(mesh, "stl_export_examples/tetrahedron.stl", "tetrahedron")

    if success:
        print("✓ Exported tetrahedron.stl")
        print(f"  4 triangular faces")


def demo_2_cube():
    """Demo 2: Cube from HEX8"""
    print("\n" + "="*60)
    print("Demo 2: Cube")
    print("="*60)

    mesh = MeshData(element_type=ElementType.HEX8)
    node_ids = []
    for i in range(2):
        for j in range(2):
            for k in range(2):
                node_ids.append(mesh.add_node(float(i*10), float(j*10), float(k*10)))
    mesh.add_element([node_ids[0], node_ids[1], node_ids[3], node_ids[2],
                     node_ids[4], node_ids[5], node_ids[7], node_ids[6]])

    success = export_to_stl(mesh, "stl_export_examples/cube.stl", "cube")

    if success:
        print("✓ Exported cube.stl")
        print(f"  6 quad faces = 12 triangles")


def demo_3_prism():
    """Demo 3: Triangular prism"""
    print("\n" + "="*60)
    print("Demo 3: Triangular Prism")
    print("="*60)

    mesh = MeshData(element_type=ElementType.PRISM6)
    n1 = mesh.add_node(0.0, 0.0, 0.0)
    n2 = mesh.add_node(10.0, 0.0, 0.0)
    n3 = mesh.add_node(5.0, 10.0, 0.0)
    n4 = mesh.add_node(0.0, 0.0, 10.0)
    n5 = mesh.add_node(10.0, 0.0, 10.0)
    n6 = mesh.add_node(5.0, 10.0, 10.0)
    mesh.add_element([n1, n2, n3, n4, n5, n6])

    success = export_to_stl(mesh, "stl_export_examples/prism.stl", "prism")

    if success:
        print("✓ Exported prism.stl")
        print(f"  2 triangular + 3 quad faces")


def main():
    print("="*60)
    print("STL Export Demonstrations")
    print("="*60)
    print("\nSTL (STereoLithography) format for 3D printing")
    print("Website: https://en.wikipedia.org/wiki/STL_(file_format)")

    try:
        demo_1_simple_tetrahedron()
        demo_2_cube()
        demo_3_prism()

        print("\n" + "="*60)
        print("All STL export demonstrations completed!")
        print("="*60)
        print("\nFiles created in: stl_export_examples/")
        print("\nUse with:")
        print("  - 3D Printers (Ultimaker Cura, PrusaSlicer)")
        print("  - CAD Software (Fusion 360, SolidWorks)")
        print("  - Mesh viewers (MeshLab, Blender)")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
