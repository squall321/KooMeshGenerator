"""
Sheet Metal Forming Simulation Example
=======================================

Complete workflow for sheet metal forming simulation using KooMeshGenerator.

This example demonstrates:
- Sheet metal blank preparation
- Tool geometry (punch, die, binder)
- Tool-part contact definitions
- Adaptive remeshing for large deformations
- Quality control for forming
- LS-DYNA export for forming simulation

Typical use cases:
- Deep drawing
- Stamping operations
- Hydroforming
- Incremental forming

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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def create_forming_geometry():
    """
    Create mock STEP files for forming simulation

    Returns:
        dict: Paths to blank, punch, die, and binder STEP files
    """

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

    geometry = {}

    # Sheet metal blank (deformable)
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.step',
        delete=False,
        prefix='blank_'
    ) as f:
        content = step_template.format(
            description='Sheet metal blank (1.0mm thick)',
            filename='blank.step'
        )
        f.write(content)
        geometry['blank'] = f.name
        logger.info(f"Created blank STEP file: {f.name}")

    # Punch (rigid tool)
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.step',
        delete=False,
        prefix='punch_'
    ) as f:
        content = step_template.format(
            description='Forming punch (rigid)',
            filename='punch.step'
        )
        f.write(content)
        geometry['punch'] = f.name
        logger.info(f"Created punch STEP file: {f.name}")

    # Die (rigid tool)
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.step',
        delete=False,
        prefix='die_'
    ) as f:
        content = step_template.format(
            description='Forming die (rigid)',
            filename='die.step'
        )
        f.write(content)
        geometry['die'] = f.name
        logger.info(f"Created die STEP file: {f.name}")

    # Blank holder/binder (rigid tool)
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.step',
        delete=False,
        prefix='binder_'
    ) as f:
        content = step_template.format(
            description='Blank holder/binder (rigid)',
            filename='binder.step'
        )
        f.write(content)
        geometry['binder'] = f.name
        logger.info(f"Created binder STEP file: {f.name}")

    return geometry


def forming_simulation():
    """
    Complete forming simulation workflow
    """

    print("\n" + "="*70)
    print("SHEET METAL FORMING SIMULATION - Complete Workflow")
    print("="*70)

    # Step 1: Prepare forming tools
    print("\n[Step 1] Preparing forming geometry...")
    geometry = create_forming_geometry()

    print(f"  Components:")
    print(f"    - Blank:  {Path(geometry['blank']).name} (deformable)")
    print(f"    - Punch:  {Path(geometry['punch']).name} (rigid)")
    print(f"    - Die:    {Path(geometry['die']).name} (rigid)")
    print(f"    - Binder: {Path(geometry['binder']).name} (rigid)")

    # Step 2: Configure pipeline for forming
    print("\n[Step 2] Configuring forming simulation pipeline...")

    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / 'forming_simulation.k'

    config = PipelineConfig(
        # Input/Output
        input_files=list(geometry.values()),
        output_file=str(output_file),

        # Mesh parameters (shell elements for thin sheet)
        mesh_size=5.0,  # 5mm elements for sheet metal
        element_type='tet4',  # Use tet4 (convert to shells in LS-DYNA)

        # Geometry processing
        clean_geometry=True,
        geometry_tolerance=0.05,  # Tight tolerance for tools
        remove_small_features=True,
        min_feature_size=1.0,  # Remove very small features

        # Quality control (critical for forming)
        enable_quality_check=True,
        min_quality_threshold=0.4,  # Higher minimum for forming
        target_quality_threshold=0.7,  # Target high quality
        enable_auto_remesh=True,  # Important for adaptive meshing
        max_remesh_iterations=3,
        refinement_strategy='adaptive',  # Adaptive for strain localization

        # Contact detection (critical for forming)
        enable_contact_detection=True,
        contact_tolerance=0.1,  # Tight tolerance for forming
        enable_self_contact=True,  # Self-contact for blank
        self_contact_tolerance=0.05,

        # Validation
        enable_validation=True,

        # Output
        generate_report=True,
        verbose=True
    )

    print(f"  Output file: {output_file}")
    print(f"  Mesh size: {config.mesh_size} mm")
    print(f"  Element type: {config.element_type}")
    print(f"  Adaptive remeshing: {config.enable_auto_remesh}")
    print(f"  Contact tolerance: {config.contact_tolerance} mm")

    # Step 3: Run pipeline
    print("\n[Step 3] Running mesh generation pipeline...")

    def progress_callback(stage_name, progress, message):
        """Progress callback with visual bar"""
        bar_length = 40
        filled = int(bar_length * progress)
        bar = '▓' * filled + '░' * (bar_length - filled)
        percentage = progress * 100
        print(f"  {stage_name:12s} [{bar}] {percentage:5.1f}%")

    try:
        pipeline = MeshGenerationPipeline(config, progress_callback)
        result = pipeline.run()

        # Step 4: Analyze results
        print("\n[Step 4] Forming Simulation Results")
        print("="*70)

        if result.success:
            print("✓ Mesh generation successful!")

            print(f"\nMesh Statistics:")
            print(f"  Nodes:        {result.num_nodes:,}")
            print(f"  Elements:     {result.num_elements:,}")
            print(f"  Contacts:     {result.num_contacts}")

            print(f"\nQuality Metrics:")
            print(f"  Average:      {result.avg_quality:.3f}")
            print(f"  Minimum:      {result.min_quality:.3f}")
            print(f"  Maximum:      {result.max_quality:.3f}")

            # Quality assessment for forming
            if result.avg_quality >= 0.6:
                print(f"  ✓ Quality EXCELLENT for forming")
            elif result.avg_quality >= 0.5:
                print(f"  ✓ Quality GOOD for forming")
            else:
                print(f"  ⚠ Quality MARGINAL - consider refinement")

            print(f"\nExecution Time:")
            print(f"  Total: {result.execution_time:.2f} seconds")

            if result.stage_durations:
                print(f"\n  Stage breakdown:")
                for stage, duration in result.stage_durations.items():
                    pct = (duration / result.execution_time) * 100
                    print(f"    {stage:15s}: {duration:6.2f}s ({pct:5.1f}%)")

            # Step 5: Material setup
            print(f"\n[Step 5] Material Assignment for Forming")
            print("="*70)
            print("Recommended materials:")
            print("  • Blank (sheet metal):")
            print("      Material:  *MAT_PIECEWISE_LINEAR_PLASTICITY")
            print("      Thickness: 1.0 mm")
            print("      Steel properties:")
            print("        - Density:  7.85e-9 tonne/mm³")
            print("        - Young's:  210,000 MPa")
            print("        - Poisson:  0.3")
            print("        - Yield:    300 MPa (mild steel)")
            print("  • Tools (punch, die, binder):")
            print("      Material:  *MAT_RIGID")
            print("      Density:   7.85e-9 tonne/mm³")

            # Step 6: Simulation setup
            print(f"\n[Step 6] LS-DYNA Forming Simulation Setup")
            print("="*70)
            print("Forming process parameters:")
            print(f"  • Process type:    Deep drawing")
            print(f"  • Punch velocity:  5,000 mm/s (5 m/s)")
            print(f"  • Binder force:    50 kN")
            print(f"  • Stroke:          50 mm")
            print(f"  • Duration:        0.01 seconds (10 ms)")
            print(f"\nContact definitions:")
            print(f"  • Blank-Punch:     *CONTACT_FORMING_ONE_WAY_SURFACE_TO_SURFACE")
            print(f"  • Blank-Die:       *CONTACT_FORMING_ONE_WAY_SURFACE_TO_SURFACE")
            print(f"  • Blank-Binder:    *CONTACT_FORMING_ONE_WAY_SURFACE_TO_SURFACE")
            print(f"  • Blank-Blank:     *CONTACT_AUTOMATIC_SINGLE_SURFACE")
            print(f"  • Friction:        0.15 (typical for lubricated forming)")
            print(f"\nBoundary conditions:")
            print(f"  • Die:             Fixed (*BOUNDARY_SPC_SET)")
            print(f"  • Binder:          Z-motion only + force")
            print(f"  • Punch:           Prescribed motion (*BOUNDARY_PRESCRIBED_MOTION)")
            print(f"\nOutput settings:")
            print(f"  • D3PLOT:          Every 0.1ms (100 frames)")
            print(f"  • Adaptive mesh:   *CONTROL_ADAPTIVE (if needed)")
            print(f"  • Thinning:        Track with history variables")

            # Step 7: Post-processing
            print(f"\n[Step 7] Post-Processing Checklist")
            print("="*70)
            print("Key results to extract:")
            print("  1. Thickness distribution (thinning/thickening)")
            print("  2. Effective plastic strain")
            print("  3. Forming limit diagram (FLD)")
            print("  4. Springback prediction")
            print("  5. Wrinkling detection")
            print("  6. Tool forces (punch force, binder force)")
            print("  7. Blank draw-in")

            print(f"\nFailure modes to check:")
            print("  • Tearing:         Max thinning > 20%")
            print("  • Wrinkling:       Check compression zones")
            print("  • Springback:      Compare formed vs. final shape")

        else:
            print("✗ Pipeline failed!")
            print(f"Errors: {len(result.errors)}")
            for error in result.errors[:5]:
                print(f"  - {error}")

        # Cleanup
        print(f"\n[Cleanup] Removing temporary files...")
        for geom_file in geometry.values():
            Path(geom_file).unlink(missing_ok=True)
        print("  Temporary files removed")

        return result

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()

        # Cleanup on error
        for geom_file in geometry.values():
            Path(geom_file).unlink(missing_ok=True)

        raise


def forming_with_springback():
    """
    Forming simulation with springback analysis
    """

    print("\n" + "="*70)
    print("FORMING WITH SPRINGBACK ANALYSIS")
    print("="*70)

    geometry = create_forming_geometry()
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)

    # Phase 1: Forming
    print("\n[Phase 1] Forming stage...")
    output_forming = output_dir / 'forming_stage.k'

    config_forming = PipelineConfig(
        input_files=list(geometry.values()),
        output_file=str(output_forming),
        mesh_size=5.0,
        element_type='tet4',
        enable_contact_detection=True,
        enable_auto_remesh=True,
        verbose=False
    )

    try:
        pipeline = MeshGenerationPipeline(config_forming)
        result_forming = pipeline.run()

        if result_forming.success:
            print(f"  ✓ Forming mesh: {result_forming.num_elements:,} elements")

            # Phase 2: Springback (remove tools, apply gravity)
            print("\n[Phase 2] Springback stage...")
            print("  Note: Springback uses formed geometry as input")
            print("  Setup steps:")
            print("    1. Remove tool contacts")
            print("    2. Release blank from binder")
            print("    3. Apply gravity")
            print("    4. Run implicit solver")

            print(f"\n  Springback simulation file: springback_stage.k")
            print(f"  (Would be generated from formed state)")

        # Cleanup
        for geom_file in geometry.values():
            Path(geom_file).unlink(missing_ok=True)

        return result_forming

    except Exception as e:
        logger.error(f"Springback simulation failed: {e}")
        for geom_file in geometry.values():
            Path(geom_file).unlink(missing_ok=True)
        raise


if __name__ == "__main__":
    print("\n" + "="*70)
    print("KooMeshGenerator - Forming Simulation Example")
    print("="*70)
    print("\nThis example demonstrates sheet metal forming simulation setup.")
    print("Replace mock geometry with actual forming tools from CAD.")

    # Run main forming simulation
    try:
        result = forming_simulation()

        if result.success:
            print("\n" + "="*70)
            print("✓ EXAMPLE COMPLETED SUCCESSFULLY")
            print("="*70)
            print(f"\nNext steps:")
            print(f"  1. Open output/forming_simulation.k in LS-PrePost")
            print(f"  2. Verify tool geometries and contacts")
            print(f"  3. Assign material properties to blank")
            print(f"  4. Set up forming process parameters")
            print(f"  5. Run LS-DYNA explicit solver")
            print(f"  6. Post-process: thinning, FLD, springback")

            print(f"\nAdvanced:")
            print(f"  • Enable adaptive meshing for severe deformation")
            print(f"  • Add springback analysis (implicit solver)")
            print(f"  • Optimize binder force to prevent wrinkling")

    except Exception as e:
        print("\n" + "="*70)
        print("✗ EXAMPLE FAILED")
        print("="*70)
        print(f"Error: {e}")
        sys.exit(1)
