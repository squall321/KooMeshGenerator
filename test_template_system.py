#!/usr/bin/env python3
"""Test script for template system"""

import sys
from pathlib import Path

# Add koomesh to path
sys.path.insert(0, str(Path(__file__).parent))

from koomesh.templates import TemplateManager, list_templates, load_template
from koomesh.templates.template_validator import TemplateValidator
from koomesh.templates.template_customizer import TemplateCustomizer
from koomesh.materials.material_library import MaterialLibrary


def test_material_database():
    """Test material database loading"""
    print("=" * 70)
    print("Testing Material Database")
    print("=" * 70)

    library = MaterialLibrary()
    library.load_default_materials()

    print(f"✓ Loaded {len(library.materials)} materials")

    # Show categories
    categories = {}
    for mat in library.materials.values():
        mat_type = mat.material_type.value
        categories[mat_type] = categories.get(mat_type, 0) + 1

    print("\nMaterials by type:")
    for mat_type, count in sorted(categories.items()):
        print(f"  {mat_type}: {count}")

    # Show some example materials
    print("\nExample materials:")
    for i, name in enumerate(sorted(library.list_materials())[:10]):
        mat = library.get_material(name)
        print(f"  {i+1}. {name} ({mat.material_type.value})")

    print(f"  ... and {len(library.materials) - 10} more")
    print()


def test_template_manager():
    """Test template manager"""
    print("=" * 70)
    print("Testing Template Manager")
    print("=" * 70)

    manager = TemplateManager()
    manager.load_builtin_templates()

    print(f"✓ Loaded {len(manager.templates)} templates")

    # List by category
    from koomesh.templates.template_manager import TemplateCategory

    print("\nTemplates by category:")
    for category in TemplateCategory:
        templates = manager.list_templates(category)
        if templates:
            print(f"  {category.value}: {len(templates)}")
            for name in templates[:3]:
                print(f"    - {name}")
            if len(templates) > 3:
                print(f"    ... and {len(templates) - 3} more")

    # Show a specific template
    print("\nExample template: automotive_crash_frontal")
    template = manager.get_template("automotive_crash_frontal")
    if template:
        print(f"  Description: {template.description}")
        # Handle both enum and string values
        analysis_type = template.analysis_type if isinstance(template.analysis_type, str) else template.analysis_type.value
        print(f"  Analysis: {analysis_type} ({template.solver_type})")
        print(f"  Element size: {template.target_element_size} mm")
        print(f"  Duration: {template.analysis_duration} s")
        print(f"  Materials: {', '.join(template.materials[:3])}")
        print(f"  Tags: {', '.join(template.tags)}")
    print()


def test_template_validator():
    """Test template validator"""
    print("=" * 70)
    print("Testing Template Validator")
    print("=" * 70)

    library = MaterialLibrary()
    library.load_default_materials()

    validator = TemplateValidator(library)

    # Validate a template
    manager = TemplateManager()
    manager.load_builtin_templates()

    template = manager.get_template("automotive_crash_frontal")

    print(f"Validating template: {template.name}")
    result = validator.validate(template)

    print(result.get_summary())
    print()


def test_template_customizer():
    """Test template customizer"""
    print("=" * 70)
    print("Testing Template Customizer")
    print("=" * 70)

    library = MaterialLibrary()
    library.load_default_materials()

    customizer = TemplateCustomizer(library)

    # Load base template
    manager = TemplateManager()
    manager.load_builtin_templates()

    template = manager.get_template("automotive_crash_frontal")

    print(f"Base template: {template.name}")
    print(f"  Element size: {template.target_element_size} mm")
    print(f"  Duration: {template.analysis_duration} s")

    # Refine mesh
    refined = customizer.refine_mesh(template, factor=2.0)
    print(f"\n✓ Refined template: {refined.name}")
    print(f"  Element size: {refined.target_element_size} mm")

    # Coarsen mesh
    coarse = customizer.coarsen_mesh(template, factor=2.0)
    print(f"\n✓ Coarsened template: {coarse.name}")
    print(f"  Element size: {coarse.target_element_size} mm")

    # Optimize for speed
    fast = customizer.optimize_for_speed(template)
    print(f"\n✓ Fast variant: {fast.name}")
    print(f"  Element size: {fast.target_element_size} mm")
    print(f"  Output frequency: {fast.output_frequency}")

    # Optimize for accuracy
    accurate = customizer.optimize_for_accuracy(template)
    print(f"\n✓ Accurate variant: {accurate.name}")
    print(f"  Element size: {accurate.target_element_size} mm")
    print(f"  Output frequency: {accurate.output_frequency}")

    print()


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("KooMeshGenerator Template System Test Suite")
    print("=" * 70 + "\n")

    try:
        test_material_database()
        test_template_manager()
        test_template_validator()
        test_template_customizer()

        print("=" * 70)
        print("✓ All tests passed!")
        print("=" * 70)

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
