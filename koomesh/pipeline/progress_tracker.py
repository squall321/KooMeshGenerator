"""
Progress tracking for mesh generation pipeline

This module provides real-time progress tracking for the mesh generation
pipeline, allowing users to monitor the status of each stage.
"""

from typing import Optional, Callable, Dict
from dataclasses import dataclass
from enum import Enum
import time


class StageStatus(Enum):
    """Status of a pipeline stage"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StageProgress:
    """
    Progress information for a single stage

    Attributes:
        name: Stage name
        status: Current status
        progress: Progress from 0.0 to 1.0
        message: Status message
        start_time: Start timestamp (Unix time)
        end_time: End timestamp (Unix time)
    """
    name: str
    status: StageStatus
    progress: float  # 0.0 to 1.0
    message: str
    start_time: Optional[float] = None
    end_time: Optional[float] = None

    @property
    def duration(self) -> Optional[float]:
        """Get stage duration in seconds"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None

    @property
    def is_complete(self) -> bool:
        """Check if stage is completed"""
        return self.status == StageStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        """Check if stage failed"""
        return self.status == StageStatus.FAILED

    @property
    def is_running(self) -> bool:
        """Check if stage is currently running"""
        return self.status == StageStatus.RUNNING


class ProgressTracker:
    """
    Track progress through pipeline stages

    Features:
    - Stage-based progress tracking
    - Time tracking for each stage
    - Callbacks for UI updates
    - Summary statistics

    Example:
        >>> def on_progress(stages):
        ...     for name, stage in stages.items():
        ...         print(f"{name}: {stage.status.value} ({stage.progress*100:.0f}%)")
        >>>
        >>> tracker = ProgressTracker(callback=on_progress)
        >>> tracker.add_stage("geometry", "Reading geometry")
        >>> tracker.start_stage("geometry")
        >>> tracker.update_stage("geometry", 0.5, "Processing...")
        >>> tracker.complete_stage("geometry", "Done!")
    """

    def __init__(self, callback: Optional[Callable[[Dict[str, StageProgress]], None]] = None):
        """
        Initialize progress tracker

        Args:
            callback: Optional callback function called on progress updates.
                     Receives dict of stage name -> StageProgress
        """
        self.callback = callback
        self.stages: Dict[str, StageProgress] = {}
        self.current_stage: Optional[str] = None
        self._total_start_time: Optional[float] = None

    def add_stage(self, name: str, message: str = ""):
        """
        Add a new stage to track

        Args:
            name: Stage identifier
            message: Initial status message
        """
        self.stages[name] = StageProgress(
            name=name,
            status=StageStatus.PENDING,
            progress=0.0,
            message=message
        )

    def start_stage(self, name: str, message: str = ""):
        """
        Start a stage

        Args:
            name: Stage identifier
            message: Optional status message
        """
        if name not in self.stages:
            self.add_stage(name, message)

        self.current_stage = name
        self.stages[name].status = StageStatus.RUNNING
        self.stages[name].start_time = time.time()
        self.stages[name].progress = 0.0

        if message:
            self.stages[name].message = message

        if self._total_start_time is None:
            self._total_start_time = time.time()

        self._notify()

    def update_stage(self, name: str, progress: float, message: str = ""):
        """
        Update stage progress

        Args:
            name: Stage identifier
            progress: Progress value from 0.0 to 1.0
            message: Optional status message
        """
        if name not in self.stages:
            raise ValueError(f"Stage '{name}' not found")

        # Clamp progress to [0.0, 1.0]
        progress = max(0.0, min(1.0, progress))

        self.stages[name].progress = progress
        if message:
            self.stages[name].message = message

        self._notify()

    def complete_stage(self, name: str, message: str = ""):
        """
        Mark stage as completed

        Args:
            name: Stage identifier
            message: Optional completion message
        """
        if name not in self.stages:
            raise ValueError(f"Stage '{name}' not found")

        self.stages[name].status = StageStatus.COMPLETED
        self.stages[name].progress = 1.0
        self.stages[name].end_time = time.time()

        if message:
            self.stages[name].message = message

        self._notify()

    def fail_stage(self, name: str, error: str):
        """
        Mark stage as failed

        Args:
            name: Stage identifier
            error: Error message
        """
        if name not in self.stages:
            raise ValueError(f"Stage '{name}' not found")

        self.stages[name].status = StageStatus.FAILED
        self.stages[name].message = error
        self.stages[name].end_time = time.time()

        self._notify()

    def skip_stage(self, name: str, reason: str = ""):
        """
        Mark stage as skipped

        Args:
            name: Stage identifier
            reason: Optional reason for skipping
        """
        if name not in self.stages:
            raise ValueError(f"Stage '{name}' not found")

        self.stages[name].status = StageStatus.SKIPPED
        self.stages[name].progress = 1.0
        if reason:
            self.stages[name].message = reason

        self._notify()

    def _notify(self):
        """Notify callback of progress update"""
        if self.callback:
            try:
                self.callback(self.stages)
            except Exception as e:
                # Don't let callback errors break the pipeline
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Progress callback error: {e}")

    def get_summary(self) -> dict:
        """
        Get progress summary statistics

        Returns:
            Dictionary with summary information:
            - total_stages: Total number of stages
            - completed: Number of completed stages
            - failed: Number of failed stages
            - running: Number of running stages
            - overall_progress: Overall progress (0.0 to 1.0)
            - total_duration: Total elapsed time (seconds)
            - stages: Dict of all stage progress
        """
        total = len(self.stages)
        completed = sum(1 for s in self.stages.values()
                       if s.status == StageStatus.COMPLETED)
        failed = sum(1 for s in self.stages.values()
                    if s.status == StageStatus.FAILED)
        running = sum(1 for s in self.stages.values()
                     if s.status == StageStatus.RUNNING)

        # Calculate overall progress
        if total > 0:
            overall_progress = sum(s.progress for s in self.stages.values()) / total
        else:
            overall_progress = 0.0

        # Calculate total duration
        total_duration = None
        if self._total_start_time is not None:
            # If all stages complete, use last end time
            if completed + failed == total:
                end_times = [s.end_time for s in self.stages.values()
                           if s.end_time is not None]
                if end_times:
                    total_duration = max(end_times) - self._total_start_time
            else:
                # Otherwise use current time
                total_duration = time.time() - self._total_start_time

        return {
            'total_stages': total,
            'completed': completed,
            'failed': failed,
            'running': running,
            'overall_progress': overall_progress,
            'total_duration': total_duration,
            'stages': self.stages
        }

    def reset(self):
        """Reset all stages to pending"""
        for stage in self.stages.values():
            stage.status = StageStatus.PENDING
            stage.progress = 0.0
            stage.start_time = None
            stage.end_time = None
        self.current_stage = None
        self._total_start_time = None

    def __repr__(self) -> str:
        """String representation"""
        summary = self.get_summary()
        return (f"ProgressTracker("
                f"stages={summary['total_stages']}, "
                f"completed={summary['completed']}, "
                f"progress={summary['overall_progress']:.1%})")
