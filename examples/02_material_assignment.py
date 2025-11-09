"""
Example 2: Material Assignment

This example demonstrates automatic material assignment for an automotive assembly.
"""

from koomesh.materials.material_assigner import (
    GeometryBasedMaterialAssigner,
    AssignmentStrategy
)
from koomesh.materials.material_validator import (
    MaterialValidator,
    MaterialRecommender
)


def create_sample_parts():
    """Create sample parts with geometry properties"""
    return [
        {
            'name': 'hood_outer_left.step',
            'thickness': 0.8,  # mm
            'volume': 4500.0,  # mm³
            'area': 5625.0     # mm²
        },
        {
            'name': 'hood_inner_left.step',
            'thickness': 0.9,
            'volume': 4000.0,
            'area': 4444.0
        },
        {
            'name': 'door_outer_fl.step',
            'thickness': 0.7,
            'volume': 3500.0,
            'area': 5000.0
        },
        {
            'name': 'door_inner_fl.step',
            'thickness': 1.2,
            'volume': 3000.0,
            'area': 2500.0
        },
        {
            'name': 'pillar_a_left.step',
            'thickness': 2.5,
            'volume': 15000.0,
            'area': 6000.0
        },
        {
            'name': 'pillar_b_left.step',
            'thickness': 2.0,
            'volume': 12000.0,
            'area': 6000.0
        },
        {
            'name': 'floor_front.step',
            'thickness': 1.5,
            'volume': 25000.0,
            'area': 16666.0
        },
        {
            'name': 'bumper_beam_front.step',
            'thickness': 3.0,
            'volume': 18000.0,
            'area': 6000.0
        },
        {
            'name': 'bumper_cover_front.step',
            'thickness': 3.5,
            'volume': 12000.0,
            'area': 3428.0
        },
        {
            'name': 'bracket_hood_hinge.step',
            'thickness': 4.0,
            'volume': 2000.0,
            'area': 500.0
        }
    ]


def example_filename_based():
    """Example 1: Filename-based assignment"""
    print("\n" + "=" * 60)
    print("Example 2a: Filename-Based Material Assignment")
    print("=" * 60)
    print()

    assigner = GeometryBasedMaterialAssigner()
    parts = create_sample_parts()

    print("Assigning materials using automotive template...")
    print()

    for part in parts:
        material = assigner.assign_by_filename(
            part['name'],
            template='automotive'
        )

        print(f"{part['name']:30} → {material}")

    print()


def example_geometry_based():
    """Example 2: Geometry-based assignment"""
    print("\n" + "=" * 60)
    print("Example 2b: Geometry-Based Material Assignment")
    print("=" * 60)
    print()

    assigner = GeometryBasedMaterialAssigner()
    parts = create_sample_parts()

    print("Assigning materials based on geometry properties...")
    print()
    print(f"{'Part Name':30} {'Thickness':>10} {'Material':>20}")
    print("-" * 60)

    for part in parts:
        material = assigner.assign_by_geometry(
            thickness=part['thickness'],
            volume=part['volume'],
            area=part['area']
        )

        print(f"{part['name']:30} {part['thickness']:>10.1f} mm {material:>20}")

    print()


def example_template_based():
    """Example 3: Template-based batch assignment"""
    print("\n" + "=" * 60)
    print("Example 2c: Template-Based Batch Assignment")
    print("=" * 60)
    print()

    assigner = GeometryBasedMaterialAssigner()
    parts = create_sample_parts()

    templates = ['automotive', 'automotive_crash']

    for template in templates:
        print(f"\nUsing template: {template}")
        print("-" * 60)

        assignments = assigner.assign_by_template(parts, template=template)

        print(f"{'Part Name':30} {'Material':>20} {'Strategy':>15}")
        print("-" * 60)
        for assignment in assignments:
            print(f"{assignment['part_name']:30} "
                  f"{assignment['material']:>20} "
                  f"{assignment['strategy_used']:>15}")

    print()


def example_validation():
    """Example 4: Material validation"""
    print("\n" + "=" * 60)
    print("Example 2d: Material Validation")
    print("=" * 60)
    print()

    validator = MaterialValidator()
    assigner = GeometryBasedMaterialAssigner()
    parts = create_sample_parts()[:3]  # Just first 3 parts

    # Assign materials
    assignments = assigner.assign_by_template(parts, template='automotive_crash')

    print("Validating material assignments for crash simulation...")
    print()

    for assignment in assignments:
        part_name = assignment['part_name']
        material_name = assignment['material']

        # Get part volume for validation
        part = next(p for p in parts if p['name'] == part_name)

        print(f"\nValidating: {part_name}")
        print(f"  Assigned material: {material_name}")

        report = validator.validate_assignment(
            part_name=part_name,
            material_name=material_name,
            simulation_type='crash',
            part_volume=part['volume']
        )

        if report.valid:
            print(f"  ✓ PASSED (score: {report.statistics.get('num_errors', 0)} errors, "
                  f"{report.statistics.get('num_warnings', 0)} warnings)")
        else:
            print(f"  ✗ FAILED")

        # Show issues
        if report.issues:
            for issue in report.issues:
                symbol = "⚠" if issue.severity == 'WARNING' else "✗"
                print(f"    {symbol} {issue.severity}: {issue.message}")
                if issue.suggestion:
                    print(f"      → {issue.suggestion}")

    print()


def example_recommendation():
    """Example 5: Material recommendation"""
    print("\n" + "=" * 60)
    print("Example 2e: Material Recommendation")
    print("=" * 60)
    print()

    recommender = MaterialRecommender()

    # Scenario 1: Structural beam for crash
    print("Scenario 1: Structural beam for crash simulation")
    print("Requirements: High strength (≥400 MPa), Moderate weight (≤8000 kg/m³)")
    print()

    recommendations = recommender.recommend_materials(
        part_name='Structural_Beam',
        simulation_type='crash',
        constraints={
            'min_strength': 400.0,
            'max_density': 8000.0
        },
        top_n=5
    )

    print(f"{'Rank':>4} {'Material':30} {'Score':>6} {'Reason'}")
    print("-" * 80)
    for i, (material, score, reason) in enumerate(recommendations, 1):
        print(f"{i:>4}. {material.name:30} {score:>6.2f} {reason}")

    print()

    # Scenario 2: Sheet metal for forming
    print("\nScenario 2: Sheet metal for forming simulation")
    print("Requirements: Good formability, Lightweight")
    print()

    recommendations = recommender.recommend_materials(
        part_name='Blank',
        simulation_type='forming',
        constraints={
            'formability': 'required',
            'max_density': 5000.0
        },
        top_n=5
    )

    print(f"{'Rank':>4} {'Material':30} {'Score':>6} {'Reason'}")
    print("-" * 80)
    for i, (material, score, reason) in enumerate(recommendations, 1):
        print(f"{i:>4}. {material.name:30} {score:>6.2f} {reason}")

    print()


def main():
    """Run all examples"""
    print("=" * 60)
    print("Material Assignment Examples")
    print("=" * 60)

    # Run all examples
    example_filename_based()
    example_geometry_based()
    example_template_based()
    example_validation()
    example_recommendation()

    print("\n" + "=" * 60)
    print("All examples complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()
