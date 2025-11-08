"""
Parallel Processing Utilities
=============================

Performance utilities and benchmarking tools for parallel processing.

Author: KooMeshGenerator Team
"""

import logging
import time
import multiprocessing
from typing import Callable, Dict, Any, Optional
from functools import wraps
import numpy as np

logger = logging.getLogger(__name__)


def get_optimal_workers(
    num_tasks: int,
    overhead_ratio: float = 0.1,
    max_workers: Optional[int] = None
) -> int:
    """
    Calculate optimal number of workers for a given number of tasks.

    Takes into account:
    - Number of CPU cores
    - Number of tasks
    - Parallel overhead

    Parameters:
        num_tasks: Number of independent tasks
        overhead_ratio: Estimated parallel overhead (0.0 - 1.0)
        max_workers: Maximum workers to use (default: all cores)

    Returns:
        Optimal number of workers

    Example:
        >>> optimal = get_optimal_workers(num_tasks=1000)
        >>> print(f"Use {optimal} workers for 1000 tasks")
    """
    available_cores = multiprocessing.cpu_count()

    if max_workers:
        available_cores = min(available_cores, max_workers)

    # For very small numbers of tasks, use fewer workers
    if num_tasks < 10:
        return 1
    elif num_tasks < 100:
        return min(4, available_cores)

    # Estimate efficiency
    # More workers = more overhead
    # Sweet spot is usually 50-80% of cores for CPU-bound tasks

    if overhead_ratio < 0.2:
        # Low overhead: can use all cores
        optimal = available_cores
    elif overhead_ratio < 0.5:
        # Medium overhead: use 75% of cores
        optimal = int(available_cores * 0.75)
    else:
        # High overhead: use 50% of cores
        optimal = max(1, int(available_cores * 0.5))

    # Don't use more workers than tasks
    optimal = min(optimal, num_tasks)

    return optimal


def benchmark(
    func: Callable,
    *args,
    n_runs: int = 3,
    warmup: int = 1,
    **kwargs
) -> Dict[str, Any]:
    """
    Benchmark a function with timing statistics.

    Parameters:
        func: Function to benchmark
        *args: Positional arguments for function
        n_runs: Number of benchmark runs
        warmup: Number of warmup runs (not counted)
        **kwargs: Keyword arguments for function

    Returns:
        Dictionary with timing statistics

    Example:
        >>> stats = benchmark(checker.check_mesh, mesh_data, n_runs=5)
        >>> print(f"Mean time: {stats['mean']:.3f}s")
    """
    # Warmup runs
    for _ in range(warmup):
        func(*args, **kwargs)

    # Benchmark runs
    times = []
    for _ in range(n_runs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        times.append(elapsed)

    times = np.array(times)

    stats = {
        'mean': float(np.mean(times)),
        'median': float(np.median(times)),
        'std': float(np.std(times)),
        'min': float(np.min(times)),
        'max': float(np.max(times)),
        'n_runs': n_runs,
        'warmup': warmup
    }

    logger.info(f"Benchmark: {func.__name__} - mean={stats['mean']:.3f}s, std={stats['std']:.3f}s ({n_runs} runs)")

    return stats


def compare_parallel_speedup(
    serial_func: Callable,
    parallel_func: Callable,
    *args,
    n_runs: int = 3,
    **kwargs
) -> Dict[str, Any]:
    """
    Compare serial vs parallel performance.

    Parameters:
        serial_func: Serial version of function
        parallel_func: Parallel version of function
        *args: Positional arguments for both functions
        n_runs: Number of benchmark runs
        **kwargs: Keyword arguments for both functions

    Returns:
        Dictionary with comparison statistics

    Example:
        >>> stats = compare_parallel_speedup(
        ...     serial_checker.check_mesh,
        ...     parallel_checker.check_mesh,
        ...     mesh_data,
        ...     n_runs=5
        ... )
        >>> print(f"Speedup: {stats['speedup']:.2f}x")
    """
    # Benchmark serial
    serial_stats = benchmark(serial_func, *args, n_runs=n_runs, **kwargs)

    # Benchmark parallel
    parallel_stats = benchmark(parallel_func, *args, n_runs=n_runs, **kwargs)

    # Calculate speedup
    speedup = serial_stats['mean'] / parallel_stats['mean']

    # Try to get number of workers
    n_workers = multiprocessing.cpu_count()
    if hasattr(parallel_func, '__self__'):
        obj = parallel_func.__self__
        if hasattr(obj, 'n_workers'):
            n_workers = obj.n_workers

    efficiency = speedup / n_workers

    comparison = {
        'serial_mean': serial_stats['mean'],
        'serial_std': serial_stats['std'],
        'parallel_mean': parallel_stats['mean'],
        'parallel_std': parallel_stats['std'],
        'speedup': speedup,
        'efficiency': efficiency,
        'n_workers': n_workers,
        'n_runs': n_runs
    }

    logger.info(f"Speedup: {speedup:.2f}x with {n_workers} workers (efficiency: {efficiency*100:.1f}%)")

    return comparison


class PerformanceMonitor:
    """
    Monitor and log performance of operations.

    Example:
        >>> monitor = PerformanceMonitor()
        >>> with monitor.time("mesh_generation"):
        ...     mesh = mesher.mesh_shape(shape)
        >>> print(monitor.get_summary())
    """

    def __init__(self):
        """Initialize performance monitor."""
        self.timings = {}
        self.counts = {}

    def time(self, operation: str):
        """
        Context manager for timing operations.

        Parameters:
            operation: Operation name

        Example:
            >>> with monitor.time("quality_check"):
            ...     checker.check_mesh(mesh)
        """
        return _TimingContext(self, operation)

    def record(self, operation: str, duration: float):
        """
        Record timing for an operation.

        Parameters:
            operation: Operation name
            duration: Duration in seconds
        """
        if operation not in self.timings:
            self.timings[operation] = []
            self.counts[operation] = 0

        self.timings[operation].append(duration)
        self.counts[operation] += 1

    def get_summary(self) -> Dict[str, Dict]:
        """
        Get summary statistics for all operations.

        Returns:
            Dictionary of operation statistics
        """
        summary = {}

        for operation, times in self.timings.items():
            times_array = np.array(times)

            summary[operation] = {
                'count': self.counts[operation],
                'total': float(np.sum(times_array)),
                'mean': float(np.mean(times_array)),
                'median': float(np.median(times_array)),
                'std': float(np.std(times_array)),
                'min': float(np.min(times_array)),
                'max': float(np.max(times_array))
            }

        return summary

    def print_summary(self):
        """Print formatted summary of all timings."""
        summary = self.get_summary()

        print("\nPerformance Summary:")
        print("=" * 80)
        print(f"{'Operation':<30} {'Count':>8} {'Total':>10} {'Mean':>10} {'Std':>10}")
        print("-" * 80)

        for operation, stats in summary.items():
            print(f"{operation:<30} {stats['count']:>8} {stats['total']:>10.3f}s {stats['mean']:>10.3f}s {stats['std']:>10.3f}s")

        print("=" * 80)


class _TimingContext:
    """Context manager for timing operations."""

    def __init__(self, monitor: PerformanceMonitor, operation: str):
        self.monitor = monitor
        self.operation = operation
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        self.monitor.record(self.operation, duration)


def parallel_timer(func: Callable) -> Callable:
    """
    Decorator to time function execution.

    Parameters:
        func: Function to time

    Returns:
        Wrapped function that logs execution time

    Example:
        >>> @parallel_timer
        ... def process_mesh(mesh):
        ...     return checker.check_mesh(mesh)
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start

        logger.info(f"{func.__name__} completed in {elapsed:.3f}s")

        # Add timing to result if it's a dict
        if isinstance(result, dict):
            result['execution_time'] = elapsed

        return result

    return wrapper
