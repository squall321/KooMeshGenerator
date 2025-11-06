#!/usr/bin/env python3
"""
CalculiX Export Demonstration
==============================

Demonstrates CalculiX INP format export capabilities.

CalculiX is an open-source finite element solver compatible with ABAQUS
input files. This demo shows how to create complete analysis-ready models.

Author: KooMeshGenerator Team
License: MIT
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from koomesh.meshing.mesh_data import MeshData, ElementType
from koomesh.export.calculix_writer import CalculixWriter, export_to_calculix


def demo_1_basic_hex8():
    """Demo 1: Basic HEX8 Mesh Export

    Creates a simple single-element hexahedral mesh for CalculiX.
    Demonstrates basic INP file structure.
    """
    print("\n" + "="*70)
    print("Demo 1: Basic HEX8 Mesh Export")
    print("="*70)

    # Create mesh
    mesh = MeshData(element_type=ElementType.HEX8)

    # Add nodes for a unit cube
    for i in range(2):
        for j in range(2):
            for k in range(2):
                node_id = i * 4 + j * 2 + k + 1
                mesh.add_node(float(i), float(j), float(k), node_id=node_id)

    # Add element (node ordering: bottom face CCW, top face CCW)
    mesh.add_element([1, 3, 7, 5, 2, 4, 8, 6], element_id=1)

    # Export using convenience function
    output_file = "calculix_export_examples/demo1_basic_hex8.inp"
    Path(output_file).parent.mkdir(exist_ok=True)

    success = export_to_calculix(mesh, output_file, title="Basic HEX8 Demo")

    if success:
        print(f"✓ Successfully exported to {output_file}")
        print(f"  Nodes: {len(mesh.nodes)}")
        print(f"  Elements: {len(mesh.elements)}")
        print(f"  Element type: C3D8 (8-node hexahedron)")

        # Show file preview
        with open(output_file, 'r') as f:
            lines = f.readlines()[:20]
            print("\nFile preview (first 20 lines):")
            print("".join(lines))
    else:
        print("✗ Export failed")


def demo_2_tet4_mesh():
    """Demo 2: TET4 Mesh Export

    Creates a tetrahedral mesh for CalculiX.
    Shows C3D4 element type.
    """
    print("\n" + "="*70)
    print("Demo 2: TET4 Mesh Export")
    print("="*70)

    # Create mesh
    mesh = MeshData(element_type=ElementType.TET4)

    # Add nodes for two tetrahedra
    mesh.add_node(0.0, 0.0, 0.0, node_id=1)
    mesh.add_node(1.0, 0.0, 0.0, node_id=2)
    mesh.add_node(0.5, 1.0, 0.0, node_id=3)
    mesh.add_node(0.5, 0.5, 1.0, node_id=4)
    mesh.add_node(0.5, 0.5, -1.0, node_id=5)

    # Add elements
    mesh.add_element([1, 2, 3, 4], element_id=1)
    mesh.add_element([1, 2, 3, 5], element_id=2)

    # Export
    output_file = "calculix_export_examples/demo2_tet4_mesh.inp"

    with CalculixWriter(output_file, title="TET4 Mesh Demo") as writer:
        writer.write_mesh(mesh)

    print(f"✓ Successfully exported to {output_file}")
    print(f"  Nodes: {len(mesh.nodes)}")
    print(f"  Elements: {len(mesh.elements)}")
    print(f"  Element type: C3D4 (4-node tetrahedron)")


def demo_3_quadratic_hex20():
    """Demo 3: Quadratic HEX20 Export

    Creates a 20-node quadratic hexahedral mesh.
    Demonstrates C3D20 element type for accurate stress analysis.
    """
    print("\n" + "="*70)
    print("Demo 3: Quadratic HEX20 Export")
    print("="*70)

    # Create mesh
    mesh = MeshData(element_type=ElementType.HEX20)

    # Add corner nodes (1-8)
    for i in range(2):
        for j in range(2):
            for k in range(2):
                node_id = i * 4 + j * 2 + k + 1
                mesh.add_node(float(i), float(j), float(k), node_id=node_id)

    # Add mid-edge nodes (9-20)
    # Bottom edges
    mesh.add_node(0.5, 0.0, 0.0, node_id=9)
    mesh.add_node(0.0, 0.5, 0.0, node_id=10)
    mesh.add_node(0.5, 1.0, 0.0, node_id=11)
    mesh.add_node(1.0, 0.5, 0.0, node_id=12)
    # Top edges
    mesh.add_node(0.5, 0.0, 1.0, node_id=13)
    mesh.add_node(0.0, 0.5, 1.0, node_id=14)
    mesh.add_node(0.5, 1.0, 1.0, node_id=15)
    mesh.add_node(1.0, 0.5, 1.0, node_id=16)
    # Vertical edges
    mesh.add_node(0.0, 0.0, 0.5, node_id=17)
    mesh.add_node(1.0, 0.0, 0.5, node_id=18)
    mesh.add_node(0.0, 1.0, 0.5, node_id=19)
    mesh.add_node(1.0, 1.0, 0.5, node_id=20)

    # Add element with all 20 nodes
    mesh.add_element([1, 3, 7, 5, 2, 4, 8, 6,
                      9, 11, 13, 10, 12, 15, 14, 16,
                      17, 18, 19, 20], element_id=1)

    # Export
    output_file = "calculix_export_examples/demo3_quadratic_hex20.inp"

    with CalculixWriter(output_file, title="Quadratic HEX20 Demo") as writer:
        writer.write_mesh(mesh)

    print(f"✓ Successfully exported to {output_file}")
    print(f"  Nodes: {len(mesh.nodes)}")
    print(f"  Elements: {len(mesh.elements)}")
    print(f"  Element type: C3D20 (20-node quadratic hexahedron)")
    print("  Note: Quadratic elements provide more accurate results")


def demo_4_element_and_node_sets():
    """Demo 4: Element and Node Sets

    Demonstrates element sets (ELSET) and node sets (NSET).
    These are essential for applying boundary conditions and materials.
    """
    print("\n" + "="*70)
    print("Demo 4: Element and Node Sets")
    print("="*70)

    # Create mesh with multiple elements
    mesh = MeshData(element_type=ElementType.HEX8)

    # Create 2x1x1 mesh (2 elements)
    for i in range(3):
        for j in range(2):
            for k in range(2):
                node_id = i * 4 + j * 2 + k + 1
                mesh.add_node(float(i), float(j), float(k), node_id=node_id)

    # Add two elements
    mesh.add_element([1, 3, 7, 5, 2, 4, 8, 6], element_id=1)
    mesh.add_element([5, 7, 11, 9, 6, 8, 12, 10], element_id=2)

    # Define sets
    elsets = {
        "Part1": [1],
        "Part2": [2],
        "AllElements": [1, 2]
    }

    nsets = {
        "FixedEnd": [1, 2, 3, 4],
        "LoadedEnd": [9, 10, 11, 12],
        "MidPlane": [5, 6, 7, 8]
    }

    # Export
    output_file = "calculix_export_examples/demo4_sets.inp"

    with CalculixWriter(output_file, title="Element and Node Sets Demo") as writer:
        writer.write_mesh(mesh, elsets=elsets, nsets=nsets)

    print(f"✓ Successfully exported to {output_file}")
    print(f"  Nodes: {len(mesh.nodes)}")
    print(f"  Elements: {len(mesh.elements)}")
    print(f"  Element sets: {len(elsets)}")
    print(f"  Node sets: {len(nsets)}")

    # Show set details
    print("\n  Element sets:")
    for name, elements in elsets.items():
        print(f"    {name}: {elements}")
    print("\n  Node sets:")
    for name, nodes in nsets.items():
        print(f"    {name}: {nodes}")


def demo_5_material_properties():
    """Demo 5: Material Properties

    Demonstrates elastic and plastic material definitions.
    Shows how to define complete material models for CalculiX.
    """
    print("\n" + "="*70)
    print("Demo 5: Material Properties")
    print("="*70)

    # Create simple mesh
    mesh = MeshData(element_type=ElementType.HEX8)
    for i in range(2):
        for j in range(2):
            for k in range(2):
                node_id = i * 4 + j * 2 + k + 1
                mesh.add_node(float(i), float(j), float(k), node_id=node_id)
    mesh.add_element([1, 3, 7, 5, 2, 4, 8, 6], element_id=1)

    # Element set for material assignment
    elsets = {"Part1": [1]}

    # Export with materials
    output_file = "calculix_export_examples/demo5_materials.inp"

    with CalculixWriter(output_file, title="Material Properties Demo") as writer:
        writer.write_mesh(mesh, elsets=elsets)

        # Write elastic material (Steel)
        writer.write_material("Steel",
                            elastic=(210000.0, 0.3),  # E, nu
                            density=7850.0)

        # Write elastic-plastic material (Aluminum)
        writer.write_material("Aluminum",
                            elastic=(70000.0, 0.33),
                            plastic=[(250.0, 0.0),    # Yield stress, plastic strain
                                   (300.0, 0.05),
                                   (350.0, 0.15)],
                            density=2700.0)

        # Assign material to element set
        writer.write_solid_section("Part1", "Steel")

    print(f"✓ Successfully exported to {output_file}")
    print("  Materials defined:")
    print("    Steel: E=210000 MPa, ν=0.3, ρ=7850 kg/m³")
    print("    Aluminum: E=70000 MPa, ν=0.33, ρ=2700 kg/m³")
    print("              with plastic behavior (3 points)")
    print("  Section assignment: Part1 → Steel")


def demo_6_boundary_conditions_and_loads():
    """Demo 6: Boundary Conditions and Loads

    Demonstrates boundary conditions and load application.
    Essential for complete structural analysis setup.
    """
    print("\n" + "="*70)
    print("Demo 6: Boundary Conditions and Loads")
    print("="*70)

    # Create cantilever beam mesh (4 elements)
    mesh = MeshData(element_type=ElementType.HEX8)

    # Create 4x1x1 mesh
    for i in range(5):
        for j in range(2):
            for k in range(2):
                node_id = i * 4 + j * 2 + k + 1
                mesh.add_node(float(i), float(j), float(k), node_id=node_id)

    # Add 4 elements
    for i in range(4):
        base = i * 4
        mesh.add_element([base+1, base+3, base+7, base+5,
                         base+2, base+4, base+8, base+6], element_id=i+1)

    # Define sets
    elsets = {"Beam": [1, 2, 3, 4]}
    nsets = {
        "Fixed": [1, 2, 3, 4],        # Fixed end
        "LoadPoint": [17, 18, 19, 20]  # Free end
    }

    # Export
    output_file = "calculix_export_examples/demo6_bc_loads.inp"

    with CalculixWriter(output_file, title="Boundary Conditions and Loads Demo") as writer:
        writer.write_mesh(mesh, elsets=elsets, nsets=nsets)

        # Material
        writer.write_material("Steel", elastic=(210000.0, 0.3))
        writer.write_solid_section("Beam", "Steel")

        # Boundary conditions: fix all DOFs at one end
        writer.write_boundary_condition("Fixed", [1, 2, 3])

        # Concentrated load: apply force in -Z direction at free end
        writer.write_cload("LoadPoint", 3, -1000.0)

        # Distributed pressure load on top surface
        writer.write_dload("Beam", "P3", 10.0)

    print(f"✓ Successfully exported to {output_file}")
    print("  Boundary conditions:")
    print("    Fixed: All DOFs constrained (U1=U2=U3=0)")
    print("  Loads:")
    print("    Concentrated: -1000 N in Z-direction at free end")
    print("    Distributed: 10 MPa pressure on top surface")


def demo_7_static_analysis_step():
    """Demo 7: Static Analysis Step

    Demonstrates complete static analysis setup with steps and output requests.
    Creates a ready-to-run CalculiX model.
    """
    print("\n" + "="*70)
    print("Demo 7: Static Analysis Step")
    print("="*70)

    # Create simple mesh
    mesh = MeshData(element_type=ElementType.HEX8)
    for i in range(2):
        for j in range(2):
            for k in range(2):
                node_id = i * 4 + j * 2 + k + 1
                mesh.add_node(float(i), float(j), float(k), node_id=node_id)
    mesh.add_element([1, 3, 7, 5, 2, 4, 8, 6], element_id=1)

    elsets = {"Part1": [1]}
    nsets = {"Fixed": [1, 2, 3, 4], "Loaded": [5, 6, 7, 8]}

    # Export
    output_file = "calculix_export_examples/demo7_static_analysis.inp"

    with CalculixWriter(output_file, title="Static Analysis Demo") as writer:
        writer.write_mesh(mesh, elsets=elsets, nsets=nsets)
        writer.write_material("Steel", elastic=(210000.0, 0.3))
        writer.write_solid_section("Part1", "Steel")
        writer.write_boundary_condition("Fixed", [1, 2, 3])
        writer.write_cload("Loaded", 3, -1000.0)

        # Write static analysis step
        writer.write_step_static(initial_inc=0.1,
                               total_time=1.0,
                               min_inc=0.01,
                               max_inc=0.5)

        # Request outputs
        writer.write_output_requests(node_output=["U", "RF"],
                                    element_output=["S", "E", "PE"])

    print(f"✓ Successfully exported to {output_file}")
    print("  Analysis type: Static")
    print("  Step parameters:")
    print("    Initial increment: 0.1")
    print("    Total time: 1.0")
    print("    Min increment: 0.01")
    print("    Max increment: 0.5")
    print("  Output requests:")
    print("    Node: U (displacement), RF (reaction force)")
    print("    Element: S (stress), E (strain), PE (plastic strain)")
    print("\n  This file is ready to run with: ccx jobname")


def demo_8_complete_analysis_model():
    """Demo 8: Complete Analysis Model

    Creates a comprehensive analysis-ready model with all features.
    This is a production-quality CalculiX input file.
    """
    print("\n" + "="*70)
    print("Demo 8: Complete Analysis Model")
    print("="*70)

    # Create more complex mesh (2x2x1 = 4 elements)
    mesh = MeshData(element_type=ElementType.HEX8)

    # Create 3x3x2 node grid
    for i in range(3):
        for j in range(3):
            for k in range(2):
                node_id = i * 6 + j * 2 + k + 1
                mesh.add_node(float(i) * 0.5, float(j) * 0.5, float(k) * 0.5,
                            node_id=node_id)

    # Add 4 elements (2x2 grid in XY plane)
    elem_id = 1
    for i in range(2):
        for j in range(2):
            base = i * 6 + j * 2 + 1
            mesh.add_element([base, base+2, base+8, base+6,
                            base+1, base+3, base+9, base+7],
                           element_id=elem_id)
            elem_id += 1

    # Define comprehensive sets
    elsets = {
        "AllElements": [1, 2, 3, 4],
        "BottomElements": [1, 2],
        "TopElements": [3, 4]
    }

    nsets = {
        "FixedBase": [1, 2, 3, 4, 5, 6],  # Bottom nodes
        "LoadedTop": [13, 14, 15, 16, 17, 18],  # Top nodes
        "LeftEdge": [1, 2, 7, 8, 13, 14],
        "RightEdge": [5, 6, 11, 12, 17, 18]
    }

    # Export complete model
    output_file = "calculix_export_examples/demo8_complete_model.inp"

    with CalculixWriter(output_file, title="Complete Analysis Model") as writer:
        # 1. Write mesh
        writer.write_mesh(mesh, elsets=elsets, nsets=nsets)

        # 2. Define materials
        writer.write_material("StructuralSteel",
                            elastic=(210000.0, 0.3),
                            plastic=[(250.0, 0.0),
                                   (400.0, 0.2),
                                   (550.0, 0.5)],
                            density=7850.0)

        # 3. Assign sections
        writer.write_solid_section("AllElements", "StructuralSteel")

        # 4. Apply boundary conditions
        writer.write_boundary_condition("FixedBase", [1, 2, 3])

        # 5. Apply loads
        writer.write_cload("LoadedTop", 3, -5000.0)
        writer.write_dload("TopElements", "P3", 100.0)

        # 6. Define analysis step
        writer.write_step_static(initial_inc=0.05,
                               total_time=1.0,
                               min_inc=0.001,
                               max_inc=0.2)

        # 7. Request comprehensive outputs
        writer.write_output_requests(
            node_output=["U", "RF", "NT"],
            element_output=["S", "E", "PE", "PEEQ", "ENER"]
        )

    print(f"✓ Successfully exported to {output_file}")
    print(f"  Mesh: {len(mesh.nodes)} nodes, {len(mesh.elements)} elements")
    print(f"  Element sets: {len(elsets)}")
    print(f"  Node sets: {len(nsets)}")
    print("  Material: Structural steel with elastic-plastic behavior")
    print("  Boundary conditions: Fixed base (all DOFs)")
    print("  Loads:")
    print("    - Concentrated: -5000 N in Z at top nodes")
    print("    - Distributed: 100 MPa pressure on top elements")
    print("  Analysis: Static with adaptive time stepping")
    print("  Outputs: Full displacement, stress, strain, and energy")
    print("\n  ⚙️  Ready to run with CalculiX:")
    print(f"     ccx {Path(output_file).stem}")

    # Show file statistics
    with open(output_file, 'r') as f:
        lines = f.readlines()
    print(f"\n  File statistics:")
    print(f"    Total lines: {len(lines)}")
    print(f"    File size: {Path(output_file).stat().st_size} bytes")


def main():
    """Run all CalculiX export demonstrations"""
    print("="*70)
    print("CalculiX Export Demonstrations")
    print("="*70)
    print("\nCalculiX is an open-source finite element solver compatible with")
    print("ABAQUS input files. These demos show how to create complete")
    print("analysis-ready models for structural analysis.")
    print("\nFormat: INP (ABAQUS-compatible keyword format)")
    print("Website: http://www.calculix.de/")

    try:
        demo_1_basic_hex8()
        demo_2_tet4_mesh()
        demo_3_quadratic_hex20()
        demo_4_element_and_node_sets()
        demo_5_material_properties()
        demo_6_boundary_conditions_and_loads()
        demo_7_static_analysis_step()
        demo_8_complete_analysis_model()

        print("\n" + "="*70)
        print("All CalculiX export demonstrations completed successfully!")
        print("="*70)
        print("\nOutput files created in: calculix_export_examples/")
        print("\nTo run any model with CalculiX:")
        print("  1. Install CalculiX: http://www.calculix.de/")
        print("  2. Run: ccx jobname")
        print("  3. View results: cgx jobname.frd")
        print("\nNote: CalculiX uses ABAQUS-compatible input format")

    except Exception as e:
        print(f"\n✗ Error during demonstrations: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
