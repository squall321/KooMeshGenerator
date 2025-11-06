"""
Universal File Format (UNV) Export Writer
==========================================

This module provides functionality to export mesh data to Universal File Format (.unv).

Universal File Format is a widely-used ASCII-based format originating from I-DEAS
and supported by many FEA tools:
- ANSYS
- ABAQUS
- Nastran
- Femap
- Patran
- Many others

Format Structure:
- Dataset-based format
- Each dataset starts with -1 and ends with -1
- Dataset numbers define data type (e.g., 2411=nodes, 2412=elements)

Key Datasets:
- 2411: Nodes (coordinates)
- 2412: Elements (connectivity)
- 2467: Groups (node/element sets)
- 164: Units
- 2414: Analysis data

Author: KooMeshGenerator Development Team
"""

import logging
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime

from koomesh.meshing.mesh_data import MeshData, ElementType


class UNVWriter:
    """
    Writer for Universal File Format (.unv)

    Universal File Format is a dataset-based ASCII format widely supported
    by FEA pre/post processors.

    Element type mapping (UNV element IDs):
    - HEX8 → 115 (Solid Brick 8-node)
    - HEX20 → 116 (Solid Brick 20-node)
    - TET4 → 111 (Solid Tetrahedron 4-node)
    - TET10 → 118 (Solid Tetrahedron 10-node)
    - PRISM6 → 112 (Solid Wedge 6-node)
    - PYRAMID5 → 117 (Solid Pyramid 5-node)

    Usage:
        with UNVWriter('output.unv') as writer:
            writer.write_complete_model(mesh)
    """

    # UNV element type IDs
    UNV_ELEMENT_TYPES = {
        ElementType.HEX8: 115,      # Solid Brick 8-node
        ElementType.HEX20: 116,     # Solid Brick 20-node
        ElementType.HEX27: 116,     # Map to 20-node (UNV doesn't have 27-node)
        ElementType.TET4: 111,      # Solid Tetrahedron 4-node
        ElementType.TET10: 118,     # Solid Tetrahedron 10-node
        ElementType.PRISM6: 112,    # Solid Wedge 6-node
        ElementType.PYRAMID5: 117,  # Solid Pyramid 5-node
    }

    def __init__(self, output_path: str, units: str = "SI"):
        """
        Initialize UNV writer

        Args:
            output_path: Output file path (.unv)
            units: Unit system ("SI", "Imperial", or "User-defined")
        """
        self.output_path = Path(output_path)
        self.units = units
        self.file = None

        self.logger = logging.getLogger(__name__)

        # Ensure .unv extension
        if self.output_path.suffix.lower() != '.unv':
            self.logger.warning(f"UNV files should use .unv extension, got {self.output_path.suffix}")

    def __enter__(self):
        """Context manager entry"""
        self.file = open(self.output_path, 'w')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.file:
            self.file.close()

    def _write_dataset_header(self, dataset_num: int):
        """Write dataset header marker"""
        self.file.write("    -1\n")
        self.file.write(f"  {dataset_num}\n")

    def _write_dataset_footer(self):
        """Write dataset footer marker"""
        self.file.write("    -1\n")

    def write_header(self, title: str = "KooMeshGenerator UNV Export",
                     comments: Optional[List[str]] = None):
        """
        Write file header with comments

        Args:
            title: Model title
            comments: Optional list of comment strings
        """
        # File header comment (not a dataset, just comments)
        self.file.write(f"$ {title}\n")
        self.file.write(f"$ Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        if comments:
            for comment in comments:
                self.file.write(f"$ {comment}\n")

        self.file.write("$\n")

    def write_units(self, unit_code: int = 1):
        """
        Write Dataset 164: Units

        Args:
            unit_code: Unit code (1=SI, 2=Imperial, etc.)
        """
        self._write_dataset_header(164)

        # Line 1: unit_code
        # 1 = SI (m, kg, N, s, K)
        # 2 = Imperial (in, lbf, s, °F)
        self.file.write(f"  {unit_code}\n")

        # Line 2-10: Unit factors (all 1.0 for standard units)
        for _ in range(9):
            self.file.write("  1.000000000000000E+00\n")

        # Line 11: Temperature mode (1=Absolute, 2=Relative)
        self.file.write("         1\n")

        self._write_dataset_footer()

    def write_nodes(self, mesh: MeshData):
        """
        Write Dataset 2411: Nodes

        Format:
        Line 1: node_label, export_coord_sys, displacement_coord_sys, color
        Line 2-4: x, y, z coordinates (3 lines)
        """
        self._write_dataset_header(2411)

        for node_id in sorted(mesh.nodes.keys()):
            node = mesh.nodes[node_id]

            # Line 1: node_label (10), coord_sys (3), disp_coord_sys (3), color (11)
            self.file.write(f"{node_id:10d}{1:10d}{1:10d}{1:10d}\n")

            # Lines 2-4: coordinates (one per line, E format)
            self.file.write(f"{node.x:25.16E}\n")
            self.file.write(f"{node.y:25.16E}\n")
            self.file.write(f"{node.z:25.16E}\n")

        self._write_dataset_footer()
        self.logger.info(f"Wrote {mesh.num_nodes()} nodes")

    def write_elements(self, mesh: MeshData):
        """
        Write Dataset 2412: Elements

        Format:
        Line 1: element_label, fe_descriptor_id, physical_property_table,
                material_property_table, color, num_nodes
        Line 2+: node labels (up to 8 per line)
        """
        self._write_dataset_header(2412)

        unv_type = self.UNV_ELEMENT_TYPES.get(mesh.element_type)
        if unv_type is None:
            raise ValueError(f"Element type {mesh.element_type.code} not supported in UNV export")

        for elem in mesh.elements.values():
            num_nodes = len(elem.nodes)

            # Line 1: elem_label, fe_descriptor, phys_prop, mat_prop, color, num_nodes
            self.file.write(f"{elem.id:10d}{unv_type:10d}{1:10d}{1:10d}{7:10d}{num_nodes:10d}\n")

            # Write node connectivity (8 nodes per line)
            nodes = elem.nodes
            for i in range(0, len(nodes), 8):
                line_nodes = nodes[i:i+8]
                line = ''.join(f"{nid:10d}" for nid in line_nodes)
                self.file.write(line + "\n")

        self._write_dataset_footer()
        self.logger.info(f"Wrote {mesh.num_elements()} elements")

    def write_groups(self, group_name: str, entity_type: str, entity_ids: List[int]):
        """
        Write Dataset 2467: Permanent Groups

        Args:
            group_name: Name of the group
            entity_type: "NODE" or "ELEMENT"
            entity_ids: List of node or element IDs
        """
        self._write_dataset_header(2467)

        # Line 1: Group number (just use 1 for simplicity)
        self.file.write("         1\n")

        # Line 2: Active constraint set, active restraint set, active load set, etc. (all 0)
        for _ in range(7):
            self.file.write("         0")
        self.file.write("\n")

        # Line 3: Group name (max 80 characters)
        self.file.write(f"{group_name:<80s}\n")

        # Line 4-6: Entity type codes
        # 8 fields per line, 3 lines total (24 fields)
        # Field 1: 7=node, 8=element
        entity_code = 7 if entity_type.upper() == "NODE" else 8

        # Line 4: entity type codes 1-8
        self.file.write(f"{entity_code:10d}")
        for _ in range(7):
            self.file.write(f"{0:10d}")
        self.file.write("\n")

        # Lines 5-6: remaining codes (all 0)
        for _ in range(2):
            for _ in range(8):
                self.file.write(f"{0:10d}")
            self.file.write("\n")

        # Line 7-9: Entity counts for each type
        # We only use first position
        self.file.write(f"{len(entity_ids):10d}")
        for _ in range(7):
            self.file.write(f"{0:10d}")
        self.file.write("\n")

        for _ in range(2):
            for _ in range(8):
                self.file.write(f"{0:10d}")
            self.file.write("\n")

        # Write entity IDs (2 per line)
        for i in range(0, len(entity_ids), 2):
            if i + 1 < len(entity_ids):
                self.file.write(f"{entity_type[:1].upper():1s}{entity_ids[i]:10d}{entity_type[:1].upper():1s}{entity_ids[i+1]:10d}{0:10d}{0:10d}\n")
            else:
                self.file.write(f"{entity_type[:1].upper():1s}{entity_ids[i]:10d}{0:10d}{0:10d}{0:10d}{0:10d}\n")

        self._write_dataset_footer()
        self.logger.info(f"Wrote group '{group_name}' with {len(entity_ids)} entities")

    def write_complete_model(self, mesh: MeshData,
                           title: str = "Model",
                           unit_code: int = 1):
        """
        Write complete mesh model to UNV file

        Args:
            mesh: Mesh data to export
            title: Model title
            unit_code: Unit code (1=SI, 2=Imperial)
        """
        self.write_header(title)
        self.write_units(unit_code)
        self.write_nodes(mesh)
        self.write_elements(mesh)

        self.logger.info(f"Wrote complete model to {self.output_path}")

    @staticmethod
    def write_simple(mesh: MeshData, output_path: str, title: str = "Model"):
        """
        Convenience method to write mesh without context manager

        Args:
            mesh: Mesh data to export
            output_path: Output file path
            title: Model title
        """
        with UNVWriter(output_path) as writer:
            writer.write_complete_model(mesh, title)
