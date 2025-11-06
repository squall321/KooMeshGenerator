"""
Mesh Quality Checker Demo
==========================

This example demonstrates the extended mesh quality checking features
added in [007]:

1. Basic quality checking with comprehensive metrics
2. Element-by-element quality analysis
3. Quality distribution and grading
4. CSV/JSON export capabilities
5. Histogram generation
6. Detailed reporting

The quality checker evaluates multiple metrics:
- Jacobian determinant
- Aspect ratio
- Skewness
- Warpage (hex elements)
- Element angles
- Edge length ratios
- Overall quality grade (Excellent/Good/Fair/Poor/Bad)
"""

import numpy as np
from pathlib import Path
from koomesh.meshing.mesh_data import MeshData, ElementType
from koomesh.meshing.quality_checker import QualityChecker


def create_test_mesh():
    """Create a test mesh with elements of varying quality"""
    print("\nCreating test mesh with varying quality elements...")
    mesh = MeshData(element_type=ElementType.HEX8)

    # Element 1: Excellent quality - perfect cube
    coords1 = [
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [1.0, 1.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
        [1.0, 0.0, 1.0],
        [1.0, 1.0, 1.0],
        [0.0, 1.0, 1.0],
    ]

    # Element 2: Good quality - slightly non-uniform
    coords2 = [
        [2.0, 0.0, 0.0],
        [3.1, 0.0, 0.0],
        [3.1, 1.0, 0.0],
        [2.0, 1.0, 0.0],
        [2.0, 0.0, 0.9],
        [3.1, 0.0, 0.9],
        [3.1, 1.0, 0.9],
        [2.0, 1.0, 0.9],
    ]

    # Element 3: Fair quality - moderately distorted
    coords3 = [
        [4.0, 0.0, 0.0],
        [5.5, 0.0, 0.0],
        [5.5, 1.2, 0.0],
        [4.0, 1.2, 0.0],
        [4.0, 0.0, 0.7],
        [5.5, 0.0, 0.7],
        [5.5, 1.2, 0.7],
        [4.0, 1.2, 0.7],
    ]

    # Element 4: Poor quality - heavily distorted
    coords4 = [
        [6.0, 0.0, 0.0],
        [9.0, 0.0, 0.0],  # Very stretched
        [9.0, 0.8, 0.0],
        [6.0, 0.8, 0.0],
        [6.0, 0.0, 0.5],
        [9.0, 0.0, 0.5],
        [9.0, 0.8, 0.5],
        [6.0, 0.8, 0.5],
    ]

    # Element 5: Bad quality - extremely distorted
    coords5 = [
        [10.0, 0.0, 0.0],
        [15.0, 0.0, 0.0],  # Extremely stretched
        [15.0, 0.4, 0.0],
        [10.0, 0.4, 0.0],
        [10.0, 0.0, 0.3],
        [15.0, 0.0, 0.3],
        [15.0, 0.4, 0.3],
        [10.0, 0.4, 0.3],
    ]

    # Add all elements
    element_names = ["Excellent", "Good", "Fair", "Poor", "Bad"]
    for i, coords in enumerate([coords1, coords2, coords3, coords4, coords5], 1):
        node_ids = [mesh.add_node(x, y, z) for x, y, z in coords]
        mesh.add_element(node_ids)
        print(f"  Element {i}: {element_names[i-1]} quality (target)")

    print(f"\nCreated mesh with {mesh.num_elements()} elements")
    return mesh


def demo_basic_quality_check():
    """Demonstrate basic quality checking"""
    print("\n" + "="*70)
    print("Demo 1: Basic Quality Checking")
    print("="*70)

    mesh = create_test_mesh()
    checker = QualityChecker()

    # Perform quality check
    print("\nPerforming quality check...")
    report = checker.check_mesh(mesh)

    # Display summary
    print("\n" + report.summary())

    # Check if mesh is valid
    if report.is_valid():
        print("\n✓ Mesh passed quality checks")
    else:
        print("\n✗ Mesh failed quality checks")
        print(f"  Found {report.num_bad_elements} bad elements")


def demo_quality_distribution():
    """Demonstrate quality distribution analysis"""
    print("\n" + "="*70)
    print("Demo 2: Quality Distribution Analysis")
    print("="*70)

    mesh = create_test_mesh()
    checker = QualityChecker()

    report = checker.check_mesh(mesh)

    print("\nQuality Grade Distribution:")
    print("-" * 70)
    for grade in ['Excellent', 'Good', 'Fair', 'Poor', 'Bad']:
        count = report.quality_distribution.get(grade, 0)
        percentage = (count / report.num_elements * 100) if report.num_elements > 0 else 0
        bar = "█" * int(percentage / 5)  # Scale bar
        print(f"{grade:10s}: {count:3d} ({percentage:5.1f}%) {bar}")

    print(f"\nTotal: {report.num_elements} elements")


def demo_element_by_element_analysis():
    """Demonstrate element-by-element quality analysis"""
    print("\n" + "="*70)
    print("Demo 3: Element-by-Element Analysis")
    print("="*70)

    mesh = create_test_mesh()
    checker = QualityChecker()

    print("\nAnalyzing each element individually...")
    print("-" * 70)

    for elem_id in sorted(mesh.elements.keys()):
        elem = mesh.get_element(elem_id)
        elem_report = checker.get_element_report(elem, mesh)

        print(f"\nElement {elem_id}:")
        print(f"  Quality Grade:     {elem_report['quality_grade']}")
        print(f"  Jacobian:          {elem_report['jacobian']:.6f}")
        print(f"  Aspect Ratio:      {elem_report['aspect_ratio']:.3f}")
        print(f"  Skewness:          {elem_report['skewness']:.3f}")
        print(f"  Min Angle:         {elem_report['min_angle']:.2f}°")
        print(f"  Max Angle:         {elem_report['max_angle']:.2f}°")
        print(f"  Edge Length Ratio: {elem_report['edge_length_ratio']:.3f}")


def demo_detailed_report():
    """Demonstrate detailed comprehensive reporting"""
    print("\n" + "="*70)
    print("Demo 4: Detailed Comprehensive Report")
    print("="*70)

    mesh = create_test_mesh()
    checker = QualityChecker()

    print("\nGenerating detailed report...")
    detailed_report = checker.get_detailed_report(mesh)
    print("\n" + detailed_report)


def demo_histogram_generation():
    """Demonstrate histogram generation for quality metrics"""
    print("\n" + "="*70)
    print("Demo 5: Quality Metric Histograms")
    print("="*70)

    mesh = create_test_mesh()
    checker = QualityChecker()

    metrics = ['jacobian', 'aspect_ratio', 'skewness']

    for metric in metrics:
        print(f"\n{metric.upper()} Histogram:")
        print("-" * 70)

        hist = checker.get_quality_histogram(mesh, metric, bins=5)

        for i, (bin_range, count) in enumerate(zip(hist['bins'], hist['counts'])):
            bar = "█" * (count * 10)  # Scale bar
            print(f"{bin_range}: {count:2d} {bar}")


def demo_csv_export():
    """Demonstrate CSV export functionality"""
    print("\n" + "="*70)
    print("Demo 6: CSV Export")
    print("="*70)

    mesh = create_test_mesh()
    checker = QualityChecker()

    output_file = "/tmp/mesh_quality_report.csv"
    print(f"\nExporting quality metrics to CSV: {output_file}")

    checker.export_to_csv(mesh, output_file)

    print(f"✓ Successfully exported to {output_file}")

    # Display first few lines
    print("\nCSV Preview (first 3 elements):")
    print("-" * 70)
    with open(output_file, 'r') as f:
        lines = f.readlines()
        for line in lines[:4]:  # Header + 3 elements
            print(line.rstrip())


def demo_json_export():
    """Demonstrate JSON export functionality"""
    print("\n" + "="*70)
    print("Demo 7: JSON Export")
    print("="*70)

    mesh = create_test_mesh()
    checker = QualityChecker()

    output_file = "/tmp/mesh_quality_report.json"
    print(f"\nExporting quality metrics to JSON: {output_file}")

    checker.export_to_json(mesh, output_file)

    print(f"✓ Successfully exported to {output_file}")

    # Display JSON structure
    print("\nJSON Structure:")
    print("-" * 70)
    import json
    with open(output_file, 'r') as f:
        data = json.load(f)

    print(f"Summary:")
    print(f"  - Number of elements: {data['summary']['num_elements']}")
    print(f"  - Bad elements: {data['summary']['num_bad_elements']}")
    print(f"\nQuality Distribution:")
    for grade, count in data['summary']['quality_distribution'].items():
        print(f"  - {grade}: {count}")

    print(f"\nFirst element details:")
    elem = data['elements'][0]
    print(f"  - Element ID: {elem['element_id']}")
    print(f"  - Quality Grade: {elem['quality_grade']}")
    print(f"  - Jacobian: {elem['metrics']['jacobian']:.6f}")
    print(f"  - Aspect Ratio: {elem['metrics']['aspect_ratio']:.3f}")


def demo_quality_threshold_tuning():
    """Demonstrate quality threshold tuning"""
    print("\n" + "="*70)
    print("Demo 8: Quality Threshold Tuning")
    print("="*70)

    mesh = create_test_mesh()

    print("\nComparing different quality threshold settings...")
    print("-" * 70)

    # Default thresholds
    checker1 = QualityChecker()
    report1 = checker1.check_mesh(mesh)

    print("\nDefault Thresholds:")
    print(f"  Jacobian threshold:     0.1")
    print(f"  Aspect ratio threshold: 10.0")
    print(f"  Skewness threshold:     0.8")
    print(f"  → Bad elements: {report1.num_bad_elements}")

    # Strict thresholds
    checker2 = QualityChecker(
        jacobian_threshold=0.5,
        aspect_ratio_threshold=5.0,
        skewness_threshold=0.5
    )
    report2 = checker2.check_mesh(mesh)

    print("\nStrict Thresholds:")
    print(f"  Jacobian threshold:     0.5")
    print(f"  Aspect ratio threshold: 5.0")
    print(f"  Skewness threshold:     0.5")
    print(f"  → Bad elements: {report2.num_bad_elements}")

    # Lenient thresholds
    checker3 = QualityChecker(
        jacobian_threshold=0.01,
        aspect_ratio_threshold=50.0,
        skewness_threshold=0.95
    )
    report3 = checker3.check_mesh(mesh)

    print("\nLenient Thresholds:")
    print(f"  Jacobian threshold:     0.01")
    print(f"  Aspect ratio threshold: 50.0")
    print(f"  Skewness threshold:     0.95")
    print(f"  → Bad elements: {report3.num_bad_elements}")


def demo_quality_metrics_comparison():
    """Demonstrate comparison of quality metrics"""
    print("\n" + "="*70)
    print("Demo 9: Quality Metrics Comparison")
    print("="*70)

    mesh = create_test_mesh()
    checker = QualityChecker()
    report = checker.check_mesh(mesh)

    print("\nComparative Analysis of Quality Metrics:")
    print("-" * 70)

    metrics = [
        ('Jacobian', report.jacobian),
        ('Aspect Ratio', report.aspect_ratio),
        ('Skewness', report.skewness),
        ('Angles', report.angles),
        ('Edge Length Ratio', report.edge_length_ratio),
    ]

    for name, metric_data in metrics:
        print(f"\n{name}:")
        print(f"  Range:  [{metric_data.get('min', 0):.3f}, {metric_data.get('max', 0):.3f}]")
        print(f"  Mean:   {metric_data.get('mean', 0):.3f}")
        if 'std' in metric_data:
            print(f"  Std:    {metric_data.get('std', 0):.3f}")
        if 'median' in metric_data:
            print(f"  Median: {metric_data.get('median', 0):.3f}")


def main():
    """Run all demonstrations"""
    print("="*70)
    print("KooMeshGenerator: Quality Checker Demo")
    print("="*70)
    print("\nThis demo showcases extended quality checking features ([007]):")
    print("  • Element quality grading (Excellent/Good/Fair/Poor/Bad)")
    print("  • Comprehensive angle analysis")
    print("  • Edge length ratio metrics")
    print("  • Quality distribution statistics")
    print("  • Element-by-element analysis")
    print("  • CSV/JSON export capabilities")
    print("  • Histogram generation")
    print("  • Detailed reporting")

    # Run all demonstrations
    demo_basic_quality_check()
    demo_quality_distribution()
    demo_element_by_element_analysis()
    demo_detailed_report()
    demo_histogram_generation()
    demo_csv_export()
    demo_json_export()
    demo_quality_threshold_tuning()
    demo_quality_metrics_comparison()

    print("\n" + "="*70)
    print("Demo Complete!")
    print("="*70)
    print("\nOutput files generated:")
    print("  - /tmp/mesh_quality_report.csv")
    print("  - /tmp/mesh_quality_report.json")
    print("\nKey Takeaways:")
    print("  • Quality checker provides comprehensive mesh analysis")
    print("  • Multiple metrics evaluate different quality aspects")
    print("  • Export capabilities enable integration with other tools")
    print("  • Element grading helps identify problematic regions")
    print("  • Threshold tuning allows customization for specific needs")


if __name__ == '__main__':
    main()
