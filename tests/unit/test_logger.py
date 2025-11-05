"""
Unit tests for logging utility
"""

import pytest
import logging
from koomesh.utils.logger import (
    setup_logger,
    get_logger,
    LogContext,
    LogTimer
)


def test_logger_setup():
    """Test logger initialization"""
    logger = setup_logger('test', level='DEBUG', console_output=False, file_output=False)

    assert logger.name == 'test'
    assert logger.level == logging.DEBUG


def test_logger_levels(mock_logger):
    """Test different log levels"""
    # Should not raise any exceptions
    mock_logger.debug('Debug message')
    mock_logger.info('Info message')
    mock_logger.warning('Warning message')
    mock_logger.error('Error message')


def test_log_context(mock_logger):
    """Test LogContext for temporary level changes"""
    original_level = mock_logger.level

    with LogContext(mock_logger, 'ERROR'):
        assert mock_logger.level == logging.ERROR

    assert mock_logger.level == original_level


def test_log_timer(mock_logger):
    """Test LogTimer for operation timing"""
    import time

    with LogTimer(mock_logger, 'Test operation'):
        time.sleep(0.1)

    # Should complete without errors
