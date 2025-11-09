"""
Example 3: Automotive Crash Simulation Workflow

This example demonstrates a complete workflow for preparing an automotive
assembly for crash simulation, including:
- Material assignment
- Contact detection
- Contact quality validation
- Export for LS-DYNA
"""

import numpy as np
from pathlib import Path

from koomesh.materials.material_assigner import GeometryBasedMaterialAssigner
from koomesh.materials.material_validator import MaterialValidator
from koomesh.contact.assembly_contact import AssemblyContactManager
from koomesh.contact.contact_quality import ContactQualityChecker
from koomesh.meshing.mesh_data import MeshData


def create_automotive_assembly():
    """
    Create a simplified automotive front-end assembly.

    Parts:
    - Bumper beam (energy absorption)
    - Front rails (left/right, structural)
    - Hood (outer panel)
    - Radiator support (structural)
    """
    parts_with_geometry = []
    parts_with_mesh = []

    # Part 1: Bumper beam
    part_info = {
        'name': 'bumper_beam_front.step',
        'thickness': 3.0,
        'volume': 20000.0,
        'area': 6666.0
    }
    # Simple mesh representation
    nodes = np.array([
        [-500, 900, 400], [500, 900, 400],
        [500, 900, 450], [-500, 900, 450]
    ], dtype=float)
    elements = np.array([[0, 1, 2, 3]])
    mesh = MeshData(nodes=nodes, elements=elements)

    parts_with_geometry.append(part_info)
    parts_with_mesh.append(('Bumper_Beam', mesh))

    # Part 2: Front rail left
    part_info = {
        'name': 'rail_front_left.step',
        'thickness': 2.5,
        'volume': 18000.0,
        'area': 7200.0
    }
    nodes = np.array([
        [-300, 0, 400], [-300, 900, 400],
        [-300, 900, 450], [-300, 0, 450]
    ], dtype=float)
    elements = np.array([[0, 1, 2, 3]])
    mesh = MeshData(nodes=nodes, elements=elements)

    parts_with_geometry.append(part_info)
    parts_with_mesh.append(('Rail_Front_Left', mesh))

    # Part 3: Front rail right
    part_info = {
        'name': 'rail_front_right.step',
        'thickness': 2.5,
        'volume': 18000.0,
        'area': 7200.0
    }
    nodes = np.array([
        [300, 0, 400], [300, 900, 400],
        [300, 900, 450], [300, 0, 450]
    ], dtype=float)
    elements = np.array([[0, 1, 2, 3]])
    mesh = MeshData(nodes=nodes, elements=elements)

    parts_with_geometry.append(part_info)
    parts_with_mesh.append(('Rail_Front_Right', mesh))

    # Part 4: Hood
    part_info = {
        'name': 'hood_outer.step',
        'thickness': 0.8,
        'volume': 8000.0,
        'area': 10000.0
    }
    nodes = np.array([
        [-600, 0, 600], [600, 0, 600],
        [600, 1200, 650], [-600, 1200, 650]
    ], dtype=float)
    elements = np.array([[0, 1, 2, 3]])
    mesh = MeshData(nodes=nodes, elements=elements)

    parts_with_geometry.append(part_info)
    parts_with_mesh.append(('Hood', mesh))

    # Part 5: Radiator support
    part_info = {
        'name': 'radiator_support.step',
        'thickness': 2.0,
        'volume': 12000.0,
        'area': 6000.0
    }
    nodes = np.array([
        [-400, 800, 300], [400, 800, 300],
        [400, 800, 550], [-400, 800, 550]
    ], dtype=float)
    elements = np.array([[0, 1, 2, 3]])
    mesh = MeshData(nodes=nodes, elements=elements)

    parts_with_geometry.append(part_info)
    parts_with_mesh.append(('Radiator_Support', mesh))

    return parts_with_geometry, parts_with_mesh


def step1_material_assignment(parts_with_geometry):
    """Step 1: Assign materials to all parts"""
    print("\n" + "=" * 70)
    print("STEP 1: Material Assignment")
    print("=" * 70)
    print()

    assigner = GeometryBasedMaterialAssigner()

    print("Assigning materials using 'automotive_crash' template...")
    print()

    assignments = assigner.assign_by_template(
        parts_with_geometry,
        template='automotive_crash'
    )

    print(f"{'Part Name':35} {'Material':25} {'Strategy'}")
    print("-" * 70)
    for assignment in assignments:
        print(f"{assignment['part_name']:35} "
              f"{assignment['material']:25} "
              f"{assignment['strategy_used']}")

    print()
    return assignments


def step2_material_validation(assignments):
    """Step 2: Validate material assignments"""
    print("\n" + "=" * 70)
    print("STEP 2: Material Validation")
    print("=" * 70)
    print()

    validator = MaterialValidator()

    print("Validating materials for crash simulation...")
    print()

    all_valid = True
    validation_results = []

    for assignment in assignments:
        part_name = assignment['part_name']
        material_name = assignment['material']

        report = validator.validate_assignment(
            part_name=part_name,
            material_name=material_name,
            simulation_type='crash'
        )

        validation_results.append({
            'part': part_name,
            'material': material_name,
            'valid': report.valid,
            'report': report
        })

        status = "✓ PASS" if report.valid else "✗ FAIL"
        errors = sum(1 for i in report.issues if i.severity == 'ERROR')
        warnings = sum(1 for i in report.issues if i.severity == 'WARNING')

        print(f"{status} {part_name:35} (E:{errors}, W:{warnings})")

        if report.issues:
            for issue in report.issues:
                if issue.severity == 'ERROR':
                    print(f"     ✗ {issue.message}")
                    all_valid = False
                elif issue.severity == 'WARNING':
                    print(f"     ⚠ {issue.message}")

    print()
    if all_valid:
        print("✓ All materials passed validation!")
    else:
        print("✗ Some materials have errors. Review and fix before continuing.")

    print()
    return validation_results


def step3_contact_detection(parts_with_mesh):
    """Step 3: Detect contacts between parts"""
    print("\n" + "=" * 70)
    print("STEP 3: Contact Detection")
    print("=" * 70)
    print()

    manager = AssemblyContactManager()

    print("Detecting contacts (tolerance = 100 mm)...")
    print("(Using large tolerance for demonstration)")
    print()

    contact_pairs = manager.detect_contacts(
        parts_with_mesh,
        tolerance=100.0,  # Large tolerance for this simplified example
        auto_classify=True
    )

    print(f"Found {len(contact_pairs)} contact pairs:")
    print()

    for i, pair in enumerate(contact_pairs, 1):
        print(f"{i}. {pair.master_part:25} <-> {pair.slave_part:25}")
        print(f"   Type: {pair.contact_type.value:15} "
              f"Friction: {pair.parameters.fs:.2f} "
              f"SOFT: {pair.parameters.soft}")

        if pair.metadata:
            print(f"   Gap: {pair.metadata.get('gap', 0.0):.1f} mm, "
                  f"Area: {pair.metadata.get('area', 0.0):.0f} mm², "
                  f"Angle: {pair.metadata.get('angle', 0.0):.1f}°")
        print()

    return contact_pairs


def step4_contact_validation(contact_pairs, parts_with_mesh):
    """Step 4: Validate contact quality"""
    print("\n" + "=" * 70)
    print("STEP 4: Contact Quality Validation")
    print("=" * 70)
    print()

    checker = ContactQualityChecker()

    print("Checking contact quality for all pairs...")
    print()

    # Create a mapping of part names to meshes
    mesh_dict = {name: mesh for name, mesh in parts_with_mesh}

    all_passed = True
    quality_results = []

    for i, pair in enumerate(contact_pairs, 1):
        print(f"Contact {i}: {pair.master_part} <-> {pair.slave_part}")

        master_mesh = mesh_dict[pair.master_part]
        slave_mesh = mesh_dict[pair.slave_part]

        # Use all elements as contact surfaces for this example
        master_surfaces = np.arange(len(master_mesh.elements))
        slave_surfaces = np.arange(len(slave_mesh.elements))

        report = checker.check_contact_quality(
            master_mesh,
            slave_mesh,
            master_surfaces,
            slave_surfaces,
            tolerance=1.0
        )

        quality_results.append({
            'pair': pair,
            'report': report
        })

        status = "✓ PASS" if report.passed else "✗ FAIL"
        print(f"  {status} (Score: {report.score:.2f})")

        if not report.passed:
            all_passed = False

        # Show critical issues
        for issue in report.issues:
            if issue.severity == 'ERROR':
                print(f"     ✗ {issue.message}")
                print(f"        Fix: {issue.fix_suggestion}")

        print()

    if all_passed:
        print("✓ All contacts passed quality checks!")
    else:
        print("⚠ Some contacts have quality issues. Review before simulation.")

    print()
    return quality_results


def step5_export_summary(assignments, contact_pairs):
    """Step 5: Generate summary and export information"""
    print("\n" + "=" * 70)
    print("STEP 5: Summary and Export")
    print("=" * 70)
    print()

    print("Crash Simulation Setup Summary")
    print("-" * 70)
    print()

    # Parts summary
    print(f"Parts: {len(assignments)}")
    material_counts = {}
    for assignment in assignments:
        mat = assignment['material']
        material_counts[mat] = material_counts.get(mat, 0) + 1

    print("\nMaterial Distribution:")
    for material, count in sorted(material_counts.items()):
        print(f"  {material:30} {count:2} parts")

    # Contacts summary
    print(f"\nContacts: {len(contact_pairs)}")
    contact_type_counts = {}
    for pair in contact_pairs:
        ctype = pair.contact_type.value
        contact_type_counts[ctype] = contact_type_counts.get(ctype, 0) + 1

    print("\nContact Type Distribution:")
    for ctype, count in sorted(contact_type_counts.items()):
        print(f"  {ctype:30} {count:2} pairs")

    # Export information
    print("\nNext Steps:")
    print("  1. Export mesh to LS-DYNA format:")
    print("     $ koomesh export assembly.k --format lsdyna")
    print()
    print("  2. Export contact definitions:")
    print("     $ koomesh contact export contacts.k --format lsdyna")
    print()
    print("  3. Export material cards:")
    print("     $ koomesh material export materials.k")
    print()
    print("  4. Run LS-DYNA simulation:")
    print("     $ lsdyna i=crash_model.k")
    print()


def main():
    """Main workflow"""
    print("=" * 70)
    print("Automotive Crash Simulation - Complete Workflow")
    print("=" * 70)
    print()
    print("This example demonstrates the complete workflow for setting up")
    print("an automotive crash simulation:")
    print("  1. Material assignment")
    print("  2. Material validation")
    print("  3. Contact detection")
    print("  4. Contact quality validation")
    print("  5. Export preparation")
    print()

    # Create assembly
    print("Loading automotive front-end assembly...")
    parts_with_geometry, parts_with_mesh = create_automotive_assembly()
    print(f"  Loaded {len(parts_with_geometry)} parts")
    print()

    # Run workflow
    assignments = step1_material_assignment(parts_with_geometry)
    validation_results = step2_material_validation(assignments)
    contact_pairs = step3_contact_detection(parts_with_mesh)
    quality_results = step4_contact_validation(contact_pairs, parts_with_mesh)
    step5_export_summary(assignments, contact_pairs)

    print("=" * 70)
    print("Workflow Complete!")
    print("=" * 70)
    print()
    print("Your automotive crash model is ready for simulation.")
    print()


if __name__ == '__main__':
    main()
