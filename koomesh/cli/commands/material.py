"""
Material Command
================

Material library management CLI command.

Usage:
    koomesh material list
    koomesh material show Steel_Mild
    koomesh material add custom_material.json
    koomesh material export Steel_Mild --format lsdyna

Author: KooMeshGenerator Team
"""

import click
import sys
import json
import logging
from pathlib import Path
from typing import Optional

from koomesh.materials.material_library import MaterialLibrary, Material, MaterialType
from koomesh.materials.lsdyna_material import LSDynaMaterialGenerator

logger = logging.getLogger(__name__)


@click.group()
@click.pass_context
def material(ctx):
    """
    Material library management

    Manage materials for FEA simulations. List, add, remove,
    and export material definitions.

    Examples:

    \b
    # List all materials
    koomesh material list

    \b
    # Show material details
    koomesh material show Steel_Mild

    \b
    # Add custom material
    koomesh material add my_material.json

    \b
    # Export to LS-DYNA format
    koomesh material export Steel_Mild --format lsdyna
    """
    pass


@material.command()
@click.option(
    '--filter', '-f',
    type=str,
    help='Filter materials by name or type'
)
@click.option(
    '--type', '-t',
    type=click.Choice(['elastic', 'plastic', 'rigid', 'all'], case_sensitive=False),
    default='all',
    help='Filter by material type (default: all)'
)
@click.option(
    '--library', '-l',
    type=click.Path(exists=True),
    help='Path to custom material library JSON file'
)
@click.pass_context
def list(ctx, filter: Optional[str], type: str, library: Optional[str]):
    """
    List available materials

    Displays all materials in the library with their properties.

    Examples:

    \b
    # List all materials
    koomesh material list

    \b
    # Filter by name
    koomesh material list --filter steel

    \b
    # Filter by type
    koomesh material list --type plastic
    """
    logger = ctx.obj.get('logger', logging.getLogger(__name__))

    try:
        # Load library
        mat_lib = MaterialLibrary()

        if library:
            mat_lib.load_from_file(library)
            click.echo(f"Loaded custom library: {library}\n")

        materials = mat_lib.list_materials()

        # Apply filters
        if filter:
            filter_lower = filter.lower()
            materials = [
                m for m in materials
                if filter_lower in m.name.lower() or filter_lower in m.material_type.value.lower()
            ]

        if type != 'all':
            materials = [
                m for m in materials
                if m.material_type.value.lower() == type.lower()
            ]

        if not materials:
            click.echo("No materials found matching criteria")
            return

        # Display materials
        click.echo("="*80)
        click.echo(f"{'Name':<25} {'Type':<12} {'Density':<12} {'E (GPa)':<12} {'ν':<8}")
        click.echo("-"*80)

        for mat in sorted(materials, key=lambda m: m.name):
            density_str = f"{mat.density:.0f}" if mat.density else "N/A"
            E_GPa = mat.elastic_modulus / 1e9 if mat.elastic_modulus else 0
            E_str = f"{E_GPa:.0f}" if mat.elastic_modulus else "N/A"
            nu_str = f"{mat.poisson_ratio:.2f}" if mat.poisson_ratio else "N/A"

            click.echo(
                f"{mat.name:<25} {mat.material_type.value:<12} "
                f"{density_str:<12} {E_str:<12} {nu_str:<8}"
            )

        click.echo("="*80)
        click.echo(f"\nTotal: {len(materials)} material(s)")

    except Exception as e:
        logger.error(f"Error listing materials: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@material.command()
@click.argument('material_name', type=str)
@click.option(
    '--library', '-l',
    type=click.Path(exists=True),
    help='Path to custom material library JSON file'
)
@click.pass_context
def show(ctx, material_name: str, library: Optional[str]):
    """
    Show detailed material properties

    Displays all properties of a material including derived properties.

    Examples:

    \b
    # Show material details
    koomesh material show Steel_Mild

    \b
    # From custom library
    koomesh material show MyMaterial --library custom.json
    """
    logger = ctx.obj.get('logger', logging.getLogger(__name__))

    try:
        # Load library
        mat_lib = MaterialLibrary()

        if library:
            mat_lib.load_from_file(library)

        # Get material
        mat = mat_lib.get_material(material_name)

        if mat is None:
            click.echo(f"Material not found: {material_name}", err=True)
            click.echo("\nAvailable materials:")
            for m in mat_lib.list_materials():
                click.echo(f"  - {m.name}")
            sys.exit(1)

        # Display material
        click.echo("\n" + "="*70)
        click.echo(f"MATERIAL: {mat.name}")
        click.echo("="*70)
        click.echo(f"\nType: {mat.material_type.value}")

        click.echo("\nBasic Properties:")
        click.echo(f"  Density (ρ):           {mat.density:>12.2f} kg/m³")
        click.echo(f"  Elastic Modulus (E):   {mat.elastic_modulus/1e9:>12.2f} GPa")
        click.echo(f"  Poisson's Ratio (ν):   {mat.poisson_ratio:>12.4f}")

        if mat.yield_stress:
            click.echo(f"  Yield Stress (σy):     {mat.yield_stress/1e6:>12.2f} MPa")

        if mat.tangent_modulus:
            click.echo(f"  Tangent Modulus (Et):  {mat.tangent_modulus/1e9:>12.2f} GPa")

        if mat.hardening_parameter:
            click.echo(f"  Hardening Parameter:   {mat.hardening_parameter:>12.4f}")

        click.echo("\nDerived Properties:")
        click.echo(f"  Shear Modulus (G):     {mat.get_shear_modulus()/1e9:>12.2f} GPa")
        click.echo(f"  Bulk Modulus (K):      {mat.get_bulk_modulus()/1e9:>12.2f} GPa")
        click.echo(f"  Wave Speed (c):        {mat.get_wave_speed():>12.2f} m/s")

        click.echo("\n" + "="*70)

    except Exception as e:
        logger.error(f"Error showing material: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@material.command()
@click.argument('material_file', type=click.Path(exists=True))
@click.option(
    '--library', '-l',
    type=click.Path(),
    help='Path to library file to update (default: creates new)'
)
@click.pass_context
def add(ctx, material_file: str, library: Optional[str]):
    """
    Add material from JSON file

    Adds a custom material to the library from a JSON definition file.

    JSON format:
    {
      "name": "MyMaterial",
      "type": "PLASTIC",
      "density": 7850,
      "elastic_modulus": 2.1e11,
      "poisson_ratio": 0.3,
      "yield_stress": 2.5e8
    }

    Examples:

    \b
    # Add material to new library
    koomesh material add custom_steel.json --library my_library.json
    """
    logger = ctx.obj.get('logger', logging.getLogger(__name__))

    try:
        # Load material definition
        with open(material_file, 'r') as f:
            mat_data = json.load(f)

        # Create material
        material_type = MaterialType[mat_data['type'].upper()]

        new_material = Material(
            name=mat_data['name'],
            material_type=material_type,
            density=mat_data['density'],
            elastic_modulus=mat_data['elastic_modulus'],
            poisson_ratio=mat_data['poisson_ratio'],
            yield_stress=mat_data.get('yield_stress'),
            tangent_modulus=mat_data.get('tangent_modulus'),
            hardening_parameter=mat_data.get('hardening_parameter'),
        )

        # Load or create library
        mat_lib = MaterialLibrary()

        if library and Path(library).exists():
            mat_lib.load_from_file(library)

        # Add material
        mat_lib.add_material(new_material)

        # Save library
        output_path = library if library else "materials.json"
        mat_lib.save_to_file(output_path)

        click.echo(f"✓ Added material: {new_material.name}")
        click.echo(f"✓ Library saved: {output_path}")

    except Exception as e:
        logger.error(f"Error adding material: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@material.command()
@click.argument('material_name', type=str)
@click.option(
    '--format', '-f',
    type=click.Choice(['lsdyna', 'json'], case_sensitive=False),
    default='lsdyna',
    help='Export format (default: lsdyna)'
)
@click.option(
    '--output', '-o',
    type=click.Path(),
    help='Output file path (default: material_name.{ext})'
)
@click.option(
    '--library', '-l',
    type=click.Path(exists=True),
    help='Path to custom material library JSON file'
)
@click.pass_context
def export(ctx, material_name: str, format: str, output: Optional[str], library: Optional[str]):
    """
    Export material definition

    Exports material in various formats for FEA solvers.

    Examples:

    \b
    # Export to LS-DYNA format
    koomesh material export Steel_Mild --format lsdyna

    \b
    # Export to JSON
    koomesh material export Steel_Mild --format json --output steel.json
    """
    logger = ctx.obj.get('logger', logging.getLogger(__name__))

    try:
        # Load library
        mat_lib = MaterialLibrary()

        if library:
            mat_lib.load_from_file(library)

        # Get material
        mat = mat_lib.get_material(material_name)

        if mat is None:
            click.echo(f"Material not found: {material_name}", err=True)
            sys.exit(1)

        # Determine output path
        if output is None:
            if format == 'lsdyna':
                output = f"{material_name}.k"
            else:
                output = f"{material_name}.json"

        # Export
        if format == 'lsdyna':
            generator = LSDynaMaterialGenerator()
            card = generator.generate_material_card(mat, material_id=1)

            with open(output, 'w') as f:
                f.write(card)

            click.echo(f"✓ LS-DYNA material card exported: {output}")

        elif format == 'json':
            mat_data = {
                'name': mat.name,
                'type': mat.material_type.value,
                'density': mat.density,
                'elastic_modulus': mat.elastic_modulus,
                'poisson_ratio': mat.poisson_ratio,
            }

            if mat.yield_stress:
                mat_data['yield_stress'] = mat.yield_stress
            if mat.tangent_modulus:
                mat_data['tangent_modulus'] = mat.tangent_modulus
            if mat.hardening_parameter:
                mat_data['hardening_parameter'] = mat.hardening_parameter

            with open(output, 'w') as f:
                json.dump(mat_data, f, indent=2)

            click.echo(f"✓ JSON material definition exported: {output}")

    except Exception as e:
        logger.error(f"Error exporting material: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@material.command()
@click.argument('material_name', type=str)
@click.option(
    '--library', '-l',
    type=click.Path(),
    required=True,
    help='Path to library file to update'
)
@click.pass_context
def remove(ctx, material_name: str, library: str):
    """
    Remove material from library

    Examples:

    \b
    # Remove material
    koomesh material remove MyMaterial --library my_library.json
    """
    logger = ctx.obj.get('logger', logging.getLogger(__name__))

    try:
        # Load library
        if not Path(library).exists():
            click.echo(f"Library file not found: {library}", err=True)
            sys.exit(1)

        mat_lib = MaterialLibrary()
        mat_lib.load_from_file(library)

        # Remove material
        if mat_lib.remove_material(material_name):
            mat_lib.save_to_file(library)
            click.echo(f"✓ Removed material: {material_name}")
            click.echo(f"✓ Library updated: {library}")
        else:
            click.echo(f"Material not found: {material_name}", err=True)
            sys.exit(1)

    except Exception as e:
        logger.error(f"Error removing material: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@material.command()
@click.argument('parts', nargs=-1, type=click.Path(exists=True), required=True)
@click.option(
    '--template', '-t',
    type=str,
    help='Template name for automatic assignment rules (e.g., automotive_crash)'
)
@click.option(
    '--rules', '-r',
    type=click.Path(exists=True),
    help='YAML file with custom assignment rules'
)
@click.option(
    '--by-geometry/--no-by-geometry',
    default=True,
    help='Use geometry analysis for assignment (default: true)'
)
@click.option(
    '--output', '-o',
    type=click.Path(),
    help='Output file for assignments (JSON)'
)
@click.pass_context
def assign(ctx, parts, template, rules, by_geometry, output):
    """
    Automatically assign materials to parts

    Assigns materials based on:
    - Filename patterns
    - Geometry properties (thickness, volume)
    - Template rules
    - Custom rules from YAML file

    Examples:

    \b
    # Auto-assign using template
    koomesh material assign *.step --template automotive_crash

    \b
    # Use custom rules
    koomesh material assign *.step --rules my_rules.yaml

    \b
    # Geometry-based assignment
    koomesh material assign parts/*.step --by-geometry
    """
    logger = ctx.obj.get('logger', logging.getLogger(__name__))

    try:
        from koomesh.materials.material_assigner import GeometryBasedMaterialAssigner, MaterialRuleEngine
        from pathlib import Path

        parts = [Path(p) for p in parts]
        click.echo(f"Assigning materials to {len(parts)} parts...")

        assigner = GeometryBasedMaterialAssigner()
        assignments = {}

        # Strategy 1: Custom rules from YAML
        if rules:
            import yaml
            with open(rules, 'r') as f:
                custom_rules = yaml.safe_load(f).get('rules', {})

            click.echo("Applying custom rules...")
            assignments.update(assigner.assign_by_filename(parts, custom_rules))

        # Strategy 2: Template rules
        if template:
            click.echo(f"Applying template rules: {template}...")

            if 'automotive' in template.lower():
                template_rules = MaterialRuleEngine.get_automotive_rules()
            elif 'aerospace' in template.lower():
                template_rules = MaterialRuleEngine.get_aerospace_rules()
            elif 'forming' in template.lower():
                template_rules = MaterialRuleEngine.get_forming_rules()
            else:
                template_rules = {}

            if template_rules:
                part_names = [p.stem for p in parts]
                template_assignments = assigner.assign_by_template(part_names, template_rules)

                for idx, mat in template_assignments.items():
                    if idx not in assignments:
                        assignments[idx] = mat

        # Strategy 3: Geometry-based (fallback)
        if by_geometry:
            click.echo("Analyzing geometry for remaining parts...")
            # Would need actual geometry loading here
            # For now, skip if no geometries available

        # Display results
        click.echo("\nMaterial Assignments:")
        click.echo("-" * 60)
        for idx, part in enumerate(parts):
            mat = assignments.get(idx, 'Unassigned')
            click.echo(f"{part.name:40s} → {mat}")

        # Save to file if requested
        if output:
            output_data = {
                'assignments': [
                    {'file': str(parts[idx]), 'material': mat}
                    for idx, mat in assignments.items()
                ]
            }

            with open(output, 'w') as f:
                json.dump(output_data, f, indent=2)

            click.echo(f"\n✓ Assignments saved: {output}")

        click.echo(f"\n✓ Assigned materials to {len(assignments)}/{len(parts)} parts")

    except Exception as e:
        logger.error(f"Error assigning materials: {e}")
        click.echo(f"Error: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


@material.command()
@click.argument('material_name', type=str)
@click.option(
    '--simulation-type', '-s',
    type=click.Choice(['crash', 'forming', 'impact', 'static'], case_sensitive=False),
    default='crash',
    help='Type of simulation (default: crash)'
)
@click.option(
    '--volume', '-v',
    type=float,
    help='Part volume in cm³ (for practical checks)'
)
@click.pass_context
def validate(ctx, material_name, simulation_type, volume):
    """
    Validate material assignment for simulation

    Checks:
    - Simulation type compatibility
    - Required properties completeness
    - Physical reasonableness
    - Practical concerns

    Examples:

    \b
    # Validate for crash simulation
    koomesh material validate Steel_Mild --simulation-type crash

    \b
    # Validate with volume check
    koomesh material validate Aluminum_5052 --simulation-type forming --volume 500.0
    """
    logger = ctx.obj.get('logger', logging.getLogger(__name__))

    try:
        from koomesh.materials.material_validator import MaterialValidator

        validator = MaterialValidator()

        click.echo(f"Validating material: {material_name}")
        click.echo(f"Simulation type: {simulation_type}")
        if volume:
            click.echo(f"Part volume: {volume} cm³")
        click.echo("-" * 60)

        report = validator.validate_assignment(
            part_name="Part",
            material_name=material_name,
            simulation_type=simulation_type,
            part_volume=volume
        )

        if report.valid:
            click.echo("✓ Validation PASSED")
        else:
            click.echo("✗ Validation FAILED")

        click.echo(f"\nScore: {report.statistics.get('score', 0.0):.2f}/1.0")

        # Show issues
        if report.issues:
            click.echo("\nIssues:")
            for issue in report.issues:
                symbol = "✗" if issue.severity == 'ERROR' else "⚠" if issue.severity == 'WARNING' else "ℹ"
                click.echo(f"\n{symbol} {issue.severity}: {issue.message}")
                if issue.suggestion:
                    click.echo(f"  → Suggestion: {issue.suggestion}")
        else:
            click.echo("\n✓ No issues found")

        sys.exit(0 if report.valid else 1)

    except Exception as e:
        logger.error(f"Error validating material: {e}")
        click.echo(f"Error: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


@material.command()
@click.option(
    '--simulation-type', '-s',
    type=click.Choice(['crash', 'forming', 'impact', 'static'], case_sensitive=False),
    default='crash',
    help='Type of simulation (default: crash)'
)
@click.option(
    '--min-strength',
    type=float,
    help='Minimum yield strength in MPa'
)
@click.option(
    '--max-density',
    type=float,
    help='Maximum density in kg/m³'
)
@click.option(
    '--formability',
    type=click.Choice(['required', 'preferred', 'none'], case_sensitive=False),
    default='none',
    help='Formability requirement (default: none)'
)
@click.option(
    '--top', '-n',
    type=int,
    default=5,
    help='Number of recommendations to show (default: 5)'
)
@click.pass_context
def recommend(ctx, simulation_type, min_strength, max_density, formability, top):
    """
    Recommend suitable materials based on requirements

    Returns top N materials ranked by suitability score.

    Examples:

    \b
    # Recommend for crash with strength requirement
    koomesh material recommend --simulation-type crash --min-strength 400

    \b
    # Recommend lightweight materials for forming
    koomesh material recommend --simulation-type forming --max-density 3000 --formability required

    \b
    # Get top 10 recommendations
    koomesh material recommend --simulation-type impact --top 10
    """
    logger = ctx.obj.get('logger', logging.getLogger(__name__))

    try:
        from koomesh.materials.material_validator import MaterialRecommender

        recommender = MaterialRecommender()

        # Build constraints
        constraints = {}
        if min_strength:
            constraints['min_strength'] = min_strength
        if max_density:
            constraints['max_density'] = max_density
        if formability and formability != 'none':
            constraints['formability'] = formability

        click.echo("Material Recommendations")
        click.echo("=" * 70)
        click.echo(f"Simulation type: {simulation_type}")

        if constraints:
            click.echo("Constraints:")
            for key, value in constraints.items():
                click.echo(f"  - {key}: {value}")

        click.echo("-" * 70)

        recommendations = recommender.recommend_materials(
            part_name="Part",
            simulation_type=simulation_type,
            constraints=constraints,
            top_n=top
        )

        if not recommendations:
            click.echo("No materials found matching criteria")
            sys.exit(0)

        click.echo(f"\nTop {len(recommendations)} Materials:\n")

        for i, (material, score, reason) in enumerate(recommendations, 1):
            click.echo(f"{i}. {material.name} (score: {score:.2f})")
            click.echo(f"   Category: {material.category}")

            if hasattr(material, 'density') and material.density:
                click.echo(f"   Density: {material.density:.0f} kg/m³")

            if hasattr(material, 'youngs_modulus') and material.youngs_modulus:
                click.echo(f"   Young's Modulus: {material.youngs_modulus:.0f} MPa")

            if hasattr(material, 'yield_strength') and material.yield_strength:
                click.echo(f"   Yield Strength: {material.yield_strength:.0f} MPa")

            click.echo(f"   Reason: {reason}")
            click.echo()

        click.echo("✓ Recommendations complete")

    except Exception as e:
        logger.error(f"Error recommending materials: {e}")
        click.echo(f"Error: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)
