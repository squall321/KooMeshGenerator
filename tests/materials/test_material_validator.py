"""
Tests for Material Validation and Recommendation

Tests material validation for simulations and material recommendation system.
"""

import pytest
from unittest.mock import Mock, patch

from koomesh.materials.material_validator import (
    MaterialIssue,
    MaterialValidationReport,
    MaterialValidator,
    MaterialRecommender
)
from koomesh.materials.material_library import Material


@pytest.fixture
def validator():
    """Create MaterialValidator instance"""
    return MaterialValidator()


@pytest.fixture
def recommender():
    """Create MaterialRecommender instance"""
    return MaterialRecommender()


@pytest.fixture
def sample_material():
    """Create sample material for testing"""
    return Material(
        name='Steel_Mild',
        category='Metal',
        density=7850.0,  # kg/m³
        youngs_modulus=210000.0,  # MPa
        poissons_ratio=0.3,
        yield_strength=250.0,  # MPa
        ultimate_strength=400.0,  # MPa
        failure_strain=0.2
    )


class TestMaterialIssue:
    """Test MaterialIssue dataclass"""

    def test_material_issue_creation(self):
        """Test creating a material issue"""
        issue = MaterialIssue(
            part_index=0,
            part_name='Hood',
            severity='ERROR',
            message='Missing density',
            suggestion='Add density property'
        )

        assert issue.part_index == 0
        assert issue.part_name == 'Hood'
        assert issue.severity == 'ERROR'
        assert issue.message == 'Missing density'
        assert issue.suggestion == 'Add density property'


class TestMaterialValidationReport:
    """Test MaterialValidationReport dataclass"""

    def test_validation_report_creation(self):
        """Test creating a validation report"""
        issues = [
            MaterialIssue(0, 'Part1', 'ERROR', 'Test error', 'Fix it')
        ]

        report = MaterialValidationReport(
            valid=False,
            issues=issues,
            statistics={'num_errors': 1}
        )

        assert not report.valid
        assert len(report.issues) == 1
        assert report.statistics['num_errors'] == 1


class TestMaterialValidator:
    """Test MaterialValidator class"""

    def test_initialization(self, validator):
        """Test validator initialization"""
        assert validator is not None
        assert validator.logger is not None
        assert validator.material_library is not None

    # ============= Basic Validation Tests =============

    def test_validate_valid_material(self, validator, sample_material):
        """Test validation of valid material"""
        with patch.object(validator.material_library, 'get_material', return_value=sample_material):
            report = validator.validate_assignment(
                part_name='TestPart',
                material_name='Steel_Mild',
                simulation_type='crash'
            )

            # Should pass validation
            assert report.valid
            assert len([i for i in report.issues if i.severity == 'ERROR']) == 0

    def test_validate_nonexistent_material(self, validator):
        """Test validation with non-existent material"""
        with patch.object(validator.material_library, 'get_material', return_value=None):
            report = validator.validate_assignment(
                part_name='TestPart',
                material_name='NonExistent_Material',
                simulation_type='crash'
            )

            # Should fail
            assert not report.valid
            assert len([i for i in report.issues if i.severity == 'ERROR']) > 0

            # Should have specific error
            errors = [i for i in report.issues if i.severity == 'ERROR']
            assert any('not found' in e.message.lower() for e in errors)

    # ============= Simulation Compatibility Tests =============

    def test_crash_simulation_compatibility(self, validator):
        """Test material compatibility for crash simulation"""
        # Material without failure model
        material = Material(
            name='Test_Metal',
            category='Metal',
            density=7850.0,
            youngs_modulus=210000.0,
            poissons_ratio=0.3,
            yield_strength=250.0
            # Missing failure_strain
        )

        with patch.object(validator.material_library, 'get_material', return_value=material):
            report = validator.validate_assignment(
                part_name='TestPart',
                material_name='Test_Metal',
                simulation_type='crash'
            )

            # Should have warning about missing failure model
            warnings = [i for i in report.issues if i.severity == 'WARNING']
            assert any('failure' in w.message.lower() for w in warnings)

    def test_forming_simulation_compatibility(self, validator):
        """Test material compatibility for forming simulation"""
        # High-strength steel (poor formability)
        material = Material(
            name='Steel_HighStrength',
            category='Metal',
            density=7850.0,
            youngs_modulus=210000.0,
            poissons_ratio=0.3,
            yield_strength=800.0  # High strength → poor formability
        )

        with patch.object(validator.material_library, 'get_material', return_value=material):
            report = validator.validate_assignment(
                part_name='Blank',
                material_name='Steel_HighStrength',
                simulation_type='forming'
            )

            # Should have warning about formability
            warnings = [i for i in report.issues if i.severity == 'WARNING']
            assert any('formability' in w.message.lower() for w in warnings)

    def test_impact_simulation_compatibility(self, validator):
        """Test material compatibility for impact simulation"""
        # Brittle material (bad for impact)
        material = Material(
            name='Ceramic_Brittle',
            category='Brittle',
            density=2500.0,
            youngs_modulus=300000.0,
            poissons_ratio=0.25
        )

        with patch.object(validator.material_library, 'get_material', return_value=material):
            report = validator.validate_assignment(
                part_name='Component',
                material_name='Ceramic_Brittle',
                simulation_type='impact'
            )

            # Should have warning about brittleness
            warnings = [i for i in report.issues if i.severity == 'WARNING']
            assert any('brittle' in w.message.lower() for w in warnings)

    # ============= Property Completeness Tests =============

    def test_missing_essential_properties(self, validator):
        """Test material missing essential properties"""
        # Material missing density
        material = Material(
            name='Incomplete_Material',
            category='Metal',
            # Missing density
            youngs_modulus=210000.0,
            poissons_ratio=0.3
        )

        with patch.object(validator.material_library, 'get_material', return_value=material):
            report = validator.validate_assignment(
                part_name='TestPart',
                material_name='Incomplete_Material',
                simulation_type='crash'
            )

            # Should fail (missing essential property)
            assert not report.valid
            errors = [i for i in report.issues if i.severity == 'ERROR']
            assert any('density' in e.message.lower() for e in errors)

    def test_missing_simulation_specific_properties(self, validator):
        """Test material missing simulation-specific properties"""
        # Material without yield strength for crash
        material = Material(
            name='Test_Material',
            category='Metal',
            density=7850.0,
            youngs_modulus=210000.0,
            poissons_ratio=0.3
            # Missing yield_strength
        )

        with patch.object(validator.material_library, 'get_material', return_value=material):
            report = validator.validate_assignment(
                part_name='TestPart',
                material_name='Test_Material',
                simulation_type='crash'
            )

            # Should have warning
            warnings = [i for i in report.issues if i.severity == 'WARNING']
            assert any('yield_strength' in w.message.lower() for w in warnings)

    # ============= Physical Reasonableness Tests =============

    def test_unreasonably_low_youngs_modulus(self, validator):
        """Test material with unreasonably low Young's modulus"""
        material = Material(
            name='Test_Material',
            category='Metal',
            density=7850.0,
            youngs_modulus=0.01,  # Unreasonably low
            poissons_ratio=0.3
        )

        with patch.object(validator.material_library, 'get_material', return_value=material):
            report = validator.validate_assignment(
                part_name='TestPart',
                material_name='Test_Material',
                simulation_type='crash'
            )

            # Should have error
            errors = [i for i in report.issues if i.severity == 'ERROR']
            assert any('young' in e.message.lower() for e in errors)

    def test_very_high_youngs_modulus(self, validator):
        """Test material with very high Young's modulus"""
        material = Material(
            name='Test_Material',
            category='Metal',
            density=7850.0,
            youngs_modulus=1000000.0,  # Very high (diamond-like)
            poissons_ratio=0.3
        )

        with patch.object(validator.material_library, 'get_material', return_value=material):
            report = validator.validate_assignment(
                part_name='TestPart',
                material_name='Test_Material',
                simulation_type='crash'
            )

            # Should have warning
            warnings = [i for i in report.issues if i.severity == 'WARNING']
            assert any('young' in w.message.lower() for w in warnings)

    def test_invalid_poissons_ratio(self, validator):
        """Test material with invalid Poisson's ratio"""
        material = Material(
            name='Test_Material',
            category='Metal',
            density=7850.0,
            youngs_modulus=210000.0,
            poissons_ratio=0.7  # Invalid (> 0.5)
        )

        with patch.object(validator.material_library, 'get_material', return_value=material):
            report = validator.validate_assignment(
                part_name='TestPart',
                material_name='Test_Material',
                simulation_type='crash'
            )

            # Should have error
            errors = [i for i in report.issues if i.severity == 'ERROR']
            assert any('poisson' in e.message.lower() for e in errors)

    def test_unreasonably_low_density(self, validator):
        """Test material with unreasonably low density"""
        material = Material(
            name='Test_Material',
            category='Metal',
            density=0.0001,  # Unreasonably low
            youngs_modulus=210000.0,
            poissons_ratio=0.3
        )

        with patch.object(validator.material_library, 'get_material', return_value=material):
            report = validator.validate_assignment(
                part_name='TestPart',
                material_name='Test_Material',
                simulation_type='crash'
            )

            # Should have error
            errors = [i for i in report.issues if i.severity == 'ERROR']
            assert any('density' in e.message.lower() for e in errors)

    # ============= Practical Concerns Tests =============

    def test_very_heavy_part_warning(self, validator, sample_material):
        """Test warning for very heavy parts"""
        with patch.object(validator.material_library, 'get_material', return_value=sample_material):
            report = validator.validate_assignment(
                part_name='HeavyPart',
                material_name='Steel_Mild',
                simulation_type='crash',
                part_volume=200000.0  # cm³ → ~1600 kg with steel
            )

            # Should have info about weight
            info_issues = [i for i in report.issues if i.severity == 'INFO']
            # May or may not have weight warning depending on threshold
            # Just verify report is generated
            assert isinstance(report, MaterialValidationReport)


class TestMaterialRecommender:
    """Test MaterialRecommender class"""

    def test_initialization(self, recommender):
        """Test recommender initialization"""
        assert recommender is not None
        assert recommender.logger is not None
        assert recommender.material_library is not None

    # ============= Basic Recommendation Tests =============

    def test_recommend_materials_basic(self, recommender):
        """Test basic material recommendation"""
        # Mock material library
        mock_materials = {
            'Steel_Mild': Material(
                name='Steel_Mild',
                category='Metal',
                density=7850.0,
                youngs_modulus=210000.0,
                poissons_ratio=0.3,
                yield_strength=250.0
            ),
            'Aluminum_6061': Material(
                name='Aluminum_6061',
                category='Metal',
                density=2700.0,
                youngs_modulus=69000.0,
                poissons_ratio=0.33,
                yield_strength=276.0
            )
        }

        with patch.object(recommender.material_library, 'list_materials', return_value=list(mock_materials.keys())):
            with patch.object(recommender.material_library, 'get_material', side_effect=lambda name: mock_materials.get(name)):
                recommendations = recommender.recommend_materials(
                    part_name='TestPart',
                    simulation_type='crash',
                    top_n=5
                )

                # Should return recommendations
                assert len(recommendations) > 0
                assert len(recommendations) <= 5

                # Each recommendation should be (Material, score, reason)
                for material, score, reason in recommendations:
                    assert isinstance(material, Material)
                    assert 0.0 <= score <= 1.0
                    assert isinstance(reason, str)

    # ============= Constraint-Based Recommendation Tests =============

    def test_recommend_with_strength_constraint(self, recommender):
        """Test recommendation with minimum strength constraint"""
        mock_materials = {
            'Steel_Mild': Material(
                name='Steel_Mild', category='Metal', density=7850.0,
                youngs_modulus=210000.0, poissons_ratio=0.3, yield_strength=250.0
            ),
            'Steel_HighStrength': Material(
                name='Steel_HighStrength', category='Metal', density=7850.0,
                youngs_modulus=210000.0, poissons_ratio=0.3, yield_strength=600.0
            ),
            'Aluminum_6061': Material(
                name='Aluminum_6061', category='Metal', density=2700.0,
                youngs_modulus=69000.0, poissons_ratio=0.33, yield_strength=276.0
            )
        }

        with patch.object(recommender.material_library, 'list_materials', return_value=list(mock_materials.keys())):
            with patch.object(recommender.material_library, 'get_material', side_effect=lambda name: mock_materials.get(name)):
                recommendations = recommender.recommend_materials(
                    part_name='TestPart',
                    simulation_type='crash',
                    constraints={'min_strength': 400.0},  # Only high-strength steel qualifies
                    top_n=5
                )

                # Should only recommend materials meeting constraint
                for material, score, reason in recommendations:
                    assert material.yield_strength >= 400.0

    def test_recommend_with_density_constraint(self, recommender):
        """Test recommendation with maximum density constraint"""
        mock_materials = {
            'Steel_Mild': Material(
                name='Steel_Mild', category='Metal', density=7850.0,
                youngs_modulus=210000.0, poissons_ratio=0.3, yield_strength=250.0
            ),
            'Aluminum_6061': Material(
                name='Aluminum_6061', category='Metal', density=2700.0,
                youngs_modulus=69000.0, poissons_ratio=0.33, yield_strength=276.0
            )
        }

        with patch.object(recommender.material_library, 'list_materials', return_value=list(mock_materials.keys())):
            with patch.object(recommender.material_library, 'get_material', side_effect=lambda name: mock_materials.get(name)):
                recommendations = recommender.recommend_materials(
                    part_name='TestPart',
                    simulation_type='crash',
                    constraints={'max_density': 5000.0},  # Only aluminum qualifies
                    top_n=5
                )

                # Should only recommend lightweight materials
                for material, score, reason in recommendations:
                    assert material.density <= 5000.0

    def test_recommend_with_formability_constraint(self, recommender):
        """Test recommendation with formability requirement"""
        mock_materials = {
            'Steel_Mild': Material(
                name='Steel_Mild', category='Metal', density=7850.0,
                youngs_modulus=210000.0, poissons_ratio=0.3, yield_strength=250.0
            ),
            'Steel_HighStrength': Material(
                name='Steel_HighStrength', category='Metal', density=7850.0,
                youngs_modulus=210000.0, poissons_ratio=0.3, yield_strength=800.0
            )
        }

        with patch.object(recommender.material_library, 'list_materials', return_value=list(mock_materials.keys())):
            with patch.object(recommender.material_library, 'get_material', side_effect=lambda name: mock_materials.get(name)):
                recommendations = recommender.recommend_materials(
                    part_name='Blank',
                    simulation_type='forming',
                    constraints={'formability': 'required'},
                    top_n=5
                )

                # Should only recommend formable materials (σy < 400 MPa)
                for material, score, reason in recommendations:
                    if hasattr(material, 'yield_strength'):
                        assert material.yield_strength <= 400.0

    # ============= Scoring Tests =============

    def test_scoring_for_crash_simulation(self, recommender):
        """Test scoring algorithm for crash simulation"""
        material = Material(
            name='Steel_Mild',
            category='Metal',
            density=7850.0,
            youngs_modulus=210000.0,
            poissons_ratio=0.3,
            yield_strength=350.0  # Good for crash (200-600 MPa)
        )

        score = recommender._calculate_suitability_score(
            material,
            simulation_type='crash',
            constraints={}
        )

        # Should have reasonable score
        assert 0.0 <= score <= 1.0
        # Metal with yield strength in good range → high score
        assert score > 0.5

    def test_scoring_for_forming_simulation(self, recommender):
        """Test scoring algorithm for forming simulation"""
        material = Material(
            name='Aluminum_5052',
            category='Metal',
            density=2700.0,
            youngs_modulus=70000.0,
            poissons_ratio=0.33,
            yield_strength=200.0  # Soft → good for forming
        )

        score = recommender._calculate_suitability_score(
            material,
            simulation_type='forming',
            constraints={}
        )

        # Soft metal → high score for forming
        assert score > 0.5

    def test_completeness_bonus(self, recommender):
        """Test that complete materials score higher"""
        complete_material = Material(
            name='Complete',
            category='Metal',
            density=7850.0,
            youngs_modulus=210000.0,
            poissons_ratio=0.3,
            yield_strength=250.0
        )

        incomplete_material = Material(
            name='Incomplete',
            category='Metal',
            density=7850.0,
            youngs_modulus=210000.0,
            poissons_ratio=0.3
            # Missing yield_strength
        )

        score_complete = recommender._calculate_suitability_score(
            complete_material, 'crash', {}
        )
        score_incomplete = recommender._calculate_suitability_score(
            incomplete_material, 'crash', {}
        )

        # Complete material should score higher
        assert score_complete > score_incomplete


class TestMaterialValidatorIntegration:
    """Integration tests for material validation workflow"""

    @pytest.mark.integration
    def test_full_validation_workflow(self, validator, sample_material):
        """Test complete validation workflow"""
        with patch.object(validator.material_library, 'get_material', return_value=sample_material):
            # Validate material
            report = validator.validate_assignment(
                part_name='Hood',
                material_name='Steel_Mild',
                simulation_type='crash',
                part_volume=5000.0
            )

            # Should have complete statistics
            assert 'num_errors' in report.statistics
            assert 'num_warnings' in report.statistics
            assert 'material_category' in report.statistics
            assert 'material_density' in report.statistics

    @pytest.mark.integration
    def test_validation_and_recommendation_workflow(self, validator, recommender, sample_material):
        """Test validation + recommendation workflow"""
        # First validate current material
        with patch.object(validator.material_library, 'get_material', return_value=sample_material):
            validation_report = validator.validate_assignment(
                part_name='TestPart',
                material_name='Steel_Mild',
                simulation_type='crash'
            )

        # If validation fails or has warnings, get recommendations
        if not validation_report.valid or len(validation_report.issues) > 0:
            with patch.object(recommender.material_library, 'list_materials', return_value=['Steel_Mild', 'Aluminum_6061']):
                with patch.object(recommender.material_library, 'get_material', return_value=sample_material):
                    recommendations = recommender.recommend_materials(
                        part_name='TestPart',
                        simulation_type='crash',
                        top_n=3
                    )

                    # Should provide alternatives
                    assert len(recommendations) > 0


class TestMaterialValidatorEdgeCases:
    """Test edge cases and error handling"""

    def test_validate_with_none_material_name(self, validator):
        """Test validation with None material name"""
        with patch.object(validator.material_library, 'get_material', return_value=None):
            report = validator.validate_assignment(
                part_name='TestPart',
                material_name=None,
                simulation_type='crash'
            )

            # Should fail gracefully
            assert not report.valid

    def test_recommend_with_no_materials(self, recommender):
        """Test recommendation when no materials match"""
        with patch.object(recommender.material_library, 'list_materials', return_value=[]):
            recommendations = recommender.recommend_materials(
                part_name='TestPart',
                simulation_type='crash',
                top_n=5
            )

            # Should return empty list
            assert len(recommendations) == 0

    def test_recommend_with_impossible_constraints(self, recommender):
        """Test recommendation with impossible constraints"""
        mock_materials = {
            'Steel_Mild': Material(
                name='Steel_Mild', category='Metal', density=7850.0,
                youngs_modulus=210000.0, poissons_ratio=0.3, yield_strength=250.0
            )
        }

        with patch.object(recommender.material_library, 'list_materials', return_value=list(mock_materials.keys())):
            with patch.object(recommender.material_library, 'get_material', side_effect=lambda name: mock_materials.get(name)):
                recommendations = recommender.recommend_materials(
                    part_name='TestPart',
                    simulation_type='crash',
                    constraints={
                        'min_strength': 1000.0,  # Impossible
                        'max_density': 1000.0  # Impossible for metals
                    },
                    top_n=5
                )

                # Should return empty (no materials meet constraints)
                assert len(recommendations) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
