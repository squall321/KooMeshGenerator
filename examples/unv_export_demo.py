"""
Universal File Format (UNV) Export Demo
========================================

This demo shows how to export meshes to Universal File Format (.unv).

Universal File Format (.unv) is a widely-used ASCII-based format:
- Originally from I-DEAS
- Supported by many FEA tools (ANSYS, ABAQUS, Nastran, Femap, etc.)
- Dataset-based structure
- Easy to read and edit

Features demonstrated:
1. Basic HEX8 mesh export
2. TET4 mesh export
3. Mesh with groups (node sets and element sets)
4. All element types (HEX8, HEX20, TET4, TET10, PRISM6, PYRAMID5)
5. Multiple groups
6. Custom units

UNV files can be imported into:
- ANSYS
- ABAQUS
- Nastran
- Femap
- Patran
- Many other FEA pre/post processors
"""

from pathlib import Path
from koomesh.meshing.mesh_data import MeshData, Node, Element, ElementType
from koomesh.export.unv_writer import UNVWriter


# Create output directory
output_dir = Path("unv_export_examples")
output_dir.mkdir(exist_ok=True)


# ============================================================================
# Demo 1: Basic HEX8 Mesh
# ============================================================================

def demo_1_basic_hex8():
    """Export a basic HEX8 mesh"""
    print("\n" + "="*70)
    print("Demo 1: Basic HEX8 Mesh")
    print("="*70)

    # Create mesh with 2x2x2 elements
    mesh = MeshData(element_type=ElementType.HEX8)

    # Create nodes (3x3x3 grid)
    node_id = 1
    for i in range(3):
        for j in range(3):
            for k in range(3):
                x, y, z = float(i) * 10.0, float(j) * 10.0, float(k) * 10.0
                mesh.nodes[node_id] = Node(node_id, x, y, z)
                node_id += 1

    # Create 8 elements (2x2x2 grid)
    elem_id = 1
    for i in range(2):
        for j in range(2):
            for k in range(2):
                # Calculate corner nodes for this element
                n1 = i * 9 + j * 3 + k + 1
                n2 = n1 + 1
                n3 = n1 + 3
                n4 = n1 + 4
                n5 = n1 + 9
                n6 = n5 + 1
                n7 = n5 + 3
                n8 = n5 + 4

                mesh.elements[elem_id] = Element(
                    elem_id, ElementType.HEX8, [n1, n2, n4, n3, n5, n6, n8, n7]
                )
                elem_id += 1

    # Write to UNV file
    output_file = output_dir / "demo_1_basic_hex8.unv"
    with UNVWriter(output_file) as writer:
        writer.write_complete_model(mesh, title="Demo 1: Basic HEX8 Mesh")

    print(f"✓ Created: {output_file}")
    print(f"  - Nodes: {mesh.num_nodes()}")
    print(f"  - Elements: {mesh.num_elements()}")
    print(f"  - Element Type: HEX8 (UNV type 115)")
    print(f"  - Datasets: 164 (Units), 2411 (Nodes), 2412 (Elements)")
    print(f"  - Can be imported into: ANSYS, ABAQUS, Femap, Patran")


# ============================================================================
# Demo 2: TET4 Mesh
# ============================================================================

def demo_2_tet4():
    """Export TET4 mesh"""
    print("\n" + "="*70)
    print("Demo 2: TET4 Mesh")
    print("="*70)

    # Create TET4 mesh
    mesh = MeshData(element_type=ElementType.TET4)

    # Create nodes in a simple pattern
    mesh.nodes[1] = Node(1, 0.0, 0.0, 0.0)
    mesh.nodes[2] = Node(2, 10.0, 0.0, 0.0)
    mesh.nodes[3] = Node(3, 5.0, 10.0, 0.0)
    mesh.nodes[4] = Node(4, 5.0, 5.0, 10.0)
    mesh.nodes[5] = Node(5, 15.0, 5.0, 5.0)
    mesh.nodes[6] = Node(6, 10.0, 10.0, 5.0)

    # Create 4 tet elements
    mesh.elements[1] = Element(1, ElementType.TET4, [1, 2, 3, 4])
    mesh.elements[2] = Element(2, ElementType.TET4, [2, 5, 3, 4])
    mesh.elements[3] = Element(3, ElementType.TET4, [3, 5, 6, 4])
    mesh.elements[4] = Element(4, ElementType.TET4, [2, 5, 6, 3])

    # Write to UNV file
    output_file = output_dir / "demo_2_tet4.unv"
    with UNVWriter(output_file) as writer:
        writer.write_complete_model(mesh, title="Demo 2: TET4 Mesh")

    print(f"✓ Created: {output_file}")
    print(f"  - Nodes: {mesh.num_nodes()}")
    print(f"  - Elements: {mesh.num_elements()}")
    print(f"  - Element Type: TET4 (UNV type 111)")
    print(f"  - Good for: Complex geometries, automatic meshing")


# ============================================================================
# Demo 3: Mesh with Groups (Node and Element Sets)
# ============================================================================

def demo_3_with_groups():
    """Export mesh with node and element groups"""
    print("\n" + "="*70)
    print("Demo 3: Mesh with Groups")
    print("="*70)

    # Create mesh
    mesh = MeshData(element_type=ElementType.HEX8)

    # Create nodes (4x2x2 grid for beam-like structure)
    node_id = 1
    for i in range(5):
        for j in range(2):
            for k in range(2):
                x = float(i) * 10.0
                y = float(j) * 2.0
                z = float(k) * 2.0
                mesh.nodes[node_id] = Node(node_id, x, y, z)
                node_id += 1

    # Create 4 elements
    for i in range(4):
        elem_id = i + 1
        base = i * 4 + 1
        nodes = [
            base, base + 1, base + 3, base + 2,
            base + 4, base + 5, base + 7, base + 6
        ]
        mesh.elements[elem_id] = Element(elem_id, ElementType.HEX8, nodes)

    # Write mesh with groups
    output_file = output_dir / "demo_3_with_groups.unv"
    with UNVWriter(output_file) as writer:
        writer.write_complete_model(mesh, title="Demo 3: Mesh with Groups")

        # Add node groups (for boundary conditions)
        fixed_nodes = [1, 2, 3, 4]  # Left end
        loaded_nodes = [17, 18, 19, 20]  # Right end

        writer.write_groups("FIXED_NODES", "NODE", fixed_nodes)
        writer.write_groups("LOADED_NODES", "NODE", loaded_nodes)

        # Add element groups (for materials/sections)
        part1_elems = [1, 2]  # First half
        part2_elems = [3, 4]  # Second half

        writer.write_groups("PART_1", "ELEMENT", part1_elems)
        writer.write_groups("PART_2", "ELEMENT", part2_elems)

    print(f"✓ Created: {output_file}")
    print(f"  - Node Groups:")
    print(f"    • FIXED_NODES: {len(fixed_nodes)} nodes (boundary conditions)")
    print(f"    • LOADED_NODES: {len(loaded_nodes)} nodes (applied loads)")
    print(f"  - Element Groups:")
    print(f"    • PART_1: {len(part1_elems)} elements")
    print(f"    • PART_2: {len(part2_elems)} elements")
    print(f"  - Dataset 2467: Permanent Groups")


# ============================================================================
# Demo 4: All Element Types
# ============================================================================

def demo_4_all_element_types():
    """Demonstrate all supported element types"""
    print("\n" + "="*70)
    print("Demo 4: All Element Types")
    print("="*70)

    element_types = [
        (ElementType.HEX8, "HEX8", 115, 8),
        (ElementType.HEX20, "HEX20", 116, 20),
        (ElementType.TET4, "TET4", 111, 4),
        (ElementType.TET10, "TET10", 118, 10),
        (ElementType.PRISM6, "PRISM6", 112, 6),
        (ElementType.PYRAMID5, "PYRAMID5", 117, 5),
    ]

    for elem_type, name, unv_code, num_nodes in element_types:
        mesh = MeshData(element_type=elem_type)

        # Create simplified nodes (just for demonstration)
        for i in range(num_nodes):
            x = float(i % 3)
            y = float((i // 3) % 3)
            z = float(i // 9)
            mesh.nodes[i+1] = Node(i+1, x, y, z)

        # Create single element
        mesh.elements[1] = Element(1, elem_type, list(range(1, num_nodes + 1)))

        # Export
        output_file = output_dir / f"demo_4_{name.lower()}.unv"
        UNVWriter.write_simple(mesh, str(output_file), title=f"{name} Element")

        print(f"  ✓ {name}: UNV type {unv_code} ({num_nodes} nodes)")

    print(f"\n  All element types exported to: {output_dir}/")


# ============================================================================
# Demo 5: Multiple Groups for Complex Models
# ============================================================================

def demo_5_multiple_groups():
    """Export mesh with multiple groups for different purposes"""
    print("\n" + "="*70)
    print("Demo 5: Multiple Groups for Complex Models")
    print("="*70)

    # Create 3x3x3 mesh
    mesh = MeshData(element_type=ElementType.HEX8)

    # Create nodes (4x4x4 grid)
    node_id = 1
    for i in range(4):
        for j in range(4):
            for k in range(4):
                mesh.nodes[node_id] = Node(node_id, float(i), float(j), float(k))
                node_id += 1

    # Create 27 elements (3x3x3)
    elem_id = 1
    for i in range(3):
        for j in range(3):
            for k in range(3):
                n1 = i * 16 + j * 4 + k + 1
                n2 = n1 + 1
                n3 = n1 + 4
                n4 = n1 + 5
                n5 = n1 + 16
                n6 = n5 + 1
                n7 = n5 + 4
                n8 = n5 + 5

                mesh.elements[elem_id] = Element(
                    elem_id, ElementType.HEX8, [n1, n2, n4, n3, n5, n6, n8, n7]
                )
                elem_id += 1

    # Write with many groups
    output_file = output_dir / "demo_5_multiple_groups.unv"
    with UNVWriter(output_file) as writer:
        writer.write_complete_model(mesh, title="Demo 5: Multiple Groups")

        # Boundary node groups (6 faces of the cube)
        bottom_nodes = [i for i in range(1, 17)]  # z=0
        top_nodes = [i for i in range(49, 65)]    # z=3
        left_nodes = [1, 2, 3, 4, 17, 18, 19, 20, 33, 34, 35, 36, 49, 50, 51, 52]  # x=0
        right_nodes = [13, 14, 15, 16, 29, 30, 31, 32, 45, 46, 47, 48, 61, 62, 63, 64]  # x=3

        writer.write_groups("BOTTOM_FACE", "NODE", bottom_nodes)
        writer.write_groups("TOP_FACE", "NODE", top_nodes)
        writer.write_groups("LEFT_FACE", "NODE", left_nodes)
        writer.write_groups("RIGHT_FACE", "NODE", right_nodes)

        # Element groups by layer
        layer1_elems = list(range(1, 10))   # Bottom layer
        layer2_elems = list(range(10, 19))  # Middle layer
        layer3_elems = list(range(19, 28))  # Top layer

        writer.write_groups("LAYER_1", "ELEMENT", layer1_elems)
        writer.write_groups("LAYER_2", "ELEMENT", layer2_elems)
        writer.write_groups("LAYER_3", "ELEMENT", layer3_elems)

    print(f"✓ Created: {output_file}")
    print(f"  - 8 groups total:")
    print(f"    • 4 node groups (boundary faces)")
    print(f"    • 3 element groups (layers)")
    print(f"  - Use cases:")
    print(f"    • Apply different boundary conditions per face")
    print(f"    • Assign different materials per layer")
    print(f"    • Monitor results by region")


# ============================================================================
# Demo 6: Imperial Units
# ============================================================================

def demo_6_imperial_units():
    """Export mesh with Imperial units"""
    print("\n" + "="*70)
    print("Demo 6: Imperial Units")
    print("="*70)

    # Create simple mesh
    mesh = MeshData(element_type=ElementType.HEX8)

    # Create single hex element
    for i, (x, y, z) in enumerate([
        (0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),
        (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)
    ], start=1):
        mesh.nodes[i] = Node(i, x, y, z)

    mesh.elements[1] = Element(1, ElementType.HEX8, [1, 2, 3, 4, 5, 6, 7, 8])

    # Write with Imperial units
    output_file = output_dir / "demo_6_imperial_units.unv"
    with UNVWriter(output_file, units="Imperial") as writer:
        writer.write_complete_model(mesh, title="Imperial Units Model", unit_code=2)

    print(f"✓ Created: {output_file}")
    print(f"  - Units: Imperial (inches, lbf, seconds, °F)")
    print(f"  - Unit code: 2")
    print(f"  - Dataset 164: Units specification")


# ============================================================================
# Main: Run All Demos
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("UNIVERSAL FILE FORMAT (UNV) EXPORT DEMONSTRATION")
    print("="*70)
    print("\nThis demo creates 6 sets of UNV files showing various features.")
    print(f"Output directory: {output_dir.absolute()}")

    # Run all demos
    demo_1_basic_hex8()
    demo_2_tet4()
    demo_3_with_groups()
    demo_4_all_element_types()
    demo_5_multiple_groups()
    demo_6_imperial_units()

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"✓ Created UNV files in {output_dir}/")
    print("\nKey Features Demonstrated:")
    print("  • Dataset-based ASCII format")
    print("  • All element types (HEX8, HEX20, TET4, TET10, PRISM6, PYRAMID5)")
    print("  • Node and element groups (Dataset 2467)")
    print("  • Units specification (Dataset 164)")
    print("  • Multiple groups for complex models")
    print("\nUNV Datasets Used:")
    print("  • 164: Units")
    print("  • 2411: Nodes (coordinates)")
    print("  • 2412: Elements (connectivity)")
    print("  • 2467: Permanent Groups (sets)")
    print("\nCompatible Software:")
    print("  • ANSYS Mechanical")
    print("  • ABAQUS")
    print("  • MSC Nastran / NX Nastran")
    print("  • Femap")
    print("  • Patran")
    print("  • Hypermesh")
    print("  • Many other FEA pre/post processors")
    print("\nFile Format:")
    print("  • ASCII text (easy to read/edit)")
    print("  • Dataset markers: -1 (start and end)")
    print("  • Fixed-width fields for numbers")
    print("  • Standard I-DEAS Universal File Format")
    print("\n" + "="*70)
