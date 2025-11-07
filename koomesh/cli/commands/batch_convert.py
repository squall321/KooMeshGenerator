"""
Batch Convert Command
=====================

Batch convert multiple STEP files to mesh format using glob patterns.

Usage:
    koomesh batch-convert "input/*.step" --output-dir meshes/
    koomesh batch-convert "cad/**/*.step" --mesh-size 2.0 --parallel --jobs 8

Author: KooMeshGenerator Team
"""

import click
import sys
import logging
from pathlib import Path
from typing import Optional

from koomesh.batch import BatchProcessor, BatchJob

logger = logging.getLogger(__name__)


@click.command(name='batch-convert')
@click.argument('pattern', type=str)
@click.option(
    '--output-dir', '-o',
    type=click.Path(),
    required=True,
    help='Output directory for mesh files'
)
@click.option(
    '--mesh-size', '-s',
    type=float,
    default=2.0,
    help='Target mesh element size (default: 2.0)'
)
@click.option(
    '--element-type', '-e',
    type=click.Choice(['auto', 'tet4', 'hex8'], case_sensitive=False),
    default='auto',
    help='Element type (default: auto)'
)
@click.option(
    '--format', '-f',
    type=click.Choice(['lsdyna', 'abaqus', 'nastran'], case_sensitive=False),
    default='lsdyna',
    help='Output format (default: lsdyna)'
)
@click.option(
    '--parallel/--no-parallel',
    default=False,
    help='Use parallel processing (default: false)'
)
@click.option(
    '--jobs', '-j',
    type=int,
    default=-1,
    help='Number of parallel jobs (default: -1 = all cores)'
)
@click.option(
    '--max-retries',
    type=int,
    default=3,
    help='Maximum retry attempts for failed jobs (default: 3)'
)
@click.option(
    '--save-results',
    type=click.Path(),
    help='Save batch results to CSV file'
)
@click.pass_context
def batch_convert(
    ctx,
    pattern: str,
    output_dir: str,
    mesh_size: float,
    element_type: str,
    format: str,
    parallel: bool,
    jobs: int,
    max_retries: int,
    save_results: Optional[str]
):
    """
    Batch convert STEP files to mesh format

    This command converts multiple STEP files to mesh format using glob patterns.
    Supports parallel processing, retry logic, and progress tracking.

    Examples:

    \b
    # Convert all STEP files in input/ directory
    koomesh batch-convert "input/*.step" --output-dir meshes/

    \b
    # Recursive search with custom mesh size
    koomesh batch-convert "cad/**/*.step" --output-dir output/ --mesh-size 1.5

    \b
    # Parallel processing with 8 workers
    koomesh batch-convert "input/*.step" \\
        --output-dir meshes/ \\
        --parallel \\
        --jobs 8

    \b
    # With retry logic and result logging
    koomesh batch-convert "input/*.step" \\
        --output-dir meshes/ \\
        --max-retries 5 \\
        --save-results results.csv
    """
    logger = ctx.obj.get('logger', logging.getLogger(__name__))

    try:
        # Create batch processor
        click.echo(f"Initializing batch processor...")
        processor = BatchProcessor(
            n_jobs=jobs if parallel else 1,
            max_retries=max_retries,
            verbose=True
        )

        # Determine output extension
        ext_map = {
            'lsdyna': '.k',
            'abaqus': '.inp',
            'nastran': '.bdf'
        }
        output_extension = ext_map.get(format, '.k')

        # Create jobs from glob pattern
        click.echo(f"\nScanning files: {pattern}")
        parameters = {
            'mesh_size': mesh_size,
            'element_type': element_type,
            'format': format
        }

        jobs = processor.create_jobs_from_glob(
            pattern,
            output_dir,
            output_extension=output_extension,
            parameters=parameters
        )

        if not jobs:
            click.echo("Error: No files found matching pattern", err=True)
            sys.exit(1)

        click.echo(f"✓ Found {len(jobs)} files")

        # Show job summary
        click.echo("\nJob Summary:")
        click.echo("-" * 70)
        click.echo(f"  Files to process: {len(jobs)}")
        click.echo(f"  Output directory: {output_dir}")
        click.echo(f"  Mesh size: {mesh_size}")
        click.echo(f"  Element type: {element_type}")
        click.echo(f"  Output format: {format}")
        click.echo(f"  Parallel: {'Yes' if parallel else 'No'}")
        if parallel:
            click.echo(f"  Workers: {jobs if jobs > 0 else 'all cores'}")
        click.echo(f"  Max retries: {max_retries}")
        click.echo("-" * 70)

        # Confirm execution
        if not click.confirm("\nProceed with batch conversion?"):
            click.echo("Cancelled")
            sys.exit(0)

        # Execute batch
        click.echo(f"\n{'='*70}")
        click.echo("EXECUTING BATCH CONVERSION")
        click.echo(f"{'='*70}\n")

        # Job function (placeholder - actual implementation needed)
        def process_job(job: BatchJob) -> bool:
            """Process single mesh conversion job"""
            try:
                # TODO: Implement actual mesh generation
                # For now, just simulate work
                click.echo(f"  ⚠ Mesh generation not yet fully integrated")
                click.echo(f"    Would convert: {job.input_file}")
                click.echo(f"    To: {job.output_file}")
                click.echo(f"    With mesh_size={job.parameters.get('mesh_size')}")

                # Simulate success
                return True

            except Exception as e:
                logger.error(f"Job {job.id} failed: {e}")
                return False

        result = processor.execute(jobs, process_job, parallel=parallel)

        # Print results
        click.echo(f"\n{'='*70}")
        result.print_summary()

        # Save results if requested
        if save_results:
            processor.save_results(result, save_results)
            click.echo(f"\n✓ Results saved to: {save_results}")

        # Exit with appropriate code
        if result.failed == 0:
            click.echo(f"\n✓ Batch conversion completed successfully")
            sys.exit(0)
        else:
            click.echo(f"\n⚠ Batch conversion completed with {result.failed} failures")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Error during batch conversion: {e}")
        click.echo(f"\nError: {e}", err=True)
        import traceback
        if ctx.obj.get('verbose'):
            traceback.print_exc()
        sys.exit(1)
