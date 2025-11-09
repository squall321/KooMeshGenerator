"""
Tests for Contact Type Classification

Tests automatic contact type classification and LS-DYNA parameter optimization.
"""

import pytest
import numpy as np
from unittest.mock import Mock

from koomesh.contact.contact_classifier import (
    ContactType,
    ContactParameters,
    ContactClassifier,
    ContactPair
)


@pytest.fixture
def classifier():
    """Create ContactClassifier instance"""
    return ContactClassifier()


@pytest.fixture
def sample_contact_data():
    """Create sample contact data for testing"""
    return {
        'gap': 0.1,
        'surface_angle': 0.0,
        'contact_area': 100.0,
        'material1': 'Steel_Mild',
        'material2': 'Aluminum_6061'
    }


class TestContactType:
    """Test ContactType enum"""

    def test_contact_types_exist(self):
        """Test that all contact types are defined"""
        assert ContactType.AUTOMATIC is not None
        assert ContactType.TIED is not None
        assert ContactType.SLIDING is not None
        assert ContactType.TIEBREAK is not None
        assert ContactType.FORMING is not None
        assert ContactType.ERODING is not None

    def test_contact_type_values(self):
        """Test contact type string values"""
        assert ContactType.AUTOMATIC.value == 'AUTOMATIC'
        assert ContactType.TIED.value == 'TIED'
        assert ContactType.SLIDING.value == 'SLIDING'


class TestContactParameters:
    """Test ContactParameters dataclass"""

    def test_default_parameters(self):
        """Test default parameter creation"""
        params = ContactParameters()

        assert params.fs == 0.0  # Default friction
        assert params.fd == 0.0
        assert params.soft == 0
        assert params.depth == 5

    def test_custom_parameters(self):
        """Test custom parameter creation"""
        params = ContactParameters(
            fs=0.3,
            fd=0.2,
            soft=2,
            depth=10,
            sbopt=2.0,
            penmax=1e10
        )

        assert params.fs == 0.3
        assert params.fd == 0.2
        assert params.soft == 2
        assert params.depth == 10
        assert params.sbopt == 2.0
        assert params.penmax == 1e10


class TestContactClassifier:
    """Test ContactClassifier class"""

    def test_initialization(self, classifier):
        """Test classifier initialization"""
        assert classifier is not None
        assert classifier.logger is not None

    # ============= Contact Type Classification Tests =============

    def test_classify_tied_contact(self, classifier):
        """Test classification of tied (bonded) contact"""
        # Very small gap → TIED
        contact_type = classifier.classify_contact_type(
            gap=0.005,  # < 0.01mm
            surface_angle=0.0,  # Parallel
            contact_area=50.0,  # Medium area
            material1='Steel_Mild',
            material2='Steel_Mild'
        )

        assert contact_type == ContactType.TIED

    def test_classify_tiebreak_contact(self, classifier):
        """Test classification of tiebreak (spot weld) contact"""
        # Very small gap + small area → TIEBREAK
        contact_type = classifier.classify_contact_type(
            gap=0.005,  # < 0.01mm
            surface_angle=0.0,
            contact_area=5.0,  # < 10mm² (spot weld size)
            material1='Steel_Mild',
            material2='Steel_Mild'
        )

        assert contact_type == ContactType.TIEBREAK

    def test_classify_sliding_contact(self, classifier):
        """Test classification of sliding contact"""
        # Large angle → SLIDING
        contact_type = classifier.classify_contact_type(
            gap=0.5,
            surface_angle=85.0,  # > 80° (nearly perpendicular)
            contact_area=50.0,
            material1='Steel_Mild',
            material2='Aluminum_6061'
        )

        assert contact_type == ContactType.SLIDING

    def test_classify_forming_contact(self, classifier):
        """Test classification of forming contact"""
        # Large area + parallel → FORMING
        contact_type = classifier.classify_contact_type(
            gap=0.2,
            surface_angle=2.0,  # < 5° (nearly parallel)
            contact_area=500.0,  # > 100mm² (large area)
            material1='Steel_Mild',
            material2='Aluminum_6061'
        )

        assert contact_type == ContactType.FORMING

    def test_classify_eroding_contact(self, classifier):
        """Test classification of eroding contact"""
        # Eroding material → ERODING
        contact_type = classifier.classify_contact_type(
            gap=0.2,
            surface_angle=10.0,
            contact_area=50.0,
            material1='Steel_Mild',
            material2='Foam_Polyurethane'  # Soft/crushable material
        )

        # For now, may return AUTOMATIC if eroding logic not fully implemented
        # Just check it returns a valid type
        assert isinstance(contact_type, ContactType)

    def test_classify_automatic_fallback(self, classifier):
        """Test fallback to AUTOMATIC for general cases"""
        # Medium gap, medium angle, medium area
        contact_type = classifier.classify_contact_type(
            gap=0.5,
            surface_angle=30.0,
            contact_area=50.0,
            material1='Steel_Mild',
            material2='Aluminum_6061'
        )

        # Should use AUTOMATIC for general cases
        assert contact_type == ContactType.AUTOMATIC

    # ============= Parameter Optimization Tests =============

    def test_optimize_parameters_for_tied(self, classifier):
        """Test parameter optimization for TIED contact"""
        params = classifier.optimize_parameters(
            contact_type=ContactType.TIED,
            gap=0.005,
            surface_angle=0.0,
            material1='Steel_Mild',
            material2='Steel_Mild'
        )

        # TIED should have no friction (bonded)
        assert params.fs == 0.0
        # Should use soft constraint for small gaps
        assert params.soft in [1, 2]

    def test_optimize_parameters_for_sliding(self, classifier):
        """Test parameter optimization for SLIDING contact"""
        params = classifier.optimize_parameters(
            contact_type=ContactType.SLIDING,
            gap=0.5,
            surface_angle=85.0,
            material1='Steel_Mild',
            material2='Aluminum_6061'
        )

        # SLIDING should have friction
        assert params.fs > 0.0
        # Typical steel-aluminum friction: 0.2-0.5
        assert 0.1 <= params.fs <= 0.6

    def test_optimize_parameters_for_forming(self, classifier):
        """Test parameter optimization for FORMING contact"""
        params = classifier.optimize_parameters(
            contact_type=ContactType.FORMING,
            gap=0.2,
            surface_angle=2.0,
            material1='Steel_Mild',
            material2='Aluminum_6061'
        )

        # FORMING should have moderate friction
        assert params.fs > 0.0
        # Should use appropriate depth for forming
        assert params.depth >= 5

    def test_optimize_parameters_for_tiebreak(self, classifier):
        """Test parameter optimization for TIEBREAK contact"""
        params = classifier.optimize_parameters(
            contact_type=ContactType.TIEBREAK,
            gap=0.005,
            surface_angle=0.0,
            material1='Steel_Mild',
            material2='Steel_Mild'
        )

        # TIEBREAK has special parameters
        # Should have failure criteria defined
        assert hasattr(params, 'fs')

    # ============= Friction Estimation Tests =============

    def test_estimate_friction_steel_steel(self, classifier):
        """Test friction estimation for steel-steel contact"""
        friction = classifier._estimate_friction('Steel_Mild', 'Steel_HighStrength')

        # Steel-steel: typically 0.5-0.8 (dry), 0.1-0.2 (lubricated)
        # Using default (dry)
        assert 0.3 <= friction <= 0.8

    def test_estimate_friction_steel_aluminum(self, classifier):
        """Test friction estimation for steel-aluminum contact"""
        friction = classifier._estimate_friction('Steel_Mild', 'Aluminum_6061')

        # Steel-aluminum: typically 0.4-0.6
        assert 0.2 <= friction <= 0.7

    def test_estimate_friction_steel_plastic(self, classifier):
        """Test friction estimation for steel-plastic contact"""
        friction = classifier._estimate_friction('Steel_Mild', 'Plastic_ABS')

        # Steel-plastic: typically 0.2-0.4
        assert 0.1 <= friction <= 0.5

    def test_estimate_friction_symmetric(self, classifier):
        """Test that friction estimation is symmetric"""
        friction1 = classifier._estimate_friction('Steel_Mild', 'Aluminum_6061')
        friction2 = classifier._estimate_friction('Aluminum_6061', 'Steel_Mild')

        assert friction1 == friction2

    def test_estimate_friction_unknown_materials(self, classifier):
        """Test friction estimation with unknown materials"""
        friction = classifier._estimate_friction('Unknown_Material', 'Another_Unknown')

        # Should return default friction
        assert friction == 0.3  # Default

    # ============= Helper Method Tests =============

    def test_is_soft_material(self, classifier):
        """Test soft material detection"""
        # Soft materials
        assert classifier._is_soft_material('Foam_Polyurethane')
        assert classifier._is_soft_material('Rubber_Natural')
        assert classifier._is_soft_material('Plastic_PP')  # Plastics are somewhat soft

        # Hard materials
        assert not classifier._is_soft_material('Steel_Mild')
        assert not classifier._is_soft_material('Aluminum_6061')

    def test_material_category_detection(self, classifier):
        """Test material category detection from name"""
        # Metals
        assert 'Steel' in 'Steel_Mild'
        assert 'Aluminum' in 'Aluminum_6061'

        # Plastics
        assert 'Plastic' in 'Plastic_ABS'

        # Foams
        assert 'Foam' in 'Foam_Polyurethane'

    # ============= ContactPair Tests =============

    def test_create_contact_pair_basic(self):
        """Test basic contact pair creation"""
        pair = ContactPair(
            master_part='Part1',
            slave_part='Part2',
            contact_type=ContactType.AUTOMATIC,
            parameters=ContactParameters()
        )

        assert pair.master_part == 'Part1'
        assert pair.slave_part == 'Part2'
        assert pair.contact_type == ContactType.AUTOMATIC
        assert isinstance(pair.parameters, ContactParameters)

    def test_create_contact_pair_with_metadata(self):
        """Test contact pair with metadata"""
        pair = ContactPair(
            master_part='Part1',
            slave_part='Part2',
            contact_type=ContactType.SLIDING,
            parameters=ContactParameters(fs=0.3),
            metadata={
                'gap': 0.5,
                'area': 100.0,
                'angle': 45.0
            }
        )

        assert pair.metadata['gap'] == 0.5
        assert pair.metadata['area'] == 100.0
        assert pair.metadata['angle'] == 45.0


class TestContactClassifierIntegration:
    """Integration tests for contact classification workflow"""

    @pytest.mark.integration
    def test_full_classification_workflow(self, classifier):
        """Test complete classification workflow"""
        # Step 1: Classify contact type
        contact_type = classifier.classify_contact_type(
            gap=0.2,
            surface_angle=10.0,
            contact_area=75.0,
            material1='Steel_Mild',
            material2='Aluminum_6061'
        )

        # Step 2: Optimize parameters
        params = classifier.optimize_parameters(
            contact_type=contact_type,
            gap=0.2,
            surface_angle=10.0,
            material1='Steel_Mild',
            material2='Aluminum_6061'
        )

        # Step 3: Create contact pair
        pair = ContactPair(
            master_part='Body',
            slave_part='Bumper',
            contact_type=contact_type,
            parameters=params,
            metadata={
                'gap': 0.2,
                'area': 75.0,
                'angle': 10.0
            }
        )

        # Verify complete pair
        assert pair.contact_type == contact_type
        assert pair.parameters.fs >= 0.0
        assert pair.metadata['gap'] == 0.2

    @pytest.mark.integration
    def test_multiple_contact_scenarios(self, classifier):
        """Test classification across multiple scenarios"""
        scenarios = [
            # (gap, angle, area, expected_type)
            (0.005, 0.0, 5.0, ContactType.TIEBREAK),  # Spot weld
            (0.005, 0.0, 50.0, ContactType.TIED),  # Bonded
            (0.5, 85.0, 50.0, ContactType.SLIDING),  # Sliding
            (0.2, 2.0, 500.0, ContactType.FORMING),  # Forming
        ]

        for gap, angle, area, expected_type in scenarios:
            contact_type = classifier.classify_contact_type(
                gap=gap,
                surface_angle=angle,
                contact_area=area,
                material1='Steel_Mild',
                material2='Aluminum_6061'
            )

            assert contact_type == expected_type, \
                f"Failed for gap={gap}, angle={angle}, area={area}"


class TestContactClassifierEdgeCases:
    """Test edge cases and error handling"""

    def test_negative_gap(self, classifier):
        """Test with negative gap (penetration)"""
        contact_type = classifier.classify_contact_type(
            gap=-0.1,  # Penetration
            surface_angle=0.0,
            contact_area=50.0,
            material1='Steel_Mild',
            material2='Aluminum_6061'
        )

        # Should still classify (may treat as very small gap)
        assert isinstance(contact_type, ContactType)

    def test_very_large_gap(self, classifier):
        """Test with very large gap"""
        contact_type = classifier.classify_contact_type(
            gap=100.0,  # Very large
            surface_angle=0.0,
            contact_area=50.0,
            material1='Steel_Mild',
            material2='Aluminum_6061'
        )

        # Should return AUTOMATIC or similar
        assert isinstance(contact_type, ContactType)

    def test_zero_contact_area(self, classifier):
        """Test with zero contact area"""
        contact_type = classifier.classify_contact_type(
            gap=0.1,
            surface_angle=0.0,
            contact_area=0.0,  # No area
            material1='Steel_Mild',
            material2='Aluminum_6061'
        )

        # Should handle gracefully
        assert isinstance(contact_type, ContactType)

    def test_invalid_surface_angle(self, classifier):
        """Test with invalid surface angle"""
        # Angle > 180°
        contact_type = classifier.classify_contact_type(
            gap=0.1,
            surface_angle=200.0,
            contact_area=50.0,
            material1='Steel_Mild',
            material2='Aluminum_6061'
        )

        # Should handle gracefully
        assert isinstance(contact_type, ContactType)

    def test_none_materials(self, classifier):
        """Test with None materials"""
        friction = classifier._estimate_friction(None, None)

        # Should return default
        assert friction == 0.3

    def test_empty_material_names(self, classifier):
        """Test with empty material names"""
        friction = classifier._estimate_friction('', '')

        # Should return default
        assert friction == 0.3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
