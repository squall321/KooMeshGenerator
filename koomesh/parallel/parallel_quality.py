"""
Parallel Quality Checker
========================

High-performance parallel mesh quality checking using multiprocessing.

Parallelizes element-wise quality computations across CPU cores for significant
speedup on large meshes.

Author: KooMeshGenerator Team
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import numpy as np
from joblib import Parallel, delayed
import multiprocessing

from koomesh.meshing.mesh_data import MeshData, Element
from koomesh.meshing.quality_checker import QualityChecker, QualityReport

logger = logging.getLogger(__name__)


def _compute_element_quality(element: Element, nodes_dict: Dict, checker: QualityChecker) -> Dict:
    """
    Compute quality metrics for a single element.

    Worker function for parallel processing.

    Parameters:
        element: Element to check
        nodes_dict: Dictionary of node ID to Node
        checker: QualityChecker instance

    Returns:
        Dictionary with element quality metrics
    """
    # Create temporary mesh data with just this element and its nodes
    temp_mesh = MeshData(element_type=element.type)
    temp_mesh.nodes = nodes_dict
    temp_mesh.elements = {element.id: element}

    # Compute metrics
    result = {
        'element_id': element.id,
        'aspect_ratio': checker._compute_aspect_ratio(element, temp_mesh),
        'jacobian': checker._compute_jacobian(element, temp_mesh),
        'skewness': checker._compute_skewness(element, temp_mesh),
    }

    # Compute volume
    coords = np.array([
        nodes_dict[nid].coordinates()
        for nid in element.nodes
    ])
    result['volume'] = checker._compute_volume(coords)

    return result


class ParallelQualityChecker:
    """
    Parallel mesh quality checker using multiprocessing.

    Provides significant speedup over serial QualityChecker for large meshes
    by distributing element quality computations across CPU cores.

    Attributes:
        n_jobs: Number of parallel jobs (-1 for all cores, -2 for all but one)
        batch_size: Elements per batch for parallel processing
        verbose: Show progress during checking

    Example:
        >>> checker = ParallelQualityChecker(n_jobs=-1)
        >>> result = checker.check_mesh(mesh_data)
        >>> print(f"Speedup: {result.metadata['speedup']:.2f}x")
    """

    def __init__(
        self,
        n_jobs: int = -1,
        batch_size: int = 100,
        verbose: int = 0,
        aspect_ratio_threshold: float = 10.0,
        jacobian_threshold: float = 0.1,
        skewness_threshold: float = 0.8,
    ):
        """
        Initialize parallel quality checker.

        Parameters:
            n_jobs: Number of parallel jobs (-1 = all cores, -2 = all but one)
            batch_size: Number of elements per batch
            verbose: Verbosity level (0 = silent, 1 = progress, 2 = debug)
            aspect_ratio_threshold: Maximum acceptable aspect ratio
            jacobian_threshold: Minimum acceptable Jacobian
            skewness_threshold: Maximum acceptable skewness
        """
        self.n_jobs = n_jobs
        self.batch_size = batch_size
        self.verbose = verbose

        # Create base quality checker with same thresholds
        self.base_checker = QualityChecker(
            aspect_ratio_threshold=aspect_ratio_threshold,
            jacobian_threshold=jacobian_threshold,
            skewness_threshold=skewness_threshold
        )

        # Determine actual number of workers
        if n_jobs == -1:
            self.n_workers = multiprocessing.cpu_count()
        elif n_jobs == -2:
            self.n_workers = max(1, multiprocessing.cpu_count() - 1)
        else:
            self.n_workers = max(1, min(n_jobs, multiprocessing.cpu_count()))

        logger.info(f"ParallelQualityChecker initialized: {self.n_workers} workers")

    def check_mesh(self, mesh: MeshData) -> QualityReport:
        """
        Check mesh quality in parallel.

        Parameters:
            mesh: Mesh to check

        Returns:
            Quality report with statistics
        """
        import time
        start_time = time.time()

        logger.info(f"Parallel quality check: {len(mesh.elements)} elements, {self.n_workers} workers")

        # Prepare nodes dict for workers (avoid pickling whole mesh repeatedly)
        nodes_dict = mesh.nodes

        # Parallel computation
        results = Parallel(n_jobs=self.n_workers, verbose=self.verbose, batch_size=self.batch_size)(
            delayed(_compute_element_quality)(element, nodes_dict, self.base_checker)
            for element in mesh.elements.values()
        )

        # Aggregate results
        aspect_ratios = []
        jacobians = []
        skewnesses = []
        volumes = []

        for result in results:
            aspect_ratios.append(result['aspect_ratio'])
            jacobians.append(result['jacobian'])
            skewnesses.append(result['skewness'])
            volumes.append(result['volume'])

        aspect_ratios = np.array(aspect_ratios)
        jacobians = np.array(jacobians)
        skewnesses = np.array(skewnesses)
        volumes = np.array(volumes)

        # Build report
        report = QualityReport()
        report.num_elements = len(mesh.elements)

        # Aspect ratio stats
        report.aspect_ratio = {
            'min': float(np.min(aspect_ratios)),
            'max': float(np.max(aspect_ratios)),
            'mean': float(np.mean(aspect_ratios)),
            'median': float(np.median(aspect_ratios)),
            'std': float(np.std(aspect_ratios)),
            'bad_elements': int(np.sum(aspect_ratios > self.base_checker.aspect_ratio_threshold))
        }

        # Jacobian stats
        report.jacobian = {
            'min': float(np.min(jacobians)),
            'max': float(np.max(jacobians)),
            'mean': float(np.mean(jacobians)),
            'median': float(np.median(jacobians)),
            'std': float(np.std(jacobians)),
            'bad_elements': int(np.sum(jacobians < self.base_checker.jacobian_threshold))
        }

        # Skewness stats
        report.skewness = {
            'min': float(np.min(skewnesses)),
            'max': float(np.max(skewnesses)),
            'mean': float(np.mean(skewnesses)),
            'median': float(np.median(skewnesses)),
            'std': float(np.std(skewnesses)),
            'bad_elements': int(np.sum(skewnesses > self.base_checker.skewness_threshold))
        }

        # Element size stats
        report.element_size = {
            'min': float(np.min(volumes)),
            'max': float(np.max(volumes)),
            'mean': float(np.mean(volumes)),
            'median': float(np.median(volumes)),
            'std': float(np.std(volumes)),
            'bad_elements': 0
        }

        # Count bad elements
        report.num_bad_elements = (
            report.aspect_ratio['bad_elements'] +
            report.jacobian['bad_elements'] +
            report.skewness['bad_elements']
        )

        # Identify bad element IDs
        bad_elem_ids = []
        for i, (elem_id, element) in enumerate(mesh.elements.items()):
            if (aspect_ratios[i] > self.base_checker.aspect_ratio_threshold or
                jacobians[i] < self.base_checker.jacobian_threshold or
                skewnesses[i] > self.base_checker.skewness_threshold):
                bad_elem_ids.append(elem_id)

        report.bad_elements = bad_elem_ids

        # Add performance metadata
        elapsed_time = time.time() - start_time
        report.metadata = {
            'parallel': True,
            'n_workers': self.n_workers,
            'elapsed_time': elapsed_time,
            'elements_per_second': len(mesh.elements) / elapsed_time
        }

        logger.info(f"Parallel quality check complete: {elapsed_time:.3f}s, {report.metadata['elements_per_second']:.0f} elem/s")

        return report

    def compare_with_serial(self, mesh: MeshData) -> Dict:
        """
        Compare parallel vs serial performance.

        Parameters:
            mesh: Mesh to benchmark

        Returns:
            Dictionary with timing comparison
        """
        import time

        # Serial check
        serial_checker = QualityChecker()
        start = time.time()
        serial_result = serial_checker.check_mesh(mesh)
        serial_time = time.time() - start

        # Parallel check
        start = time.time()
        parallel_result = self.check_mesh(mesh)
        parallel_time = time.time() - start

        speedup = serial_time / parallel_time
        efficiency = speedup / self.n_workers

        return {
            'num_elements': len(mesh.elements),
            'serial_time': serial_time,
            'parallel_time': parallel_time,
            'speedup': speedup,
            'efficiency': efficiency,
            'n_workers': self.n_workers,
            'elements_per_second_serial': len(mesh.elements) / serial_time,
            'elements_per_second_parallel': len(mesh.elements) / parallel_time
        }
