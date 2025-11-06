"""
Mesh Smoothing Module
=====================

This module provides various mesh smoothing algorithms to improve mesh quality.
Smoothing algorithms relocate nodes to improve element shapes while preserving
mesh topology and geometry.

Features:
- Laplacian smoothing
- Smart Laplacian (boundary-preserving)
- Taubin smoothing (shrinkage prevention)
- Quality-based smoothing
- Angle-weighted smoothing

Usage:
    >>> from koomesh.meshing.mesh_smoother import MeshSmoother
    >>> smoother = MeshSmoother(mesh_data)
    >>> smoother.laplacian_smooth(iterations=10)
    >>> # or
    >>> smoother.smart_laplacian(iterations=10, preserve_boundary=True)
"""

import logging
from typing import Dict, List, Set, Optional, Tuple
import numpy as np
from collections import defaultdict

from koomesh.meshing.mesh_data import MeshData, Element, Node, ElementType
from koomesh.meshing.quality_checker import QualityChecker


class MeshSmoother:
    """
    Mesh smoothing class

    Provides various algorithms to improve mesh quality by relocating nodes.
    All smoothing preserves mesh topology (connectivity).

    Example:
        >>> smoother = MeshSmoother(mesh_data)
        >>> initial_quality = smoother.get_quality_stats()
        >>> smoother.smart_laplacian(iterations=10)
        >>> final_quality = smoother.get_quality_stats()
        >>> print(f"Quality improved from {initial_quality} to {final_quality}")
    """

    def __init__(self, mesh_data: MeshData):
        """
        Initialize mesh smoother

        Args:
            mesh_data: MeshData object to smooth
        """
        self.logger = logging.getLogger(__name__)
        self.mesh = mesh_data
        self.quality_checker = QualityChecker()

        # Build node connectivity graph
        self._build_node_connectivity()

        # Identify boundary nodes
        self._identify_boundary_nodes()

    def _build_node_connectivity(self):
        """Build node-to-node connectivity graph"""
        self.logger.debug("Building node connectivity graph...")

        # Node adjacency: node_id -> set of adjacent node_ids
        self.node_adjacency: Dict[int, Set[int]] = defaultdict(set)

        # Node-element map: node_id -> set of element_ids
        self.node_elements: Dict[int, Set[int]] = defaultdict(set)

        # Build connectivity from elements
        for elem in self.mesh.elements.values():
            nodes = elem.nodes

            # Record which elements each node belongs to
            for node_id in nodes:
                self.node_elements[node_id].add(elem.id)

            # Build adjacency (nodes in same element are adjacent)
            for i, node_i in enumerate(nodes):
                for j, node_j in enumerate(nodes):
                    if i != j:
                        self.node_adjacency[node_i].add(node_j)

        self.logger.debug(f"Built connectivity for {len(self.node_adjacency)} nodes")

    def _identify_boundary_nodes(self):
        """Identify boundary (surface) nodes"""
        self.logger.debug("Identifying boundary nodes...")

        self.boundary_nodes: Set[int] = set()

        # Count face occurrences
        # Boundary faces appear only once, internal faces appear twice
        face_count: Dict[Tuple[int, ...], int] = defaultdict(int)

        for elem in self.mesh.elements.values():
            # Get all faces of this element
            num_faces = self._get_num_faces(elem.type)

            for face_id in range(num_faces):
                try:
                    face_nodes = elem.get_face_nodes(face_id)
                    # Sort to create canonical representation
                    face_key = tuple(sorted(face_nodes))
                    face_count[face_key] += 1
                except:
                    pass

        # Boundary faces appear only once
        for face_key, count in face_count.items():
            if count == 1:
                # Add all nodes of this face to boundary set
                self.boundary_nodes.update(face_key)

        self.logger.debug(f"Identified {len(self.boundary_nodes)} boundary nodes")

    def _get_num_faces(self, elem_type: ElementType) -> int:
        """Get number of faces for element type"""
        if elem_type.is_hex():
            return 6
        elif elem_type.is_tet():
            return 4
        elif elem_type == ElementType.PRISM6:
            return 5
        elif elem_type == ElementType.PYRAMID5:
            return 5
        else:
            return 0

    def laplacian_smooth(self, iterations: int = 10, relaxation: float = 0.5):
        """
        Laplacian smoothing

        Basic smoothing algorithm that moves each node to the average position
        of its neighbors. Simple but effective.

        Args:
            iterations: Number of smoothing iterations
            relaxation: Relaxation factor (0-1). 1.0 = full move, 0.5 = half move

        Note:
            This may cause mesh shrinkage. Consider using taubin_smooth() instead.
        """
        self.logger.info(f"Applying Laplacian smoothing ({iterations} iterations)...")

        for iteration in range(iterations):
            new_positions = {}

            # Compute new positions for all nodes
            for node_id, node in self.mesh.nodes.items():
                if node_id not in self.node_adjacency:
                    continue

                # Get adjacent nodes
                adjacent_ids = self.node_adjacency[node_id]
                if not adjacent_ids:
                    continue

                # Compute average position of neighbors
                avg_pos = np.zeros(3)
                for adj_id in adjacent_ids:
                    adj_node = self.mesh.get_node(adj_id)
                    avg_pos += adj_node.coordinates()

                avg_pos /= len(adjacent_ids)

                # Apply relaxation
                current_pos = node.coordinates()
                new_pos = current_pos + relaxation * (avg_pos - current_pos)
                new_positions[node_id] = new_pos

            # Update node positions
            for node_id, new_pos in new_positions.items():
                node = self.mesh.get_node(node_id)
                node.x, node.y, node.z = new_pos

            self.logger.debug(f"  Iteration {iteration + 1}/{iterations} complete")

        self.logger.info("Laplacian smoothing complete")

    def smart_laplacian(self,
                       iterations: int = 10,
                       relaxation: float = 0.5,
                       preserve_boundary: bool = True,
                       quality_threshold: Optional[float] = None):
        """
        Smart Laplacian smoothing with boundary preservation

        Enhanced Laplacian that preserves boundary nodes and optionally
        only smooths poor-quality regions.

        Args:
            iterations: Number of smoothing iterations
            relaxation: Relaxation factor (0-1)
            preserve_boundary: If True, don't move boundary nodes
            quality_threshold: If specified, only smooth nodes with element quality below this

        Example:
            >>> smoother.smart_laplacian(iterations=10, preserve_boundary=True, quality_threshold=0.3)
        """
        self.logger.info(f"Applying Smart Laplacian smoothing ({iterations} iterations)...")

        # Identify poor quality nodes if threshold specified
        poor_quality_nodes = None
        if quality_threshold is not None:
            poor_quality_nodes = self._identify_poor_quality_nodes(quality_threshold)
            self.logger.info(f"Focusing on {len(poor_quality_nodes)} poor-quality nodes")

        for iteration in range(iterations):
            new_positions = {}

            for node_id, node in self.mesh.nodes.items():
                # Skip if boundary and preserving boundary
                if preserve_boundary and node_id in self.boundary_nodes:
                    continue

                # Skip if not in poor quality region
                if poor_quality_nodes is not None and node_id not in poor_quality_nodes:
                    continue

                if node_id not in self.node_adjacency:
                    continue

                adjacent_ids = self.node_adjacency[node_id]
                if not adjacent_ids:
                    continue

                # Compute average position
                avg_pos = np.zeros(3)
                for adj_id in adjacent_ids:
                    adj_node = self.mesh.get_node(adj_id)
                    avg_pos += adj_node.coordinates()

                avg_pos /= len(adjacent_ids)

                # Apply relaxation
                current_pos = node.coordinates()
                new_pos = current_pos + relaxation * (avg_pos - current_pos)
                new_positions[node_id] = new_pos

            # Update positions
            for node_id, new_pos in new_positions.items():
                node = self.mesh.get_node(node_id)
                node.x, node.y, node.z = new_pos

            self.logger.debug(f"  Iteration {iteration + 1}/{iterations} complete")

        self.logger.info("Smart Laplacian smoothing complete")

    def taubin_smooth(self,
                     iterations: int = 10,
                     lambda_param: float = 0.5,
                     mu_param: float = -0.53,
                     preserve_boundary: bool = True):
        """
        Taubin smoothing (low-pass filter)

        Two-step smoothing that prevents mesh shrinkage:
        1. Inflation step (positive lambda)
        2. Deflation step (negative mu)

        Args:
            iterations: Number of smoothing iterations (each = inflate + deflate)
            lambda_param: Inflation parameter (positive, typically 0.5)
            mu_param: Deflation parameter (negative, typically -0.53)
            preserve_boundary: If True, don't move boundary nodes

        Reference:
            Taubin, G. (1995). "A signal processing approach to fair surface design"

        Example:
            >>> smoother.taubin_smooth(iterations=10)
        """
        self.logger.info(f"Applying Taubin smoothing ({iterations} iterations)...")

        for iteration in range(iterations):
            # Step 1: Inflation (lambda > 0)
            self._taubin_step(lambda_param, preserve_boundary)

            # Step 2: Deflation (mu < 0)
            self._taubin_step(mu_param, preserve_boundary)

            self.logger.debug(f"  Iteration {iteration + 1}/{iterations} complete")

        self.logger.info("Taubin smoothing complete")

    def _taubin_step(self, weight: float, preserve_boundary: bool):
        """Single step of Taubin smoothing"""
        new_positions = {}

        for node_id, node in self.mesh.nodes.items():
            if preserve_boundary and node_id in self.boundary_nodes:
                continue

            if node_id not in self.node_adjacency:
                continue

            adjacent_ids = self.node_adjacency[node_id]
            if not adjacent_ids:
                continue

            # Compute Laplacian
            current_pos = node.coordinates()
            avg_pos = np.zeros(3)

            for adj_id in adjacent_ids:
                adj_node = self.mesh.get_node(adj_id)
                avg_pos += adj_node.coordinates()

            avg_pos /= len(adjacent_ids)
            laplacian = avg_pos - current_pos

            # Update position
            new_pos = current_pos + weight * laplacian
            new_positions[node_id] = new_pos

        # Apply updates
        for node_id, new_pos in new_positions.items():
            node = self.mesh.get_node(node_id)
            node.x, node.y, node.z = new_pos

    def angle_weighted_smooth(self,
                            iterations: int = 10,
                            preserve_boundary: bool = True):
        """
        Angle-weighted Laplacian smoothing

        Uses angle-based weights for better shape preservation.
        Weights are based on angles at the node being smoothed.

        Args:
            iterations: Number of smoothing iterations
            preserve_boundary: If True, don't move boundary nodes
        """
        self.logger.info(f"Applying angle-weighted smoothing ({iterations} iterations)...")

        for iteration in range(iterations):
            new_positions = {}

            for node_id, node in self.mesh.nodes.items():
                if preserve_boundary and node_id in self.boundary_nodes:
                    continue

                if node_id not in self.node_adjacency:
                    continue

                adjacent_ids = list(self.node_adjacency[node_id])
                if len(adjacent_ids) < 2:
                    continue

                # Compute angle-weighted average
                current_pos = node.coordinates()
                weighted_sum = np.zeros(3)
                weight_sum = 0.0

                # For each pair of adjacent nodes, compute angle
                for i, adj_id in enumerate(adjacent_ids):
                    adj_pos = self.mesh.get_node(adj_id).coordinates()

                    # Get next adjacent node (circular)
                    next_id = adjacent_ids[(i + 1) % len(adjacent_ids)]
                    next_pos = self.mesh.get_node(next_id).coordinates()

                    # Compute angle at current node
                    v1 = adj_pos - current_pos
                    v2 = next_pos - current_pos

                    v1_norm = np.linalg.norm(v1)
                    v2_norm = np.linalg.norm(v2)

                    if v1_norm > 1e-10 and v2_norm > 1e-10:
                        cos_angle = np.dot(v1, v2) / (v1_norm * v2_norm)
                        cos_angle = np.clip(cos_angle, -1.0, 1.0)
                        angle = np.arccos(cos_angle)

                        # Use angle as weight
                        weight = angle
                        weighted_sum += weight * adj_pos
                        weight_sum += weight

                if weight_sum > 1e-10:
                    new_pos = weighted_sum / weight_sum
                    new_positions[node_id] = new_pos

            # Apply updates
            for node_id, new_pos in new_positions.items():
                node = self.mesh.get_node(node_id)
                node.x, node.y, node.z = new_pos

            self.logger.debug(f"  Iteration {iteration + 1}/{iterations} complete")

        self.logger.info("Angle-weighted smoothing complete")

    def _identify_poor_quality_nodes(self, threshold: float) -> Set[int]:
        """
        Identify nodes that belong to poor-quality elements

        Args:
            threshold: Quality threshold (Jacobian)

        Returns:
            Set of node IDs belonging to poor-quality elements
        """
        poor_nodes = set()

        for elem_id, elem in self.mesh.elements.items():
            # Get element coordinates
            coords = self.mesh.get_element_coordinates(elem_id)

            # Compute quality (Jacobian)
            jacobian = self.quality_checker._compute_jacobian(elem, coords)

            if jacobian < threshold:
                # Add all nodes of this element
                poor_nodes.update(elem.nodes)

        return poor_nodes

    def get_quality_stats(self) -> Dict:
        """
        Get current mesh quality statistics

        Returns:
            Dictionary with quality metrics
        """
        report = self.quality_checker.check_mesh(self.mesh)

        return {
            'num_elements': report.num_elements,
            'jacobian_min': report.jacobian.get('min', 0),
            'jacobian_mean': report.jacobian.get('mean', 0),
            'jacobian_max': report.jacobian.get('max', 0),
        }

    def smooth_with_quality_monitoring(self,
                                      method: str = 'smart_laplacian',
                                      iterations: int = 10,
                                      min_quality_improvement: float = 0.01):
        """
        Smooth mesh with quality monitoring

        Stops if quality stops improving or starts degrading.

        Args:
            method: Smoothing method ('laplacian', 'smart_laplacian', 'taubin')
            iterations: Maximum iterations
            min_quality_improvement: Minimum improvement to continue (relative)

        Returns:
            Number of iterations performed
        """
        self.logger.info(f"Smoothing with quality monitoring ({method})...")

        prev_quality = self.get_quality_stats()
        prev_min = prev_quality['jacobian_min']

        for i in range(iterations):
            # Perform one iteration
            if method == 'laplacian':
                self.laplacian_smooth(iterations=1)
            elif method == 'smart_laplacian':
                self.smart_laplacian(iterations=1)
            elif method == 'taubin':
                self.taubin_smooth(iterations=1)
            else:
                raise ValueError(f"Unknown method: {method}")

            # Check quality
            current_quality = self.get_quality_stats()
            current_min = current_quality['jacobian_min']

            improvement = (current_min - prev_min) / abs(prev_min + 1e-10)

            self.logger.debug(f"  Iteration {i + 1}: min Jacobian = {current_min:.6f}, "
                            f"improvement = {improvement:.4f}")

            # Stop if quality degraded or improvement too small
            if improvement < -0.001:  # Quality degraded
                self.logger.warning("Quality degraded, stopping")
                return i

            if i > 5 and improvement < min_quality_improvement:  # No significant improvement
                self.logger.info(f"Converged after {i + 1} iterations")
                return i + 1

            prev_min = current_min

        self.logger.info(f"Completed {iterations} iterations")
        return iterations

    def get_summary(self) -> Dict:
        """
        Get smoother summary

        Returns:
            Dictionary with smoother information
        """
        return {
            'num_nodes': self.mesh.num_nodes(),
            'num_elements': self.mesh.num_elements(),
            'num_boundary_nodes': len(self.boundary_nodes),
            'num_interior_nodes': self.mesh.num_nodes() - len(self.boundary_nodes),
        }
