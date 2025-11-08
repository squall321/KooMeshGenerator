"""
Tests for GeometryProcessor

Tests the geometry processing functionality for the pipeline.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

from koomesh.pipeline.geometry_processor import (
    GeometryProcessor,
    GeometryProcessingError
)
from koomesh.pipeline.constants import (
    DEFAULT_GEOMETRY_TOLERANCE,
    MIN_GEOMETRY_TOLERANCE,
    MAX_GEOMETRY_TOLERANCE,
)


class TestGeometryProcessorInit:
    """Test GeometryProcessor initialization"""

    def test_init_success(self):
        """Test successful initialization"""
        processor = GeometryProcessor()

        assert processor.step_reader is not None
        assert processor.classifier is not None
        assert processor.cleaner is not None
        assert processor.logger is not None

    def test_init_creates_components(self):
        """Test that initialization creates all required components"""
        processor = GeometryProcessor()

        # Check components are initialized
        assert hasattr(processor, 'step_reader')
        assert hasattr(processor, 'classifier')
        assert hasattr(processor, 'cleaner')


class TestGeometryProcessorProcess:
    """Test GeometryProcessor.process() method"""

    def test_process_empty_file_list(self):
        """Test process with empty file list"""
        processor = GeometryProcessor()

        with pytest.raises(ValueError, match="No input files provided"):
            processor.process(input_files=[])

    def test_process_invalid_tolerance_too_small(self):
        """Test process with tolerance below minimum"""
        processor = GeometryProcessor()

        with pytest.raises(ValueError, match="out of valid range"):
            processor.process(
                input_files=["test.step"],
                tolerance=1e-10  # Too small
            )

    def test_process_invalid_tolerance_too_large(self):
        """Test process with tolerance above maximum"""
        processor = GeometryProcessor()

        with pytest.raises(ValueError, match="out of valid range"):
            processor.process(
                input_files=["test.step"],
                tolerance=10.0  # Too large
            )

    def test_process_file_not_found(self):
        """Test process with non-existent file"""
        processor = GeometryProcessor()

        with pytest.raises(GeometryProcessingError, match="Failed to process"):
            processor.process(
                input_files=["nonexistent_file.step"]
            )

    @patch('koomesh.pipeline.geometry_processor.STEPReader')
    @patch('koomesh.pipeline.geometry_processor.ShapeClassifier')
    def test_process_single_file_no_clean(
        self,
        mock_classifier_class,
        mock_reader_class,
        tmp_path
    ):
        """Test processing single file without cleaning"""
        # Create test file
        test_file = tmp_path / "test.step"
        test_file.write_text("dummy content")

        # Mock shape
        mock_shape = Mock()

        # Mock reader
        mock_reader = Mock()
        mock_reader.read_file.return_value = [mock_shape]
        mock_reader_class.return_value = mock_reader

        # Mock classifier
        mock_classifier = Mock()
        mock_classifier.classify.return_value = 'solid'
        mock_classifier_class.return_value = mock_classifier

        # Process
        processor = GeometryProcessor()
        results = processor.process(
            input_files=[str(test_file)],
            clean=False
        )

        # Assertions
        assert len(results) == 1
        shape, shape_type = results[0]
        assert shape == mock_shape
        assert shape_type == 'solid'

        # Verify reader was called
        mock_reader.read_file.assert_called_once_with(str(test_file))

        # Verify classifier was called
        mock_classifier.classify.assert_called_once()

    @patch('koomesh.pipeline.geometry_processor.STEPReader')
    @patch('koomesh.pipeline.geometry_processor.ShapeClassifier')
    @patch('koomesh.pipeline.geometry_processor.GeometryCleaner')
    def test_process_single_file_with_clean(
        self,
        mock_cleaner_class,
        mock_classifier_class,
        mock_reader_class,
        tmp_path
    ):
        """Test processing single file with cleaning"""
        # Create test file
        test_file = tmp_path / "test.step"
        test_file.write_text("dummy content")

        # Mock shapes
        mock_shape = Mock()
        mock_cleaned_shape = Mock()

        # Mock reader
        mock_reader = Mock()
        mock_reader.read_file.return_value = [mock_shape]
        mock_reader_class.return_value = mock_reader

        # Mock cleaner
        mock_cleaner = Mock()
        mock_cleaner.remove_duplicate_faces.return_value = mock_cleaned_shape
        mock_cleaner.heal_surface.return_value = mock_cleaned_shape
        mock_cleaner_class.return_value = mock_cleaner

        # Mock classifier
        mock_classifier = Mock()
        mock_classifier.classify.return_value = 'shell'
        mock_classifier_class.return_value = mock_classifier

        # Process
        processor = GeometryProcessor()
        results = processor.process(
            input_files=[str(test_file)],
            clean=True,
            tolerance=1e-3
        )

        # Assertions
        assert len(results) == 1
        shape, shape_type = results[0]
        assert shape == mock_cleaned_shape
        assert shape_type == 'shell'

        # Verify cleaner was called
        mock_cleaner.remove_duplicate_faces.assert_called()
        mock_cleaner.heal_surface.assert_called()

    @patch('koomesh.pipeline.geometry_processor.STEPReader')
    @patch('koomesh.pipeline.geometry_processor.ShapeClassifier')
    def test_process_multiple_files(
        self,
        mock_classifier_class,
        mock_reader_class,
        tmp_path
    ):
        """Test processing multiple files"""
        # Create test files
        test_file1 = tmp_path / "test1.step"
        test_file1.write_text("dummy content 1")
        test_file2 = tmp_path / "test2.step"
        test_file2.write_text("dummy content 2")

        # Mock shapes
        mock_shape1 = Mock()
        mock_shape2 = Mock()
        mock_shape3 = Mock()

        # Mock reader
        mock_reader = Mock()
        mock_reader.read_file.side_effect = [
            [mock_shape1, mock_shape2],  # File 1 has 2 shapes
            [mock_shape3]                 # File 2 has 1 shape
        ]
        mock_reader_class.return_value = mock_reader

        # Mock classifier
        mock_classifier = Mock()
        mock_classifier.classify.side_effect = ['solid', 'shell', 'beam']
        mock_classifier_class.return_value = mock_classifier

        # Process
        processor = GeometryProcessor()
        results = processor.process(
            input_files=[str(test_file1), str(test_file2)],
            clean=False
        )

        # Assertions
        assert len(results) == 3
        assert results[0][1] == 'solid'
        assert results[1][1] == 'shell'
        assert results[2][1] == 'beam'

        # Verify reader was called twice
        assert mock_reader.read_file.call_count == 2

    @patch('koomesh.pipeline.geometry_processor.STEPReader')
    def test_process_empty_step_file(
        self,
        mock_reader_class,
        tmp_path
    ):
        """Test processing STEP file with no shapes"""
        # Create test file
        test_file = tmp_path / "empty.step"
        test_file.write_text("empty")

        # Mock reader returns empty list
        mock_reader = Mock()
        mock_reader.read_file.return_value = []
        mock_reader_class.return_value = mock_reader

        # Process
        processor = GeometryProcessor()
        results = processor.process(
            input_files=[str(test_file)]
        )

        # Should return empty results
        assert len(results) == 0

    @patch('koomesh.pipeline.geometry_processor.STEPReader')
    @patch('koomesh.pipeline.geometry_processor.ShapeClassifier')
    def test_process_classification_failure(
        self,
        mock_classifier_class,
        mock_reader_class,
        tmp_path
    ):
        """Test handling of classification failures"""
        # Create test file
        test_file = tmp_path / "test.step"
        test_file.write_text("dummy content")

        # Mock shape
        mock_shape = Mock()

        # Mock reader
        mock_reader = Mock()
        mock_reader.read_file.return_value = [mock_shape]
        mock_reader_class.return_value = mock_reader

        # Mock classifier raises exception
        mock_classifier = Mock()
        mock_classifier.classify.side_effect = Exception("Classification failed")
        mock_classifier_class.return_value = mock_classifier

        # Process - should default to 'solid' on classification failure
        processor = GeometryProcessor()
        results = processor.process(
            input_files=[str(test_file)],
            clean=False
        )

        # Should still return result with default type
        assert len(results) == 1
        shape, shape_type = results[0]
        assert shape_type == 'solid'  # Default type


class TestGeometryProcessorStatistics:
    """Test GeometryProcessor.get_statistics() method"""

    def test_get_statistics_empty(self):
        """Test statistics with empty results"""
        processor = GeometryProcessor()
        stats = processor.get_statistics([])

        assert stats['total_shapes'] == 0
        assert stats['solid_count'] == 0
        assert stats['shell_count'] == 0
        assert stats['beam_count'] == 0
        assert stats['unknown_count'] == 0

    def test_get_statistics_mixed_types(self):
        """Test statistics with mixed shape types"""
        processor = GeometryProcessor()

        mock_shape = Mock()
        results = [
            (mock_shape, 'solid'),
            (mock_shape, 'solid'),
            (mock_shape, 'shell'),
            (mock_shape, 'beam'),
            (mock_shape, 'unknown'),
        ]

        stats = processor.get_statistics(results)

        assert stats['total_shapes'] == 5
        assert stats['solid_count'] == 2
        assert stats['shell_count'] == 1
        assert stats['beam_count'] == 1
        assert stats['unknown_count'] == 1


class TestGeometryProcessorSingleFile:
    """Test GeometryProcessor.process_single_file() convenience method"""

    @patch('koomesh.pipeline.geometry_processor.STEPReader')
    @patch('koomesh.pipeline.geometry_processor.ShapeClassifier')
    def test_process_single_file_convenience(
        self,
        mock_classifier_class,
        mock_reader_class,
        tmp_path
    ):
        """Test process_single_file convenience method"""
        # Create test file
        test_file = tmp_path / "test.step"
        test_file.write_text("dummy content")

        # Mock shape
        mock_shape = Mock()

        # Mock reader
        mock_reader = Mock()
        mock_reader.read_file.return_value = [mock_shape]
        mock_reader_class.return_value = mock_reader

        # Mock classifier
        mock_classifier = Mock()
        mock_classifier.classify.return_value = 'solid'
        mock_classifier_class.return_value = mock_classifier

        # Process
        processor = GeometryProcessor()
        results = processor.process_single_file(str(test_file))

        # Assertions
        assert len(results) == 1
        shape, shape_type = results[0]
        assert shape_type == 'solid'
