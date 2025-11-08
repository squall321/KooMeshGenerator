"""
Mesh Format Converter
=====================

Convert mesh data between different file formats.

Supported formats:
- VTK (Visualization Toolkit) - .vtk
- Abaqus INP - .inp
- Nastran BDF - .bdf
- GMSH MSH - .msh (basic support)

Author: KooMeshGenerator Team
"""

import logging
from pathlib import Path
from typing import Optional
from koomesh.meshing.mesh_data import MeshData, ElementType, Node, Element


logger = logging.getLogger(__name__)


class MeshFormatConverter:
    """
    Convert mesh data between different file formats

    Example:
        >>> converter = MeshFormatConverter()
        >>> converter.export_vtk(mesh, "output.vtk")
        >>> converter.export_abaqus(mesh, "output.inp")
    """

    def __init__(self):
        """Initialize format converter"""
        self.logger = logging.getLogger(__name__)

    def export_vtk(self, mesh: MeshData, filename: str, binary: bool = False):
        """
        Export mesh to VTK format

        VTK (Visualization Toolkit) format is widely used for scientific
        visualization. This exports in legacy VTK ASCII format.

        Args:
            mesh: Mesh to export
            filename: Output filename
            binary: If True, use binary format (not yet implemented)

        Example:
            >>> converter.export_vtk(mesh, "mesh.vtk")
        """
        self.logger.info(f"Exporting mesh to VTK format: {filename}")

        if binary:
            self.logger.warning("Binary VTK export not yet implemented, using ASCII")

        # VTK element type mapping
        vtk_type_map = {
            ElementType.TET4: (10, 4),      # VTK_TETRA
            ElementType.TET10: (24, 10),    # VTK_QUADRATIC_TETRA
            ElementType.HEX8: (12, 8),      # VTK_HEXAHEDRON
            ElementType.HEX20: (25, 20),    # VTK_QUADRATIC_HEXAHEDRON
            ElementType.HEX27: (29, 27),    # VTK_TRIQUADRATIC_HEXAHEDRON
            ElementType.PYRAMID5: (14, 5),  # VTK_PYRAMID
            ElementType.PRISM6: (13, 6),    # VTK_WEDGE
            ElementType.TRI3: (5, 3),       # VTK_TRIANGLE
            ElementType.QUAD4: (9, 4),      # VTK_QUAD
        }

        with open(filename, 'w') as f:
            # Header
            f.write("# vtk DataFile Version 3.0\n")
            f.write("Mesh exported from KooMeshGenerator\n")
            f.write("ASCII\n")
            f.write("DATASET UNSTRUCTURED_GRID\n")

            # Points
            f.write(f"POINTS {mesh.num_nodes()} double\n")
            for node_id in sorted(mesh.nodes.keys()):
                node = mesh.nodes[node_id]
                f.write(f"{node.x} {node.y} {node.z}\n")

            # Cells
            num_cells = mesh.num_elements()
            # Calculate total size (each cell: 1 + num_nodes + connectivity)
            total_size = sum(1 + len(elem.nodes) for elem in mesh.elements.values())

            f.write(f"\nCELLS {num_cells} {total_size}\n")

            # Create node ID to index mapping (VTK uses 0-based indices)
            node_id_to_idx = {nid: idx for idx, nid in enumerate(sorted(mesh.nodes.keys()))}

            for elem in mesh.elements.values():
                node_indices = [node_id_to_idx[nid] for nid in elem.nodes]
                f.write(f"{len(node_indices)} " + " ".join(map(str, node_indices)) + "\n")

            # Cell types
            f.write(f"\nCELL_TYPES {num_cells}\n")
            for elem in mesh.elements.values():
                if elem.type in vtk_type_map:
                    vtk_type = vtk_type_map[elem.type][0]
                    f.write(f"{vtk_type}\n")
                else:
                    self.logger.warning(f"Unknown element type for VTK: {elem.type}")
                    f.write("0\n")

            # Cell data (part IDs)
            f.write(f"\nCELL_DATA {num_cells}\n")
            f.write("SCALARS part_id int 1\n")
            f.write("LOOKUP_TABLE default\n")
            for elem in mesh.elements.values():
                f.write(f"{elem.part_id}\n")

        self.logger.info(f"Exported {mesh.num_nodes()} nodes, {mesh.num_elements()} elements")

    def export_abaqus(self, mesh: MeshData, filename: str, part_name: str = "Part-1"):
        """
        Export mesh to Abaqus INP format

        Abaqus is a commercial FEA software. This exports a basic INP file
        with nodes, elements, and element sets by part.

        Args:
            mesh: Mesh to export
            filename: Output filename
            part_name: Name of the part in Abaqus

        Example:
            >>> converter.export_abaqus(mesh, "mesh.inp")
        """
        self.logger.info(f"Exporting mesh to Abaqus INP format: {filename}")

        # Abaqus element type mapping
        abaqus_type_map = {
            ElementType.TET4: "C3D4",
            ElementType.TET10: "C3D10",
            ElementType.HEX8: "C3D8",
            ElementType.HEX20: "C3D20",
            ElementType.HEX27: "C3D27",
            ElementType.PYRAMID5: "C3D5",
            ElementType.PRISM6: "C3D6",
        }

        with open(filename, 'w') as f:
            # Header
            f.write("*Heading\n")
            f.write("** Mesh exported from KooMeshGenerator\n")
            f.write("**\n")

            # Part
            f.write(f"*Part, name={part_name}\n")

            # Nodes
            f.write("*Node\n")
            for node_id in sorted(mesh.nodes.keys()):
                node = mesh.nodes[node_id]
                f.write(f"{node_id}, {node.x}, {node.y}, {node.z}\n")

            # Elements by type and part
            elem_by_type_part = {}
            for elem in mesh.elements.values():
                key = (elem.type, elem.part_id)
                if key not in elem_by_type_part:
                    elem_by_type_part[key] = []
                elem_by_type_part[key].append(elem)

            for (elem_type, part_id), elements in sorted(elem_by_type_part.items()):
                if elem_type in abaqus_type_map:
                    abaqus_type = abaqus_type_map[elem_type]
                    f.write(f"*Element, type={abaqus_type}, elset=Part{part_id}\n")

                    for elem in elements:
                        node_str = ", ".join(map(str, elem.nodes))
                        f.write(f"{elem.id}, {node_str}\n")
                else:
                    self.logger.warning(f"Unknown element type for Abaqus: {elem_type}")

            # End part
            f.write("*End Part\n")

            # Assembly
            f.write("**\n")
            f.write("*Assembly, name=Assembly\n")
            f.write(f"*Instance, name={part_name}-1, part={part_name}\n")
            f.write("*End Instance\n")
            f.write("*End Assembly\n")

        self.logger.info(f"Exported {mesh.num_nodes()} nodes, {mesh.num_elements()} elements")

    def export_nastran(self, mesh: MeshData, filename: str):
        """
        Export mesh to Nastran BDF format

        Nastran is widely used in aerospace/automotive FEA.

        Args:
            mesh: Mesh to export
            filename: Output filename

        Example:
            >>> converter.export_nastran(mesh, "mesh.bdf")
        """
        self.logger.info(f"Exporting mesh to Nastran BDF format: {filename}")

        # Nastran element type mapping
        nastran_type_map = {
            ElementType.TET4: "CTETRA",
            ElementType.TET10: "CTETRA",
            ElementType.HEX8: "CHEXA",
            ElementType.HEX20: "CHEXA",
            ElementType.PYRAMID5: "CPYRAM",
            ElementType.PRISM6: "CPENTA",
        }

        with open(filename, 'w') as f:
            # Header
            f.write("$\n")
            f.write("$ Mesh exported from KooMeshGenerator\n")
            f.write("$\n")
            f.write("BEGIN BULK\n")

            # Nodes (GRID cards)
            for node_id in sorted(mesh.nodes.keys()):
                node = mesh.nodes[node_id]
                # Nastran format: GRID, NID, CP, X, Y, Z
                f.write(f"GRID,{node_id},,{node.x:.6e},{node.y:.6e},{node.z:.6e}\n")

            # Elements
            for elem in mesh.elements.values():
                if elem.type in nastran_type_map:
                    nastran_type = nastran_type_map[elem.type]
                    # Format: CTETRA, EID, PID, N1, N2, N3, N4, ...
                    node_str = ",".join(map(str, elem.nodes))
                    f.write(f"{nastran_type},{elem.id},{elem.part_id},{node_str}\n")
                else:
                    self.logger.warning(f"Unknown element type for Nastran: {elem.type}")

            # End
            f.write("ENDDATA\n")

        self.logger.info(f"Exported {mesh.num_nodes()} nodes, {mesh.num_elements()} elements")

    def import_from_vtk(self, filename: str) -> MeshData:
        """
        Import mesh from VTK format (basic implementation)

        Args:
            filename: Input VTK filename

        Returns:
            MeshData object

        Note:
            This is a basic implementation supporting legacy VTK ASCII format
        """
        self.logger.info(f"Importing mesh from VTK format: {filename}")
        self.logger.warning("VTK import is basic - may not support all features")

        # VTK to ElementType mapping (reverse)
        vtk_to_elem_type = {
            10: ElementType.TET4,
            24: ElementType.TET10,
            12: ElementType.HEX8,
            25: ElementType.HEX20,
            29: ElementType.HEX27,
            14: ElementType.PYRAMID5,
            13: ElementType.PRISM6,
            5: ElementType.TRI3,
            9: ElementType.QUAD4,
        }

        mesh = None
        nodes = []
        cells = []
        cell_types = []

        with open(filename, 'r') as f:
            lines = f.readlines()

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            if line.startswith("POINTS"):
                # Read points
                parts = line.split()
                num_points = int(parts[1])
                i += 1
                for _ in range(num_points):
                    coords = list(map(float, lines[i].strip().split()))
                    nodes.append(coords)
                    i += 1
                continue

            elif line.startswith("CELLS"):
                # Read cells
                parts = line.split()
                num_cells = int(parts[1])
                i += 1
                for _ in range(num_cells):
                    cell_data = list(map(int, lines[i].strip().split()))
                    num_nodes = cell_data[0]
                    cell_nodes = cell_data[1:num_nodes+1]
                    cells.append(cell_nodes)
                    i += 1
                continue

            elif line.startswith("CELL_TYPES"):
                # Read cell types
                parts = line.split()
                num_cells = int(parts[1])
                i += 1
                for _ in range(num_cells):
                    cell_type = int(lines[i].strip())
                    cell_types.append(cell_type)
                    i += 1
                continue

            i += 1

        # Create mesh
        if cells and cell_types:
            elem_type = vtk_to_elem_type.get(cell_types[0], ElementType.TET4)
            mesh = MeshData(element_type=elem_type)

            # Add nodes
            for idx, coords in enumerate(nodes):
                mesh.add_node(coords[0], coords[1], coords[2])

            # Add elements
            for cell_nodes, cell_type in zip(cells, cell_types):
                # Convert 0-based indices to 1-based node IDs
                node_ids = [nid + 1 for nid in cell_nodes]
                elem_type = vtk_to_elem_type.get(cell_type, ElementType.TET4)
                mesh.add_element(node_ids, element_type=elem_type)

            self.logger.info(f"Imported {mesh.num_nodes()} nodes, {mesh.num_elements()} elements")
        else:
            raise ValueError("Could not parse VTK file")

        return mesh


def convert_format(input_file: str, output_file: str):
    """
    Convert mesh between formats based on file extensions

    Supported extensions:
    - .vtk: VTK format
    - .inp: Abaqus format
    - .bdf: Nastran format

    Args:
        input_file: Input mesh file
        output_file: Output mesh file

    Example:
        >>> convert_format("mesh.vtk", "mesh.inp")
    """
    converter = MeshFormatConverter()

    input_ext = Path(input_file).suffix.lower()
    output_ext = Path(output_file).suffix.lower()

    # Import
    if input_ext == ".vtk":
        mesh = converter.import_from_vtk(input_file)
    else:
        raise ValueError(f"Unsupported input format: {input_ext}")

    # Export
    if output_ext == ".vtk":
        converter.export_vtk(mesh, output_file)
    elif output_ext == ".inp":
        converter.export_abaqus(mesh, output_file)
    elif output_ext == ".bdf":
        converter.export_nastran(mesh, output_file)
    else:
        raise ValueError(f"Unsupported output format: {output_ext}")

    logger.info(f"Conversion complete: {input_file} -> {output_file}")
