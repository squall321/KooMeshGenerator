"""
Elmer FEM Mesh Format Writer
=============================

Writes mesh data to Elmer format for multiphysics FEM simulations.

Elmer uses a simple ASCII mesh format with separate files:
- mesh.header: Basic mesh information
- mesh.nodes: Node coordinates
- mesh.elements: Element connectivity
- mesh.boundary: Boundary elements

Author: KooMeshGenerator Team
License: MIT
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

from koomesh.meshing.mesh_data import MeshData, ElementType


class ElmerError(Exception):
    """Exception raised for Elmer export errors"""
    pass


class ElmerWriter:
    """
    Writer for Elmer FEM mesh format

    Example:
        >>> writer = ElmerWriter("mesh_directory")
        >>> writer.write_mesh(mesh)
    """

    ELMER_ELEMENT_TYPES = {
        ElementType.HEX8: 808,
        ElementType.HEX20: 820,
        ElementType.TET4: 504,
        ElementType.TET10: 510,
        ElementType.PRISM6: 706,
        ElementType.PYRAMID5: 605,
    }

    def __init__(self, mesh_dir: str):
        """Initialize Elmer writer"""
        self.mesh_dir = Path(mesh_dir)
        self.logger = logging.getLogger(__name__)

    def write_mesh(self, mesh: MeshData):
        """Write mesh to Elmer format"""
        if not mesh.elements:
            raise ElmerError("Cannot export empty mesh")

        self.mesh_dir.mkdir(parents=True, exist_ok=True)

        self._write_header(mesh)
        self._write_nodes(mesh)
        self._write_elements(mesh)
        self._write_boundary(mesh)

        self.logger.info(f"Wrote Elmer mesh to {self.mesh_dir}")

    def _write_header(self, mesh: MeshData):
        """Write mesh.header file"""
        filepath = self.mesh_dir / "mesh.header"

        with open(filepath, 'w') as f:
            f.write(f"{len(mesh.nodes)} {len(mesh.elements)} 0\n")
            f.write("2\n")  # Element types count (simplified)
            elem_type_code = self.ELMER_ELEMENT_TYPES.get(mesh.element_type, 808)
            f.write(f"{elem_type_code} {len(mesh.elements)}\n")

    def _write_nodes(self, mesh: MeshData):
        """Write mesh.nodes file"""
        filepath = self.mesh_dir / "mesh.nodes"

        with open(filepath, 'w') as f:
            for idx, (nid, node) in enumerate(sorted(mesh.nodes.items()), 1):
                f.write(f"{idx} -1 {node.x:.16e} {node.y:.16e} {node.z:.16e}\n")

    def _write_elements(self, mesh: MeshData):
        """Write mesh.elements file"""
        filepath = self.mesh_dir / "mesh.elements"

        # Create node ID mapping
        node_map = {nid: idx for idx, nid in enumerate(sorted(mesh.nodes.keys()), 1)}

        with open(filepath, 'w') as f:
            for idx, elem in enumerate(mesh.elements.values(), 1):
                elem_type_code = self.ELMER_ELEMENT_TYPES.get(elem.type, 808)
                node_indices = [node_map[nid] for nid in elem.nodes]

                # Format: elem_id body_id elem_type_code node_indices
                nodes_str = ' '.join(map(str, node_indices))
                f.write(f"{idx} 1 {elem_type_code} {nodes_str}\n")

    def _write_boundary(self, mesh: MeshData):
        """Write mesh.boundary file (empty for now)"""
        filepath = self.mesh_dir / "mesh.boundary"

        with open(filepath, 'w') as f:
            f.write("0 0 0\n")  # No boundary elements


def export_to_elmer(mesh: MeshData, mesh_dir: str) -> bool:
    """
    Convenience function to export mesh to Elmer format

    Args:
        mesh: Mesh data to export
        mesh_dir: Directory for Elmer mesh files

    Returns:
        True if successful

    Example:
        >>> export_to_elmer(mesh, "elmer_mesh")
    """
    try:
        writer = ElmerWriter(mesh_dir)
        writer.write_mesh(mesh)
        return True
    except Exception as e:
        logging.error(f"Elmer export failed: {e}")
        return False
