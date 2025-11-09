"""
Example 1: Basic Contact Detection

This example demonstrates basic contact detection for a simple assembly.
"""

import numpy as np
from koomesh.contact.assembly_contact import AssemblyContactManager
from koomesh.meshing.mesh_data import MeshData


def create_sample_assembly():
    """Create a simple 3-part assembly for demonstration"""
    parts = []

    # Part 1: Base plate (10x10mm at z=0)
    nodes1 = np.array([
        [0, 0, 0],
        [10, 0, 0],
        [10, 10, 0],
        [0, 10, 0],
        [5, 5, 0]
    ], dtype=float)

    elements1 = np.array([
        [0, 1, 4],
        [1, 2, 4],
        [2, 3, 4],
        [3, 0, 4]
    ])

    mesh1 = MeshData(nodes=nodes1, elements=elements1)
    parts.append(('Base_Plate', mesh1))

    # Part 2: Middle plate (8x8mm at z=0.5mm, small gap)
    nodes2 = np.array([
        [1, 1, 0.5],
        [9, 1, 0.5],
        [9, 9, 0.5],
        [1, 9, 0.5],
        [5, 5, 0.5]
    ], dtype=float)

    elements2 = np.array([
        [0, 1, 4],
        [1, 2, 4],
        [2, 3, 4],
        [3, 0, 4]
    ])

    mesh2 = MeshData(nodes=nodes2, elements=elements2)
    parts.append(('Middle_Plate', mesh2))

    # Part 3: Top plate (6x6mm at z=1.0mm)
    nodes3 = np.array([
        [2, 2, 1.0],
        [8, 2, 1.0],
        [8, 8, 1.0],
        [2, 8, 1.0],
        [5, 5, 1.0]
    ], dtype=float)

    elements3 = np.array([
        [0, 1, 4],
        [1, 2, 4],
        [2, 3, 4],
        [3, 0, 4]
    ])

    mesh3 = MeshData(nodes=nodes3, elements=elements3)
    parts.append(('Top_Plate', mesh3))

    return parts


def main():
    """Main example function"""
    print("=" * 60)
    print("Example 1: Basic Contact Detection")
    print("=" * 60)
    print()

    # Create sample assembly
    print("Creating 3-part assembly...")
    parts = create_sample_assembly()
    print(f"  Created {len(parts)} parts:")
    for name, mesh in parts:
        print(f"    - {name}: {len(mesh.nodes)} nodes, {len(mesh.elements)} elements")
    print()

    # Initialize contact manager
    print("Initializing contact manager...")
    manager = AssemblyContactManager()
    print()

    # Detect contacts with different tolerances
    tolerances = [0.3, 0.6, 1.0]

    for tolerance in tolerances:
        print(f"Detecting contacts (tolerance = {tolerance} mm)...")
        contact_pairs = manager.detect_contacts(
            parts,
            tolerance=tolerance,
            auto_classify=True
        )

        print(f"  Found {len(contact_pairs)} contact pairs:")
        for i, pair in enumerate(contact_pairs, 1):
            print(f"    {i}. {pair.master_part} <-> {pair.slave_part}")
            print(f"       Type: {pair.contact_type.value}")
            print(f"       Friction: {pair.parameters.fs:.2f}")
            if pair.metadata:
                print(f"       Gap: {pair.metadata.get('gap', 'N/A'):.3f} mm")
                print(f"       Area: {pair.metadata.get('area', 'N/A'):.1f} mm²")
        print()

    # Detailed analysis
    print("Detailed contact analysis (tolerance = 1.0 mm)...")
    contact_pairs = manager.detect_contacts(
        parts,
        tolerance=1.0,
        auto_classify=True
    )

    for i, pair in enumerate(contact_pairs, 1):
        print(f"\nContact Pair {i}:")
        print(f"  Master: {pair.master_part}")
        print(f"  Slave:  {pair.slave_part}")
        print(f"  Type:   {pair.contact_type.value}")
        print(f"\n  LS-DYNA Parameters:")
        print(f"    FS (static friction):  {pair.parameters.fs:.3f}")
        print(f"    FD (dynamic friction): {pair.parameters.fd:.3f}")
        print(f"    SOFT (penalty):        {pair.parameters.soft}")
        print(f"    DEPTH (search depth):  {pair.parameters.depth}")

        if pair.metadata:
            print(f"\n  Geometry:")
            print(f"    Gap distance: {pair.metadata.get('gap', 0.0):.3f} mm")
            print(f"    Contact area: {pair.metadata.get('area', 0.0):.1f} mm²")
            print(f"    Surface angle: {pair.metadata.get('angle', 0.0):.1f}°")

    print("\n" + "=" * 60)
    print("Example complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()
