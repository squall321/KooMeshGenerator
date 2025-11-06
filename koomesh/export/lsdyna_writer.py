"""
LS-DYNA Keyword Writer
======================

This module exports meshes and contacts to LS-DYNA keyword format.

Features:
- NODE keyword
- ELEMENT_SOLID keyword
- PART keyword
- SECTION_SOLID keyword
- CONTACT keywords (TIED, SURFACE_TO_SURFACE, AUTOMATIC)
- Include file generation

Usage:
    >>> from koomesh.export.lsdyna_writer import LSDynaWriter
    >>> writer = LSDynaWriter('output.k')
    >>> writer.write_mesh(mesh, contacts, hierarchy)
"""

import logging
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime

from koomesh.meshing.mesh_data import MeshData
from koomesh.contact.contact_data import ContactPair, ContactType
from koomesh.io.hierarchy_parser import HierarchyNode


class LSDynaWriter:
    """
    LS-DYNA keyword file writer

    This class writes mesh data and contacts to LS-DYNA keyword format.

    Attributes:
        output_path: Output file path
        precision: Float precision ('single' or 'double')
        logger: Logger instance

    Example:
        >>> writer = LSDynaWriter('model.k', precision='double')
        >>> writer.write_header()
        >>> writer.write_nodes(mesh)
        >>> writer.write_elements(mesh)
        >>> writer.write_contacts(contacts)
        >>> writer.finalize()
    """

    def __init__(self,
                 output_path: str,
                 precision: str = 'double'):
        """
        Initialize LS-DYNA writer

        Args:
            output_path: Output file path
            precision: Float precision ('single' or 'double')
        """
        self.output_path = Path(output_path)
        self.precision = precision
        self.logger = logging.getLogger(__name__)

        self.file = None
        self._node_id_offset = 0
        self._element_id_offset = 0

    def __enter__(self):
        """Context manager entry"""
        self.file = open(self.output_path, 'w')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.file:
            self.file.close()

    def write_header(self):
        """Write file header"""
        self.file.write("*KEYWORD\n")
        self.file.write("$# ============================================================\n")
        self.file.write("$# KooMeshGenerator - Automated Mesh Generation\n")
        self.file.write(f"$# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        self.file.write(f"$# Precision: {self.precision}\n")
        self.file.write("$# ============================================================\n")
        self.file.write("$\n")

        self.logger.debug("Wrote header")

    def write_nodes(self, mesh: MeshData):
        """
        Write NODE keyword

        Args:
            mesh: Mesh containing nodes
        """
        self.file.write("*NODE\n")
        self.file.write("$#   nid               x               y               z      tc      rc\n")

        format_str = self._get_node_format()

        for node in mesh.nodes.values():
            line = format_str.format(
                nid=node.id,
                x=node.x,
                y=node.y,
                z=node.z
            )
            self.file.write(line + "\n")

        self.logger.info(f"Wrote {mesh.num_nodes()} nodes")

    def _get_node_format(self) -> str:
        """Get format string for node output"""
        if self.precision == 'double':
            return "{nid:8d}{x:16.8e}{y:16.8e}{z:16.8e}"
        else:
            return "{nid:8d}{x:12.5e}{y:12.5e}{z:12.5e}"

    def write_elements(self, mesh: MeshData, part_id: int = 1):
        """
        Write ELEMENT_SOLID keyword

        Args:
            mesh: Mesh containing elements
            part_id: Part ID for elements
        """
        if mesh.element_type.is_hex():
            self._write_hex_elements(mesh, part_id)
        elif mesh.element_type.is_tet():
            self._write_tet_elements(mesh, part_id)
        else:
            self.logger.warning(f"Element type {mesh.element_type.code} not fully supported")
            self._write_hex_elements(mesh, part_id)  # Fallback

    def _write_hex_elements(self, mesh: MeshData, part_id: int):
        """Write hexahedral elements"""
        from koomesh.meshing.mesh_data import ElementType

        self.file.write("*ELEMENT_SOLID\n")

        if mesh.element_type == ElementType.HEX8:
            self.file.write("$#   eid     pid      n1      n2      n3      n4      n5      n6      n7      n8\n")
            for elem in mesh.elements.values():
                self.file.write(f"{elem.id:8d}{part_id:8d}")
                for nid in elem.nodes:
                    self.file.write(f"{nid:8d}")
                self.file.write("\n")

        elif mesh.element_type == ElementType.HEX20:
            self.file.write("$# HEX20: 20-node hexahedron (quadratic)\n")
            self.file.write("$#   eid     pid      n1      n2      n3      n4      n5      n6      n7      n8\n")
            for elem in mesh.elements.values():
                # Line 1: eid, pid, n1-n8 (corner nodes)
                self.file.write(f"{elem.id:8d}{part_id:8d}")
                for nid in elem.nodes[0:8]:
                    self.file.write(f"{nid:8d}")
                self.file.write("\n")
                # Line 2: n9-n16 (mid-side nodes)
                self.file.write(" " * 16)  # Blank for eid and pid
                for nid in elem.nodes[8:16]:
                    self.file.write(f"{nid:8d}")
                self.file.write("\n")
                # Line 3: n17-n20 (remaining mid-side nodes)
                self.file.write(" " * 16)
                for nid in elem.nodes[16:20]:
                    self.file.write(f"{nid:8d}")
                self.file.write("\n")

        elif mesh.element_type == ElementType.HEX27:
            self.file.write("$# HEX27: 27-node hexahedron (quadratic, full)\n")
            self.file.write("$#   eid     pid      n1      n2      n3      n4      n5      n6      n7      n8\n")
            for elem in mesh.elements.values():
                # Line 1: eid, pid, n1-n8 (corner nodes)
                self.file.write(f"{elem.id:8d}{part_id:8d}")
                for nid in elem.nodes[0:8]:
                    self.file.write(f"{nid:8d}")
                self.file.write("\n")
                # Line 2: n9-n16 (mid-side nodes)
                self.file.write(" " * 16)
                for nid in elem.nodes[8:16]:
                    self.file.write(f"{nid:8d}")
                self.file.write("\n")
                # Line 3: n17-n24 (more mid-side nodes)
                self.file.write(" " * 16)
                for nid in elem.nodes[16:24]:
                    self.file.write(f"{nid:8d}")
                self.file.write("\n")
                # Line 4: n25-n27 (face center and volume center nodes)
                self.file.write(" " * 16)
                for nid in elem.nodes[24:27]:
                    self.file.write(f"{nid:8d}")
                self.file.write("\n")

        else:
            self.logger.warning(f"Unsupported hex element type: {mesh.element_type.code}")

        self.logger.info(f"Wrote {mesh.num_elements()} hexahedral elements ({mesh.element_type.code})")

    def _write_tet_elements(self, mesh: MeshData, part_id: int):
        """Write tetrahedral elements"""
        from koomesh.meshing.mesh_data import ElementType

        self.file.write("*ELEMENT_SOLID\n")

        if mesh.element_type == ElementType.TET4:
            self.file.write("$#   eid     pid      n1      n2      n3      n4      n5      n6      n7      n8\n")
            for elem in mesh.elements.values():
                self.file.write(f"{elem.id:8d}{part_id:8d}")
                # For tet4, write 4 nodes + repeat last node for remaining positions
                for nid in elem.nodes:
                    self.file.write(f"{nid:8d}")
                # Fill remaining positions with last node (LS-DYNA convention)
                last_node = elem.nodes[-1]
                for _ in range(8 - len(elem.nodes)):
                    self.file.write(f"{last_node:8d}")
                self.file.write("\n")

        elif mesh.element_type == ElementType.TET10:
            self.file.write("$# TET10: 10-node tetrahedron (quadratic)\n")
            self.file.write("$#   eid     pid      n1      n2      n3      n4      n5      n6      n7      n8\n")
            for elem in mesh.elements.values():
                # Line 1: eid, pid, n1-n4 (corner nodes) + n5-n8 (first 4 mid-side nodes)
                self.file.write(f"{elem.id:8d}{part_id:8d}")
                for nid in elem.nodes[0:8]:
                    self.file.write(f"{nid:8d}")
                self.file.write("\n")
                # Line 2: n9-n10 (remaining mid-side nodes)
                self.file.write(" " * 16)  # Blank for eid and pid
                for nid in elem.nodes[8:10]:
                    self.file.write(f"{nid:8d}")
                self.file.write("\n")

        else:
            self.logger.warning(f"Unsupported tet element type: {mesh.element_type.code}")

        self.logger.info(f"Wrote {mesh.num_elements()} tetrahedral elements ({mesh.element_type.code})")

    def write_parts(self, hierarchy: HierarchyNode):
        """
        Write PART keywords

        Args:
            hierarchy: Hierarchy tree
        """
        # Flatten hierarchy to get all parts
        parts = self._flatten_hierarchy(hierarchy)

        for i, node in enumerate(parts, start=1):
            self.file.write("*PART\n")
            self.file.write(f"${node.name}\n")
            self.file.write("$#     pid     secid       mid     eosid      hgid      grav    adpopt      tmid\n")
            self.file.write(f"{i:10d}{i:10d}         1         0         0         0         0         0\n")

        self.logger.info(f"Wrote {len(parts)} parts")

    def _flatten_hierarchy(self, root: HierarchyNode) -> List[HierarchyNode]:
        """Flatten hierarchy to list"""
        result = []
        if root.is_leaf():
            result.append(root)
        for child in root.children:
            result.extend(self._flatten_hierarchy(child))
        return result

    def write_sections(self, num_parts: int):
        """
        Write SECTION_SOLID keywords

        Args:
            num_parts: Number of parts/sections
        """
        for i in range(1, num_parts + 1):
            self.file.write("*SECTION_SOLID\n")
            self.file.write(f"$# Section {i}\n")
            self.file.write("$#   secid    elform       aet\n")
            self.file.write(f"{i:10d}         1         0\n")

        self.logger.info(f"Wrote {num_parts} sections")

    def write_material(self, mat_id: int = 1):
        """
        Write basic MAT_ELASTIC material

        Args:
            mat_id: Material ID
        """
        self.file.write("*MAT_ELASTIC\n")
        self.file.write("$#     mid        ro         e        pr        da        db  not used\n")
        self.file.write(f"{mat_id:10d}  7.85e-09  2.00e+05      0.30         0         0\n")

        self.logger.debug(f"Wrote material {mat_id}")

    def write_contacts(self, contacts: List[ContactPair]):
        """
        Write CONTACT keywords

        Args:
            contacts: List of contact pairs
        """
        for i, contact in enumerate(contacts, start=1):
            if contact.contact_type == ContactType.TIED:
                self._write_tied_contact(contact, i)
            elif contact.contact_type == ContactType.SURFACE_TO_SURFACE:
                self._write_surface_contact(contact, i)
            elif contact.contact_type == ContactType.AUTOMATIC:
                self._write_automatic_contact(contact, i)
            else:
                self.logger.warning(f"Unknown contact type: {contact.contact_type}")

        self.logger.info(f"Wrote {len(contacts)} contacts")

    def _write_tied_contact(self, contact: ContactPair, cid: int):
        """Write CONTACT_TIED_SURFACE_TO_SURFACE"""
        self.file.write("*CONTACT_TIED_SURFACE_TO_SURFACE\n")
        self.file.write("$#     cid                                                                 title\n")
        title = f"Tied: {contact.get_master_part()} - {contact.get_slave_part()}"
        self.file.write(f"{cid:10d}{title}\n")
        self.file.write("$#    ssid      msid     sstyp     mstyp    sboxid    mboxid       spr       mpr\n")

        # Use part IDs for slave and master
        ssid = contact.slave_surface.part_id
        msid = contact.master_surface.part_id

        self.file.write(f"{ssid:10d}{msid:10d}         3         3         0         0         0         0\n")
        self.file.write("$#      fs        fd        dc        vc       vdc    penchk        bt        dt\n")
        self.file.write("       0.0       0.0       0.0       0.0       0.0         0       0.0   1.0E+20\n")

    def _write_surface_contact(self, contact: ContactPair, cid: int):
        """Write CONTACT_AUTOMATIC_SURFACE_TO_SURFACE"""
        self.file.write("*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE\n")
        self.file.write("$#     cid                                                                 title\n")
        title = f"Contact: {contact.get_master_part()} - {contact.get_slave_part()}"
        self.file.write(f"{cid:10d}{title}\n")
        self.file.write("$#    ssid      msid     sstyp     mstyp    sboxid    mboxid       spr       mpr\n")

        ssid = contact.slave_surface.part_id
        msid = contact.master_surface.part_id

        self.file.write(f"{ssid:10d}{msid:10d}         3         3         0         0         0         0\n")
        self.file.write("$#      fs        fd        dc        vc       vdc    penchk        bt        dt\n")
        self.file.write(f"{contact.friction:10.3f}       0.0       0.0       0.0       0.0         0       0.0   1.0E+20\n")

    def _write_automatic_contact(self, contact: ContactPair, cid: int):
        """Write CONTACT_AUTOMATIC_GENERAL"""
        self.file.write("*CONTACT_AUTOMATIC_GENERAL\n")
        self.file.write("$#     cid                                                                 title\n")
        title = f"Auto: {contact.get_master_part()} - {contact.get_slave_part()}"
        self.file.write(f"{cid:10d}{title}\n")
        self.file.write("$#    ssid      msid     sstyp     mstyp    sboxid    mboxid       spr       mpr\n")

        ssid = contact.slave_surface.part_id
        msid = contact.master_surface.part_id

        self.file.write(f"{ssid:10d}{msid:10d}         3         3         0         0         0         0\n")
        self.file.write("$#      fs        fd        dc        vc       vdc    penchk        bt        dt\n")
        self.file.write(f"{contact.friction:10.3f}       0.0       0.0       0.0       0.0         0       0.0   1.0E+20\n")

    def finalize(self):
        """Write file footer"""
        self.file.write("$\n")
        self.file.write("$# ============================================================\n")
        self.file.write("$# End of file\n")
        self.file.write("$# ============================================================\n")
        self.file.write("*END\n")

        self.logger.info(f"Finalized LS-DYNA file: {self.output_path}")

    def write_complete_model(self,
                            meshes: List[MeshData],
                            contacts: List[ContactPair],
                            hierarchy: HierarchyNode):
        """
        Write complete model to file

        Convenience method that writes everything in order.

        Args:
            meshes: List of meshes
            contacts: List of contacts
            hierarchy: Hierarchy tree
        """
        self.logger.info("Writing complete LS-DYNA model...")

        self.write_header()

        # Write nodes from all meshes
        for mesh in meshes:
            self.write_nodes(mesh)

        # Write elements from all meshes
        for i, mesh in enumerate(meshes, start=1):
            self.write_elements(mesh, part_id=i)

        # Write parts
        self.write_parts(hierarchy)

        # Write sections
        num_parts = len(self._flatten_hierarchy(hierarchy))
        self.write_sections(num_parts)

        # Write material
        self.write_material()

        # Write contacts
        if contacts:
            self.write_contacts(contacts)

        # Finalize
        self.finalize()

        self.logger.info("Complete model written successfully")


def export_to_lsdyna(meshes: List[MeshData],
                    contacts: List[ContactPair],
                    hierarchy: HierarchyNode,
                    output_path: str) -> Path:
    """
    Export meshes and contacts to LS-DYNA format

    Convenience function for exporting.

    Args:
        meshes: List of meshes
        contacts: List of contacts
        hierarchy: Hierarchy tree
        output_path: Output file path

    Returns:
        Path to output file

    Example:
        >>> path = export_to_lsdyna(meshes, contacts, hierarchy, 'output.k')
        >>> print(f"Exported to: {path}")
    """
    with LSDynaWriter(output_path) as writer:
        writer.write_complete_model(meshes, contacts, hierarchy)

    return Path(output_path)
