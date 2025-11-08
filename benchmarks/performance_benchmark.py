#!/usr/bin/env python3
"""
Performance Benchmark Suite
============================

This script benchmarks various operations in KooMeshGenerator to track
performance over time and identify optimization opportunities.

Usage:
    python benchmarks/performance_benchmark.py
    python benchmarks/performance_benchmark.py --output results.json
"""

import sys
import argparse
from pathlib import Path
import time
import tempfile
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from koomesh.utils.performance import (
    PerformanceProfiler,
    MemoryMonitor,
    get_system_info
)
from koomesh.utils.cache import GeometryCache, ConfigCache, MemoryCache
from koomesh.batch.batch_processor import BatchProcessor, BatchJob


class BenchmarkSuite:
    """
    Performance benchmark suite

    Runs standardized benchmarks and collects performance metrics.
    """

    def __init__(self, output_file: Path = None):
        """
        Initialize benchmark suite

        Args:
            output_file: Path to save results (JSON)
        """
        self.output_file = output_file
        self.profiler = PerformanceProfiler()
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'system_info': get_system_info(),
            'benchmarks': {}
        }

    def run_all(self):
        """Run all benchmarks"""
        print("="*70)
        print("KooMeshGenerator Performance Benchmark Suite")
        print("="*70)
        print()

        self.benchmark_geometry_cache()
        self.benchmark_config_cache()
        self.benchmark_memory_cache()
        self.benchmark_batch_processor()
        self.benchmark_array_operations()

        self.print_summary()

        if self.output_file:
            self.save_results()

    def benchmark_geometry_cache(self):
        """Benchmark geometry cache performance"""
        print("[1/5] Benchmarking Geometry Cache...")

        with tempfile.TemporaryDirectory() as tmpdir:
            cache = GeometryCache(cache_dir=Path(tmpdir) / 'cache')

            # Create test data
            test_data = {
                'volume': 1000.0,
                'area': 500.0,
                'faces': 100,
                'data': list(range(10000))  # Some large data
            }

            # Benchmark write
            with self.profiler.profile("cache_write"):
                for i in range(100):
                    cache.set(f"key_{i}", test_data)

            # Benchmark read (hits)
            with self.profiler.profile("cache_read_hit"):
                for i in range(100):
                    _ = cache.get(f"key_{i}")

            # Benchmark read (misses)
            with self.profiler.profile("cache_read_miss"):
                for i in range(100):
                    _ = cache.get(f"nonexistent_{i}")

            stats = cache.get_stats()
            self.results['benchmarks']['geometry_cache'] = {
                'write_time': self.profiler.metrics[-3].duration,
                'read_hit_time': self.profiler.metrics[-2].duration,
                'read_miss_time': self.profiler.metrics[-1].duration,
                'cache_stats': stats
            }

        print("  ✓ Complete\n")

    def benchmark_config_cache(self):
        """Benchmark config cache performance"""
        print("[2/5] Benchmarking Config Cache...")

        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ConfigCache(cache_dir=Path(tmpdir) / 'cache')

            test_config = {
                'meshing': {'mesh_size': 2.0, 'element_type': 'tet4'},
                'quality': {'thresholds': {'aspect_ratio': 10.0}},
                'data': list(range(1000))
            }

            # Benchmark operations
            with self.profiler.profile("config_cache_write"):
                for i in range(50):
                    cache.set(f"config_{i}", test_config)

            with self.profiler.profile("config_cache_read"):
                for i in range(50):
                    _ = cache.get(f"config_{i}")

            self.results['benchmarks']['config_cache'] = {
                'write_time': self.profiler.metrics[-2].duration,
                'read_time': self.profiler.metrics[-1].duration,
            }

        print("  ✓ Complete\n")

    def benchmark_memory_cache(self):
        """Benchmark in-memory cache"""
        print("[3/5] Benchmarking Memory Cache...")

        cache = MemoryCache(max_entries=1000)

        # Benchmark writes
        with self.profiler.profile("memory_cache_write"):
            for i in range(10000):
                cache.set(f"key_{i}", {'value': i, 'data': list(range(10))})

        # Benchmark reads (recent entries - should hit)
        with self.profiler.profile("memory_cache_read_recent"):
            for i in range(9000, 10000):  # Recent entries
                _ = cache.get(f"key_{i}")

        # Benchmark reads (old entries - should miss due to LRU)
        with self.profiler.profile("memory_cache_read_old"):
            for i in range(100):  # Very old entries
                _ = cache.get(f"key_{i}")

        self.results['benchmarks']['memory_cache'] = {
            'write_time': self.profiler.metrics[-3].duration,
            'read_recent_time': self.profiler.metrics[-2].duration,
            'read_old_time': self.profiler.metrics[-1].duration,
            'final_size': len(cache)
        }

        print("  ✓ Complete\n")

    def benchmark_batch_processor(self):
        """Benchmark batch processing"""
        print("[4/5] Benchmarking Batch Processor...")

        processor = BatchProcessor(n_jobs=4, max_retries=1)

        # Create test jobs
        jobs = [
            BatchJob(
                id=f"job_{i}",
                input_file=f"input_{i}.step",
                output_file=f"output_{i}.k",
                parameters={'value': i}
            )
            for i in range(100)
        ]

        # Simple job function
        def test_job(job):
            time.sleep(0.001)  # Simulate work
            return True

        # Benchmark sequential processing
        with self.profiler.profile("batch_sequential"):
            result = processor.execute(jobs[:10], test_job, parallel=False)

        # Benchmark parallel processing
        with self.profiler.profile("batch_parallel"):
            result = processor.execute(jobs[:10], test_job, parallel=True)

        self.results['benchmarks']['batch_processor'] = {
            'sequential_time': self.profiler.metrics[-2].duration,
            'parallel_time': self.profiler.metrics[-1].duration,
            'speedup': self.profiler.metrics[-2].duration / self.profiler.metrics[-1].duration
        }

        print("  ✓ Complete\n")

    def benchmark_array_operations(self):
        """Benchmark array operations"""
        print("[5/5] Benchmarking Array Operations...")

        import numpy as np

        # Large array creation
        with self.profiler.profile("array_create_large"):
            large_array = np.random.rand(1000000, 3)

        # Array operations
        with self.profiler.profile("array_compute"):
            result = np.sum(large_array, axis=0)
            norms = np.linalg.norm(large_array, axis=1)

        # Memory monitoring
        with MemoryMonitor() as monitor:
            temp_array = np.zeros((5000000, 3))  # ~114 MB
            _ = np.sum(temp_array)

        self.results['benchmarks']['array_operations'] = {
            'create_time': self.profiler.metrics[-2].duration,
            'compute_time': self.profiler.metrics[-1].duration,
            'memory_peak_mb': monitor.peak_memory_mb,
            'memory_delta_mb': monitor.delta_mb
        }

        print("  ✓ Complete\n")

    def print_summary(self):
        """Print benchmark summary"""
        print("="*70)
        print("Benchmark Results Summary")
        print("="*70)
        print()

        # System info
        sys_info = self.results['system_info']
        print(f"System:")
        print(f"  CPU Cores:      {sys_info['cpu_count']}")
        print(f"  CPU Usage:      {sys_info['cpu_percent']:.1f}%")
        print(f"  Memory Total:   {sys_info['memory_total_gb']:.1f} GB")
        print(f"  Memory Avail:   {sys_info['memory_available_gb']:.1f} GB")
        print()

        # Benchmark results
        benchmarks = self.results['benchmarks']

        print("Geometry Cache:")
        gc = benchmarks['geometry_cache']
        print(f"  Write (100 items):  {gc['write_time']*1000:.2f} ms ({gc['write_time']/100*1000:.3f} ms/item)")
        print(f"  Read Hit (100):     {gc['read_hit_time']*1000:.2f} ms ({gc['read_hit_time']/100*1000:.3f} ms/item)")
        print(f"  Read Miss (100):    {gc['read_miss_time']*1000:.2f} ms ({gc['read_miss_time']/100*1000:.3f} ms/item)")
        print()

        print("Memory Cache:")
        mc = benchmarks['memory_cache']
        print(f"  Write (10k items):  {mc['write_time']*1000:.2f} ms ({mc['write_time']/10000*1000:.4f} ms/item)")
        print(f"  Read Recent (1k):   {mc['read_recent_time']*1000:.2f} ms ({mc['read_recent_time']/1000*1000:.4f} ms/item)")
        print(f"  Final Cache Size:   {mc['final_size']} entries")
        print()

        print("Batch Processing:")
        bp = benchmarks['batch_processor']
        print(f"  Sequential (10):    {bp['sequential_time']*1000:.2f} ms")
        print(f"  Parallel (10):      {bp['parallel_time']*1000:.2f} ms")
        print(f"  Speedup:            {bp['speedup']:.2f}x")
        print()

        print("Array Operations:")
        ao = benchmarks['array_operations']
        print(f"  Create (1M x 3):    {ao['create_time']*1000:.2f} ms")
        print(f"  Compute:            {ao['compute_time']*1000:.2f} ms")
        print(f"  Memory Peak:        {ao['memory_peak_mb']:.1f} MB")
        print()

        print("="*70)

    def save_results(self):
        """Save results to JSON file"""
        with open(self.output_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"\nResults saved to: {self.output_file}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="KooMeshGenerator Performance Benchmark Suite"
    )
    parser.add_argument(
        '--output', '-o',
        type=Path,
        help='Output file for results (JSON)'
    )
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Run quick benchmarks only'
    )

    args = parser.parse_args()

    suite = BenchmarkSuite(output_file=args.output)
    suite.run_all()


if __name__ == '__main__':
    main()
