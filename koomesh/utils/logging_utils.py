"""
Logging Utilities

Provides structured logging and performance tracking for KooMeshGenerator.
"""

import logging
import time
from typing import Optional
from contextlib import contextmanager
from functools import wraps


class PerformanceLogger:
    """
    Track and log performance metrics.

    Example:
        >>> perf_logger = PerformanceLogger()
        >>> with perf_logger.timer("mesh_generation"):
        ...     generate_mesh()
        >>> perf_logger.log_statistics()
    """

    def __init__(self, logger_name: Optional[str] = None):
        self.logger = logging.getLogger(logger_name or __name__)
        self.timings = {}
        self.counters = {}

    @contextmanager
    def timer(self, operation_name: str):
        """
        Context manager for timing operations.

        Args:
            operation_name: Name of the operation being timed

        Example:
            >>> with perf_logger.timer("contact_detection"):
            ...     detect_contacts()
        """
        start_time = time.time()
        self.logger.debug(f"Starting: {operation_name}")

        try:
            yield
        finally:
            elapsed = time.time() - start_time

            # Store timing
            if operation_name not in self.timings:
                self.timings[operation_name] = []
            self.timings[operation_name].append(elapsed)

            # Log
            self.logger.info(
                f"Completed: {operation_name} in {elapsed:.3f}s"
            )

    def increment_counter(self, counter_name: str, value: int = 1):
        """Increment a counter."""
        if counter_name not in self.counters:
            self.counters[counter_name] = 0
        self.counters[counter_name] += value

    def log_statistics(self):
        """Log accumulated statistics."""
        if self.timings:
            self.logger.info("=== Performance Statistics ===")
            for operation, times in self.timings.items():
                avg_time = sum(times) / len(times)
                total_time = sum(times)
                self.logger.info(
                    f"  {operation}: "
                    f"avg={avg_time:.3f}s, "
                    f"total={total_time:.3f}s, "
                    f"count={len(times)}"
                )

        if self.counters:
            self.logger.info("=== Counters ===")
            for counter, value in self.counters.items():
                self.logger.info(f"  {counter}: {value}")


def performance_tracked(operation_name: Optional[str] = None):
    """
    Decorator to track function performance.

    Args:
        operation_name: Name of operation (defaults to function name)

    Example:
        >>> @performance_tracked("mesh_generation")
        ... def generate_mesh():
        ...     pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__module__)
            op_name = operation_name or func.__name__

            start_time = time.time()
            logger.debug(f"Starting: {op_name}")

            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                logger.info(f"Completed: {op_name} in {elapsed:.3f}s")
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"Failed: {op_name} after {elapsed:.3f}s - {e}")
                raise

        return wrapper
    return decorator


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    enable_colors: bool = True
):
    """
    Configure logging for KooMeshGenerator.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional log file path
        enable_colors: Enable colored output (requires colorama)

    Example:
        >>> setup_logging(level="DEBUG", log_file="koomesh.log")
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Create formatter
    log_format = (
        '%(asctime)s - %(name)s - %(levelname)s - '
        '%(message)s'
    )

    formatter = logging.Formatter(
        log_format,
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Configure root logger
    root_logger = logging.getLogger('koomesh')
    root_logger.setLevel(numeric_level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        root_logger.info(f"Logging to file: {log_file}")

    root_logger.info(f"Logging initialized at {level} level")


class ProgressReporter:
    """
    Report progress for long-running operations.

    Example:
        >>> reporter = ProgressReporter("Processing parts", total=100)
        >>> for i in range(100):
        ...     reporter.update(1)
        >>> reporter.finish()
    """

    def __init__(
        self,
        description: str,
        total: int,
        logger_name: Optional[str] = None
    ):
        self.description = description
        self.total = total
        self.current = 0
        self.logger = logging.getLogger(logger_name or __name__)
        self.start_time = time.time()
        self.last_report_time = self.start_time
        self.report_interval = 5.0  # Report every 5 seconds

        self.logger.info(f"{description}: Starting (total={total})")

    def update(self, n: int = 1):
        """Update progress by n items."""
        self.current += n

        # Report progress periodically
        current_time = time.time()
        if current_time - self.last_report_time >= self.report_interval:
            self._report_progress()
            self.last_report_time = current_time

    def _report_progress(self):
        """Report current progress."""
        if self.total > 0:
            percent = (self.current / self.total) * 100
            elapsed = time.time() - self.start_time

            if self.current > 0:
                eta = (elapsed / self.current) * (self.total - self.current)
                self.logger.info(
                    f"{self.description}: {self.current}/{self.total} "
                    f"({percent:.1f}%) - ETA: {eta:.1f}s"
                )
            else:
                self.logger.info(
                    f"{self.description}: {self.current}/{self.total} "
                    f"({percent:.1f}%)"
                )

    def finish(self):
        """Mark operation as complete."""
        elapsed = time.time() - self.start_time
        self.logger.info(
            f"{self.description}: Completed {self.current}/{self.total} "
            f"in {elapsed:.2f}s"
        )
