"""
ABAQUS Export Demonstration
============================

This script demonstrates the ABAQUS export functionality with various examples:

1. Basic HEX8 mesh export
2. Quadratic element export (HEX20)
3. TET4 mesh export
4. Complete model with material properties
5. Multi-part assembly
6. Contact definition between parts
7. Advanced features (sets, surfaces, sections)

Run this script to generate example ABAQUS .inp files:
    python examples/abaqus_export_demo.py
"""

import numpy as np
from pathlib import Path

from koomesh.meshing.mesh_data import MeshData, ElementType, Node, Element
from koomesh.export.abaqus_writer import AbaqusWriter


def demo_1_basic_hex8_export():
    """
    Demo 1: Basic HEX8 mesh export
    ==============================

    Creates a simple 2x2x2 grid of HEX8 elements and exports to ABAQUS format.
    """
    print("\n" + "="*70)
    print("Demo 1: Basic HEX8 Export")
    print("="*70)

    # Create mesh
    mesh = MeshData(element_type=ElementType.HEX8)

    # Create 3x3x3 grid of nodes (27 nodes)
    node_id = 1
    for k in range(3):
        for j in range(3):
            for i in range(3):
                x, y, z = float(i), float(j), float(k)
                mesh.nodes[node_id] = Node(node_id, x, y, z)
                node_id += 1

    # Create 2x2x2 grid of elements (8 elements)
    elem_id = 1
    for k in range(2):
        for j in range(2):
            for i in range(2):
                # Calculate node indices for this element
                n1 = 1 + i + j*3 + k*9
                n2 = n1 + 1
                n3 = n2 + 3
                n4 = n1 + 3
                n5 = n1 + 9
                n6 = n2 + 9
                n7 = n3 + 9
                n8 = n4 + 9

                mesh.elements[elem_id] = Element(
                    elem_id, ElementType.HEX8, [n1, n2, n3, n4, n5, n6, n7, n8]
                )
                elem_id += 1

    print(f"Created mesh with {mesh.num_nodes()} nodes and {mesh.num_elements()} elements")

    # Export to ABAQUS
    output_path = "demo1_basic_hex8.inp"
    with AbaqusWriter(output_path) as writer:
        writer.write_complete_model(
            mesh,
            model_name="Basic HEX8 Grid",
            material_name="STEEL",
            youngs=210000.0,
            poisson=0.3,
            density=7.85e-9
        )

    print(f"✓ Exported to: {output_path}")
    print(f"  - Element type: C3D8")
    print(f"  - Material: STEEL (E=210 GPa, ν=0.3)")


def demo_2_quadratic_hex20_export():
    """
    Demo 2: Quadratic HEX20 element export
    =======================================

    Creates a single HEX20 element with mid-side nodes.
    """
    print("\n" + "="*70)
    print("Demo 2: Quadratic HEX20 Export")
    print("="*70)

    mesh = MeshData(element_type=ElementType.HEX20)

    # 8 corner nodes (unit cube)
    corners = [
        (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 1.0, 0.0), (0.0, 1.0, 0.0),
        (0.0, 0.0, 1.0), (1.0, 0.0, 1.0), (1.0, 1.0, 1.0), (0.0, 1.0, 1.0)
    ]

    for i, (x, y, z) in enumerate(corners, start=1):
        mesh.nodes[i] = Node(i, x, y, z)

    # 12 mid-edge nodes
    mid_edges = [
        (0.5, 0.0, 0.0), (1.0, 0.5, 0.0), (0.5, 1.0, 0.0), (0.0, 0.5, 0.0),  # Bottom edges
        (0.5, 0.0, 1.0), (1.0, 0.5, 1.0), (0.5, 1.0, 1.0), (0.0, 0.5, 1.0),  # Top edges
        (0.0, 0.0, 0.5), (1.0, 0.0, 0.5), (1.0, 1.0, 0.5), (0.0, 1.0, 0.5)   # Vertical edges
    ]

    for i, (x, y, z) in enumerate(mid_edges, start=9):
        mesh.nodes[i] = Node(i, x, y, z)

    # Create element with all 20 nodes
    node_ids = list(range(1, 21))
    mesh.elements[1] = Element(1, ElementType.HEX20, node_ids)

    print(f"Created HEX20 mesh with {mesh.num_nodes()} nodes")

    # Export with high precision
    output_path = "demo2_hex20_quadratic.inp"
    with AbaqusWriter(output_path, precision=10) as writer:
        writer.write_complete_model(
            mesh,
            model_name="Quadratic HEX20 Element",
            material_name="ALUMINUM",
            youngs=70000.0,
            poisson=0.33,
            density=2.7e-9
        )

    print(f"✓ Exported to: {output_path}")
    print(f"  - Element type: C3D20 (20-node brick)")
    print(f"  - Precision: 10 decimal places")
    print(f"  - Material: ALUMINUM (E=70 GPa, ν=0.33)")


def demo_3_tet4_mesh_export():
    """
    Demo 3: TET4 mesh export
    =========================

    Creates a simple tetrahedral mesh.
    """
    print("\n" + "="*70)
    print("Demo 3: TET4 Mesh Export")
    print("="*70)

    mesh = MeshData(element_type=ElementType.TET4)

    # Create nodes for a pyramidal TET mesh
    mesh.nodes[1] = Node(1, 0.0, 0.0, 0.0)
    mesh.nodes[2] = Node(2, 1.0, 0.0, 0.0)
    mesh.nodes[3] = Node(3, 0.5, 1.0, 0.0)
    mesh.nodes[4] = Node(4, 0.5, 0.5, 1.0)

    # Additional nodes for more tets
    mesh.nodes[5] = Node(5, 0.5, 0.0, 0.0)
    mesh.nodes[6] = Node(6, 0.25, 0.5, 0.0)
    mesh.nodes[7] = Node(7, 0.75, 0.5, 0.0)

    # Create tetrahedral elements
    mesh.elements[1] = Element(1, ElementType.TET4, [1, 2, 3, 4])
    mesh.elements[2] = Element(2, ElementType.TET4, [1, 5, 6, 4])
    mesh.elements[3] = Element(3, ElementType.TET4, [2, 7, 3, 4])

    print(f"Created TET4 mesh with {mesh.num_nodes()} nodes and {mesh.num_elements()} elements")

    # Export with reduced integration option
    output_path = "demo3_tet4_mesh.inp"
    with AbaqusWriter(output_path, reduced_integration=True) as writer:
        writer.write_complete_model(
            mesh,
            model_name="TET4 Mesh",
            material_name="PLASTIC",
            youngs=3000.0,
            poisson=0.4,
            density=1.2e-9
        )

    print(f"✓ Exported to: {output_path}")
    print(f"  - Element type: C3D4")
    print(f"  - Material: PLASTIC (E=3 GPa, ν=0.4)")


def demo_4_complete_model_with_sets():
    """
    Demo 4: Complete model with node/element sets
    ==============================================

    Demonstrates creating node sets and element sets for boundary conditions.
    """
    print("\n" + "="*70)
    print("Demo 4: Complete Model with Sets")
    print("="*70)

    # Create a 1x1x3 column of hex elements
    mesh = MeshData(element_type=ElementType.HEX8)

    # Nodes for 3 stacked cubes (4x4 nodes = 16 nodes)
    node_id = 1
    for k in range(4):  # 4 layers
        for j in range(2):  # 2x2 grid
            for i in range(2):
                x, y, z = float(i), float(j), float(k)
                mesh.nodes[node_id] = Node(node_id, x, y, z)
                node_id += 1

    # Create 3 elements (column)
    for k in range(3):
        elem_id = k + 1
        offset = k * 4
        n1 = 1 + offset
        n2 = 2 + offset
        n3 = 4 + offset
        n4 = 3 + offset
        n5 = 5 + offset
        n6 = 6 + offset
        n7 = 8 + offset
        n8 = 7 + offset

        mesh.elements[elem_id] = Element(
            elem_id, ElementType.HEX8, [n1, n2, n3, n4, n5, n6, n7, n8]
        )

    print(f"Created column mesh: {mesh.num_nodes()} nodes, {mesh.num_elements()} elements")

    # Export with custom sets
    output_path = "demo4_model_with_sets.inp"
    with AbaqusWriter(output_path) as writer:
        # Header
        writer.write_header(
            "Column with Boundary Conditions",
            comments=["Fixed bottom, load on top"]
        )

        # Nodes and elements
        writer.write_nodes(mesh)
        writer.write_elements(mesh, "ALL_ELEMENTS")

        # Create node sets for boundary conditions
        bottom_nodes = [1, 2, 3, 4]  # Bottom layer
        top_nodes = [13, 14, 15, 16]  # Top layer

        writer.write_node_set(mesh, "FIXED_BOTTOM", bottom_nodes)
        writer.write_node_set(mesh, "LOAD_TOP", top_nodes)

        # Create element sets
        writer.write_element_set(mesh, "BOTTOM_ELEM", [1])
        writer.write_element_set(mesh, "MIDDLE_ELEM", [2])
        writer.write_element_set(mesh, "TOP_ELEM", [3])

        # Section and material
        writer.write_section("SECTION1", "ALL_ELEMENTS", "CONCRETE")
        writer.write_material(
            "CONCRETE",
            youngs=30000.0,
            poisson=0.2,
            density=2.4e-9,
            comments=["Concrete C30/37"]
        )

    print(f"✓ Exported to: {output_path}")
    print(f"  - Node sets: FIXED_BOTTOM (4 nodes), LOAD_TOP (4 nodes)")
    print(f"  - Element sets: BOTTOM_ELEM, MIDDLE_ELEM, TOP_ELEM")
    print(f"  - Material: CONCRETE (E=30 GPa, ν=0.2)")


def demo_5_multipart_assembly():
    """
    Demo 5: Multi-part assembly
    ============================

    Creates two separate parts and exports them with different materials.
    """
    print("\n" + "="*70)
    print("Demo 5: Multi-Part Assembly")
    print("="*70)

    # Part 1: Steel block
    part1 = MeshData(element_type=ElementType.HEX8)
    for i in range(8):
        x = float(i % 2)
        y = float((i // 2) % 2)
        z = float(i // 4)
        part1.nodes[i+1] = Node(i+1, x, y, z)

    part1.elements[1] = Element(1, ElementType.HEX8, [1, 2, 3, 4, 5, 6, 7, 8])

    # Part 2: Aluminum block (offset in Z)
    part2 = MeshData(element_type=ElementType.HEX8)
    for i in range(8):
        x = float(i % 2)
        y = float((i // 2) % 2)
        z = 1.0 + float(i // 4)  # Offset by 1.0 in Z
        part2.nodes[i+9] = Node(i+9, x, y, z)

    part2.elements[2] = Element(2, ElementType.HEX8, [9, 10, 11, 12, 13, 14, 15, 16])

    print(f"Part 1: {part1.num_elements()} element (Steel)")
    print(f"Part 2: {part2.num_elements()} element (Aluminum)")

    # Export assembly
    output_path = "demo5_multipart_assembly.inp"
    with AbaqusWriter(output_path) as writer:
        writer.write_header("Two-Part Assembly")

        # Write nodes from both parts
        writer.write_nodes(part1)
        for node in part2.nodes.values():
            line = f"{node.id}, {node.x:.8e}, {node.y:.8e}, {node.z:.8e}\n"
            writer.file.write(line)

        # Write elements for part 1
        writer.write_elements(part1, "PART1_STEEL")

        # Write elements for part 2
        writer.write_elements(part2, "PART2_ALUMINUM")

        # Sections and materials
        writer.write_section("SEC_STEEL", "PART1_STEEL", "STEEL")
        writer.write_section("SEC_ALUM", "PART2_ALUMINUM", "ALUMINUM")

        writer.write_material("STEEL", youngs=210000.0, poisson=0.3, density=7.85e-9)
        writer.write_material("ALUMINUM", youngs=70000.0, poisson=0.33, density=2.7e-9)

    print(f"✓ Exported to: {output_path}")
    print(f"  - Part 1: STEEL (1 element)")
    print(f"  - Part 2: ALUMINUM (1 element)")


def demo_6_contact_definition():
    """
    Demo 6: Contact definition between surfaces
    ============================================

    Demonstrates surface and contact pair definition.
    """
    print("\n" + "="*70)
    print("Demo 6: Contact Definition")
    print("="*70)

    # Create two blocks that should be in contact
    mesh1 = MeshData(element_type=ElementType.HEX8)
    mesh2 = MeshData(element_type=ElementType.HEX8)

    # Block 1 (bottom)
    for i in range(8):
        x = float(i % 2)
        y = float((i // 2) % 2)
        z = float(i // 4)
        mesh1.nodes[i+1] = Node(i+1, x, y, z)

    mesh1.elements[1] = Element(1, ElementType.HEX8, [1, 2, 3, 4, 5, 6, 7, 8])

    # Block 2 (top, with small gap)
    gap = 0.01
    for i in range(8):
        x = float(i % 2)
        y = float((i // 2) % 2)
        z = 1.0 + gap + float(i // 4)
        mesh2.nodes[i+9] = Node(i+9, x, y, z)

    mesh2.elements[2] = Element(2, ElementType.HEX8, [9, 10, 11, 12, 13, 14, 15, 16])

    print(f"Created two blocks with gap = {gap}")

    # Export with contact
    output_path = "demo6_contact_definition.inp"
    with AbaqusWriter(output_path) as writer:
        writer.write_header("Contact Analysis Model")

        # Nodes and elements
        writer.write_nodes(mesh1)
        for node in mesh2.nodes.values():
            line = f"{node.id}, {node.x:.8e}, {node.y:.8e}, {node.z:.8e}\n"
            writer.file.write(line)

        writer.write_elements(mesh1, "BLOCK1")
        writer.write_elements(mesh2, "BLOCK2")

        # Define surfaces
        writer.write_surface("SURF_BLOCK1_TOP", "BLOCK1", "S2")  # Top surface
        writer.write_surface("SURF_BLOCK2_BOTTOM", "BLOCK2", "S1")  # Bottom surface

        # Define contact pair with friction
        writer.write_contact_pair(
            "CONTACT_BLOCKS",
            "SURF_BLOCK1_TOP",  # Master
            "SURF_BLOCK2_BOTTOM",  # Slave
            friction=0.3
        )

        # Sections and material
        writer.write_section("SEC1", "BLOCK1", "STEEL")
        writer.write_section("SEC2", "BLOCK2", "STEEL")
        writer.write_material("STEEL", youngs=210000.0, poisson=0.3, density=7.85e-9)

    print(f"✓ Exported to: {output_path}")
    print(f"  - Surfaces: SURF_BLOCK1_TOP, SURF_BLOCK2_BOTTOM")
    print(f"  - Contact: CONTACT_BLOCKS (friction μ=0.3)")


def demo_7_advanced_features():
    """
    Demo 7: Advanced features - ties, multiple materials, complex geometry
    =======================================================================

    Comprehensive example showing all advanced features.
    """
    print("\n" + "="*70)
    print("Demo 7: Advanced Features")
    print("="*70)

    # Create a more complex mesh
    mesh = MeshData(element_type=ElementType.HEX8)

    # 2x2x2 mesh
    node_id = 1
    for k in range(3):
        for j in range(3):
            for i in range(3):
                x, y, z = float(i), float(j), float(k)
                mesh.nodes[node_id] = Node(node_id, x, y, z)
                node_id += 1

    # Create 8 elements (2x2x2 grid)
    elem_id = 1
    for k in range(2):
        for j in range(2):
            for i in range(2):
                n1 = 1 + i + j*3 + k*9
                n2 = n1 + 1
                n3 = n2 + 3
                n4 = n1 + 3
                n5 = n1 + 9
                n6 = n2 + 9
                n7 = n3 + 9
                n8 = n4 + 9

                mesh.elements[elem_id] = Element(
                    elem_id, ElementType.HEX8, [n1, n2, n3, n4, n5, n6, n7, n8]
                )
                elem_id += 1

    print(f"Created complex mesh: {mesh.num_nodes()} nodes, {mesh.num_elements()} elements")

    # Export with all features
    output_path = "demo7_advanced_features.inp"
    with AbaqusWriter(output_path, precision=12) as writer:
        writer.write_header(
            "Advanced Features Demo",
            comments=[
                "Multiple materials",
                "Complex sets",
                "Surfaces and ties",
                "High precision output"
            ]
        )

        # Nodes and elements
        writer.write_nodes(mesh)
        writer.write_elements(mesh, "ALL_ELEMENTS")

        # Define multiple element sets (by layers)
        bottom_layer = [1, 2, 3, 4]
        top_layer = [5, 6, 7, 8]

        writer.write_element_set(mesh, "LAYER_BOTTOM", bottom_layer)
        writer.write_element_set(mesh, "LAYER_TOP", top_layer)

        # Define node sets for each face
        bottom_nodes = [1, 2, 3, 4, 5, 6, 7, 8, 9]  # Z=0
        top_nodes = [19, 20, 21, 22, 23, 24, 25, 26, 27]  # Z=2

        writer.write_node_set(mesh, "NODES_BOTTOM", bottom_nodes)
        writer.write_node_set(mesh, "NODES_TOP", top_nodes)

        # Sections with different materials
        writer.write_section("SEC_BOTTOM", "LAYER_BOTTOM", "STEEL")
        writer.write_section("SEC_TOP", "LAYER_TOP", "TITANIUM")

        # Materials
        writer.write_material(
            "STEEL",
            youngs=210000.0,
            poisson=0.3,
            density=7.85e-9,
            comments=["AISI 4140 Steel"]
        )

        writer.write_material(
            "TITANIUM",
            youngs=110000.0,
            poisson=0.34,
            density=4.5e-9,
            comments=["Ti-6Al-4V Grade 5"]
        )

        # Define surfaces
        writer.write_surface("SURF_INTERFACE", "LAYER_BOTTOM", "S2")
        writer.write_surface("SURF_TOP_INTERFACE", "LAYER_TOP", "S1")

        # Tie constraint (bonded interface)
        writer.write_tie_constraint("TIE_LAYERS", "SURF_INTERFACE", "SURF_TOP_INTERFACE")

        writer.file.write("**\n")
        writer.file.write("** End of advanced features demo\n")

    print(f"✓ Exported to: {output_path}")
    print(f"  - 2 materials: STEEL, TITANIUM")
    print(f"  - 2 layers with different sections")
    print(f"  - Tied interface between layers")
    print(f"  - Precision: 12 decimal places")


def main():
    """Run all demos"""
    print("\n" + "="*70)
    print("ABAQUS EXPORT DEMONSTRATION")
    print("="*70)
    print("\nThis script will create 7 example ABAQUS .inp files demonstrating")
    print("various export capabilities.\n")

    # Create output directory
    output_dir = Path("abaqus_export_examples")
    output_dir.mkdir(exist_ok=True)
    import os
    os.chdir(output_dir)

    # Run all demos
    demo_1_basic_hex8_export()
    demo_2_quadratic_hex20_export()
    demo_3_tet4_mesh_export()
    demo_4_complete_model_with_sets()
    demo_5_multipart_assembly()
    demo_6_contact_definition()
    demo_7_advanced_features()

    print("\n" + "="*70)
    print("ALL DEMOS COMPLETED")
    print("="*70)
    print(f"\nGenerated files are in: {output_dir.absolute()}")
    print("\nYou can import these .inp files into ABAQUS/CAE using:")
    print("  File → Import → Model...")
    print("\nOr run from command line:")
    print("  abaqus job=demo1_basic_hex8 interactive")


if __name__ == "__main__":
    main()
