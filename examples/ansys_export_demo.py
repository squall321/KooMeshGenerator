"""
ANSYS Export Demonstration
===========================

This script demonstrates the ANSYS export functionality with various examples:

1. Basic HEX8 mesh export
2. Quadratic element export (HEX20)
3. TET4 mesh export
4. Complete model with material properties
5. Multi-element type model
6. Component (group) definitions
7. Advanced features (multiple materials, components)

Run this script to generate example ANSYS .cdb files:
    python examples/ansys_export_demo.py
"""

import numpy as np
from pathlib import Path

from koomesh.meshing.mesh_data import MeshData, ElementType, Node, Element
from koomesh.export.ansys_writer import ANSYSWriter


def demo_1_basic_hex8_export():
    """
    Demo 1: Basic HEX8 mesh export
    ===============================

    Creates a simple 2x2x2 grid of HEX8 elements and exports to ANSYS format.
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

    # Export to ANSYS
    output_path = "demo1_basic_hex8.cdb"
    with ANSYSWriter(output_path) as writer:
        writer.write_complete_model(
            mesh,
            title="Basic HEX8 Grid",
            material_name="STEEL",
            youngs=210000.0,
            poisson=0.3,
            density=7.85e-9
        )

    print(f"✓ Exported to: {output_path}")
    print(f"  - Element type: SOLID185 (8-node hexahedron)")
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
        (0.5, 0.0, 0.0), (1.0, 0.5, 0.0), (0.5, 1.0, 0.0), (0.0, 0.5, 0.0),
        (0.5, 0.0, 1.0), (1.0, 0.5, 1.0), (0.5, 1.0, 1.0), (0.0, 0.5, 1.0),
        (0.0, 0.0, 0.5), (1.0, 0.0, 0.5), (1.0, 1.0, 0.5), (0.0, 1.0, 0.5)
    ]

    for i, (x, y, z) in enumerate(mid_edges, start=9):
        mesh.nodes[i] = Node(i, x, y, z)

    # Create element with all 20 nodes
    node_ids = list(range(1, 21))
    mesh.elements[1] = Element(1, ElementType.HEX20, node_ids)

    print(f"Created HEX20 mesh with {mesh.num_nodes()} nodes")

    # Export
    output_path = "demo2_hex20_quadratic.cdb"
    with ANSYSWriter(output_path, precision=13) as writer:
        writer.write_complete_model(
            mesh,
            title="Quadratic HEX20 Element",
            material_name="ALUMINUM",
            youngs=70000.0,
            poisson=0.33,
            density=2.7e-9
        )

    print(f"✓ Exported to: {output_path}")
    print(f"  - Element type: SOLID186 (20-node hexahedron)")
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
    mesh.nodes[5] = Node(5, 0.5, 0.0, 0.0)
    mesh.nodes[6] = Node(6, 0.25, 0.5, 0.0)
    mesh.nodes[7] = Node(7, 0.75, 0.5, 0.0)

    # Create tetrahedral elements
    mesh.elements[1] = Element(1, ElementType.TET4, [1, 2, 3, 4])
    mesh.elements[2] = Element(2, ElementType.TET4, [1, 5, 6, 4])
    mesh.elements[3] = Element(3, ElementType.TET4, [2, 7, 3, 4])

    print(f"Created TET4 mesh with {mesh.num_nodes()} nodes and {mesh.num_elements()} elements")

    # Export
    output_path = "demo3_tet4_mesh.cdb"
    with ANSYSWriter(output_path) as writer:
        writer.write_complete_model(
            mesh,
            title="TET4 Mesh",
            material_name="PLASTIC",
            youngs=3000.0,
            poisson=0.4,
            density=1.2e-9
        )

    print(f"✓ Exported to: {output_path}")
    print(f"  - Element type: SOLID285 (4-node tetrahedron)")
    print(f"  - Material: PLASTIC (E=3 GPa, ν=0.4)")


def demo_4_model_with_components():
    """
    Demo 4: Model with components (groups)
    =======================================

    Demonstrates creating node and element components for boundary conditions.
    """
    print("\n" + "="*70)
    print("Demo 4: Model with Components")
    print("="*70)

    # Create a 1x1x3 column of hex elements
    mesh = MeshData(element_type=ElementType.HEX8)

    # Nodes for 3 stacked cubes
    node_id = 1
    for k in range(4):
        for j in range(2):
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

    # Export with components
    output_path = "demo4_model_with_components.cdb"
    with ANSYSWriter(output_path) as writer:
        # Header
        writer.write_header(
            "Column with Boundary Conditions",
            comments=["Fixed bottom, load on top"]
        )

        # Element type
        writer.write_element_types(mesh, et_id=1)

        # Nodes and elements
        writer.write_nodes(mesh)
        writer.write_elements(mesh, et_id=1, mat_id=1)

        # Create node components for boundary conditions
        bottom_nodes = [1, 2, 3, 4]  # Bottom layer
        top_nodes = [13, 14, 15, 16]  # Top layer

        writer.write_component("FIXED_BOTTOM", "NODE", bottom_nodes)
        writer.write_component("LOAD_TOP", "NODE", top_nodes)

        # Create element components
        writer.write_component("BOTTOM_ELEM", "ELEM", [1])
        writer.write_component("MIDDLE_ELEM", "ELEM", [2])
        writer.write_component("TOP_ELEM", "ELEM", [3])

        # Material
        writer.write_material(
            "CONCRETE",
            mat_id=1,
            youngs=30000.0,
            poisson=0.2,
            density=2.4e-9,
            comments=["Concrete C30/37"]
        )

        writer.file.write("FINISH\n")

    print(f"✓ Exported to: {output_path}")
    print(f"  - Node components: FIXED_BOTTOM (4 nodes), LOAD_TOP (4 nodes)")
    print(f"  - Element components: BOTTOM_ELEM, MIDDLE_ELEM, TOP_ELEM")
    print(f"  - Material: CONCRETE (E=30 GPa, ν=0.2)")


def demo_5_multiple_element_types():
    """
    Demo 5: Multiple element types in one model
    ============================================

    Demonstrates exporting different element types (not in same mesh object).
    Shows how to handle multiple meshes.
    """
    print("\n" + "="*70)
    print("Demo 5: Multiple Element Types")
    print("="*70)

    # Mesh 1: HEX8
    mesh_hex = MeshData(element_type=ElementType.HEX8)
    for i in range(8):
        x = float(i % 2)
        y = float((i // 2) % 2)
        z = float(i // 4)
        mesh_hex.nodes[i+1] = Node(i+1, x, y, z)
    mesh_hex.elements[1] = Element(1, ElementType.HEX8, list(range(1, 9)))

    # Mesh 2: TET4 (offset nodes)
    mesh_tet = MeshData(element_type=ElementType.TET4)
    mesh_tet.nodes[9] = Node(9, 2.0, 0.0, 0.0)
    mesh_tet.nodes[10] = Node(10, 3.0, 0.0, 0.0)
    mesh_tet.nodes[11] = Node(11, 2.5, 1.0, 0.0)
    mesh_tet.nodes[12] = Node(12, 2.5, 0.5, 1.0)
    mesh_tet.elements[2] = Element(2, ElementType.TET4, [9, 10, 11, 12])

    print(f"Mesh 1 (HEX8): {mesh_hex.num_elements()} element")
    print(f"Mesh 2 (TET4): {mesh_tet.num_elements()} element")

    # Export both meshes
    output_path = "demo5_multi_element_types.cdb"
    with ANSYSWriter(output_path) as writer:
        writer.write_header("Multi-Element Type Model")

        # Element types
        writer.write_element_types(mesh_hex, et_id=1)  # SOLID185
        writer.write_element_types(mesh_tet, et_id=2)  # SOLID285

        # Write HEX8 nodes and elements
        writer.write_nodes(mesh_hex)
        writer.write_elements(mesh_hex, et_id=1, mat_id=1)

        # Write TET4 nodes (manually since it's a different mesh)
        for node in mesh_tet.nodes.values():
            pass  # Already have all nodes, but in real case would add

        # For this demo, manually write TET4 nodes
        writer.file.write("NBLOCK,6,SOLID,12,9\n")
        writer.file.write("(1i9,3e20.13)\n")
        for node in mesh_tet.nodes.values():
            line = f"{node.id:9d}{node.x:20.13e}{node.y:20.13e}{node.z:20.13e}\n"
            writer.file.write(line)
        writer.file.write("N,R5.3,LOC,       -1,\n")

        # Write TET4 elements
        writer.write_elements(mesh_tet, et_id=2, mat_id=2)

        # Materials
        writer.write_material("STEEL", mat_id=1, youngs=210000.0, poisson=0.3)
        writer.write_material("ALUMINUM", mat_id=2, youngs=70000.0, poisson=0.33)

        writer.file.write("FINISH\n")

    print(f"✓ Exported to: {output_path}")
    print(f"  - Element Type 1: SOLID185 (HEX8)")
    print(f"  - Element Type 2: SOLID285 (TET4)")


def demo_6_advanced_features():
    """
    Demo 6: Advanced features - multiple materials, components
    ===========================================================

    Comprehensive example showing all advanced features.
    """
    print("\n" + "="*70)
    print("Demo 6: Advanced Features")
    print("="*70)

    # Create a complex mesh (2x2x2)
    mesh = MeshData(element_type=ElementType.HEX8)

    node_id = 1
    for k in range(3):
        for j in range(3):
            for i in range(3):
                x, y, z = float(i), float(j), float(k)
                mesh.nodes[node_id] = Node(node_id, x, y, z)
                node_id += 1

    # Create 8 elements
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
    output_path = "demo6_advanced_features.cdb"
    with ANSYSWriter(output_path) as writer:
        writer.write_header(
            "Advanced Features Demo",
            comments=[
                "Multiple materials",
                "Complex components",
                "Layered structure"
            ]
        )

        # Element types
        writer.write_element_types(mesh, et_id=1)

        # Nodes and elements
        writer.write_nodes(mesh)

        # Write bottom layer with mat_id=1
        bottom_elems = [1, 2, 3, 4]
        for elem_id in bottom_elems:
            elem = mesh.elements[elem_id]
            # Write individual element with mat 1
            pass  # In real implementation would set material per element

        # For simplicity, write all elements with same mat
        writer.write_elements(mesh, et_id=1, mat_id=1)

        # Define components by layers
        bottom_nodes = [1, 2, 3, 4, 5, 6, 7, 8, 9]  # Z=0
        middle_nodes = [10, 11, 12, 13, 14, 15, 16, 17, 18]  # Z=1
        top_nodes = [19, 20, 21, 22, 23, 24, 25, 26, 27]  # Z=2

        writer.write_component("NODES_BOTTOM", "NODE", bottom_nodes)
        writer.write_component("NODES_MIDDLE", "NODE", middle_nodes)
        writer.write_component("NODES_TOP", "NODE", top_nodes)

        # Element components
        writer.write_component("LAYER_BOTTOM", "ELEM", [1, 2, 3, 4])
        writer.write_component("LAYER_TOP", "ELEM", [5, 6, 7, 8])

        # Multiple materials
        writer.write_material(
            "STEEL",
            mat_id=1,
            youngs=210000.0,
            poisson=0.3,
            density=7.85e-9,
            comments=["AISI 4140 Steel"]
        )

        writer.write_material(
            "TITANIUM",
            mat_id=2,
            youngs=110000.0,
            poisson=0.34,
            density=4.5e-9,
            comments=["Ti-6Al-4V Grade 5"]
        )

        writer.file.write("/COM,\n")
        writer.file.write("/COM,  End of advanced features demo\n")
        writer.file.write("FINISH\n")

    print(f"✓ Exported to: {output_path}")
    print(f"  - 2 materials: STEEL, TITANIUM")
    print(f"  - Multiple node/element components")
    print(f"  - Layered structure")


def main():
    """Run all demos"""
    print("\n" + "="*70)
    print("ANSYS EXPORT DEMONSTRATION")
    print("="*70)
    print("\nThis script will create 6 example ANSYS .cdb files demonstrating")
    print("various export capabilities.\n")

    # Create output directory
    output_dir = Path("ansys_export_examples")
    output_dir.mkdir(exist_ok=True)
    import os
    os.chdir(output_dir)

    # Run all demos
    demo_1_basic_hex8_export()
    demo_2_quadratic_hex20_export()
    demo_3_tet4_mesh_export()
    demo_4_model_with_components()
    demo_5_multiple_element_types()
    demo_6_advanced_features()

    print("\n" + "="*70)
    print("ALL DEMOS COMPLETED")
    print("="*70)
    print(f"\nGenerated files are in: {output_dir.absolute()}")
    print("\nYou can import these .cdb files into ANSYS Mechanical APDL using:")
    print("  /INPUT,demo1_basic_hex8,cdb")
    print("\nOr open in Workbench:")
    print("  External Model → Browse → Select .cdb file")


if __name__ == "__main__":
    main()
