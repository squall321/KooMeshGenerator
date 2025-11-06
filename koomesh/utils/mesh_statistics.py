"""
Mesh Statistics Utility
========================

Provides comprehensive statistics about mesh data.

Author: KooMeshGenerator Team
License: MIT
"""

import numpy as np
from typing import Dict, List, Any
from collections import Counter

from koomesh.meshing.mesh_data import MeshData, ElementType


class MeshStatistics:
    """
    Compute and report mesh statistics

    Example:
        >>> stats = MeshStatistics(mesh)
        >>> report = stats.generate_report()
        >>> print(report)
    """

    def __init__(self, mesh: MeshData):
        """Initialize with mesh data"""
        self.mesh = mesh

    def get_basic_stats(self) -> Dict[str, Any]:
        """Get basic mesh statistics"""
        return {
            'num_nodes': len(self.mesh.nodes),
            'num_elements': len(self.mesh.elements),
            'element_type': str(self.mesh.element_type),
        }

    def get_element_type_distribution(self) -> Dict[str, int]:
        """Get distribution of element types"""
        type_counts = Counter()
        for elem in self.mesh.elements.values():
            type_counts[str(elem.type)] += 1
        return dict(type_counts)

    def get_bounding_box(self) -> Dict[str, tuple]:
        """Get mesh bounding box"""
        if not self.mesh.nodes:
            return {'min': (0, 0, 0), 'max': (0, 0, 0), 'size': (0, 0, 0)}

        coords = np.array([[n.x, n.y, n.z] for n in self.mesh.nodes.values()])
        min_coords = coords.min(axis=0)
        max_coords = coords.max(axis=0)
        size = max_coords - min_coords

        return {
            'min': tuple(min_coords),
            'max': tuple(max_coords),
            'size': tuple(size),
            'center': tuple((min_coords + max_coords) / 2)
        }

    def get_element_size_stats(self) -> Dict[str, float]:
        """Get element size statistics"""
        if not self.mesh.elements:
            return {'min': 0, 'max': 0, 'mean': 0, 'std': 0}

        sizes = []
        for elem in self.mesh.elements.values():
            nodes = [self.mesh.nodes[nid] for nid in elem.nodes]
            coords = np.array([[n.x, n.y, n.z] for n in nodes])
            # Simple size estimate: max distance between nodes
            dists = []
            for i in range(len(coords)):
                for j in range(i+1, len(coords)):
                    dist = np.linalg.norm(coords[i] - coords[j])
                    dists.append(dist)
            if dists:
                sizes.append(max(dists))

        if not sizes:
            return {'min': 0, 'max': 0, 'mean': 0, 'std': 0}

        return {
            'min': float(np.min(sizes)),
            'max': float(np.max(sizes)),
            'mean': float(np.mean(sizes)),
            'std': float(np.std(sizes))
        }

    def get_connectivity_stats(self) -> Dict[str, Any]:
        """Get connectivity statistics"""
        node_connectivity = Counter()
        for elem in self.mesh.elements.values():
            for nid in elem.nodes:
                node_connectivity[nid] += 1

        if not node_connectivity:
            return {'min': 0, 'max': 0, 'mean': 0}

        conn_values = list(node_connectivity.values())
        return {
            'min_node_connectivity': min(conn_values),
            'max_node_connectivity': max(conn_values),
            'mean_node_connectivity': np.mean(conn_values)
        }

    def generate_report(self, detailed: bool = True) -> str:
        """
        Generate text report of mesh statistics

        Args:
            detailed: Include detailed statistics

        Returns:
            Formatted text report
        """
        lines = []
        lines.append("="*60)
        lines.append("MESH STATISTICS REPORT")
        lines.append("="*60)

        # Basic stats
        basic = self.get_basic_stats()
        lines.append("\nBasic Information:")
        lines.append(f"  Nodes:     {basic['num_nodes']:,}")
        lines.append(f"  Elements:  {basic['num_elements']:,}")
        lines.append(f"  Type:      {basic['element_type']}")

        # Element type distribution
        if detailed:
            type_dist = self.get_element_type_distribution()
            if len(type_dist) > 1:
                lines.append("\nElement Type Distribution:")
                for elem_type, count in type_dist.items():
                    pct = 100 * count / basic['num_elements']
                    lines.append(f"  {elem_type}: {count:,} ({pct:.1f}%)")

        # Bounding box
        bbox = self.get_bounding_box()
        lines.append("\nBounding Box:")
        lines.append(f"  Min: ({bbox['min'][0]:.3f}, {bbox['min'][1]:.3f}, {bbox['min'][2]:.3f})")
        lines.append(f"  Max: ({bbox['max'][0]:.3f}, {bbox['max'][1]:.3f}, {bbox['max'][2]:.3f})")
        lines.append(f"  Size: ({bbox['size'][0]:.3f}, {bbox['size'][1]:.3f}, {bbox['size'][2]:.3f})")
        lines.append(f"  Center: ({bbox['center'][0]:.3f}, {bbox['center'][1]:.3f}, {bbox['center'][2]:.3f})")

        # Element sizes
        if detailed and self.mesh.elements:
            size_stats = self.get_element_size_stats()
            lines.append("\nElement Sizes:")
            lines.append(f"  Min:  {size_stats['min']:.3e}")
            lines.append(f"  Max:  {size_stats['max']:.3e}")
            lines.append(f"  Mean: {size_stats['mean']:.3e}")
            lines.append(f"  Std:  {size_stats['std']:.3e}")

        # Connectivity
        if detailed and self.mesh.elements:
            conn = self.get_connectivity_stats()
            lines.append("\nConnectivity:")
            lines.append(f"  Min node connectivity: {conn['min_node_connectivity']}")
            lines.append(f"  Max node connectivity: {conn['max_node_connectivity']}")
            lines.append(f"  Avg node connectivity: {conn['mean_node_connectivity']:.1f}")

        lines.append("\n" + "="*60)

        return "\n".join(lines)

    def export_stats_dict(self) -> Dict[str, Any]:
        """Export all statistics as dictionary"""
        return {
            'basic': self.get_basic_stats(),
            'element_types': self.get_element_type_distribution(),
            'bounding_box': self.get_bounding_box(),
            'element_sizes': self.get_element_size_stats(),
            'connectivity': self.get_connectivity_stats()
        }


def print_mesh_statistics(mesh: MeshData, detailed: bool = True):
    """
    Convenience function to print mesh statistics

    Args:
        mesh: Mesh data
        detailed: Include detailed statistics

    Example:
        >>> print_mesh_statistics(mesh)
    """
    stats = MeshStatistics(mesh)
    print(stats.generate_report(detailed=detailed))
