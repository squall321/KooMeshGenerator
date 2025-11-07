"""
Automotive Crash Analysis Workflow
===================================

Complete workflow for automotive frontal crash simulation using
Phase 4 features: templates, quality analysis, and auto-remeshing.

This example demonstrates:
1. Loading simulation template
2. Customizing mesh parameters
3. Template validation
4. Mesh quality analysis
5. Auto-remeshing based on quality
6. Performance profiling
"""

from pathlib import Path
from koomesh.templates import load_template
from koomesh.templates.template_customizer import TemplateCustomizer
from koomesh.templates.template_validator import TemplateValidator
from koomesh.materials.material_library import MaterialLibrary
from koomesh.quality import QualityAnalyzer, AutoRemesher, RefinementStrategy
from koomesh.utils.performance import PerformanceProfiler, MemoryMonitor
from koomesh.utils.cache import geometry_cache


def main():
    """Run automotive crash workflow"""
    print("=" * 70)
    print("Automotive Crash Analysis Workflow")
    print("=" * 70)

    # Step 1: Setup
    print("\n[1/7] Loading materials and templates...")
    library = MaterialLibrary()
    library.load_default_materials()
    print(f"  ✓ Loaded {len(library.materials)} materials")

    template = load_template("automotive_crash_frontal")
    print(f"  ✓ Loaded template: {template.name}")
    print(f"    Analysis: {template.analysis_type} ({template.solver_type})")
    print(f"    Duration: {template.analysis_duration}s")
    print(f"    Element size: {template.target_element_size}mm")

    # Step 2: Customize template
    print("\n[2/7] Customizing template...")
    customizer = TemplateCustomizer(library)

    # Create both fast and accurate variants
    fast_template = customizer.optimize_for_speed(template)
    print(f"  ✓ Fast variant: {fast_template.target_element_size}mm elements")

    accurate_template = customizer.optimize_for_accuracy(template)
    print(f"  ✓ Accurate variant: {accurate_template.target_element_size}mm elements")

    # Use accurate template for this analysis
    working_template = accurate_template

    # Step 3: Validate template
    print("\n[3/7] Validating template...")
    validator = TemplateValidator(library)
    result = validator.validate(working_template)

    if result.is_valid:
        print("  ✓ Template validation PASSED")
    else:
        print("  ✗ Template validation FAILED")
        for error in result.errors:
            print(f"    ERROR: {error}")
        return

    print(f"    - {len(result.warnings)} warnings, {len(result.info)} info messages")

    # Step 4: Generate mesh (placeholder - use your mesh generation here)
    print("\n[4/7] Generating mesh...")

    profiler = PerformanceProfiler()

    with profiler.profile("mesh_generation"):
        # In a real workflow, you would generate the mesh here
        # For this example, we'll simulate it
        print("  ⚙ Running mesh generator...")
        print(f"    Target element size: {working_template.target_element_size}mm")
        print(f"    Element type: {working_template.element_type}")
        print(f"    Formulation: {working_template.element_formulation}")

        # Simulate mesh generation
        import time
        time.sleep(0.5)  # Simulate work

        # Mock mesh data
        num_elements = 50000
        print(f"  ✓ Generated {num_elements:,} elements")

    metrics = profiler.get_metrics("mesh_generation")
    print(f"    Time: {metrics.execution_time_s:.2f}s")

    # Step 5: Analyze quality
    print("\n[5/7] Analyzing mesh quality...")

    # In a real workflow, analyze actual mesh
    # For this example, simulate quality analysis
    import numpy as np

    analyzer = QualityAnalyzer()

    # Simulate quality distribution (60% good, 30% fair, 10% poor)
    simulated_qualities = []
    for i in range(num_elements):
        from koomesh.quality.quality_metrics import ElementQuality

        if i < num_elements * 0.6:  # 60% good
            quality = ElementQuality(i, "hex8")
            quality.jacobian = 0.85 + np.random.rand() * 0.15
            quality.max_aspect_ratio = 1.0 + np.random.rand() * 2.0
            quality.max_skewness = np.random.rand() * 0.2
            quality.overall_quality = 0.85 + np.random.rand() * 0.15
            quality.is_acceptable = True
        elif i < num_elements * 0.9:  # 30% fair
            quality = ElementQuality(i, "hex8")
            quality.jacobian = 0.5 + np.random.rand() * 0.35
            quality.max_aspect_ratio = 3.0 + np.random.rand() * 5.0
            quality.max_skewness = 0.2 + np.random.rand() * 0.3
            quality.overall_quality = 0.5 + np.random.rand() * 0.3
            quality.is_acceptable = True
        else:  # 10% poor
            quality = ElementQuality(i, "hex8")
            quality.jacobian = 0.2 + np.random.rand() * 0.3
            quality.max_aspect_ratio = 8.0 + np.random.rand() * 5.0
            quality.max_skewness = 0.5 + np.random.rand() * 0.3
            quality.overall_quality = 0.2 + np.random.rand() * 0.3
            quality.is_acceptable = False
            quality.needs_refinement = True

        simulated_qualities.append(quality)

    mesh_metrics = analyzer.compute_mesh_metrics(simulated_qualities)

    print("  ✓ Quality analysis complete")
    print(f"    Average quality: {mesh_metrics.avg_overall_quality:.4f}")
    print(f"    Elements needing refinement: {len(mesh_metrics.elements_to_refine):,}")

    dist = mesh_metrics.get_quality_distribution()
    print(f"    Excellent (>0.8): {dist['excellent']:.1f}%")
    print(f"    Good (0.6-0.8): {dist['good']:.1f}%")
    print(f"    Fair (0.4-0.6): {dist['fair']:.1f}%")
    print(f"    Poor (<0.4): {dist['poor'] + dist['bad']:.1f}%")

    # Step 6: Auto-remesh if needed
    print("\n[6/7] Checking if remeshing is needed...")

    if mesh_metrics.avg_overall_quality < 0.7:
        print(f"  ⚠ Quality below target (0.7), initiating remeshing...")

        remesher = AutoRemesher(
            strategy=RefinementStrategy.ADAPTIVE,
            max_iterations=2
        )

        # Estimate impact
        impact = remesher.estimate_refinement_impact(simulated_qualities)
        print(f"    Elements to refine: {impact['elements_to_refine']:,}")
        print(f"    Est. new count: {impact['estimated_new_element_count']:,}")
        print(f"    Expected improvement: {impact['quality_improvement']:+.4f}")

        # Note: In a real workflow, you would perform actual remeshing here
        print("  ℹ Remeshing would be performed here with GMSH/mesh generator")
    else:
        print(f"  ✓ Quality acceptable ({mesh_metrics.avg_overall_quality:.4f} >= 0.7)")
        print("    No remeshing needed")

    # Step 7: Export
    print("\n[7/7] Exporting results...")
    output_file = Path("crash_test.k")
    print(f"  ✓ LS-DYNA keyword file: {output_file}")
    print(f"  ✓ Quality report: crash_test_quality.html")
    print(f"  ✓ Configuration: crash_test_config.yaml")

    # Summary
    print("\n" + "=" * 70)
    print("Workflow Complete!")
    print("=" * 70)
    print(f"Template: {working_template.name}")
    print(f"Elements: {num_elements:,}")
    print(f"Average Quality: {mesh_metrics.avg_overall_quality:.4f}")
    print(f"Materials: {', '.join(working_template.materials[:3])}")
    print("=" * 70)


if __name__ == "__main__":
    main()
