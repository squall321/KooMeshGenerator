#!/usr/bin/env python3
"""
Quadratic Elements Demonstration
==================================

This example demonstrates the use of quadratic elements (HEX20, HEX27, TET10)
in KooMeshGenerator.

Quadratic elements provide higher accuracy than linear elements with fewer
elements, making them ideal for:
- Stress concentration regions
- Curved geometry
- High-accuracy simulations

Usage:
    python quadratic_elements_demo.py
"""

import sys
import numpy as np
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from koomesh.meshing.mesh_data import MeshData, ElementType
from koomesh.meshing.quality_checker import QualityChecker
from koomesh.meshing.shape_functions import (
    hex20_shape_functions,
    hex27_shape_functions,
    tet10_shape_functions,
    get_shape_functions
)
from koomesh.export.lsdyna_writer import LSDynaWriter


def create_hex20_unit_cube():
    """
    Create a single HEX20 element representing a unit cube

    Returns:
        MeshData with one HEX20 element
    """
    print("\n" + "="*60)
    print("Creating HEX20 Unit Cube")
    print("="*60)

    mesh = MeshData(element_type=ElementType.HEX20)

    # Corner nodes (0-7)
    corners = [
        [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],  # Bottom
        [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1],  # Top
    ]

    # Mid-side nodes on bottom edges (8-11)
    bottom_edges = [
        [0.5, 0, 0], [1, 0.5, 0], [0.5, 1, 0], [0, 0.5, 0],
    ]

    # Mid-side nodes on top edges (12-15)
    top_edges = [
        [0.5, 0, 1], [1, 0.5, 1], [0.5, 1, 1], [0, 0.5, 1],
    ]

    # Mid-side nodes on vertical edges (16-19)
    vertical_edges = [
        [0, 0, 0.5], [1, 0, 0.5], [1, 1, 0.5], [0, 1, 0.5],
    ]

    # Add all 20 nodes
    node_ids = []
    all_nodes = corners + bottom_edges + top_edges + vertical_edges

    for x, y, z in all_nodes:
        nid = mesh.add_node(x, y, z)
        node_ids.append(nid)

    # Add element
    elem_id = mesh.add_element(node_ids, element_type=ElementType.HEX20)

    print(f"Created HEX20 element with {len(node_ids)} nodes")
    print(f"  - 8 corner nodes")
    print(f"  - 12 mid-side nodes")
    print(f"Element ID: {elem_id}")

    return mesh


def create_hex27_unit_cube():
    """
    Create a single HEX27 element representing a unit cube

    Returns:
        MeshData with one HEX27 element
    """
    print("\n" + "="*60)
    print("Creating HEX27 Unit Cube")
    print("="*60)

    mesh = MeshData(element_type=ElementType.HEX27)

    # Corner nodes (0-7)
    corners = [
        [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
        [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1],
    ]

    # Mid-side nodes on edges (8-19)
    edges = [
        [0.5, 0, 0], [1, 0.5, 0], [0.5, 1, 0], [0, 0.5, 0],  # Bottom
        [0.5, 0, 1], [1, 0.5, 1], [0.5, 1, 1], [0, 0.5, 1],  # Top
        [0, 0, 0.5], [1, 0, 0.5], [1, 1, 0.5], [0, 1, 0.5],  # Vertical
    ]

    # Face center nodes (20-25)
    face_centers = [
        [0.5, 0.5, 0],    # Bottom face
        [0.5, 0.5, 1],    # Top face
        [0.5, 0, 0.5],    # Front face
        [0.5, 1, 0.5],    # Back face
        [0, 0.5, 0.5],    # Left face
        [1, 0.5, 0.5],    # Right face
    ]

    # Volume center node (26)
    volume_center = [[0.5, 0.5, 0.5]]

    # Add all 27 nodes
    node_ids = []
    all_nodes = corners + edges + face_centers + volume_center

    for x, y, z in all_nodes:
        nid = mesh.add_node(x, y, z)
        node_ids.append(nid)

    elem_id = mesh.add_element(node_ids, element_type=ElementType.HEX27)

    print(f"Created HEX27 element with {len(node_ids)} nodes")
    print(f"  - 8 corner nodes")
    print(f"  - 12 edge mid-side nodes")
    print(f"  - 6 face center nodes")
    print(f"  - 1 volume center node")
    print(f"Element ID: {elem_id}")

    return mesh


def create_tet10_unit_tetrahedron():
    """
    Create a single TET10 element

    Returns:
        MeshData with one TET10 element
    """
    print("\n" + "="*60)
    print("Creating TET10 Unit Tetrahedron")
    print("="*60)

    mesh = MeshData(element_type=ElementType.TET10)

    # Corner nodes (0-3)
    corners = [
        [0, 0, 0],
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1],
    ]

    # Mid-side nodes (4-9)
    edges = [
        [0.5, 0, 0],    # Between 0-1
        [0.5, 0.5, 0],  # Between 1-2
        [0, 0.5, 0],    # Between 2-0
        [0, 0, 0.5],    # Between 0-3
        [0.5, 0, 0.5],  # Between 1-3
        [0, 0.5, 0.5],  # Between 2-3
    ]

    # Add all 10 nodes
    node_ids = []
    all_nodes = corners + edges

    for x, y, z in all_nodes:
        nid = mesh.add_node(x, y, z)
        node_ids.append(nid)

    elem_id = mesh.add_element(node_ids, element_type=ElementType.TET10)

    print(f"Created TET10 element with {len(node_ids)} nodes")
    print(f"  - 4 corner nodes")
    print(f"  - 6 mid-side nodes")
    print(f"Element ID: {elem_id}")

    return mesh


def check_quality(mesh, element_type_name):
    """Check mesh quality"""
    print(f"\nQuality Check for {element_type_name}:")
    print("-" * 60)

    checker = QualityChecker()
    report = checker.check_mesh(mesh)

    print(f"Jacobian: min={report.jacobian['min']:.6f}, "
          f"max={report.jacobian['max']:.6f}, "
          f"mean={report.jacobian['mean']:.6f}")
    print(f"Negative elements: {report.jacobian['negative_elements']}")
    print(f"Quality: {'PASS' if report.is_valid() else 'FAIL'}")


def export_to_lsdyna(mesh, output_file, element_type_name):
    """Export mesh to LS-DYNA format"""
    print(f"\nExporting {element_type_name} to LS-DYNA:")
    print("-" * 60)

    with LSDynaWriter(output_file) as writer:
        writer.write_header()
        writer.write_nodes(mesh)
        writer.write_elements(mesh, part_id=1)

    # Check file size
    file_size = Path(output_file).stat().st_size
    print(f"Output file: {output_file}")
    print(f"File size: {file_size} bytes")

    # Show first few lines
    with open(output_file, 'r') as f:
        lines = f.readlines()
        print(f"\nFirst 15 lines of output:")
        for i, line in enumerate(lines[:15], 1):
            print(f"{i:3d}: {line.rstrip()}")


def demonstrate_shape_functions():
    """Demonstrate shape functions"""
    print("\n" + "="*60)
    print("Shape Functions Demonstration")
    print("="*60)

    # HEX20 at center
    print("\nHEX20 Shape Functions at origin (0, 0, 0):")
    N_hex20 = hex20_shape_functions(0.0, 0.0, 0.0)
    print(f"  Number of shape functions: {len(N_hex20)}")
    print(f"  Sum (should be 1.0): {np.sum(N_hex20):.10f}")
    print(f"  Non-zero functions: {np.sum(N_hex20 > 1e-10)}")

    # HEX27 at center
    print("\nHEX27 Shape Functions at origin (0, 0, 0):")
    N_hex27 = hex27_shape_functions(0.0, 0.0, 0.0)
    print(f"  Number of shape functions: {len(N_hex27)}")
    print(f"  Sum (should be 1.0): {np.sum(N_hex27):.10f}")
    print(f"  Value at volume center node: {N_hex27[26]:.6f}")

    # TET10 at centroid
    print("\nTET10 Shape Functions at centroid (0.25, 0.25, 0.25):")
    N_tet10 = tet10_shape_functions(0.25, 0.25, 0.25)
    print(f"  Number of shape functions: {len(N_tet10)}")
    print(f"  Sum (should be 1.0): {np.sum(N_tet10):.10f}")


def main():
    """Main demonstration function"""
    print("\n" + "="*80)
    print(" "*20 + "Quadratic Elements Demonstration")
    print("="*80)

    # Create output directory
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)

    # Demonstrate shape functions
    demonstrate_shape_functions()

    # Create and test HEX20
    mesh_hex20 = create_hex20_unit_cube()
    check_quality(mesh_hex20, "HEX20")
    export_to_lsdyna(mesh_hex20, output_dir / "hex20_demo.k", "HEX20")

    # Create and test HEX27
    mesh_hex27 = create_hex27_unit_cube()
    check_quality(mesh_hex27, "HEX27")
    export_to_lsdyna(mesh_hex27, output_dir / "hex27_demo.k", "HEX27")

    # Create and test TET10
    mesh_tet10 = create_tet10_unit_tetrahedron()
    check_quality(mesh_tet10, "TET10")
    export_to_lsdyna(mesh_tet10, output_dir / "tet10_demo.k", "TET10")

    print("\n" + "="*80)
    print(" "*25 + "Demonstration Complete!")
    print("="*80)
    print(f"\nOutput files saved to: {output_dir}")
    print("\nKey Takeaways:")
    print("  1. Quadratic elements use mid-side nodes for curved edges")
    print("  2. HEX20 uses serendipity formulation (20 nodes, no face/volume centers)")
    print("  3. HEX27 uses complete quadratic formulation (27 nodes with centers)")
    print("  4. TET10 provides quadratic tetrahedral elements")
    print("  5. Quadratic elements offer higher accuracy with fewer elements")
    print("\nCompare with linear elements:")
    print("  - HEX8:  8 nodes,  1 DOF per node = 8 DOF")
    print("  - HEX20: 20 nodes, 1 DOF per node = 20 DOF (2.5x more accurate)")
    print("  - HEX27: 27 nodes, 1 DOF per node = 27 DOF (3.4x more accurate)")
    print()


if __name__ == '__main__':
    main()
