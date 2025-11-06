"""
Nastran Export Demo
====================

This demo shows how to export meshes to Nastran Bulk Data format (.bdf).

Features demonstrated:
1. Basic HEX8 mesh export (large field format)
2. HEX8 mesh export with small field format
3. Quadratic HEX20 element export
4. TET4 tetrahedron mesh export
5. Complete model with material properties
6. Multi-part model with sets
7. Advanced mesh with properties and sets

Nastran Format Features:
- GRID entries for nodes (large/small field)
- CHEXA, CTETRA, CPENTA, CPYRAM element types
- MAT1 material properties
- PSOLID property definitions
- SET1 node/element sets
- Comment lines with $
"""

from pathlib import Path
from koomesh.meshing.mesh_data import MeshData, Node, Element, ElementType
from koomesh.export.nastran_writer import NastranWriter


# Create output directory
output_dir = Path("nastran_export_examples")
output_dir.mkdir(exist_ok=True)


# ============================================================================
# Demo 1: Basic HEX8 Mesh (Large Field Format)
# ============================================================================

def demo_1_basic_hex8():
    """Export a basic HEX8 mesh using large field format"""
    print("\n" + "="*70)
    print("Demo 1: Basic HEX8 Mesh (Large Field Format)")
    print("="*70)

    # Create mesh
    mesh = MeshData(element_type=ElementType.HEX8)

    # Create 12 nodes for 2 hex elements
    mesh.nodes[1] = Node(1, 0.0, 0.0, 0.0)
    mesh.nodes[2] = Node(2, 1.0, 0.0, 0.0)
    mesh.nodes[3] = Node(3, 1.0, 1.0, 0.0)
    mesh.nodes[4] = Node(4, 0.0, 1.0, 0.0)
    mesh.nodes[5] = Node(5, 0.0, 0.0, 1.0)
    mesh.nodes[6] = Node(6, 1.0, 0.0, 1.0)
    mesh.nodes[7] = Node(7, 1.0, 1.0, 1.0)
    mesh.nodes[8] = Node(8, 0.0, 1.0, 1.0)
    mesh.nodes[9] = Node(9, 2.0, 0.0, 0.0)
    mesh.nodes[10] = Node(10, 2.0, 1.0, 0.0)
    mesh.nodes[11] = Node(11, 2.0, 0.0, 1.0)
    mesh.nodes[12] = Node(12, 2.0, 1.0, 1.0)

    # Create 2 elements
    mesh.elements[1] = Element(1, ElementType.HEX8, [1, 2, 3, 4, 5, 6, 7, 8])
    mesh.elements[2] = Element(2, ElementType.HEX8, [2, 9, 10, 3, 6, 11, 12, 7])

    # Write to file using large field format (default)
    output_file = output_dir / "demo_1_basic_hex8_large.bdf"
    with NastranWriter(output_file, format='large') as writer:
        writer.write_complete_model(
            mesh=mesh,
            title="Demo 1: Basic HEX8 Mesh (Large Field)"
        )

    print(f"✓ Created: {output_file}")
    print(f"  - Nodes: {mesh.num_nodes()}")
    print(f"  - Elements: {mesh.num_elements()}")
    print(f"  - Element Type: {mesh.element_type.code} (CHEXA)")
    print(f"  - Field Format: Large (16 chars per field)")
    print(f"  - Features: GRID*, CHEXA*, MAT1*, PSOLID*")


# ============================================================================
# Demo 2: HEX8 Mesh with Small Field Format
# ============================================================================

def demo_2_small_field():
    """Export HEX8 mesh using small field format (8-char fields)"""
    print("\n" + "="*70)
    print("Demo 2: HEX8 Mesh (Small Field Format)")
    print("="*70)

    # Create simple mesh
    mesh = MeshData(element_type=ElementType.HEX8)

    # Single hex element
    mesh.nodes[1] = Node(1, 0.0, 0.0, 0.0)
    mesh.nodes[2] = Node(2, 1.0, 0.0, 0.0)
    mesh.nodes[3] = Node(3, 1.0, 1.0, 0.0)
    mesh.nodes[4] = Node(4, 0.0, 1.0, 0.0)
    mesh.nodes[5] = Node(5, 0.0, 0.0, 1.0)
    mesh.nodes[6] = Node(6, 1.0, 0.0, 1.0)
    mesh.nodes[7] = Node(7, 1.0, 1.0, 1.0)
    mesh.nodes[8] = Node(8, 0.0, 1.0, 1.0)

    mesh.elements[1] = Element(1, ElementType.HEX8, [1, 2, 3, 4, 5, 6, 7, 8])

    # Write using small field format
    output_file = output_dir / "demo_2_small_field.bdf"
    with NastranWriter(output_file, format='small', precision=6) as writer:
        writer.write_complete_model(
            mesh=mesh,
            title="Demo 2: Small Field Format"
        )

    print(f"✓ Created: {output_file}")
    print(f"  - Field Format: Small (8 chars per field)")
    print(f"  - Precision: 6 decimal places")
    print(f"  - More compact file size")
    print(f"  - Compatible with older Nastran versions")


# ============================================================================
# Demo 3: Quadratic HEX20 Elements
# ============================================================================

def demo_3_hex20():
    """Export quadratic HEX20 elements"""
    print("\n" + "="*70)
    print("Demo 3: Quadratic HEX20 Elements")
    print("="*70)

    # Create HEX20 mesh
    mesh = MeshData(element_type=ElementType.HEX20)

    # 8 corner nodes
    mesh.nodes[1] = Node(1, 0.0, 0.0, 0.0)
    mesh.nodes[2] = Node(2, 1.0, 0.0, 0.0)
    mesh.nodes[3] = Node(3, 1.0, 1.0, 0.0)
    mesh.nodes[4] = Node(4, 0.0, 1.0, 0.0)
    mesh.nodes[5] = Node(5, 0.0, 0.0, 1.0)
    mesh.nodes[6] = Node(6, 1.0, 0.0, 1.0)
    mesh.nodes[7] = Node(7, 1.0, 1.0, 1.0)
    mesh.nodes[8] = Node(8, 0.0, 1.0, 1.0)

    # 12 mid-edge nodes
    mesh.nodes[9] = Node(9, 0.5, 0.0, 0.0)
    mesh.nodes[10] = Node(10, 1.0, 0.5, 0.0)
    mesh.nodes[11] = Node(11, 0.5, 1.0, 0.0)
    mesh.nodes[12] = Node(12, 0.0, 0.5, 0.0)
    mesh.nodes[13] = Node(13, 0.5, 0.0, 1.0)
    mesh.nodes[14] = Node(14, 1.0, 0.5, 1.0)
    mesh.nodes[15] = Node(15, 0.5, 1.0, 1.0)
    mesh.nodes[16] = Node(16, 0.0, 0.5, 1.0)
    mesh.nodes[17] = Node(17, 0.0, 0.0, 0.5)
    mesh.nodes[18] = Node(18, 1.0, 0.0, 0.5)
    mesh.nodes[19] = Node(19, 1.0, 1.0, 0.5)
    mesh.nodes[20] = Node(20, 0.0, 1.0, 0.5)

    # Create HEX20 element
    mesh.elements[1] = Element(1, ElementType.HEX20, list(range(1, 21)))

    # Write to file
    output_file = output_dir / "demo_3_hex20.bdf"
    with NastranWriter(output_file) as writer:
        writer.write_complete_model(
            mesh=mesh,
            title="Demo 3: Quadratic HEX20 Elements"
        )

    print(f"✓ Created: {output_file}")
    print(f"  - Element Type: HEX20 (20-node hexahedron)")
    print(f"  - Nodes per element: 20 (8 corner + 12 mid-edge)")
    print(f"  - Better stress accuracy than HEX8")
    print(f"  - Multiple continuation lines for node list")


# ============================================================================
# Demo 4: TET4 Tetrahedron Mesh
# ============================================================================

def demo_4_tet4():
    """Export a TET4 tetrahedron mesh"""
    print("\n" + "="*70)
    print("Demo 4: TET4 Tetrahedron Mesh")
    print("="*70)

    # Create TET4 mesh
    mesh = MeshData(element_type=ElementType.TET4)

    # Create nodes
    mesh.nodes[1] = Node(1, 0.0, 0.0, 0.0)
    mesh.nodes[2] = Node(2, 1.0, 0.0, 0.0)
    mesh.nodes[3] = Node(3, 0.5, 1.0, 0.0)
    mesh.nodes[4] = Node(4, 0.5, 0.5, 1.0)
    mesh.nodes[5] = Node(5, 1.5, 0.5, 0.5)

    # Create 2 tet elements
    mesh.elements[1] = Element(1, ElementType.TET4, [1, 2, 3, 4])
    mesh.elements[2] = Element(2, ElementType.TET4, [2, 5, 3, 4])

    # Write to file
    output_file = output_dir / "demo_4_tet4.bdf"
    with NastranWriter(output_file) as writer:
        writer.write_complete_model(
            mesh=mesh,
            title="Demo 4: TET4 Mesh"
        )

    print(f"✓ Created: {output_file}")
    print(f"  - Element Type: TET4 (CTETRA)")
    print(f"  - Nodes per element: 4")
    print(f"  - Good for complex geometries")
    print(f"  - Automatic meshing friendly")


# ============================================================================
# Demo 5: Complete Model with Material Properties
# ============================================================================

def demo_5_with_material():
    """Export complete model with material properties"""
    print("\n" + "="*70)
    print("Demo 5: Complete Model with Material Properties")
    print("="*70)

    # Create mesh
    mesh = MeshData(element_type=ElementType.HEX8)

    # Create nodes (2x2x1 grid)
    for i in range(3):
        for j in range(3):
            for k in range(2):
                node_id = i * 6 + j * 2 + k + 1
                mesh.nodes[node_id] = Node(node_id, float(i), float(j), float(k))

    # Create 4 elements
    mesh.elements[1] = Element(1, ElementType.HEX8, [1, 3, 9, 7, 2, 4, 10, 8])
    mesh.elements[2] = Element(2, ElementType.HEX8, [3, 5, 11, 9, 4, 6, 12, 10])
    mesh.elements[3] = Element(3, ElementType.HEX8, [7, 9, 15, 13, 8, 10, 16, 14])
    mesh.elements[4] = Element(4, ElementType.HEX8, [9, 11, 17, 15, 10, 12, 18, 16])

    # Write with material properties
    output_file = output_dir / "demo_5_with_material.bdf"
    with NastranWriter(output_file) as writer:
        writer.write_complete_model(
            mesh=mesh,
            title="Demo 5: Model with Steel Material",
            youngs=210000.0,  # MPa
            poisson=0.3,
            density=7.85e-9   # tonne/mm^3
        )

    print(f"✓ Created: {output_file}")
    print(f"  - Material: Steel")
    print(f"    • Young's Modulus: 210 GPa")
    print(f"    • Poisson's Ratio: 0.3")
    print(f"    • Density: 7.85e-9 tonne/mm³")
    print(f"  - MAT1 entry with calculated shear modulus")
    print(f"  - PSOLID property linking elements to material")


# ============================================================================
# Demo 6: Multi-Part Model with Sets
# ============================================================================

def demo_6_multipart_with_sets():
    """Export multi-part model with node and element sets"""
    print("\n" + "="*70)
    print("Demo 6: Multi-Part Model with Sets")
    print("="*70)

    # Create mesh
    mesh = MeshData(element_type=ElementType.HEX8)

    # Part 1: Lower section (8 nodes)
    for i in range(2):
        for j in range(2):
            for k in range(2):
                node_id = i * 4 + j * 2 + k + 1
                mesh.nodes[node_id] = Node(node_id, float(i), float(j), float(k))

    # Part 2: Upper section (8 nodes)
    for i in range(2):
        for j in range(2):
            for k in range(2):
                node_id = i * 4 + j * 2 + k + 9
                mesh.nodes[node_id] = Node(node_id, float(i), float(j), float(k) + 1.0)

    # Elements
    mesh.elements[1] = Element(1, ElementType.HEX8, [1, 2, 4, 3, 5, 6, 8, 7])  # Lower
    mesh.elements[2] = Element(2, ElementType.HEX8, [5, 6, 8, 7, 9, 10, 12, 11])  # Upper

    # Write with sets
    output_file = output_dir / "demo_6_multipart_sets.bdf"
    with NastranWriter(output_file) as writer:
        writer.write_complete_model(
            mesh=mesh,
            title="Demo 6: Multi-Part Model with Sets"
        )

        # Define sets
        writer.write_set(set_id=100, set_type="NODE", entity_ids=[1, 2, 3, 4])  # Bottom nodes
        writer.write_set(set_id=101, set_type="NODE", entity_ids=[9, 10, 11, 12])  # Top nodes
        writer.write_set(set_id=200, set_type="ELEM", entity_ids=[1])  # Lower part
        writer.write_set(set_id=201, set_type="ELEM", entity_ids=[2])  # Upper part

    print(f"✓ Created: {output_file}")
    print(f"  - 2 parts (lower and upper)")
    print(f"  - Node Sets:")
    print(f"    • Set 100: Bottom nodes (boundary conditions)")
    print(f"    • Set 101: Top nodes (loads)")
    print(f"  - Element Sets:")
    print(f"    • Set 200: Lower part")
    print(f"    • Set 201: Upper part")
    print(f"  - SET1 entries for easy reference in analysis")


# ============================================================================
# Demo 7: Advanced Mesh with Multiple Materials
# ============================================================================

def demo_7_advanced():
    """Export advanced mesh with multiple materials and properties"""
    print("\n" + "="*70)
    print("Demo 7: Advanced Mesh with Multiple Materials")
    print("="*70)

    # Create mesh
    mesh = MeshData(element_type=ElementType.HEX8)

    # Create 3x1x1 mesh (3 elements)
    for i in range(4):
        for j in range(2):
            for k in range(2):
                node_id = i * 4 + j * 2 + k + 1
                mesh.nodes[node_id] = Node(node_id, float(i) * 10.0, float(j) * 10.0, float(k) * 10.0)

    # Create 3 elements
    mesh.elements[1] = Element(1, ElementType.HEX8, [1, 2, 4, 3, 5, 6, 8, 7])
    mesh.elements[2] = Element(2, ElementType.HEX8, [5, 6, 8, 7, 9, 10, 12, 11])
    mesh.elements[3] = Element(3, ElementType.HEX8, [9, 10, 12, 11, 13, 14, 16, 15])

    # Write model with manual control
    output_file = output_dir / "demo_7_advanced.bdf"
    with NastranWriter(output_file) as writer:
        # Header with custom comments
        writer.write_header(
            title="Demo 7: Advanced Multi-Material Model",
            comments=[
                "Three-section composite structure",
                "Section 1: Aluminum alloy",
                "Section 2: Steel",
                "Section 3: Titanium alloy",
                "Units: N, mm, tonne, s"
            ]
        )

        # Write mesh
        writer.write_nodes(mesh)

        # Write all elements (we'd need different element types for different materials in real use)
        writer.write_elements(mesh, pid=1)

        # Define materials
        writer.write_material(
            mat_id=1,
            youngs=70000.0,    # Aluminum
            poisson=0.33,
            density=2.7e-9,
            comments=["Aluminum Alloy 6061-T6"]
        )

        writer.write_material(
            mat_id=2,
            youngs=210000.0,   # Steel
            poisson=0.30,
            density=7.85e-9,
            comments=["Structural Steel"]
        )

        writer.write_material(
            mat_id=3,
            youngs=110000.0,   # Titanium
            poisson=0.34,
            density=4.43e-9,
            thermal_exp=8.6e-6,
            comments=["Titanium Alloy Ti-6Al-4V"]
        )

        # Define properties (linking materials to elements)
        writer.write_property(pid=1, mat_id=1)
        writer.write_property(pid=2, mat_id=2)
        writer.write_property(pid=3, mat_id=3)

        # Define element sets for each section
        writer.write_set(set_id=1, set_type="ELEM", entity_ids=[1])
        writer.write_set(set_id=2, set_type="ELEM", entity_ids=[2])
        writer.write_set(set_id=3, set_type="ELEM", entity_ids=[3])

        # End
        writer.file.write("$\n")
        writer.file.write("ENDDATA\n")

    print(f"✓ Created: {output_file}")
    print(f"  - 3 different materials:")
    print(f"    • Material 1: Aluminum (E=70 GPa)")
    print(f"    • Material 2: Steel (E=210 GPa)")
    print(f"    • Material 3: Titanium (E=110 GPa)")
    print(f"  - 3 property definitions (PID 1-3)")
    print(f"  - Element sets for each section")
    print(f"  - Demonstrates manual control of writer")
    print(f"  - Custom comments throughout")


# ============================================================================
# Main: Run All Demos
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("NASTRAN EXPORT DEMONSTRATION")
    print("="*70)
    print("\nThis demo creates 7 example Nastran .bdf files showing various features.")
    print(f"Output directory: {output_dir.absolute()}")

    # Run all demos
    demo_1_basic_hex8()
    demo_2_small_field()
    demo_3_hex20()
    demo_4_tet4()
    demo_5_with_material()
    demo_6_multipart_with_sets()
    demo_7_advanced()

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"✓ Created 7 Nastran .bdf files in {output_dir}/")
    print("\nKey Features Demonstrated:")
    print("  • Large and small field formats")
    print("  • HEX8, HEX20, TET4 element types")
    print("  • GRID entries for nodes")
    print("  • CHEXA, CTETRA element definitions")
    print("  • MAT1 material properties")
    print("  • PSOLID property definitions")
    print("  • SET1 node/element sets")
    print("  • Comment lines with $")
    print("  • Continuation lines with *")
    print("\nYou can import these files into:")
    print("  • MSC Nastran")
    print("  • NX Nastran")
    print("  • FEMAP")
    print("  • Patran")
    print("  • Other Nastran-compatible FEA tools")
    print("\n" + "="*70)
