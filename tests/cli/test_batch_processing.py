"""
Test Batch Processing System

Tests batch processor, glob patterns, CSV parsing, and parallel execution.
"""

import pytest
from pathlib import Path
import tempfile
import csv
import time

from koomesh.batch.batch_processor import BatchProcessor, BatchJob, BatchResult


class TestBatchJob:
    """Test BatchJob dataclass"""

    def test_create_batch_job(self):
        """Test creating a batch job"""
        job = BatchJob(
            id='job_001',
            input_file='input.step',
            output_file='output.k',
            parameters={'mesh_size': 2.0}
        )

        assert job.id == 'job_001'
        assert job.input_file == 'input.step'
        assert job.status == 'pending'
        assert job.parameters['mesh_size'] == 2.0


class TestBatchProcessor:
    """Test BatchProcessor functionality"""

    def test_processor_initialization(self):
        """Test processor initialization"""
        processor = BatchProcessor(n_jobs=4, max_retries=3)

        assert processor.n_jobs == 4
        assert processor.max_retries == 3

    def test_create_jobs_from_glob(self):
        """Test creating jobs from glob pattern"""
        # Create temporary directory with test files
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create some test files
            for i in range(3):
                (tmppath / f'part_{i}.step').touch()

            output_dir = tmppath / 'output'
            output_dir.mkdir()

            processor = BatchProcessor()
            jobs = processor.create_jobs_from_glob(
                pattern=str(tmppath / '*.step'),
                output_dir=str(output_dir)
            )

            assert len(jobs) == 3
            assert all(job.status == 'pending' for job in jobs)
            assert all('.step' in job.input_file for job in jobs)

    def test_create_jobs_from_csv(self):
        """Test creating jobs from CSV file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            csv_file = tmppath / 'jobs.csv'

            # Create CSV file
            with open(csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'input_file', 'output_file', 'mesh_size'])
                writer.writerow(['job1', 'part1.step', 'part1.k', '2.0'])
                writer.writerow(['job2', 'part2.step', 'part2.k', '3.0'])

            processor = BatchProcessor()
            jobs = processor.create_jobs_from_csv(str(csv_file))

            assert len(jobs) == 2
            assert jobs[0].id == 'job1'
            assert jobs[0].parameters['mesh_size'] == '2.0'
            assert jobs[1].id == 'job2'


class TestBatchExecution:
    """Test batch execution"""

    def test_execute_simple_jobs(self):
        """Test executing simple jobs"""

        def simple_job_function(job: BatchJob) -> bool:
            """Simple test function that always succeeds"""
            time.sleep(0.01)  # Simulate work
            return True

        processor = BatchProcessor(n_jobs=2)

        jobs = [
            BatchJob(id=f'job_{i}', input_file=f'input_{i}.step', output_file=f'output_{i}.k')
            for i in range(5)
        ]

        result = processor.execute(jobs, simple_job_function, parallel=False)

        assert result.total == 5
        assert result.succeeded == 5
        assert result.failed == 0

    def test_execute_with_failures(self):
        """Test executing jobs with some failures"""

        def failing_job_function(job: BatchJob) -> bool:
            """Function that fails for certain jobs"""
            if 'fail' in job.id:
                return False
            return True

        processor = BatchProcessor(n_jobs=2, max_retries=1)

        jobs = [
            BatchJob(id='job_success_1', input_file='input1.step', output_file='output1.k'),
            BatchJob(id='job_fail_1', input_file='input2.step', output_file='output2.k'),
            BatchJob(id='job_success_2', input_file='input3.step', output_file='output3.k'),
        ]

        result = processor.execute(jobs, failing_job_function, parallel=False)

        assert result.total == 3
        assert result.succeeded == 2
        assert result.failed == 1

    def test_execute_parallel(self):
        """Test parallel execution"""

        def slow_job_function(job: BatchJob) -> bool:
            """Slow function to test parallelization"""
            time.sleep(0.1)
            return True

        processor = BatchProcessor(n_jobs=4)

        jobs = [
            BatchJob(id=f'job_{i}', input_file=f'input_{i}.step', output_file=f'output_{i}.k')
            for i in range(8)
        ]

        start_time = time.time()
        result = processor.execute(jobs, slow_job_function, parallel=True)
        elapsed = time.time() - start_time

        assert result.succeeded == 8
        # Parallel should be faster than sequential
        # 8 jobs * 0.1s = 0.8s sequential, but with 4 workers should be ~0.2s
        assert elapsed < 0.5  # Give some margin


class TestBatchResult:
    """Test BatchResult functionality"""

    def test_batch_result_summary(self):
        """Test batch result summary"""
        result = BatchResult(
            total=10,
            succeeded=8,
            failed=2,
            execution_time=10.5
        )

        assert result.total == 10
        assert result.succeeded == 8
        assert result.failed == 2
        assert result.execution_time == 10.5

    def test_batch_result_print_summary(self, capsys):
        """Test printing batch result summary"""
        result = BatchResult(
            total=5,
            succeeded=4,
            failed=1,
            execution_time=5.0
        )

        result.print_summary()

        captured = capsys.readouterr()
        assert 'Batch Processing Results' in captured.out
        assert '5' in captured.out  # Total
        assert '4' in captured.out  # Succeeded


class TestCSVParsing:
    """Test CSV/Excel parsing"""

    def test_parse_csv_with_custom_columns(self):
        """Test parsing CSV with custom parameter columns"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            csv_file = tmppath / 'custom_params.csv'

            # Create CSV with custom columns
            with open(csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'input_file', 'output_file', 'mesh_size', 'material', 'quality'])
                writer.writerow(['part1', 'p1.step', 'p1.k', '2.0', 'Steel', '0.9'])

            processor = BatchProcessor()
            jobs = processor.create_jobs_from_csv(str(csv_file))

            assert len(jobs) == 1
            assert 'mesh_size' in jobs[0].parameters
            assert 'material' in jobs[0].parameters
            assert 'quality' in jobs[0].parameters

    def test_parse_csv_minimal_columns(self):
        """Test parsing CSV with minimal columns"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            csv_file = tmppath / 'minimal.csv'

            # Create CSV with only required columns
            with open(csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['input_file', 'output_file'])
                writer.writerow(['input.step', 'output.k'])

            processor = BatchProcessor()
            jobs = processor.create_jobs_from_csv(str(csv_file))

            assert len(jobs) == 1
            assert jobs[0].input_file == 'input.step'
            assert jobs[0].output_file == 'output.k'


class TestJobRetry:
    """Test job retry logic"""

    def test_retry_on_failure(self):
        """Test that jobs are retried on failure"""
        attempt_count = {'count': 0}

        def flaky_job_function(job: BatchJob) -> bool:
            """Function that fails first time, succeeds second time"""
            attempt_count['count'] += 1
            if attempt_count['count'] == 1:
                return False
            return True

        processor = BatchProcessor(max_retries=2)

        jobs = [
            BatchJob(id='job_1', input_file='input.step', output_file='output.k')
        ]

        result = processor.execute(jobs, flaky_job_function, parallel=False)

        assert result.succeeded == 1
        assert attempt_count['count'] >= 2  # Should have retried

    def test_max_retries_exceeded(self):
        """Test that jobs fail after max retries"""

        def always_fail_function(job: BatchJob) -> bool:
            """Function that always fails"""
            return False

        processor = BatchProcessor(max_retries=2)

        jobs = [
            BatchJob(id='job_1', input_file='input.step', output_file='output.k')
        ]

        result = processor.execute(jobs, always_fail_function, parallel=False)

        assert result.failed == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
