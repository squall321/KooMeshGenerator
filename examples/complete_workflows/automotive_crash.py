"""
Automotive Crash Simulation Example
====================================

Complete workflow for multi-part automotive crash simulation using KooMeshGenerator.

This example demonstrates:
- Loading multiple STEP files (vehicle parts)
- Mesh generation with appropriate element types
- Contact detection between parts
- Material assignment
- Quality control
- LS-DYNA export for crash simulation

Author: KooMeshGenerator Team
"""

import sys
from pathlib import Path
import logging
import tempfile

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from koomesh.pipeline import (
    MeshGenerationPipeline,
    PipelineConfig
)
# from koomesh.templates.simulation_templates import SimulationTemplate  # Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def create_mock_vehicle_parts():
    """
    Create mock STEP files representing vehicle parts

    In real usage, you would have actual STEP files from CAD software.
    """
    parts = {}

    # Mock STEP file content
    step_template = """ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('{description}'),'2;1');
FILE_NAME('{filename}','','','','','','');
FILE_SCHEMA(('AUTOMOTIVE_DESIGN'));
ENDSEC;
DATA;
#1=CARTESIAN_POINT('',(0.,0.,0.));
#2=DIRECTION('',(0.,0.,1.));
#3=AXIS2_PLACEMENT_3D('',#1,#2,#3);
ENDSEC;
END-ISO-10303-21;
"""

    # Create temporary STEP files for each part
    part_names = [
        'front_bumper',
        'hood',
        'chassis',
        'door_left',
        'door_right'
    ]

    for part_name in part_names:
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.step',
            delete=False,
            prefix=f'{part_name}_'
        ) as f:
            content = step_template.format(
                description=f'Vehicle {part_name.replace("_", " ")}',
                filename=f'{part_name}.step'
            )
            f.write(content)
            parts[part_name] = f.name
            logger.info(f"Created mock STEP file for {part_name}: {f.name}")

    return parts


def automotive_crash_simulation():
    """
    Complete automotive crash simulation workflow
    """

    print("\n" + "="*70)
    print("AUTOMOTIVE CRASH SIMULATION - Complete Workflow")
    print("="*70)

    # Step 1: Prepare input files
    print("\n[Step 1] Preparing vehicle part files...")
    parts = create_mock_vehicle_parts()

    input_files = list(parts.values())
    print(f"  Vehicle parts: {len(input_files)}")
    for name, path in parts.items():
        print(f"    - {name}: {Path(path).name}")

    # Step 2: Configure pipeline for crash simulation
    print("\n[Step 2] Configuring crash simulation pipeline...")

    # Output file
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / 'automotive_crash.k'

    config = PipelineConfig(
        # Input/Output
        input_files=input_files,
        output_file=str(output_file),

        # Mesh parameters
        mesh_size=10.0,  # 10mm elements (appropriate for crash)
        element_type='tet4',  # Tetrahedral elements for complex geometry

        # Geometry processing
        clean_geometry=True,
        geometry_tolerance=0.5,  # 0.5mm tolerance for automotive parts
        remove_small_features=True,
        min_feature_size=2.0,  # Remove features < 2mm

        # Quality control
        enable_quality_check=True,
        min_quality_threshold=0.3,  # LS-DYNA minimum
        target_quality_threshold=0.6,  # Target for crash simulation
        enable_auto_remesh=True,  # Enable automatic remeshing
        max_remesh_iterations=2,

        # Contact detection
        enable_contact_detection=True,
        contact_tolerance=0.5,  # 0.5mm contact tolerance
        enable_self_contact=False,  # Not needed for separate parts

        # Validation
        enable_validation=True,

        # Output
        generate_report=True,
        verbose=True
    )

    print(f"  Output file: {output_file}")
    print(f"  Mesh size: {config.mesh_size} mm")
    print(f"  Element type: {config.element_type}")
    print(f"  Contact tolerance: {config.contact_tolerance} mm")

    # Step 3: Create and run pipeline
    print("\n[Step 3] Running mesh generation pipeline...")

    def progress_callback(stage_name, progress, message):
        """Progress callback for pipeline"""
        print(f"  [{stage_name}] {progress*100:5.1f}% - {message}")

    try:
        pipeline = MeshGenerationPipeline(config, progress_callback)
        result = pipeline.run()

        # Step 4: Check results
        print("\n[Step 4] Pipeline Results")
        print("="*70)

        if result.success:
            print("✓ Pipeline completed successfully!")
            print(f"\nMesh Statistics:")
            print(f"  Nodes:        {result.num_nodes:,}")
            print(f"  Elements:     {result.num_elements:,}")
            print(f"  Contacts:     {result.num_contacts}")
            print(f"\nQuality Metrics:")
            print(f"  Average:      {result.avg_quality:.3f}")
            print(f"  Minimum:      {result.min_quality:.3f}")
            print(f"  Maximum:      {result.max_quality:.3f}")
            print(f"\nExecution:")
            print(f"  Total time:   {result.execution_time:.2f} seconds")

            if result.stage_durations:
                print(f"\nStage Durations:")
                for stage, duration in result.stage_durations.items():
                    print(f"  {stage:15s}: {duration:.2f}s")

            print(f"\nOutput File:")
            print(f"  Location: {output_file}")
            print(f"  Size:     {output_file.stat().st_size:,} bytes")

            # Material recommendations
            print(f"\n[Step 5] Material Assignment Recommendations")
            print("="*70)
            print("For crash simulation, assign appropriate materials:")
            print("  • Front Bumper: *MAT_PLASTIC_KINEMATIC")
            print("  • Hood:         *MAT_PIECEWISE_LINEAR_PLASTICITY (Steel)")
            print("  • Chassis:      *MAT_PIECEWISE_LINEAR_PLASTICITY (High-strength steel)")
            print("  • Doors:        *MAT_PIECEWISE_LINEAR_PLASTICITY (Steel)")

            # Simulation setup recommendations
            print(f"\n[Step 6] LS-DYNA Simulation Setup")
            print("="*70)
            print("Recommended settings for crash simulation:")
            print("  • Time step:    Auto (with *CONTROL_TIMESTEP)")
            print("  • Duration:     0.100 seconds (100ms crash)")
            print("  • Contact:      Use *CONTACT_AUTOMATIC_SURFACE_TO_SURFACE")
            print("  • Hourglass:    Type 4 (recommended for crash)")
            print("  • Output:       D3PLOT every 1ms")

        else:
            print("✗ Pipeline failed!")
            print(f"Errors: {len(result.errors)}")
            for error in result.errors[:5]:
                print(f"  - {error}")

        # Cleanup
        print(f"\n[Cleanup] Removing temporary files...")
        for part_file in parts.values():
            Path(part_file).unlink(missing_ok=True)
        print("  Temporary files removed")

        return result

    except Exception as e:
        logger.error(f"Pipeline failed with exception: {e}")
        import traceback
        traceback.print_exc()

        # Cleanup on error
        for part_file in parts.values():
            Path(part_file).unlink(missing_ok=True)

        raise


def automotive_crash_with_template():
    """
    Alternative workflow using simulation template
    """

    print("\n" + "="*70)
    print("AUTOMOTIVE CRASH - Using Simulation Template")
    print("="*70)

    # Create vehicle parts
    parts = create_mock_vehicle_parts()
    input_files = list(parts.values())

    output_file = Path('output') / 'automotive_crash_template.k'

    # Use crash simulation template
    config = PipelineConfig(
        input_files=input_files,
        output_file=str(output_file),
        template_name='crash_simulation'  # Use predefined template
    )

    print(f"Using template: {config.template_name}")
    print(f"Output: {output_file}")

    try:
        pipeline = MeshGenerationPipeline(config)
        result = pipeline.run()

        if result.success:
            print(f"✓ Template-based simulation complete!")
            print(f"  Elements: {result.num_elements:,}")
            print(f"  Contacts: {result.num_contacts}")

        # Cleanup
        for part_file in parts.values():
            Path(part_file).unlink(missing_ok=True)

        return result

    except Exception as e:
        logger.error(f"Template-based pipeline failed: {e}")
        for part_file in parts.values():
            Path(part_file).unlink(missing_ok=True)
        raise


if __name__ == "__main__":
    print("\n" + "="*70)
    print("KooMeshGenerator - Automotive Crash Simulation Example")
    print("="*70)
    print("\nThis example demonstrates complete workflow for crash simulation.")
    print("In production, replace mock STEP files with actual CAD geometry.")

    # Run main workflow
    try:
        result = automotive_crash_simulation()

        if result.success:
            print("\n" + "="*70)
            print("✓ EXAMPLE COMPLETED SUCCESSFULLY")
            print("="*70)
            print(f"\nNext steps:")
            print(f"  1. Open output/automotive_crash.k in LS-PrePost")
            print(f"  2. Assign materials to parts")
            print(f"  3. Set up crash simulation parameters")
            print(f"  4. Run LS-DYNA solver")
            print(f"  5. Post-process results")

    except Exception as e:
        print("\n" + "="*70)
        print("✗ EXAMPLE FAILED")
        print("="*70)
        print(f"Error: {e}")
        sys.exit(1)
