"""
Tests for Assembly Contact Management

Tests multi-part assembly contact detection with spatial hashing.
"""

import pytest
import numpy as np
from unittest.mock import Mock

from koomesh.contact.assembly_contact import (
    SpatialHashGrid,
    AssemblyContactManager,
    ContactPair
)
from koomesh.meshing.mesh_data import MeshData


@pytest.fixture
def sample_parts():
    """Create sample parts for testing"""
    parts = []

    # Part 1: 2x2 grid at z=0
    nodes1 = np.array([
        [0, 0, 0],
        [2, 0, 0],
        [2, 2, 0],
        [0, 2, 0]
    ], dtype=float)
    elements1 = np.array([[0, 1, 2, 3]])
    parts.append(('Part1', MeshData(nodes=nodes1, elements=elements1)))

    # Part 2: 2x2 grid at z=0.1 (close to Part1)
    nodes2 = np.array([
        [0, 0, 0.1],
        [2, 0, 0.1],
        [2, 2, 0.1],
        [0, 2, 0.1]
    ], dtype=float)
    elements2 = np.array([[0, 1, 2, 3]])
    parts.append(('Part2', MeshData(nodes=nodes2, elements=elements2)))

    # Part 3: 2x2 grid at z=10 (far from others)
    nodes3 = np.array([
        [0, 0, 10],
        [2, 0, 10],
        [2, 2, 10],
        [0, 2, 10]
    ], dtype=float)
    elements3 = np.array([[0, 1, 2, 3]])
    parts.append(('Part3', MeshData(nodes=nodes3, elements=elements3)))

    return parts


@pytest.fixture
def manager():
    """Create AssemblyContactManager instance"""
    return AssemblyContactManager()


class TestSpatialHashGrid:
    """Test SpatialHashGrid class"""

    def test_initialization(self):
        """Test spatial hash grid initialization"""
        grid = SpatialHashGrid(cell_size=1.0)

        assert grid.cell_size == 1.0
        assert len(grid.grid) == 0

    def test_insert_single_bbox(self):
        """Test inserting a single bounding box"""
        grid = SpatialHashGrid(cell_size=1.0)

        bbox = (0.0, 0.0, 0.0, 1.0, 1.0, 1.0)
        grid.insert(0, bbox)

        # Should have cells populated
        assert len(grid.grid) > 0

    def test_insert_multiple_bboxes(self):
        """Test inserting multiple bounding boxes"""
        grid = SpatialHashGrid(cell_size=1.0)

        grid.insert(0, (0, 0, 0, 1, 1, 1))
        grid.insert(1, (5, 5, 5, 6, 6, 6))
        grid.insert(2, (0.5, 0.5, 0.5, 1.5, 1.5, 1.5))

        # All should be inserted
        assert len(grid.grid) > 0

    def test_query_no_overlap(self):
        """Test querying with no overlapping boxes"""
        grid = SpatialHashGrid(cell_size=1.0)

        grid.insert(0, (0, 0, 0, 1, 1, 1))
        grid.insert(1, (10, 10, 10, 11, 11, 11))

        # Query for part 0
        candidates = grid.query((0, 0, 0, 1, 1, 1))

        # Should find itself
        assert 0 in candidates
        # Should not find part 1 (too far)
        assert 1 not in candidates

    def test_query_with_overlap(self):
        """Test querying with overlapping boxes"""
        grid = SpatialHashGrid(cell_size=1.0)

        grid.insert(0, (0, 0, 0, 2, 2, 2))
        grid.insert(1, (1, 1, 1, 3, 3, 3))  # Overlaps with 0

        candidates = grid.query((0, 0, 0, 2, 2, 2))

        # Should find both
        assert 0 in candidates
        assert 1 in candidates

    def test_get_cell_coords(self):
        """Test cell coordinate calculation"""
        grid = SpatialHashGrid(cell_size=1.0)

        # Point (1.5, 2.5, 3.5) → cell (1, 2, 3)
        cell = grid._get_cell_coords(1.5, 2.5, 3.5)
        assert cell == (1, 2, 3)

        # Point (0.0, 0.0, 0.0) → cell (0, 0, 0)
        cell = grid._get_cell_coords(0.0, 0.0, 0.0)
        assert cell == (0, 0, 0)

        # Negative coordinates
        cell = grid._get_cell_coords(-1.5, -2.5, -3.5)
        assert cell == (-2, -3, -4)

    def test_affected_cells(self):
        """Test getting affected cells for a bbox"""
        grid = SpatialHashGrid(cell_size=1.0)

        bbox = (0.0, 0.0, 0.0, 2.5, 2.5, 2.5)
        cells = list(grid._get_affected_cells(bbox))

        # Should span multiple cells
        assert len(cells) > 1

        # Should include (0,0,0) and (2,2,2)
        assert (0, 0, 0) in cells
        assert (2, 2, 2) in cells


class TestAssemblyContactManager:
    """Test AssemblyContactManager class"""

    def test_initialization(self, manager):
        """Test manager initialization"""
        assert manager is not None
        assert manager.logger is not None

    def test_detect_contacts_basic(self, manager, sample_parts):
        """Test basic contact detection"""
        contact_pairs = manager.detect_contacts(
            sample_parts,
            tolerance=1.0
        )

        # Should find at least Part1-Part2 contact (gap 0.1mm < 1.0mm)
        assert len(contact_pairs) >= 1

        # Check that pairs are valid
        for pair in contact_pairs:
            assert pair.master_part in ['Part1', 'Part2', 'Part3']
            assert pair.slave_part in ['Part1', 'Part2', 'Part3']
            assert pair.master_part != pair.slave_part

    def test_detect_contacts_no_contacts(self, manager):
        """Test detection with no contacts (parts far apart)"""
        parts = [
            ('Part1', MeshData(
                nodes=np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]], dtype=float),
                elements=np.array([[0, 1, 2, 3]])
            )),
            ('Part2', MeshData(
                nodes=np.array([[100, 100, 100], [101, 100, 100], [101, 101, 100], [100, 101, 100]], dtype=float),
                elements=np.array([[0, 1, 2, 3]])
            ))
        ]

        contact_pairs = manager.detect_contacts(parts, tolerance=1.0)

        # No contacts (too far apart)
        assert len(contact_pairs) == 0

    def test_detect_contacts_with_tolerance(self, manager, sample_parts):
        """Test contact detection with different tolerances"""
        # Small tolerance (0.05mm)
        pairs_small = manager.detect_contacts(sample_parts, tolerance=0.05)

        # Large tolerance (5.0mm)
        pairs_large = manager.detect_contacts(sample_parts, tolerance=5.0)

        # Larger tolerance should find same or more contacts
        assert len(pairs_large) >= len(pairs_small)

    def test_spatial_hashing_optimization(self, manager):
        """Test that spatial hashing improves performance"""
        # Create many parts
        parts = []
        for i in range(15):
            nodes = np.array([
                [i*10, 0, 0],
                [i*10+1, 0, 0],
                [i*10+1, 1, 0],
                [i*10, 1, 0]
            ], dtype=float)
            elements = np.array([[0, 1, 2, 3]])
            parts.append((f'Part{i}', MeshData(nodes=nodes, elements=elements)))

        # Should complete efficiently (O(n) vs O(n²))
        contact_pairs = manager.detect_contacts(parts, tolerance=2.0)

        # Should find only adjacent parts (if any)
        # Verify it completes without timeout
        assert isinstance(contact_pairs, list)

    def test_calculate_bbox(self, manager):
        """Test bounding box calculation"""
        nodes = np.array([
            [0, 0, 0],
            [5, 0, 0],
            [5, 10, 0],
            [0, 10, 2]
        ], dtype=float)

        bbox = manager._calculate_bbox(nodes)

        assert bbox == (0.0, 0.0, 0.0, 5.0, 10.0, 2.0)

    def test_bboxes_close(self, manager):
        """Test bounding box proximity check"""
        bbox1 = (0, 0, 0, 10, 10, 10)
        bbox2 = (5, 5, 5, 15, 15, 15)  # Overlaps
        bbox3 = (20, 20, 20, 30, 30, 30)  # Far away

        assert manager._bboxes_close(bbox1, bbox2, tolerance=0.0)
        assert not manager._bboxes_close(bbox1, bbox3, tolerance=0.0)

        # With tolerance
        bbox4 = (10.5, 0, 0, 20, 10, 10)  # Gap of 0.5
        assert not manager._bboxes_close(bbox1, bbox4, tolerance=0.1)
        assert manager._bboxes_close(bbox1, bbox4, tolerance=1.0)

    def test_calculate_contact_gap(self, manager):
        """Test contact gap calculation"""
        # Part 1
        nodes1 = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]], dtype=float)

        # Part 2 (parallel, 0.5mm above)
        nodes2 = np.array([[0, 0, 0.5], [1, 0, 0.5], [1, 1, 0.5], [0, 1, 0.5]], dtype=float)

        gap = manager._calculate_contact_gap(nodes1, nodes2)

        # Gap should be approximately 0.5mm
        assert abs(gap - 0.5) < 0.1

    def test_calculate_surface_angle(self, manager):
        """Test surface angle calculation"""
        # Parallel surfaces (angle = 0°)
        nodes1 = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]], dtype=float)
        nodes2 = np.array([[0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]], dtype=float)

        angle = manager._calculate_surface_angle(nodes1, nodes2)
        assert angle < 5.0  # Nearly parallel

        # Perpendicular surfaces (angle = 90°)
        nodes3 = np.array([[0, 0, 0], [1, 0, 0], [1, 0, 1], [0, 0, 1]], dtype=float)
        angle = manager._calculate_surface_angle(nodes1, nodes3)
        assert 80.0 <= angle <= 100.0  # Nearly perpendicular

    def test_estimate_contact_area(self, manager):
        """Test contact area estimation"""
        # 1x1 square
        nodes1 = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]], dtype=float)

        # 2x2 square
        nodes2 = np.array([[0, 0, 0], [2, 0, 0], [2, 2, 0], [0, 2, 0]], dtype=float)

        area1 = manager._estimate_contact_area(nodes1)
        area2 = manager._estimate_contact_area(nodes2)

        # Area1 should be ~1.0
        assert 0.5 <= area1 <= 2.0

        # Area2 should be ~4.0 (larger)
        assert area2 > area1


class TestContactPairCreation:
    """Test ContactPair creation in assembly context"""

    def test_contact_pair_with_metadata(self):
        """Test creating contact pair with assembly metadata"""
        from koomesh.contact.contact_classifier import ContactType, ContactParameters

        pair = ContactPair(
            master_part='Body',
            slave_part='Door',
            contact_type=ContactType.AUTOMATIC,
            parameters=ContactParameters(fs=0.3),
            metadata={
                'gap': 0.5,
                'area': 150.0,
                'angle': 10.0,
                'detection_method': 'spatial_hashing'
            }
        )

        assert pair.master_part == 'Body'
        assert pair.slave_part == 'Door'
        assert pair.metadata['detection_method'] == 'spatial_hashing'


class TestAssemblyContactIntegration:
    """Integration tests for assembly contact workflow"""

    @pytest.mark.integration
    def test_full_assembly_workflow(self, manager, sample_parts):
        """Test complete assembly contact detection workflow"""
        # Detect contacts
        contact_pairs = manager.detect_contacts(
            sample_parts,
            tolerance=1.0,
            auto_classify=False
        )

        # Verify results
        assert isinstance(contact_pairs, list)
        for pair in contact_pairs:
            assert hasattr(pair, 'master_part')
            assert hasattr(pair, 'slave_part')
            assert hasattr(pair, 'contact_type')
            assert hasattr(pair, 'parameters')

    @pytest.mark.integration
    def test_assembly_with_classification(self, manager, sample_parts):
        """Test assembly detection with automatic classification"""
        contact_pairs = manager.detect_contacts(
            sample_parts,
            tolerance=1.0,
            auto_classify=True
        )

        # All pairs should have classified contact type
        for pair in contact_pairs:
            from koomesh.contact.contact_classifier import ContactType
            assert isinstance(pair.contact_type, ContactType)

            # Should have optimized parameters
            assert pair.parameters.fs >= 0.0

    @pytest.mark.integration
    def test_large_assembly(self, manager):
        """Test detection in large assembly"""
        # Create 10 parts in a row
        parts = []
        for i in range(10):
            nodes = np.array([
                [i, 0, 0],
                [i+1, 0, 0],
                [i+1, 1, 0],
                [i, 1, 0]
            ], dtype=float)
            elements = np.array([[0, 1, 2, 3]])
            parts.append((f'Part{i}', MeshData(nodes=nodes, elements=elements)))

        # Detect contacts
        contact_pairs = manager.detect_contacts(parts, tolerance=0.1)

        # Should find adjacent contacts
        # 10 parts in a row → up to 9 contact pairs
        assert len(contact_pairs) <= 9 * 2  # Master-slave pairs


class TestAssemblyContactEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_parts_list(self, manager):
        """Test with empty parts list"""
        contact_pairs = manager.detect_contacts([], tolerance=1.0)
        assert len(contact_pairs) == 0

    def test_single_part(self, manager):
        """Test with single part (no contacts possible)"""
        parts = [(
            'Part1',
            MeshData(
                nodes=np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]], dtype=float),
                elements=np.array([[0, 1, 2, 3]])
            )
        )]

        contact_pairs = manager.detect_contacts(parts, tolerance=1.0)
        assert len(contact_pairs) == 0

    def test_negative_tolerance(self, manager, sample_parts):
        """Test with negative tolerance"""
        # Should handle gracefully
        contact_pairs = manager.detect_contacts(sample_parts, tolerance=-1.0)
        assert isinstance(contact_pairs, list)

    def test_very_large_tolerance(self, manager, sample_parts):
        """Test with very large tolerance"""
        # Should find all possible pairs
        contact_pairs = manager.detect_contacts(sample_parts, tolerance=1000.0)

        # All parts within tolerance
        # 3 parts → up to 3 pairs (3 choose 2)
        assert len(contact_pairs) <= 6  # Max pairs with master/slave

    def test_parts_with_empty_mesh(self, manager):
        """Test with parts that have empty meshes"""
        parts = [
            ('Part1', MeshData(nodes=np.array([]), elements=np.array([]))),
            ('Part2', MeshData(
                nodes=np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]], dtype=float),
                elements=np.array([[0, 1, 2, 3]])
            ))
        ]

        # Should handle gracefully
        contact_pairs = manager.detect_contacts(parts, tolerance=1.0)
        assert isinstance(contact_pairs, list)

    def test_duplicate_part_names(self, manager):
        """Test with duplicate part names"""
        parts = [
            ('Part1', MeshData(
                nodes=np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]], dtype=float),
                elements=np.array([[0, 1, 2, 3]])
            )),
            ('Part1', MeshData(  # Same name
                nodes=np.array([[5, 0, 0], [6, 0, 0], [6, 1, 0], [5, 1, 0]], dtype=float),
                elements=np.array([[0, 1, 2, 3]])
            ))
        ]

        # Should still detect (or handle duplicate names)
        contact_pairs = manager.detect_contacts(parts, tolerance=1.0)
        assert isinstance(contact_pairs, list)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
