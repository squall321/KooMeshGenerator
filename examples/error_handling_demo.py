#!/usr/bin/env python3
"""
Error Handling and Logging Demonstration
=========================================

This script demonstrates the enhanced error handling and logging
system in KooMeshGenerator.

Features demonstrated:
- Custom exception classes with helpful suggestions
- Structured logging with colors
- Error messages with context
- User-friendly error display
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from koomesh.utils.exceptions import (
    FileNotFoundError,
    InvalidGeometryError,
    MeshGenerationError,
    MeshQualityError,
    ConfigValidationError,
    DependencyError,
)
from koomesh.utils.error_messages import (
    format_error_message,
    suggest_geometry_fix,
    suggest_meshing_fix,
    ErrorDisplay,
)
from koomesh.utils.logger import setup_logger, LogTimer


def demo_custom_exceptions():
    """Demonstrate custom exception classes"""
    print("\n" + "="*70)
    print("DEMO 1: Custom Exception Classes")
    print("="*70 + "\n")

    # Example 1: File not found
    try:
        raise FileNotFoundError(Path("/nonexistent/file.step"))
    except FileNotFoundError as e:
        print(str(e))
        print()

    # Example 2: Invalid geometry
    try:
        raise InvalidGeometryError(reason="Self-intersecting faces detected")
    except InvalidGeometryError as e:
        print(str(e))
        print()

    # Example 3: Mesh quality error
    try:
        raise MeshQualityError(
            metric="aspect_ratio",
            value=15.2,
            threshold=10.0
        )
    except MeshQualityError as e:
        print(str(e))
        print()

    # Example 4: Dependency error
    try:
        raise DependencyError("PythonOCC", reason="Required for STEP file reading")
    except DependencyError as e:
        print(str(e))
        print()


def demo_error_messages():
    """Demonstrate error message templates"""
    print("\n" + "="*70)
    print("DEMO 2: Error Message Templates")
    print("="*70 + "\n")

    # File not found message
    msg1 = format_error_message("file_not_found", filepath="/path/to/file.step")
    print(msg1)
    print()

    # Invalid geometry message
    msg2 = format_error_message("invalid_geometry")
    print(msg2)
    print()

    # Meshing failed message
    msg3 = format_error_message("meshing_failed")
    print(msg3)
    print()


def demo_suggestions():
    """Demonstrate context-aware suggestions"""
    print("\n" + "="*70)
    print("DEMO 3: Context-Aware Suggestions")
    print("="*70 + "\n")

    # Geometry issue suggestions
    print("Suggestions for self-intersection:")
    for suggestion in suggest_geometry_fix("self_intersection"):
        print(f"  • {suggestion}")
    print()

    # Meshing issue suggestions
    print("Suggestions for geometry_invalid:")
    for suggestion in suggest_meshing_fix("geometry_invalid"):
        print(f"  • {suggestion}")
    print()

    # Complex geometry suggestions
    print("Suggestions for mesh_size_too_small:")
    for suggestion in suggest_meshing_fix("mesh_size_too_small"):
        print(f"  • {suggestion}")
    print()


def demo_error_display():
    """Demonstrate user-friendly error display"""
    print("\n" + "="*70)
    print("DEMO 4: User-Friendly Error Display")
    print("="*70 + "\n")

    # File error
    print("1. File Error:")
    ErrorDisplay.print_file_error(Path("/nonexistent.step"))
    print()

    # Geometry error
    print("2. Geometry Error:")
    ErrorDisplay.print_geometry_error("self_intersection")
    print()

    # Meshing error
    print("3. Meshing Error:")
    ErrorDisplay.print_meshing_error("geometry_invalid")
    print()

    # Quality warning
    print("4. Quality Warning:")
    ErrorDisplay.print_quality_warning("aspect_ratio", 15.2, 10.0)
    print()


def demo_logging():
    """Demonstrate logging features"""
    print("\n" + "="*70)
    print("DEMO 5: Enhanced Logging")
    print("="*70 + "\n")

    # Setup logger with colors
    logger = setup_logger('demo', level='DEBUG', file_output=False)

    logger.debug("This is a DEBUG message (grey)")
    logger.info("This is an INFO message (green)")
    logger.warning("This is a WARNING message (yellow)")
    logger.error("This is an ERROR message (red)")

    print()

    # Demonstrate LogTimer
    print("Using LogTimer context manager:")
    with LogTimer(logger, "Processing large file"):
        import time
        time.sleep(0.5)  # Simulate work

    print()


def demo_complete_workflow():
    """Demonstrate complete error handling workflow"""
    print("\n" + "="*70)
    print("DEMO 6: Complete Workflow with Error Handling")
    print("="*70 + "\n")

    logger = setup_logger('workflow', level='INFO', file_output=False)

    def process_geometry(filename: str):
        """Simulate geometry processing with error handling"""
        from koomesh.preprocessing.geometry_analyzer import GeometryAnalyzer

        logger.info(f"Processing {filename}...")

        try:
            analyzer = GeometryAnalyzer()

            # This will raise FileNotFoundError if file doesn't exist
            info = analyzer.analyze(filename)

            logger.info(f"✓ Analysis complete: {info.num_faces} faces")

        except FileNotFoundError as e:
            logger.error(f"✗ File error: {e}")
            print("\n" + str(e))
        except DependencyError as e:
            logger.error(f"✗ Dependency error: {e}")
            print("\n" + str(e))
        except Exception as e:
            logger.error(f"✗ Unexpected error: {e}")
            import traceback
            traceback.print_exc()

    # Try to process non-existent file (will fail gracefully)
    process_geometry("/nonexistent_file.step")

    print()


def main():
    """Run all demonstrations"""
    print("\n" + "#"*70)
    print("# KooMeshGenerator - Error Handling & Logging Demo")
    print("#"*70)

    demo_custom_exceptions()
    demo_error_messages()
    demo_suggestions()
    demo_error_display()
    demo_logging()
    demo_complete_workflow()

    print("\n" + "#"*70)
    print("# Demo Complete!")
    print("#"*70 + "\n")

    print("Key Features:")
    print("  ✓ Custom exception classes with error codes")
    print("  ✓ Helpful suggestions for common errors")
    print("  ✓ Context-aware error messages")
    print("  ✓ Color-coded console logging")
    print("  ✓ User-friendly error display")
    print("  ✓ Structured error handling")
    print()


if __name__ == "__main__":
    main()
