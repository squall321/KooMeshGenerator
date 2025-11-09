"""
Tests for Material Assignment

Tests automatic material assignment based on geometry, filenames, and templates.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch
from pathlib import Path

from koomesh.materials.material_assigner import (
    GeometryBasedMaterialAssigner,
    MaterialRuleEngine,
    AssignmentStrategy
)


@pytest.fixture
def assigner():
    """Create GeometryBasedMaterialAssigner instance"""
    return GeometryBasedMaterialAssigner()


@pytest.fixture
def sample_parts():
    """Create sample parts with geometry properties"""
    return [
        {
            'name': 'hood_outer.step',
            'thickness': 0.8,  # mm
            'volume': 5000.0,  # mm³
            'area': 6000.0  # mm²
        },
        {
            'name': 'pillar_a_left.step',
            'thickness': 2.5,
            'volume': 15000.0,
            'area': 6000.0
        },
        {
            'name': 'bumper_front.step',
            'thickness': 3.0,
            'volume': 8000.0,
            'area': 2666.0
        },
        {
            'name': 'unknown_part.step',
            'thickness': 1.5,
            'volume': 3000.0,
            'area': 2000.0
        }
    ]


class TestAssignmentStrategy:
    """Test AssignmentStrategy enum"""

    def test_strategies_exist(self):
        """Test that all strategies are defined"""
        assert AssignmentStrategy.FILENAME is not None
        assert AssignmentStrategy.GEOMETRY is not None
        assert AssignmentStrategy.TEMPLATE is not None
        assert AssignmentStrategy.DEFAULT is not None


class TestMaterialRuleEngine:
    """Test MaterialRuleEngine class"""

    def test_automotive_rules(self):
        """Test automotive industry rules"""
        rules = MaterialRuleEngine.get_automotive_rules()

        assert isinstance(rules, dict)
        assert len(rules) > 0

        # Check specific rules
        assert 'hood' in rules
        assert 'bumper' in rules
        assert 'pillar_a' in rules

    def test_aerospace_rules(self):
        """Test aerospace industry rules"""
        rules = MaterialRuleEngine.get_aerospace_rules()

        assert isinstance(rules, dict)
        assert len(rules) > 0

        # Check specific rules
        assert 'fuselage' in rules or 'wing' in rules or 'skin' in rules

    def test_forming_rules(self):
        """Test forming/stamping rules"""
        rules = MaterialRuleEngine.get_forming_rules()

        assert isinstance(rules, dict)
        assert len(rules) > 0

        # Should have blank/tool rules
        assert 'blank' in rules or 'die' in rules or 'punch' in rules

    def test_match_filename_exact(self):
        """Test exact filename matching"""
        rules = {'hood': 'Aluminum_5052'}

        match = MaterialRuleEngine.match_filename('hood_outer.step', rules)
        assert match == 'Aluminum_5052'

    def test_match_filename_partial(self):
        """Test partial filename matching"""
        rules = {
            'bumper': 'Plastic_PP',
            'pillar_a': 'Steel_UltraHighStrength'
        }

        match = MaterialRuleEngine.match_filename('front_bumper_assembly.step', rules)
        assert match == 'Plastic_PP'

        match = MaterialRuleEngine.match_filename('pillar_a_left.step', rules)
        assert match == 'Steel_UltraHighStrength'

    def test_match_filename_no_match(self):
        """Test filename matching with no match"""
        rules = {'hood': 'Aluminum_5052'}

        match = MaterialRuleEngine.match_filename('unknown_part.step', rules)
        assert match is None

    def test_match_filename_case_insensitive(self):
        """Test case-insensitive filename matching"""
        rules = {'hood': 'Aluminum_5052'}

        match = MaterialRuleEngine.match_filename('HOOD_OUTER.STEP', rules)
        assert match == 'Aluminum_5052'

        match = MaterialRuleEngine.match_filename('Hood_Outer.step', rules)
        assert match == 'Aluminum_5052'


class TestGeometryBasedMaterialAssigner:
    """Test GeometryBasedMaterialAssigner class"""

    def test_initialization(self, assigner):
        """Test assigner initialization"""
        assert assigner is not None
        assert assigner.logger is not None

    # ============= Filename-Based Assignment Tests =============

    def test_assign_by_filename(self, assigner):
        """Test assignment using filename patterns"""
        part = {
            'name': 'hood_outer.step',
            'thickness': 0.8,
            'volume': 5000.0,
            'area': 6000.0
        }

        material = assigner.assign_by_filename(
            part['name'],
            template='automotive'
        )

        # Hood should be assigned aluminum
        assert 'Aluminum' in material

    def test_assign_by_filename_bumper(self, assigner):
        """Test bumper assignment"""
        material = assigner.assign_by_filename(
            'front_bumper.step',
            template='automotive'
        )

        # Bumper should be plastic
        assert 'Plastic' in material

    def test_assign_by_filename_no_match(self, assigner):
        """Test filename with no match"""
        material = assigner.assign_by_filename(
            'unknown_part_xyz.step',
            template='automotive'
        )

        # Should return None (no match)
        assert material is None

    # ============= Geometry-Based Assignment Tests =============

    def test_assign_by_geometry_thin_sheet(self, assigner):
        """Test assignment for thin sheet metal"""
        material = assigner.assign_by_geometry(
            thickness=0.8,  # < 1.5mm → sheet metal
            volume=5000.0,
            area=6000.0
        )

        # Thin sheet → Aluminum or steel sheet
        assert material in ['Aluminum_5052', 'Steel_Mild']

    def test_assign_by_geometry_thick_structural(self, assigner):
        """Test assignment for thick structural parts"""
        material = assigner.assign_by_geometry(
            thickness=5.0,  # > 3mm → structural
            volume=50000.0,
            area=10000.0
        )

        # Thick structural → High-strength steel
        assert 'Steel' in material

    def test_assign_by_geometry_thin_large_area(self, assigner):
        """Test thin part with large area (sheet metal)"""
        material = assigner.assign_by_geometry(
            thickness=1.0,
            volume=100000.0,
            area=100000.0  # Large area/volume ratio
        )

        # Large thin sheet → Steel or aluminum
        assert material in ['Steel_Mild', 'Aluminum_5052', 'Aluminum_6061']

    def test_assign_by_geometry_bulk_part(self, assigner):
        """Test bulk/compact part"""
        material = assigner.assign_by_geometry(
            thickness=10.0,
            volume=100000.0,
            area=10000.0  # Compact
        )

        # Bulk part → Structural steel or cast iron
        assert 'Steel' in material or 'Iron' in material

    # ============= Template-Based Assignment Tests =============

    def test_assign_by_template_automotive(self, assigner, sample_parts):
        """Test automotive template assignment"""
        assignments = assigner.assign_by_template(
            sample_parts,
            template='automotive'
        )

        assert len(assignments) == len(sample_parts)

        # Check specific assignments
        hood = [a for a in assignments if 'hood' in a['part_name'].lower()][0]
        assert 'Aluminum' in hood['material']

        pillar = [a for a in assignments if 'pillar' in a['part_name'].lower()][0]
        assert 'Steel' in pillar['material']

    def test_assign_by_template_aerospace(self, assigner):
        """Test aerospace template assignment"""
        parts = [
            {'name': 'wing_skin.step', 'thickness': 2.0, 'volume': 10000.0, 'area': 5000.0},
            {'name': 'fuselage_frame.step', 'thickness': 5.0, 'volume': 20000.0, 'area': 4000.0}
        ]

        assignments = assigner.assign_by_template(parts, template='aerospace')

        # Aerospace parts should use aluminum or composites
        for assignment in assignments:
            material = assignment['material']
            assert 'Aluminum' in material or 'Titanium' in material or 'Composite' in material or 'Steel' in material

    def test_assign_by_template_forming(self, assigner):
        """Test forming/stamping template assignment"""
        parts = [
            {'name': 'blank.step', 'thickness': 1.0, 'volume': 5000.0, 'area': 5000.0},
            {'name': 'die_upper.step', 'thickness': 50.0, 'volume': 500000.0, 'area': 10000.0}
        ]

        assignments = assigner.assign_by_template(parts, template='forming')

        # Blank should be formable material
        blank = [a for a in assignments if 'blank' in a['part_name'].lower()][0]
        # Should be aluminum or mild steel
        assert 'Aluminum' in blank['material'] or 'Steel_Mild' in blank['material']

        # Die should be tool steel
        die = [a for a in assignments if 'die' in a['part_name'].lower()][0]
        assert 'Steel' in die['material']

    # ============= Multi-Strategy Assignment Tests =============

    def test_assign_with_fallback(self, assigner):
        """Test assignment with fallback strategy"""
        # Try filename first
        material = assigner.assign_material(
            part_name='hood_outer.step',
            thickness=0.8,
            volume=5000.0,
            area=6000.0,
            template='automotive',
            strategy=AssignmentStrategy.FILENAME
        )

        # Should match via filename
        assert 'Aluminum' in material

    def test_assign_with_geometry_fallback(self, assigner):
        """Test assignment falling back to geometry"""
        # Filename won't match, should use geometry
        material = assigner.assign_material(
            part_name='unknown_xyz.step',
            thickness=0.8,
            volume=5000.0,
            area=6000.0,
            template='automotive',
            strategy=AssignmentStrategy.FILENAME
        )

        # Should fall back to geometry
        # Thin sheet → aluminum or steel
        assert material is not None

    def test_assign_with_explicit_geometry_strategy(self, assigner):
        """Test assignment with explicit geometry strategy"""
        material = assigner.assign_material(
            part_name='any_name.step',
            thickness=2.5,
            volume=15000.0,
            area=6000.0,
            strategy=AssignmentStrategy.GEOMETRY
        )

        # Should use geometry only
        assert material is not None
        assert isinstance(material, str)

    # ============= Batch Assignment Tests =============

    def test_batch_assign(self, assigner, sample_parts):
        """Test batch assignment of multiple parts"""
        assignments = assigner.batch_assign(
            sample_parts,
            template='automotive',
            strategy=AssignmentStrategy.TEMPLATE
        )

        assert len(assignments) == len(sample_parts)

        # All should have materials assigned
        for assignment in assignments:
            assert 'part_name' in assignment
            assert 'material' in assignment
            assert 'strategy_used' in assignment
            assert assignment['material'] is not None

    def test_batch_assign_mixed_strategies(self, assigner, sample_parts):
        """Test batch assignment using mixed strategies"""
        # Should try filename first, fall back to geometry
        assignments = assigner.batch_assign(
            sample_parts,
            template='automotive',
            strategy=AssignmentStrategy.FILENAME
        )

        # Known parts should use filename
        hood = [a for a in assignments if 'hood' in a['part_name'].lower()][0]
        assert hood['strategy_used'] == AssignmentStrategy.FILENAME.value

        # Unknown parts should use geometry fallback
        unknown = [a for a in assignments if 'unknown' in a['part_name'].lower()][0]
        assert unknown['strategy_used'] in [
            AssignmentStrategy.GEOMETRY.value,
            AssignmentStrategy.DEFAULT.value
        ]


class TestGeometryAnalysis:
    """Test geometry analysis helpers"""

    def test_calculate_aspect_ratio(self, assigner):
        """Test aspect ratio calculation"""
        # Thin sheet: large area, small volume
        ratio = assigner._calculate_aspect_ratio(
            volume=1000.0,
            area=1000.0
        )

        # thickness ≈ volume/area = 1.0
        # For sheet, ratio should indicate thinness
        assert ratio > 0

    def test_classify_geometry_type(self, assigner):
        """Test geometry type classification"""
        # Thin sheet
        geo_type = assigner._classify_geometry_type(
            thickness=0.8,
            volume=5000.0,
            area=6000.0
        )
        assert geo_type == 'sheet'

        # Structural/thick
        geo_type = assigner._classify_geometry_type(
            thickness=5.0,
            volume=50000.0,
            area=10000.0
        )
        assert geo_type == 'structural'

        # Bulk/compact
        geo_type = assigner._classify_geometry_type(
            thickness=10.0,
            volume=100000.0,
            area=10000.0
        )
        assert geo_type == 'bulk'


class TestMaterialAssignerIntegration:
    """Integration tests for material assignment workflow"""

    @pytest.mark.integration
    def test_full_assignment_workflow(self, assigner):
        """Test complete assignment workflow"""
        parts = [
            {
                'name': 'hood_outer.step',
                'thickness': 0.8,
                'volume': 5000.0,
                'area': 6000.0
            },
            {
                'name': 'door_inner.step',
                'thickness': 1.2,
                'volume': 8000.0,
                'area': 6666.0
            }
        ]

        # Assign materials
        assignments = assigner.batch_assign(
            parts,
            template='automotive',
            strategy=AssignmentStrategy.TEMPLATE
        )

        # Verify all parts have materials
        assert len(assignments) == 2
        for assignment in assignments:
            assert assignment['material'] is not None
            assert assignment['strategy_used'] is not None

    @pytest.mark.integration
    def test_automotive_crash_scenario(self, assigner):
        """Test material assignment for automotive crash simulation"""
        crash_parts = [
            {'name': 'bumper_beam.step', 'thickness': 3.0, 'volume': 10000.0, 'area': 3333.0},
            {'name': 'hood.step', 'thickness': 0.8, 'volume': 5000.0, 'area': 6250.0},
            {'name': 'front_rail.step', 'thickness': 2.0, 'volume': 15000.0, 'area': 7500.0},
            {'name': 'pillar_a.step', 'thickness': 2.5, 'volume': 12000.0, 'area': 4800.0}
        ]

        assignments = assigner.batch_assign(
            crash_parts,
            template='automotive_crash',
            strategy=AssignmentStrategy.TEMPLATE
        )

        # Energy-absorbing parts should have appropriate materials
        # Bumper: high-strength steel or aluminum
        bumper = [a for a in assignments if 'bumper' in a['part_name'].lower()][0]
        assert 'Steel' in bumper['material'] or 'Aluminum' in bumper['material']

        # Structural parts: high-strength steel
        pillar = [a for a in assignments if 'pillar' in a['part_name'].lower()][0]
        assert 'Steel' in pillar['material']


class TestMaterialAssignerEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_parts_list(self, assigner):
        """Test with empty parts list"""
        assignments = assigner.batch_assign([], template='automotive')
        assert len(assignments) == 0

    def test_part_missing_properties(self, assigner):
        """Test with part missing geometry properties"""
        part = {'name': 'test.step'}  # No thickness/volume/area

        # Should handle gracefully (use filename only)
        material = assigner.assign_by_filename(part['name'], template='automotive')
        # May be None if no filename match
        assert material is None or isinstance(material, str)

    def test_invalid_template(self, assigner):
        """Test with invalid template name"""
        parts = [{'name': 'test.step', 'thickness': 1.0, 'volume': 1000.0, 'area': 1000.0}]

        # Should handle gracefully
        assignments = assigner.batch_assign(parts, template='invalid_template')

        # Should still return assignments (may use default)
        assert len(assignments) == len(parts)

    def test_zero_geometry_values(self, assigner):
        """Test with zero geometry values"""
        material = assigner.assign_by_geometry(
            thickness=0.0,
            volume=0.0,
            area=0.0
        )

        # Should handle gracefully
        assert material is None or isinstance(material, str)

    def test_negative_geometry_values(self, assigner):
        """Test with negative geometry values"""
        material = assigner.assign_by_geometry(
            thickness=-1.0,
            volume=-1000.0,
            area=-1000.0
        )

        # Should handle gracefully
        assert material is None or isinstance(material, str)

    def test_very_large_geometry_values(self, assigner):
        """Test with very large geometry values"""
        material = assigner.assign_by_geometry(
            thickness=1000.0,  # Very thick
            volume=1e10,  # Huge volume
            area=1e8
        )

        # Should still assign something
        assert material is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
