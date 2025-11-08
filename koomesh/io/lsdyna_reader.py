"""
LS-DYNA Keyword File Reader
============================

Read and parse LS-DYNA keyword (.k) files to reconstruct MeshData.

Supported keywords:
- *NODE: Node definitions
- *ELEMENT_SOLID: Solid element definitions (TET4, HEX8, etc.)
- *PART: Part information

Author: KooMeshGenerator Team
"""

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from koomesh.meshing.mesh_data import MeshData, ElementType, Node, Element

logger = logging.getLogger(__name__)


class LSDynaReader:
    """
    Read LS-DYNA keyword files and reconstruct MeshData

    Example:
        >>> reader = LSDynaReader()
        >>> mesh_data = reader.read_file("mesh.k")
        >>> print(f"Loaded {len(mesh_data.nodes)} nodes, {len(mesh_data.elements)} elements")
    """

    # Element type mapping: (num_nodes) -> ElementType
    ELEMENT_TYPE_MAP = {
        4: ElementType.TET4,
        5: ElementType.PYRAMID5,
        6: ElementType.PRISM6,
        8: ElementType.HEX8,
        10: ElementType.TET10,
        20: ElementType.HEX20,
        27: ElementType.HEX27,
    }

    def __init__(self):
        """Initialize LS-DYNA reader"""
        self.logger = logging.getLogger(__name__)

    def read_file(self, filename: str) -> MeshData:
        """
        Read LS-DYNA keyword file and return MeshData

        Args:
            filename: Path to LS-DYNA keyword file

        Returns:
            MeshData object reconstructed from file

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid

        Example:
            >>> reader = LSDynaReader()
            >>> mesh = reader.read_file("crash_mesh.k")
        """
        filepath = Path(filename)
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filename}")

        self.logger.info(f"Reading LS-DYNA keyword file: {filename}")

        # Parse file
        nodes, elements, parts = self._parse_file(filepath)

        if not nodes:
            raise ValueError(f"No nodes found in file: {filename}")
        if not elements:
            raise ValueError(f"No elements found in file: {filename}")

        # Determine element type from first element
        first_element = next(iter(elements.values()))
        element_type = first_element.type

        # Check if all elements are the same type
        mixed_types = False
        for elem in elements.values():
            if elem.type != element_type:
                mixed_types = True
                break

        if mixed_types:
            self.logger.warning("Mesh contains mixed element types. Using type of first element.")

        # Create MeshData
        mesh_data = MeshData(element_type=element_type)
        mesh_data.nodes = nodes
        mesh_data.elements = elements
        mesh_data.parts = parts

        self.logger.info(
            f"Loaded mesh: {len(nodes)} nodes, {len(elements)} elements, "
            f"{len(parts)} parts, type={element_type.code}"
        )

        return mesh_data

    def _parse_file(self, filepath: Path) -> Tuple[Dict[int, Node], Dict[int, Element], Dict]:
        """
        Parse LS-DYNA keyword file

        Returns:
            Tuple of (nodes_dict, elements_dict, parts_dict)
        """
        nodes = {}
        elements = {}
        parts = {}

        current_section = None
        section_data = []

        with open(filepath, 'r') as f:
            for line in f:
                # Check for keyword (starts with *)
                if line.startswith('*'):
                    # Process previous section if any
                    if current_section and section_data:
                        self._process_section(current_section, section_data, nodes, elements, parts)
                        section_data = []

                    # Start new section
                    keyword = line.strip().upper()

                    if keyword.startswith('*NODE'):
                        current_section = 'NODE'
                    elif keyword.startswith('*ELEMENT_SOLID'):
                        current_section = 'ELEMENT_SOLID'
                    elif keyword.startswith('*PART'):
                        current_section = 'PART'
                    else:
                        current_section = None

                elif current_section:
                    # Collect data lines for current section
                    stripped = line.strip()
                    if stripped and not stripped.startswith('$'):  # Skip empty lines and comments
                        section_data.append(line)

        # Process last section
        if current_section and section_data:
            self._process_section(current_section, section_data, nodes, elements, parts)

        return nodes, elements, parts

    def _process_section(
        self,
        section_type: str,
        data_lines: List[str],
        nodes: Dict[int, Node],
        elements: Dict[int, Element],
        parts: Dict
    ):
        """Process a keyword section"""
        if section_type == 'NODE':
            self._parse_nodes(data_lines, nodes)
        elif section_type == 'ELEMENT_SOLID':
            self._parse_elements(data_lines, elements)
        elif section_type == 'PART':
            self._parse_part(data_lines, parts)

    def _parse_nodes(self, lines: List[str], nodes: Dict[int, Node]):
        """
        Parse *NODE section

        Format (free format or fixed):
        node_id, x, y, z
        """
        for line in lines:
            try:
                # Try comma-separated first
                if ',' in line:
                    parts = [p.strip() for p in line.split(',')]
                else:
                    # Fixed format: columns
                    parts = line.split()

                if len(parts) >= 4:
                    node_id = int(parts[0])
                    x = float(parts[1])
                    y = float(parts[2])
                    z = float(parts[3])

                    nodes[node_id] = Node(id=node_id, x=x, y=y, z=z)

            except (ValueError, IndexError) as e:
                self.logger.warning(f"Failed to parse node line: {line.strip()} - {e}")

    def _parse_elements(self, lines: List[str], elements: Dict[int, Element]):
        """
        Parse *ELEMENT_SOLID section

        Format (free format or fixed):
        elem_id, part_id, n1, n2, n3, n4, [n5, n6, n7, n8, ...]
        """
        for line in lines:
            try:
                # Try comma-separated first
                if ',' in line:
                    parts = [p.strip() for p in line.split(',')]
                else:
                    # Fixed format: columns
                    parts = line.split()

                if len(parts) >= 6:  # At least elem_id, part_id, and 4 nodes (TET4)
                    elem_id = int(parts[0])
                    part_id = int(parts[1])

                    # Node connectivity starts from index 2
                    node_ids = [int(p) for p in parts[2:] if p.strip()]

                    # Determine element type from number of nodes
                    num_nodes = len(node_ids)
                    element_type = self.ELEMENT_TYPE_MAP.get(num_nodes)

                    if element_type is None:
                        self.logger.warning(
                            f"Unknown element type with {num_nodes} nodes for element {elem_id}"
                        )
                        continue

                    elements[elem_id] = Element(
                        id=elem_id,
                        type=element_type,
                        nodes=node_ids,
                        part_id=part_id
                    )

            except (ValueError, IndexError) as e:
                self.logger.warning(f"Failed to parse element line: {line.strip()} - {e}")

    def _parse_part(self, lines: List[str], parts: Dict):
        """
        Parse *PART section

        Format:
        part_name
        part_id, section_id, material_id
        """
        if len(lines) >= 2:
            part_name = lines[0].strip()

            try:
                # Parse part definition line
                if ',' in lines[1]:
                    parts_line = [p.strip() for p in lines[1].split(',')]
                else:
                    parts_line = lines[1].split()

                if len(parts_line) >= 1:
                    part_id = int(parts_line[0])

                    parts[part_id] = {
                        'name': part_name,
                        'id': part_id,
                        'section_id': int(parts_line[1]) if len(parts_line) > 1 else None,
                        'material_id': int(parts_line[2]) if len(parts_line) > 2 else None,
                    }

            except (ValueError, IndexError) as e:
                self.logger.warning(f"Failed to parse part: {e}")

    def get_file_info(self, filename: str) -> Dict:
        """
        Get basic information about LS-DYNA file without full parsing

        Args:
            filename: Path to LS-DYNA keyword file

        Returns:
            Dictionary with file statistics

        Example:
            >>> reader = LSDynaReader()
            >>> info = reader.get_file_info("mesh.k")
            >>> print(f"File has {info['num_nodes']} nodes")
        """
        filepath = Path(filename)
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filename}")

        info = {
            'filename': str(filepath),
            'size_bytes': filepath.stat().st_size,
            'num_nodes': 0,
            'num_elements': 0,
            'num_parts': 0,
            'keywords': []
        }

        with open(filepath, 'r') as f:
            in_node_section = False
            in_element_section = False

            for line in f:
                if line.startswith('*'):
                    keyword = line.strip().upper()
                    info['keywords'].append(keyword)

                    in_node_section = keyword.startswith('*NODE')
                    in_element_section = keyword.startswith('*ELEMENT')

                    if keyword.startswith('*PART'):
                        info['num_parts'] += 1

                elif in_node_section:
                    if line.strip() and not line.strip().startswith('$'):
                        info['num_nodes'] += 1

                elif in_element_section:
                    if line.strip() and not line.strip().startswith('$'):
                        info['num_elements'] += 1

        return info


def read_lsdyna_file(filename: str) -> MeshData:
    """
    Convenience function to read LS-DYNA file

    Args:
        filename: Path to LS-DYNA keyword file

    Returns:
        MeshData object

    Example:
        >>> from koomesh.io.lsdyna_reader import read_lsdyna_file
        >>> mesh = read_lsdyna_file("mesh.k")
    """
    reader = LSDynaReader()
    return reader.read_file(filename)
