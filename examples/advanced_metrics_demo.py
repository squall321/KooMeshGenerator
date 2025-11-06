"""
Advanced Mesh Quality Metrics Demo
===================================

Demonstrates advanced quality metrics: Jacobian ratio, skewness, aspect ratio.

Author: KooMeshGenerator Team
"""

import numpy as np
from koomesh.meshing.mesh_data import MeshData, ElementType
from koomesh.quality.advanced_metrics import (
    AdvancedQualityMetrics,
    analyze_mesh_quality
)


def demo_perfect_cube_metrics():
    """Analyze quality of a perfect cube"""
    print("\n" + "="*60)
    print("Demo 1: Perfect Cube Metrics")
    print("="*60)

    # Create perfect cube
    mesh = MeshData(element_type=ElementType.HEX8)

    node_ids = []
    for i in range(2):
        for j in range(2):
            for k in range(2):
                node_ids.append(mesh.add_node(float(i), float(j), float(k)))

    mesh.add_element([node_ids[0], node_ids[1], node_ids[3], node_ids[2],
                     node_ids[4], node_ids[5], node_ids[7], node_ids[6]])

    # Analyze
    metrics = AdvancedQualityMetrics(mesh)
    eid = list(mesh.elements.keys())[0]

    print(f"\nPerfect cube (1x1x1) quality:")
    print(f"  Jacobian ratio: {metrics.compute_jacobian_ratio(eid):.4f} (1.0 = perfect)")
    print(f"  Skewness:       {metrics.compute_skewness(eid):.4f} (0.0 = perfect)")
    print(f"  Aspect ratio:   {metrics.compute_aspect_ratio(eid):.4f} (1.0 = perfect)")


def demo_distorted_hex():
    """Analyze quality of a distorted hexahedron"""
    print("\n" + "="*60)
    print("Demo 2: Distorted Hexahedron")
    print("="*60)

    mesh = MeshData(element_type=ElementType.HEX8)

    node_ids = []
    # Create distorted hex
    node_ids.append(mesh.add_node(0.0, 0.0, 0.0))
    node_ids.append(mesh.add_node(1.0, 0.0, 0.0))
    node_ids.append(mesh.add_node(1.0, 1.0, 0.0))
    node_ids.append(mesh.add_node(0.0, 1.0, 0.0))
    node_ids.append(mesh.add_node(0.2, 0.2, 1.0))  # Distorted
    node_ids.append(mesh.add_node(1.0, 0.0, 1.0))
    node_ids.append(mesh.add_node(1.0, 1.0, 1.0))
    node_ids.append(mesh.add_node(0.0, 1.0, 1.0))

    mesh.add_element([node_ids[0], node_ids[1], node_ids[2], node_ids[3],
                     node_ids[4], node_ids[5], node_ids[6], node_ids[7]])

    metrics = AdvancedQualityMetrics(mesh)
    eid = list(mesh.elements.keys())[0]

    print(f"\nDistorted hexahedron quality:")
    print(f"  Jacobian ratio: {metrics.compute_jacobian_ratio(eid):.4f}")
    print(f"  Skewness:       {metrics.compute_skewness(eid):.4f}")
    print(f"  Aspect ratio:   {metrics.compute_aspect_ratio(eid):.4f}")
    print(f"\nNote: Lower Jacobian ratio indicates distortion")


def demo_elongated_tet():
    """Analyze elongated tetrahedron (poor aspect ratio)"""
    print("\n" + "="*60)
    print("Demo 3: Elongated Tetrahedron")
    print("="*60)

    mesh = MeshData(element_type=ElementType.TET4)

    node_ids = []
    node_ids.append(mesh.add_node(0.0, 0.0, 0.0))
    node_ids.append(mesh.add_node(10.0, 0.0, 0.0))  # Very long edge
    node_ids.append(mesh.add_node(0.0, 1.0, 0.0))
    node_ids.append(mesh.add_node(0.0, 0.0, 1.0))
    mesh.add_element(node_ids)

    metrics = AdvancedQualityMetrics(mesh)
    eid = list(mesh.elements.keys())[0]

    print(f"\nElongated tet quality:")
    print(f"  Jacobian ratio: {metrics.compute_jacobian_ratio(eid):.4f}")
    print(f"  Skewness:       {metrics.compute_skewness(eid):.4f}")
    print(f"  Aspect ratio:   {metrics.compute_aspect_ratio(eid):.4f}")
    print(f"\nNote: High aspect ratio (>3) indicates poor element shape")


def demo_multi_element_analysis():
    """Analyze mesh with multiple elements"""
    print("\n" + "="*60)
    print("Demo 4: Multi-Element Mesh Analysis")
    print("="*60)

    # Create mesh with good and bad elements
    mesh = MeshData(element_type=ElementType.TET4)

    # Good element
    node_ids = []
    node_ids.append(mesh.add_node(0.0, 0.0, 0.0))
    node_ids.append(mesh.add_node(1.0, 0.0, 0.0))
    node_ids.append(mesh.add_node(0.5, np.sqrt(3)/2, 0.0))
    node_ids.append(mesh.add_node(0.5, np.sqrt(3)/6, np.sqrt(2/3)))
    mesh.add_element(node_ids)

    # Bad element (elongated)
    node_ids = []
    node_ids.append(mesh.add_node(2.0, 0.0, 0.0))
    node_ids.append(mesh.add_node(8.0, 0.0, 0.0))
    node_ids.append(mesh.add_node(2.0, 1.0, 0.0))
    node_ids.append(mesh.add_node(2.0, 0.0, 1.0))
    mesh.add_element(node_ids)

    # Another good element
    node_ids = []
    node_ids.append(mesh.add_node(0.0, 2.0, 0.0))
    node_ids.append(mesh.add_node(1.0, 2.0, 0.0))
    node_ids.append(mesh.add_node(0.0, 3.0, 0.0))
    node_ids.append(mesh.add_node(0.0, 2.0, 1.0))
    mesh.add_element(node_ids)

    print(f"\nAnalyzing mesh with {len(mesh.elements)} elements...")
    metrics = analyze_mesh_quality(mesh, print_report=True)


def demo_quality_report():
    """Generate comprehensive quality report"""
    print("\n" + "="*60)
    print("Demo 5: Comprehensive Quality Report")
    print("="*60)

    # Create structured hex mesh
    mesh = MeshData(element_type=ElementType.HEX8)

    # 3x3x3 grid
    node_ids = []
    for i in range(4):
        for j in range(4):
            for k in range(4):
                # Add slight randomness for more interesting metrics
                dx = 0.1 * np.random.randn() if i > 0 and i < 3 else 0
                dy = 0.1 * np.random.randn() if j > 0 and j < 3 else 0
                dz = 0.1 * np.random.randn() if k > 0 and k < 3 else 0
                node_ids.append(mesh.add_node(float(i) + dx, float(j) + dy, float(k) + dz))

    # Create hex elements
    for i in range(3):
        for j in range(3):
            for k in range(3):
                n000 = i * 16 + j * 4 + k
                n100 = (i+1) * 16 + j * 4 + k
                n010 = i * 16 + (j+1) * 4 + k
                n110 = (i+1) * 16 + (j+1) * 4 + k
                n001 = i * 16 + j * 4 + (k+1)
                n101 = (i+1) * 16 + j * 4 + (k+1)
                n011 = i * 16 + (j+1) * 4 + (k+1)
                n111 = (i+1) * 16 + (j+1) * 4 + (k+1)

                mesh.add_element([node_ids[n000], node_ids[n100], node_ids[n110], node_ids[n010],
                                 node_ids[n001], node_ids[n101], node_ids[n111], node_ids[n011]])

    print(f"\nStructured mesh: {len(mesh.nodes)} nodes, {len(mesh.elements)} elements")

    analyzer = AdvancedQualityMetrics(mesh)
    print(analyzer.generate_report())


def demo_element_by_element():
    """Show element-by-element quality metrics"""
    print("\n" + "="*60)
    print("Demo 6: Element-by-Element Analysis")
    print("="*60)

    mesh = MeshData(element_type=ElementType.TET4)

    # Create 3 tets with varying quality
    specs = [
        ("Good", [(0, 0, 0), (1, 0, 0), (0.5, 0.866, 0), (0.5, 0.289, 0.816)]),
        ("Fair", [(2, 0, 0), (3, 0, 0), (2, 1, 0), (2, 0, 2)]),
        ("Poor", [(4, 0, 0), (8, 0, 0), (4, 0.5, 0), (4, 0, 0.5)])
    ]

    eids = []
    for name, coords in specs:
        node_ids = [mesh.add_node(*coord) for coord in coords]
        eids.append(mesh.add_element(node_ids))

    metrics = AdvancedQualityMetrics(mesh)

    print(f"\nElement-by-element comparison:")
    print(f"\n{'Element':<10} {'Jacobian':<12} {'Skewness':<12} {'Aspect':<12}")
    print("-" * 46)

    for i, (name, _) in enumerate(specs):
        eid = eids[i]
        j = metrics.compute_jacobian_ratio(eid)
        s = metrics.compute_skewness(eid)
        a = metrics.compute_aspect_ratio(eid)
        print(f"{name:<10} {j:<12.4f} {s:<12.4f} {a:<12.4f}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("ADVANCED MESH QUALITY METRICS DEMONSTRATIONS")
    print("="*60)

    # Set random seed for reproducibility
    np.random.seed(42)

    demo_perfect_cube_metrics()
    demo_distorted_hex()
    demo_elongated_tet()
    demo_multi_element_analysis()
    demo_quality_report()
    demo_element_by_element()

    print("\n" + "="*60)
    print("All demos completed!")
    print("="*60)
    print("\nQuality Metric Guidelines:")
    print("  - Jacobian Ratio: >0.3 good, <0.1 poor")
    print("  - Skewness: <0.5 good, >0.8 poor")
    print("  - Aspect Ratio: <3 good, >10 poor")
