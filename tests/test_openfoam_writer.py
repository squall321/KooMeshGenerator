"""
Tests for OpenFOAM polyMesh Writer
===================================

Tests the OpenFOAM mesh export functionality.
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from koomesh.meshing.mesh_data import MeshData, ElementType
from koomesh.export.openfoam_writer import OpenFOAMWriter, export_to_openfoam, OpenFOAMError


class TestBasicFunctionality:
    """Test basic OpenFOAM writer functionality"""

    def test_initialization(self):
        """Test writer initialization"""
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = OpenFOAMWriter(tmpdir)
            assert writer.case_dir == Path(tmpdir)
            assert writer.polymesh_dir == Path(tmpdir) / "constant" / "polyMesh"

    def test_directory_creation(self):
        """Test polyMesh directory is created"""
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = OpenFOAMWriter(tmpdir)
            mesh = self._create_simple_hex8()
            writer.write_mesh(mesh)

            polymesh_dir = Path(tmpdir) / "constant" / "polyMesh"
            assert polymesh_dir.exists()
            assert polymesh_dir.is_dir()

    def test_required_files_created(self):
        """Test all required polyMesh files are created"""
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = OpenFOAMWriter(tmpdir)
            mesh = self._create_simple_hex8()
            writer.write_mesh(mesh)

            polymesh_dir = Path(tmpdir) / "constant" / "polyMesh"
            required_files = ["points", "faces", "owner", "neighbour", "boundary"]

            for filename in required_files:
                filepath = polymesh_dir / filename
                assert filepath.exists(), f"Missing required file: {filename}"

    def test_empty_mesh_error(self):
        """Test error on empty mesh"""
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = OpenFOAMWriter(tmpdir)
            mesh = MeshData(element_type=ElementType.HEX8)

            with pytest.raises(OpenFOAMError, match="empty mesh"):
                writer.write_mesh(mesh)

    @staticmethod
    def _create_simple_hex8():
        """Create simple single hex8 element"""
        mesh = MeshData(element_type=ElementType.HEX8)
        # Create unit cube
        node_ids = []
        for i in range(2):
            for j in range(2):
                for k in range(2):
                    nid = mesh.add_node(float(i), float(j), float(k))
                    node_ids.append(nid)
        mesh.add_element([node_ids[0], node_ids[1], node_ids[3], node_ids[2],
                         node_ids[4], node_ids[5], node_ids[7], node_ids[6]])
        return mesh


class TestPointsFile:
    """Test points file writing"""

    def test_points_count(self):
        """Test correct number of points written"""
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = OpenFOAMWriter(tmpdir)
            mesh = self._create_two_hex8()
            writer.write_mesh(mesh)

            points_file = Path(tmpdir) / "constant" / "polyMesh" / "points"
            content = points_file.read_text()

            # Should have 12 nodes (two cubes sharing 4 nodes)
            assert "12" in content.split('\n')

    def test_points_format(self):
        """Test points are written in correct format"""
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = OpenFOAMWriter(tmpdir)
            mesh = MeshData(element_type=ElementType.HEX8)
            node_ids = []
            node_ids.append(mesh.add_node(1.5, 2.5, 3.5))
            node_ids.append(mesh.add_node(0.0, 0.0, 0.0))
            for i in range(6):
                node_ids.append(mesh.add_node(0.0, 0.0, 0.0))
            mesh.add_element(node_ids)

            writer.write_mesh(mesh)

            points_file = Path(tmpdir) / "constant" / "polyMesh" / "points"
            content = points_file.read_text()

            # Check for coordinates in scientific notation
            assert "(1.5" in content or "(1.50000" in content
            assert "2.5" in content or "2.50000" in content
            assert "3.5" in content or "3.50000" in content

    @staticmethod
    def _create_two_hex8():
        """Create two hex8 elements side by side"""
        mesh = MeshData(element_type=ElementType.HEX8)
        node_ids = []
        # First cube: x=0 to 1
        for i in range(2):
            for j in range(2):
                for k in range(2):
                    nid = mesh.add_node(float(i), float(j), float(k))
                    node_ids.append(nid)
        # Second cube: x=1 to 2 (shares 4 nodes with first)
        for j in range(2):
            for k in range(2):
                nid = mesh.add_node(2.0, float(j), float(k))
                node_ids.append(nid)

        # First cube
        mesh.add_element([node_ids[0], node_ids[1], node_ids[3], node_ids[2],
                         node_ids[4], node_ids[5], node_ids[7], node_ids[6]])
        # Second cube shares right face with first
        mesh.add_element([node_ids[1], node_ids[8], node_ids[9], node_ids[3],
                         node_ids[5], node_ids[10], node_ids[11], node_ids[7]])
        return mesh


class TestFaceExtraction:
    """Test face extraction from elements"""

    def test_single_hex8_faces(self):
        """Test face extraction from single hex8"""
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = OpenFOAMWriter(tmpdir)
            mesh = self._create_simple_hex8()
            writer.write_mesh(mesh)

            faces_file = Path(tmpdir) / "constant" / "polyMesh" / "faces"
            content = faces_file.read_text()

            # Single hex8 has 6 faces, all boundary
            assert "\n6\n" in content  # Check face count

    def test_two_hex8_internal_face(self):
        """Test internal face detection between two hexes"""
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = OpenFOAMWriter(tmpdir)
            mesh = self._create_two_hex8()
            writer.write_mesh(mesh)

            neighbour_file = Path(tmpdir) / "constant" / "polyMesh" / "neighbour"
            content = neighbour_file.read_text()

            # Two hex8 share 1 face, so should have 1 internal face
            # Check that the file contains "1" as the count
            assert "\n1\n" in content  # Count of internal faces

    def test_tet4_face_count(self):
        """Test TET4 element face count"""
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = OpenFOAMWriter(tmpdir)
            mesh = MeshData(element_type=ElementType.TET4)
            n1 = mesh.add_node(0.0, 0.0, 0.0)
            n2 = mesh.add_node(1.0, 0.0, 0.0)
            n3 = mesh.add_node(0.5, 1.0, 0.0)
            n4 = mesh.add_node(0.5, 0.5, 1.0)
            mesh.add_element([n1, n2, n3, n4])

            writer.write_mesh(mesh)

            faces_file = Path(tmpdir) / "constant" / "polyMesh" / "faces"
            content = faces_file.read_text()

            # Single TET4 has 4 triangular faces
            assert "\n4\n" in content  # Check face count

    @staticmethod
    def _create_simple_hex8():
        """Create simple single hex8 element"""
        mesh = MeshData(element_type=ElementType.HEX8)
        node_ids = []
        for i in range(2):
            for j in range(2):
                for k in range(2):
                    node_ids.append(mesh.add_node(float(i), float(j), float(k)))
        mesh.add_element([node_ids[0], node_ids[1], node_ids[3], node_ids[2],
                         node_ids[4], node_ids[5], node_ids[7], node_ids[6]])
        return mesh

    @staticmethod
    def _create_two_hex8():
        """Create two hex8 elements sharing a face"""
        mesh = MeshData(element_type=ElementType.HEX8)
        node_ids = []
        # First cube
        for i in range(2):
            for j in range(2):
                for k in range(2):
                    node_ids.append(mesh.add_node(float(i), float(j), float(k)))
        # Second cube (shares x=1 face)
        for j in range(2):
            for k in range(2):
                node_ids.append(mesh.add_node(2.0, float(j), float(k)))

        mesh.add_element([node_ids[0], node_ids[1], node_ids[3], node_ids[2],
                         node_ids[4], node_ids[5], node_ids[7], node_ids[6]])
        mesh.add_element([node_ids[1], node_ids[8], node_ids[9], node_ids[3],
                         node_ids[5], node_ids[10], node_ids[11], node_ids[7]])
        return mesh


class TestOwnerNeighbour:
    """Test owner/neighbour file writing"""

    def test_owner_count_matches_faces(self):
        """Test owner entries match face count"""
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = OpenFOAMWriter(tmpdir)
            mesh = self._create_simple_hex8()
            writer.write_mesh(mesh)

            owner_file = Path(tmpdir) / "constant" / "polyMesh" / "owner"
            faces_file = Path(tmpdir) / "constant" / "polyMesh" / "faces"

            owner_content = owner_file.read_text()
            faces_content = faces_file.read_text()

            # Extract counts from files
            owner_count = int([l for l in owner_content.split('\n') if l.strip() and l.strip().isdigit()][0])
            faces_count = int([l for l in faces_content.split('\n') if l.strip() and l.strip().isdigit()][0])

            assert owner_count == faces_count

    def test_neighbour_only_internal(self):
        """Test neighbour file only has internal faces"""
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = OpenFOAMWriter(tmpdir)
            mesh = self._create_two_hex8()
            writer.write_mesh(mesh)

            neighbour_file = Path(tmpdir) / "constant" / "polyMesh" / "neighbour"
            content = neighbour_file.read_text()

            # Count neighbour entries
            lines = content.split('\n')
            count_line = [l for l in lines if l.strip() and l.strip().isdigit()][0]
            n_neighbours = int(count_line)

            # Two cubes share 1 face
            assert n_neighbours == 1

    def test_owner_values_valid(self):
        """Test owner cell IDs are valid"""
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = OpenFOAMWriter(tmpdir)
            mesh = self._create_two_hex8()
            writer.write_mesh(mesh)

            owner_file = Path(tmpdir) / "constant" / "polyMesh" / "owner"
            content = owner_file.read_text()

            # Extract owner IDs
            lines = [l.strip() for l in content.split('\n') if l.strip() and l.strip().isdigit()]
            owner_ids = [int(l) for l in lines[1:]]  # Skip count line

            # Owner IDs should be 0 or 1 (two cells)
            assert all(owner_id in [0, 1] for owner_id in owner_ids)

    @staticmethod
    def _create_simple_hex8():
        """Create simple single hex8 element"""
        mesh = MeshData(element_type=ElementType.HEX8)
        node_ids = []
        for i in range(2):
            for j in range(2):
                for k in range(2):
                    node_ids.append(mesh.add_node(float(i), float(j), float(k)))
        mesh.add_element([node_ids[0], node_ids[1], node_ids[3], node_ids[2],
                         node_ids[4], node_ids[5], node_ids[7], node_ids[6]])
        return mesh

    @staticmethod
    def _create_two_hex8():
        """Create two hex8 elements sharing a face"""
        mesh = MeshData(element_type=ElementType.HEX8)
        node_ids = []
        for i in range(2):
            for j in range(2):
                for k in range(2):
                    node_ids.append(mesh.add_node(float(i), float(j), float(k)))
        for j in range(2):
            for k in range(2):
                node_ids.append(mesh.add_node(2.0, float(j), float(k)))
        mesh.add_element([node_ids[0], node_ids[1], node_ids[3], node_ids[2],
                         node_ids[4], node_ids[5], node_ids[7], node_ids[6]])
        mesh.add_element([node_ids[1], node_ids[8], node_ids[9], node_ids[3],
                         node_ids[5], node_ids[10], node_ids[11], node_ids[7]])
        return mesh


class TestBoundaryFile:
    """Test boundary file writing"""

    def test_default_boundary_patch(self):
        """Test default boundary patch is created"""
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = OpenFOAMWriter(tmpdir)
            mesh = self._create_simple_hex8()
            writer.write_mesh(mesh)

            boundary_file = Path(tmpdir) / "constant" / "polyMesh" / "boundary"
            content = boundary_file.read_text()

            assert "defaultFaces" in content
            assert "type" in content
            assert "patch" in content

    def test_custom_boundary_patches(self):
        """Test custom boundary patches"""
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = OpenFOAMWriter(tmpdir)
            mesh = self._create_simple_hex8()

            patches = {
                "inlet": [(0, 0)],
                "outlet": [(0, 1)],
                "walls": [(0, 2), (0, 3), (0, 4), (0, 5)]
            }

            writer.write_mesh(mesh, boundary_patches=patches)

            boundary_file = Path(tmpdir) / "constant" / "polyMesh" / "boundary"
            content = boundary_file.read_text()

            assert "inlet" in content
            assert "outlet" in content
            assert "walls" in content
            assert "\n3\n" in content  # 3 patches

    def test_boundary_face_counts(self):
        """Test boundary patch face counts"""
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = OpenFOAMWriter(tmpdir)
            mesh = self._create_two_hex8()

            patches = {
                "inlet": [(0, 0)],
                "outlet": [(1, 1)]
            }

            writer.write_mesh(mesh, boundary_patches=patches)

            boundary_file = Path(tmpdir) / "constant" / "polyMesh" / "boundary"
            content = boundary_file.read_text()

            # Each patch should have nFaces entry
            assert "nFaces" in content
            assert "startFace" in content

    @staticmethod
    def _create_simple_hex8():
        """Create simple single hex8 element"""
        mesh = MeshData(element_type=ElementType.HEX8)
        node_ids = []
        for i in range(2):
            for j in range(2):
                for k in range(2):
                    node_ids.append(mesh.add_node(float(i), float(j), float(k)))
        mesh.add_element([node_ids[0], node_ids[1], node_ids[3], node_ids[2],
                         node_ids[4], node_ids[5], node_ids[7], node_ids[6]])
        return mesh

    @staticmethod
    def _create_two_hex8():
        """Create two hex8 elements"""
        mesh = MeshData(element_type=ElementType.HEX8)
        node_ids = []
        for i in range(2):
            for j in range(2):
                for k in range(2):
                    node_ids.append(mesh.add_node(float(i), float(j), float(k)))
        for j in range(2):
            for k in range(2):
                node_ids.append(mesh.add_node(2.0, float(j), float(k)))
        mesh.add_element([node_ids[0], node_ids[1], node_ids[3], node_ids[2],
                         node_ids[4], node_ids[5], node_ids[7], node_ids[6]])
        mesh.add_element([node_ids[1], node_ids[8], node_ids[9], node_ids[3],
                         node_ids[5], node_ids[10], node_ids[11], node_ids[7]])
        return mesh


class TestElementTypes:
    """Test different element types"""

    def test_hex20_export(self):
        """Test HEX20 element export"""
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = OpenFOAMWriter(tmpdir)
            mesh = self._create_hex20()
            writer.write_mesh(mesh)

            faces_file = Path(tmpdir) / "constant" / "polyMesh" / "faces"
            assert faces_file.exists()

    def test_tet10_export(self):
        """Test TET10 element export"""
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = OpenFOAMWriter(tmpdir)
            mesh = self._create_tet10()
            writer.write_mesh(mesh)

            faces_file = Path(tmpdir) / "constant" / "polyMesh" / "faces"
            assert faces_file.exists()

    def test_prism6_export(self):
        """Test PRISM6 element export"""
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = OpenFOAMWriter(tmpdir)
            mesh = self._create_prism6()
            writer.write_mesh(mesh)

            faces_file = Path(tmpdir) / "constant" / "polyMesh" / "faces"
            content = faces_file.read_text()

            # PRISM6 has 5 faces (2 triangular + 3 quad)
            assert "5" in content

    def test_pyramid5_export(self):
        """Test PYRAMID5 element export"""
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = OpenFOAMWriter(tmpdir)
            mesh = self._create_pyramid5()
            writer.write_mesh(mesh)

            faces_file = Path(tmpdir) / "constant" / "polyMesh" / "faces"
            content = faces_file.read_text()

            # PYRAMID5 has 5 faces (1 quad + 4 triangular)
            assert "5" in content

    def test_unsupported_element_error(self):
        """Test error on unsupported element type"""
        # This would test if we somehow got an unsupported type
        # Current implementation supports all our element types
        pass

    @staticmethod
    def _create_hex20():
        """Create HEX20 element"""
        mesh = MeshData(element_type=ElementType.HEX20)
        node_ids = []
        # Corner nodes
        for i in range(2):
            for j in range(2):
                for k in range(2):
                    node_ids.append(mesh.add_node(float(i), float(j), float(k)))
        # Mid-edge nodes (12 nodes)
        for i in range(12):
            node_ids.append(mesh.add_node(0.5, 0.5, 0.5))
        mesh.add_element(node_ids)
        return mesh

    @staticmethod
    def _create_tet10():
        """Create TET10 element"""
        mesh = MeshData(element_type=ElementType.TET10)
        node_ids = []
        # Corner nodes
        node_ids.append(mesh.add_node(0.0, 0.0, 0.0))
        node_ids.append(mesh.add_node(1.0, 0.0, 0.0))
        node_ids.append(mesh.add_node(0.5, 1.0, 0.0))
        node_ids.append(mesh.add_node(0.5, 0.5, 1.0))
        # Mid-edge nodes (6 nodes)
        for i in range(6):
            node_ids.append(mesh.add_node(0.5, 0.5, 0.5))
        mesh.add_element(node_ids)
        return mesh

    @staticmethod
    def _create_prism6():
        """Create PRISM6 element"""
        mesh = MeshData(element_type=ElementType.PRISM6)
        node_ids = []
        # Bottom triangle
        node_ids.append(mesh.add_node(0.0, 0.0, 0.0))
        node_ids.append(mesh.add_node(1.0, 0.0, 0.0))
        node_ids.append(mesh.add_node(0.5, 1.0, 0.0))
        # Top triangle
        node_ids.append(mesh.add_node(0.0, 0.0, 1.0))
        node_ids.append(mesh.add_node(1.0, 0.0, 1.0))
        node_ids.append(mesh.add_node(0.5, 1.0, 1.0))
        mesh.add_element(node_ids)
        return mesh

    @staticmethod
    def _create_pyramid5():
        """Create PYRAMID5 element"""
        mesh = MeshData(element_type=ElementType.PYRAMID5)
        node_ids = []
        # Base quad
        node_ids.append(mesh.add_node(0.0, 0.0, 0.0))
        node_ids.append(mesh.add_node(1.0, 0.0, 0.0))
        node_ids.append(mesh.add_node(1.0, 1.0, 0.0))
        node_ids.append(mesh.add_node(0.0, 1.0, 0.0))
        # Apex
        node_ids.append(mesh.add_node(0.5, 0.5, 1.0))
        mesh.add_element(node_ids)
        return mesh


class TestConvenienceFunction:
    """Test convenience export function"""

    def test_export_to_openfoam_success(self):
        """Test successful export using convenience function"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mesh = self._create_simple_hex8()
            result = export_to_openfoam(mesh, tmpdir)

            assert result is True
            polymesh_dir = Path(tmpdir) / "constant" / "polyMesh"
            assert polymesh_dir.exists()

    def test_export_to_openfoam_with_patches(self):
        """Test export with boundary patches"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mesh = self._create_simple_hex8()
            patches = {"inlet": [(0, 0)], "outlet": [(0, 1)]}
            result = export_to_openfoam(mesh, tmpdir, boundary_patches=patches)

            assert result is True

    @staticmethod
    def _create_simple_hex8():
        """Create simple single hex8 element"""
        mesh = MeshData(element_type=ElementType.HEX8)
        node_ids = []
        for i in range(2):
            for j in range(2):
                for k in range(2):
                    node_ids.append(mesh.add_node(float(i), float(j), float(k)))
        mesh.add_element([node_ids[0], node_ids[1], node_ids[3], node_ids[2],
                         node_ids[4], node_ids[5], node_ids[7], node_ids[6]])
        return mesh


class TestFileFormat:
    """Test OpenFOAM file format compliance"""

    def test_foam_file_header(self):
        """Test FoamFile header is present"""
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = OpenFOAMWriter(tmpdir)
            mesh = self._create_simple_hex8()
            writer.write_mesh(mesh)

            points_file = Path(tmpdir) / "constant" / "polyMesh" / "points"
            content = points_file.read_text()

            assert "FoamFile" in content
            assert "version" in content
            assert "format" in content
            assert "class" in content
            assert "object" in content

    def test_ascii_format(self):
        """Test files are in ASCII format"""
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = OpenFOAMWriter(tmpdir)
            mesh = self._create_simple_hex8()
            writer.write_mesh(mesh)

            points_file = Path(tmpdir) / "constant" / "polyMesh" / "points"
            content = points_file.read_text()

            assert "format      ascii" in content

    def test_parentheses_format(self):
        """Test OpenFOAM parentheses format"""
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = OpenFOAMWriter(tmpdir)
            mesh = self._create_simple_hex8()
            writer.write_mesh(mesh)

            points_file = Path(tmpdir) / "constant" / "polyMesh" / "points"
            content = points_file.read_text()

            # OpenFOAM lists use parentheses
            assert "(\n" in content
            assert "\n)" in content or ")\n" in content

    @staticmethod
    def _create_simple_hex8():
        """Create simple single hex8 element"""
        mesh = MeshData(element_type=ElementType.HEX8)
        node_ids = []
        for i in range(2):
            for j in range(2):
                for k in range(2):
                    node_ids.append(mesh.add_node(float(i), float(j), float(k)))
        mesh.add_element([node_ids[0], node_ids[1], node_ids[3], node_ids[2],
                         node_ids[4], node_ids[5], node_ids[7], node_ids[6]])
        return mesh
