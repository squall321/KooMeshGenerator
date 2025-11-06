"""
Gmsh MSH Format Import/Export
==============================

This module provides functionality to import and export mesh data in Gmsh MSH format.

Gmsh is a popular open-source mesh generator, and the .msh format is widely supported
by many FEA and CFD tools.

Supported Versions:
- MSH 2.2: ASCII format (most widely compatible)
- MSH 4.1: Modern ASCII format with improved structure

Key Features:
- Direct file parsing (no gmsh library dependency)
- Read and write MSH files
- Support for physical groups
- Element type conversion
- Binary format support (future)

Format Details:
- Storage: ASCII text format
- Sections: $MeshFormat, $Nodes, $Elements, $PhysicalNames
- Element types: 20+ types supported
- Applications: Gmsh, GetDP, Code_Aster, etc.

Supported Element Types:
- TET4: 4-node tetrahedron (type 4)
- TET10: 10-node tetrahedron (type 11)
- HEX8: 8-node hexahedron (type 5)
- HEX20: 20-node hexahedron (type 17)
- HEX27: 27-node hexahedron (type 12)
- PRISM6: 6-node prism (type 6)
- PYRAMID5: 5-node pyramid (type 7)

Usage (Export):
    >>> from koomesh.export.gmsh_writer import GmshWriter
    >>> from koomesh.meshing.mesh_data import MeshData
    >>>
    >>> # Create and populate mesh
    >>> mesh = MeshData()
    >>> # ... add nodes and elements ...
    >>>
    >>> # Export to Gmsh MSH format
    >>> with GmshWriter("output.msh", version="2.2") as writer:
    ...     writer.write_mesh(mesh)

Usage (Import):
    >>> from koomesh.import_module.gmsh_reader import GmshReader
    >>>
    >>> # Import from Gmsh MSH file
    >>> with GmshReader("input.msh") as reader:
    ...     mesh = reader.read_mesh()

Author: KooMeshGenerator Team
License: MIT
"""

import logging
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from enum import Enum

from koomesh.meshing.mesh_data import MeshData, ElementType


class MshVersion(Enum):
    """Gmsh MSH file format versions"""
    V2_2 = "2.2"
    V4_1 = "4.1"


class GmshError(Exception):
    """Exception raised for Gmsh MSH format errors"""
    pass


class GmshWriter:
    """
    Gmsh MSH format writer

    Exports mesh data to Gmsh MSH ASCII format.

    Attributes:
        filepath: Path to output file
        version: MSH format version ("2.2" or "4.1")

    Example:
        >>> writer = GmshWriter("mesh.msh", version="2.2")
        >>> with writer:
        ...     writer.write_mesh(mesh_data)
    """

    # Gmsh MSH element type numbers (version 2.2/4.1)
    GMSH_ELEMENT_TYPES = {
        ElementType.TET4: 4,
        ElementType.HEX8: 5,
        ElementType.PRISM6: 6,
        ElementType.PYRAMID5: 7,
        ElementType.TET10: 11,
        ElementType.HEX27: 12,
        ElementType.HEX20: 17,
    }

    # Number of nodes per element type
    NODES_PER_ELEMENT = {
        ElementType.TET4: 4,
        ElementType.TET10: 10,
        ElementType.HEX8: 8,
        ElementType.HEX20: 20,
        ElementType.HEX27: 27,
        ElementType.PRISM6: 6,
        ElementType.PYRAMID5: 5,
    }

    def __init__(self, filepath: str, version: str = "2.2"):
        """
        Initialize Gmsh MSH writer

        Args:
            filepath: Output file path (.msh extension)
            version: MSH format version ("2.2" or "4.1")

        Raises:
            GmshError: If version is not supported
        """
        self.filepath = Path(filepath)

        # Validate version
        if version not in ["2.2", "4.1"]:
            raise GmshError(f"Unsupported MSH version: {version}. Use '2.2' or '4.1'")

        self.version = version
        self.file = None
        self.logger = logging.getLogger(__name__)

        # Ensure proper file extension
        if self.filepath.suffix != '.msh':
            self.logger.warning(
                f"File extension {self.filepath.suffix} is non-standard. "
                "Recommended: .msh"
            )

    def __enter__(self):
        """Context manager entry"""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    def open(self):
        """Open file for writing"""
        if self.file is not None:
            self.logger.warning("File already open")
            return

        try:
            # Create parent directory if needed
            self.filepath.parent.mkdir(parents=True, exist_ok=True)

            # Open file in text mode
            self.file = open(self.filepath, 'w', encoding='utf-8')

            self.logger.debug(f"Opened Gmsh MSH file: {self.filepath}")

        except Exception as e:
            raise GmshError(f"Failed to open file {self.filepath}: {e}")

    def close(self):
        """Close file"""
        if self.file is not None:
            try:
                self.file.close()
                self.file = None
                self.logger.debug(f"Closed Gmsh MSH file: {self.filepath}")
            except Exception as e:
                self.logger.error(f"Error closing file: {e}")

    def write_mesh(self,
                   mesh: MeshData,
                   physical_groups: Optional[Dict[str, List[int]]] = None):
        """
        Write complete mesh to Gmsh MSH file

        Args:
            mesh: MeshData object with nodes and elements
            physical_groups: Optional dictionary mapping group names to element IDs
                           Used for boundary conditions and material regions

        Raises:
            GmshError: If file is not open or mesh is invalid

        Example:
            >>> physical_groups = {
            ...     "volume1": [1, 2, 3, 4],
            ...     "volume2": [5, 6, 7, 8]
            ... }
            >>> writer.write_mesh(mesh, physical_groups)
        """
        if self.file is None:
            raise GmshError("File not open. Use 'with' statement or call open() first.")

        if mesh.num_nodes() == 0:
            raise GmshError("Mesh has no nodes")

        if mesh.num_elements() == 0:
            raise GmshError("Mesh has no elements")

        self.logger.info(f"Writing Gmsh MSH {self.version}: {mesh.num_nodes()} nodes, "
                        f"{mesh.num_elements()} elements")

        # Write format based on version
        if self.version == "2.2":
            self._write_msh_v2(mesh, physical_groups)
        else:  # version == "4.1"
            self._write_msh_v4(mesh, physical_groups)

        self.logger.info(f"Successfully wrote Gmsh MSH file: {self.filepath}")

    def _write_msh_v2(self, mesh: MeshData, physical_groups: Optional[Dict[str, List[int]]]):
        """Write MSH 2.2 format"""
        # Write mesh format section
        self.file.write("$MeshFormat\n")
        self.file.write("2.2 0 8\n")  # version, file-type (0=ASCII), data-size
        self.file.write("$EndMeshFormat\n")

        # Write physical names if provided
        if physical_groups:
            self._write_physical_names_v2(physical_groups)

        # Write nodes
        self._write_nodes_v2(mesh)

        # Write elements
        self._write_elements_v2(mesh, physical_groups)

    def _write_physical_names_v2(self, physical_groups: Dict[str, List[int]]):
        """Write physical names section (MSH 2.2)"""
        self.file.write("$PhysicalNames\n")
        self.file.write(f"{len(physical_groups)}\n")

        # In MSH 2.2, physical names are: dimension physical-tag "name"
        # We use dimension 3 for all volumes
        for idx, (name, _) in enumerate(physical_groups.items(), start=1):
            self.file.write(f"3 {idx} \"{name}\"\n")

        self.file.write("$EndPhysicalNames\n")

    def _write_nodes_v2(self, mesh: MeshData):
        """Write nodes section (MSH 2.2)"""
        self.file.write("$Nodes\n")
        self.file.write(f"{mesh.num_nodes()}\n")

        # Write nodes: node-id x y z
        for node_id in sorted(mesh.nodes.keys()):
            node = mesh.nodes[node_id]
            self.file.write(f"{node_id} {node.x:.16e} {node.y:.16e} {node.z:.16e}\n")

        self.file.write("$EndNodes\n")

        self.logger.debug(f"Wrote {mesh.num_nodes()} nodes")

    def _write_elements_v2(self, mesh: MeshData, physical_groups: Optional[Dict[str, List[int]]]):
        """Write elements section (MSH 2.2)"""
        self.file.write("$Elements\n")
        self.file.write(f"{mesh.num_elements()}\n")

        # Create element to physical group mapping
        elem_to_group = {}
        if physical_groups:
            for group_idx, (_, elem_ids) in enumerate(physical_groups.items(), start=1):
                for elem_id in elem_ids:
                    elem_to_group[elem_id] = group_idx

        # Write elements: elem-id elem-type num-tags [tags] node-ids
        # Tags: physical-tag, elementary-tag, [partition-tags]
        for elem_id in sorted(mesh.elements.keys()):
            element = mesh.elements[elem_id]

            # Get Gmsh element type number
            gmsh_type = self.GMSH_ELEMENT_TYPES.get(element.type)
            if gmsh_type is None:
                raise GmshError(f"Unsupported element type: {element.type}")

            # Determine tags
            physical_tag = elem_to_group.get(elem_id, 0)
            elementary_tag = 1  # Default elementary entity
            num_tags = 2

            # Write element line
            self.file.write(f"{elem_id} {gmsh_type} {num_tags} {physical_tag} {elementary_tag}")

            # Write connectivity
            for node_id in element.nodes:
                self.file.write(f" {node_id}")

            self.file.write("\n")

        self.file.write("$EndElements\n")

        self.logger.debug(f"Wrote {mesh.num_elements()} elements")

    def _write_msh_v4(self, mesh: MeshData, physical_groups: Optional[Dict[str, List[int]]]):
        """Write MSH 4.1 format"""
        # Write mesh format section
        self.file.write("$MeshFormat\n")
        self.file.write("4.1 0 8\n")  # version, file-type (0=ASCII), data-size
        self.file.write("$EndMeshFormat\n")

        # Write physical names if provided
        if physical_groups:
            self._write_physical_names_v4(physical_groups)

        # Write entities (required in v4)
        self._write_entities_v4(mesh, physical_groups)

        # Write nodes
        self._write_nodes_v4(mesh)

        # Write elements
        self._write_elements_v4(mesh, physical_groups)

    def _write_physical_names_v4(self, physical_groups: Dict[str, List[int]]):
        """Write physical names section (MSH 4.1)"""
        self.file.write("$PhysicalNames\n")
        self.file.write(f"{len(physical_groups)}\n")

        # Format: dimension physical-tag "name"
        for idx, (name, _) in enumerate(physical_groups.items(), start=1):
            self.file.write(f"3 {idx} \"{name}\"\n")

        self.file.write("$EndPhysicalNames\n")

    def _write_entities_v4(self, mesh: MeshData, physical_groups: Optional[Dict[str, List[int]]]):
        """Write entities section (MSH 4.1)"""
        # Entities section: points, curves, surfaces, volumes
        # For simplicity, we create one volume entity containing all elements

        # Compute bounding box
        if mesh.num_nodes() == 0:
            return

        node_coords = [(n.x, n.y, n.z) for n in mesh.nodes.values()]
        min_x = min(c[0] for c in node_coords)
        max_x = max(c[0] for c in node_coords)
        min_y = min(c[1] for c in node_coords)
        max_y = max(c[1] for c in node_coords)
        min_z = min(c[2] for c in node_coords)
        max_z = max(c[2] for c in node_coords)

        self.file.write("$Entities\n")

        # Points, curves, surfaces (all zero for simple case)
        num_points = 0
        num_curves = 0
        num_surfaces = 0

        # Volumes
        num_volumes = len(physical_groups) if physical_groups else 1

        self.file.write(f"{num_points} {num_curves} {num_surfaces} {num_volumes}\n")

        # Write volume entities
        if physical_groups:
            for idx, (name, _) in enumerate(physical_groups.items(), start=1):
                # volume-tag minX minY minZ maxX maxY maxZ numPhysicalTags physical-tag numBoundingSurfaces
                self.file.write(
                    f"{idx} {min_x:.16e} {min_y:.16e} {min_z:.16e} "
                    f"{max_x:.16e} {max_y:.16e} {max_z:.16e} 1 {idx} 0\n"
                )
        else:
            # Single default volume
            self.file.write(
                f"1 {min_x:.16e} {min_y:.16e} {min_z:.16e} "
                f"{max_x:.16e} {max_y:.16e} {max_z:.16e} 0 0\n"
            )

        self.file.write("$EndEntities\n")

    def _write_nodes_v4(self, mesh: MeshData):
        """Write nodes section (MSH 4.1)"""
        # In v4, nodes are grouped by entity blocks
        # For simplicity, put all nodes in one entity block

        num_nodes = mesh.num_nodes()

        self.file.write("$Nodes\n")
        # numEntityBlocks numNodes minNodeTag maxNodeTag
        min_node_id = min(mesh.nodes.keys())
        max_node_id = max(mesh.nodes.keys())
        self.file.write(f"1 {num_nodes} {min_node_id} {max_node_id}\n")

        # Entity block: entityDim entityTag parametric numNodesInBlock
        self.file.write(f"3 1 0 {num_nodes}\n")

        # Node tags
        for node_id in sorted(mesh.nodes.keys()):
            self.file.write(f"{node_id}\n")

        # Node coordinates
        for node_id in sorted(mesh.nodes.keys()):
            node = mesh.nodes[node_id]
            self.file.write(f"{node.x:.16e} {node.y:.16e} {node.z:.16e}\n")

        self.file.write("$EndNodes\n")

        self.logger.debug(f"Wrote {num_nodes} nodes")

    def _write_elements_v4(self, mesh: MeshData, physical_groups: Optional[Dict[str, List[int]]]):
        """Write elements section (MSH 4.1)"""
        # Elements are grouped by entity and element type

        # Group elements by type and physical group
        element_blocks = {}

        # Create element to physical group mapping
        elem_to_group = {}
        if physical_groups:
            for group_idx, (_, elem_ids) in enumerate(physical_groups.items(), start=1):
                for elem_id in elem_ids:
                    elem_to_group[elem_id] = group_idx

        # Group elements
        for elem_id, element in mesh.elements.items():
            entity_tag = elem_to_group.get(elem_id, 1)
            elem_type = element.type

            key = (entity_tag, elem_type)
            if key not in element_blocks:
                element_blocks[key] = []
            element_blocks[key].append(elem_id)

        num_blocks = len(element_blocks)
        num_elements = mesh.num_elements()
        min_elem_id = min(mesh.elements.keys())
        max_elem_id = max(mesh.elements.keys())

        self.file.write("$Elements\n")
        # numEntityBlocks numElements minElementTag maxElementTag
        self.file.write(f"{num_blocks} {num_elements} {min_elem_id} {max_elem_id}\n")

        # Write each element block
        for (entity_tag, elem_type), elem_ids in element_blocks.items():
            gmsh_type = self.GMSH_ELEMENT_TYPES.get(elem_type)
            if gmsh_type is None:
                raise GmshError(f"Unsupported element type: {elem_type}")

            # entityDim entityTag elementType numElementsInBlock
            self.file.write(f"3 {entity_tag} {gmsh_type} {len(elem_ids)}\n")

            # Elements: elementTag nodeTag1 nodeTag2 ...
            for elem_id in sorted(elem_ids):
                element = mesh.elements[elem_id]
                self.file.write(f"{elem_id}")
                for node_id in element.nodes:
                    self.file.write(f" {node_id}")
                self.file.write("\n")

        self.file.write("$EndElements\n")

        self.logger.debug(f"Wrote {num_elements} elements in {num_blocks} blocks")


def export_to_gmsh(mesh: MeshData,
                  filepath: str,
                  version: str = "2.2",
                  physical_groups: Optional[Dict[str, List[int]]] = None) -> bool:
    """
    Convenience function to export mesh to Gmsh MSH format

    Args:
        mesh: MeshData object
        filepath: Output file path
        version: MSH format version ("2.2" or "4.1")
        physical_groups: Optional physical groups

    Returns:
        True if export succeeded, False otherwise

    Example:
        >>> from koomesh.meshing.mesh_data import MeshData
        >>> mesh = MeshData()
        >>> # ... populate mesh ...
        >>> success = export_to_gmsh(mesh, "output.msh", version="2.2")
    """
    try:
        with GmshWriter(filepath, version=version) as writer:
            writer.write_mesh(mesh, physical_groups)
        return True
    except Exception as e:
        logging.getLogger(__name__).error(f"Gmsh export failed: {e}")
        return False
