"""
Parallel Processing Module
==========================

High-performance parallel processing utilities for mesh operations.

Features:
---------
- Parallel quality checking with multiprocessing
- Parallel contact detection
- Performance benchmarking utilities
- Automatic CPU core detection
- Progress tracking for long operations

Modules:
--------
- parallel_quality: Parallel mesh quality checking
- parallel_contact: Parallel contact detection
- parallel_utils: Performance utilities and benchmarks

Example:
--------
```python
from koomesh.parallel import ParallelQualityChecker

# Use all available cores
checker = ParallelQualityChecker(n_jobs=-1)
result = checker.check_mesh(mesh_data)

# Speedup compared to serial version
print(f"Checked {len(mesh_data.elements)} elements using {checker.n_jobs} cores")
```

Author: KooMeshGenerator Team
"""

from koomesh.parallel.parallel_quality import ParallelQualityChecker
from koomesh.parallel.parallel_contact import ParallelContactDetector
from koomesh.parallel.parallel_utils import benchmark, get_optimal_workers

__all__ = [
    'ParallelQualityChecker',
    'ParallelContactDetector',
    'benchmark',
    'get_optimal_workers'
]
