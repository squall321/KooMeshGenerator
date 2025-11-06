"""
Tests for Adaptive Mesh Refinement
===================================

This module tests the adaptive mesh refinement (AMR) functionality.
"""

import pytest
import numpy as np

# Try to import GMSH-dependent modules
try:
    import gmsh
    from koomesh.meshing.adaptive_refiner import (
        AdaptiveMeshRefiner,
        BoxZone,
        SphereZone,
        CylinderZone,
        DistanceToSurfaceZone,
        create_refinement_from_stress_concentrations,
        create_boundary_layer_refinement
    )
    from koomesh.meshing.gmsh_utils import GmshWrapper
    GMSH_AVAILABLE = True
except ImportError:
    GMSH_AVAILABLE = False

pytestmark = pytest.mark.skipif(not GMSH_AVAILABLE, reason="GMSH not available")


class TestRefinementZones:
    """Test refinement zone classes"""

    def test_box_zone_creation(self):
        """Test BoxZone creation"""
        zone = BoxZone(
            center=(5.0, 5.0, 5.0),
            size=(2.0, 2.0, 2.0),
            mesh_size=0.1,
            transition_distance=1.0
        )

        assert zone.center == (5.0, 5.0, 5.0)
        assert zone.size == (2.0, 2.0, 2.0)
        assert zone.mesh_size == 0.1
        assert zone.transition_distance == 1.0

        desc = zone.get_description()
        assert "Box" in desc
        assert "0.1" in desc

    def test_sphere_zone_creation(self):
        """Test SphereZone creation"""
        zone = SphereZone(
            center=(10.0, 10.0, 10.0),
            radius=3.0,
            mesh_size=0.2,
            transition_distance=1.5
        )

        assert zone.center == (10.0, 10.0, 10.0)
        assert zone.radius == 3.0
        assert zone.mesh_size == 0.2

        desc = zone.get_description()
        assert "Sphere" in desc
        assert "0.2" in desc

    def test_cylinder_zone_creation(self):
        """Test CylinderZone creation"""
        zone = CylinderZone(
            center=(0.0, 0.0, 0.0),
            axis=(0.0, 0.0, 1.0),
            radius=2.0,
            height=10.0,
            mesh_size=0.15
        )

        assert zone.center == (0.0, 0.0, 0.0)
        assert zone.axis == (0.0, 0.0, 1.0)
        assert zone.radius == 2.0
        assert zone.mesh_size == 0.15

        desc = zone.get_description()
        assert "Cylinder" in desc

    def test_distance_to_surface_zone_creation(self):
        """Test DistanceToSurfaceZone creation"""
        zone = DistanceToSurfaceZone(
            surface_tags=[1, 2, 3],
            mesh_size_near=0.05,
            mesh_size_far=1.0,
            distance_near=0.5,
            distance_far=2.0
        )

        assert zone.surface_tags == [1, 2, 3]
        assert zone.mesh_size_near == 0.05
        assert zone.mesh_size_far == 1.0

        desc = zone.get_description()
        assert "Distance" in desc


class TestAdaptiveMeshRefiner:
    """Test AdaptiveMeshRefiner class"""

    def test_refiner_creation(self):
        """Test creating AdaptiveMeshRefiner"""
        refiner = AdaptiveMeshRefiner(base_mesh_size=1.0)

        assert refiner.base_mesh_size == 1.0
        assert len(refiner.zones) == 0
        assert refiner.curvature_enabled is False

    def test_add_refinement_zone(self):
        """Test adding refinement zones"""
        refiner = AdaptiveMeshRefiner(base_mesh_size=1.0)

        zone1 = BoxZone((5, 5, 5), (2, 2, 2), 0.1)
        zone2 = SphereZone((10, 10, 10), 3.0, 0.2)

        refiner.add_refinement_zone(zone1)
        refiner.add_refinement_zone(zone2)

        assert len(refiner.zones) == 2

    def test_enable_curvature_refinement(self):
        """Test enabling curvature refinement"""
        refiner = AdaptiveMeshRefiner(base_mesh_size=1.0)

        refiner.enable_curvature_refinement(
            min_points_per_curve=15,
            min_points_per_circle=30
        )

        assert refiner.curvature_enabled is True
        assert refiner.curvature_params['min_points_per_curve'] == 15
        assert refiner.curvature_params['min_points_per_circle'] == 30

    def test_clear_zones(self):
        """Test clearing refinement zones"""
        refiner = AdaptiveMeshRefiner(base_mesh_size=1.0)

        zone1 = BoxZone((5, 5, 5), (2, 2, 2), 0.1)
        zone2 = SphereZone((10, 10, 10), 3.0, 0.2)

        refiner.add_refinement_zone(zone1)
        refiner.add_refinement_zone(zone2)
        assert len(refiner.zones) == 2

        refiner.clear_zones()
        assert len(refiner.zones) == 0

    def test_remove_zone(self):
        """Test removing specific zone"""
        refiner = AdaptiveMeshRefiner(base_mesh_size=1.0)

        zone1 = BoxZone((5, 5, 5), (2, 2, 2), 0.1)
        zone2 = SphereZone((10, 10, 10), 3.0, 0.2)

        refiner.add_refinement_zone(zone1)
        refiner.add_refinement_zone(zone2)

        refiner.remove_zone(0)
        assert len(refiner.zones) == 1

    def test_get_summary(self):
        """Test getting refiner summary"""
        refiner = AdaptiveMeshRefiner(base_mesh_size=1.0)

        zone1 = BoxZone((5, 5, 5), (2, 2, 2), 0.1)
        refiner.add_refinement_zone(zone1)
        refiner.enable_curvature_refinement()

        summary = refiner.get_summary()

        assert summary['base_mesh_size'] == 1.0
        assert summary['num_zones'] == 1
        assert summary['curvature_enabled'] is True
        assert len(summary['zones']) == 1


class TestAMRIntegration:
    """Test AMR integration with GMSH"""

    def test_box_zone_gmsh_field(self):
        """Test BoxZone GMSH field creation"""
        with GmshWrapper() as wrapper:
            wrapper.new_model("test")

            # Create a simple box geometry
            box = gmsh.model.occ.addBox(0, 0, 0, 10, 10, 10)
            gmsh.model.occ.synchronize()

            # Create and apply box zone
            zone = BoxZone((5, 5, 5), (2, 2, 2), 0.2)
            next_id = zone.to_gmsh_field(1)

            # Should return next available field ID
            assert next_id == 2

    def test_sphere_zone_gmsh_field(self):
        """Test SphereZone GMSH field creation"""
        with GmshWrapper() as wrapper:
            wrapper.new_model("test")

            box = gmsh.model.occ.addBox(0, 0, 0, 10, 10, 10)
            gmsh.model.occ.synchronize()

            zone = SphereZone((5, 5, 5), 3.0, 0.2)
            next_id = zone.to_gmsh_field(1)

            assert next_id == 2

    def test_refiner_apply_to_gmsh(self):
        """Test applying refiner to GMSH"""
        with GmshWrapper() as wrapper:
            wrapper.new_model("test")

            # Create geometry
            box = gmsh.model.occ.addBox(0, 0, 0, 10, 10, 10)
            gmsh.model.occ.synchronize()

            # Create refiner with zones
            refiner = AdaptiveMeshRefiner(base_mesh_size=1.0)
            refiner.add_refinement_zone(BoxZone((3, 3, 3), (1, 1, 1), 0.1))
            refiner.add_refinement_zone(SphereZone((7, 7, 7), 1.5, 0.15))

            # Apply to GMSH
            refiner.apply_to_gmsh()

            # Should not raise any errors
            assert True

    def test_refiner_with_curvature(self):
        """Test refiner with curvature enabled"""
        with GmshWrapper() as wrapper:
            wrapper.new_model("test")

            box = gmsh.model.occ.addBox(0, 0, 0, 10, 10, 10)
            gmsh.model.occ.synchronize()

            refiner = AdaptiveMeshRefiner(base_mesh_size=1.0)
            refiner.enable_curvature_refinement(min_points_per_curve=20)

            refiner.apply_to_gmsh()

            # Check that curvature options were set
            assert gmsh.option.getNumber("Mesh.CharacteristicLengthFromCurvature") == 1

    def test_complete_amr_workflow(self):
        """Test complete AMR workflow: geometry -> refine -> mesh"""
        with GmshWrapper() as wrapper:
            wrapper.new_model("test")

            # Create box geometry
            box = gmsh.model.occ.addBox(0, 0, 0, 10, 10, 10)
            gmsh.model.occ.synchronize()

            # Set up adaptive refinement
            refiner = AdaptiveMeshRefiner(base_mesh_size=1.0)
            refiner.add_refinement_zone(BoxZone((5, 5, 5), (2, 2, 2), 0.2))
            refiner.enable_curvature_refinement()

            wrapper.set_adaptive_refinement(refiner)

            # Generate mesh
            wrapper.generate_mesh(3)

            # Extract mesh stats
            stats = wrapper.get_mesh_statistics()

            assert stats['num_nodes'] > 0
            assert stats['num_elements'] > 0


class TestHelperFunctions:
    """Test helper functions for AMR"""

    def test_create_refinement_from_stress_concentrations(self):
        """Test creating refinement from stress points"""
        points = [(5, 5, 0), (15, 15, 0), (25, 25, 0)]

        refiner = create_refinement_from_stress_concentrations(
            stress_points=points,
            base_size=1.0,
            fine_size=0.1,
            radius=2.0
        )

        assert len(refiner.zones) == 3
        assert refiner.base_mesh_size == 1.0

        # All zones should be SphereZones
        for zone in refiner.zones:
            assert isinstance(zone, SphereZone)
            assert zone.mesh_size == 0.1
            assert zone.radius == 2.0

    def test_create_boundary_layer_refinement(self):
        """Test creating boundary layer refinement"""
        surface_tags = [1, 2, 3]

        refiner = create_boundary_layer_refinement(
            surface_tags=surface_tags,
            first_layer_size=0.01,
            growth_rate=1.3,
            num_layers=5
        )

        # Should create num_layers zones
        assert len(refiner.zones) == 5

        # All zones should be DistanceToSurfaceZones
        for zone in refiner.zones:
            assert isinstance(zone, DistanceToSurfaceZone)


class TestAMRMeshQuality:
    """Test that AMR improves mesh quality in refined regions"""

    def test_mesh_size_distribution(self):
        """Test that mesh is finer in refinement zone"""
        with GmshWrapper() as wrapper:
            wrapper.new_model("test")

            # Create box
            box = gmsh.model.occ.addBox(0, 0, 0, 10, 10, 10)
            gmsh.model.occ.synchronize()

            # Refine center region
            refiner = AdaptiveMeshRefiner(base_mesh_size=1.0)
            refiner.add_refinement_zone(BoxZone((5, 5, 5), (2, 2, 2), 0.2))

            wrapper.set_adaptive_refinement(refiner)
            wrapper.generate_mesh(3)

            # Get mesh
            mesh_data = wrapper.extract_mesh()

            # Should have created elements
            assert mesh_data.num_elements() > 0

            # Calculate element sizes
            element_sizes = []
            for elem in mesh_data.elements.values():
                # Get element node coordinates
                coords = mesh_data.get_element_coordinates(elem.id)

                # Calculate approximate size (max distance between nodes)
                max_dist = 0
                for i in range(len(coords)):
                    for j in range(i+1, len(coords)):
                        dist = np.linalg.norm(coords[i] - coords[j])
                        max_dist = max(max_dist, dist)

                element_sizes.append(max_dist)

            # Should have a range of element sizes
            min_size = min(element_sizes)
            max_size = max(element_sizes)

            assert max_size > min_size
            # Refined region should have smaller elements
            assert min_size < 1.0  # Smaller than base size


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
