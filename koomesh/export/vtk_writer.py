"""
VTK Export Writer
==================

This module provides functionality to export mesh data to VTK formats:
- .vtu (VTK XML Unstructured Grid) - Modern XML-based format
- .vtk (Legacy VTK format) - ASCII/Binary format

VTK (Visualization Toolkit) formats are widely used for scientific visualization
and are compatible with:
- ParaView
- VisIt
- Mayavi
- VTK-based applications

Author: KooMeshGenerator Development Team
"""

import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import base64
import struct

from koomesh.meshing.mesh_data import MeshData, ElementType


class VTKWriter:
    """
    Writer for VTK format files (.vtu and .vtk)

    Supports:
    - VTU (XML Unstructured Grid): Modern format with compression support
    - VTK (Legacy): ASCII format for compatibility

    Element type mapping:
    - HEX8 → VTK_HEXAHEDRON (12)
    - HEX20 → VTK_QUADRATIC_HEXAHEDRON (25)
    - HEX27 → VTK_TRIQUADRATIC_HEXAHEDRON (29)
    - TET4 → VTK_TETRA (10)
    - TET10 → VTK_QUADRATIC_TETRA (24)
    - PRISM6 → VTK_WEDGE (13)
    - PYRAMID5 → VTK_PYRAMID (14)

    Usage:
        with VTKWriter('output.vtu') as writer:
            writer.write_mesh(mesh)
    """

    # VTK cell type IDs
    VTK_CELL_TYPES = {
        ElementType.HEX8: 12,      # VTK_HEXAHEDRON
        ElementType.HEX20: 25,     # VTK_QUADRATIC_HEXAHEDRON
        ElementType.HEX27: 29,     # VTK_TRIQUADRATIC_HEXAHEDRON
        ElementType.TET4: 10,      # VTK_TETRA
        ElementType.TET10: 24,     # VTK_QUADRATIC_TETRA
        ElementType.PRISM6: 13,    # VTK_WEDGE
        ElementType.PYRAMID5: 14,  # VTK_PYRAMID
    }

    def __init__(self, output_path: str, format: str = 'xml', encoding: str = 'ascii'):
        """
        Initialize VTK writer

        Args:
            output_path: Output file path (.vtu or .vtk)
            format: 'xml' for .vtu (default) or 'legacy' for .vtk
            encoding: 'ascii' (default) or 'binary' (for XML format)
        """
        self.output_path = Path(output_path)
        self.format = format.lower()
        self.encoding = encoding.lower()
        self.file = None

        self.logger = logging.getLogger(__name__)

        # Validate format
        if self.format not in ['xml', 'legacy']:
            raise ValueError(f"Format must be 'xml' or 'legacy', got '{self.format}'")

        # Validate encoding
        if self.encoding not in ['ascii', 'binary']:
            raise ValueError(f"Encoding must be 'ascii' or 'binary', got '{self.encoding}'")

        # Ensure correct file extension
        if self.format == 'xml' and self.output_path.suffix != '.vtu':
            self.logger.warning(f"XML format should use .vtu extension, got {self.output_path.suffix}")
        elif self.format == 'legacy' and self.output_path.suffix != '.vtk':
            self.logger.warning(f"Legacy format should use .vtk extension, got {self.output_path.suffix}")

    def __enter__(self):
        """Context manager entry"""
        self.file = open(self.output_path, 'w')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.file:
            self.file.close()

    def write_mesh(self, mesh: MeshData,
                   scalar_data: Optional[Dict[str, List[float]]] = None,
                   vector_data: Optional[Dict[str, List[List[float]]]] = None):
        """
        Write complete mesh to VTK file

        Args:
            mesh: Mesh data to export
            scalar_data: Optional scalar data fields {name: [values]}
            vector_data: Optional vector data fields {name: [[x,y,z], ...]}
        """
        if self.format == 'xml':
            self._write_vtu(mesh, scalar_data, vector_data)
        else:
            self._write_vtk_legacy(mesh, scalar_data, vector_data)

        self.logger.info(f"Wrote mesh to {self.output_path}")

    def _write_vtu(self, mesh: MeshData,
                   scalar_data: Optional[Dict[str, List[float]]] = None,
                   vector_data: Optional[Dict[str, List[List[float]]]] = None):
        """Write VTK XML Unstructured Grid (.vtu)"""

        # Create XML structure
        root = ET.Element('VTKFile')
        root.set('type', 'UnstructuredGrid')
        root.set('version', '1.0')
        root.set('byte_order', 'LittleEndian')

        # UnstructuredGrid element
        ugrid = ET.SubElement(root, 'UnstructuredGrid')

        # Piece element (single piece for now)
        piece = ET.SubElement(ugrid, 'Piece')
        piece.set('NumberOfPoints', str(mesh.num_nodes()))
        piece.set('NumberOfCells', str(mesh.num_elements()))

        # Points (nodes)
        points = ET.SubElement(piece, 'Points')
        points_data = ET.SubElement(points, 'DataArray')
        points_data.set('type', 'Float64')
        points_data.set('NumberOfComponents', '3')
        points_data.set('format', self.encoding)

        # Write point coordinates
        coords_list = []
        for node_id in sorted(mesh.nodes.keys()):
            node = mesh.nodes[node_id]
            coords_list.extend([node.x, node.y, node.z])

        if self.encoding == 'ascii':
            points_data.text = ' '.join(f'{c:.8e}' for c in coords_list)
        else:
            # Binary encoding (base64)
            binary_data = struct.pack(f'{len(coords_list)}d', *coords_list)
            points_data.text = base64.b64encode(binary_data).decode('ascii')

        # Cells (elements)
        cells = ET.SubElement(piece, 'Cells')

        # Connectivity
        connectivity = ET.SubElement(cells, 'DataArray')
        connectivity.set('type', 'Int32')
        connectivity.set('Name', 'connectivity')
        connectivity.set('format', self.encoding)

        # Build connectivity array (convert 1-based to 0-based)
        conn_list = []
        for elem in mesh.elements.values():
            conn_list.extend([nid - 1 for nid in elem.nodes])

        if self.encoding == 'ascii':
            connectivity.text = ' '.join(str(c) for c in conn_list)
        else:
            binary_data = struct.pack(f'{len(conn_list)}i', *conn_list)
            connectivity.text = base64.b64encode(binary_data).decode('ascii')

        # Offsets
        offsets = ET.SubElement(cells, 'DataArray')
        offsets.set('type', 'Int32')
        offsets.set('Name', 'offsets')
        offsets.set('format', self.encoding)

        offset_list = []
        current_offset = 0
        for elem in mesh.elements.values():
            current_offset += len(elem.nodes)
            offset_list.append(current_offset)

        if self.encoding == 'ascii':
            offsets.text = ' '.join(str(o) for o in offset_list)
        else:
            binary_data = struct.pack(f'{len(offset_list)}i', *offset_list)
            offsets.text = base64.b64encode(binary_data).decode('ascii')

        # Cell types
        types = ET.SubElement(cells, 'DataArray')
        types.set('type', 'UInt8')
        types.set('Name', 'types')
        types.set('format', self.encoding)

        vtk_type = self.VTK_CELL_TYPES.get(mesh.element_type)
        if vtk_type is None:
            raise ValueError(f"Element type {mesh.element_type.code} not supported in VTK export")

        type_list = [vtk_type] * mesh.num_elements()

        if self.encoding == 'ascii':
            types.text = ' '.join(str(t) for t in type_list)
        else:
            binary_data = struct.pack(f'{len(type_list)}B', *type_list)
            types.text = base64.b64encode(binary_data).decode('ascii')

        # Point data (optional)
        if scalar_data or vector_data:
            point_data = ET.SubElement(piece, 'PointData')

            if scalar_data:
                for name, values in scalar_data.items():
                    data_array = ET.SubElement(point_data, 'DataArray')
                    data_array.set('type', 'Float64')
                    data_array.set('Name', name)
                    data_array.set('format', self.encoding)

                    if self.encoding == 'ascii':
                        data_array.text = ' '.join(f'{v:.8e}' for v in values)
                    else:
                        binary_data = struct.pack(f'{len(values)}d', *values)
                        data_array.text = base64.b64encode(binary_data).decode('ascii')

            if vector_data:
                for name, vectors in vector_data.items():
                    data_array = ET.SubElement(point_data, 'DataArray')
                    data_array.set('type', 'Float64')
                    data_array.set('Name', name)
                    data_array.set('NumberOfComponents', '3')
                    data_array.set('format', self.encoding)

                    # Flatten vector list
                    flat_vectors = [comp for vec in vectors for comp in vec]

                    if self.encoding == 'ascii':
                        data_array.text = ' '.join(f'{v:.8e}' for v in flat_vectors)
                    else:
                        binary_data = struct.pack(f'{len(flat_vectors)}d', *flat_vectors)
                        data_array.text = base64.b64encode(binary_data).decode('ascii')

        # Write to file with pretty printing
        xml_str = ET.tostring(root, encoding='unicode')
        dom = minidom.parseString(xml_str)
        pretty_xml = dom.toprettyxml(indent='  ')

        # Remove extra blank lines
        lines = [line for line in pretty_xml.split('\n') if line.strip()]
        self.file.write('\n'.join(lines))

    def _write_vtk_legacy(self, mesh: MeshData,
                          scalar_data: Optional[Dict[str, List[float]]] = None,
                          vector_data: Optional[Dict[str, List[List[float]]]] = None):
        """Write legacy VTK format (.vtk)"""

        # Header
        self.file.write("# vtk DataFile Version 3.0\n")
        self.file.write("KooMeshGenerator VTK Export\n")
        self.file.write("ASCII\n")
        self.file.write("DATASET UNSTRUCTURED_GRID\n")

        # Points
        self.file.write(f"\nPOINTS {mesh.num_nodes()} double\n")
        for node_id in sorted(mesh.nodes.keys()):
            node = mesh.nodes[node_id]
            self.file.write(f"{node.x:.8e} {node.y:.8e} {node.z:.8e}\n")

        # Cells
        total_size = sum(len(elem.nodes) + 1 for elem in mesh.elements.values())
        self.file.write(f"\nCELLS {mesh.num_elements()} {total_size}\n")

        for elem in mesh.elements.values():
            # Convert 1-based to 0-based indexing
            nodes_0based = [nid - 1 for nid in elem.nodes]
            self.file.write(f"{len(nodes_0based)} " + ' '.join(str(n) for n in nodes_0based) + "\n")

        # Cell types
        vtk_type = self.VTK_CELL_TYPES.get(mesh.element_type)
        if vtk_type is None:
            raise ValueError(f"Element type {mesh.element_type.code} not supported in VTK export")

        self.file.write(f"\nCELL_TYPES {mesh.num_elements()}\n")
        for _ in range(mesh.num_elements()):
            self.file.write(f"{vtk_type}\n")

        # Point data (optional)
        if scalar_data or vector_data:
            self.file.write(f"\nPOINT_DATA {mesh.num_nodes()}\n")

            if scalar_data:
                for name, values in scalar_data.items():
                    self.file.write(f"\nSCALARS {name} double 1\n")
                    self.file.write("LOOKUP_TABLE default\n")
                    for value in values:
                        self.file.write(f"{value:.8e}\n")

            if vector_data:
                for name, vectors in vector_data.items():
                    self.file.write(f"\nVECTORS {name} double\n")
                    for vec in vectors:
                        self.file.write(f"{vec[0]:.8e} {vec[1]:.8e} {vec[2]:.8e}\n")

    @staticmethod
    def write_simple(mesh: MeshData, output_path: str, format: str = 'xml'):
        """
        Convenience method to write mesh without context manager

        Args:
            mesh: Mesh data to export
            output_path: Output file path
            format: 'xml' for .vtu or 'legacy' for .vtk
        """
        with VTKWriter(output_path, format=format) as writer:
            writer.write_mesh(mesh)
