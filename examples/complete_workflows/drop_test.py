"""
Drop Test Simulation Example
=============================

Complete workflow for object drop test simulation using KooMeshGenerator.

This example demonstrates:
- Loading object and floor geometry
- Self-contact detection for deformable objects
- Impact surface preparation
- Quality optimization for impact simulation
- LS-DYNA export for drop test

Typical use cases:
- Product drop testing (phones, packages)
- Safety equipment testing (helmets, protective gear)
- Impact resistance validation

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


def create_drop_test_geometry():
    """
    Create mock STEP files for drop test

    Returns:
        dict: Paths to object and floor STEP files
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

    # Create object to drop (e.g., smartphone)
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.step',
        delete=False,
        prefix='drop_object_'
    ) as f:
        content = step_template.format(
            description='Drop test object (smartphone)',
            filename='smartphone.step'
        )
        f.write(content)
        geometry['object'] = f.name
        logger.info(f"Created object STEP file: {f.name}")

    # Create floor/ground surface
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.step',
        delete=False,
        prefix='floor_'
    ) as f:
        content = step_template.format(
            description='Floor surface (rigid)',
            filename='floor.step'
        )
        f.write(content)
        geometry['floor'] = f.name
        logger.info(f"Created floor STEP file: {f.name}")

    return geometry


def drop_test_simulation():
    """
    Complete drop test simulation workflow
    """

    print("\n" + "="*70)
    print("DROP TEST SIMULATION - Complete Workflow")
    print("="*70)

    # Step 1: Prepare geometry
    print("\n[Step 1] Preparing drop test geometry...")
    geometry = create_drop_test_geometry()

    print(f"  Object: {Path(geometry['object']).name}")
    print(f"  Floor:  {Path(geometry['floor']).name}")

    # Step 2: Configure pipeline for drop test
    print("\n[Step 2] Configuring drop test pipeline...")

    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / 'drop_test.k'

    config = PipelineConfig(
        # Input/Output
        input_files=[geometry['object'], geometry['floor']],
        output_file=str(output_file),

        # Mesh parameters
        mesh_size=2.0,  # 2mm elements for detailed impact analysis
        element_type='tet4',  # Tetrahedral for complex deformation

        # Geometry processing
        clean_geometry=True,
        geometry_tolerance=0.1,  # Tight tolerance for impact surfaces
        remove_small_features=True,
        min_feature_size=0.5,  # Keep small features (buttons, ports)

        # Quality control (critical for impact)
        enable_quality_check=True,
        min_quality_threshold=0.4,  # Higher minimum for impact
        target_quality_threshold=0.7,  # Target high quality
        enable_auto_remesh=True,
        max_remesh_iterations=3,  # More iterations for quality

        # Contact detection
        enable_contact_detection=True,
        contact_tolerance=0.2,  # Tight contact tolerance for impact
        enable_self_contact=True,  # Enable for deformable object
        self_contact_tolerance=0.1,  # Very tight for self-contact

        # Validation
        enable_validation=True,

        # Output
        generate_report=True,
        verbose=True
    )

    print(f"  Output file: {output_file}")
    print(f"  Mesh size: {config.mesh_size} mm (fine for impact)")
    print(f"  Element type: {config.element_type}")
    print(f"  Self-contact: {config.enable_self_contact}")
    print(f"  Contact tolerance: {config.contact_tolerance} mm")

    # Step 3: Run pipeline
    print("\n[Step 3] Running mesh generation pipeline...")

    def progress_callback(stage_name, progress, message):
        """Progress callback"""
        bar_length = 30
        filled = int(bar_length * progress)
        bar = '█' * filled + '░' * (bar_length - filled)
        print(f"  [{stage_name:12s}] [{bar}] {progress*100:5.1f}% - {message}")

    try:
        pipeline = MeshGenerationPipeline(config, progress_callback)
        result = pipeline.run()

        # Step 4: Analyze results
        print("\n[Step 4] Drop Test Results")
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

            # Quality assessment
            if result.min_quality >= 0.4:
                print(f"  ✓ Quality GOOD (min >= 0.4)")
            elif result.min_quality >= 0.3:
                print(f"  ⚠ Quality ACCEPTABLE (min >= 0.3)")
            else:
                print(f"  ✗ Quality POOR (min < 0.3) - consider remeshing")

            print(f"\nExecution Time:")
            print(f"  Total: {result.execution_time:.2f} seconds")

            # Step 5: Material and simulation setup
            print(f"\n[Step 5] Material Assignment for Drop Test")
            print("="*70)
            print("Recommended materials:")
            print("  • Object (smartphone):")
            print("      - Glass:      *MAT_BRITTLE_DAMAGE")
            print("      - Plastic:    *MAT_PLASTIC_KINEMATIC")
            print("      - Aluminum:   *MAT_PIECEWISE_LINEAR_PLASTICITY")
            print("  • Floor:")
            print("      - Rigid:      *MAT_RIGID")

            print(f"\n[Step 6] LS-DYNA Simulation Setup")
            print("="*70)
            print("Drop test simulation parameters:")
            print(f"  • Drop height:     1.0 m (typical)")
            print(f"  • Initial velocity: 0 m/s")
            print(f"  • Gravity:         9.81 m/s²")
            print(f"  • Duration:        0.05 seconds")
            print(f"  • Time step:       Auto (CFL condition)")
            print(f"\nContact setup:")
            print(f"  • Object-Floor:    *CONTACT_AUTOMATIC_SURFACE_TO_SURFACE")
            print(f"  • Self-Contact:    *CONTACT_AUTOMATIC_SINGLE_SURFACE")
            print(f"  • Friction:        0.3 (typical for plastic on concrete)")
            print(f"\nOutput settings:")
            print(f"  • D3PLOT:          Every 0.5ms (100 frames)")
            print(f"  • GLSTAT:          Global statistics")
            print(f"  • MATSUM:          Material energies")

            # Post-processing recommendations
            print(f"\n[Step 7] Post-Processing Analysis")
            print("="*70)
            print("Key metrics to extract:")
            print("  1. Peak impact force (from RCFORC)")
            print("  2. Maximum stress (from MATSUM)")
            print("  3. Plastic strain distribution")
            print("  4. Energy absorption")
            print("  5. Rebound height/velocity")

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


def parametric_drop_test():
    """
    Parametric drop test with varying heights
    """

    print("\n" + "="*70)
    print("PARAMETRIC DROP TEST - Multiple Heights")
    print("="*70)

    geometry = create_drop_test_geometry()
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)

    drop_heights = [0.5, 1.0, 1.5, 2.0]  # meters
    results = {}

    print(f"\nRunning {len(drop_heights)} drop simulations...")

    for height in drop_heights:
        print(f"\n  Drop height: {height} m")

        output_file = output_dir / f'drop_test_{height}m.k'

        config = PipelineConfig(
            input_files=[geometry['object'], geometry['floor']],
            output_file=str(output_file),
            mesh_size=2.0,
            element_type='tet4',
            enable_contact_detection=True,
            contact_tolerance=0.2,
            verbose=False  # Quiet mode for batch
        )

        try:
            pipeline = MeshGenerationPipeline(config)
            result = pipeline.run()

            if result.success:
                results[height] = result
                print(f"    ✓ Complete: {result.num_elements:,} elements")
            else:
                print(f"    ✗ Failed")

        except Exception as e:
            logger.error(f"    ✗ Error: {e}")

    # Summary
    print(f"\n" + "="*70)
    print(f"Parametric Study Complete")
    print("="*70)
    print(f"Successful runs: {len(results)}/{len(drop_heights)}")

    if results:
        print(f"\nResults:")
        print(f"  Height   Elements   Contacts   Quality")
        print(f"  ------   --------   --------   -------")
        for height, result in results.items():
            print(f"  {height:4.1f}m   {result.num_elements:8,}   "
                  f"{result.num_contacts:8}   {result.avg_quality:7.3f}")

    # Cleanup
    for geom_file in geometry.values():
        Path(geom_file).unlink(missing_ok=True)

    return results


if __name__ == "__main__":
    print("\n" + "="*70)
    print("KooMeshGenerator - Drop Test Simulation Example")
    print("="*70)
    print("\nThis example demonstrates drop test setup with impact analysis.")
    print("Replace mock geometry with actual CAD files for real simulations.")

    # Run main drop test
    try:
        result = drop_test_simulation()

        if result.success:
            print("\n" + "="*70)
            print("✓ EXAMPLE COMPLETED SUCCESSFULLY")
            print("="*70)
            print(f"\nNext steps:")
            print(f"  1. Open output/drop_test.k in LS-PrePost")
            print(f"  2. Verify mesh quality in impact zones")
            print(f"  3. Assign materials (glass, plastic, etc.)")
            print(f"  4. Set up drop test boundary conditions")
            print(f"  5. Run LS-DYNA explicit solver")
            print(f"  6. Analyze impact forces and stresses")

            # Optional: Run parametric study
            print(f"\nOptional: Run parametric study")
            print(f"  Uncomment parametric_drop_test() to test multiple heights")

    except Exception as e:
        print("\n" + "="*70)
        print("✗ EXAMPLE FAILED")
        print("="*70)
        print(f"Error: {e}")
        sys.exit(1)
