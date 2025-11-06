"""
Tests for Mesh Repair Utilities

Author: KooMeshGenerator Team
"""

import pytest
from koomesh.meshing.mesh_data import MeshData, ElementType
from koomesh.utils.mesh_repair import MeshRepair, repair_mesh


@pytest.fixture
def mesh_with_duplicates():
    """Mesh with duplicate nodes"""
    mesh = MeshData(element_type=ElementType.TET4)

    # Add nodes, including duplicates
    n1 = mesh.add_node(0.0, 0.0, 0.0)
    n2 = mesh.add_node(1.0, 0.0, 0.0)
    n3 = mesh.add_node(0.0, 1.0, 0.0)
    n4 = mesh.add_node(0.0, 0.0, 1.0)
    n5 = mesh.add_node(0.0, 0.0, 0.0)  # Duplicate of n1
    n6 = mesh.add_node(1.0, 0.0, 0.0)  # Duplicate of n2

    mesh.add_element([n1, n2, n3, n4])
    mesh.add_element([n5, n6, n3, n4])  # Uses duplicate nodes

    return mesh


@pytest.fixture
def mesh_with_degenerate():
    """Mesh with degenerate element"""
    mesh = MeshData(element_type=ElementType.TET4)

    n1 = mesh.add_node(0.0, 0.0, 0.0)
    n2 = mesh.add_node(1.0, 0.0, 0.0)
    n3 = mesh.add_node(0.0, 1.0, 0.0)
    n4 = mesh.add_node(0.0, 0.0, 1.0)

    mesh.add_element([n1, n2, n3, n4])  # Good
    mesh.add_element([n1, n1, n2, n3])  # Degenerate (n1 repeated)

    return mesh


@pytest.fixture
def mesh_with_unused_nodes():
    """Mesh with unused nodes"""
    mesh = MeshData(element_type=ElementType.TET4)

    n1 = mesh.add_node(0.0, 0.0, 0.0)
    n2 = mesh.add_node(1.0, 0.0, 0.0)
    n3 = mesh.add_node(0.0, 1.0, 0.0)
    n4 = mesh.add_node(0.0, 0.0, 1.0)
    n5 = mesh.add_node(5.0, 5.0, 5.0)  # Unused
    n6 = mesh.add_node(6.0, 6.0, 6.0)  # Unused

    mesh.add_element([n1, n2, n3, n4])

    return mesh


class TestRemoveDuplicateNodes:
    """Test duplicate node removal"""

    def test_remove_duplicates(self, mesh_with_duplicates):
        """Test that duplicate nodes are removed"""
        original_count = len(mesh_with_duplicates.nodes)

        repair = MeshRepair(mesh_with_duplicates)
        count = repair.remove_duplicate_nodes()

        assert count == 2  # Two duplicates
        assert len(mesh_with_duplicates.nodes) == original_count - 2

    def test_no_duplicates(self):
        """Test mesh with no duplicates"""
        mesh = MeshData(element_type=ElementType.TET4)
        n1 = mesh.add_node(0.0, 0.0, 0.0)
        n2 = mesh.add_node(1.0, 0.0, 0.0)
        n3 = mesh.add_node(0.0, 1.0, 0.0)
        n4 = mesh.add_node(0.0, 0.0, 1.0)
        mesh.add_element([n1, n2, n3, n4])

        repair = MeshRepair(mesh)
        count = repair.remove_duplicate_nodes()

        assert count == 0

    def test_tolerance(self):
        """Test tolerance parameter"""
        mesh = MeshData(element_type=ElementType.TET4)
        n1 = mesh.add_node(0.0, 0.0, 0.0)
        n2 = mesh.add_node(1e-7, 0.0, 0.0)  # Very close
        n3 = mesh.add_node(0.0, 1.0, 0.0)
        n4 = mesh.add_node(0.0, 0.0, 1.0)
        mesh.add_element([n1, n2, n3, n4])

        repair = MeshRepair(mesh)
        count = repair.remove_duplicate_nodes(tolerance=1e-6)

        assert count == 1  # Should merge with larger tolerance


class TestRemoveDegenerateElements:
    """Test degenerate element removal"""

    def test_remove_degenerate(self, mesh_with_degenerate):
        """Test that degenerate elements are removed"""
        original_count = len(mesh_with_degenerate.elements)

        repair = MeshRepair(mesh_with_degenerate)
        count = repair.remove_degenerate_elements()

        assert count == 1
        assert len(mesh_with_degenerate.elements) == original_count - 1

    def test_no_degenerate(self):
        """Test mesh with no degenerate elements"""
        mesh = MeshData(element_type=ElementType.TET4)
        n1 = mesh.add_node(0.0, 0.0, 0.0)
        n2 = mesh.add_node(1.0, 0.0, 0.0)
        n3 = mesh.add_node(0.0, 1.0, 0.0)
        n4 = mesh.add_node(0.0, 0.0, 1.0)
        mesh.add_element([n1, n2, n3, n4])

        repair = MeshRepair(mesh)
        count = repair.remove_degenerate_elements()

        assert count == 0


class TestRemoveUnusedNodes:
    """Test unused node removal"""

    def test_remove_unused(self, mesh_with_unused_nodes):
        """Test that unused nodes are removed"""
        repair = MeshRepair(mesh_with_unused_nodes)
        count = repair.remove_unused_nodes()

        assert count == 2  # Two unused nodes
        assert len(mesh_with_unused_nodes.nodes) == 4

    def test_all_nodes_used(self):
        """Test mesh where all nodes are used"""
        mesh = MeshData(element_type=ElementType.TET4)
        n1 = mesh.add_node(0.0, 0.0, 0.0)
        n2 = mesh.add_node(1.0, 0.0, 0.0)
        n3 = mesh.add_node(0.0, 1.0, 0.0)
        n4 = mesh.add_node(0.0, 0.0, 1.0)
        mesh.add_element([n1, n2, n3, n4])

        repair = MeshRepair(mesh)
        count = repair.remove_unused_nodes()

        assert count == 0


class TestRepairAll:
    """Test comprehensive repair"""

    def test_repair_all_counts(self):
        """Test that repair_all returns correct counts"""
        mesh = MeshData(element_type=ElementType.TET4)

        # Add duplicates
        n1 = mesh.add_node(0.0, 0.0, 0.0)
        n2 = mesh.add_node(1.0, 0.0, 0.0)
        n3 = mesh.add_node(0.0, 1.0, 0.0)
        n4 = mesh.add_node(0.0, 0.0, 1.0)
        n5 = mesh.add_node(0.0, 0.0, 0.0)  # Duplicate
        n6 = mesh.add_node(5.0, 5.0, 5.0)  # Unused

        mesh.add_element([n1, n2, n3, n4])
        mesh.add_element([n1, n1, n2, n3])  # Degenerate

        repair = MeshRepair(mesh)
        results = repair.repair_all()

        assert results['duplicate_nodes'] == 1
        assert results['degenerate_elements'] == 1
        assert results['unused_nodes'] == 1
        assert results['total'] > 0

    def test_clean_mesh(self):
        """Test repair_all on clean mesh"""
        mesh = MeshData(element_type=ElementType.TET4)
        n1 = mesh.add_node(0.0, 0.0, 0.0)
        n2 = mesh.add_node(1.0, 0.0, 0.0)
        n3 = mesh.add_node(0.0, 1.0, 0.0)
        n4 = mesh.add_node(0.0, 0.0, 1.0)
        mesh.add_element([n1, n2, n3, n4])

        repair = MeshRepair(mesh)
        results = repair.repair_all()

        assert results['total'] == 0


class TestConvenienceFunction:
    """Test convenience function"""

    def test_repair_mesh_function(self, mesh_with_duplicates, capsys):
        """Test repair_mesh convenience function"""
        results = repair_mesh(mesh_with_duplicates, tolerance=1e-10)

        assert isinstance(results, dict)
        assert 'total' in results

        # Should print report
        captured = capsys.readouterr()
        assert len(captured.out) > 0


class TestGenerateReport:
    """Test report generation"""

    def test_report_with_repairs(self, mesh_with_duplicates):
        """Test report generation after repairs"""
        repair = MeshRepair(mesh_with_duplicates)
        repair.remove_duplicate_nodes()

        report = repair.generate_report()

        assert isinstance(report, str)
        assert "duplicate" in report.lower()

    def test_report_no_repairs(self):
        """Test report when no repairs needed"""
        mesh = MeshData(element_type=ElementType.TET4)
        repair = MeshRepair(mesh)

        report = repair.generate_report()

        assert "clean" in report.lower()
