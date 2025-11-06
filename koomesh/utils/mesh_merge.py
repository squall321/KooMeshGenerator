"""
Mesh Merge Utilities
====================

Merge multiple meshes into a single mesh.

Author: KooMeshGenerator Team
"""

import copy
import logging
from typing import List, Optional
from koomesh.meshing.mesh_data import MeshData, ElementType


logger = logging.getLogger(__name__)


def merge_meshes(meshes: List[MeshData],
                 renumber: bool = True,
                 preserve_parts: bool = True) -> MeshData:
    """
    Merge multiple meshes into a single mesh

    Args:
        meshes: List of MeshData objects to merge
        renumber: If True, renumber nodes and elements (default: True)
        preserve_parts: If True, preserve original part IDs (default: True)

    Returns:
        Merged MeshData

    Example:
        >>> merged = merge_meshes([mesh1, mesh2, mesh3])

    Note:
        - All meshes should have compatible element types
        - If renumber=False, node/element IDs must not conflict
        - Duplicate nodes at same location are NOT automatically merged
    """
    if not meshes:
        raise ValueError("No meshes provided to merge")

    if len(meshes) == 1:
        return copy.deepcopy(meshes[0])

    # Use first mesh's element type as primary
    primary_type = meshes[0].element_type
    merged_mesh = MeshData(element_type=primary_type)

    logger.info(f"Merging {len(meshes)} meshes...")

    # Track ID offsets for renumbering
    node_id_offset = 0
    elem_id_offset = 0
    part_id_offset = 0

    for i, mesh in enumerate(meshes):
        logger.debug(f"Processing mesh {i+1}/{len(meshes)}: "
                    f"{mesh.num_nodes()} nodes, {mesh.num_elements()} elements")

        # Node ID mapping for this mesh
        node_id_map = {}

        # Copy nodes
        for node_id, node in mesh.nodes.items():
            if renumber:
                new_node_id = node_id + node_id_offset
            else:
                new_node_id = node_id

            # Check for ID conflicts if not renumbering
            if not renumber and new_node_id in merged_mesh.nodes:
                raise ValueError(
                    f"Node ID conflict: {new_node_id} already exists. "
                    "Use renumber=True to avoid conflicts."
                )

            node_id_map[node_id] = new_node_id
            merged_mesh.add_node(
                node.x, node.y, node.z,
                node_id=new_node_id,
                metadata=copy.deepcopy(node.metadata)
            )

        # Copy elements
        for elem_id, elem in mesh.elements.items():
            if renumber:
                new_elem_id = elem_id + elem_id_offset
            else:
                new_elem_id = elem_id

            # Check for ID conflicts if not renumbering
            if not renumber and new_elem_id in merged_mesh.elements:
                raise ValueError(
                    f"Element ID conflict: {new_elem_id} already exists. "
                    "Use renumber=True to avoid conflicts."
                )

            # Map node IDs
            new_node_ids = [node_id_map[nid] for nid in elem.nodes]

            # Adjust part ID if preserving parts
            if preserve_parts and i > 0:
                new_part_id = elem.part_id + part_id_offset
            else:
                new_part_id = elem.part_id

            merged_mesh.add_element(
                new_node_ids,
                element_id=new_elem_id,
                element_type=elem.type,
                part_id=new_part_id,
                metadata=copy.deepcopy(elem.metadata)
            )

        # Update offsets for next mesh
        if renumber:
            node_id_offset = max(merged_mesh.nodes.keys()) if merged_mesh.nodes else 0
            elem_id_offset = max(merged_mesh.elements.keys()) if merged_mesh.elements else 0

        if preserve_parts:
            # Find max part ID in current merged mesh
            if merged_mesh.elements:
                max_part = max(elem.part_id for elem in merged_mesh.elements.values())
                part_id_offset = max_part

    logger.info(f"Merge complete: {merged_mesh.num_nodes()} nodes, "
                f"{merged_mesh.num_elements()} elements")

    return merged_mesh


def merge_meshes_with_tolerance(meshes: List[MeshData],
                                tolerance: float = 1e-6) -> MeshData:
    """
    Merge meshes and eliminate duplicate nodes within tolerance

    This is more advanced than merge_meshes - it identifies and merges
    nodes that are within the specified tolerance distance.

    Args:
        meshes: List of MeshData objects to merge
        tolerance: Distance tolerance for considering nodes identical

    Returns:
        Merged MeshData with duplicate nodes eliminated

    Example:
        >>> # Merge meshes and weld nodes within 1e-6 distance
        >>> merged = merge_meshes_with_tolerance([mesh1, mesh2], tolerance=1e-6)

    Warning:
        This operation can be slow for large meshes (O(n^2) in worst case)
    """
    import numpy as np

    if not meshes:
        raise ValueError("No meshes provided to merge")

    # First, do a simple merge
    merged = merge_meshes(meshes, renumber=True, preserve_parts=True)

    logger.info(f"Eliminating duplicate nodes within tolerance {tolerance}...")

    # Build array of node coordinates
    node_ids = list(merged.nodes.keys())
    coords = np.array([[merged.nodes[nid].x,
                       merged.nodes[nid].y,
                       merged.nodes[nid].z] for nid in node_ids])

    # Find duplicate nodes
    node_mapping = {}  # Maps original node ID to canonical node ID
    canonical_nodes = set()  # Set of canonical (kept) node IDs

    for i, nid1 in enumerate(node_ids):
        if nid1 in canonical_nodes:
            continue  # Already assigned as canonical

        # Check if this node is duplicate of any canonical node
        is_duplicate = False
        for nid2 in canonical_nodes:
            idx2 = node_ids.index(nid2)
            dist = np.linalg.norm(coords[i] - coords[idx2])
            if dist < tolerance:
                node_mapping[nid1] = nid2
                is_duplicate = True
                break

        if not is_duplicate:
            # This is a new canonical node
            canonical_nodes.add(nid1)
            node_mapping[nid1] = nid1

    num_duplicates = len(node_ids) - len(canonical_nodes)
    logger.debug(f"Found {num_duplicates} duplicate nodes")

    if num_duplicates == 0:
        return merged  # No duplicates found

    # Create new mesh with deduplicated nodes
    new_mesh = MeshData(element_type=merged.element_type)

    # Add only canonical nodes
    for nid in canonical_nodes:
        node = merged.nodes[nid]
        new_mesh.add_node(
            node.x, node.y, node.z,
            node_id=nid,
            metadata=copy.deepcopy(node.metadata)
        )

    # Add elements with remapped node IDs
    for elem_id, elem in merged.elements.items():
        new_node_ids = [node_mapping[nid] for nid in elem.nodes]
        new_mesh.add_element(
            new_node_ids,
            element_id=elem_id,
            element_type=elem.type,
            part_id=elem.part_id,
            metadata=copy.deepcopy(elem.metadata)
        )

    # Copy metadata
    new_mesh.metadata = copy.deepcopy(merged.metadata)

    logger.info(f"Deduplication complete: {merged.num_nodes()} -> {new_mesh.num_nodes()} nodes")

    return new_mesh
