"""
Pytest configuration and fixtures for KooMeshGenerator tests
=============================================================

This module provides common fixtures and test utilities used across
all test modules.
"""

import pytest
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def temp_dir():
    """
    Provide a temporary directory for tests

    Yields:
        Path to temporary directory (automatically cleaned up after test)
    """
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def fixtures_dir():
    """
    Provide path to test fixtures directory

    Returns:
        Path to fixtures directory
    """
    return Path(__file__).parent / 'fixtures'


@pytest.fixture
def step_files_dir(fixtures_dir):
    """
    Provide path to STEP test files directory

    Returns:
        Path to STEP files directory
    """
    return fixtures_dir / 'step_files'


@pytest.fixture
def sample_config():
    """
    Provide sample configuration for tests

    Returns:
        Config instance with test settings
    """
    from koomesh.config import Config

    config = Config()
    config.mesh.default_size = 1.0
    config.log.level = 'DEBUG'
    config.log.file_output = False  # Don't create log files during tests

    return config


@pytest.fixture
def mock_logger():
    """
    Provide a logger for tests

    Returns:
        Logger instance configured for testing
    """
    from koomesh.utils.logger import setup_logger

    return setup_logger(
        'test',
        level='DEBUG',
        console_output=False,
        file_output=False
    )
