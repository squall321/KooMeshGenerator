"""Tests for STL Writer"""

import pytest
import tempfile
from pathlib import Path

from koomesh.meshing.mesh_data import MeshData, ElementType
from koomesh.export.stl_writer import STLWriter, export_to_stl, STLError


class TestSTLWriter:
    """Test STL writer functionality"""

    def test_basic_tet4_export(self):
        """Test basic TET4 export"""
        mesh = MeshData(element_type=ElementType.TET4)
        n1 = mesh.add_node(0.0, 0.0, 0.0)
        n2 = mesh.add_node(1.0, 0.0, 0.0)
        n3 = mesh.add_node(0.5, 1.0, 0.0)
        n4 = mesh.add_node(0.5, 0.5, 1.0)
        mesh.add_element([n1, n2, n3, n4])

        with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as f:
            filepath = f.name

        writer = STLWriter(filepath)
        writer.write_surface_mesh(mesh)

        assert Path(filepath).exists()
        with open(filepath, 'r') as f:
            content = f.read()
            assert "solid mesh" in content
            assert "facet normal" in content
            assert "vertex" in content
            assert "endsolid" in content

        Path(filepath).unlink()

    def test_hex8_export(self):
        """Test HEX8 export"""
        mesh = MeshData(element_type=ElementType.HEX8)
        node_ids = []
        for i in range(2):
            for j in range(2):
                for k in range(2):
                    node_ids.append(mesh.add_node(float(i), float(j), float(k)))
        mesh.add_element([node_ids[0], node_ids[1], node_ids[3], node_ids[2],
                         node_ids[4], node_ids[5], node_ids[7], node_ids[6]])

        with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as f:
            filepath = f.name

        writer = STLWriter(filepath)
        writer.write_surface_mesh(mesh, solid_name="cube")

        assert Path(filepath).exists()
        with open(filepath, 'r') as f:
            content = f.read()
            assert "solid cube" in content
            # HEX8 has 6 quad faces = 12 triangles
            assert content.count("facet normal") == 12

        Path(filepath).unlink()

    def test_empty_mesh_error(self):
        """Test error on empty mesh"""
        mesh = MeshData(element_type=ElementType.TET4)

        with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as f:
            filepath = f.name

        writer = STLWriter(filepath)
        with pytest.raises(STLError, match="empty mesh"):
            writer.write_surface_mesh(mesh)

        Path(filepath).unlink()

    def test_convenience_function(self):
        """Test convenience export function"""
        mesh = MeshData(element_type=ElementType.TET4)
        n1 = mesh.add_node(0.0, 0.0, 0.0)
        n2 = mesh.add_node(1.0, 0.0, 0.0)
        n3 = mesh.add_node(0.5, 1.0, 0.0)
        n4 = mesh.add_node(0.5, 0.5, 1.0)
        mesh.add_element([n1, n2, n3, n4])

        with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as f:
            filepath = f.name

        success = export_to_stl(mesh, filepath, solid_name="test")
        assert success
        assert Path(filepath).exists()

        Path(filepath).unlink()

    def test_prism6_export(self):
        """Test PRISM6 export"""
        mesh = MeshData(element_type=ElementType.PRISM6)
        n1 = mesh.add_node(0.0, 0.0, 0.0)
        n2 = mesh.add_node(1.0, 0.0, 0.0)
        n3 = mesh.add_node(0.5, 1.0, 0.0)
        n4 = mesh.add_node(0.0, 0.0, 1.0)
        n5 = mesh.add_node(1.0, 0.0, 1.0)
        n6 = mesh.add_node(0.5, 1.0, 1.0)
        mesh.add_element([n1, n2, n3, n4, n5, n6])

        with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as f:
            filepath = f.name

        writer = STLWriter(filepath)
        writer.write_surface_mesh(mesh)

        assert Path(filepath).exists()
        Path(filepath).unlink()

    def test_pyramid5_export(self):
        """Test PYRAMID5 export"""
        mesh = MeshData(element_type=ElementType.PYRAMID5)
        n1 = mesh.add_node(0.0, 0.0, 0.0)
        n2 = mesh.add_node(1.0, 0.0, 0.0)
        n3 = mesh.add_node(1.0, 1.0, 0.0)
        n4 = mesh.add_node(0.0, 1.0, 0.0)
        n5 = mesh.add_node(0.5, 0.5, 1.0)
        mesh.add_element([n1, n2, n3, n4, n5])

        with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as f:
            filepath = f.name

        writer = STLWriter(filepath)
        writer.write_surface_mesh(mesh)

        assert Path(filepath).exists()
        Path(filepath).unlink()
