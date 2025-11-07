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
