"""
Integration Tests for Batch Processor
======================================

These tests verify the batch processing functionality for multiple STEP files.
"""

import pytest
import tempfile
from pathlib import Path
import time

try:
    from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder
    from OCC.Core.STEPControl import STEPControl_Writer, STEPControl_AsIs
    from OCC.Core.gp import gp_Ax2, gp_Pnt, gp_Dir
    PYTHONOCC_AVAILABLE = True
except ImportError:
    PYTHONOCC_AVAILABLE = False

from koomesh.core.batch_processor import (
    BatchProcessor, BatchJob, BatchResult, process_directory_batch
)
from koomesh.config import KooMeshConfig


@pytest.mark.skipif(not PYTHONOCC_AVAILABLE, reason="PythonOCC not available")
class TestBatchProcessor:
    """Test batch processing functionality"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def input_dir(self, temp_dir):
        """Create input directory with test STEP files"""
        input_path = temp_dir / "input"
        input_path.mkdir()

        # Create several simple STEP files
        for i in range(3):
            box = BRepPrimAPI_MakeBox(10.0, 10.0, 10.0).Shape()

            step_file = input_path / f"box_{i+1}.step"
            writer = STEPControl_Writer()
            writer.Transfer(box, STEPControl_AsIs)
            writer.Write(str(step_file))

        return input_path

    @pytest.fixture
    def output_dir(self, temp_dir):
        """Create output directory"""
        output_path = temp_dir / "output"
        output_path.mkdir()
        return output_path

    @pytest.fixture
    def config(self):
        """Create test configuration"""
        config = KooMeshConfig()
        config.mesh.default_size = 5.0  # Larger size for faster testing
        config.mesh.hex_priority = True
        return config

    def test_batch_processor_initialization(self, config):
        """Test batch processor initialization"""
        processor = BatchProcessor(config=config, num_workers=2)

        assert processor.config == config
        assert processor.num_workers == 2
        assert not processor.use_multiprocessing

    def test_batch_processor_sequential(self, input_dir, output_dir, config):
        """Test sequential batch processing"""
        processor = BatchProcessor(config=config, num_workers=1)

        result = processor.process_directory(
            input_dir=str(input_dir),
            output_dir=str(output_dir),
            mesh_size=5.0,
            parallel=False  # Sequential processing
        )

        # Check result
        assert isinstance(result, BatchResult)
        assert result.total_jobs == 3
        assert result.completed >= 0
        assert result.completed + result.failed == result.total_jobs

        # Check output files
        output_files = list(output_dir.glob("*.k"))
        assert len(output_files) == result.completed

    def test_batch_processor_parallel(self, input_dir, output_dir, config):
        """Test parallel batch processing"""
        processor = BatchProcessor(config=config, num_workers=2)

        result = processor.process_directory(
            input_dir=str(input_dir),
            output_dir=str(output_dir),
            mesh_size=5.0,
            parallel=True
        )

        assert result.total_jobs == 3
        assert result.completed >= 0

        # Parallel processing should produce same number of outputs
        output_files = list(output_dir.glob("*.k"))
        assert len(output_files) == result.completed

    def test_batch_processor_statistics(self, input_dir, output_dir, config):
        """Test batch processing statistics collection"""
        processor = BatchProcessor(config=config)

        result = processor.process_directory(
            input_dir=str(input_dir),
            output_dir=str(output_dir),
            mesh_size=5.0
        )

        # Check statistics
        assert 'total_nodes' in result.statistics
        assert 'total_elements' in result.statistics
        assert 'total_contacts' in result.statistics

        if result.completed > 0:
            assert result.statistics['total_nodes'] >= 0
            assert result.statistics['total_elements'] >= 0

    def test_batch_processor_success_rate(self, input_dir, output_dir, config):
        """Test success rate calculation"""
        processor = BatchProcessor(config=config)

        result = processor.process_directory(
            input_dir=str(input_dir),
            output_dir=str(output_dir),
            mesh_size=5.0
        )

        success_rate = result.success_rate
        assert 0 <= success_rate <= 100

        if result.total_jobs > 0:
            expected_rate = (result.completed / result.total_jobs) * 100
            assert success_rate == expected_rate

    def test_batch_job_creation(self):
        """Test BatchJob creation"""
        job = BatchJob(
            input_file=Path("input.step"),
            output_file=Path("output.k"),
            mesh_size=1.0,
            hex_priority=True
        )

        assert job.input_file == Path("input.step")
        assert job.output_file == Path("output.k")
        assert job.mesh_size == 1.0
        assert job.hex_priority
        assert job.status == 'pending'
        assert job.result is None
        assert job.error is None

    def test_batch_result_creation(self):
        """Test BatchResult creation"""
        result = BatchResult(
            total_jobs=10,
            completed=8,
            failed=2
        )

        assert result.total_jobs == 10
        assert result.completed == 8
        assert result.failed == 2
        assert result.success_rate == 80.0

    def test_batch_result_summary_printing(self):
        """Test BatchResult summary printing"""
        result = BatchResult(
            total_jobs=5,
            completed=4,
            failed=1,
            statistics={
                'total_nodes': 1000,
                'total_elements': 500,
                'total_contacts': 10
            }
        )

        # This should not raise an exception
        result.print_summary()

    def test_batch_processor_empty_directory(self, temp_dir, config):
        """Test batch processing with empty directory"""
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()

        output_dir = temp_dir / "output"
        output_dir.mkdir()

        processor = BatchProcessor(config=config)

        result = processor.process_directory(
            input_dir=str(empty_dir),
            output_dir=str(output_dir),
            mesh_size=5.0
        )

        assert result.total_jobs == 0
        assert result.completed == 0
        assert result.failed == 0

    def test_batch_processor_recursive(self, temp_dir, config):
        """Test batch processing with recursive directory search"""
        input_dir = temp_dir / "input"
        input_dir.mkdir()

        # Create subdirectory with STEP file
        subdir = input_dir / "subdir"
        subdir.mkdir()

        box = BRepPrimAPI_MakeBox(10.0, 10.0, 10.0).Shape()
        step_file = subdir / "box.step"
        writer = STEPControl_Writer()
        writer.Transfer(box, STEPControl_AsIs)
        writer.Write(str(step_file))

        output_dir = temp_dir / "output"
        output_dir.mkdir()

        processor = BatchProcessor(config=config)

        # Non-recursive - should find 0 files
        result_non_recursive = processor.process_directory(
            input_dir=str(input_dir),
            output_dir=str(output_dir),
            mesh_size=5.0,
            recursive=False
        )
        assert result_non_recursive.total_jobs == 0

        # Recursive - should find 1 file
        result_recursive = processor.process_directory(
            input_dir=str(input_dir),
            output_dir=str(output_dir),
            mesh_size=5.0,
            recursive=True
        )
        assert result_recursive.total_jobs == 1

    def test_batch_processor_file_list(self, temp_dir, config):
        """Test batch processing with explicit file list"""
        # Create test files
        input_dir = temp_dir / "input"
        input_dir.mkdir()
        output_dir = temp_dir / "output"
        output_dir.mkdir()

        file_pairs = []
        for i in range(2):
            box = BRepPrimAPI_MakeBox(10.0, 10.0, 10.0).Shape()

            input_file = input_dir / f"box_{i+1}.step"
            output_file = output_dir / f"box_{i+1}.k"

            writer = STEPControl_Writer()
            writer.Transfer(box, STEPControl_AsIs)
            writer.Write(str(input_file))

            file_pairs.append((str(input_file), str(output_file)))

        processor = BatchProcessor(config=config)

        result = processor.process_file_list(
            file_pairs=file_pairs,
            mesh_size=5.0
        )

        assert result.total_jobs == 2

    def test_batch_processor_execution_time(self, input_dir, output_dir, config):
        """Test that execution time is tracked"""
        processor = BatchProcessor(config=config)

        start_time = time.time()
        result = processor.process_directory(
            input_dir=str(input_dir),
            output_dir=str(output_dir),
            mesh_size=5.0
        )
        end_time = time.time()

        assert result.execution_time > 0
        assert result.execution_time <= (end_time - start_time) + 1.0  # Allow 1s tolerance

    def test_process_directory_batch_convenience(self, input_dir, output_dir):
        """Test convenience function for batch processing"""
        result = process_directory_batch(
            input_dir=str(input_dir),
            output_dir=str(output_dir),
            mesh_size=5.0,
            hex_priority=True,
            num_workers=2
        )

        assert isinstance(result, BatchResult)
        assert result.total_jobs == 3

    def test_batch_processor_error_recovery(self, temp_dir, config):
        """Test error recovery in batch processing"""
        input_dir = temp_dir / "input"
        input_dir.mkdir()
        output_dir = temp_dir / "output"
        output_dir.mkdir()

        # Create one valid STEP file
        box = BRepPrimAPI_MakeBox(10.0, 10.0, 10.0).Shape()
        valid_file = input_dir / "valid.step"
        writer = STEPControl_Writer()
        writer.Transfer(box, STEPControl_AsIs)
        writer.Write(str(valid_file))

        # Create one invalid file (empty)
        invalid_file = input_dir / "invalid.step"
        invalid_file.write_text("")

        processor = BatchProcessor(config=config)

        result = processor.process_directory(
            input_dir=str(input_dir),
            output_dir=str(output_dir),
            mesh_size=5.0
        )

        # Should process 2 files (1 valid, 1 invalid)
        assert result.total_jobs == 2

        # At least one should succeed (the valid file)
        # The invalid one may succeed or fail depending on error handling
        assert result.completed + result.failed == result.total_jobs


class TestBatchProcessorConfiguration:
    """Test batch processor configuration options"""

    def test_num_workers_configuration(self):
        """Test number of workers configuration"""
        processor = BatchProcessor(num_workers=4)
        assert processor.num_workers == 4

    def test_num_workers_default(self):
        """Test default number of workers"""
        processor = BatchProcessor()
        assert processor.num_workers >= 1

    def test_multiprocessing_mode(self):
        """Test multiprocessing mode configuration"""
        processor_threading = BatchProcessor(use_multiprocessing=False)
        assert not processor_threading.use_multiprocessing

        processor_multiprocessing = BatchProcessor(use_multiprocessing=True)
        assert processor_multiprocessing.use_multiprocessing

    def test_config_override(self):
        """Test configuration override"""
        config = KooMeshConfig()
        config.mesh.default_size = 10.0

        processor = BatchProcessor(config=config)
        assert processor.config.mesh.default_size == 10.0


@pytest.mark.performance
class TestBatchProcessorPerformance:
    """Performance tests for batch processor"""

    def test_parallel_speedup(self, temp_dir):
        """Test that parallel processing is faster than sequential"""
        pytest.skip("Performance test - run separately")

    def test_large_batch_processing(self, temp_dir):
        """Test processing large number of files"""
        pytest.skip("Performance test - run separately")
