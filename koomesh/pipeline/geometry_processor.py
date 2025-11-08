"""
Geometry Processor for Pipeline
=================================

Process geometry for meshing pipeline.

Steps:
1. Read STEP file(s)
2. Extract shapes
3. Clean geometry (remove duplicates, heal)
4. Classify shapes (solid/shell/beam)

Author: KooMeshGenerator Team
"""

import logging
from typing import List, Tuple, Any, Optional
from pathlib import Path

from koomesh.io.step_reader import STEPReader
from koomesh.geometry.shape_classifier import ShapeClassifier
from koomesh.preprocessing.geometry_cleaner import GeometryCleaner
from koomesh.pipeline.constants import (
    DEFAULT_GEOMETRY_TOLERANCE,
    MIN_GEOMETRY_TOLERANCE,
    MAX_GEOMETRY_TOLERANCE,
)

logger = logging.getLogger(__name__)


class GeometryProcessingError(Exception):
    """Raised when geometry processing fails"""
    pass


class GeometryProcessor:
    """
    Process geometry for meshing pipeline

    This class orchestrates the complete geometry processing workflow:
    - Reading STEP files
    - Cleaning geometry (optional)
    - Classifying shapes

    Example:
        >>> processor = GeometryProcessor()
        >>> shapes = processor.process(
        ...     input_files=["part1.step", "part2.step"],
        ...     clean=True,
        ...     tolerance=1e-3
        ... )
        >>> for shape, shape_type in shapes:
        ...     print(f"Shape type: {shape_type}")
    """

    def __init__(self):
        """Initialize geometry processor"""
        self.step_reader = STEPReader()
        self.classifier = ShapeClassifier()
        self.cleaner = GeometryCleaner()
        self.logger = logging.getLogger(__name__)

    def process(
        self,
        input_files: List[str],
        clean: bool = True,
        tolerance: float = DEFAULT_GEOMETRY_TOLERANCE
    ) -> List[Tuple[Any, str]]:
        """
        Process all geometry files

        Args:
            input_files: List of STEP file paths to process
            clean: Whether to clean geometry before classification
            tolerance: Tolerance for geometry cleaning (mm)

        Returns:
            List of (shape, shape_type) tuples

        Raises:
            GeometryProcessingError: If processing fails
            FileNotFoundError: If input file doesn't exist
            ValueError: If tolerance is out of valid range
        """
        # Validate inputs
        if not input_files:
            raise ValueError("No input files provided")

        if not (MIN_GEOMETRY_TOLERANCE <= tolerance <= MAX_GEOMETRY_TOLERANCE):
            raise ValueError(
                f"Tolerance {tolerance} out of valid range "
                f"[{MIN_GEOMETRY_TOLERANCE}, {MAX_GEOMETRY_TOLERANCE}]"
            )

        self.logger.info(
            f"Processing {len(input_files)} file(s) with clean={clean}, "
            f"tolerance={tolerance}"
        )

        results = []

        for file_path in input_files:
            try:
                shapes = self._process_file(file_path, clean, tolerance)
                results.extend(shapes)
            except Exception as e:
                error_msg = f"Failed to process {file_path}: {str(e)}"
                self.logger.error(error_msg)
                raise GeometryProcessingError(error_msg) from e

        self.logger.info(f"Processed {len(results)} shape(s) total")
        return results

    def _process_file(
        self,
        file_path: str,
        clean: bool,
        tolerance: float
    ) -> List[Tuple[Any, str]]:
        """
        Process a single STEP file

        Args:
            file_path: Path to STEP file
            clean: Whether to clean geometry
            tolerance: Cleaning tolerance

        Returns:
            List of (shape, shape_type) tuples
        """
        # Validate file exists
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Input file not found: {file_path}")

        self.logger.debug(f"Reading STEP file: {file_path}")

        # Read STEP file
        try:
            shapes = self.step_reader.read_file(str(file_path))
        except Exception as e:
            raise GeometryProcessingError(
                f"Failed to read STEP file {file_path}: {str(e)}"
            ) from e

        if not shapes:
            self.logger.warning(f"No shapes found in {file_path}")
            return []

        self.logger.debug(f"Found {len(shapes)} shape(s) in {file_path}")

        # Process each shape
        results = []
        for i, shape in enumerate(shapes):
            try:
                # Clean if enabled
                if clean:
                    shape = self._clean_shape(shape, tolerance)

                # Classify
                shape_type = self._classify_shape(shape)

                results.append((shape, shape_type))

                self.logger.debug(
                    f"Shape {i+1}/{len(shapes)}: type={shape_type}"
                )

            except Exception as e:
                self.logger.warning(
                    f"Failed to process shape {i+1} from {file_path}: {str(e)}"
                )
                # Continue with other shapes
                continue

        return results

    def _clean_shape(self, shape: Any, tolerance: float) -> Any:
        """
        Clean a single shape

        Args:
            shape: Input shape
            tolerance: Cleaning tolerance

        Returns:
            Cleaned shape
        """
        try:
            # Remove duplicate faces
            shape = self.cleaner.remove_duplicate_faces(shape, tolerance)

            # Heal surface
            shape = self.cleaner.heal_surface(shape, tolerance)

            return shape

        except Exception as e:
            self.logger.warning(f"Geometry cleaning failed: {str(e)}")
            # Return original shape if cleaning fails
            return shape

    def _classify_shape(self, shape: Any) -> str:
        """
        Classify a shape

        Args:
            shape: Input shape

        Returns:
            Shape type string ('solid', 'shell', or 'beam')
        """
        try:
            return self.classifier.classify(shape)
        except Exception as e:
            self.logger.warning(f"Shape classification failed: {str(e)}")
            # Default to 'solid' if classification fails
            return 'solid'

    def process_single_file(
        self,
        input_file: str,
        clean: bool = True,
        tolerance: float = DEFAULT_GEOMETRY_TOLERANCE
    ) -> List[Tuple[Any, str]]:
        """
        Convenience method to process a single file

        Args:
            input_file: Path to STEP file
            clean: Whether to clean geometry
            tolerance: Cleaning tolerance

        Returns:
            List of (shape, shape_type) tuples
        """
        return self.process([input_file], clean, tolerance)

    def get_statistics(self, results: List[Tuple[Any, str]]) -> dict:
        """
        Get statistics about processed shapes

        Args:
            results: List of (shape, shape_type) tuples from process()

        Returns:
            Dictionary with statistics
        """
        stats = {
            'total_shapes': len(results),
            'solid_count': 0,
            'shell_count': 0,
            'beam_count': 0,
            'unknown_count': 0
        }

        for shape, shape_type in results:
            if shape_type == 'solid':
                stats['solid_count'] += 1
            elif shape_type == 'shell':
                stats['shell_count'] += 1
            elif shape_type == 'beam':
                stats['beam_count'] += 1
            else:
                stats['unknown_count'] += 1

        return stats
