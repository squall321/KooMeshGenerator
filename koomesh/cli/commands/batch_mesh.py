"""
Batch Mesh Command
==================

Batch mesh generation from CSV/Excel parameter file.
Each row defines a separate meshing job with custom parameters.

Usage:
    koomesh batch-mesh parts_list.csv
    koomesh batch-mesh parts.xlsx --sheet "Sheet1" --parallel

Author: KooMeshGenerator Team
"""

import click
import sys
import logging
from pathlib import Path
from typing import Optional

from koomesh.batch import BatchProcessor, BatchJob

logger = logging.getLogger(__name__)


@click.command(name='batch-mesh')
@click.argument('parameter_file', type=click.Path(exists=True))
@click.option(
    '--sheet',
    type=str,
    default='0',
    help='Excel sheet name or index (default: 0 = first sheet)'
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
@click.option(
    '--dry-run',
    is_flag=True,
    help='Show jobs without executing'
)
@click.pass_context
def batch_mesh(
    ctx,
    parameter_file: str,
    sheet: str,
    parallel: bool,
    jobs: int,
    max_retries: int,
    save_results: Optional[str],
    dry_run: bool
):
    """
    Batch mesh generation from parameter file

    This command reads a CSV or Excel file containing job parameters
    and executes mesh generation for each row. Each job can have
    different parameters (mesh_size, element_type, material, etc.).

    CSV/Excel Format:
        Required columns: input_file, output_file
        Optional columns: mesh_size, element_type, material, ...

    Examples:

    \b
    # Process from CSV file
    koomesh batch-mesh parts_list.csv

    \b
    # Process from Excel file with specific sheet
    koomesh batch-mesh parts.xlsx --sheet "Parts"

    \b
    # Parallel processing with retry
    koomesh batch-mesh parts.csv \\
        --parallel \\
        --jobs 8 \\
        --max-retries 5

    \b
    # Dry run to preview jobs
    koomesh batch-mesh parts.csv --dry-run

    \b
    # With result logging
    koomesh batch-mesh parts.csv --save-results results.csv
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

        # Load jobs from file
        file_path = Path(parameter_file)
        click.echo(f"\nLoading jobs from: {parameter_file}")

        if file_path.suffix.lower() in ['.xlsx', '.xls']:
            # Excel file
            try:
                sheet_idx = int(sheet)
            except ValueError:
                sheet_idx = sheet

            jobs_list = processor.create_jobs_from_excel(
                parameter_file,
                sheet_name=sheet_idx
            )
        elif file_path.suffix.lower() == '.csv':
            # CSV file
            jobs_list = processor.create_jobs_from_csv(parameter_file)
        else:
            click.echo(
                f"Error: Unsupported file format: {file_path.suffix}",
                err=True
            )
            click.echo("Supported formats: .csv, .xlsx, .xls", err=True)
            sys.exit(1)

        if not jobs_list:
            click.echo("Error: No jobs found in parameter file", err=True)
            sys.exit(1)

        click.echo(f"✓ Loaded {len(jobs_list)} jobs")

        # Show job summary
        click.echo("\nJob Summary:")
        click.echo("-" * 70)
        click.echo(f"  Total jobs: {len(jobs_list)}")
        click.echo(f"  Parallel: {'Yes' if parallel else 'No'}")
        if parallel:
            click.echo(f"  Workers: {jobs if jobs > 0 else 'all cores'}")
        click.echo(f"  Max retries: {max_retries}")
        click.echo("-" * 70)

        # Show first few jobs as preview
        click.echo("\nJob Preview (first 5):")
        for i, job in enumerate(jobs_list[:5], 1):
            click.echo(f"\n  Job {i}: {job.id}")
            click.echo(f"    Input:  {job.input_file}")
            click.echo(f"    Output: {job.output_file}")
            if job.parameters:
                click.echo(f"    Parameters:")
                for k, v in job.parameters.items():
                    click.echo(f"      - {k}: {v}")

        if len(jobs_list) > 5:
            click.echo(f"\n  ... and {len(jobs_list) - 5} more jobs")

        # Dry run mode
        if dry_run:
            click.echo("\n✓ Dry run complete (no execution)")
            sys.exit(0)

        # Confirm execution
        if not click.confirm("\nProceed with batch meshing?"):
            click.echo("Cancelled")
            sys.exit(0)

        # Execute batch
        click.echo(f"\n{'='*70}")
        click.echo("EXECUTING BATCH MESHING")
        click.echo(f"{'='*70}\n")

        # Job function (placeholder - actual implementation needed)
        def process_job(job: BatchJob) -> bool:
            """Process single meshing job"""
            try:
                # TODO: Implement actual mesh generation
                # For now, just simulate work
                click.echo(f"\n  Processing: {job.id}")
                click.echo(f"    Input: {job.input_file}")
                click.echo(f"    Output: {job.output_file}")

                if job.parameters:
                    click.echo(f"    Parameters:")
                    for k, v in job.parameters.items():
                        click.echo(f"      - {k}: {v}")

                click.echo(f"    ⚠ Mesh generation not yet fully integrated")

                # Simulate success
                return True

            except Exception as e:
                logger.error(f"Job {job.id} failed: {e}")
                return False

        result = processor.execute(jobs_list, process_job, parallel=parallel)

        # Print results
        click.echo(f"\n{'='*70}")
        result.print_summary()

        # Save results if requested
        if save_results:
            processor.save_results(result, save_results)
            click.echo(f"\n✓ Results saved to: {save_results}")

        # Exit with appropriate code
        if result.failed == 0:
            click.echo(f"\n✓ Batch meshing completed successfully")
            sys.exit(0)
        else:
            click.echo(f"\n⚠ Batch meshing completed with {result.failed} failures")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Error during batch meshing: {e}")
        click.echo(f"\nError: {e}", err=True)
        import traceback
        if ctx.obj.get('verbose'):
            traceback.print_exc()
        sys.exit(1)
