"""
Biomedical Implant Analysis Workflow
=====================================

Workflow for hip implant stress analysis using Phase 4 features.

This example demonstrates:
1. Loading biomedical template
2. Material selection for implants
3. Mesh refinement for critical regions
4. Quality-driven remeshing
"""

from koomesh.templates import load_template, search_templates
from koomesh.templates.template_customizer import TemplateCustomizer
from koomesh.materials.material_library import MaterialLibrary
from koomesh.quality import QualityAnalyzer


def main():
    """Run biomedical implant workflow"""
    print("=" * 70)
    print("Biomedical Implant Analysis Workflow")
    print("=" * 70)

    # Step 1: Find biomedical templates
    print("\n[1/5] Searching for biomedical templates...")
    templates = search_templates("implant")

    print(f"  ✓ Found {len(templates)} implant templates:")
    for t in templates:
        print(f"    - {t.name}: {t.description}")

    # Load hip implant template
    template = load_template("biomedical_hip_implant")
    print(f"\n  ✓ Using: {template.name}")

    # Step 2: Material selection
    print("\n[2/5] Selecting biocompatible materials...")
    library = MaterialLibrary()
    library.load_default_materials()

    # Find biocompatible materials
    biocompatible_materials = []
    for mat_name in library.list_materials():
        mat = library.get_material(mat_name)
        if mat.metadata.get("biocompatible", False):
            biocompatible_materials.append(mat_name)

    print(f"  ✓ Found {len(biocompatible_materials)} biocompatible materials:")
    for mat_name in biocompatible_materials:
        mat = library.get_material(mat_name)
        print(f"    - {mat_name}: {mat.metadata.get('description', 'N/A')}")

    # Step 3: Refine mesh for critical regions
    print("\n[3/5] Refining mesh for high-stress regions...")
    customizer = TemplateCustomizer(library)

    # Create extra-refined version for contact areas
    refined = customizer.refine_mesh(template, factor=3.0)
    print(f"  ✓ Original element size: {template.target_element_size}mm")
    print(f"  ✓ Refined element size: {refined.target_element_size}mm")
    print(f"  ✓ Min element size: {refined.min_element_size}mm")

    # Step 4: Quality requirements
    print("\n[4/5] Setting quality requirements...")
    print("  ⚙ Implant analysis requires high quality:")
    print("    - Min Jacobian: 0.4 (higher than default 0.3)")
    print("    - Max Aspect Ratio: 5.0 (stricter than default 10.0)")
    print("    - Max Skewness: 0.5 (stricter than default 0.7)")

    analyzer = QualityAnalyzer(quality_thresholds={
        'min_jacobian': 0.4,
        'max_aspect_ratio': 5.0,
        'max_skewness': 0.5,
        'overall_quality': 0.6,
    })

    print("  ✓ Quality analyzer configured with strict thresholds")

    # Step 5: Summary
    print("\n[5/5] Analysis setup complete")
    print("\n" + "=" * 70)
    print("Ready for Mesh Generation")
    print("=" * 70)
    print(f"Template: {refined.name}")
    print(f"Element size: {refined.min_element_size} - {refined.max_element_size}mm")
    print(f"Materials: {', '.join(refined.materials)}")
    print(f"Analysis type: {template.analysis_type}")
    print(f"Solver: {template.solver_type}")
    print("=" * 70)


if __name__ == "__main__":
    main()
