"""
Mesh Repair Utilities
======================

Tools for fixing common mesh issues: duplicate nodes, degenerate elements, etc.

Author: KooMeshGenerator Team
"""

import numpy as np
from typing import List, Tuple, Set
from koomesh.meshing.mesh_data import MeshData


class MeshRepair:
    """
    Mesh repair toolkit

    Example:
        >>> repair = MeshRepair(mesh)
        >>> repair.remove_duplicate_nodes()
        >>> repair.remove_degenerate_elements()
        >>> cleaned_mesh = repair.mesh
    """

    def __init__(self, mesh: MeshData):
        """Initialize with mesh to repair"""
        self.mesh = mesh
        self.repairs_made = []

    def remove_duplicate_nodes(self, tolerance: float = 1e-10) -> int:
        """
        Remove duplicate nodes (same coordinates)

        Args:
            tolerance: Distance tolerance for considering nodes duplicate

        Returns:
            Number of duplicate nodes removed

        Example:
            >>> count = repair.remove_duplicate_nodes(1e-9)
        """
        if not self.mesh.nodes:
            return 0

        # Build coordinate to node ID mapping
        coord_map = {}
        duplicates = {}  # maps duplicate ID to canonical ID

        for nid, node in self.mesh.nodes.items():
            # Round coordinates for comparison
            key = (
                round(node.x / tolerance),
                round(node.y / tolerance),
                round(node.z / tolerance)
            )

            if key in coord_map:
                # Duplicate found
                duplicates[nid] = coord_map[key]
            else:
                coord_map[key] = nid

        if not duplicates:
            return 0

        # Update element connectivity
        for elem in self.mesh.elements.values():
            elem.nodes = [duplicates.get(nid, nid) for nid in elem.nodes]

        # Remove duplicate nodes
        for dup_nid in duplicates.keys():
            if dup_nid in self.mesh.nodes:
                del self.mesh.nodes[dup_nid]

        count = len(duplicates)
        self.repairs_made.append(f"Removed {count} duplicate nodes")
        return count

    def remove_degenerate_elements(self) -> int:
        """
        Remove elements with duplicate nodes

        Returns:
            Number of degenerate elements removed

        Example:
            >>> count = repair.remove_degenerate_elements()
        """
        if not self.mesh.elements:
            return 0

        degenerate_ids = []

        for eid, elem in self.mesh.elements.items():
            # Check for duplicate nodes in element
            if len(elem.nodes) != len(set(elem.nodes)):
                degenerate_ids.append(eid)

        # Remove degenerate elements
        for eid in degenerate_ids:
            del self.mesh.elements[eid]

        count = len(degenerate_ids)
        if count > 0:
            self.repairs_made.append(f"Removed {count} degenerate elements")
        return count

    def remove_unused_nodes(self) -> int:
        """
        Remove nodes not referenced by any element

        Returns:
            Number of unused nodes removed

        Example:
            >>> count = repair.remove_unused_nodes()
        """
        if not self.mesh.elements:
            # If no elements, all nodes are unused
            count = len(self.mesh.nodes)
            self.mesh.nodes.clear()
            if count > 0:
                self.repairs_made.append(f"Removed {count} unused nodes (no elements)")
            return count

        # Find used nodes
        used_nodes = set()
        for elem in self.mesh.elements.values():
            used_nodes.update(elem.nodes)

        # Find unused nodes
        all_nodes = set(self.mesh.nodes.keys())
        unused = all_nodes - used_nodes

        # Remove unused nodes
        for nid in unused:
            del self.mesh.nodes[nid]

        count = len(unused)
        if count > 0:
            self.repairs_made.append(f"Removed {count} unused nodes")
        return count

    def remove_zero_volume_elements(self, tolerance: float = 1e-10) -> int:
        """
        Remove elements with zero or near-zero volume

        Args:
            tolerance: Volume threshold

        Returns:
            Number of elements removed

        Example:
            >>> count = repair.remove_zero_volume_elements()
        """
        from koomesh.meshing.mesh_data import ElementType

        zero_vol_ids = []

        for eid, elem in self.mesh.elements.items():
            nodes = [self.mesh.nodes[nid] for nid in elem.nodes]
            coords = np.array([[n.x, n.y, n.z] for n in nodes])

            volume = 0.0

            if elem.type == ElementType.TET4:
                # Tetrahedron volume
                v1 = coords[1] - coords[0]
                v2 = coords[2] - coords[0]
                v3 = coords[3] - coords[0]
                volume = abs(np.dot(v1, np.cross(v2, v3))) / 6.0

            elif elem.type in [ElementType.HEX8, ElementType.HEX20, ElementType.HEX27]:
                # Approximate hex volume using diagonals
                diag1 = np.linalg.norm(coords[0] - coords[6])
                diag2 = np.linalg.norm(coords[1] - coords[7])
                diag3 = np.linalg.norm(coords[2] - coords[4])
                volume = (diag1 * diag2 * diag3) / 8.0

            if volume < tolerance:
                zero_vol_ids.append(eid)

        # Remove zero volume elements
        for eid in zero_vol_ids:
            del self.mesh.elements[eid]

        count = len(zero_vol_ids)
        if count > 0:
            self.repairs_made.append(f"Removed {count} zero-volume elements")
        return count

    def merge_coincident_nodes(self, tolerance: float = 1e-6) -> int:
        """
        Merge nodes that are very close together

        Args:
            tolerance: Distance threshold for merging

        Returns:
            Number of nodes merged

        Example:
            >>> count = repair.merge_coincident_nodes(1e-5)
        """
        # This is similar to remove_duplicate_nodes but with larger tolerance
        return self.remove_duplicate_nodes(tolerance)

    def fix_element_connectivity(self) -> int:
        """
        Fix elements referencing non-existent nodes

        Returns:
            Number of bad elements removed

        Example:
            >>> count = repair.fix_element_connectivity()
        """
        bad_elements = []

        for eid, elem in self.mesh.elements.items():
            for nid in elem.nodes:
                if nid not in self.mesh.nodes:
                    bad_elements.append(eid)
                    break

        # Remove bad elements
        for eid in bad_elements:
            del self.mesh.elements[eid]

        count = len(bad_elements)
        if count > 0:
            self.repairs_made.append(f"Removed {count} elements with invalid nodes")
        return count

    def repair_all(self, tolerance: float = 1e-10) -> dict:
        """
        Run all repair operations

        Args:
            tolerance: Tolerance for node comparison

        Returns:
            Dictionary of repair counts

        Example:
            >>> results = repair.repair_all()
            >>> print(f"Fixed {results['total']} issues")
        """
        results = {
            'duplicate_nodes': self.remove_duplicate_nodes(tolerance),
            'degenerate_elements': self.remove_degenerate_elements(),
            'zero_volume_elements': self.remove_zero_volume_elements(tolerance),
            'bad_connectivity': self.fix_element_connectivity(),
            'unused_nodes': self.remove_unused_nodes(),
        }

        results['total'] = sum(results.values())
        return results

    def generate_report(self) -> str:
        """Generate repair summary report"""
        if not self.repairs_made:
            return "No repairs needed - mesh is clean"

        lines = []
        lines.append("Mesh Repair Summary")
        lines.append("=" * 50)
        for repair in self.repairs_made:
            lines.append(f"  ✓ {repair}")
        lines.append("=" * 50)

        return "\n".join(lines)


def repair_mesh(mesh: MeshData, tolerance: float = 1e-10) -> dict:
    """
    Convenience function to repair mesh

    Args:
        mesh: Mesh to repair (modified in place)
        tolerance: Tolerance for node comparison

    Returns:
        Dictionary of repair counts

    Example:
        >>> results = repair_mesh(mesh)
        >>> print(results)
    """
    repair = MeshRepair(mesh)
    results = repair.repair_all(tolerance)
    print(repair.generate_report())
    return results
