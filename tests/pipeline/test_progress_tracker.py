"""
Tests for ProgressTracker
"""

import pytest
import time
from koomesh.pipeline.progress_tracker import (
    ProgressTracker,
    StageProgress,
    StageStatus
)


class TestStageProgress:
    """Test StageProgress dataclass"""

    def test_create_stage_progress(self):
        """Test creating stage progress"""
        stage = StageProgress(
            name="test",
            status=StageStatus.PENDING,
            progress=0.0,
            message="Test stage"
        )

        assert stage.name == "test"
        assert stage.status == StageStatus.PENDING
        assert stage.progress == 0.0
        assert stage.message == "Test stage"
        assert stage.start_time is None
        assert stage.end_time is None

    def test_duration(self):
        """Test duration calculation"""
        stage = StageProgress(
            name="test",
            status=StageStatus.COMPLETED,
            progress=1.0,
            message="Done",
            start_time=100.0,
            end_time=105.5
        )

        assert stage.duration == 5.5

    def test_duration_none(self):
        """Test duration when times not set"""
        stage = StageProgress(
            name="test",
            status=StageStatus.PENDING,
            progress=0.0,
            message="Waiting"
        )

        assert stage.duration is None

    def test_is_complete(self):
        """Test is_complete property"""
        stage = StageProgress(
            name="test",
            status=StageStatus.COMPLETED,
            progress=1.0,
            message="Done"
        )

        assert stage.is_complete is True
        assert stage.is_failed is False
        assert stage.is_running is False

    def test_is_failed(self):
        """Test is_failed property"""
        stage = StageProgress(
            name="test",
            status=StageStatus.FAILED,
            progress=0.5,
            message="Error occurred"
        )

        assert stage.is_complete is False
        assert stage.is_failed is True
        assert stage.is_running is False

    def test_is_running(self):
        """Test is_running property"""
        stage = StageProgress(
            name="test",
            status=StageStatus.RUNNING,
            progress=0.3,
            message="Processing..."
        )

        assert stage.is_complete is False
        assert stage.is_failed is False
        assert stage.is_running is True


class TestProgressTracker:
    """Test ProgressTracker class"""

    def test_create_tracker(self):
        """Test creating progress tracker"""
        tracker = ProgressTracker()

        assert len(tracker.stages) == 0
        assert tracker.current_stage is None

    def test_add_stage(self):
        """Test adding a stage"""
        tracker = ProgressTracker()
        tracker.add_stage("geometry", "Reading geometry")

        assert "geometry" in tracker.stages
        assert tracker.stages["geometry"].name == "geometry"
        assert tracker.stages["geometry"].status == StageStatus.PENDING
        assert tracker.stages["geometry"].message == "Reading geometry"

    def test_start_stage(self):
        """Test starting a stage"""
        tracker = ProgressTracker()
        tracker.add_stage("geometry", "Reading geometry")
        tracker.start_stage("geometry")

        stage = tracker.stages["geometry"]
        assert stage.status == StageStatus.RUNNING
        assert stage.start_time is not None
        assert tracker.current_stage == "geometry"

    def test_start_stage_auto_add(self):
        """Test starting a stage that wasn't added"""
        tracker = ProgressTracker()
        tracker.start_stage("geometry", "Reading geometry")

        assert "geometry" in tracker.stages
        assert tracker.stages["geometry"].status == StageStatus.RUNNING

    def test_update_stage(self):
        """Test updating stage progress"""
        tracker = ProgressTracker()
        tracker.start_stage("geometry")
        tracker.update_stage("geometry", 0.5, "Processing...")

        stage = tracker.stages["geometry"]
        assert stage.progress == 0.5
        assert stage.message == "Processing..."

    def test_update_stage_clamp(self):
        """Test progress clamping to [0, 1]"""
        tracker = ProgressTracker()
        tracker.start_stage("geometry")

        # Test too high
        tracker.update_stage("geometry", 1.5)
        assert tracker.stages["geometry"].progress == 1.0

        # Test too low
        tracker.update_stage("geometry", -0.5)
        assert tracker.stages["geometry"].progress == 0.0

    def test_update_stage_not_found(self):
        """Test updating non-existent stage"""
        tracker = ProgressTracker()

        with pytest.raises(ValueError, match="Stage 'geometry' not found"):
            tracker.update_stage("geometry", 0.5)

    def test_complete_stage(self):
        """Test completing a stage"""
        tracker = ProgressTracker()
        tracker.start_stage("geometry")
        time.sleep(0.01)  # Small delay
        tracker.complete_stage("geometry", "Done!")

        stage = tracker.stages["geometry"]
        assert stage.status == StageStatus.COMPLETED
        assert stage.progress == 1.0
        assert stage.end_time is not None
        assert stage.message == "Done!"
        assert stage.duration is not None
        assert stage.duration > 0

    def test_fail_stage(self):
        """Test failing a stage"""
        tracker = ProgressTracker()
        tracker.start_stage("geometry")
        time.sleep(0.01)
        tracker.fail_stage("geometry", "Error: File not found")

        stage = tracker.stages["geometry"]
        assert stage.status == StageStatus.FAILED
        assert stage.end_time is not None
        assert stage.message == "Error: File not found"

    def test_skip_stage(self):
        """Test skipping a stage"""
        tracker = ProgressTracker()
        tracker.add_stage("quality", "Quality check")
        tracker.skip_stage("quality", "Quality check disabled")

        stage = tracker.stages["quality"]
        assert stage.status == StageStatus.SKIPPED
        assert stage.progress == 1.0
        assert stage.message == "Quality check disabled"

    def test_callback(self):
        """Test progress callback"""
        callback_calls = []

        def on_progress(stages):
            callback_calls.append(len(stages))

        tracker = ProgressTracker(callback=on_progress)
        tracker.add_stage("geometry", "Reading")
        tracker.start_stage("geometry")
        tracker.update_stage("geometry", 0.5)
        tracker.complete_stage("geometry")

        # Callback should be called 3 times (start, update, complete)
        assert len(callback_calls) == 3

    def test_callback_error_handling(self):
        """Test that callback errors don't break tracker"""
        def bad_callback(stages):
            raise RuntimeError("Callback error!")

        tracker = ProgressTracker(callback=bad_callback)
        tracker.start_stage("geometry")  # Should not raise

        assert tracker.stages["geometry"].status == StageStatus.RUNNING

    def test_get_summary(self):
        """Test getting progress summary"""
        tracker = ProgressTracker()

        # Add and complete some stages
        tracker.add_stage("geometry", "Reading")
        tracker.add_stage("meshing", "Generating")
        tracker.add_stage("quality", "Checking")

        tracker.start_stage("geometry")
        tracker.complete_stage("geometry")

        tracker.start_stage("meshing")
        tracker.update_stage("meshing", 0.5)

        summary = tracker.get_summary()

        assert summary['total_stages'] == 3
        assert summary['completed'] == 1
        assert summary['failed'] == 0
        assert summary['running'] == 1
        assert 0 < summary['overall_progress'] < 1.0
        assert summary['total_duration'] is not None

    def test_get_summary_all_complete(self):
        """Test summary when all stages complete"""
        tracker = ProgressTracker()

        tracker.add_stage("stage1")
        tracker.add_stage("stage2")

        tracker.start_stage("stage1")
        time.sleep(0.01)
        tracker.complete_stage("stage1")

        tracker.start_stage("stage2")
        time.sleep(0.01)
        tracker.complete_stage("stage2")

        summary = tracker.get_summary()

        assert summary['total_stages'] == 2
        assert summary['completed'] == 2
        assert summary['overall_progress'] == 1.0
        assert summary['total_duration'] is not None

    def test_reset(self):
        """Test resetting tracker"""
        tracker = ProgressTracker()

        tracker.start_stage("geometry")
        tracker.complete_stage("geometry")

        tracker.reset()

        assert tracker.stages["geometry"].status == StageStatus.PENDING
        assert tracker.stages["geometry"].progress == 0.0
        assert tracker.stages["geometry"].start_time is None
        assert tracker.stages["geometry"].end_time is None
        assert tracker.current_stage is None

    def test_multiple_stages_workflow(self):
        """Test realistic multi-stage workflow"""
        tracker = ProgressTracker()

        stages = [
            "geometry",
            "meshing",
            "quality",
            "contact",
            "export",
            "validation"
        ]

        # Add all stages
        for stage in stages:
            tracker.add_stage(stage, f"Stage: {stage}")

        # Process stages
        for i, stage in enumerate(stages):
            tracker.start_stage(stage)

            # Simulate some progress
            for progress in [0.25, 0.5, 0.75]:
                tracker.update_stage(stage, progress)

            tracker.complete_stage(stage, f"{stage} complete")

            # Check summary
            summary = tracker.get_summary()
            assert summary['completed'] == i + 1

        # Final check
        summary = tracker.get_summary()
        assert summary['completed'] == len(stages)
        assert summary['overall_progress'] == 1.0

    def test_repr(self):
        """Test string representation"""
        tracker = ProgressTracker()
        tracker.add_stage("stage1")
        tracker.start_stage("stage1")
        tracker.complete_stage("stage1")

        repr_str = repr(tracker)
        assert "ProgressTracker" in repr_str
        assert "stages=1" in repr_str
        assert "completed=1" in repr_str
        assert "progress=" in repr_str


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
