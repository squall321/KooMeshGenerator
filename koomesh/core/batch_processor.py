"""
Batch Processing
================

This module provides batch processing capabilities for handling multiple STEP files.

Features:
- Directory scanning for STEP files
- Parallel processing support
- Aggregated statistics
- Error handling and recovery
- Progress tracking across multiple files

Usage:
    >>> from koomesh.core.batch_processor import BatchProcessor
    >>> processor = BatchProcessor()
    >>> results = processor.process_directory('input_dir/', 'output_dir/')
"""

import logging
import time
from pathlib import Path
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import multiprocessing

from koomesh.config import KooMeshConfig
from koomesh.core.pipeline import MeshPipeline, PipelineResult, PipelineProgress


@dataclass
class BatchJob:
    """
    Batch processing job

    Attributes:
        input_file: Input STEP file path
        output_file: Output LS-DYNA file path
        mesh_size: Mesh element size
        hex_priority: Prioritize hexahedral meshing
        status: Job status ('pending', 'running', 'completed', 'failed')
        result: Pipeline result (after execution)
        error: Error message (if failed)
    """
    input_file: Path
    output_file: Path
    mesh_size: float
    hex_priority: bool = True
    status: str = 'pending'
    result: Optional[PipelineResult] = None
    error: Optional[str] = None

    def __repr__(self) -> str:
        return f"BatchJob(input={self.input_file.name}, status={self.status})"


@dataclass
class BatchResult:
    """
    Batch processing result

    Attributes:
        total_jobs: Total number of jobs
        completed: Number of successfully completed jobs
        failed: Number of failed jobs
        results: List of individual pipeline results
        execution_time: Total execution time (seconds)
        statistics: Aggregated statistics
    """
    total_jobs: int
    completed: int = 0
    failed: int = 0
    results: List[PipelineResult] = field(default_factory=list)
    execution_time: float = 0.0
    statistics: Dict = field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_jobs == 0:
            return 0.0
        return (self.completed / self.total_jobs) * 100.0

    def print_summary(self):
        """Print batch processing summary"""
        print("\n" + "=" * 70)
        print("BATCH PROCESSING SUMMARY")
        print("=" * 70)
        print(f"Total Jobs: {self.total_jobs}")
        print(f"Completed: {self.completed} ({self.success_rate:.1f}%)")
        print(f"Failed: {self.failed}")
        print(f"Total Execution Time: {self.execution_time:.2f}s")

        if self.completed > 0:
            avg_time = self.execution_time / self.completed
            print(f"Average Time per Job: {avg_time:.2f}s")

        if self.statistics:
            print("\nAggregated Statistics:")
            total_nodes = self.statistics.get('total_nodes', 0)
            total_elements = self.statistics.get('total_elements', 0)
            total_contacts = self.statistics.get('total_contacts', 0)

            print(f"  Total Nodes: {total_nodes:,}")
            print(f"  Total Elements: {total_elements:,}")
            print(f"  Total Contacts: {total_contacts:,}")

        print("=" * 70 + "\n")


class BatchProcessor:
    """
    Batch processor for multiple STEP files

    Handles processing of multiple STEP files in a directory or file list.
    Supports parallel processing for improved performance.

    Attributes:
        config: KooMesh configuration
        logger: Logger instance
        num_workers: Number of parallel workers
        use_multiprocessing: Use multiprocessing instead of threading

    Example:
        >>> processor = BatchProcessor(num_workers=4)
        >>> results = processor.process_directory(
        ...     input_dir='step_files/',
        ...     output_dir='output/',
        ...     mesh_size=1.0
        ... )
        >>> results.print_summary()
    """

    def __init__(self,
                 config: Optional[KooMeshConfig] = None,
                 num_workers: Optional[int] = None,
                 use_multiprocessing: bool = False):
        """
        Initialize batch processor

        Args:
            config: KooMesh configuration
            num_workers: Number of parallel workers (defaults to CPU count)
            use_multiprocessing: Use multiprocessing instead of threading
        """
        self.config = config or KooMeshConfig()
        self.logger = logging.getLogger(__name__)
        self.num_workers = num_workers or max(1, multiprocessing.cpu_count() - 1)
        self.use_multiprocessing = use_multiprocessing

        self.logger.info(
            f"BatchProcessor initialized: {self.num_workers} workers, "
            f"mode={'multiprocessing' if use_multiprocessing else 'threading'}"
        )

    def process_directory(self,
                         input_dir: str,
                         output_dir: str,
                         mesh_size: Optional[float] = None,
                         hex_priority: bool = True,
                         pattern: str = "*.step",
                         recursive: bool = False,
                         parallel: bool = True) -> BatchResult:
        """
        Process all STEP files in a directory

        Args:
            input_dir: Input directory containing STEP files
            output_dir: Output directory for LS-DYNA files
            mesh_size: Mesh element size (uses config default if not specified)
            hex_priority: Prioritize hexahedral meshing
            pattern: File pattern for matching STEP files
            recursive: Search subdirectories recursively
            parallel: Enable parallel processing

        Returns:
            BatchResult with aggregated results

        Example:
            >>> results = processor.process_directory('input/', 'output/', mesh_size=1.0)
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)

        if not input_path.exists():
            raise ValueError(f"Input directory does not exist: {input_dir}")

        # Create output directory
        output_path.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"Scanning directory: {input_dir}")

        # Find all STEP files
        if recursive:
            step_files = list(input_path.rglob(pattern))
        else:
            step_files = list(input_path.glob(pattern))

        # Also check for .stp extension
        if pattern == "*.step" or pattern == "*.STEP":
            if recursive:
                step_files.extend(list(input_path.rglob("*.stp")))
                step_files.extend(list(input_path.rglob("*.STP")))
            else:
                step_files.extend(list(input_path.glob("*.stp")))
                step_files.extend(list(input_path.glob("*.STP")))

        self.logger.info(f"Found {len(step_files)} STEP files")

        # Create batch jobs
        jobs = []
        for step_file in step_files:
            # Generate output filename
            relative_path = step_file.relative_to(input_path)
            output_file = output_path / relative_path.with_suffix('.k')

            # Create output subdirectories if needed
            output_file.parent.mkdir(parents=True, exist_ok=True)

            job = BatchJob(
                input_file=step_file,
                output_file=output_file,
                mesh_size=mesh_size or self.config.mesh.default_size,
                hex_priority=hex_priority
            )
            jobs.append(job)

        # Process jobs
        if parallel and len(jobs) > 1:
            return self._process_parallel(jobs)
        else:
            return self._process_sequential(jobs)

    def process_file_list(self,
                         file_pairs: List[tuple[str, str]],
                         mesh_size: Optional[float] = None,
                         hex_priority: bool = True,
                         parallel: bool = True) -> BatchResult:
        """
        Process a list of (input, output) file pairs

        Args:
            file_pairs: List of (input_file, output_file) tuples
            mesh_size: Mesh element size
            hex_priority: Prioritize hexahedral meshing
            parallel: Enable parallel processing

        Returns:
            BatchResult with aggregated results

        Example:
            >>> pairs = [('model1.step', 'out1.k'), ('model2.step', 'out2.k')]
            >>> results = processor.process_file_list(pairs, mesh_size=1.0)
        """
        self.logger.info(f"Processing {len(file_pairs)} file pairs")

        # Create batch jobs
        jobs = []
        for input_file, output_file in file_pairs:
            job = BatchJob(
                input_file=Path(input_file),
                output_file=Path(output_file),
                mesh_size=mesh_size or self.config.mesh.default_size,
                hex_priority=hex_priority
            )
            jobs.append(job)

        # Process jobs
        if parallel and len(jobs) > 1:
            return self._process_parallel(jobs)
        else:
            return self._process_sequential(jobs)

    def _process_sequential(self, jobs: List[BatchJob]) -> BatchResult:
        """Process jobs sequentially"""
        self.logger.info(f"Processing {len(jobs)} jobs sequentially")

        start_time = time.time()
        results = []

        for i, job in enumerate(jobs, 1):
            self.logger.info(f"Processing job {i}/{len(jobs)}: {job.input_file.name}")

            job.status = 'running'

            try:
                # Create pipeline and run
                pipeline = MeshPipeline(config=self.config)
                result = pipeline.run(
                    step_file=str(job.input_file),
                    output_file=str(job.output_file),
                    mesh_size=job.mesh_size,
                    hex_priority=job.hex_priority
                )

                job.result = result
                job.status = 'completed' if result.success else 'failed'

                if not result.success:
                    job.error = result.errors[0] if result.errors else "Unknown error"

                results.append(result)

            except Exception as e:
                self.logger.error(f"Job {i} failed: {e}")
                job.status = 'failed'
                job.error = str(e)

        execution_time = time.time() - start_time

        # Create batch result
        batch_result = self._create_batch_result(jobs, results, execution_time)

        self.logger.info(
            f"Sequential processing complete: {batch_result.completed}/{len(jobs)} succeeded"
        )

        return batch_result

    def _process_parallel(self, jobs: List[BatchJob]) -> BatchResult:
        """Process jobs in parallel"""
        self.logger.info(
            f"Processing {len(jobs)} jobs in parallel with {self.num_workers} workers"
        )

        start_time = time.time()
        results = []

        # Choose executor
        if self.use_multiprocessing:
            ExecutorClass = ProcessPoolExecutor
        else:
            ExecutorClass = ThreadPoolExecutor

        # Process jobs
        with ExecutorClass(max_workers=self.num_workers) as executor:
            # Submit all jobs
            future_to_job = {}
            for job in jobs:
                future = executor.submit(self._run_job, job)
                future_to_job[future] = job

            # Collect results as they complete
            completed_count = 0
            for future in as_completed(future_to_job):
                job = future_to_job[future]
                completed_count += 1

                try:
                    result = future.result()
                    job.result = result
                    job.status = 'completed' if result.success else 'failed'

                    if not result.success:
                        job.error = result.errors[0] if result.errors else "Unknown error"

                    results.append(result)

                    self.logger.info(
                        f"[{completed_count}/{len(jobs)}] Completed: {job.input_file.name} "
                        f"({'success' if result.success else 'failed'})"
                    )

                except Exception as e:
                    self.logger.error(f"Job failed with exception: {e}")
                    job.status = 'failed'
                    job.error = str(e)

        execution_time = time.time() - start_time

        # Create batch result
        batch_result = self._create_batch_result(jobs, results, execution_time)

        self.logger.info(
            f"Parallel processing complete: {batch_result.completed}/{len(jobs)} succeeded"
        )

        return batch_result

    def _run_job(self, job: BatchJob) -> PipelineResult:
        """Run a single job"""
        job.status = 'running'

        # Create pipeline and run
        pipeline = MeshPipeline(config=self.config)
        result = pipeline.run(
            step_file=str(job.input_file),
            output_file=str(job.output_file),
            mesh_size=job.mesh_size,
            hex_priority=job.hex_priority
        )

        return result

    def _create_batch_result(self,
                            jobs: List[BatchJob],
                            results: List[PipelineResult],
                            execution_time: float) -> BatchResult:
        """Create batch result from individual results"""
        # Count successes and failures
        completed = sum(1 for job in jobs if job.status == 'completed')
        failed = sum(1 for job in jobs if job.status == 'failed')

        # Aggregate statistics
        total_nodes = sum(r.statistics.get('total_nodes', 0) for r in results if r.success)
        total_elements = sum(r.statistics.get('total_elements', 0) for r in results if r.success)
        total_contacts = sum(r.statistics.get('num_contacts', 0) for r in results if r.success)

        statistics = {
            'total_nodes': total_nodes,
            'total_elements': total_elements,
            'total_contacts': total_contacts
        }

        batch_result = BatchResult(
            total_jobs=len(jobs),
            completed=completed,
            failed=failed,
            results=results,
            execution_time=execution_time,
            statistics=statistics
        )

        return batch_result

    def create_job_report(self, jobs: List[BatchJob], output_file: str):
        """
        Create detailed job report

        Args:
            jobs: List of batch jobs
            output_file: Output report file path
        """
        self.logger.info(f"Creating job report: {output_file}")

        with open(output_file, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("KOOMESH BATCH PROCESSING REPORT\n")
            f.write("=" * 80 + "\n\n")

            # Summary
            completed = sum(1 for job in jobs if job.status == 'completed')
            failed = sum(1 for job in jobs if job.status == 'failed')
            success_rate = (completed / len(jobs)) * 100 if jobs else 0

            f.write(f"Total Jobs: {len(jobs)}\n")
            f.write(f"Completed: {completed} ({success_rate:.1f}%)\n")
            f.write(f"Failed: {failed}\n\n")

            # Individual job details
            f.write("=" * 80 + "\n")
            f.write("JOB DETAILS\n")
            f.write("=" * 80 + "\n\n")

            for i, job in enumerate(jobs, 1):
                f.write(f"Job {i}: {job.input_file.name}\n")
                f.write(f"  Status: {job.status}\n")
                f.write(f"  Input: {job.input_file}\n")
                f.write(f"  Output: {job.output_file}\n")

                if job.result:
                    f.write(f"  Execution Time: {job.result.execution_time:.2f}s\n")

                    if job.result.success:
                        f.write(f"  Nodes: {job.result.statistics.get('total_nodes', 0):,}\n")
                        f.write(f"  Elements: {job.result.statistics.get('total_elements', 0):,}\n")
                        f.write(f"  Contacts: {job.result.statistics.get('num_contacts', 0)}\n")
                    else:
                        f.write(f"  Errors: {len(job.result.errors)}\n")
                        for error in job.result.errors[:3]:
                            f.write(f"    - {error}\n")

                if job.error:
                    f.write(f"  Error: {job.error}\n")

                f.write("\n")

        self.logger.info(f"Job report written to: {output_file}")


def process_directory_batch(input_dir: str,
                            output_dir: str,
                            mesh_size: float,
                            hex_priority: bool = True,
                            num_workers: Optional[int] = None,
                            recursive: bool = False) -> BatchResult:
    """
    Convenience function for batch processing

    Args:
        input_dir: Input directory containing STEP files
        output_dir: Output directory for LS-DYNA files
        mesh_size: Mesh element size
        hex_priority: Prioritize hexahedral meshing
        num_workers: Number of parallel workers
        recursive: Search subdirectories recursively

    Returns:
        BatchResult with aggregated results

    Example:
        >>> from koomesh.core.batch_processor import process_directory_batch
        >>> results = process_directory_batch('input/', 'output/', mesh_size=1.0)
        >>> results.print_summary()
    """
    processor = BatchProcessor(num_workers=num_workers)
    return processor.process_directory(
        input_dir=input_dir,
        output_dir=output_dir,
        mesh_size=mesh_size,
        hex_priority=hex_priority,
        recursive=recursive
    )
