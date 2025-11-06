"""
Gmsh MSH Format Export Demonstration
=====================================

This script demonstrates the capabilities of the Gmsh MSH format export functionality.

Gmsh is a popular open-source mesh generator, and the .msh format is widely supported
by many FEA and CFD tools.

Demonstrations:
1. Basic HEX8 mesh export (MSH 2.2)
2. TET4 mesh export (MSH 2.2)
3. HEX20 quadratic element export
4. Mixed element types
5. MSH 4.1 format export
6. Physical groups for material regions
7. Complete mesh with multiple groups

Requirements:
- KooMeshGenerator installed

Author: KooMeshGenerator Team
License: MIT
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from koomesh.meshing.mesh_data import MeshData, ElementType
from koomesh.export.gmsh_writer import GmshWriter, export_to_gmsh


def demo_1_basic_hex8():
    """Demo 1: Basic HEX8 mesh export (MSH 2.2)"""
    print("\n" + "=" * 70)
    print("Demo 1: Basic HEX8 Mesh Export (MSH 2.2)")
    print("=" * 70)

    # Create mesh
    mesh = MeshData(element_type=ElementType.HEX8)

    # Add nodes for a unit cube
    mesh.add_node(0.0, 0.0, 0.0, node_id=1)
    mesh.add_node(1.0, 0.0, 0.0, node_id=2)
    mesh.add_node(1.0, 1.0, 0.0, node_id=3)
    mesh.add_node(0.0, 1.0, 0.0, node_id=4)
    mesh.add_node(0.0, 0.0, 1.0, node_id=5)
    mesh.add_node(1.0, 0.0, 1.0, node_id=6)
    mesh.add_node(1.0, 1.0, 1.0, node_id=7)
    mesh.add_node(0.0, 1.0, 1.0, node_id=8)

    # Add HEX8 element
    mesh.add_element([1, 2, 3, 4, 5, 6, 7, 8], element_id=1)

    print(f"Created mesh: {mesh.num_nodes()} nodes, {mesh.num_elements()} elements")

    # Export
    output_file = "gmsh_export_examples/demo1_hex8.msh"
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    with GmshWriter(output_file, version="2.2") as writer:
        writer.write_mesh(mesh)

    print(f"✓ Exported to: {output_file}")

    # Verify by reading first few lines
    with open(output_file, 'r') as f:
        lines = f.readlines()[:10]
        print("  First few lines:")
        for line in lines[:5]:
            print(f"    {line.rstrip()}")


def demo_2_tet4_mesh():
    """Demo 2: TET4 mesh export"""
    print("\n" + "=" * 70)
    print("Demo 2: TET4 Mesh Export")
    print("=" * 70)

    # Create mesh
    mesh = MeshData(element_type=ElementType.TET4)

    # Add nodes for a tetrahedron
    mesh.add_node(0.0, 0.0, 0.0, node_id=1)
    mesh.add_node(1.0, 0.0, 0.0, node_id=2)
    mesh.add_node(0.5, 1.0, 0.0, node_id=3)
    mesh.add_node(0.5, 0.5, 1.0, node_id=4)

    # Add TET4 element
    mesh.add_element([1, 2, 3, 4], element_id=1)

    print(f"Created mesh: {mesh.num_nodes()} nodes, {mesh.num_elements()} elements")

    # Export
    output_file = "gmsh_export_examples/demo2_tet4.msh"
    success = export_to_gmsh(mesh, output_file, version="2.2")

    if success:
        print(f"✓ Exported to: {output_file}")
        print(f"  Format: MSH 2.2 (ASCII)")


def demo_3_hex20_quadratic():
    """Demo 3: HEX20 quadratic element export"""
    print("\n" + "=" * 70)
    print("Demo 3: HEX20 Quadratic Element Export")
    print("=" * 70)

    # Create mesh
    mesh = MeshData(element_type=ElementType.HEX20)

    # Add 20 nodes for HEX20 (8 corners + 12 mid-edges)
    nodes_coords = [
        (0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),  # Corner nodes (bottom)
        (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1),  # Corner nodes (top)
        (0.5, 0, 0), (1, 0.5, 0), (0.5, 1, 0), (0, 0.5, 0),  # Mid-edge (bottom)
        (0.5, 0, 1), (1, 0.5, 1), (0.5, 1, 1), (0, 0.5, 1),  # Mid-edge (top)
        (0, 0, 0.5), (1, 0, 0.5), (1, 1, 0.5), (0, 1, 0.5),  # Mid-edge (vertical)
    ]

    for i, (x, y, z) in enumerate(nodes_coords, 1):
        mesh.add_node(float(x), float(y), float(z), node_id=i)

    # Add HEX20 element
    mesh.add_element(list(range(1, 21)), element_id=1)

    print(f"Created mesh: {mesh.num_nodes()} nodes, {mesh.num_elements()} elements")

    # Export
    output_file = "gmsh_export_examples/demo3_hex20.msh"
    with GmshWriter(output_file) as writer:
        writer.write_mesh(mesh)

    print(f"✓ Exported to: {output_file}")
    print(f"  Element type: HEX20 (20-node quadratic hexahedron)")


def demo_4_mixed_elements():
    """Demo 4: Mixed element types"""
    print("\n" + "=" * 70)
    print("Demo 4: Mixed Element Types")
    print("=" * 70)

    # Create mesh
    mesh = MeshData(element_type=ElementType.HEX8)

    # Add nodes for HEX8 (nodes 1-8)
    mesh.add_node(0.0, 0.0, 0.0, node_id=1)
    mesh.add_node(1.0, 0.0, 0.0, node_id=2)
    mesh.add_node(1.0, 1.0, 0.0, node_id=3)
    mesh.add_node(0.0, 1.0, 0.0, node_id=4)
    mesh.add_node(0.0, 0.0, 1.0, node_id=5)
    mesh.add_node(1.0, 0.0, 1.0, node_id=6)
    mesh.add_node(1.0, 1.0, 1.0, node_id=7)
    mesh.add_node(0.0, 1.0, 1.0, node_id=8)

    # Add nodes for TET4 (nodes 9-12)
    mesh.add_node(2.0, 0.0, 0.0, node_id=9)
    mesh.add_node(3.0, 0.0, 0.0, node_id=10)
    mesh.add_node(2.5, 1.0, 0.0, node_id=11)
    mesh.add_node(2.5, 0.5, 1.0, node_id=12)

    # Add HEX8 element
    mesh.add_element([1, 2, 3, 4, 5, 6, 7, 8], element_id=1, element_type=ElementType.HEX8)

    # Add TET4 element
    mesh.add_element([9, 10, 11, 12], element_id=2, element_type=ElementType.TET4)

    print(f"Created mesh: {mesh.num_nodes()} nodes, {mesh.num_elements()} elements")
    print("  - 1 HEX8, 1 TET4")

    # Export
    output_file = "gmsh_export_examples/demo4_mixed.msh"
    with GmshWriter(output_file) as writer:
        writer.write_mesh(mesh)

    print(f"✓ Exported to: {output_file}")


def demo_5_msh_v4():
    """Demo 5: MSH 4.1 format export"""
    print("\n" + "=" * 70)
    print("Demo 5: MSH 4.1 Format Export")
    print("=" * 70)

    # Create simple mesh
    mesh = MeshData(element_type=ElementType.HEX8)

    # Add nodes
    mesh.add_node(0.0, 0.0, 0.0, node_id=1)
    mesh.add_node(1.0, 0.0, 0.0, node_id=2)
    mesh.add_node(1.0, 1.0, 0.0, node_id=3)
    mesh.add_node(0.0, 1.0, 0.0, node_id=4)
    mesh.add_node(0.0, 0.0, 1.0, node_id=5)
    mesh.add_node(1.0, 0.0, 1.0, node_id=6)
    mesh.add_node(1.0, 1.0, 1.0, node_id=7)
    mesh.add_node(0.0, 1.0, 1.0, node_id=8)

    # Add element
    mesh.add_element([1, 2, 3, 4, 5, 6, 7, 8], element_id=1)

    print(f"Created mesh: {mesh.num_nodes()} nodes, {mesh.num_elements()} elements")

    # Export as MSH 4.1
    output_file = "gmsh_export_examples/demo5_msh41.msh"
    with GmshWriter(output_file, version="4.1") as writer:
        writer.write_mesh(mesh)

    print(f"✓ Exported to: {output_file}")
    print(f"  Format: MSH 4.1 (modern)")

    # Read and show format differences
    with open(output_file, 'r') as f:
        content = f.read()
        print("  Key sections:")
        if "$Entities" in content:
            print("    - $Entities (v4.1 feature)")
        if "$Nodes" in content:
            print("    - $Nodes")
        if "$Elements" in content:
            print("    - $Elements")


def demo_6_physical_groups():
    """Demo 6: Physical groups for material regions"""
    print("\n" + "=" * 70)
    print("Demo 6: Physical Groups (Material Regions)")
    print("=" * 70)

    # Create mesh with multiple elements
    mesh = MeshData(element_type=ElementType.HEX8)

    # Create 2x1x1 grid (2 cubes)
    for i in range(3):
        for j in range(2):
            for k in range(2):
                node_id = i * 4 + j * 2 + k + 1
                mesh.add_node(float(i), float(j), float(k), node_id=node_id)

    # Add two elements
    mesh.add_element([1, 3, 7, 5, 2, 4, 8, 6], element_id=1)
    mesh.add_element([5, 7, 11, 9, 6, 8, 12, 10], element_id=2)

    print(f"Created mesh: {mesh.num_nodes()} nodes, {mesh.num_elements()} elements")

    # Define physical groups
    physical_groups = {
        "steel": [1],
        "aluminum": [2]
    }

    print("  - Physical groups:")
    for name, elems in physical_groups.items():
        print(f"    {name}: elements {elems}")

    # Export
    output_file = "gmsh_export_examples/demo6_physical_groups.msh"
    with GmshWriter(output_file) as writer:
        writer.write_mesh(mesh, physical_groups=physical_groups)

    print(f"✓ Exported to: {output_file}")

    # Verify
    with open(output_file, 'r') as f:
        content = f.read()
        if "$PhysicalNames" in content:
            print("  ✓ Physical names section included")


def demo_7_complete_mesh():
    """Demo 7: Complete mesh with multiple groups"""
    print("\n" + "=" * 70)
    print("Demo 7: Complete Mesh with Multiple Groups")
    print("=" * 70)

    # Create 2x2x1 mesh (4 cubes)
    mesh = MeshData(element_type=ElementType.HEX8)

    # Create nodes for 3x3x2 grid
    for i in range(3):
        for j in range(3):
            for k in range(2):
                node_id = i * 6 + j * 2 + k + 1
                mesh.add_node(float(i), float(j), float(k), node_id=node_id)

    # Add 4 HEX8 elements
    mesh.add_element([1, 3, 9, 7, 2, 4, 10, 8], element_id=1)
    mesh.add_element([3, 5, 11, 9, 4, 6, 12, 10], element_id=2)
    mesh.add_element([7, 9, 15, 13, 8, 10, 16, 14], element_id=3)
    mesh.add_element([9, 11, 17, 15, 10, 12, 18, 16], element_id=4)

    print(f"Created mesh: {mesh.num_nodes()} nodes, {mesh.num_elements()} elements")

    # Define multiple physical groups
    physical_groups = {
        "bottom_left": [1],
        "bottom_right": [2],
        "top_left": [3],
        "top_right": [4]
    }

    print("  - Physical groups: 4 regions")

    # Export with MSH 2.2
    output_v2 = "gmsh_export_examples/demo7_complete_v2.msh"
    with GmshWriter(output_v2, version="2.2") as writer:
        writer.write_mesh(mesh, physical_groups=physical_groups)
    print(f"✓ Exported MSH 2.2: {output_v2}")

    # Export with MSH 4.1
    output_v4 = "gmsh_export_examples/demo7_complete_v4.msh"
    with GmshWriter(output_v4, version="4.1") as writer:
        writer.write_mesh(mesh, physical_groups=physical_groups)
    print(f"✓ Exported MSH 4.1: {output_v4}")


def main():
    """Run all demonstrations"""
    print("\n" + "=" * 70)
    print("Gmsh MSH Format Export Demonstrations")
    print("=" * 70)
    print("\nThis script demonstrates Gmsh MSH format export capabilities.")
    print("Output files will be created in: gmsh_export_examples/")

    try:
        # Run all demos
        demo_1_basic_hex8()
        demo_2_tet4_mesh()
        demo_3_hex20_quadratic()
        demo_4_mixed_elements()
        demo_5_msh_v4()
        demo_6_physical_groups()
        demo_7_complete_mesh()

        print("\n" + "=" * 70)
        print("All Demonstrations Completed Successfully!")
        print("=" * 70)
        print("\nGenerated files:")
        print("  - gmsh_export_examples/demo1_hex8.msh")
        print("  - gmsh_export_examples/demo2_tet4.msh")
        print("  - gmsh_export_examples/demo3_hex20.msh")
        print("  - gmsh_export_examples/demo4_mixed.msh")
        print("  - gmsh_export_examples/demo5_msh41.msh")
        print("  - gmsh_export_examples/demo6_physical_groups.msh")
        print("  - gmsh_export_examples/demo7_complete_v2.msh")
        print("  - gmsh_export_examples/demo7_complete_v4.msh")
        print("\nThese files can be opened in:")
        print("  - Gmsh (open-source mesh generator)")
        print("  - GetDP (finite element solver)")
        print("  - Code_Aster (structural analysis)")
        print("  - FreeCAD (CAD/CAM)")
        print("  - ParaView (with Gmsh reader plugin)")
        print()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
