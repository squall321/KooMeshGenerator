"""
Adaptive Mesh Refinement Demo
==============================

This example demonstrates the adaptive mesh refinement (AMR) capabilities
of KooMeshGenerator. AMR allows you to create finer mesh in regions of interest
while keeping coarser mesh elsewhere, reducing computational cost.

Features demonstrated:
1. Box-shaped refinement zones
2. Sphere-shaped refinement zones
3. Cylinder-shaped refinement zones
4. Curvature-based refinement
5. Multiple zones with different strategies
6. Boundary layer refinement
7. Stress concentration refinement

Run this demo:
    python examples/adaptive_mesh_refinement_demo.py
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from koomesh.meshing.gmsh_utils import GmshWrapper
    from koomesh.meshing.adaptive_refiner import (
        AdaptiveMeshRefiner,
        BoxZone,
        SphereZone,
        CylinderZone,
        create_refinement_from_stress_concentrations,
        create_boundary_layer_refinement
    )
    from koomesh.meshing.quality_checker import QualityChecker
    from koomesh.export.lsdyna_writer import LSDynaWriter
    import gmsh
    GMSH_AVAILABLE = True
except ImportError as e:
    print(f"Error: Required modules not available: {e}")
    print("Please install GMSH: pip install gmsh")
    sys.exit(1)


def demo_box_refinement():
    """Demonstrate box-shaped refinement zone"""
    print("\n" + "="*70)
    print("Demo 1: Box-Shaped Refinement Zone")
    print("="*70)

    print("\nThis demo creates a box geometry with refined mesh in the center.")
    print("Center region will have 5x finer mesh than the rest.")

    with GmshWrapper() as wrapper:
        wrapper.new_model("box_refinement")

        # Create box geometry (10x10x10)
        print("\nCreating box geometry (10x10x10)...")
        box = gmsh.model.occ.addBox(0, 0, 0, 10, 10, 10)
        gmsh.model.occ.synchronize()

        # Set up adaptive refinement
        print("\nSetting up adaptive refinement:")
        print("  - Base mesh size: 1.0")
        print("  - Refinement zone: Box at center (5,5,5)")
        print("  - Zone size: 2x2x2")
        print("  - Fine mesh size: 0.2")

        refiner = AdaptiveMeshRefiner(base_mesh_size=1.0)
        refiner.add_refinement_zone(
            BoxZone(
                center=(5, 5, 5),
                size=(2, 2, 2),
                mesh_size=0.2,
                transition_distance=1.0
            )
        )

        wrapper.set_adaptive_refinement(refiner)

        # Generate mesh
        print("\nGenerating mesh...")
        wrapper.generate_mesh(3)
        wrapper.optimize_mesh()

        # Extract mesh
        mesh_data = wrapper.extract_mesh()

        # Get stats
        stats = wrapper.get_mesh_statistics()
        print(f"\nMesh Statistics:")
        print(f"  Nodes: {stats['num_nodes']}")
        print(f"  Elements: {stats['num_elements']}")

        # Export
        output_file = "/tmp/box_refinement.k"
        print(f"\nExporting to {output_file}...")
        with LSDynaWriter(output_file) as writer:
            writer.write_header()
            writer.write_nodes(mesh_data)
            writer.write_elements(mesh_data)

        print(f"✓ Demo 1 complete! Output: {output_file}")

    return mesh_data


def demo_sphere_refinement():
    """Demonstrate sphere-shaped refinement zone"""
    print("\n" + "="*70)
    print("Demo 2: Sphere-Shaped Refinement Zone")
    print("="*70)

    print("\nThis demo creates a box with spherical refined region.")
    print("Useful for point loads or stress concentrations.")

    with GmshWrapper() as wrapper:
        wrapper.new_model("sphere_refinement")

        # Create box geometry
        print("\nCreating box geometry (20x20x20)...")
        box = gmsh.model.occ.addBox(0, 0, 0, 20, 20, 20)
        gmsh.model.occ.synchronize()

        # Set up refinement
        print("\nSetting up adaptive refinement:")
        print("  - Base mesh size: 2.0")
        print("  - Refinement zone: Sphere at (10,10,10)")
        print("  - Sphere radius: 4.0")
        print("  - Fine mesh size: 0.3")

        refiner = AdaptiveMeshRefiner(base_mesh_size=2.0)
        refiner.add_refinement_zone(
            SphereZone(
                center=(10, 10, 10),
                radius=4.0,
                mesh_size=0.3,
                transition_distance=2.0
            )
        )

        wrapper.set_adaptive_refinement(refiner)
        wrapper.generate_mesh(3)
        wrapper.optimize_mesh()

        mesh_data = wrapper.extract_mesh()
        stats = wrapper.get_mesh_statistics()

        print(f"\nMesh Statistics:")
        print(f"  Nodes: {stats['num_nodes']}")
        print(f"  Elements: {stats['num_elements']}")

        output_file = "/tmp/sphere_refinement.k"
        with LSDynaWriter(output_file) as writer:
            writer.write_header()
            writer.write_nodes(mesh_data)
            writer.write_elements(mesh_data)

        print(f"✓ Demo 2 complete! Output: {output_file}")

    return mesh_data


def demo_multiple_zones():
    """Demonstrate multiple refinement zones"""
    print("\n" + "="*70)
    print("Demo 3: Multiple Refinement Zones")
    print("="*70)

    print("\nThis demo uses multiple refinement zones in one mesh.")
    print("Demonstrates combining box, sphere, and cylinder zones.")

    with GmshWrapper() as wrapper:
        wrapper.new_model("multiple_zones")

        # Create larger box
        print("\nCreating box geometry (30x30x30)...")
        box = gmsh.model.occ.addBox(0, 0, 0, 30, 30, 30)
        gmsh.model.occ.synchronize()

        # Set up multiple refinement zones
        print("\nSetting up multiple refinement zones:")
        refiner = AdaptiveMeshRefiner(base_mesh_size=2.0)

        # Zone 1: Box in corner
        print("  Zone 1: Box at (5,5,5), size 3x3x3, mesh size 0.3")
        refiner.add_refinement_zone(
            BoxZone(
                center=(5, 5, 5),
                size=(3, 3, 3),
                mesh_size=0.3
            )
        )

        # Zone 2: Sphere in center
        print("  Zone 2: Sphere at (15,15,15), radius 4, mesh size 0.4")
        refiner.add_refinement_zone(
            SphereZone(
                center=(15, 15, 15),
                radius=4.0,
                mesh_size=0.4
            )
        )

        # Zone 3: Cylinder
        print("  Zone 3: Cylinder at (25,25,15), radius 2, mesh size 0.5")
        refiner.add_refinement_zone(
            CylinderZone(
                center=(25, 25, 15),
                axis=(0, 0, 1),
                radius=2.0,
                height=10.0,
                mesh_size=0.5
            )
        )

        # Apply all zones
        wrapper.set_adaptive_refinement(refiner)
        wrapper.generate_mesh(3)
        wrapper.optimize_mesh()

        mesh_data = wrapper.extract_mesh()
        stats = wrapper.get_mesh_statistics()

        print(f"\nMesh Statistics:")
        print(f"  Nodes: {stats['num_nodes']}")
        print(f"  Elements: {stats['num_elements']}")

        output_file = "/tmp/multiple_zones.k"
        with LSDynaWriter(output_file) as writer:
            writer.write_header()
            writer.write_nodes(mesh_data)
            writer.write_elements(mesh_data)

        print(f"✓ Demo 3 complete! Output: {output_file}")

    return mesh_data


def demo_curvature_refinement():
    """Demonstrate curvature-based refinement"""
    print("\n" + "="*70)
    print("Demo 4: Curvature-Based Refinement")
    print("="*70)

    print("\nThis demo enables automatic refinement based on geometry curvature.")
    print("Regions with high curvature will automatically get finer mesh.")

    with GmshWrapper() as wrapper:
        wrapper.new_model("curvature_refinement")

        # Create geometry with curves (cylinder + sphere)
        print("\nCreating geometry with curves...")
        cylinder = gmsh.model.occ.addCylinder(0, 0, 0, 0, 0, 10, 3)
        sphere = gmsh.model.occ.addSphere(0, 0, 12, 4)
        gmsh.model.occ.synchronize()

        # Enable curvature refinement
        print("\nEnabling curvature-based refinement:")
        print("  - Minimum 20 points per curve")
        print("  - Minimum 40 points per full circle")

        refiner = AdaptiveMeshRefiner(base_mesh_size=1.0)
        refiner.enable_curvature_refinement(
            min_points_per_curve=20,
            min_points_per_circle=40
        )

        wrapper.set_adaptive_refinement(refiner)
        wrapper.generate_mesh(3)
        wrapper.optimize_mesh()

        mesh_data = wrapper.extract_mesh()
        stats = wrapper.get_mesh_statistics()

        print(f"\nMesh Statistics:")
        print(f"  Nodes: {stats['num_nodes']}")
        print(f"  Elements: {stats['num_elements']}")

        output_file = "/tmp/curvature_refinement.k"
        with LSDynaWriter(output_file) as writer:
            writer.write_header()
            writer.write_nodes(mesh_data)
            writer.write_elements(mesh_data)

        print(f"✓ Demo 4 complete! Output: {output_file}")

    return mesh_data


def demo_stress_concentration_refinement():
    """Demonstrate refinement at known stress concentration points"""
    print("\n" + "="*70)
    print("Demo 5: Stress Concentration Refinement")
    print("="*70)

    print("\nThis demo refines mesh at known stress concentration points.")
    print("Useful when you know where high stresses will occur.")

    with GmshWrapper() as wrapper:
        wrapper.new_model("stress_concentration")

        # Create plate with holes (simplified)
        print("\nCreating box geometry (40x40x5)...")
        box = gmsh.model.occ.addBox(0, 0, 0, 40, 40, 5)
        gmsh.model.occ.synchronize()

        # Define stress concentration points (e.g., around holes)
        stress_points = [
            (10, 10, 2.5),  # Point 1
            (30, 10, 2.5),  # Point 2
            (10, 30, 2.5),  # Point 3
            (30, 30, 2.5),  # Point 4
        ]

        print(f"\nDefining {len(stress_points)} stress concentration points...")
        for i, point in enumerate(stress_points, 1):
            print(f"  Point {i}: {point}")

        # Create refinement from stress points
        refiner = create_refinement_from_stress_concentrations(
            stress_points=stress_points,
            base_size=2.0,
            fine_size=0.3,
            radius=3.0
        )

        print("\nRefinement configuration:")
        print(f"  Base mesh size: 2.0")
        print(f"  Fine mesh size: 0.3")
        print(f"  Refinement radius: 3.0")

        wrapper.set_adaptive_refinement(refiner)
        wrapper.generate_mesh(3)
        wrapper.optimize_mesh()

        mesh_data = wrapper.extract_mesh()
        stats = wrapper.get_mesh_statistics()

        print(f"\nMesh Statistics:")
        print(f"  Nodes: {stats['num_nodes']}")
        print(f"  Elements: {stats['num_elements']}")

        output_file = "/tmp/stress_concentration.k"
        with LSDynaWriter(output_file) as writer:
            writer.write_header()
            writer.write_nodes(mesh_data)
            writer.write_elements(mesh_data)

        print(f"✓ Demo 5 complete! Output: {output_file}")

    return mesh_data


def demo_combined_strategies():
    """Demonstrate combining multiple refinement strategies"""
    print("\n" + "="*70)
    print("Demo 6: Combined Refinement Strategies")
    print("="*70)

    print("\nThis demo combines multiple strategies:")
    print("  - Geometric zones (box, sphere)")
    print("  - Curvature-based refinement")
    print("  - Multiple refinement levels")

    with GmshWrapper() as wrapper:
        wrapper.new_model("combined_strategies")

        # Create complex geometry
        print("\nCreating geometry...")
        box = gmsh.model.occ.addBox(0, 0, 0, 50, 50, 20)
        gmsh.model.occ.synchronize()

        # Set up combined refinement
        print("\nSetting up combined refinement:")
        refiner = AdaptiveMeshRefiner(base_mesh_size=3.0)

        # Enable curvature
        print("  ✓ Curvature refinement enabled")
        refiner.enable_curvature_refinement(min_points_per_curve=15)

        # Add geometric zones
        print("  ✓ Fine zone: Sphere at (25,25,10), size 0.3")
        refiner.add_refinement_zone(
            SphereZone(
                center=(25, 25, 10),
                radius=8.0,
                mesh_size=0.3
            )
        )

        print("  ✓ Medium zone: Box at (10,10,5), size 0.8")
        refiner.add_refinement_zone(
            BoxZone(
                center=(10, 10, 5),
                size=(5, 5, 5),
                mesh_size=0.8
            )
        )

        wrapper.set_adaptive_refinement(refiner)
        wrapper.generate_mesh(3)
        wrapper.optimize_mesh()

        mesh_data = wrapper.extract_mesh()
        stats = wrapper.get_mesh_statistics()

        print(f"\nMesh Statistics:")
        print(f"  Nodes: {stats['num_nodes']}")
        print(f"  Elements: {stats['num_elements']}")

        # Quality check
        print("\nPerforming quality check...")
        checker = QualityChecker()
        report = checker.check_mesh(mesh_data)

        print(f"  Jacobian - Min: {report.jacobian['min']:.6f}")
        print(f"  Jacobian - Mean: {report.jacobian['mean']:.6f}")

        output_file = "/tmp/combined_strategies.k"
        with LSDynaWriter(output_file) as writer:
            writer.write_header()
            writer.write_nodes(mesh_data)
            writer.write_elements(mesh_data)

        print(f"✓ Demo 6 complete! Output: {output_file}")

    return mesh_data


def print_summary():
    """Print summary of AMR capabilities"""
    print("\n" + "="*70)
    print("Adaptive Mesh Refinement Summary")
    print("="*70)

    print("\n📌 Key Features:")
    print("  • Box, Sphere, and Cylinder refinement zones")
    print("  • Curvature-based automatic refinement")
    print("  • Multiple zones with smooth transitions")
    print("  • Stress concentration point refinement")
    print("  • Boundary layer refinement")
    print("  • Combine multiple strategies")

    print("\n📊 Benefits:")
    print("  • Reduced element count (faster simulation)")
    print("  • Focused accuracy where needed")
    print("  • Automatic adaptation to geometry")
    print("  • Easy to use API")

    print("\n💡 Use Cases:")
    print("  • Crash analysis: Refine impact zones")
    print("  • Contact simulation: Refine contact surfaces")
    print("  • CFD: Boundary layers near walls")
    print("  • Stress analysis: Refine notches, holes")
    print("  • Multi-scale problems")

    print("\n📂 Output Files:")
    print("  All demos generated LS-DYNA .k files in /tmp/")
    print("  Import these files into LS-DYNA or other FEA solvers")


def main():
    """Run all AMR demonstrations"""
    print("="*70)
    print("KooMeshGenerator: Adaptive Mesh Refinement Demo")
    print("="*70)

    try:
        demo_box_refinement()
        demo_sphere_refinement()
        demo_multiple_zones()
        demo_curvature_refinement()
        demo_stress_concentration_refinement()
        demo_combined_strategies()

        print_summary()

        print("\n" + "="*70)
        print("All Demos Complete!")
        print("="*70)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
