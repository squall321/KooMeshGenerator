"""
Prism and Pyramid Elements Demo
================================

This example demonstrates the usage of prism (PRISM6) and pyramid (PYRAMID5)
elements in KooMeshGenerator. These transition elements are useful for bridging
between hexahedral and tetrahedral meshes.

Features demonstrated:
1. Creating PRISM6 (wedge) elements
2. Creating PYRAMID5 elements
3. Computing element quality metrics
4. Exporting to LS-DYNA format
"""

import numpy as np
from koomesh.meshing.mesh_data import MeshData, ElementType
from koomesh.meshing.shape_functions import (
    prism6_shape_functions,
    pyramid5_shape_functions,
    prism6_shape_derivatives,
    pyramid5_shape_derivatives,
    compute_jacobian
)
from koomesh.meshing.quality_checker import QualityChecker
from koomesh.export.lsdyna_writer import LSDynaWriter


def demo_prism6_element():
    """Demonstrate PRISM6 (wedge) element usage"""
    print("\n" + "="*70)
    print("PRISM6 (Wedge) Element Demonstration")
    print("="*70)

    # Create mesh with PRISM6 elements
    mesh = MeshData(element_type=ElementType.PRISM6)

    # Define a unit prism element
    # Bottom triangle at z=0, top triangle at z=1
    coords = [
        [0.0, 0.0, 0.0],  # Node 0: bottom triangle
        [1.0, 0.0, 0.0],  # Node 1
        [0.0, 1.0, 0.0],  # Node 2
        [0.0, 0.0, 1.0],  # Node 3: top triangle
        [1.0, 0.0, 1.0],  # Node 4
        [0.0, 1.0, 1.0],  # Node 5
    ]

    print("\nCreating unit prism element...")
    node_ids = []
    for i, (x, y, z) in enumerate(coords):
        nid = mesh.add_node(x, y, z)
        node_ids.append(nid)
        print(f"  Node {nid}: ({x:.3f}, {y:.3f}, {z:.3f})")

    eid = mesh.add_element(node_ids, element_type=ElementType.PRISM6)
    print(f"\nCreated PRISM6 element with ID {eid}")

    # Test shape functions at various points
    print("\nShape Function Analysis:")
    print("-" * 70)

    test_points = [
        (0.0, 0.0, 0.0, "Bottom corner"),
        (1.0, 0.0, 0.0, "Bottom corner 2"),
        (0.0, 0.0, 1.0, "Top corner"),
        (0.33, 0.33, 0.0, "Bottom center"),
        (0.33, 0.33, 1.0, "Top center"),
        (0.33, 0.33, 0.0, "Mid-height center"),
    ]

    for xi, eta, zeta, description in test_points:
        N = prism6_shape_functions(xi, eta, zeta)
        N_sum = np.sum(N)
        print(f"\n{description} (ξ={xi:.2f}, η={eta:.2f}, ζ={zeta:.2f}):")
        print(f"  Shape functions: {N}")
        print(f"  Sum (should be 1.0): {N_sum:.10f}")

    # Compute Jacobian
    print("\nJacobian Analysis:")
    print("-" * 70)
    coords_array = np.array(coords)
    dN = prism6_shape_derivatives(0.33, 0.33, 0.0)
    J, det_J = compute_jacobian(coords_array, dN)

    print(f"Jacobian matrix at element center:")
    print(J)
    print(f"\nJacobian determinant: {det_J:.6f}")

    # Quality check
    print("\nQuality Metrics:")
    print("-" * 70)
    checker = QualityChecker()
    report = checker.check_mesh(mesh)

    print(f"Number of elements: {report.num_elements}")
    print(f"Jacobian - Min: {report.jacobian['min']:.6f}")
    print(f"Jacobian - Max: {report.jacobian['max']:.6f}")
    print(f"Jacobian - Mean: {report.jacobian['mean']:.6f}")

    # Face node extraction
    print("\nFace Node Information:")
    print("-" * 70)
    elem = mesh.get_element(eid)
    print("PRISM6 has 5 faces:")
    print("  - 2 triangular faces (top/bottom)")
    print("  - 3 rectangular faces (sides)")

    for face_id in range(5):
        face_nodes = elem.get_face_nodes(face_id)
        if len(face_nodes) == 3:
            face_type = "triangular"
        else:
            face_type = "rectangular"
        print(f"  Face {face_id}: {face_type} with nodes {face_nodes}")

    # Export to LS-DYNA
    output_file = "/tmp/prism6_demo.k"
    print(f"\nExporting to LS-DYNA format: {output_file}")
    with LSDynaWriter(output_file) as writer:
        writer.write_header()
        writer.write_nodes(mesh)
        writer.write_elements(mesh)

    print(f"✓ Successfully exported to {output_file}")

    return mesh


def demo_pyramid5_element():
    """Demonstrate PYRAMID5 element usage"""
    print("\n" + "="*70)
    print("PYRAMID5 Element Demonstration")
    print("="*70)

    # Create mesh with PYRAMID5 elements
    mesh = MeshData(element_type=ElementType.PYRAMID5)

    # Define a unit pyramid element
    # Square base at z=0, apex at z=1
    coords = [
        [-1.0, -1.0, 0.0],  # Node 0: base corners
        [ 1.0, -1.0, 0.0],  # Node 1
        [ 1.0,  1.0, 0.0],  # Node 2
        [-1.0,  1.0, 0.0],  # Node 3
        [ 0.0,  0.0, 1.0],  # Node 4: apex
    ]

    print("\nCreating unit pyramid element...")
    node_ids = []
    for i, (x, y, z) in enumerate(coords):
        nid = mesh.add_node(x, y, z)
        node_ids.append(nid)
        print(f"  Node {nid}: ({x:.3f}, {y:.3f}, {z:.3f})")

    eid = mesh.add_element(node_ids, element_type=ElementType.PYRAMID5)
    print(f"\nCreated PYRAMID5 element with ID {eid}")

    # Test shape functions at various points
    print("\nShape Function Analysis:")
    print("-" * 70)

    test_points = [
        (-1.0, -1.0, 0.0, "Base corner 0"),
        ( 1.0, -1.0, 0.0, "Base corner 1"),
        ( 0.0,  0.0, 0.0, "Base center"),
        ( 0.0,  0.0, 0.5, "Mid-height"),
        ( 0.0,  0.0, 0.9, "Near apex"),
        ( 0.0,  0.0, 1.0, "Apex"),
    ]

    for xi, eta, zeta, description in test_points:
        N = pyramid5_shape_functions(xi, eta, zeta)
        N_sum = np.sum(N)
        print(f"\n{description} (ξ={xi:.2f}, η={eta:.2f}, ζ={zeta:.2f}):")
        print(f"  Shape functions: {N}")
        print(f"  Sum (should be 1.0): {N_sum:.10f}")

    # Compute Jacobian (avoid apex where derivatives are undefined)
    print("\nJacobian Analysis:")
    print("-" * 70)
    coords_array = np.array(coords)
    dN = pyramid5_shape_derivatives(0.0, 0.0, 0.5)  # Mid-height
    J, det_J = compute_jacobian(coords_array, dN)

    print(f"Jacobian matrix at mid-height:")
    print(J)
    print(f"\nJacobian determinant: {det_J:.6f}")
    print("\nNote: Jacobian is undefined at apex (ζ=1) due to singularity")

    # Quality check
    print("\nQuality Metrics:")
    print("-" * 70)
    checker = QualityChecker()
    report = checker.check_mesh(mesh)

    print(f"Number of elements: {report.num_elements}")
    print(f"Jacobian - Min: {report.jacobian['min']:.6f}")
    print(f"Jacobian - Max: {report.jacobian['max']:.6f}")
    print(f"Jacobian - Mean: {report.jacobian['mean']:.6f}")

    # Face node extraction
    print("\nFace Node Information:")
    print("-" * 70)
    elem = mesh.get_element(eid)
    print("PYRAMID5 has 5 faces:")
    print("  - 1 square face (base)")
    print("  - 4 triangular faces (sides)")

    for face_id in range(5):
        face_nodes = elem.get_face_nodes(face_id)
        if len(face_nodes) == 4:
            face_type = "square base"
        else:
            face_type = "triangular side"
        print(f"  Face {face_id}: {face_type} with nodes {face_nodes}")

    # Export to LS-DYNA
    output_file = "/tmp/pyramid5_demo.k"
    print(f"\nExporting to LS-DYNA format: {output_file}")
    with LSDynaWriter(output_file) as writer:
        writer.write_header()
        writer.write_nodes(mesh)
        writer.write_elements(mesh)

    print(f"✓ Successfully exported to {output_file}")

    return mesh


def demo_hybrid_mesh():
    """Demonstrate combining prism and pyramid elements"""
    print("\n" + "="*70)
    print("Hybrid Mesh Demonstration (Combined Usage)")
    print("="*70)

    print("\nTransition elements (PRISM6 and PYRAMID5) are commonly used to bridge")
    print("between different mesh topologies:")
    print("  - Hex mesh → Tet mesh transitions")
    print("  - Structured → Unstructured mesh regions")
    print("  - Boundary layer → Volume mesh interfaces")

    print("\nTypical use cases:")
    print("  1. PRISM6 (Wedge):")
    print("     • Boundary layer meshing near walls")
    print("     • Extruded triangular meshes")
    print("     • Hex-to-Tet transitions")

    print("\n  2. PYRAMID5:")
    print("     • Connecting quad faces to tet mesh")
    print("     • Hex-to-Tet transitions")
    print("     • Filling gaps in hybrid meshes")

    print("\nNode ordering conventions:")
    print("  PRISM6:")
    print("    Bottom triangle: nodes 0-2")
    print("    Top triangle: nodes 3-5")
    print("    Height direction: -1 ≤ ζ ≤ 1")

    print("\n  PYRAMID5:")
    print("    Square base: nodes 0-3 (counterclockwise)")
    print("    Apex: node 4")
    print("    Height direction: 0 ≤ ζ ≤ 1")


def main():
    """Run all demonstrations"""
    print("="*70)
    print("KooMeshGenerator: Prism and Pyramid Elements Demo")
    print("="*70)
    print("\nThis demo showcases transition elements for hybrid meshing:")
    print("  • PRISM6 (6-node wedge/prism)")
    print("  • PYRAMID5 (5-node pyramid)")

    # Run demonstrations
    demo_prism6_element()
    demo_pyramid5_element()
    demo_hybrid_mesh()

    print("\n" + "="*70)
    print("Demo Complete!")
    print("="*70)
    print("\nOutput files generated:")
    print("  - /tmp/prism6_demo.k")
    print("  - /tmp/pyramid5_demo.k")
    print("\nThese files can be imported into LS-DYNA or other FEA solvers.")


if __name__ == '__main__':
    main()
