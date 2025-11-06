"""
Exodus II Format Export
=======================

This module provides functionality to export mesh data to Exodus II format (.exo, .e).

Exodus II is a widely-used binary format for finite element analysis developed by
Sandia National Laboratories. It uses netCDF4 as the underlying storage mechanism.

Key Features:
- Binary format for efficient storage
- Support for element blocks (groups of same element type)
- Node sets and side sets for boundary conditions
- Time-dependent data support
- Metadata and quality assurance information

Format Details:
- Storage: netCDF4 binary format
- Element blocks: Required, group elements by type
- Coordinate system: Global 3D coordinates
- Connectivity: 1-based indexing
- Applications: CUBIT, ParaView, VisIt, Sandia tools

Supported Element Types:
- HEX8: 8-node hexahedron (Exodus: "HEX")
- HEX20: 20-node hexahedron (Exodus: "HEX20")
- HEX27: 27-node hexahedron (Exodus: "HEX27")
- TET4: 4-node tetrahedron (Exodus: "TETRA4")
- TET10: 10-node tetrahedron (Exodus: "TETRA10")
- PRISM6: 6-node prism/wedge (Exodus: "WEDGE6")
- PYRAMID5: 5-node pyramid (Exodus: "PYRAMID5")

Usage:
    >>> from koomesh.export.exodus_writer import ExodusWriter
    >>> from koomesh.meshing.mesh_data import MeshData
    >>>
    >>> # Create and populate mesh
    >>> mesh = MeshData()
    >>> # ... add nodes and elements ...
    >>>
    >>> # Export to Exodus II
    >>> with ExodusWriter("output.exo") as writer:
    ...     writer.write_mesh(mesh)
    >>>
    >>> # With element blocks and sets
    >>> with ExodusWriter("output.exo", title="My Mesh") as writer:
    ...     writer.write_mesh(
    ...         mesh,
    ...         element_blocks={"block1": [1, 2, 3], "block2": [4, 5, 6]},
    ...         node_sets={"boundary": [1, 2, 3, 4]}
    ...     )

Author: KooMeshGenerator Team
License: MIT
"""

import logging
from pathlib import Path
from typing import Optional, Dict, List, Set
from datetime import datetime

try:
    from netCDF4 import Dataset
    NETCDF4_AVAILABLE = True
except ImportError:
    NETCDF4_AVAILABLE = False
    Dataset = None

from koomesh.meshing.mesh_data import MeshData, ElementType


class ExodusError(Exception):
    """Exception raised for Exodus II export errors"""
    pass


class ExodusWriter:
    """
    Exodus II format writer

    Exports mesh data to Exodus II binary format using netCDF4.

    Attributes:
        filepath: Path to output file
        title: Mesh title/description
        ncfile: netCDF4 Dataset object

    Example:
        >>> writer = ExodusWriter("mesh.exo", title="Test Mesh")
        >>> with writer:
        ...     writer.write_mesh(mesh_data)
    """

    # Exodus II element type names
    EXODUS_ELEMENT_TYPES = {
        ElementType.HEX8: "HEX",
        ElementType.HEX20: "HEX20",
        ElementType.HEX27: "HEX27",
        ElementType.TET4: "TETRA4",
        ElementType.TET10: "TETRA10",
        ElementType.PRISM6: "WEDGE6",
        ElementType.PYRAMID5: "PYRAMID5",
    }

    # Number of nodes per element type
    NODES_PER_ELEMENT = {
        ElementType.HEX8: 8,
        ElementType.HEX20: 20,
        ElementType.HEX27: 27,
        ElementType.TET4: 4,
        ElementType.TET10: 10,
        ElementType.PRISM6: 6,
        ElementType.PYRAMID5: 5,
    }

    def __init__(self, filepath: str, title: str = "KooMesh Generated", mode: str = 'w'):
        """
        Initialize Exodus II writer

        Args:
            filepath: Output file path (.exo or .e extension)
            title: Mesh title/description
            mode: File mode ('w' for write, 'a' for append)

        Raises:
            ExodusError: If netCDF4 is not available
        """
        if not NETCDF4_AVAILABLE:
            raise ExodusError(
                "netCDF4 library is required for Exodus II export. "
                "Install it with: pip install netCDF4"
            )

        self.filepath = Path(filepath)
        self.title = title
        self.mode = mode
        self.ncfile: Optional[Dataset] = None
        self.logger = logging.getLogger(__name__)

        # Ensure proper file extension
        if self.filepath.suffix not in ['.exo', '.e', '.ex2', '.exoII']:
            self.logger.warning(
                f"File extension {self.filepath.suffix} is non-standard. "
                "Recommended: .exo, .e, .ex2, or .exoII"
            )

    def __enter__(self):
        """Context manager entry"""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    def open(self):
        """Open netCDF4 file for writing"""
        if self.ncfile is not None:
            self.logger.warning("File already open")
            return

        try:
            # Create parent directory if needed
            self.filepath.parent.mkdir(parents=True, exist_ok=True)

            # Open netCDF4 file
            self.ncfile = Dataset(str(self.filepath), self.mode, format='NETCDF3_64BIT_OFFSET')

            # Write global attributes
            self.ncfile.api_version = 5.14  # Exodus II API version
            self.ncfile.version = 5.14
            self.ncfile.floating_point_word_size = 8
            self.ncfile.file_size = 1  # Large file mode
            self.ncfile.title = self.title

            self.logger.debug(f"Opened Exodus II file: {self.filepath}")

        except Exception as e:
            raise ExodusError(f"Failed to open file {self.filepath}: {e}")

    def close(self):
        """Close netCDF4 file"""
        if self.ncfile is not None:
            try:
                self.ncfile.close()
                self.ncfile = None
                self.logger.debug(f"Closed Exodus II file: {self.filepath}")
            except Exception as e:
                self.logger.error(f"Error closing file: {e}")

    def write_mesh(self,
                   mesh: MeshData,
                   element_blocks: Optional[Dict[str, List[int]]] = None,
                   node_sets: Optional[Dict[str, List[int]]] = None,
                   side_sets: Optional[Dict[str, List[tuple]]] = None):
        """
        Write complete mesh to Exodus II file

        Args:
            mesh: MeshData object with nodes and elements
            element_blocks: Optional dictionary mapping block names to element IDs
                          If None, creates one block per element type
            node_sets: Optional dictionary mapping set names to node IDs
            side_sets: Optional dictionary mapping set names to (elem_id, side_num) tuples

        Raises:
            ExodusError: If file is not open or mesh is invalid

        Example:
            >>> element_blocks = {
            ...     "steel": [1, 2, 3, 4],
            ...     "aluminum": [5, 6, 7, 8]
            ... }
            >>> node_sets = {
            ...     "bottom": [1, 2, 3, 4],
            ...     "top": [101, 102, 103, 104]
            ... }
            >>> writer.write_mesh(mesh, element_blocks, node_sets)
        """
        if self.ncfile is None:
            raise ExodusError("File not open. Use 'with' statement or call open() first.")

        if mesh.num_nodes() == 0:
            raise ExodusError("Mesh has no nodes")

        if mesh.num_elements() == 0:
            raise ExodusError("Mesh has no elements")

        self.logger.info(f"Writing Exodus II mesh: {mesh.num_nodes()} nodes, "
                        f"{mesh.num_elements()} elements")

        # Write dimensions
        self._write_dimensions(mesh)

        # Write coordinate names
        self._write_coordinate_names()

        # Write quality assurance
        self._write_qa_records()

        # Write nodes
        self._write_nodes(mesh)

        # Write element blocks
        if element_blocks is None:
            # Auto-create element blocks by type
            element_blocks = self._create_element_blocks_by_type(mesh)

        self._write_element_blocks(mesh, element_blocks)

        # Write node sets
        if node_sets:
            self._write_node_sets(node_sets, mesh)

        # Write side sets
        if side_sets:
            self._write_side_sets(side_sets, mesh)

        # Sync to disk
        self.ncfile.sync()

        self.logger.info(f"Successfully wrote Exodus II file: {self.filepath}")

    def _write_dimensions(self, mesh: MeshData):
        """Write netCDF dimensions"""
        # Basic dimensions
        self.ncfile.createDimension('len_string', 33)
        self.ncfile.createDimension('len_line', 81)
        self.ncfile.createDimension('four', 4)
        self.ncfile.createDimension('len_name', 33)
        self.ncfile.createDimension('time_step', None)  # Unlimited

        # Mesh dimensions
        num_nodes = mesh.num_nodes()
        num_elements = mesh.num_elements()
        num_dim = 3  # Always 3D

        self.ncfile.createDimension('num_nodes', num_nodes)
        self.ncfile.createDimension('num_dim', num_dim)
        self.ncfile.createDimension('num_elem', num_elements)

        self.logger.debug(f"Created dimensions: {num_nodes} nodes, {num_elements} elements")

    def _write_coordinate_names(self):
        """Write coordinate system names"""
        # Create variable for coordinate names
        coor_names = self.ncfile.createVariable('coor_names', 'S1', ('num_dim', 'len_name'))

        # Write names (X, Y, Z)
        import numpy as np
        names = [b'X', b'Y', b'Z']
        for i, name in enumerate(names):
            name_arr = np.zeros(33, dtype='S1')
            name_arr[:len(name)] = [bytes([c]) for c in name]
            coor_names[i, :] = name_arr

    def _write_qa_records(self):
        """Write quality assurance records"""
        # Create QA dimension
        self.ncfile.createDimension('num_qa_rec', 1)

        # Create QA variable
        qa_records = self.ncfile.createVariable('qa_records', 'S1',
                                                ('num_qa_rec', 'four', 'len_string'))

        # QA record: [code name, code version, date, time]
        import numpy as np
        now = datetime.now()

        qa_data = [
            'KooMeshGenerator',
            '1.0.0',
            now.strftime('%Y/%m/%d'),
            now.strftime('%H:%M:%S')
        ]

        for i, text in enumerate(qa_data):
            text_bytes = text.encode('ascii')
            text_arr = np.zeros(33, dtype='S1')
            text_arr[:len(text_bytes)] = [bytes([c]) for c in text_bytes]
            qa_records[0, i, :] = text_arr

    def _write_nodes(self, mesh: MeshData):
        """Write node coordinates"""
        import numpy as np

        num_nodes = mesh.num_nodes()

        # Create coordinate variables
        coordx = self.ncfile.createVariable('coordx', 'f8', ('num_nodes',))
        coordy = self.ncfile.createVariable('coordy', 'f8', ('num_nodes',))
        coordz = self.ncfile.createVariable('coordz', 'f8', ('num_nodes',))

        # Extract node coordinates in ID order
        node_ids = sorted(mesh.nodes.keys())

        x_coords = np.zeros(num_nodes, dtype=np.float64)
        y_coords = np.zeros(num_nodes, dtype=np.float64)
        z_coords = np.zeros(num_nodes, dtype=np.float64)

        for idx, node_id in enumerate(node_ids):
            node = mesh.nodes[node_id]
            x_coords[idx] = node.x
            y_coords[idx] = node.y
            z_coords[idx] = node.z

        # Write coordinates
        coordx[:] = x_coords
        coordy[:] = y_coords
        coordz[:] = z_coords

        self.logger.debug(f"Wrote {num_nodes} node coordinates")

    def _create_element_blocks_by_type(self, mesh: MeshData) -> Dict[str, List[int]]:
        """
        Auto-create element blocks grouped by element type

        Args:
            mesh: MeshData object

        Returns:
            Dictionary mapping block names to element IDs
        """
        blocks = {}

        for elem_id, element in mesh.elements.items():
            elem_type = element.type
            block_name = f"{elem_type.name}_block"

            if block_name not in blocks:
                blocks[block_name] = []

            blocks[block_name].append(elem_id)

        self.logger.debug(f"Created {len(blocks)} element blocks by type")

        return blocks

    def _write_element_blocks(self, mesh: MeshData, element_blocks: Dict[str, List[int]]):
        """
        Write element blocks

        Args:
            mesh: MeshData object
            element_blocks: Dictionary mapping block names to element IDs
        """
        import numpy as np

        num_blocks = len(element_blocks)

        # Create dimension for element blocks
        self.ncfile.createDimension('num_el_blk', num_blocks)

        # Create element block status array
        eb_status = self.ncfile.createVariable('eb_status', 'i4', ('num_el_blk',))
        eb_status[:] = np.ones(num_blocks, dtype=np.int32)

        # Create element block IDs
        eb_prop1 = self.ncfile.createVariable('eb_prop1', 'i4', ('num_el_blk',))
        eb_prop1.setncattr('name', 'ID')

        # Create element block names
        eb_names = self.ncfile.createVariable('eb_names', 'S1', ('num_el_blk', 'len_name'))

        # Process each element block
        for block_idx, (block_name, elem_ids) in enumerate(element_blocks.items(), start=1):
            # Get element type from first element in block
            first_elem = mesh.elements[elem_ids[0]]
            elem_type = first_elem.type

            # Verify all elements in block have same type
            for elem_id in elem_ids:
                if mesh.elements[elem_id].type != elem_type:
                    raise ExodusError(
                        f"Element block '{block_name}' contains mixed element types"
                    )

            # Get Exodus element type name
            exodus_type = self.EXODUS_ELEMENT_TYPES.get(elem_type)
            if exodus_type is None:
                raise ExodusError(f"Unsupported element type: {elem_type}")

            num_elem_in_block = len(elem_ids)
            num_nodes_per_elem = self.NODES_PER_ELEMENT[elem_type]
            num_attr = 0  # No attributes for now

            # Create dimensions for this block
            dim_num_el = f'num_el_in_blk{block_idx}'
            dim_num_nod = f'num_nod_per_el{block_idx}'

            self.ncfile.createDimension(dim_num_el, num_elem_in_block)
            self.ncfile.createDimension(dim_num_nod, num_nodes_per_elem)

            # Write block ID
            eb_prop1[block_idx - 1] = block_idx

            # Write block name
            name_bytes = block_name.encode('ascii')
            name_arr = np.zeros(33, dtype='S1')
            name_arr[:len(name_bytes)] = [bytes([c]) for c in name_bytes]
            eb_names[block_idx - 1, :] = name_arr

            # Create connectivity variable
            connect_var = self.ncfile.createVariable(
                f'connect{block_idx}',
                'i4',
                (dim_num_el, dim_num_nod)
            )
            connect_var.elem_type = exodus_type

            # Build connectivity array
            # Exodus uses 1-based indexing, so we need to map our node IDs
            node_id_to_index = {nid: idx + 1 for idx, nid in enumerate(sorted(mesh.nodes.keys()))}

            connectivity = np.zeros((num_elem_in_block, num_nodes_per_elem), dtype=np.int32)

            for local_idx, elem_id in enumerate(elem_ids):
                element = mesh.elements[elem_id]
                for node_idx, node_id in enumerate(element.nodes):
                    connectivity[local_idx, node_idx] = node_id_to_index[node_id]

            # Write connectivity
            connect_var[:, :] = connectivity

            self.logger.debug(
                f"Wrote element block {block_idx}: '{block_name}' "
                f"({num_elem_in_block} {exodus_type} elements)"
            )

    def _write_node_sets(self, node_sets: Dict[str, List[int]], mesh: MeshData):
        """
        Write node sets

        Args:
            node_sets: Dictionary mapping set names to node IDs
            mesh: MeshData object for node ID mapping
        """
        import numpy as np

        num_node_sets = len(node_sets)

        if num_node_sets == 0:
            return

        # Create dimension
        self.ncfile.createDimension('num_node_sets', num_node_sets)

        # Create node set status
        ns_status = self.ncfile.createVariable('ns_status', 'i4', ('num_node_sets',))
        ns_status[:] = np.ones(num_node_sets, dtype=np.int32)

        # Create node set IDs
        ns_prop1 = self.ncfile.createVariable('ns_prop1', 'i4', ('num_node_sets',))
        ns_prop1.setncattr('name', 'ID')

        # Create node set names
        ns_names = self.ncfile.createVariable('ns_names', 'S1', ('num_node_sets', 'len_name'))

        # Create node ID to index mapping (not needed since we use 1-based node IDs directly)
        # node_id_to_index = {nid: idx + 1 for idx, nid in enumerate(sorted(mesh.nodes.keys()))}

        # Process each node set
        for set_idx, (set_name, node_ids) in enumerate(node_sets.items(), start=1):
            num_nodes_in_set = len(node_ids)

            # Create dimension for this set
            dim_name = f'num_nod_ns{set_idx}'
            self.ncfile.createDimension(dim_name, num_nodes_in_set)

            # Write set ID
            ns_prop1[set_idx - 1] = set_idx

            # Write set name
            name_bytes = set_name.encode('ascii')
            name_arr = np.zeros(33, dtype='S1')
            name_arr[:len(name_bytes)] = [bytes([c]) for c in name_bytes]
            ns_names[set_idx - 1, :] = name_arr

            # Create node list variable
            node_list = self.ncfile.createVariable(f'node_ns{set_idx}', 'i4', (dim_name,))

            # Write node IDs (1-based indexing)
            node_list[:] = np.array(node_ids, dtype=np.int32)

            self.logger.debug(f"Wrote node set {set_idx}: '{set_name}' ({num_nodes_in_set} nodes)")

    def _write_side_sets(self, side_sets: Dict[str, List[tuple]], mesh: MeshData):
        """
        Write side sets

        Args:
            side_sets: Dictionary mapping set names to list of (elem_id, side_num) tuples
            mesh: MeshData object (for potential future use)
        """
        import numpy as np

        num_side_sets = len(side_sets)

        if num_side_sets == 0:
            return

        # Create dimension
        self.ncfile.createDimension('num_side_sets', num_side_sets)

        # Create side set status
        ss_status = self.ncfile.createVariable('ss_status', 'i4', ('num_side_sets',))
        ss_status[:] = np.ones(num_side_sets, dtype=np.int32)

        # Create side set IDs
        ss_prop1 = self.ncfile.createVariable('ss_prop1', 'i4', ('num_side_sets',))
        ss_prop1.setncattr('name', 'ID')

        # Create side set names
        ss_names = self.ncfile.createVariable('ss_names', 'S1', ('num_side_sets', 'len_name'))

        # Process each side set
        for set_idx, (set_name, side_list) in enumerate(side_sets.items(), start=1):
            num_sides_in_set = len(side_list)

            # Create dimension for this set
            dim_name = f'num_side_ss{set_idx}'
            self.ncfile.createDimension(dim_name, num_sides_in_set)

            # Write set ID
            ss_prop1[set_idx - 1] = set_idx

            # Write set name
            name_bytes = set_name.encode('ascii')
            name_arr = np.zeros(33, dtype='S1')
            name_arr[:len(name_bytes)] = [bytes([c]) for c in name_bytes]
            ss_names[set_idx - 1, :] = name_arr

            # Create element and side lists
            elem_list = self.ncfile.createVariable(f'elem_ss{set_idx}', 'i4', (dim_name,))
            side_list_var = self.ncfile.createVariable(f'side_ss{set_idx}', 'i4', (dim_name,))

            # Extract element IDs and side numbers
            elem_ids = np.array([side[0] for side in side_list], dtype=np.int32)
            side_nums = np.array([side[1] for side in side_list], dtype=np.int32)

            # Write data
            elem_list[:] = elem_ids
            side_list_var[:] = side_nums

            self.logger.debug(f"Wrote side set {set_idx}: '{set_name}' ({num_sides_in_set} sides)")


def export_to_exodus(mesh: MeshData,
                    filepath: str,
                    title: str = "KooMesh Generated",
                    element_blocks: Optional[Dict[str, List[int]]] = None,
                    node_sets: Optional[Dict[str, List[int]]] = None,
                    side_sets: Optional[Dict[str, List[tuple]]] = None) -> bool:
    """
    Convenience function to export mesh to Exodus II format

    Args:
        mesh: MeshData object
        filepath: Output file path
        title: Mesh title
        element_blocks: Optional element blocks
        node_sets: Optional node sets
        side_sets: Optional side sets

    Returns:
        True if export succeeded, False otherwise

    Example:
        >>> from koomesh.meshing.mesh_data import MeshData
        >>> mesh = MeshData()
        >>> # ... populate mesh ...
        >>> success = export_to_exodus(mesh, "output.exo", title="Test Mesh")
    """
    try:
        with ExodusWriter(filepath, title=title) as writer:
            writer.write_mesh(mesh, element_blocks, node_sets, side_sets)
        return True
    except Exception as e:
        logging.getLogger(__name__).error(f"Exodus export failed: {e}")
        return False
