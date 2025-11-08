"""
Batch Processor
===============

Batch processing of multiple mesh generation jobs with parallel execution,
progress tracking, and error recovery.

Features:
- File glob pattern matching
- CSV/Excel parameter files
- Parallel execution with joblib
- Progress tracking with tqdm
- Error recovery and retry
- Job result logging

Author: KooMeshGenerator Team
"""

import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import glob

import pandas as pd
from tqdm import tqdm
from joblib import Parallel, delayed

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Job execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class BatchJob:
    """
    Single batch job definition

    Attributes:
        id: Unique job ID
        input_file: Input file path
        output_file: Output file path
        parameters: Job-specific parameters
        status: Job execution status
        error: Error message if failed
        retries: Number of retry attempts
        start_time: Job start timestamp
        end_time: Job end timestamp
    """
    id: str
    input_file: str
    output_file: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    status: JobStatus = JobStatus.PENDING
    error: Optional[str] = None
    retries: int = 0
    start_time: Optional[float] = None
    end_time: Optional[float] = None

    def duration(self) -> Optional[float]:
        """Get job duration in seconds"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None


@dataclass
class BatchResult:
    """
    Batch processing results

    Attributes:
        total: Total number of jobs
        completed: Number of completed jobs
        failed: Number of failed jobs
        jobs: List of all jobs with status
        total_duration: Total processing time
    """
    total: int
    completed: int
    failed: int
    jobs: List[BatchJob]
    total_duration: float

    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total == 0:
            return 0.0
        return self.completed / self.total * 100

    def print_summary(self):
        """Print batch result summary"""
        print("\n" + "="*70)
        print("BATCH PROCESSING SUMMARY")
        print("="*70)
        print(f"Total jobs: {self.total}")
        print(f"Completed: {self.completed} ({self.success_rate():.1f}%)")
        print(f"Failed: {self.failed}")
        print(f"Total duration: {self.total_duration:.1f}s")

        if self.failed > 0:
            print("\nFailed jobs:")
            for job in self.jobs:
                if job.status == JobStatus.FAILED:
                    print(f"  - {job.id}: {job.error}")

        print("="*70)


class BatchProcessor:
    """
    Batch processor for multiple mesh generation jobs

    This class handles batch processing of multiple files with:
    - Parallel execution
    - Progress tracking
    - Error recovery
    - Retry logic

    Example:
        >>> processor = BatchProcessor(n_jobs=4, max_retries=3)
        >>> jobs = processor.create_jobs_from_glob("input/*.step", "output/")
        >>> result = processor.execute(jobs)
        >>> result.print_summary()
    """

    def __init__(
        self,
        n_jobs: int = -1,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        verbose: bool = True
    ):
        """
        Initialize batch processor

        Args:
            n_jobs: Number of parallel jobs (-1 = all cores, -2 = all but one)
            max_retries: Maximum number of retry attempts for failed jobs
            retry_delay: Delay between retries in seconds
            verbose: Enable verbose output
        """
        self.n_jobs = n_jobs
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.verbose = verbose
        self.logger = logging.getLogger(__name__)

    def create_jobs_from_glob(
        self,
        pattern: str,
        output_dir: str,
        output_extension: str = ".k",
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[BatchJob]:
        """
        Create batch jobs from file glob pattern

        Args:
            pattern: File glob pattern (e.g., "input/*.step")
            output_dir: Output directory
            output_extension: Output file extension (default: .k)
            parameters: Common parameters for all jobs

        Returns:
            List of BatchJob instances

        Example:
            >>> jobs = processor.create_jobs_from_glob(
            ...     "input/*.step",
            ...     "output/",
            ...     parameters={"mesh_size": 2.0}
            ... )
        """
        files = glob.glob(pattern)

        if not files:
            self.logger.warning(f"No files found matching pattern: {pattern}")
            return []

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        jobs = []
        for i, input_file in enumerate(files, 1):
            input_path = Path(input_file)
            output_file = output_path / (input_path.stem + output_extension)

            job = BatchJob(
                id=f"job_{i:04d}",
                input_file=str(input_path),
                output_file=str(output_file),
                parameters=parameters or {}
            )
            jobs.append(job)

        self.logger.info(f"Created {len(jobs)} jobs from pattern: {pattern}")
        return jobs

    def create_jobs_from_csv(
        self,
        csv_file: str,
        required_columns: Optional[List[str]] = None
    ) -> List[BatchJob]:
        """
        Create batch jobs from CSV file

        CSV format:
            id,input_file,output_file,mesh_size,element_type,...

        Args:
            csv_file: Path to CSV file
            required_columns: Required column names (default: id, input_file, output_file)

        Returns:
            List of BatchJob instances

        Example:
            >>> jobs = processor.create_jobs_from_csv("parts_list.csv")
        """
        if required_columns is None:
            required_columns = ['input_file', 'output_file']

        # Read CSV
        df = pd.read_csv(csv_file)

        # Validate required columns
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        # Create jobs
        jobs = []
        for idx, row in df.iterrows():
            # Get ID (use index if not provided)
            job_id = str(row.get('id', f"job_{idx+1:04d}"))

            # Get input/output files
            input_file = str(row['input_file'])
            output_file = str(row['output_file'])

            # Get parameters (all other columns)
            parameters = {}
            for col in df.columns:
                if col not in ['id', 'input_file', 'output_file']:
                    value = row[col]
                    # Skip NaN values
                    if pd.notna(value):
                        parameters[col] = value

            job = BatchJob(
                id=job_id,
                input_file=input_file,
                output_file=output_file,
                parameters=parameters
            )
            jobs.append(job)

        self.logger.info(f"Created {len(jobs)} jobs from CSV: {csv_file}")
        return jobs

    def create_jobs_from_excel(
        self,
        excel_file: str,
        sheet_name: str = 0,
        required_columns: Optional[List[str]] = None
    ) -> List[BatchJob]:
        """
        Create batch jobs from Excel file

        Args:
            excel_file: Path to Excel file
            sheet_name: Sheet name or index (default: 0 = first sheet)
            required_columns: Required column names

        Returns:
            List of BatchJob instances
        """
        if required_columns is None:
            required_columns = ['input_file', 'output_file']

        # Read Excel
        df = pd.read_excel(excel_file, sheet_name=sheet_name)

        # Validate required columns
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        # Create jobs (same as CSV)
        jobs = []
        for idx, row in df.iterrows():
            job_id = str(row.get('id', f"job_{idx+1:04d}"))
            input_file = str(row['input_file'])
            output_file = str(row['output_file'])

            parameters = {}
            for col in df.columns:
                if col not in ['id', 'input_file', 'output_file']:
                    value = row[col]
                    if pd.notna(value):
                        parameters[col] = value

            job = BatchJob(
                id=job_id,
                input_file=input_file,
                output_file=output_file,
                parameters=parameters
            )
            jobs.append(job)

        self.logger.info(f"Created {len(jobs)} jobs from Excel: {excel_file}")
        return jobs

    def execute(
        self,
        jobs: List[BatchJob],
        job_function: Callable[[BatchJob], bool],
        parallel: bool = True
    ) -> BatchResult:
        """
        Execute batch jobs

        Args:
            jobs: List of jobs to execute
            job_function: Function to execute for each job (returns True on success)
            parallel: Use parallel execution

        Returns:
            BatchResult with execution summary

        Example:
            >>> def process_job(job):
            ...     # Process job
            ...     return True  # or False on failure
            >>> result = processor.execute(jobs, process_job)
        """
        start_time = time.time()

        if parallel and self.n_jobs != 1:
            result = self._execute_parallel(jobs, job_function)
        else:
            result = self._execute_sequential(jobs, job_function)

        total_duration = time.time() - start_time

        # Count completed/failed
        completed = sum(1 for j in jobs if j.status == JobStatus.COMPLETED)
        failed = sum(1 for j in jobs if j.status == JobStatus.FAILED)

        return BatchResult(
            total=len(jobs),
            completed=completed,
            failed=failed,
            jobs=jobs,
            total_duration=total_duration
        )

    def _execute_sequential(
        self,
        jobs: List[BatchJob],
        job_function: Callable[[BatchJob], bool]
    ) -> List[BatchJob]:
        """Execute jobs sequentially with progress bar"""
        if self.verbose:
            iterator = tqdm(jobs, desc="Processing jobs", unit="job")
        else:
            iterator = jobs

        for job in iterator:
            self._execute_job_with_retry(job, job_function)

        return jobs

    def _execute_parallel(
        self,
        jobs: List[BatchJob],
        job_function: Callable[[BatchJob], bool]
    ) -> List[BatchJob]:
        """Execute jobs in parallel with progress bar"""
        # Use joblib for parallel execution
        if self.verbose:
            # Parallel with progress bar
            results = Parallel(n_jobs=self.n_jobs)(
                delayed(self._execute_job_with_retry)(job, job_function)
                for job in tqdm(jobs, desc="Processing jobs", unit="job")
            )
        else:
            # Parallel without progress bar
            results = Parallel(n_jobs=self.n_jobs)(
                delayed(self._execute_job_with_retry)(job, job_function)
                for job in jobs
            )

        return jobs

    def _execute_job_with_retry(
        self,
        job: BatchJob,
        job_function: Callable[[BatchJob], bool]
    ) -> BatchJob:
        """
        Execute single job with retry logic

        Args:
            job: Job to execute
            job_function: Function to execute

        Returns:
            Updated job with status
        """
        job.start_time = time.time()
        job.status = JobStatus.RUNNING

        for attempt in range(self.max_retries + 1):
            try:
                # Execute job function
                success = job_function(job)

                if success:
                    job.status = JobStatus.COMPLETED
                    job.end_time = time.time()
                    return job
                else:
                    # Job function returned False (failure)
                    if attempt < self.max_retries:
                        job.status = JobStatus.RETRYING
                        job.retries += 1
                        self.logger.warning(
                            f"Job {job.id} failed, retrying ({attempt+1}/{self.max_retries})..."
                        )
                        time.sleep(self.retry_delay)
                    else:
                        job.status = JobStatus.FAILED
                        job.error = "Job function returned False"
                        job.end_time = time.time()

            except Exception as e:
                # Exception occurred
                if attempt < self.max_retries:
                    job.status = JobStatus.RETRYING
                    job.retries += 1
                    self.logger.warning(
                        f"Job {job.id} raised exception, retrying ({attempt+1}/{self.max_retries}): {e}"
                    )
                    time.sleep(self.retry_delay)
                else:
                    job.status = JobStatus.FAILED
                    job.error = str(e)
                    job.end_time = time.time()
                    self.logger.error(f"Job {job.id} failed after {self.max_retries} retries: {e}")

        return job

    def save_results(self, result: BatchResult, output_file: str):
        """
        Save batch results to CSV file

        Args:
            result: Batch result to save
            output_file: Output CSV file path
        """
        data = []
        for job in result.jobs:
            data.append({
                'id': job.id,
                'input_file': job.input_file,
                'output_file': job.output_file,
                'status': job.status.value,
                'error': job.error or '',
                'retries': job.retries,
                'duration': job.duration() or 0.0,
                **job.parameters
            })

        df = pd.DataFrame(data)
        df.to_csv(output_file, index=False)

        self.logger.info(f"Batch results saved to: {output_file}")
