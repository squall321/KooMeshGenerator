"""
Geometry Commands
=================

Geometry preprocessing and analysis CLI commands.

Commands:
- geometry info: Show geometry information
- geometry clean: Clean and repair geometry
- geometry compare: Compare two geometries

Usage:
    koomesh geometry info input.step
    koomesh geometry clean input.step --output cleaned.step --heal-surfaces
    koomesh geometry compare file1.step file2.step

Author: KooMeshGenerator Team
"""

import click
import sys
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@click.group()
@click.pass_context
def geometry(ctx):
    """
    Geometry preprocessing and analysis

    Tools for analyzing and cleaning STEP file geometry before meshing.

    Examples:

    \b
    # Show geometry information
    koomesh geometry info part.step

    \b
    # Clean geometry
    koomesh geometry clean input.step --output cleaned.step

    \b
    # Compare two geometries
    koomesh geometry compare original.step modified.step
    """
    pass


@geometry.command()
@click.argument('step_file', type=click.Path(exists=True))
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Show detailed information'
)
@click.pass_context
def info(ctx, step_file: str, verbose: bool):
    """
    Show geometry information

    Analyzes STEP file and displays:
    - Volume and surface area
    - Number of faces, edges, vertices
    - Bounding box dimensions
    - Validity status

    Examples:

    \b
    # Basic info
    koomesh geometry info part.step

    \b
    # Detailed info
    koomesh geometry info part.step --verbose
    """
    logger = ctx.obj.get('logger', logging.getLogger(__name__))

    try:
        from koomesh.preprocessing import GeometryAnalyzer

        click.echo(f"Analyzing geometry: {step_file}")

        analyzer = GeometryAnalyzer()
        geometry_info = analyzer.analyze(step_file)

        # Print summary
        geometry_info.print_summary()

        # Exit with appropriate code
        if geometry_info.is_valid:
            sys.exit(0)
        else:
            click.echo("\n⚠ Geometry has validation errors", err=True)
            sys.exit(1)

    except ImportError as e:
        click.echo("Error: PythonOCC is required for geometry analysis", err=True)
        click.echo("Please install PythonOCC first.", err=True)
        sys.exit(1)

    except Exception as e:
        logger.error(f"Error analyzing geometry: {e}")
        click.echo(f"\nError: {e}", err=True)
        import traceback
        if ctx.obj.get('verbose') or verbose:
            traceback.print_exc()
        sys.exit(1)


@geometry.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option(
    '--output', '-o',
    type=click.Path(),
    required=True,
    help='Output STEP file path'
)
@click.option(
    '--remove-small-features',
    type=float,
    help='Remove features smaller than this size (mm)'
)
@click.option(
    '--heal-surfaces/--no-heal-surfaces',
    default=False,
    help='Perform surface healing (sewing)'
)
@click.option(
    '--fill-gaps',
    type=float,
    help='Fill gaps smaller than this size (mm)'
)
@click.option(
    '--fix-invalid/--no-fix-invalid',
    default=True,
    help='Attempt to fix invalid geometry (default: true)'
)
@click.pass_context
def clean(
    ctx,
    input_file: str,
    output: str,
    remove_small_features: Optional[float],
    heal_surfaces: bool,
    fill_gaps: Optional[float],
    fix_invalid: bool
):
    """
    Clean and repair geometry

    Performs various geometry cleaning operations:
    - Remove small features (fillets, holes)
    - Heal surfaces (sew faces together)
    - Fill gaps between surfaces
    - Fix invalid geometry

    Examples:

    \b
    # Basic cleaning with auto-fix
    koomesh geometry clean input.step --output cleaned.step

    \b
    # Remove small features
    koomesh geometry clean input.step \\
        --output cleaned.step \\
        --remove-small-features 0.5

    \b
    # Heal surfaces and fill gaps
    koomesh geometry clean input.step \\
        --output cleaned.step \\
        --heal-surfaces \\
        --fill-gaps 0.1

    \b
    # Full cleaning
    koomesh geometry clean input.step \\
        --output cleaned.step \\
        --remove-small-features 0.5 \\
        --heal-surfaces \\
        --fill-gaps 0.1 \\
        --fix-invalid
    """
    logger = ctx.obj.get('logger', logging.getLogger(__name__))

    try:
        from koomesh.preprocessing import GeometryCleaner

        click.echo(f"Cleaning geometry: {input_file}")
        click.echo(f"Output file: {output}")

        # Show operations
        click.echo("\nOperations:")
        if fix_invalid:
            click.echo("  ✓ Fix invalid geometry")
        if heal_surfaces:
            click.echo("  ✓ Heal surfaces")
        if fill_gaps:
            click.echo(f"  ✓ Fill gaps (< {fill_gaps} mm)")
        if remove_small_features:
            click.echo(f"  ✓ Remove small features (< {remove_small_features} mm)")

        # Clean geometry
        cleaner = GeometryCleaner()
        result = cleaner.clean(
            input_file=input_file,
            output_file=output,
            remove_small_features=remove_small_features,
            heal_surfaces=heal_surfaces,
            fill_gaps=fill_gaps,
            fix_invalid=fix_invalid
        )

        # Print results
        result.print_summary()

        # Exit with appropriate code
        if result.success:
            click.echo(f"\n✓ Geometry cleaned successfully")
            sys.exit(0)
        else:
            click.echo(f"\n✗ Geometry cleaning failed", err=True)
            sys.exit(1)

    except ImportError as e:
        click.echo("Error: PythonOCC is required for geometry cleaning", err=True)
        click.echo("Please install PythonOCC first.", err=True)
        sys.exit(1)

    except Exception as e:
        logger.error(f"Error cleaning geometry: {e}")
        click.echo(f"\nError: {e}", err=True)
        import traceback
        if ctx.obj.get('verbose'):
            traceback.print_exc()
        sys.exit(1)


@geometry.command()
@click.argument('file1', type=click.Path(exists=True))
@click.argument('file2', type=click.Path(exists=True))
@click.pass_context
def compare(ctx, file1: str, file2: str):
    """
    Compare two geometries

    Compares two STEP files and shows differences:
    - Volume difference
    - Surface area difference
    - Face count difference

    Examples:

    \b
    # Compare original and cleaned geometry
    koomesh geometry compare original.step cleaned.step

    \b
    # Compare before and after simplification
    koomesh geometry compare complex.step simple.step
    """
    logger = ctx.obj.get('logger', logging.getLogger(__name__))

    try:
        from koomesh.preprocessing import GeometryAnalyzer

        click.echo(f"Comparing geometries...")
        click.echo(f"  File 1: {file1}")
        click.echo(f"  File 2: {file2}")

        analyzer = GeometryAnalyzer()
        comparison = analyzer.compare_geometries(file1, file2)

        analyzer.print_comparison(comparison)

        sys.exit(0)

    except ImportError as e:
        click.echo("Error: PythonOCC is required for geometry comparison", err=True)
        click.echo("Please install PythonOCC first.", err=True)
        sys.exit(1)

    except Exception as e:
        logger.error(f"Error comparing geometries: {e}")
        click.echo(f"\nError: {e}", err=True)
        import traceback
        if ctx.obj.get('verbose'):
            traceback.print_exc()
        sys.exit(1)


@geometry.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option(
    '--output', '-o',
    type=click.Path(),
    required=True,
    help='Output STEP file path'
)
@click.option(
    '--tolerance',
    type=float,
    default=0.1,
    help='Simplification tolerance (default: 0.1)'
)
@click.option(
    '--remove-fillets/--keep-fillets',
    default=False,
    help='Remove fillet features'
)
@click.option(
    '--defeaturing/--no-defeaturing',
    default=False,
    help='Perform automatic defeaturing'
)
@click.pass_context
def simplify(
    ctx,
    input_file: str,
    output: str,
    tolerance: float,
    remove_fillets: bool,
    defeaturing: bool
):
    """
    Simplify geometry

    Simplifies geometry for faster meshing:
    - Reduce face count
    - Remove unnecessary details
    - Defeature small features

    Note: This is a placeholder command. Full implementation requires
    advanced CAD kernel operations.

    Examples:

    \b
    # Basic simplification
    koomesh geometry simplify complex.step --output simple.step

    \b
    # Aggressive simplification
    koomesh geometry simplify complex.step \\
        --output simple.step \\
        --tolerance 0.5 \\
        --remove-fillets \\
        --defeaturing
    """
    logger = ctx.obj.get('logger', logging.getLogger(__name__))

    click.echo(f"⚠ Geometry simplification is not yet fully implemented", err=True)
    click.echo(f"\nPlaceholder: Would simplify {input_file} to {output}")
    click.echo(f"  Tolerance: {tolerance}")
    click.echo(f"  Remove fillets: {remove_fillets}")
    click.echo(f"  Defeaturing: {defeaturing}")
    click.echo(f"\nThis feature requires advanced CAD kernel operations.")
    click.echo(f"Use 'geometry clean' for basic cleaning operations.")

    sys.exit(1)
