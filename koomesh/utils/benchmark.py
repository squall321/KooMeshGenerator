"""
Performance Benchmarking Utilities
===================================

This module provides tools for benchmarking KooMesh performance.

Features:
- Execution time tracking
- Memory usage monitoring
- Element generation rates
- Throughput metrics
- Performance profiling

Usage:
    >>> from koomesh.utils.benchmark import Benchmark
    >>> with Benchmark("mesh_generation") as bench:
    ...     # perform operations
    ...     pass
    >>> bench.print_report()
"""

import time
import logging
from typing import Optional, Dict, List, Callable, Any
from dataclasses import dataclass, field
from pathlib import Path
import json
from datetime import datetime
from contextlib import contextmanager

# Try to import memory profiling
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


@dataclass
class BenchmarkResult:
    """
    Benchmark execution result

    Attributes:
        name: Benchmark name
        start_time: Start timestamp
        end_time: End timestamp
        duration: Execution duration (seconds)
        memory_start: Starting memory usage (bytes)
        memory_end: Ending memory usage (bytes)
        memory_peak: Peak memory usage (bytes)
        operations: Number of operations performed
        metrics: Additional custom metrics
    """
    name: str
    start_time: float
    end_time: float
    duration: float
    memory_start: Optional[int] = None
    memory_end: Optional[int] = None
    memory_peak: Optional[int] = None
    operations: int = 0
    metrics: Dict[str, Any] = field(default_factory=dict)

    @property
    def throughput(self) -> float:
        """Calculate operations per second"""
        if self.duration > 0 and self.operations > 0:
            return self.operations / self.duration
        return 0.0

    @property
    def memory_delta(self) -> Optional[int]:
        """Calculate memory usage change"""
        if self.memory_start is not None and self.memory_end is not None:
            return self.memory_end - self.memory_start
        return None

    def format_time(self, seconds: float) -> str:
        """Format time in human-readable format"""
        if seconds < 1:
            return f"{seconds*1000:.2f}ms"
        elif seconds < 60:
            return f"{seconds:.2f}s"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            secs = seconds % 60
            return f"{minutes}m {secs:.1f}s"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}h {minutes}m"

    def format_memory(self, bytes: Optional[int]) -> str:
        """Format memory in human-readable format"""
        if bytes is None:
            return "N/A"

        if bytes < 1024:
            return f"{bytes} B"
        elif bytes < 1024 ** 2:
            return f"{bytes / 1024:.2f} KB"
        elif bytes < 1024 ** 3:
            return f"{bytes / (1024**2):.2f} MB"
        else:
            return f"{bytes / (1024**3):.2f} GB"

    def print_report(self):
        """Print benchmark report"""
        print("\n" + "=" * 70)
        print(f"BENCHMARK: {self.name}")
        print("=" * 70)
        print(f"Duration: {self.format_time(self.duration)}")

        if self.operations > 0:
            print(f"Operations: {self.operations:,}")
            print(f"Throughput: {self.throughput:.2f} ops/sec")

        if PSUTIL_AVAILABLE and self.memory_start is not None:
            print(f"\nMemory:")
            print(f"  Start: {self.format_memory(self.memory_start)}")
            print(f"  End: {self.format_memory(self.memory_end)}")
            print(f"  Delta: {self.format_memory(self.memory_delta)}")
            if self.memory_peak:
                print(f"  Peak: {self.format_memory(self.memory_peak)}")

        if self.metrics:
            print(f"\nMetrics:")
            for key, value in self.metrics.items():
                if isinstance(value, float):
                    print(f"  {key}: {value:.4f}")
                else:
                    print(f"  {key}: {value}")

        print("=" * 70 + "\n")

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.duration,
            'memory_start': self.memory_start,
            'memory_end': self.memory_end,
            'memory_peak': self.memory_peak,
            'operations': self.operations,
            'throughput': self.throughput,
            'metrics': self.metrics
        }


class Benchmark:
    """
    Performance benchmark context manager

    Tracks execution time and memory usage for code blocks.

    Attributes:
        name: Benchmark name
        track_memory: Enable memory tracking (requires psutil)
        logger: Optional logger instance

    Example:
        >>> with Benchmark("test_operation") as bench:
        ...     # perform operations
        ...     bench.add_operations(100)
        ...     bench.set_metric("quality", 0.95)
        >>> bench.result.print_report()
    """

    def __init__(self,
                 name: str,
                 track_memory: bool = True,
                 logger: Optional[logging.Logger] = None):
        """
        Initialize benchmark

        Args:
            name: Benchmark name
            track_memory: Track memory usage (requires psutil)
            logger: Optional logger for output
        """
        self.name = name
        self.track_memory = track_memory and PSUTIL_AVAILABLE
        self.logger = logger or logging.getLogger(__name__)

        self.start_time = None
        self.end_time = None
        self.operations = 0
        self.metrics = {}

        self.memory_start = None
        self.memory_end = None
        self.memory_peak = None

        self.result: Optional[BenchmarkResult] = None

    def __enter__(self):
        """Start benchmark"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """End benchmark"""
        self.stop()

    def start(self):
        """Start benchmark timing"""
        self.start_time = time.time()

        if self.track_memory:
            process = psutil.Process()
            self.memory_start = process.memory_info().rss

        self.logger.debug(f"Benchmark '{self.name}' started")

    def stop(self):
        """Stop benchmark timing"""
        self.end_time = time.time()

        if self.track_memory:
            process = psutil.Process()
            self.memory_end = process.memory_info().rss

        duration = self.end_time - self.start_time

        self.result = BenchmarkResult(
            name=self.name,
            start_time=self.start_time,
            end_time=self.end_time,
            duration=duration,
            memory_start=self.memory_start,
            memory_end=self.memory_end,
            memory_peak=self.memory_peak,
            operations=self.operations,
            metrics=self.metrics
        )

        self.logger.debug(
            f"Benchmark '{self.name}' completed in "
            f"{self.result.format_time(duration)}"
        )

    def add_operations(self, count: int):
        """
        Add to operation count

        Args:
            count: Number of operations to add
        """
        self.operations += count

    def set_metric(self, name: str, value: Any):
        """
        Set custom metric

        Args:
            name: Metric name
            value: Metric value
        """
        self.metrics[name] = value

    def update_peak_memory(self):
        """Update peak memory usage"""
        if self.track_memory:
            process = psutil.Process()
            current = process.memory_info().rss
            if self.memory_peak is None or current > self.memory_peak:
                self.memory_peak = current


class BenchmarkSuite:
    """
    Collection of benchmarks for comprehensive testing

    Attributes:
        name: Suite name
        benchmarks: List of benchmark results
        logger: Logger instance

    Example:
        >>> suite = BenchmarkSuite("mesh_generation_suite")
        >>> with Benchmark("test1") as b:
        ...     pass
        >>> suite.add_result(b.result)
        >>> suite.save_results("benchmarks.json")
    """

    def __init__(self, name: str, logger: Optional[logging.Logger] = None):
        """
        Initialize benchmark suite

        Args:
            name: Suite name
            logger: Optional logger
        """
        self.name = name
        self.logger = logger or logging.getLogger(__name__)
        self.benchmarks: List[BenchmarkResult] = []
        self.metadata: Dict[str, Any] = {
            'timestamp': datetime.now().isoformat(),
            'name': name
        }

    def add_result(self, result: BenchmarkResult):
        """
        Add benchmark result to suite

        Args:
            result: Benchmark result to add
        """
        self.benchmarks.append(result)
        self.logger.debug(f"Added benchmark '{result.name}' to suite")

    def run_benchmark(self,
                     name: str,
                     func: Callable,
                     *args,
                     **kwargs) -> BenchmarkResult:
        """
        Run function as benchmark

        Args:
            name: Benchmark name
            func: Function to benchmark
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Benchmark result

        Example:
            >>> suite = BenchmarkSuite("tests")
            >>> result = suite.run_benchmark("test1", my_function, arg1, arg2)
        """
        with Benchmark(name) as bench:
            func(*args, **kwargs)

        self.add_result(bench.result)
        return bench.result

    def print_summary(self):
        """Print suite summary"""
        print("\n" + "=" * 70)
        print(f"BENCHMARK SUITE: {self.name}")
        print("=" * 70)
        print(f"Total benchmarks: {len(self.benchmarks)}")
        print(f"Timestamp: {self.metadata['timestamp']}")

        if self.benchmarks:
            total_duration = sum(b.duration for b in self.benchmarks)
            total_ops = sum(b.operations for b in self.benchmarks)

            print(f"\nOverall:")
            print(f"  Total duration: {BenchmarkResult.format_time(self, total_duration)}")
            print(f"  Total operations: {total_ops:,}")

            print(f"\nIndividual benchmarks:")
            for bench in self.benchmarks:
                print(f"  {bench.name}:")
                print(f"    Duration: {bench.format_time(bench.duration)}")
                if bench.operations > 0:
                    print(f"    Throughput: {bench.throughput:.2f} ops/sec")

        print("=" * 70 + "\n")

    def save_results(self, filepath: str):
        """
        Save benchmark results to JSON file

        Args:
            filepath: Output file path
        """
        data = {
            'suite_name': self.name,
            'metadata': self.metadata,
            'benchmarks': [b.to_dict() for b in self.benchmarks]
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        self.logger.info(f"Saved benchmark results to {filepath}")

    @classmethod
    def load_results(cls, filepath: str) -> 'BenchmarkSuite':
        """
        Load benchmark results from JSON file

        Args:
            filepath: Input file path

        Returns:
            BenchmarkSuite with loaded results
        """
        with open(filepath, 'r') as f:
            data = json.load(f)

        suite = cls(data['suite_name'])
        suite.metadata = data['metadata']

        for bench_data in data['benchmarks']:
            result = BenchmarkResult(
                name=bench_data['name'],
                start_time=bench_data['start_time'],
                end_time=bench_data['end_time'],
                duration=bench_data['duration'],
                memory_start=bench_data.get('memory_start'),
                memory_end=bench_data.get('memory_end'),
                memory_peak=bench_data.get('memory_peak'),
                operations=bench_data['operations'],
                metrics=bench_data.get('metrics', {})
            )
            suite.benchmarks.append(result)

        return suite


@contextmanager
def benchmark(name: str, **kwargs):
    """
    Context manager for quick benchmarking

    Args:
        name: Benchmark name
        **kwargs: Additional Benchmark arguments

    Example:
        >>> with benchmark("test_operation"):
        ...     # perform operations
        ...     pass
    """
    bench = Benchmark(name, **kwargs)
    bench.start()
    try:
        yield bench
    finally:
        bench.stop()
        bench.result.print_report()


def compare_benchmarks(results: List[BenchmarkResult], metric: str = 'duration'):
    """
    Compare multiple benchmark results

    Args:
        results: List of benchmark results
        metric: Metric to compare ('duration', 'throughput', 'memory_delta')

    Example:
        >>> results = [bench1.result, bench2.result, bench3.result]
        >>> compare_benchmarks(results, metric='duration')
    """
    print("\n" + "=" * 70)
    print("BENCHMARK COMPARISON")
    print("=" * 70)
    print(f"Comparing {len(results)} benchmarks by {metric}")
    print()

    # Sort by metric
    if metric == 'duration':
        sorted_results = sorted(results, key=lambda r: r.duration)
    elif metric == 'throughput':
        sorted_results = sorted(results, key=lambda r: r.throughput, reverse=True)
    elif metric == 'memory_delta':
        sorted_results = sorted(results, key=lambda r: r.memory_delta or 0)
    else:
        sorted_results = results

    # Find best value for normalization
    best = sorted_results[0]

    print(f"{'Rank':<6} {'Name':<30} {metric.capitalize():<20} {'Relative':<15}")
    print("-" * 70)

    for i, result in enumerate(sorted_results, 1):
        if metric == 'duration':
            value_str = result.format_time(result.duration)
            relative = result.duration / best.duration if best.duration > 0 else 1.0
        elif metric == 'throughput':
            value_str = f"{result.throughput:.2f} ops/sec"
            relative = result.throughput / best.throughput if best.throughput > 0 else 1.0
        elif metric == 'memory_delta':
            value_str = result.format_memory(result.memory_delta)
            relative = (result.memory_delta or 0) / (best.memory_delta or 1)
        else:
            value_str = "N/A"
            relative = 1.0

        relative_str = f"{relative:.2f}x"
        if i == 1:
            relative_str += " (best)"

        print(f"{i:<6} {result.name:<30} {value_str:<20} {relative_str:<15}")

    print("=" * 70 + "\n")
