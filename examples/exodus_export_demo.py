"""
Exodus II Export Demonstration
================================

This script demonstrates the capabilities of the Exodus II format export functionality.

Exodus II is a widely-used binary format for finite element analysis developed by
Sandia National Laboratories. It uses netCDF4 as the underlying storage mechanism.

Demonstrations:
1. Basic HEX8 mesh export
2. TET4 mesh export
3. HEX20 quadratic element export
4. Mixed element types with auto element blocks
5. Custom element blocks with material regions
6. Node sets for boundary conditions
7. Side sets for surface conditions
8. Complete mesh with blocks, node sets, and side sets

Requirements:
- netCDF4 library (pip install netCDF4)
- KooMeshGenerator installed

Author: KooMeshGenerator Team
License: MIT
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from koomesh.meshing.mesh_data import MeshData, ElementType
from koomesh.export.exodus_writer import ExodusWriter, export_to_exodus

# Try to import netCDF4
try:
    from netCDF4 import Dataset
    NETCDF4_AVAILABLE = True
except ImportError:
    NETCDF4_AVAILABLE = False
    print("ERROR: netCDF4 is not installed. Install it with: pip install netCDF4")
    sys.exit(1)


def demo_1_basic_hex8():
    """Demo 1: Basic HEX8 mesh export"""
    print("\n" + "=" * 70)
    print("Demo 1: Basic HEX8 Mesh Export")
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
    output_file = "exodus_export_examples/demo1_hex8.exo"
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    with ExodusWriter(output_file, title="Demo 1: Basic HEX8 Mesh") as writer:
        writer.write_mesh(mesh)

    print(f"✓ Exported to: {output_file}")

    # Verify by reading back
    with Dataset(output_file, 'r') as ncfile:
        print(f"  - Title: {ncfile.title}")
        print(f"  - Nodes: {ncfile.dimensions['num_nodes'].size}")
        print(f"  - Elements: {ncfile.dimensions['num_elem'].size}")
        print(f"  - Element blocks: {ncfile.dimensions['num_el_blk'].size}")
        print(f"  - Element type: {ncfile.variables['connect1'].elem_type}")


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
    output_file = "exodus_export_examples/demo2_tet4.exo"
    success = export_to_exodus(mesh, output_file, title="Demo 2: TET4 Mesh")

    if success:
        print(f"✓ Exported to: {output_file}")

        # Verify
        with Dataset(output_file, 'r') as ncfile:
            print(f"  - Element type: {ncfile.variables['connect1'].elem_type}")


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
    output_file = "exodus_export_examples/demo3_hex20.exo"
    with ExodusWriter(output_file, title="Demo 3: HEX20 Quadratic") as writer:
        writer.write_mesh(mesh)

    print(f"✓ Exported to: {output_file}")

    # Verify
    with Dataset(output_file, 'r') as ncfile:
        print(f"  - Element type: {ncfile.variables['connect1'].elem_type}")
        print(f"  - Nodes per element: {ncfile.dimensions['num_nod_per_el1'].size}")


def demo_4_mixed_elements():
    """Demo 4: Mixed element types with auto element blocks"""
    print("\n" + "=" * 70)
    print("Demo 4: Mixed Element Types (Auto Element Blocks)")
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

    # Add nodes for PRISM6 (nodes 13-18)
    mesh.add_node(4.0, 0.0, 0.0, node_id=13)
    mesh.add_node(5.0, 0.0, 0.0, node_id=14)
    mesh.add_node(4.5, 1.0, 0.0, node_id=15)
    mesh.add_node(4.0, 0.0, 1.0, node_id=16)
    mesh.add_node(5.0, 0.0, 1.0, node_id=17)
    mesh.add_node(4.5, 1.0, 1.0, node_id=18)

    # Add HEX8 element
    mesh.add_element([1, 2, 3, 4, 5, 6, 7, 8], element_id=1, element_type=ElementType.HEX8)

    # Add TET4 element
    mesh.add_element([9, 10, 11, 12], element_id=2, element_type=ElementType.TET4)

    # Add PRISM6 element
    mesh.add_element([13, 14, 15, 16, 17, 18], element_id=3, element_type=ElementType.PRISM6)

    print(f"Created mesh: {mesh.num_nodes()} nodes, {mesh.num_elements()} elements")
    print("  - 1 HEX8, 1 TET4, 1 PRISM6")

    # Export (auto-creates element blocks by type)
    output_file = "exodus_export_examples/demo4_mixed.exo"
    with ExodusWriter(output_file, title="Demo 4: Mixed Element Types") as writer:
        writer.write_mesh(mesh)

    print(f"✓ Exported to: {output_file}")

    # Verify
    with Dataset(output_file, 'r') as ncfile:
        num_blocks = ncfile.dimensions['num_el_blk'].size
        print(f"  - Element blocks: {num_blocks}")
        for i in range(1, num_blocks + 1):
            elem_type = ncfile.variables[f'connect{i}'].elem_type
            num_elems = ncfile.dimensions[f'num_el_in_blk{i}'].size
            print(f"    Block {i}: {num_elems} {elem_type} element(s)")


def demo_5_custom_blocks():
    """Demo 5: Custom element blocks for material regions"""
    print("\n" + "=" * 70)
    print("Demo 5: Custom Element Blocks (Material Regions)")
    print("=" * 70)

    # Create mesh with multiple HEX8 elements
    mesh = MeshData(element_type=ElementType.HEX8)

    # Create 2x2x1 grid (4 cubes)
    for i in range(3):
        for j in range(3):
            for k in range(2):
                node_id = i * 6 + j * 2 + k + 1
                mesh.add_node(float(i), float(j), float(k), node_id=node_id)

    # Add 4 HEX8 elements
    # Element 1 (bottom-left)
    mesh.add_element([1, 3, 9, 7, 2, 4, 10, 8], element_id=1)
    # Element 2 (bottom-right)
    mesh.add_element([3, 5, 11, 9, 4, 6, 12, 10], element_id=2)
    # Element 3 (top-left)
    mesh.add_element([7, 9, 15, 13, 8, 10, 16, 14], element_id=3)
    # Element 4 (top-right)
    mesh.add_element([9, 11, 17, 15, 10, 12, 18, 16], element_id=4)

    print(f"Created mesh: {mesh.num_nodes()} nodes, {mesh.num_elements()} elements")

    # Define custom element blocks (e.g., different materials)
    element_blocks = {
        "steel": [1, 2],  # Bottom two elements
        "aluminum": [3, 4]  # Top two elements
    }

    print("  - Element blocks:")
    for name, elems in element_blocks.items():
        print(f"    {name}: elements {elems}")

    # Export
    output_file = "exodus_export_examples/demo5_custom_blocks.exo"
    with ExodusWriter(output_file, title="Demo 5: Custom Element Blocks") as writer:
        writer.write_mesh(mesh, element_blocks=element_blocks)

    print(f"✓ Exported to: {output_file}")

    # Verify
    with Dataset(output_file, 'r') as ncfile:
        num_blocks = ncfile.dimensions['num_el_blk'].size
        print(f"  - Verified element blocks: {num_blocks}")
        eb_names = ncfile.variables['eb_names']
        for i in range(num_blocks):
            name = b''.join(eb_names[i, :]).decode('ascii').rstrip('\x00')
            num_elems = ncfile.dimensions[f'num_el_in_blk{i+1}'].size
            print(f"    Block '{name}': {num_elems} elements")


def demo_6_node_sets():
    """Demo 6: Node sets for boundary conditions"""
    print("\n" + "=" * 70)
    print("Demo 6: Node Sets (Boundary Conditions)")
    print("=" * 70)

    # Create simple cube mesh
    mesh = MeshData(element_type=ElementType.HEX8)

    # Add nodes
    for i in range(2):
        for j in range(2):
            for k in range(2):
                node_id = i * 4 + j * 2 + k + 1
                mesh.add_node(float(i), float(j), float(k), node_id=node_id)

    # Add element
    mesh.add_element([1, 3, 7, 5, 2, 4, 8, 6], element_id=1)

    print(f"Created mesh: {mesh.num_nodes()} nodes, {mesh.num_elements()} elements")

    # Define node sets (for boundary conditions)
    node_sets = {
        "bottom": [1, 2, 3, 4],  # Z = 0
        "top": [5, 6, 7, 8],  # Z = 1
        "left": [1, 2, 5, 6],  # X = 0
        "right": [3, 4, 7, 8],  # X = 1
    }

    print("  - Node sets:")
    for name, nodes in node_sets.items():
        print(f"    {name}: {len(nodes)} nodes")

    # Export
    output_file = "exodus_export_examples/demo6_node_sets.exo"
    with ExodusWriter(output_file, title="Demo 6: Node Sets") as writer:
        writer.write_mesh(mesh, node_sets=node_sets)

    print(f"✓ Exported to: {output_file}")

    # Verify
    with Dataset(output_file, 'r') as ncfile:
        num_node_sets = ncfile.dimensions['num_node_sets'].size
        print(f"  - Verified node sets: {num_node_sets}")
        ns_names = ncfile.variables['ns_names']
        for i in range(num_node_sets):
            name = b''.join(ns_names[i, :]).decode('ascii').rstrip('\x00')
            num_nodes = ncfile.dimensions[f'num_nod_ns{i+1}'].size
            print(f"    Set '{name}': {num_nodes} nodes")


def demo_7_side_sets():
    """Demo 7: Side sets for surface conditions"""
    print("\n" + "=" * 70)
    print("Demo 7: Side Sets (Surface Conditions)")
    print("=" * 70)

    # Create simple cube mesh
    mesh = MeshData(element_type=ElementType.HEX8)

    # Add nodes
    for i in range(2):
        for j in range(2):
            for k in range(2):
                node_id = i * 4 + j * 2 + k + 1
                mesh.add_node(float(i), float(j), float(k), node_id=node_id)

    # Add element
    mesh.add_element([1, 3, 7, 5, 2, 4, 8, 6], element_id=1)

    print(f"Created mesh: {mesh.num_nodes()} nodes, {mesh.num_elements()} elements")

    # Define side sets (for surface conditions)
    # Side numbering: 1=bottom, 2=top, 3=front, 4=right, 5=back, 6=left
    side_sets = {
        "bottom_face": [(1, 1)],  # Element 1, Side 1
        "top_face": [(1, 2)],     # Element 1, Side 2
        "front_face": [(1, 3)],   # Element 1, Side 3
    }

    print("  - Side sets:")
    for name, sides in side_sets.items():
        print(f"    {name}: {len(sides)} side(s)")

    # Export
    output_file = "exodus_export_examples/demo7_side_sets.exo"
    with ExodusWriter(output_file, title="Demo 7: Side Sets") as writer:
        writer.write_mesh(mesh, side_sets=side_sets)

    print(f"✓ Exported to: {output_file}")

    # Verify
    with Dataset(output_file, 'r') as ncfile:
        num_side_sets = ncfile.dimensions['num_side_sets'].size
        print(f"  - Verified side sets: {num_side_sets}")
        ss_names = ncfile.variables['ss_names']
        for i in range(num_side_sets):
            name = b''.join(ss_names[i, :]).decode('ascii').rstrip('\x00')
            num_sides = ncfile.dimensions[f'num_side_ss{i+1}'].size
            print(f"    Set '{name}': {num_sides} side(s)")


def demo_8_complete_mesh():
    """Demo 8: Complete mesh with blocks, node sets, and side sets"""
    print("\n" + "=" * 70)
    print("Demo 8: Complete Mesh (Blocks + Node Sets + Side Sets)")
    print("=" * 70)

    # Create 2x1x1 mesh (2 cubes)
    mesh = MeshData(element_type=ElementType.HEX8)

    # Add nodes
    for i in range(3):
        for j in range(2):
            for k in range(2):
                node_id = i * 4 + j * 2 + k + 1
                mesh.add_node(float(i), float(j), float(k), node_id=node_id)

    # Add two elements
    mesh.add_element([1, 3, 7, 5, 2, 4, 8, 6], element_id=1)
    mesh.add_element([5, 7, 11, 9, 6, 8, 12, 10], element_id=2)

    print(f"Created mesh: {mesh.num_nodes()} nodes, {mesh.num_elements()} elements")

    # Define element blocks
    element_blocks = {
        "region_1": [1],
        "region_2": [2]
    }

    # Define node sets
    node_sets = {
        "fixed": [1, 2, 3, 4],  # Left face (fixed BC)
        "load": [9, 10, 11, 12]  # Right face (load BC)
    }

    # Define side sets
    side_sets = {
        "left_surface": [(1, 6)],  # Left surface
        "right_surface": [(2, 4)],  # Right surface
        "bottom": [(1, 1), (2, 1)]  # Bottom surface
    }

    print("  - Element blocks: 2")
    print("  - Node sets: 2")
    print("  - Side sets: 3")

    # Export complete mesh
    output_file = "exodus_export_examples/demo8_complete.exo"
    with ExodusWriter(output_file, title="Demo 8: Complete Mesh") as writer:
        writer.write_mesh(
            mesh,
            element_blocks=element_blocks,
            node_sets=node_sets,
            side_sets=side_sets
        )

    print(f"✓ Exported to: {output_file}")

    # Comprehensive verification
    with Dataset(output_file, 'r') as ncfile:
        print("\n  Verification:")
        print(f"    - Title: {ncfile.title}")
        print(f"    - Nodes: {ncfile.dimensions['num_nodes'].size}")
        print(f"    - Elements: {ncfile.dimensions['num_elem'].size}")
        print(f"    - Element blocks: {ncfile.dimensions['num_el_blk'].size}")
        print(f"    - Node sets: {ncfile.dimensions['num_node_sets'].size}")
        print(f"    - Side sets: {ncfile.dimensions['num_side_sets'].size}")
        print(f"    - API version: {ncfile.api_version}")
        print(f"    - Format: netCDF {ncfile.data_model}")


def main():
    """Run all demonstrations"""
    print("\n" + "=" * 70)
    print("Exodus II Export Demonstrations")
    print("=" * 70)
    print("\nThis script demonstrates Exodus II format export capabilities.")
    print("Output files will be created in: exodus_export_examples/")

    if not NETCDF4_AVAILABLE:
        return

    try:
        # Run all demos
        demo_1_basic_hex8()
        demo_2_tet4_mesh()
        demo_3_hex20_quadratic()
        demo_4_mixed_elements()
        demo_5_custom_blocks()
        demo_6_node_sets()
        demo_7_side_sets()
        demo_8_complete_mesh()

        print("\n" + "=" * 70)
        print("All Demonstrations Completed Successfully!")
        print("=" * 70)
        print("\nGenerated files:")
        print("  - exodus_export_examples/demo1_hex8.exo")
        print("  - exodus_export_examples/demo2_tet4.exo")
        print("  - exodus_export_examples/demo3_hex20.exo")
        print("  - exodus_export_examples/demo4_mixed.exo")
        print("  - exodus_export_examples/demo5_custom_blocks.exo")
        print("  - exodus_export_examples/demo6_node_sets.exo")
        print("  - exodus_export_examples/demo7_side_sets.exo")
        print("  - exodus_export_examples/demo8_complete.exo")
        print("\nThese files can be opened in:")
        print("  - ParaView (open-source visualization)")
        print("  - VisIt (scientific visualization)")
        print("  - CUBIT/Trelis (mesh generation)")
        print("  - Any Exodus II compatible tool")
        print()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
