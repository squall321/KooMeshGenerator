"""
Test Suite for CalculiX Writer
===============================

Comprehensive tests for CalculiX INP format export.

Author: KooMeshGenerator Team
License: MIT
"""

import pytest
import tempfile
from pathlib import Path

from koomesh.meshing.mesh_data import MeshData, ElementType
from koomesh.export.calculix_writer import (
    CalculixWriter,
    CalculixError,
    export_to_calculix
)


@pytest.fixture
def temp_inp_file():
    """Create temporary INP file path"""
    with tempfile.NamedTemporaryFile(suffix='.inp', delete=False) as f:
        temp_path = f.name
    yield temp_path
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def simple_hex_mesh():
    """Create simple HEX8 mesh"""
    mesh = MeshData(element_type=ElementType.HEX8)
    for i in range(2):
        for j in range(2):
            for k in range(2):
                node_id = i * 4 + j * 2 + k + 1
                mesh.add_node(float(i), float(j), float(k), node_id=node_id)
    mesh.add_element([1, 3, 7, 5, 2, 4, 8, 6], element_id=1)
    return mesh


class TestBasicFunctionality:
    """Test basic functionality"""

    def test_writer_initialization(self, temp_inp_file):
        """Test writer initialization"""
        writer = CalculixWriter(temp_inp_file)
        assert writer.filepath == Path(temp_inp_file)

    def test_context_manager(self, temp_inp_file, simple_hex_mesh):
        """Test context manager"""
        with CalculixWriter(temp_inp_file) as writer:
            writer.write_mesh(simple_hex_mesh)
        assert Path(temp_inp_file).exists()

    def test_convenience_function(self, temp_inp_file, simple_hex_mesh):
        """Test convenience function"""
        success = export_to_calculix(simple_hex_mesh, temp_inp_file)
        assert success is True

    def test_header_written(self, temp_inp_file, simple_hex_mesh):
        """Test header is written"""
        with CalculixWriter(temp_inp_file, title="Test") as writer:
            writer.write_mesh(simple_hex_mesh)
        
        content = Path(temp_inp_file).read_text()
        assert "*HEADING" in content
        assert "Test" in content


class TestMeshWriting:
    """Test mesh writing"""

    def test_nodes_written(self, temp_inp_file, simple_hex_mesh):
        """Test nodes are written"""
        with CalculixWriter(temp_inp_file) as writer:
            writer.write_mesh(simple_hex_mesh)
        
        content = Path(temp_inp_file).read_text()
        assert "*NODE" in content
        assert "1," in content  # Node 1

    def test_elements_written(self, temp_inp_file, simple_hex_mesh):
        """Test elements are written"""
        with CalculixWriter(temp_inp_file) as writer:
            writer.write_mesh(simple_hex_mesh)
        
        content = Path(temp_inp_file).read_text()
        assert "*ELEMENT" in content
        assert "C3D8" in content  # HEX8 element type

    def test_elsets_written(self, temp_inp_file, simple_hex_mesh):
        """Test element sets are written"""
        elsets = {"Part1": [1]}
        with CalculixWriter(temp_inp_file) as writer:
            writer.write_mesh(simple_hex_mesh, elsets=elsets)
        
        content = Path(temp_inp_file).read_text()
        assert "*ELSET" in content
        assert "Part1" in content

    def test_nsets_written(self, temp_inp_file, simple_hex_mesh):
        """Test node sets are written"""
        nsets = {"Fixed": [1, 2, 3, 4]}
        with CalculixWriter(temp_inp_file) as writer:
            writer.write_mesh(simple_hex_mesh, nsets=nsets)
        
        content = Path(temp_inp_file).read_text()
        assert "*NSET" in content
        assert "Fixed" in content


class TestElementTypes:
    """Test different element types"""

    def test_hex8_export(self, temp_inp_file):
        """Test HEX8 export"""
        mesh = MeshData(element_type=ElementType.HEX8)
        for i in range(2):
            for j in range(2):
                for k in range(2):
                    mesh.add_node(float(i), float(j), float(k), node_id=i*4+j*2+k+1)
        mesh.add_element([1, 3, 7, 5, 2, 4, 8, 6], element_id=1)
        
        with CalculixWriter(temp_inp_file) as writer:
            writer.write_mesh(mesh)
        
        content = Path(temp_inp_file).read_text()
        assert "C3D8" in content

    def test_tet4_export(self, temp_inp_file):
        """Test TET4 export"""
        mesh = MeshData(element_type=ElementType.TET4)
        mesh.add_node(0.0, 0.0, 0.0, node_id=1)
        mesh.add_node(1.0, 0.0, 0.0, node_id=2)
        mesh.add_node(0.5, 1.0, 0.0, node_id=3)
        mesh.add_node(0.5, 0.5, 1.0, node_id=4)
        mesh.add_element([1, 2, 3, 4], element_id=1)
        
        with CalculixWriter(temp_inp_file) as writer:
            writer.write_mesh(mesh)
        
        content = Path(temp_inp_file).read_text()
        assert "C3D4" in content


class TestMaterialAndProperties:
    """Test material and property definitions"""

    def test_material_elastic(self, temp_inp_file, simple_hex_mesh):
        """Test elastic material"""
        with CalculixWriter(temp_inp_file) as writer:
            writer.write_mesh(simple_hex_mesh)
            writer.write_material("Steel", elastic=(210000, 0.3))
        
        content = Path(temp_inp_file).read_text()
        assert "*MATERIAL" in content
        assert "Steel" in content
        assert "*ELASTIC" in content

    def test_material_plastic(self, temp_inp_file, simple_hex_mesh):
        """Test plastic material"""
        with CalculixWriter(temp_inp_file) as writer:
            writer.write_mesh(simple_hex_mesh)
            writer.write_material("Steel", elastic=(210000, 0.3),
                                plastic=[(250, 0), (400, 0.2)])
        
        content = Path(temp_inp_file).read_text()
        assert "*PLASTIC" in content

    def test_solid_section(self, temp_inp_file, simple_hex_mesh):
        """Test solid section"""
        elsets = {"Part1": [1]}
        with CalculixWriter(temp_inp_file) as writer:
            writer.write_mesh(simple_hex_mesh, elsets=elsets)
            writer.write_material("Steel", elastic=(210000, 0.3))
            writer.write_solid_section("Part1", "Steel")
        
        content = Path(temp_inp_file).read_text()
        assert "*SOLID SECTION" in content


class TestBoundaryAndLoads:
    """Test boundary conditions and loads"""

    def test_boundary_condition(self, temp_inp_file, simple_hex_mesh):
        """Test boundary condition"""
        nsets = {"Fixed": [1, 2, 3, 4]}
        with CalculixWriter(temp_inp_file) as writer:
            writer.write_mesh(simple_hex_mesh, nsets=nsets)
            writer.write_boundary_condition("Fixed", [1, 2, 3])
        
        content = Path(temp_inp_file).read_text()
        assert "*BOUNDARY" in content

    def test_cload(self, temp_inp_file, simple_hex_mesh):
        """Test concentrated load"""
        nsets = {"Loaded": [5, 6, 7, 8]}
        with CalculixWriter(temp_inp_file) as writer:
            writer.write_mesh(simple_hex_mesh, nsets=nsets)
            writer.write_cload("Loaded", 3, -1000.0)
        
        content = Path(temp_inp_file).read_text()
        assert "*CLOAD" in content

    def test_dload(self, temp_inp_file, simple_hex_mesh):
        """Test distributed load"""
        elsets = {"Surface": [1]}
        with CalculixWriter(temp_inp_file) as writer:
            writer.write_mesh(simple_hex_mesh, elsets=elsets)
            writer.write_dload("Surface", "P", 100.0)
        
        content = Path(temp_inp_file).read_text()
        assert "*DLOAD" in content


class TestAnalysisSteps:
    """Test analysis step definitions"""

    def test_static_step(self, temp_inp_file, simple_hex_mesh):
        """Test static analysis step"""
        with CalculixWriter(temp_inp_file) as writer:
            writer.write_mesh(simple_hex_mesh)
            writer.write_step_static()
        
        content = Path(temp_inp_file).read_text()
        assert "*STEP" in content
        assert "*STATIC" in content
        assert "*END STEP" in content

    def test_output_requests(self, temp_inp_file, simple_hex_mesh):
        """Test output requests"""
        with CalculixWriter(temp_inp_file) as writer:
            writer.write_mesh(simple_hex_mesh)
            writer.write_output_requests(node_output=["U", "RF"],
                                        element_output=["S", "E"])
        
        content = Path(temp_inp_file).read_text()
        assert "*NODE FILE" in content
        assert "*EL FILE" in content


class TestErrorHandling:
    """Test error handling"""

    def test_empty_mesh_error(self, temp_inp_file):
        """Test empty mesh error"""
        mesh = MeshData()
        with pytest.raises(CalculixError, match="no nodes"):
            with CalculixWriter(temp_inp_file) as writer:
                writer.write_mesh(mesh)

    def test_no_elements_error(self, temp_inp_file):
        """Test no elements error"""
        mesh = MeshData()
        mesh.add_node(0.0, 0.0, 0.0)
        with pytest.raises(CalculixError, match="no elements"):
            with CalculixWriter(temp_inp_file) as writer:
                writer.write_mesh(mesh)

    def test_file_not_open_error(self, temp_inp_file, simple_hex_mesh):
        """Test file not open error"""
        writer = CalculixWriter(temp_inp_file)
        with pytest.raises(CalculixError, match="not open"):
            writer.write_mesh(simple_hex_mesh)


class TestCompleteModel:
    """Test complete model export"""

    def test_complete_model(self, temp_inp_file, simple_hex_mesh):
        """Test complete model with all features"""
        elsets = {"Part1": [1]}
        nsets = {"Fixed": [1, 2, 3, 4], "Loaded": [5, 6, 7, 8]}
        
        with CalculixWriter(temp_inp_file, title="Complete Test") as writer:
            writer.write_mesh(simple_hex_mesh, elsets=elsets, nsets=nsets)
            writer.write_material("Steel", elastic=(210000, 0.3), density=7850)
            writer.write_solid_section("Part1", "Steel")
            writer.write_boundary_condition("Fixed", [1, 2, 3])
            writer.write_cload("Loaded", 3, -1000.0)
            writer.write_step_static()
            writer.write_output_requests(node_output=["U"], element_output=["S"])
        
        content = Path(temp_inp_file).read_text()
        
        # Verify all sections present
        assert "*HEADING" in content
        assert "*NODE" in content
        assert "*ELEMENT" in content
        assert "*ELSET" in content
        assert "*NSET" in content
        assert "*MATERIAL" in content
        assert "*SOLID SECTION" in content
        assert "*BOUNDARY" in content
        assert "*CLOAD" in content
        assert "*STEP" in content
        assert "*END" in content


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
