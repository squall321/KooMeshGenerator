"""
Mesh Smoothing Demo
===================

This example demonstrates mesh smoothing capabilities to improve element quality.

Smoothing algorithms relocate nodes to improve element shapes while preserving
mesh topology and geometry.

Algorithms demonstrated:
1. Laplacian smoothing - Basic averaging
2. Smart Laplacian - Boundary-preserving
3. Taubin smoothing - Shrinkage prevention
4. Quality-based smoothing - Targeted improvement

Run this demo:
    python examples/mesh_smoothing_demo.py
"""

import sys
from pathlib import Path
import numpy as np

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from koomesh.meshing.mesh_data import MeshData, ElementType
from koomesh.meshing.mesh_smoother import MeshSmoother
from koomesh.meshing.quality_checker import QualityChecker
from koomesh.export.lsdyna_writer import LSDynaWriter


def create_distorted_mesh(size: int = 5, distortion: float = 0.3) -> MeshData:
    """
    Create a distorted hex mesh for demonstration

    Args:
        size: Grid size (size x size x size elements)
        distortion: Amount of random distortion (0-1)

    Returns:
        MeshData with distorted mesh
    """
    print(f"\nCreating {size}x{size}x{size} distorted mesh...")
    print(f"  Distortion level: {distortion}")

    mesh = MeshData(element_type=ElementType.HEX8)

    # Create nodes with random distortion
    node_ids = {}
    for k in range(size + 1):
        for j in range(size + 1):
            for i in range(size + 1):
                # Add distortion to interior nodes only
                is_boundary = (i == 0 or i == size or
                             j == 0 or j == size or
                             k == 0 or k == size)

                if is_boundary:
                    x, y, z = float(i), float(j), float(k)
                else:
                    x = float(i) + np.random.uniform(-distortion, distortion)
                    y = float(j) + np.random.uniform(-distortion, distortion)
                    z = float(k) + np.random.uniform(-distortion, distortion)

                nid = mesh.add_node(x, y, z)
                node_ids[(i, j, k)] = nid

    # Create elements
    for k in range(size):
        for j in range(size):
            for i in range(size):
                n0 = node_ids[(i, j, k)]
                n1 = node_ids[(i+1, j, k)]
                n2 = node_ids[(i+1, j+1, k)]
                n3 = node_ids[(i, j+1, k)]
                n4 = node_ids[(i, j, k+1)]
                n5 = node_ids[(i+1, j, k+1)]
                n6 = node_ids[(i+1, j+1, k+1)]
                n7 = node_ids[(i, j+1, k+1)]

                mesh.add_element([n0, n1, n2, n3, n4, n5, n6, n7])

    print(f"  Created {mesh.num_nodes()} nodes, {mesh.num_elements()} elements")

    return mesh


def print_quality_report(mesh: MeshData, title: str):
    """Print quality report for mesh"""
    checker = QualityChecker()
    report = checker.check_mesh(mesh)

    print(f"\n{title}")
    print("=" * 70)
    print(f"  Elements: {report.num_elements}")
    print(f"  Jacobian:")
    print(f"    Min:  {report.jacobian['min']:8.6f}")
    print(f"    Mean: {report.jacobian['mean']:8.6f}")
    print(f"    Max:  {report.jacobian['max']:8.6f}")

    if report.jacobian['min'] < 0:
        print(f"  ⚠️  WARNING: Negative Jacobian detected! (inverted elements)")
    elif report.jacobian['min'] < 0.1:
        print(f"  ⚠️  WARNING: Very poor quality elements detected")
    elif report.jacobian['min'] < 0.3:
        print(f"  ⚠️  Some poor quality elements")
    else:
        print(f"  ✓ Good quality mesh")


def demo_laplacian_smoothing():
    """Demonstrate basic Laplacian smoothing"""
    print("\n" + "="*70)
    print("Demo 1: Laplacian Smoothing")
    print("="*70)
    print("\nBasic smoothing - moves nodes to average of neighbors")
    print("Simple but effective. May cause slight mesh shrinkage.")

    # Create distorted mesh
    mesh = create_distorted_mesh(size=4, distortion=0.25)
    print_quality_report(mesh, "Initial Quality")

    # Apply Laplacian smoothing
    print("\nApplying Laplacian smoothing (10 iterations)...")
    smoother = MeshSmoother(mesh)
    smoother.laplacian_smooth(iterations=10, relaxation=0.5)

    print_quality_report(mesh, "After Laplacian Smoothing")

    # Export
    output_file = "/tmp/laplacian_smoothed.k"
    with LSDynaWriter(output_file) as writer:
        writer.write_header()
        writer.write_nodes(mesh)
        writer.write_elements(mesh)

    print(f"\n✓ Output: {output_file}")


def demo_smart_laplacian():
    """Demonstrate Smart Laplacian with boundary preservation"""
    print("\n" + "="*70)
    print("Demo 2: Smart Laplacian (Boundary-Preserving)")
    print("="*70)
    print("\nPreserves boundary nodes - only smooths interior")
    print("Better for maintaining exact geometry boundaries")

    mesh = create_distorted_mesh(size=4, distortion=0.25)
    print_quality_report(mesh, "Initial Quality")

    smoother = MeshSmoother(mesh)
    summary = smoother.get_summary()

    print(f"\nMesh Summary:")
    print(f"  Total nodes: {summary['num_nodes']}")
    print(f"  Boundary nodes: {summary['num_boundary_nodes']}")
    print(f"  Interior nodes: {summary['num_interior_nodes']}")

    print("\nApplying Smart Laplacian (10 iterations)...")
    print("  - Preserving boundary: YES")
    smoother.smart_laplacian(iterations=10, preserve_boundary=True)

    print_quality_report(mesh, "After Smart Laplacian")

    output_file = "/tmp/smart_laplacian_smoothed.k"
    with LSDynaWriter(output_file) as writer:
        writer.write_header()
        writer.write_nodes(mesh)
        writer.write_elements(mesh)

    print(f"\n✓ Output: {output_file}")


def demo_taubin_smoothing():
    """Demonstrate Taubin smoothing"""
    print("\n" + "="*70)
    print("Demo 3: Taubin Smoothing (Anti-Shrinkage)")
    print("="*70)
    print("\nTwo-step smoothing that prevents mesh shrinkage")
    print("Inflation + deflation = volume preservation")

    mesh = create_distorted_mesh(size=4, distortion=0.25)
    print_quality_report(mesh, "Initial Quality")

    print("\nApplying Taubin smoothing (10 iterations)...")
    print("  - Lambda (inflation): 0.5")
    print("  - Mu (deflation): -0.53")
    smoother = MeshSmoother(mesh)
    smoother.taubin_smooth(iterations=10, preserve_boundary=True)

    print_quality_report(mesh, "After Taubin Smoothing")

    output_file = "/tmp/taubin_smoothed.k"
    with LSDynaWriter(output_file) as writer:
        writer.write_header()
        writer.write_nodes(mesh)
        writer.write_elements(mesh)

    print(f"\n✓ Output: {output_file}")


def demo_quality_based_smoothing():
    """Demonstrate quality-based targeted smoothing"""
    print("\n" + "="*70)
    print("Demo 4: Quality-Based Smoothing")
    print("="*70)
    print("\nOnly smooths regions with poor element quality")
    print("More efficient - focuses on problem areas")

    mesh = create_distorted_mesh(size=4, distortion=0.3)
    print_quality_report(mesh, "Initial Quality")

    smoother = MeshSmoother(mesh)

    print("\nApplying quality-based smoothing...")
    print("  - Quality threshold: 0.5 (only smooth if Jacobian < 0.5)")
    smoother.smart_laplacian(
        iterations=15,
        preserve_boundary=True,
        quality_threshold=0.5
    )

    print_quality_report(mesh, "After Quality-Based Smoothing")

    output_file = "/tmp/quality_based_smoothed.k"
    with LSDynaWriter(output_file) as writer:
        writer.write_header()
        writer.write_nodes(mesh)
        writer.write_elements(mesh)

    print(f"\n✓ Output: {output_file}")


def demo_quality_monitoring():
    """Demonstrate smoothing with quality monitoring"""
    print("\n" + "="*70)
    print("Demo 5: Smoothing with Quality Monitoring")
    print("="*70)
    print("\nAutomatically stops when quality stops improving")
    print("Prevents over-smoothing")

    mesh = create_distorted_mesh(size=4, distortion=0.25)
    print_quality_report(mesh, "Initial Quality")

    smoother = MeshSmoother(mesh)

    print("\nApplying smart smoothing with quality monitoring...")
    print("  - Maximum iterations: 50")
    print("  - Minimum improvement: 1%")
    print("  - Will stop early if converged")

    iterations_done = smoother.smooth_with_quality_monitoring(
        method='smart_laplacian',
        iterations=50,
        min_quality_improvement=0.01
    )

    print(f"\nConverged after {iterations_done} iterations")
    print_quality_report(mesh, "After Monitored Smoothing")

    output_file = "/tmp/monitored_smoothed.k"
    with LSDynaWriter(output_file) as writer:
        writer.write_header()
        writer.write_nodes(mesh)
        writer.write_elements(mesh)

    print(f"\n✓ Output: {output_file}")


def demo_comparison():
    """Compare all smoothing methods"""
    print("\n" + "="*70)
    print("Demo 6: Method Comparison")
    print("="*70)
    print("\nComparing all smoothing methods on the same mesh")

    # Create base mesh
    base_mesh = create_distorted_mesh(size=4, distortion=0.3)
    checker = QualityChecker()
    initial_report = checker.check_mesh(base_mesh)

    print("\n" + "-"*70)
    print("Initial Mesh Quality:")
    print(f"  Jacobian Min: {initial_report.jacobian['min']:.6f}")
    print("-"*70)

    methods = [
        ("Laplacian", lambda m: MeshSmoother(m).laplacian_smooth(iterations=10)),
        ("Smart Laplacian", lambda m: MeshSmoother(m).smart_laplacian(iterations=10)),
        ("Taubin", lambda m: MeshSmoother(m).taubin_smooth(iterations=10)),
    ]

    results = []

    for method_name, smooth_func in methods:
        # Copy mesh for this method
        import copy
        test_mesh = copy.deepcopy(base_mesh)

        # Apply smoothing
        smooth_func(test_mesh)

        # Check quality
        report = checker.check_mesh(test_mesh)
        results.append((method_name, report))

        print(f"\n{method_name}:")
        print(f"  Jacobian Min: {report.jacobian['min']:.6f}  "
              f"(improvement: {report.jacobian['min'] - initial_report.jacobian['min']:.6f})")

    print("\n" + "-"*70)
    print("Summary:")
    print("-"*70)

    # Find best method
    best_method = max(results, key=lambda x: x[1].jacobian['min'])
    print(f"\n✓ Best method: {best_method[0]}")
    print(f"  Final Jacobian Min: {best_method[1].jacobian['min']:.6f}")


def print_summary():
    """Print summary of smoothing capabilities"""
    print("\n" + "="*70)
    print("Mesh Smoothing Summary")
    print("="*70)

    print("\n📌 Key Features:")
    print("  • Laplacian smoothing - Simple and effective")
    print("  • Smart Laplacian - Boundary preservation")
    print("  • Taubin smoothing - Volume preservation")
    print("  • Quality-based - Targeted improvement")
    print("  • Quality monitoring - Automatic convergence")

    print("\n📊 When to Use:")
    print("  • After mesh generation")
    print("  • Before FEA simulation")
    print("  • To fix distorted elements")
    print("  • To improve solution accuracy")

    print("\n💡 Best Practices:")
    print("  • Use Smart Laplacian for boundary-critical models")
    print("  • Use Taubin to prevent shrinkage")
    print("  • Start with 5-10 iterations")
    print("  • Monitor quality to avoid over-smoothing")
    print("  • Always preserve important geometry features")

    print("\n📂 Output Files:")
    print("  All demos generated LS-DYNA .k files in /tmp/")
    print("  Import these to visualize smoothing effects")


def main():
    """Run all smoothing demonstrations"""
    print("="*70)
    print("KooMeshGenerator: Mesh Smoothing Demo")
    print("="*70)

    try:
        demo_laplacian_smoothing()
        demo_smart_laplacian()
        demo_taubin_smoothing()
        demo_quality_based_smoothing()
        demo_quality_monitoring()
        demo_comparison()

        print_summary()

        print("\n" + "="*70)
        print("All Demos Complete!")
        print("="*70)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
