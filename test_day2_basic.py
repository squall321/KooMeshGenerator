#!/usr/bin/env python
"""
Day 2 Basic Integration Test
=============================

Tests the Day 2 Geometry Processing implementation.
"""

import sys
import traceback
from pathlib import Path


def test_geometry_processor_import():
    """Test that GeometryProcessor can be imported"""
    print("Test 1: Importing GeometryProcessor...")
    try:
        from koomesh.pipeline.geometry_processor import (
            GeometryProcessor,
            GeometryProcessingError
        )
        print("✓ GeometryProcessor imported successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to import GeometryProcessor: {e}")
        traceback.print_exc()
        return False


def test_geometry_processor_init():
    """Test GeometryProcessor initialization"""
    print("\nTest 2: Initializing GeometryProcessor...")
    try:
        from koomesh.pipeline.geometry_processor import GeometryProcessor

        processor = GeometryProcessor()
        assert processor.step_reader is not None
        assert processor.classifier is not None
        assert processor.cleaner is not None

        print("✓ GeometryProcessor initialized successfully")
        print(f"  - step_reader: {type(processor.step_reader).__name__}")
        print(f"  - classifier: {type(processor.classifier).__name__}")
        print(f"  - cleaner: {type(processor.cleaner).__name__}")
        return True
    except Exception as e:
        print(f"✗ Failed to initialize GeometryProcessor: {e}")
        traceback.print_exc()
        return False


def test_geometry_processor_validation():
    """Test GeometryProcessor input validation"""
    print("\nTest 3: Testing input validation...")
    try:
        from koomesh.pipeline.geometry_processor import GeometryProcessor

        processor = GeometryProcessor()

        # Test empty file list
        try:
            processor.process(input_files=[])
            print("✗ Should have raised ValueError for empty file list")
            return False
        except ValueError as e:
            if "No input files" in str(e):
                print("✓ Correctly validates empty file list")
            else:
                print(f"✗ Wrong error message: {e}")
                return False

        # Test invalid tolerance
        try:
            processor.process(input_files=["test.step"], tolerance=100.0)
            print("✗ Should have raised ValueError for invalid tolerance")
            return False
        except ValueError as e:
            if "out of valid range" in str(e):
                print("✓ Correctly validates tolerance range")
            else:
                print(f"✗ Wrong error message: {e}")
                return False

        return True
    except Exception as e:
        print(f"✗ Failed validation tests: {e}")
        traceback.print_exc()
        return False


def test_geometry_processor_statistics():
    """Test GeometryProcessor statistics"""
    print("\nTest 4: Testing statistics...")
    try:
        from koomesh.pipeline.geometry_processor import GeometryProcessor
        from unittest.mock import Mock

        processor = GeometryProcessor()

        # Test empty statistics
        stats = processor.get_statistics([])
        assert stats['total_shapes'] == 0
        assert stats['solid_count'] == 0
        print("✓ Empty statistics correct")

        # Test mixed statistics
        mock_shape = Mock()
        results = [
            (mock_shape, 'solid'),
            (mock_shape, 'solid'),
            (mock_shape, 'shell'),
            (mock_shape, 'beam'),
        ]
        stats = processor.get_statistics(results)
        assert stats['total_shapes'] == 4
        assert stats['solid_count'] == 2
        assert stats['shell_count'] == 1
        assert stats['beam_count'] == 1
        print("✓ Mixed statistics correct")
        print(f"  - Total: {stats['total_shapes']}")
        print(f"  - Solids: {stats['solid_count']}")
        print(f"  - Shells: {stats['shell_count']}")
        print(f"  - Beams: {stats['beam_count']}")

        return True
    except Exception as e:
        print(f"✗ Failed statistics tests: {e}")
        traceback.print_exc()
        return False


def test_geometry_cleaner_enhancements():
    """Test GeometryCleaner new methods"""
    print("\nTest 5: Testing GeometryCleaner enhancements...")
    try:
        from koomesh.preprocessing.geometry_cleaner import GeometryCleaner
        from unittest.mock import Mock

        cleaner = GeometryCleaner()

        # Test that new methods exist
        assert hasattr(cleaner, 'remove_duplicate_faces')
        assert hasattr(cleaner, 'heal_surface')
        assert hasattr(cleaner, 'remove_small_features')
        print("✓ All new methods exist")

        # Test that methods can be called (with mock shape)
        mock_shape = Mock()

        # These should not crash, even if they return the original shape
        result1 = cleaner.remove_duplicate_faces(mock_shape, tolerance=1e-3)
        print("✓ remove_duplicate_faces() callable")

        result2 = cleaner.heal_surface(mock_shape, tolerance=1e-3)
        print("✓ heal_surface() callable")

        result3 = cleaner.remove_small_features(mock_shape, min_size=0.1)
        print("✓ remove_small_features() callable")

        return True
    except Exception as e:
        print(f"✗ Failed GeometryCleaner tests: {e}")
        traceback.print_exc()
        return False


def test_pipeline_geometry_stage():
    """Test MeshGenerationPipeline._process_geometry() implementation"""
    print("\nTest 6: Testing pipeline geometry stage...")
    try:
        from koomesh.pipeline.mesh_pipeline import (
            MeshGenerationPipeline,
            PipelineConfig
        )
        from pathlib import Path
        import tempfile

        # Create a temporary test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.step', delete=False) as f:
            temp_file = f.name
            f.write("dummy content")

        try:
            # Create pipeline config
            config = PipelineConfig(
                input_files=[temp_file],
                output_file="output.k",
                clean_geometry=False  # Disable to avoid needing real STEP files
            )

            pipeline = MeshGenerationPipeline(config)

            # Check that _process_geometry exists and is no longer NotImplementedError
            assert hasattr(pipeline, '_process_geometry')
            print("✓ _process_geometry() method exists")

            # Try to call it (will fail because temp file is not a real STEP file)
            # but it should not raise NotImplementedError
            try:
                pipeline._process_geometry()
                # If it succeeds, great!
                print("✓ _process_geometry() executed (unexpected success)")
            except NotImplementedError:
                print("✗ _process_geometry() still raises NotImplementedError!")
                return False
            except Exception as e:
                # Expected to fail on actual processing, but not NotImplementedError
                if "NotImplemented" not in str(e):
                    print(f"✓ _process_geometry() implemented (failed on: {type(e).__name__})")
                else:
                    print(f"✗ Still not implemented: {e}")
                    return False

        finally:
            # Clean up temp file
            Path(temp_file).unlink(missing_ok=True)

        return True
    except Exception as e:
        print(f"✗ Failed pipeline geometry stage test: {e}")
        traceback.print_exc()
        return False


def test_pipeline_exports():
    """Test that all exports are available"""
    print("\nTest 7: Testing pipeline module exports...")
    try:
        from koomesh.pipeline import (
            GeometryProcessor,
            GeometryProcessingError,
            MeshGenerationPipeline,
            PipelineConfig,
            ProgressTracker,
        )
        print("✓ GeometryProcessor exported from pipeline module")
        print("✓ GeometryProcessingError exported from pipeline module")
        print("✓ All pipeline exports available")
        return True
    except Exception as e:
        print(f"✗ Failed to import pipeline exports: {e}")
        traceback.print_exc()
        return False


def test_constants_additions():
    """Test that new constants are defined"""
    print("\nTest 8: Testing new constants...")
    try:
        from koomesh.pipeline.constants import (
            DEFAULT_GEOMETRY_TOLERANCE,
            MIN_GEOMETRY_TOLERANCE,
            MAX_GEOMETRY_TOLERANCE,
        )
        print(f"✓ DEFAULT_GEOMETRY_TOLERANCE = {DEFAULT_GEOMETRY_TOLERANCE}")
        print(f"✓ MIN_GEOMETRY_TOLERANCE = {MIN_GEOMETRY_TOLERANCE}")
        print(f"✓ MAX_GEOMETRY_TOLERANCE = {MAX_GEOMETRY_TOLERANCE}")

        # Validate ranges
        assert MIN_GEOMETRY_TOLERANCE < DEFAULT_GEOMETRY_TOLERANCE < MAX_GEOMETRY_TOLERANCE
        print("✓ Constants have valid ranges")

        return True
    except Exception as e:
        print(f"✗ Failed constants test: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("="*70)
    print("DAY 2 BASIC INTEGRATION TEST")
    print("="*70)

    tests = [
        test_geometry_processor_import,
        test_geometry_processor_init,
        test_geometry_processor_validation,
        test_geometry_processor_statistics,
        test_geometry_cleaner_enhancements,
        test_pipeline_geometry_stage,
        test_pipeline_exports,
        test_constants_additions,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n✗ Test crashed: {e}")
            traceback.print_exc()
            results.append(False)

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("\n✓ ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n✗ {total - passed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
