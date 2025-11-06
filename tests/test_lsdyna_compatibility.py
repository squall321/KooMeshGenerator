"""
Tests for LS-DYNA Compatibility Checker ([012])
================================================

This module tests the LS-DYNA compatibility checking functionality including:
- Node ID validation
- Element ID validation
- Element type compatibility
- Node count validation
- Coordinate range validation
- ID renumbering
"""

import pytest
import numpy as np

from koomesh.meshing.mesh_data import MeshData, ElementType, Node, Element
from koomesh.export.lsdyna_compatibility import (
    LSDynaCompatibilityChecker,
    CompatibilityReport,
    MAX_NODE_ID,
    MAX_ELEMENT_ID,
    MIN_NODE_ID,
    MIN_ELEMENT_ID
)


@pytest.fixture
def valid_hex_mesh():
    """Create a valid hex mesh"""
    mesh = MeshData(element_type=ElementType.HEX8)

    coords = [
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [1.0, 1.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
        [1.0, 0.0, 1.0],
        [1.0, 1.0, 1.0],
        [0.0, 1.0, 1.0],
    ]

    node_ids = [mesh.add_node(x, y, z) for x, y, z in coords]
    mesh.add_element(node_ids)

    return mesh


@pytest.fixture
def mesh_with_invalid_node_ids():
    """Create mesh with invalid node IDs"""
    mesh = MeshData(element_type=ElementType.HEX8)

    # Add some valid nodes
    mesh.add_node(0.0, 0.0, 0.0)  # ID 1
    mesh.add_node(1.0, 0.0, 0.0)  # ID 2

    # Manually add node with invalid ID
    mesh.nodes[0] = Node(0, 2.0, 0.0, 0.0)  # ID 0 (below minimum)
    mesh.nodes[MAX_NODE_ID + 1] = Node(MAX_NODE_ID + 1, 3.0, 0.0, 0.0)  # Above maximum

    return mesh


@pytest.fixture
def mesh_with_invalid_element_ids():
    """Create mesh with invalid element IDs"""
    mesh = MeshData(element_type=ElementType.HEX8)

    coords = [
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [1.0, 1.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
        [1.0, 0.0, 1.0],
        [1.0, 1.0, 1.0],
        [0.0, 1.0, 1.0],
    ]

    node_ids = [mesh.add_node(x, y, z) for x, y, z in coords]

    # Add element with valid ID first
    mesh.add_element(node_ids)

    # Manually add elements with invalid IDs
    mesh.elements[0] = Element(0, ElementType.HEX8, node_ids)  # ID 0 (below minimum)
    mesh.elements[MAX_ELEMENT_ID + 1] = Element(MAX_ELEMENT_ID + 1, ElementType.HEX8, node_ids)

    return mesh


@pytest.fixture
def mesh_with_wrong_node_count():
    """Create mesh with wrong node count"""
    mesh = MeshData(element_type=ElementType.HEX8)

    # Add only 6 nodes instead of 8 for HEX8
    coords = [
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [1.0, 1.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
        [1.0, 0.0, 1.0],
    ]

    node_ids = [mesh.add_node(x, y, z) for x, y, z in coords]

    # Manually create element with wrong node count (bypass validation)
    elem = Element.__new__(Element)
    elem.id = 1
    elem.type = ElementType.HEX8
    elem.nodes = node_ids
    elem.metadata = {}
    mesh.elements[1] = elem

    return mesh


@pytest.fixture
def mesh_with_undefined_nodes():
    """Create mesh with undefined node references"""
    mesh = MeshData(element_type=ElementType.HEX8)

    coords = [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]]
    node_ids = [mesh.add_node(x, y, z) for x, y, z in coords]

    # Create element referencing non-existent nodes
    invalid_node_ids = node_ids + [999, 1000, 1001, 1002, 1003, 1004]
    mesh.elements[1] = Element(1, ElementType.HEX8, invalid_node_ids)

    return mesh


class TestCompatibilityChecker:
    """Test LSDynaCompatibilityChecker class"""

    def test_init(self):
        """Test checker initialization"""
        checker = LSDynaCompatibilityChecker()
        assert checker.max_node_id == MAX_NODE_ID
        assert checker.max_element_id == MAX_ELEMENT_ID
        assert checker.strict_mode == False

    def test_init_custom(self):
        """Test checker with custom settings"""
        checker = LSDynaCompatibilityChecker(
            max_node_id=1000000,
            max_element_id=1000000,
            strict_mode=True
        )
        assert checker.max_node_id == 1000000
        assert checker.max_element_id == 1000000
        assert checker.strict_mode == True


class TestValidMesh:
    """Test with valid mesh"""

    def test_valid_mesh_passes(self, valid_hex_mesh):
        """Test that valid mesh passes all checks"""
        checker = LSDynaCompatibilityChecker()
        report = checker.check_mesh(valid_hex_mesh)

        assert report.is_compatible == True
        assert report.is_valid() == True
        assert report.num_errors == 0
        assert len(report.issues) == 0

    def test_valid_mesh_statistics(self, valid_hex_mesh):
        """Test that statistics are correctly reported"""
        checker = LSDynaCompatibilityChecker()
        report = checker.check_mesh(valid_hex_mesh)

        assert report.node_stats['total'] == 8
        assert report.element_stats['total'] == 1
        assert report.node_stats['min_id'] >= MIN_NODE_ID
        assert report.element_stats['min_id'] >= MIN_ELEMENT_ID


class TestNodeIDValidation:
    """Test node ID validation"""

    def test_invalid_node_ids_detected(self, mesh_with_invalid_node_ids):
        """Test that invalid node IDs are detected"""
        checker = LSDynaCompatibilityChecker()
        report = checker.check_mesh(mesh_with_invalid_node_ids)

        assert report.is_compatible == False
        assert report.num_errors > 0

        # Should have errors for node ID 0 and MAX_NODE_ID+1
        node_id_errors = [i for i in report.issues if i.category == 'node_id']
        assert len(node_id_errors) >= 2

    def test_node_id_below_minimum(self):
        """Test detection of node ID below minimum"""
        mesh = MeshData(element_type=ElementType.HEX8)
        mesh.nodes[0] = Node(0, 0.0, 0.0, 0.0)

        checker = LSDynaCompatibilityChecker()
        report = checker.check_mesh(mesh)

        assert report.num_errors > 0
        assert any('below minimum' in i.message.lower() for i in report.issues)

    def test_node_id_above_maximum(self):
        """Test detection of node ID above maximum"""
        mesh = MeshData(element_type=ElementType.HEX8)
        mesh.nodes[MAX_NODE_ID + 1] = Node(MAX_NODE_ID + 1, 0.0, 0.0, 0.0)

        checker = LSDynaCompatibilityChecker()
        report = checker.check_mesh(mesh)

        assert report.num_errors > 0
        assert any('exceeds maximum' in i.message.lower() for i in report.issues)


class TestElementIDValidation:
    """Test element ID validation"""

    def test_invalid_element_ids_detected(self, mesh_with_invalid_element_ids):
        """Test that invalid element IDs are detected"""
        checker = LSDynaCompatibilityChecker()
        report = checker.check_mesh(mesh_with_invalid_element_ids)

        assert report.is_compatible == False
        assert report.num_errors > 0

        element_id_errors = [i for i in report.issues if i.category == 'element_id']
        assert len(element_id_errors) >= 2

    def test_element_id_below_minimum(self, valid_hex_mesh):
        """Test detection of element ID below minimum"""
        # Manually add element with ID 0
        node_ids = list(valid_hex_mesh.nodes.keys())
        valid_hex_mesh.elements[0] = Element(0, ElementType.HEX8, node_ids)

        checker = LSDynaCompatibilityChecker()
        report = checker.check_mesh(valid_hex_mesh)

        assert report.num_errors > 0
        assert any('below minimum' in i.message.lower() for i in report.issues)


class TestElementTypeValidation:
    """Test element type validation"""

    def test_wrong_node_count_detected(self, mesh_with_wrong_node_count):
        """Test that wrong node count is detected"""
        checker = LSDynaCompatibilityChecker()
        report = checker.check_mesh(mesh_with_wrong_node_count)

        assert report.is_compatible == False
        assert report.num_errors > 0

        node_count_errors = [i for i in report.issues if i.category == 'element_nodes']
        assert len(node_count_errors) > 0

    def test_undefined_nodes_detected(self, mesh_with_undefined_nodes):
        """Test that undefined node references are detected"""
        checker = LSDynaCompatibilityChecker()
        report = checker.check_mesh(mesh_with_undefined_nodes)

        assert report.is_compatible == False
        assert report.num_errors > 0

        undefined_errors = [i for i in report.issues if 'undefined' in i.message.lower()]
        assert len(undefined_errors) > 0


class TestCoordinateValidation:
    """Test coordinate range validation"""

    def test_extreme_coordinates_warning(self):
        """Test that extreme coordinates generate warnings"""
        mesh = MeshData(element_type=ElementType.HEX8)

        # Add node with extreme coordinate
        extreme_value = 1e16
        mesh.add_node(extreme_value, 0.0, 0.0)

        checker = LSDynaCompatibilityChecker()
        report = checker.check_mesh(mesh)

        # Should have warning (not error) for coordinate range
        assert report.num_warnings > 0
        coord_warnings = [i for i in report.issues if i.category == 'coordinate_range']
        assert len(coord_warnings) > 0


class TestReportFunctionality:
    """Test report functionality"""

    def test_report_summary(self, valid_hex_mesh):
        """Test report summary generation"""
        checker = LSDynaCompatibilityChecker()
        report = checker.check_mesh(valid_hex_mesh)

        summary = report.summary()
        assert isinstance(summary, str)
        assert 'LS-DYNA COMPATIBILITY REPORT' in summary
        assert 'COMPATIBLE' in summary

    def test_report_summary_with_errors(self, mesh_with_invalid_node_ids):
        """Test report summary with errors"""
        checker = LSDynaCompatibilityChecker()
        report = checker.check_mesh(mesh_with_invalid_node_ids)

        summary = report.summary()
        assert 'INCOMPATIBLE' in summary
        assert 'ERRORS:' in summary

    def test_report_add_issue(self):
        """Test adding issues to report"""
        report = CompatibilityReport()

        report.add_issue('error', 'test', 'Test error')
        assert report.num_errors == 1
        assert report.is_compatible == False

        report.add_issue('warning', 'test', 'Test warning')
        assert report.num_warnings == 1


class TestIDRenumbering:
    """Test ID renumbering functionality"""

    def test_fix_node_ids(self, valid_hex_mesh):
        """Test node ID renumbering"""
        checker = LSDynaCompatibilityChecker()

        # Original IDs
        original_ids = list(valid_hex_mesh.nodes.keys())

        # Renumber
        mapping = checker.fix_node_ids(valid_hex_mesh, start_id=100)

        # Check mapping
        assert len(mapping) == len(original_ids)
        assert all(new_id >= 100 for new_id in mapping.values())

        # Check sequential
        new_ids = sorted(valid_hex_mesh.nodes.keys())
        assert new_ids == list(range(100, 100 + len(original_ids)))

    def test_fix_element_ids(self, valid_hex_mesh):
        """Test element ID renumbering"""
        checker = LSDynaCompatibilityChecker()

        # Original IDs
        original_ids = list(valid_hex_mesh.elements.keys())

        # Renumber
        mapping = checker.fix_element_ids(valid_hex_mesh, start_id=1000)

        # Check mapping
        assert len(mapping) == len(original_ids)
        assert all(new_id >= 1000 for new_id in mapping.values())

        # Check sequential
        new_ids = sorted(valid_hex_mesh.elements.keys())
        assert new_ids == list(range(1000, 1000 + len(original_ids)))

    def test_fix_node_ids_updates_elements(self):
        """Test that fixing node IDs updates element references"""
        mesh = MeshData(element_type=ElementType.HEX8)

        coords = [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [1.0, 1.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [1.0, 0.0, 1.0],
            [1.0, 1.0, 1.0],
            [0.0, 1.0, 1.0],
        ]

        original_node_ids = [mesh.add_node(x, y, z) for x, y, z in coords]
        mesh.add_element(original_node_ids)

        checker = LSDynaCompatibilityChecker()
        mapping = checker.fix_node_ids(mesh, start_id=1)

        # Check that element references were updated
        elem = list(mesh.elements.values())[0]
        for node_id in elem.nodes:
            assert node_id in mesh.nodes


class TestMultipleIssues:
    """Test detection of multiple issues"""

    def test_multiple_issues_reported(self):
        """Test that multiple issues are all reported"""
        mesh = MeshData(element_type=ElementType.HEX8)

        # Add multiple issues:
        # 1. Invalid node ID (below minimum)
        mesh.nodes[0] = Node(0, 0.0, 0.0, 0.0)

        # 2. Invalid node ID (above maximum)
        mesh.nodes[MAX_NODE_ID + 1] = Node(MAX_NODE_ID + 1, 1.0, 0.0, 0.0)

        # 3. Invalid element with undefined nodes
        elem = Element.__new__(Element)
        elem.id = 1
        elem.type = ElementType.HEX8
        elem.nodes = [999, 1000, 1001, 1002, 1003, 1004, 1005, 1006]
        elem.metadata = {}
        mesh.elements[1] = elem

        checker = LSDynaCompatibilityChecker()
        report = checker.check_mesh(mesh)

        # Should have multiple errors
        assert report.num_errors >= 3
        assert len(report.issues) >= 3


class TestEdgeCases:
    """Test edge cases"""

    def test_empty_mesh(self):
        """Test checker with empty mesh"""
        mesh = MeshData(element_type=ElementType.HEX8)

        checker = LSDynaCompatibilityChecker()
        report = checker.check_mesh(mesh)

        # Empty mesh should be compatible (no violations)
        assert report.is_compatible == True
        assert report.num_errors == 0

    def test_mesh_with_only_nodes(self):
        """Test mesh with only nodes, no elements"""
        mesh = MeshData(element_type=ElementType.HEX8)
        mesh.add_node(0.0, 0.0, 0.0)
        mesh.add_node(1.0, 0.0, 0.0)

        checker = LSDynaCompatibilityChecker()
        report = checker.check_mesh(mesh)

        assert report.is_compatible == True
        assert report.node_stats['total'] == 2
        assert report.element_stats['total'] == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
