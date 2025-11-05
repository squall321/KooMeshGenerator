"""
Command Line Interface for KooMeshGenerator
============================================

This module provides the CLI entry point for KooMeshGenerator.

Commands:
- generate: Generate mesh from STEP file
- batch: Batch process multiple STEP files
- analyze: Analyze STEP file structure
- validate: Validate LS-DYNA output
- info: Show system and dependency information
- version: Show version information

Usage:
    koomesh generate input.step --mesh-size 1.0 -o output.k
    koomesh batch input_dir/ output_dir/ --mesh-size 1.0 -w 4
    koomesh analyze assembly.step
    koomesh info
    koomesh --version
"""

import click
import sys
from pathlib import Path
import logging

# Import koomesh modules
try:
    import koomesh
    from koomesh.config import KooMeshConfig
    from koomesh.utils.logger import setup_logger
    from koomesh.io.step_reader import STEPReader, check_pythonocc_available
except ImportError as e:
    print(f"Error importing koomesh modules: {e}")
    print("Please ensure KooMeshGenerator is properly installed.")
    sys.exit(1)


@click.group()
@click.version_option(version=koomesh.__version__)
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--quiet', '-q', is_flag=True, help='Suppress output except errors')
@click.pass_context
def cli(ctx, verbose, quiet):
    """
    KooMeshGenerator - Automated mesh generation from STEP files

    A comprehensive tool for automatic mesh generation with intelligent
    geometry analysis and LS-DYNA output.
    """
    # Store context
    ctx.ensure_object(dict)

    # Setup logging
    if quiet:
        log_level = 'ERROR'
    elif verbose:
        log_level = 'DEBUG'
    else:
        log_level = 'INFO'

    logger = setup_logger('koomesh', level=log_level)
    ctx.obj['logger'] = logger
    ctx.obj['config'] = KooMeshConfig()
    ctx.obj['verbose'] = verbose


@cli.command()
@click.argument('step_file', type=click.Path(exists=True))
@click.option('--mesh-size', '-s', type=float, required=True,
              help='Target mesh element size')
@click.option('--output', '-o', type=click.Path(),
              help='Output file path (default: input.k)')
@click.option('--hex-priority/--no-hex-priority', default=True,
              help='Prioritize hexahedral mesh (default: enabled)')
@click.option('--validate-quality/--no-validate-quality', default=True,
              help='Validate mesh quality (default: enabled)')
@click.pass_context
def generate(ctx, step_file, mesh_size, output, hex_priority, validate_quality):
    """
    Generate mesh from STEP file

    This command reads a STEP file, analyzes the geometry, and generates
    a mesh with automatic selection of element types.

    Example:
        koomesh generate model.step --mesh-size 1.0 -o output.k
    """
    logger = ctx.obj['logger']

    # Check if PythonOCC is available
    if not check_pythonocc_available():
        click.echo("Error: PythonOCC is not installed.", err=True)
        click.echo("Please build and install PythonOCC first.")
        click.echo("See build/README.md for instructions.")
        sys.exit(1)

    # Check if GMSH is available
    try:
        import gmsh
    except ImportError:
        click.echo("Error: GMSH is not installed.", err=True)
        click.echo("Please build and install GMSH first.")
        click.echo("See build/README.md for instructions.")
        sys.exit(1)

    # Determine output file
    if output is None:
        step_path = Path(step_file)
        output = step_path.with_suffix('.k')

    logger.info(f"Generating mesh from: {step_file}")
    logger.info(f"Mesh size: {mesh_size}")
    logger.info(f"Output file: {output}")

    try:
        # Create pipeline
        from koomesh.core.pipeline import MeshPipeline, PipelineProgress

        # Progress callback
        def show_progress(progress: PipelineProgress):
            click.echo(f"[{progress.progress:3.0f}%] {progress.message}")

        pipeline = MeshPipeline(
            config=ctx.obj['config'],
            progress_callback=show_progress if ctx.obj.get('verbose', False) else None
        )

        # Run pipeline
        result = pipeline.run(
            step_file=step_file,
            output_file=output,
            mesh_size=mesh_size,
            hex_priority=hex_priority,
            validate_quality=validate_quality
        )

        # Display result
        if result.success:
            click.echo("\n✓ Mesh generation completed successfully!")
            result.print_summary()
            sys.exit(0)
        else:
            click.echo("\n✗ Mesh generation failed!", err=True)
            result.print_summary()
            sys.exit(1)

    except Exception as e:
        logger.error(f"Error during mesh generation: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('step_file', type=click.Path(exists=True))
@click.option('--hierarchy/--no-hierarchy', default=True,
              help='Show hierarchy structure')
@click.option('--classify/--no-classify', default=True,
              help='Classify shapes')
@click.pass_context
def analyze(ctx, step_file, hierarchy, classify):
    """
    Analyze STEP file structure

    This command analyzes a STEP file and displays information about
    its geometry, hierarchy, and recommended meshing strategy.

    Example:
        koomesh analyze assembly.step
    """
    logger = ctx.obj['logger']

    if not check_pythonocc_available():
        click.echo("Error: PythonOCC is not installed.", err=True)
        sys.exit(1)

    logger.info(f"Analyzing STEP file: {step_file}")

    try:
        # Read STEP file
        reader = STEPReader()
        reader.print_file_info(step_file)

        # Show hierarchy if requested
        if hierarchy:
            click.echo("\n" + "="*60)
            click.echo("Hierarchy Structure:")
            click.echo("="*60)

            from koomesh.io.hierarchy_parser import HierarchyParser
            parser = HierarchyParser()

            try:
                root = parser.parse_from_step(step_file)
                parser.print_hierarchy()
            except Exception as e:
                logger.warning(f"Could not parse hierarchy: {e}")
                click.echo("(Hierarchy parsing failed - file may not contain assembly structure)")

        # Classify shapes if requested
        if classify:
            click.echo("\n" + "="*60)
            click.echo("Shape Classification:")
            click.echo("="*60)

            from koomesh.geometry.shape_classifier import ShapeClassifier
            classifier = ShapeClassifier()

            shape = reader.read_file(step_file)
            result = classifier.classify(shape)

            click.echo(f"Shape Type: {result.shape_type.value}")
            click.echo(f"Recommended Mesh Type: {result.mesh_type.value}")
            click.echo(f"Confidence: {result.confidence:.2%}")
            click.echo(f"Complexity: {classifier.get_complexity_score(shape):.2%}")

            if result.reasons:
                click.echo("\nReasons:")
                for reason in result.reasons:
                    click.echo(f"  • {reason}")

    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('input_dir', type=click.Path(exists=True))
@click.argument('output_dir', type=click.Path())
@click.option('--mesh-size', '-s', type=float, required=True,
              help='Target mesh element size')
@click.option('--hex-priority/--no-hex-priority', default=True,
              help='Prioritize hexahedral mesh (default: enabled)')
@click.option('--recursive/--no-recursive', default=False,
              help='Search subdirectories recursively')
@click.option('--workers', '-w', type=int, default=None,
              help='Number of parallel workers (default: CPU count - 1)')
@click.option('--sequential', is_flag=True,
              help='Process files sequentially (no parallelization)')
@click.pass_context
def batch(ctx, input_dir, output_dir, mesh_size, hex_priority, recursive, workers, sequential):
    """
    Batch process multiple STEP files

    This command processes all STEP files in a directory and generates
    meshes for each one in parallel.

    Example:
        koomesh batch input_dir/ output_dir/ --mesh-size 1.0 -w 4
    """
    logger = ctx.obj['logger']

    # Check dependencies
    if not check_pythonocc_available():
        click.echo("Error: PythonOCC is not installed.", err=True)
        sys.exit(1)

    try:
        import gmsh
    except ImportError:
        click.echo("Error: GMSH is not installed.", err=True)
        sys.exit(1)

    logger.info(f"Batch processing directory: {input_dir}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Mesh size: {mesh_size}")

    try:
        from koomesh.core.batch_processor import BatchProcessor

        # Create batch processor
        processor = BatchProcessor(
            config=ctx.obj['config'],
            num_workers=workers,
            use_multiprocessing=False
        )

        # Process directory
        result = processor.process_directory(
            input_dir=input_dir,
            output_dir=output_dir,
            mesh_size=mesh_size,
            hex_priority=hex_priority,
            recursive=recursive,
            parallel=not sequential
        )

        # Display result
        result.print_summary()

        if result.completed > 0:
            click.echo(f"\n✓ Batch processing completed: {result.completed}/{result.total_jobs} succeeded")
            sys.exit(0)
        else:
            click.echo(f"\n✗ All batch jobs failed!", err=True)
            sys.exit(1)

    except Exception as e:
        logger.error(f"Error during batch processing: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('keyword_file', type=click.Path(exists=True))
@click.pass_context
def validate(ctx, keyword_file):
    """
    Validate LS-DYNA keyword file

    This command checks an LS-DYNA keyword file for common errors
    and formatting issues.

    Example:
        koomesh validate output.k
    """
    logger = ctx.obj['logger']

    click.echo("LS-DYNA validation not yet implemented.")
    click.echo("This will be available in Phase 5 of development.")


@cli.command()
@click.pass_context
def info(ctx):
    """
    Show system and dependency information

    Displays information about installed dependencies and system configuration.
    """
    click.echo("KooMeshGenerator System Information")
    click.echo("=" * 60)
    click.echo(f"Version: {koomesh.__version__}")
    click.echo(f"Python: {sys.version}")

    # Check PythonOCC
    if check_pythonocc_available():
        try:
            from OCC import VERSION as OCC_VERSION
            click.echo(f"PythonOCC: {OCC_VERSION} ✓")
        except:
            click.echo("PythonOCC: Available ✓")
    else:
        click.echo("PythonOCC: Not installed ✗")

    # Check GMSH
    try:
        import gmsh
        gmsh.initialize()
        version_info = gmsh.option.getString("General.Version")
        gmsh.finalize()
        click.echo(f"GMSH: {version_info} ✓")
    except ImportError:
        click.echo("GMSH: Not installed ✗")

    # Check other dependencies
    try:
        import numpy
        click.echo(f"NumPy: {numpy.__version__} ✓")
    except ImportError:
        click.echo("NumPy: Not installed ✗")

    try:
        import scipy
        click.echo(f"SciPy: {scipy.__version__} ✓")
    except ImportError:
        click.echo("SciPy: Not installed ✗")

    # Configuration
    config = ctx.obj['config']
    click.echo("\nConfiguration:")
    click.echo(f"  Default Mesh Size: {config.mesh.default_size}")
    click.echo(f"  Hex Priority: {config.mesh.hex_priority}")
    click.echo(f"  Contact Detection: {config.contact.enabled}")


@cli.command()
def version():
    """Show version information"""
    click.echo(f"KooMeshGenerator version {koomesh.__version__}")
    click.echo(f"License: {koomesh.__license__}")
    click.echo(f"Author: {koomesh.__author__}")


if __name__ == '__main__':
    cli(obj={})
