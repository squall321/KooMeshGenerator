"""
Mesh Quality Reporter Demo
===========================

This example demonstrates the mesh quality reporting features added in [009]:

1. HTML report generation with visualizations
2. PDF report generation
3. Plain text summary generation
4. Multiple mesh comparison
5. Custom quality checker configuration

The reporter generates comprehensive quality reports including:
- Quality metrics (Jacobian, aspect ratio, skewness, angles)
- Quality distribution (Excellent/Good/Fair/Poor/Bad)
- Visualizations (pie charts, histograms, box plots)
- Element-by-element analysis
- Problem element identification
"""

import os
from pathlib import Path
from koomesh.meshing.mesh_data import MeshData, ElementType
from koomesh.utils.mesh_reporter import MeshReporter
from koomesh.meshing.quality_checker import QualityChecker


def create_test_meshes():
    """Create test meshes with varying quality"""
    meshes = {}

    # Mesh 1: Excellent quality - perfect cubes
    print("\nCreating high-quality mesh...")
    mesh1 = MeshData(element_type=ElementType.HEX8)
    for ix in range(3):
        for iy in range(3):
            for iz in range(3):
                coords = [
                    [ix, iy, iz],
                    [ix+1, iy, iz],
                    [ix+1, iy+1, iz],
                    [ix, iy+1, iz],
                    [ix, iy, iz+1],
                    [ix+1, iy, iz+1],
                    [ix+1, iy+1, iz+1],
                    [ix, iy+1, iz+1],
                ]
                node_ids = [mesh1.add_node(x, y, z) for x, y, z in coords]
                mesh1.add_element(node_ids)
    meshes['high_quality'] = mesh1

    # Mesh 2: Mixed quality
    print("Creating mixed-quality mesh...")
    mesh2 = MeshData(element_type=ElementType.HEX8)

    # Good element
    coords_good = [
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [1.0, 1.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
        [1.0, 0.0, 1.0],
        [1.0, 1.0, 1.0],
        [0.0, 1.0, 1.0],
    ]

    # Fair element (moderately distorted)
    coords_fair = [
        [2.0, 0.0, 0.0],
        [3.5, 0.0, 0.0],
        [3.5, 1.3, 0.0],
        [2.0, 1.3, 0.0],
        [2.0, 0.0, 0.8],
        [3.5, 0.0, 0.8],
        [3.5, 1.3, 0.8],
        [2.0, 1.3, 0.8],
    ]

    # Poor element (heavily distorted)
    coords_poor = [
        [4.0, 0.0, 0.0],
        [8.0, 0.0, 0.0],
        [8.0, 0.6, 0.0],
        [4.0, 0.6, 0.0],
        [4.0, 0.0, 0.5],
        [8.0, 0.0, 0.5],
        [8.0, 0.6, 0.5],
        [4.0, 0.6, 0.5],
    ]

    # Bad element (extremely distorted)
    coords_bad = [
        [9.0, 0.0, 0.0],
        [15.0, 0.0, 0.0],
        [15.0, 0.4, 0.0],
        [9.0, 0.4, 0.0],
        [9.0, 0.0, 0.3],
        [15.0, 0.0, 0.3],
        [15.0, 0.4, 0.3],
        [9.0, 0.4, 0.3],
    ]

    for coords in [coords_good, coords_fair, coords_poor, coords_bad]:
        node_ids = [mesh2.add_node(x, y, z) for x, y, z in coords]
        mesh2.add_element(node_ids)

    meshes['mixed_quality'] = mesh2

    return meshes


def demo_html_report_generation():
    """Demonstrate HTML report generation"""
    print("\n" + "="*70)
    print("Demo 1: HTML Report Generation")
    print("="*70)

    meshes = create_test_meshes()
    reporter = MeshReporter()

    # Generate HTML reports for both meshes
    output_dir = Path("/tmp/mesh_reports")
    output_dir.mkdir(exist_ok=True)

    for name, mesh in meshes.items():
        output_file = output_dir / f"{name}_report.html"
        print(f"\nGenerating HTML report for {name} mesh...")
        print(f"  Elements: {mesh.num_elements()}")
        print(f"  Nodes: {mesh.num_nodes()}")

        reporter.generate_html_report(
            mesh, str(output_file),
            include_charts=True
        )

        print(f"✓ Report generated: {output_file}")
        print(f"  File size: {output_file.stat().st_size / 1024:.1f} KB")

    print(f"\n✓ All HTML reports saved to: {output_dir}")


def demo_pdf_report_generation():
    """Demonstrate PDF report generation"""
    print("\n" + "="*70)
    print("Demo 2: PDF Report Generation")
    print("="*70)

    meshes = create_test_meshes()
    reporter = MeshReporter()

    output_dir = Path("/tmp/mesh_reports")
    output_dir.mkdir(exist_ok=True)

    try:
        import weasyprint
        pdf_available = True
    except ImportError:
        pdf_available = False
        print("\n⚠ WeasyPrint not installed - PDF generation skipped")
        print("  Install with: pip install weasyprint")
        return

    for name, mesh in meshes.items():
        output_file = output_dir / f"{name}_report.pdf"
        print(f"\nGenerating PDF report for {name} mesh...")

        reporter.generate_pdf_report(
            mesh, str(output_file),
            include_charts=True
        )

        print(f"✓ PDF report generated: {output_file}")
        print(f"  File size: {output_file.stat().st_size / 1024:.1f} KB")

    print(f"\n✓ All PDF reports saved to: {output_dir}")


def demo_text_summary():
    """Demonstrate plain text summary generation"""
    print("\n" + "="*70)
    print("Demo 3: Plain Text Summary")
    print("="*70)

    meshes = create_test_meshes()
    reporter = MeshReporter()

    for name, mesh in meshes.items():
        print(f"\nSummary for {name} mesh:")
        print("-" * 70)

        summary = reporter.generate_summary_text(mesh)
        print(summary)


def demo_custom_quality_checker():
    """Demonstrate custom quality checker configuration"""
    print("\n" + "="*70)
    print("Demo 4: Custom Quality Checker Configuration")
    print("="*70)

    meshes = create_test_meshes()
    mesh = meshes['mixed_quality']

    print("\nComparing reports with different quality thresholds...\n")

    # Strict quality checker
    print("Strict Quality Criteria:")
    print("-" * 70)
    strict_checker = QualityChecker(
        jacobian_threshold=0.5,
        aspect_ratio_threshold=5.0,
        skewness_threshold=0.5
    )
    strict_reporter = MeshReporter(quality_checker=strict_checker)
    strict_summary = strict_reporter.generate_summary_text(mesh)
    print(strict_summary)

    print("\n")

    # Lenient quality checker
    print("Lenient Quality Criteria:")
    print("-" * 70)
    lenient_checker = QualityChecker(
        jacobian_threshold=0.01,
        aspect_ratio_threshold=50.0,
        skewness_threshold=0.95
    )
    lenient_reporter = MeshReporter(quality_checker=lenient_checker)
    lenient_summary = lenient_reporter.generate_summary_text(mesh)
    print(lenient_summary)


def demo_quality_comparison():
    """Demonstrate quality comparison between meshes"""
    print("\n" + "="*70)
    print("Demo 5: Quality Comparison")
    print("="*70)

    meshes = create_test_meshes()
    reporter = MeshReporter()

    print("\nComparing mesh quality metrics:\n")

    results = {}
    for name, mesh in meshes.items():
        checker = QualityChecker()
        report = checker.check_mesh(mesh)
        results[name] = report

    # Print comparison table
    print(f"{'Mesh':<20} {'Elements':<10} {'Bad Elem':<10} {'Min Jac':<12} {'Max Aspect':<12}")
    print("-" * 70)

    for name, report in results.items():
        print(f"{name:<20} {report.num_elements:<10} {report.num_bad_elements:<10} "
              f"{report.jacobian['min']:<12.6f} {report.aspect_ratio['max']:<12.3f}")


def demo_chart_only_generation():
    """Demonstrate generating charts without full report"""
    print("\n" + "="*70)
    print("Demo 6: Standalone Chart Generation")
    print("="*70)

    meshes = create_test_meshes()
    mesh = meshes['mixed_quality']

    reporter = MeshReporter()

    output_dir = Path("/tmp/mesh_reports/charts")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nGenerating standalone quality charts...")

    # Generate HTML report with charts
    html_file = output_dir.parent / "temp_report.html"
    reporter.generate_html_report(mesh, str(html_file), include_charts=True)

    # Count generated charts
    chart_files = list(output_dir.parent.glob("temp_report_*.png"))
    print(f"✓ Generated {len(chart_files)} chart files:")
    for chart_file in sorted(chart_files):
        print(f"  - {chart_file.name} ({chart_file.stat().st_size / 1024:.1f} KB)")

    # Clean up temp HTML
    if html_file.exists():
        html_file.unlink()


def demo_batch_processing():
    """Demonstrate batch processing of multiple meshes"""
    print("\n" + "="*70)
    print("Demo 7: Batch Processing")
    print("="*70)

    print("\nProcessing multiple meshes in batch...")

    # Create multiple meshes with different sizes
    mesh_configs = [
        ("1x1x1", 1, 1, 1),
        ("2x2x2", 2, 2, 2),
        ("3x3x3", 3, 3, 3),
    ]

    reporter = MeshReporter()
    output_dir = Path("/tmp/mesh_reports/batch")
    output_dir.mkdir(parents=True, exist_ok=True)

    for name, nx, ny, nz in mesh_configs:
        print(f"\nProcessing {name} mesh...")

        # Create mesh
        mesh = MeshData(element_type=ElementType.HEX8)
        for ix in range(nx):
            for iy in range(ny):
                for iz in range(nz):
                    coords = [
                        [ix, iy, iz],
                        [ix+1, iy, iz],
                        [ix+1, iy+1, iz],
                        [ix, iy+1, iz],
                        [ix, iy, iz+1],
                        [ix+1, iy, iz+1],
                        [ix+1, iy+1, iz+1],
                        [ix, iy+1, iz+1],
                    ]
                    node_ids = [mesh.add_node(x, y, z) for x, y, z in coords]
                    mesh.add_element(node_ids)

        # Generate report
        html_file = output_dir / f"mesh_{name}_report.html"
        reporter.generate_html_report(mesh, str(html_file), include_charts=False)

        print(f"  ✓ {mesh.num_elements()} elements")
        print(f"  ✓ Report: {html_file}")

    print(f"\n✓ Batch processing complete: {output_dir}")


def main():
    """Run all demonstrations"""
    print("="*70)
    print("KooMeshGenerator: Mesh Quality Reporter Demo")
    print("="*70)
    print("\nThis demo showcases mesh quality reporting features ([009]):")
    print("  • HTML report generation with charts")
    print("  • PDF report generation (requires weasyprint)")
    print("  • Plain text summaries")
    print("  • Custom quality criteria")
    print("  • Batch processing")
    print("  • Quality comparison")

    # Run all demonstrations
    demo_html_report_generation()
    demo_text_summary()
    demo_custom_quality_checker()
    demo_quality_comparison()
    demo_chart_only_generation()
    demo_batch_processing()
    demo_pdf_report_generation()  # Last because it may not be available

    print("\n" + "="*70)
    print("Demo Complete!")
    print("="*70)
    print("\nGenerated files:")
    print("  HTML reports: /tmp/mesh_reports/*.html")
    print("  PDF reports:  /tmp/mesh_reports/*.pdf (if weasyprint installed)")
    print("  Charts:       /tmp/mesh_reports/*_*.png")
    print("\nKey Features:")
    print("  • Comprehensive quality metrics")
    print("  • Visual quality distribution charts")
    print("  • Element-by-element analysis")
    print("  • Problem element identification")
    print("  • Multiple output formats (HTML/PDF/TXT)")
    print("  • Customizable quality thresholds")


if __name__ == '__main__':
    main()
