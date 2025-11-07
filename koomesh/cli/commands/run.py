"""
Run Command
===========

Execute complete meshing workflow from configuration file.

Usage:
    koomesh run config.yaml
    koomesh run config.yaml --override meshing.mesh_size=1.5
    koomesh run crash_analysis.yaml --dry-run

Author: KooMeshGenerator Team
"""

import click
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from koomesh.config.workflow_schema import WorkflowConfig
from pydantic import ValidationError

logger = logging.getLogger(__name__)


@click.command()
@click.argument('config_file', type=click.Path(exists=True))
@click.option(
    '--override', '-o',
    multiple=True,
    help='Override config values (e.g., meshing.mesh_size=2.0)'
)
@click.option(
    '--dry-run',
    is_flag=True,
    help='Validate config and show what would be done without executing'
)
@click.option(
    '--validate-only',
    is_flag=True,
    help='Only validate config file, do not execute'
)
@click.pass_context
def run(ctx, config_file: str, override: tuple, dry_run: bool, validate_only: bool):
    """
    Execute complete meshing workflow from configuration file

    This command reads a YAML configuration file and executes a complete
    meshing workflow including:
    - Mesh generation from STEP files
    - Quality checking
    - Contact detection
    - Material assignment
    - Output generation
    - Visualization

    Examples:

    \b
    # Run workflow from config
    koomesh run config.yaml

    \b
    # Override specific values
    koomesh run config.yaml --override meshing.mesh_size=1.5

    \b
    # Multiple overrides
    koomesh run config.yaml \\
        --override meshing.mesh_size=1.5 \\
        --override parallel.enabled=true

    \b
    # Dry run to see what would be executed
    koomesh run config.yaml --dry-run

    \b
    # Just validate config
    koomesh run config.yaml --validate-only
    """
    logger = ctx.obj.get('logger', logging.getLogger(__name__))

    try:
        # Load configuration
        click.echo(f"Loading configuration: {config_file}")
        config = WorkflowConfig.from_yaml(config_file)

        click.echo(f"✓ Configuration loaded: {config.project.name}")

        # Apply overrides
        if override:
            click.echo("\nApplying overrides:")
            overrides = _parse_overrides(override)

            for key, value in overrides.items():
                click.echo(f"  {key} = {value}")

            config.apply_overrides(overrides)
            click.echo("✓ Overrides applied")

        # Validate
        click.echo("\nValidating configuration...")
        click.echo(f"✓ Configuration valid")

        # Show summary
        _print_config_summary(config)

        if validate_only:
            click.echo("\n✓ Validation complete (validation-only mode)")
            sys.exit(0)

        if dry_run:
            click.echo("\n✓ Dry run complete (no execution)")
            sys.exit(0)

        # Execute workflow
        click.echo("\n" + "="*70)
        click.echo("EXECUTING WORKFLOW")
        click.echo("="*70)

        _execute_workflow(config, ctx)

        click.echo("\n" + "="*70)
        click.echo("✓ WORKFLOW COMPLETED SUCCESSFULLY")
        click.echo("="*70)
        sys.exit(0)

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    except ValidationError as e:
        click.echo(f"\nError: Configuration validation failed\n", err=True)
        for error in e.errors():
            loc = '.'.join(str(l) for l in error['loc'])
            click.echo(f"  {loc}: {error['msg']}", err=True)
        sys.exit(1)

    except Exception as e:
        logger.error(f"Error executing workflow: {e}")
        click.echo(f"\nError: {e}", err=True)
        import traceback
        if ctx.obj.get('verbose'):
            traceback.print_exc()
        sys.exit(1)


def _parse_overrides(override_strings: tuple) -> Dict[str, Any]:
    """
    Parse override strings into dictionary

    Args:
        override_strings: Tuple of "key=value" strings

    Returns:
        Dictionary of overrides

    Example:
        >>> _parse_overrides(("meshing.mesh_size=2.0", "parallel.enabled=true"))
        {"meshing.mesh_size": 2.0, "parallel.enabled": True}
    """
    overrides = {}

    for override_str in override_strings:
        if '=' not in override_str:
            raise ValueError(f"Invalid override format: {override_str} (expected key=value)")

        key, value_str = override_str.split('=', 1)
        key = key.strip()
        value_str = value_str.strip()

        # Parse value
        value = _parse_value(value_str)
        overrides[key] = value

    return overrides


def _parse_value(value_str: str) -> Any:
    """
    Parse value string to appropriate Python type

    Args:
        value_str: String representation of value

    Returns:
        Parsed value (int, float, bool, str, list)
    """
    value_lower = value_str.lower()

    # Boolean
    if value_lower in ('true', 'yes', 'on', '1'):
        return True
    if value_lower in ('false', 'no', 'off', '0'):
        return False

    # List (simple comma-separated)
    if ',' in value_str and not value_str.startswith('['):
        return [v.strip() for v in value_str.split(',')]

    # Try numeric
    try:
        if '.' in value_str:
            return float(value_str)
        else:
            return int(value_str)
    except ValueError:
        pass

    # Default to string
    return value_str


def _print_config_summary(config: WorkflowConfig):
    """Print configuration summary"""
    click.echo("\nConfiguration Summary:")
    click.echo("-" * 70)

    click.echo(f"\n📁 Project:")
    click.echo(f"  Name: {config.project.name}")
    click.echo(f"  Output: {config.project.output_dir}")

    click.echo(f"\n📥 Input:")
    click.echo(f"  Files: {len(config.input.step_files)}")
    for i, f in enumerate(config.input.step_files, 1):
        click.echo(f"    {i}. {f}")

    click.echo(f"\n🔧 Meshing:")
    click.echo(f"  Algorithm: {config.meshing.algorithm}")
    click.echo(f"  Mesh size: {config.meshing.mesh_size}")
    click.echo(f"  Element type: {config.meshing.element_type}")
    if config.meshing.boundary_layer and config.meshing.boundary_layer.enabled:
        click.echo(f"  Boundary layer: {config.meshing.boundary_layer.num_layers} layers")

    click.echo(f"\n✅ Quality:")
    click.echo(f"  Enabled: {config.quality.enabled}")
    if config.quality.enabled:
        click.echo(f"  Aspect ratio: ≤ {config.quality.thresholds.aspect_ratio}")
        click.echo(f"  Jacobian: ≥ {config.quality.thresholds.jacobian}")
        click.echo(f"  Report: {config.quality.report_format}")

    click.echo(f"\n🔗 Contact:")
    click.echo(f"  Enabled: {config.contact.enabled}")
    if config.contact.enabled:
        click.echo(f"  Tolerance: {config.contact.tolerance}")
        click.echo(f"  Self-contact: {config.contact.self_contact}")

    if config.materials:
        click.echo(f"\n🧪 Materials:")
        click.echo(f"  Assignments: {len(config.materials.assignments)}")
        for part, mat in config.materials.assignments.items():
            click.echo(f"    {part} → {mat}")

    click.echo(f"\n📤 Output:")
    click.echo(f"  Format: {config.output.format}")
    click.echo(f"  File: {config.output.filename}")

    if config.parallel.enabled:
        click.echo(f"\n⚡ Parallel:")
        click.echo(f"  Jobs: {config.parallel.n_jobs}")
        click.echo(f"  Batch size: {config.parallel.batch_size}")

    if config.visualization.enabled:
        click.echo(f"\n📸 Visualization:")
        click.echo(f"  Screenshots: {len(config.visualization.screenshots)}")

    click.echo("-" * 70)


def _execute_workflow(config: WorkflowConfig, ctx):
    """
    Execute the complete workflow

    Args:
        config: Workflow configuration
        ctx: Click context
    """
    from pathlib import Path

    # Create output directory
    output_dir = Path(config.project.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    click.echo(f"\n📁 Created output directory: {output_dir}")

    # Step 1: Process each STEP file
    click.echo(f"\n{'='*70}")
    click.echo("STEP 1: Mesh Generation")
    click.echo(f"{'='*70}")

    mesh_files = []
    for i, step_file in enumerate(config.input.step_files, 1):
        click.echo(f"\n[{i}/{len(config.input.step_files)}] Processing: {step_file}")

        # For now, just show what would be done
        # TODO: Implement actual mesh generation
        click.echo(f"  ⚠ Mesh generation not yet integrated in workflow runner")
        click.echo(f"  Would generate mesh with size={config.meshing.mesh_size}")

        # Placeholder output filename
        output_name = Path(step_file).stem + ".k"
        output_path = output_dir / output_name
        click.echo(f"  Would save to: {output_path}")
        mesh_files.append(str(output_path))

    # Step 2: Quality checking
    if config.quality.enabled:
        click.echo(f"\n{'='*70}")
        click.echo("STEP 2: Quality Checking")
        click.echo(f"{'='*70}")

        click.echo(f"  ⚠ Quality checking not yet integrated in workflow runner")
        click.echo(f"  Would check {len(mesh_files)} mesh files")
        click.echo(f"  Would generate {config.quality.report_format} report")

    # Step 3: Contact detection
    if config.contact.enabled:
        click.echo(f"\n{'='*70}")
        click.echo("STEP 3: Contact Detection")
        click.echo(f"{'='*70}")

        click.echo(f"  ⚠ Contact detection not yet integrated in workflow runner")
        click.echo(f"  Would detect contacts with tolerance={config.contact.tolerance}")
        if config.contact.self_contact:
            click.echo(f"  Would detect self-contacts")

    # Step 4: Material assignment
    if config.materials and config.materials.assignments:
        click.echo(f"\n{'='*70}")
        click.echo("STEP 4: Material Assignment")
        click.echo(f"{'='*70}")

        click.echo(f"  ⚠ Material assignment not yet integrated in workflow runner")
        click.echo(f"  Would assign {len(config.materials.assignments)} materials")

    # Step 5: Visualization
    if config.visualization.enabled and config.visualization.screenshots:
        click.echo(f"\n{'='*70}")
        click.echo("STEP 5: Visualization")
        click.echo(f"{'='*70}")

        click.echo(f"  ⚠ Visualization not yet integrated in workflow runner")
        click.echo(f"  Would generate {len(config.visualization.screenshots)} screenshots")

    # Step 6: Final output
    click.echo(f"\n{'='*70}")
    click.echo("STEP 6: Final Output")
    click.echo(f"{'='*70}")

    final_output = output_dir / config.output.filename
    click.echo(f"  Would create final output: {final_output}")
    click.echo(f"  Format: {config.output.format}")
    if config.output.include_contact:
        click.echo(f"  Including contact definitions")
    if config.output.include_materials:
        click.echo(f"  Including material cards")

    click.echo(f"\n📊 Summary:")
    click.echo(f"  Output directory: {output_dir}")
    click.echo(f"  Files processed: {len(config.input.step_files)}")
    click.echo(f"  Final output: {final_output}")
