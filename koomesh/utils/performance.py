"""
Performance Monitoring and Profiling Utilities
==============================================

This module provides tools for monitoring and profiling performance:
- Memory usage tracking
- Execution time profiling
- Resource monitoring
- Performance metrics collection

Usage:
    >>> from koomesh.utils.performance import MemoryMonitor, PerformanceProfiler
    >>> with MemoryMonitor() as monitor:
    ...     # Your code here
    ...     pass
    >>> print(f"Peak memory: {monitor.peak_memory_mb:.2f} MB")
"""

import psutil
import time
import functools
from typing import Optional, Callable, Dict, Any, List
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """
    Performance metrics for an operation

    Attributes:
        operation: Name of operation
        start_time: Start timestamp
        end_time: End timestamp
        duration: Duration in seconds
        memory_start_mb: Memory at start (MB)
        memory_end_mb: Memory at end (MB)
        memory_peak_mb: Peak memory (MB)
        memory_delta_mb: Memory change (MB)
    """
    operation: str
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration: float = 0.0
    memory_start_mb: float = 0.0
    memory_end_mb: float = 0.0
    memory_peak_mb: float = 0.0
    memory_delta_mb: float = 0.0
    custom_metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'operation': self.operation,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_seconds': self.duration,
            'memory_start_mb': self.memory_start_mb,
            'memory_end_mb': self.memory_end_mb,
            'memory_peak_mb': self.memory_peak_mb,
            'memory_delta_mb': self.memory_delta_mb,
            **self.custom_metrics
        }

    def print_summary(self):
        """Print performance summary"""
        print(f"\n{'='*60}")
        print(f"Performance Metrics: {self.operation}")
        print(f"{'='*60}")
        print(f"Duration:        {self.duration:.3f} seconds")
        print(f"Memory Start:    {self.memory_start_mb:.2f} MB")
        print(f"Memory End:      {self.memory_end_mb:.2f} MB")
        print(f"Memory Peak:     {self.memory_peak_mb:.2f} MB")
        print(f"Memory Delta:    {self.memory_delta_mb:+.2f} MB")

        if self.custom_metrics:
            print(f"\nCustom Metrics:")
            for key, value in self.custom_metrics.items():
                print(f"  {key}: {value}")
        print(f"{'='*60}\n")


class MemoryMonitor:
    """
    Context manager for monitoring memory usage

    Example:
        >>> with MemoryMonitor() as monitor:
        ...     # Code to monitor
        ...     data = load_large_file()
        >>> print(f"Peak memory: {monitor.peak_memory_mb:.2f} MB")
    """

    def __init__(self, interval: float = 0.1):
        """
        Initialize memory monitor

        Args:
            interval: Sampling interval in seconds
        """
        self.interval = interval
        self.process = psutil.Process()
        self.start_memory_mb = 0.0
        self.peak_memory_mb = 0.0
        self.end_memory_mb = 0.0
        self._monitoring = False

    def __enter__(self):
        """Start monitoring"""
        self.start_memory_mb = self._get_memory_mb()
        self.peak_memory_mb = self.start_memory_mb
        self._monitoring = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop monitoring"""
        self._monitoring = False
        self.end_memory_mb = self._get_memory_mb()
        self.peak_memory_mb = max(self.peak_memory_mb, self.end_memory_mb)

    def _get_memory_mb(self) -> float:
        """Get current memory usage in MB"""
        return self.process.memory_info().rss / 1024 / 1024

    def update_peak(self):
        """Update peak memory (call periodically)"""
        if self._monitoring:
            current = self._get_memory_mb()
            self.peak_memory_mb = max(self.peak_memory_mb, current)

    @property
    def delta_mb(self) -> float:
        """Memory delta from start to end"""
        return self.end_memory_mb - self.start_memory_mb


class PerformanceProfiler:
    """
    Performance profiler with memory and time tracking

    Example:
        >>> profiler = PerformanceProfiler()
        >>> with profiler.profile("operation_name"):
        ...     # Code to profile
        ...     process_data()
        >>> profiler.print_summary()
    """

    def __init__(self):
        """Initialize profiler"""
        self.metrics: List[PerformanceMetrics] = []
        self.current_metrics: Optional[PerformanceMetrics] = None

    def profile(self, operation: str):
        """
        Context manager for profiling an operation

        Args:
            operation: Name of operation to profile

        Example:
            >>> with profiler.profile("mesh_generation"):
            ...     generate_mesh()
        """
        return ProfileContext(self, operation)

    def start_operation(self, operation: str) -> PerformanceMetrics:
        """Start profiling an operation"""
        process = psutil.Process()
        metrics = PerformanceMetrics(
            operation=operation,
            start_time=datetime.now(),
            memory_start_mb=process.memory_info().rss / 1024 / 1024
        )
        self.current_metrics = metrics
        return metrics

    def end_operation(self, metrics: PerformanceMetrics):
        """End profiling an operation"""
        process = psutil.Process()
        metrics.end_time = datetime.now()
        metrics.memory_end_mb = process.memory_info().rss / 1024 / 1024
        metrics.duration = (metrics.end_time - metrics.start_time).total_seconds()
        metrics.memory_delta_mb = metrics.memory_end_mb - metrics.memory_start_mb
        metrics.memory_peak_mb = max(metrics.memory_end_mb, metrics.memory_start_mb)

        self.metrics.append(metrics)
        self.current_metrics = None

    def add_metric(self, key: str, value: Any):
        """Add custom metric to current operation"""
        if self.current_metrics:
            self.current_metrics.custom_metrics[key] = value

    def get_metrics(self, operation: Optional[str] = None) -> List[PerformanceMetrics]:
        """
        Get metrics for operation(s)

        Args:
            operation: Operation name (None for all)

        Returns:
            List of performance metrics
        """
        if operation is None:
            return self.metrics
        return [m for m in self.metrics if m.operation == operation]

    def print_summary(self):
        """Print summary of all operations"""
        if not self.metrics:
            print("No performance metrics recorded.")
            return

        print(f"\n{'='*70}")
        print(f"Performance Summary ({len(self.metrics)} operations)")
        print(f"{'='*70}")

        total_time = sum(m.duration for m in self.metrics)
        total_memory = sum(m.memory_delta_mb for m in self.metrics)

        print(f"Total Duration: {total_time:.3f} seconds")
        print(f"Total Memory Delta: {total_memory:+.2f} MB")
        print()

        for metrics in self.metrics:
            print(f"  {metrics.operation}:")
            print(f"    Duration: {metrics.duration:.3f}s")
            print(f"    Memory: {metrics.memory_delta_mb:+.2f}MB (peak: {metrics.memory_peak_mb:.2f}MB)")
            if metrics.custom_metrics:
                for key, value in metrics.custom_metrics.items():
                    print(f"    {key}: {value}")

        print(f"{'='*70}\n")

    def export_to_json(self, filepath: Path):
        """Export metrics to JSON file"""
        import json

        data = {
            'timestamp': datetime.now().isoformat(),
            'total_operations': len(self.metrics),
            'total_duration': sum(m.duration for m in self.metrics),
            'operations': [m.to_dict() for m in self.metrics]
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def clear(self):
        """Clear all metrics"""
        self.metrics.clear()
        self.current_metrics = None


class ProfileContext:
    """Context manager for profiling"""

    def __init__(self, profiler: PerformanceProfiler, operation: str):
        self.profiler = profiler
        self.operation = operation
        self.metrics: Optional[PerformanceMetrics] = None

    def __enter__(self):
        self.metrics = self.profiler.start_operation(self.operation)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.metrics:
            self.profiler.end_operation(self.metrics)

    def add_metric(self, key: str, value: Any):
        """Add custom metric"""
        self.profiler.add_metric(key, value)


def profile_function(profiler: Optional[PerformanceProfiler] = None):
    """
    Decorator to profile function performance

    Args:
        profiler: PerformanceProfiler instance (creates new if None)

    Example:
        >>> @profile_function()
        ... def process_data():
        ...     # Heavy computation
        ...     pass
    """
    def decorator(func: Callable) -> Callable:
        _profiler = profiler or PerformanceProfiler()

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with _profiler.profile(func.__name__):
                result = func(*args, **kwargs)
            return result

        # Attach profiler to function for access
        wrapper.profiler = _profiler
        return wrapper

    return decorator


def measure_time(func: Callable) -> Callable:
    """
    Simple decorator to measure and log execution time

    Example:
        >>> @measure_time
        ... def slow_function():
        ...     time.sleep(1)
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start

        logger.info(f"{func.__name__} completed in {duration:.3f}s")
        return result

    return wrapper


def get_system_info() -> Dict[str, Any]:
    """
    Get system resource information

    Returns:
        Dictionary with system info
    """
    virtual_memory = psutil.virtual_memory()

    return {
        'cpu_count': psutil.cpu_count(),
        'cpu_percent': psutil.cpu_percent(interval=1),
        'memory_total_gb': virtual_memory.total / 1024 / 1024 / 1024,
        'memory_available_gb': virtual_memory.available / 1024 / 1024 / 1024,
        'memory_percent': virtual_memory.percent,
        'disk_usage_percent': psutil.disk_usage('/').percent,
    }


def check_memory_available(required_mb: float) -> bool:
    """
    Check if sufficient memory is available

    Args:
        required_mb: Required memory in MB

    Returns:
        True if sufficient memory available
    """
    available_mb = psutil.virtual_memory().available / 1024 / 1024
    return available_mb >= required_mb


def estimate_memory_for_mesh(num_elements: int, element_type: str = 'tet4') -> float:
    """
    Estimate memory requirement for mesh

    Args:
        num_elements: Number of elements
        element_type: Type of elements

    Returns:
        Estimated memory in MB
    """
    # Rough estimates based on element type
    bytes_per_element = {
        'tet4': 200,   # 4 nodes + data
        'tet10': 400,  # 10 nodes + data
        'hex8': 300,   # 8 nodes + data
        'hex20': 600,  # 20 nodes + data
    }

    bytes_per_elem = bytes_per_element.get(element_type, 250)
    total_bytes = num_elements * bytes_per_elem

    # Add overhead (30%)
    total_bytes *= 1.3

    return total_bytes / 1024 / 1024  # Convert to MB
