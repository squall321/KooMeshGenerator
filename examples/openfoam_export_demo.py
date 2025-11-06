#!/usr/bin/env python3
"""
OpenFOAM polyMesh Export Demonstration
=======================================

Demonstrates OpenFOAM polyMesh format export capabilities.

OpenFOAM is an open-source CFD toolbox that uses a unique face-based
mesh format. This demo shows how to create OpenFOAM-ready meshes.

Author: KooMeshGenerator Team
License: MIT
"""

import sys
from pathlib import Path
import shutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from koomesh.meshing.mesh_data import MeshData, ElementType
from koomesh.export.openfoam_writer import OpenFOAMWriter, export_to_openfoam


def demo_1_basic_hex8():
    """Demo 1: Basic HEX8 Mesh Export

    Creates a simple single-element hex mesh for OpenFOAM.
    Shows the basic polyMesh structure.
    """
    print("\n" + "="*70)
    print("Demo 1: Basic HEX8 Mesh Export")
    print("="*70)

    # Create mesh
    mesh = MeshData(element_type=ElementType.HEX8)

    # Add nodes for a unit cube
    node_ids = []
    for i in range(2):
        for j in range(2):
            for k in range(2):
                nid = mesh.add_node(float(i), float(j), float(k))
                node_ids.append(nid)

    # Add element
    mesh.add_element([node_ids[0], node_ids[1], node_ids[3], node_ids[2],
                     node_ids[4], node_ids[5], node_ids[7], node_ids[6]])

    # Export using convenience function
    case_dir = "openfoam_export_examples/demo1_basic_hex8"
    success = export_to_openfoam(mesh, case_dir)

    if success:
        print(f"✓ Successfully exported to {case_dir}")
        print(f"  Nodes: {len(mesh.nodes)}")
        print(f"  Elements: {len(mesh.elements)}")
        print(f"  Faces: 6 (all boundary)")

        # Show polyMesh directory structure
        polymesh_dir = Path(case_dir) / "constant" / "polyMesh"
        print(f"\n  polyMesh directory created:")
        for f in sorted(polymesh_dir.glob("*")):
            print(f"    - {f.name}")
    else:
        print("✗ Export failed")


def demo_2_tet4_mesh():
    """Demo 2: TET4 Mesh Export

    Creates a tetrahedral mesh for CFD.
    TET4 elements are common in unstructured CFD meshes.
    """
    print("\n" + "="*70)
    print("Demo 2: TET4 Mesh Export")
    print("="*70)

    # Create mesh
    mesh = MeshData(element_type=ElementType.TET4)

    # Add nodes for two tetrahedra
    n1 = mesh.add_node(0.0, 0.0, 0.0)
    n2 = mesh.add_node(1.0, 0.0, 0.0)
    n3 = mesh.add_node(0.5, 1.0, 0.0)
    n4 = mesh.add_node(0.5, 0.5, 1.0)
    n5 = mesh.add_node(0.5, 0.5, -1.0)

    # Add elements
    mesh.add_element([n1, n2, n3, n4])
    mesh.add_element([n1, n2, n3, n5])

    # Export
    case_dir = "openfoam_export_examples/demo2_tet4_mesh"

    writer = OpenFOAMWriter(case_dir)
    writer.write_mesh(mesh)

    print(f"✓ Successfully exported to {case_dir}")
    print(f"  Nodes: {len(mesh.nodes)}")
    print(f"  Elements: {len(mesh.elements)}")
    print(f"  Element type: TET4 (4-node tetrahedron)")


def demo_3_two_hex8_internal_face():
    """Demo 3: Two HEX8 with Internal Face

    Creates two hex elements sharing a face.
    Demonstrates internal face detection for CFD.
    """
    print("\n" + "="*70)
    print("Demo 3: Two HEX8 with Internal Face")
    print("="*70)

    # Create mesh
    mesh = MeshData(element_type=ElementType.HEX8)
    node_ids = []

    # First cube: x=0 to 1
    for i in range(2):
        for j in range(2):
            for k in range(2):
                nid = mesh.add_node(float(i), float(j), float(k))
                node_ids.append(nid)

    # Second cube: x=1 to 2 (shares 4 nodes with first)
    for j in range(2):
        for k in range(2):
            nid = mesh.add_node(2.0, float(j), float(k))
            node_ids.append(nid)

    # Add elements
    mesh.add_element([node_ids[0], node_ids[1], node_ids[3], node_ids[2],
                     node_ids[4], node_ids[5], node_ids[7], node_ids[6]])
    mesh.add_element([node_ids[1], node_ids[8], node_ids[9], node_ids[3],
                     node_ids[5], node_ids[10], node_ids[11], node_ids[7]])

    # Export
    case_dir = "openfoam_export_examples/demo3_internal_face"

    writer = OpenFOAMWriter(case_dir)
    writer.write_mesh(mesh)

    print(f"✓ Successfully exported to {case_dir}")
    print(f"  Nodes: {len(mesh.nodes)}")
    print(f"  Elements: {len(mesh.elements)}")

    # Read and check neighbour file
    neighbour_file = Path(case_dir) / "constant" / "polyMesh" / "neighbour"
    with open(neighbour_file, 'r') as f:
        content = f.read()
        # Find the count line
        for line in content.split('\n'):
            if line.strip().isdigit():
                n_internal = int(line.strip())
                print(f"  Internal faces: {n_internal}")
                break


def demo_4_boundary_patches():
    """Demo 4: Boundary Patches

    Demonstrates boundary patch definitions.
    Essential for CFD boundary conditions.
    """
    print("\n" + "="*70)
    print("Demo 4: Boundary Patches")
    print("="*70)

    # Create simple channel mesh (3 hex elements in a row)
    mesh = MeshData(element_type=ElementType.HEX8)
    node_ids = []

    # Create 4x2x2 node grid (3 elements in X direction)
    for i in range(4):
        for j in range(2):
            for k in range(2):
                nid = mesh.add_node(float(i), float(j), float(k))
                node_ids.append(nid)

    # Add 3 elements
    for elem_idx in range(3):
        base = elem_idx * 4
        mesh.add_element([
            node_ids[base+0], node_ids[base+1], node_ids[base+3], node_ids[base+2],
            node_ids[base+4], node_ids[base+5], node_ids[base+7], node_ids[base+6]
        ])

    # Define boundary patches
    # Note: In practice, you'd need to identify which faces belong to which patch
    # For this demo, we'll create empty patch definitions
    patches = {
        "inlet": [],    # Would contain (cell_id, face_id) tuples
        "outlet": [],   # for inlet boundary faces
        "walls": []     # for wall boundary faces
    }

    # Export
    case_dir = "openfoam_export_examples/demo4_boundary_patches"

    writer = OpenFOAMWriter(case_dir)
    writer.write_mesh(mesh, boundary_patches=patches)

    print(f"✓ Successfully exported to {case_dir}")
    print(f"  Nodes: {len(mesh.nodes)}")
    print(f"  Elements: {len(mesh.elements)}")
    print(f"  Boundary patches: {len(patches)}")
    for name in patches:
        print(f"    - {name}")


def demo_5_quadratic_hex20():
    """Demo 5: Quadratic HEX20 Export

    Creates a 20-node quadratic hex mesh.
    Higher-order elements for more accurate CFD.
    """
    print("\n" + "="*70)
    print("Demo 5: Quadratic HEX20 Export")
    print("="*70)

    # Create mesh
    mesh = MeshData(element_type=ElementType.HEX20)
    node_ids = []

    # Add corner nodes (1-8)
    for i in range(2):
        for j in range(2):
            for k in range(2):
                nid = mesh.add_node(float(i), float(j), float(k))
                node_ids.append(nid)

    # Add mid-edge nodes (9-20)
    mid_coords = [
        (0.5, 0.0, 0.0), (0.0, 0.5, 0.0), (0.5, 1.0, 0.0), (1.0, 0.5, 0.0),  # Bottom edges
        (0.5, 0.0, 1.0), (0.0, 0.5, 1.0), (0.5, 1.0, 1.0), (1.0, 0.5, 1.0),  # Top edges
        (0.0, 0.0, 0.5), (1.0, 0.0, 0.5), (0.0, 1.0, 0.5), (1.0, 1.0, 0.5),  # Vertical edges
    ]
    for x, y, z in mid_coords:
        nid = mesh.add_node(x, y, z)
        node_ids.append(nid)

    # Add element
    mesh.add_element(node_ids)

    # Export
    case_dir = "openfoam_export_examples/demo5_quadratic_hex20"

    writer = OpenFOAMWriter(case_dir)
    writer.write_mesh(mesh)

    print(f"✓ Successfully exported to {case_dir}")
    print(f"  Nodes: {len(mesh.nodes)}")
    print(f"  Elements: {len(mesh.elements)}")
    print(f"  Element type: HEX20 (20-node quadratic hexahedron)")
    print("  Note: Quadratic faces have mid-edge nodes")


def demo_6_mixed_elements():
    """Demo 6: Mixed Element Types

    Creates a mesh with both hex and tet elements.
    Shows OpenFOAM's flexibility with mixed meshes.
    """
    print("\n" + "="*70)
    print("Demo 6: Mixed Element Types")
    print("="*70)

    # Create mesh with default type
    mesh = MeshData(element_type=ElementType.HEX8)

    # Add nodes for a hex
    hex_nodes = []
    for i in range(2):
        for j in range(2):
            for k in range(2):
                nid = mesh.add_node(float(i), float(j), float(k))
                hex_nodes.append(nid)

    # Add hex element
    mesh.add_element([hex_nodes[0], hex_nodes[1], hex_nodes[3], hex_nodes[2],
                     hex_nodes[4], hex_nodes[5], hex_nodes[7], hex_nodes[6]],
                    element_type=ElementType.HEX8)

    # Add nodes for a tet
    tet_nodes = [
        mesh.add_node(2.0, 0.5, 0.5),
        mesh.add_node(3.0, 0.0, 0.0),
        mesh.add_node(3.0, 1.0, 0.0),
        mesh.add_node(3.0, 0.5, 1.0),
    ]

    # Add tet element
    mesh.add_element(tet_nodes, element_type=ElementType.TET4)

    # Export
    case_dir = "openfoam_export_examples/demo6_mixed_elements"

    writer = OpenFOAMWriter(case_dir)
    writer.write_mesh(mesh)

    print(f"✓ Successfully exported to {case_dir}")
    print(f"  Nodes: {len(mesh.nodes)}")
    print(f"  Elements: {len(mesh.elements)}")
    print(f"  Element types: HEX8 + TET4")
    print("  OpenFOAM automatically handles mixed element types")


def main():
    """Run all OpenFOAM export demonstrations"""
    print("="*70)
    print("OpenFOAM polyMesh Export Demonstrations")
    print("="*70)
    print("\nOpenFOAM is an open-source CFD toolbox that uses a unique")
    print("face-based mesh format (polyMesh). These demos show how to")
    print("create OpenFOAM-ready meshes from KooMeshGenerator.")
    print("\nFormat: polyMesh (faces, owner, neighbour, boundary)")
    print("Website: https://www.openfoam.com/")

    # Clean up old examples
    examples_dir = Path("openfoam_export_examples")
    if examples_dir.exists():
        shutil.rmtree(examples_dir)

    try:
        demo_1_basic_hex8()
        demo_2_tet4_mesh()
        demo_3_two_hex8_internal_face()
        demo_4_boundary_patches()
        demo_5_quadratic_hex20()
        demo_6_mixed_elements()

        print("\n" + "="*70)
        print("All OpenFOAM export demonstrations completed successfully!")
        print("="*70)
        print("\nOutput directories created in: openfoam_export_examples/")
        print("\nTo use with OpenFOAM:")
        print("  1. Copy constant/polyMesh to your OpenFOAM case")
        print("  2. Add system/controlDict, system/fvSchemes, system/fvSolution")
        print("  3. Run: checkMesh")
        print("  4. Run your solver: simpleFoam, icoFoam, etc.")
        print("\npolyMesh files:")
        print("  - points: Node coordinates")
        print("  - faces: Face definitions (node lists)")
        print("  - owner: Cell owning each face")
        print("  - neighbour: Neighboring cell (internal faces only)")
        print("  - boundary: Boundary patch definitions")

    except Exception as e:
        print(f"\n✗ Error during demonstrations: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
