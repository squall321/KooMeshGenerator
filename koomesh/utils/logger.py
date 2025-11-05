"""
Logging Utility for KooMeshGenerator
=====================================

This module provides a comprehensive logging system with:
- Console and file output
- Color-coded console messages
- Rotating file logs
- Progress tracking integration
- Multiple log levels

Usage:
    >>> from koomesh.utils.logger import setup_logger, get_logger
    >>> logger = setup_logger('my_module')
    >>> logger.info('Processing started')
    >>> logger.debug('Debug information')
    >>> logger.error('An error occurred')
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler
from datetime import datetime


# ANSI color codes for terminal output
class ColorCodes:
    """ANSI color codes for colored terminal output"""
    GREY = '\033[90m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'


class ColoredFormatter(logging.Formatter):
    """
    Custom formatter that adds color to console output

    Different log levels are displayed in different colors:
    - DEBUG: Grey
    - INFO: Green
    - WARNING: Yellow
    - ERROR: Red
    - CRITICAL: Bold Red
    """

    COLORS = {
        logging.DEBUG: ColorCodes.GREY,
        logging.INFO: ColorCodes.GREEN,
        logging.WARNING: ColorCodes.YELLOW,
        logging.ERROR: ColorCodes.RED,
        logging.CRITICAL: ColorCodes.BOLD + ColorCodes.RED,
    }

    def format(self, record):
        """Format log record with colors"""
        # Save original format
        log_fmt = self._style._fmt

        # Add color based on level
        if record.levelno in self.COLORS:
            color = self.COLORS[record.levelno]
            # Color the level name
            record.levelname = f"{color}{record.levelname}{ColorCodes.RESET}"

        # Format the message
        result = super().format(record)

        # Restore original format
        self._style._fmt = log_fmt

        return result


class ProgressFormatter(logging.Formatter):
    """
    Formatter that integrates with progress bars

    This formatter ensures that log messages don't interfere with
    progress bar output (e.g., tqdm).
    """

    def format(self, record):
        """Format log record for progress-aware output"""
        # Check if tqdm is active
        try:
            from tqdm import tqdm
            if tqdm._instances:
                # Write above progress bar
                tqdm.write(super().format(record))
                return ''
        except ImportError:
            pass

        return super().format(record)


def setup_logger(
    name: str = 'koomesh',
    level: str = 'INFO',
    log_file: Optional[Path] = None,
    console_output: bool = True,
    file_output: bool = True,
    max_file_size: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
    format_string: Optional[str] = None,
) -> logging.Logger:
    """
    Setup and configure logger

    Args:
        name: Logger name (usually module name)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (default: koomesh.log in current directory)
        console_output: Enable console output
        file_output: Enable file output
        max_file_size: Maximum log file size before rotation
        backup_count: Number of backup files to keep
        format_string: Custom format string

    Returns:
        Configured logger instance

    Example:
        >>> logger = setup_logger('geometry', level='DEBUG')
        >>> logger.info('Geometry analysis started')
    """

    # Get or create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Default format string
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)

        # Use colored formatter for console
        console_formatter = ColoredFormatter(
            fmt=format_string,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    # File handler
    if file_output:
        if log_file is None:
            log_file = Path.cwd() / 'koomesh.log'
        else:
            log_file = Path(log_file)

        # Create log directory if it doesn't exist
        log_file.parent.mkdir(parents=True, exist_ok=True)

        # Use rotating file handler
        file_handler = RotatingFileHandler(
            filename=log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)

        # Use plain formatter for file (no colors)
        file_formatter = logging.Formatter(
            fmt=format_string,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get logger instance

    If logger doesn't exist, it will be created with default settings.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)

    # If logger has no handlers, set it up with defaults
    if not logger.handlers:
        logger = setup_logger(name)

    return logger


class LogContext:
    """
    Context manager for temporary log level changes

    Usage:
        >>> logger = get_logger('test')
        >>> with LogContext(logger, 'DEBUG'):
        ...     logger.debug('This will be shown')
    """

    def __init__(self, logger: logging.Logger, level: str):
        """
        Initialize log context

        Args:
            logger: Logger instance
            level: Temporary log level
        """
        self.logger = logger
        self.new_level = getattr(logging, level.upper())
        self.old_level = logger.level

    def __enter__(self):
        """Enter context - set new log level"""
        self.logger.setLevel(self.new_level)
        return self.logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context - restore old log level"""
        self.logger.setLevel(self.old_level)


class LogTimer:
    """
    Context manager for timing operations with logging

    Usage:
        >>> logger = get_logger('test')
        >>> with LogTimer(logger, 'Processing data'):
        ...     # do some work
        ...     pass
        # Logs: "Processing data completed in 1.23s"
    """

    def __init__(self, logger: logging.Logger, operation: str, level: str = 'INFO'):
        """
        Initialize log timer

        Args:
            logger: Logger instance
            operation: Description of operation being timed
            level: Log level for timing messages
        """
        self.logger = logger
        self.operation = operation
        self.level = getattr(logging, level.upper())
        self.start_time = None

    def __enter__(self):
        """Enter context - log start and record time"""
        self.logger.log(self.level, f"{self.operation} started...")
        self.start_time = datetime.now()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context - log completion time"""
        elapsed = (datetime.now() - self.start_time).total_seconds()

        if exc_type is None:
            self.logger.log(self.level, f"{self.operation} completed in {elapsed:.2f}s")
        else:
            self.logger.error(f"{self.operation} failed after {elapsed:.2f}s")


def log_function_call(logger: logging.Logger, level: str = 'DEBUG'):
    """
    Decorator to log function calls

    Args:
        logger: Logger instance
        level: Log level for function call logs

    Usage:
        >>> logger = get_logger('module')
        >>> @log_function_call(logger)
        ... def process_data(x, y):
        ...     return x + y
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            func_name = func.__name__
            logger.log(
                getattr(logging, level.upper()),
                f"Calling {func_name}(args={args}, kwargs={kwargs})"
            )
            try:
                result = func(*args, **kwargs)
                logger.log(
                    getattr(logging, level.upper()),
                    f"{func_name} returned: {result}"
                )
                return result
            except Exception as e:
                logger.error(f"{func_name} raised exception: {e}")
                raise
        return wrapper
    return decorator


# Module-level logger
_module_logger = None


def get_module_logger() -> logging.Logger:
    """Get the main module logger"""
    global _module_logger
    if _module_logger is None:
        _module_logger = setup_logger('koomesh')
    return _module_logger


# Convenience functions
def debug(msg: str):
    """Log debug message"""
    get_module_logger().debug(msg)


def info(msg: str):
    """Log info message"""
    get_module_logger().info(msg)


def warning(msg: str):
    """Log warning message"""
    get_module_logger().warning(msg)


def error(msg: str):
    """Log error message"""
    get_module_logger().error(msg)


def critical(msg: str):
    """Log critical message"""
    get_module_logger().critical(msg)
