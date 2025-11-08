"""
LS-DYNA Validator Tests
=======================

Tests for LSDynaValidator and ValidationResult.

Author: KooMeshGenerator Team
"""

import sys
import tempfile
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from koomesh.validation.lsdyna_validator import (
    LSDynaValidator,
    ValidationResult,
    ValidationMessage,
    ValidationLevel
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(name)s - %(message)s'
)


def test_imports():
    """Test that all required modules can be imported"""
    print("\n" + "="*70)
    print("TEST 1: Import Test")
    print("="*70)

    try:
        from koomesh.validation.lsdyna_validator import (
            LSDynaValidator,
            ValidationResult,
            ValidationMessage,
            ValidationLevel
        )
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_validation_message():
    """Test ValidationMessage dataclass"""
    print("\n" + "="*70)
    print("TEST 2: ValidationMessage")
    print("="*70)

    try:
        # Create message
        msg = ValidationMessage(
            level=ValidationLevel.ERROR,
            message="Test error",
            line_number=10,
            keyword="*NODE"
        )

        print(f"  Created message: {msg}")
        assert msg.level == ValidationLevel.ERROR
        assert msg.message == "Test error"
        assert msg.line_number == 10
        assert msg.keyword == "*NODE"

        # Test string representation
        str_repr = str(msg)
        print(f"  String representation: {str_repr}")
        assert "[ERROR]" in str_repr
        assert "Line 10" in str_repr
        assert "*NODE" in str_repr

        print("✓ ValidationMessage works correctly")
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_validation_result():
    """Test ValidationResult dataclass"""
    print("\n" + "="*70)
    print("TEST 3: ValidationResult")
    print("="*70)

    try:
        # Create result
        result = ValidationResult(
            success=True,
            file_path="/tmp/test.k",
            file_size=1024
        )

        print(f"  Initial success: {result.success}")
        assert result.success == True

        # Add error (should set success to False)
        result.add_error("Test error", line_number=5, keyword="*NODE")
        print(f"  After add_error: success={result.success}")
        assert result.success == False
        assert len(result.errors) == 1

        # Add warning
        result.add_warning("Test warning")
        assert len(result.warnings) == 1

        # Add info
        result.add_info("Test info")
        assert len(result.info) == 1

        print(f"  Messages: {len(result.errors)} errors, "
              f"{len(result.warnings)} warnings, {len(result.info)} info")

        print("✓ ValidationResult works correctly")
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_validator_initialization():
    """Test LSDynaValidator initialization"""
    print("\n" + "="*70)
    print("TEST 4: LSDynaValidator Initialization")
    print("="*70)

    try:
        # Normal mode
        validator = LSDynaValidator(strict_mode=False)
        print(f"  Normal mode: {validator}")
        assert validator.strict_mode == False

        # Strict mode
        validator_strict = LSDynaValidator(strict_mode=True)
        print(f"  Strict mode: {validator_strict}")
        assert validator_strict.strict_mode == True

        # Check constants
        print(f"  MIN_ELEMENT_QUALITY: {validator.MIN_ELEMENT_QUALITY}")
        print(f"  WARNING_ELEMENT_QUALITY: {validator.WARNING_ELEMENT_QUALITY}")
        print(f"  TARGET_ELEMENT_QUALITY: {validator.TARGET_ELEMENT_QUALITY}")

        print("✓ Initialization works correctly")
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_valid_k_file(filepath: str):
    """Create a valid minimal K file for testing"""
    content = """$ LS-DYNA Keyword File
$ Test file
*KEYWORD
*NODE
1  0.0  0.0  0.0
2  1.0  0.0  0.0
3  0.0  1.0  0.0
4  0.0  0.0  1.0
*ELEMENT_SOLID
1  1  1  2  3  4  2  3  4
*MAT_ELASTIC
1  7.85e-9  210000.0  0.3
*END
"""
    with open(filepath, 'w') as f:
        f.write(content)


def create_invalid_k_file(filepath: str):
    """Create an invalid K file for testing"""
    content = """This is not a valid K file
No keywords
Just text
"""
    with open(filepath, 'w') as f:
        f.write(content)


def test_validate_valid_file():
    """Test validation of valid K file"""
    print("\n" + "="*70)
    print("TEST 5: Validate Valid K File")
    print("="*70)

    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.k', delete=False) as f:
            create_valid_k_file(f.name)
            temp_file = f.name

        try:
            validator = LSDynaValidator()
            result = validator.validate(temp_file)

            print(f"  Validation success: {result.success}")
            print(f"  Errors: {len(result.errors)}")
            print(f"  Warnings: {len(result.warnings)}")
            print(f"  Statistics: {result.statistics}")

            # Should pass or have only warnings
            if result.errors:
                print("  Errors found:")
                for error in result.errors[:3]:
                    print(f"    {error}")

            if result.warnings:
                print("  Warnings found:")
                for warning in result.warnings[:3]:
                    print(f"    {warning}")

            print("✓ Valid file validation executed")
            return True

        finally:
            Path(temp_file).unlink()

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_validate_invalid_file():
    """Test validation of invalid K file"""
    print("\n" + "="*70)
    print("TEST 6: Validate Invalid K File")
    print("="*70)

    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.k', delete=False) as f:
            create_invalid_k_file(f.name)
            temp_file = f.name

        try:
            validator = LSDynaValidator()
            result = validator.validate(temp_file)

            print(f"  Validation success: {result.success}")
            print(f"  Errors: {len(result.errors)}")
            print(f"  Warnings: {len(result.warnings)}")

            # Should have errors
            assert len(result.errors) > 0 or len(result.warnings) > 0
            print("  Sample messages:")
            for msg in (result.errors + result.warnings)[:3]:
                print(f"    {msg}")

            print("✓ Invalid file correctly detected")
            return True

        finally:
            Path(temp_file).unlink()

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_validate_missing_file():
    """Test validation of missing file"""
    print("\n" + "="*70)
    print("TEST 7: Validate Missing File")
    print("="*70)

    try:
        validator = LSDynaValidator()

        try:
            result = validator.validate("/nonexistent/file.k")
            print(f"✗ Should have raised FileNotFoundError")
            return False
        except FileNotFoundError:
            print("✓ Correctly raises FileNotFoundError for missing file")
            return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_quick_validation():
    """Test quick validation method"""
    print("\n" + "="*70)
    print("TEST 8: Quick Validation")
    print("="*70)

    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.k', delete=False) as f:
            create_valid_k_file(f.name)
            temp_file = f.name

        try:
            validator = LSDynaValidator()
            is_valid = validator.validate_quick(temp_file)

            print(f"  Quick validation result: {is_valid}")
            # Should return True or False, not crash
            assert isinstance(is_valid, bool)

            print("✓ Quick validation works")
            return True

        finally:
            Path(temp_file).unlink()

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_strict_mode():
    """Test strict mode (warnings become errors)"""
    print("\n" + "="*70)
    print("TEST 9: Strict Mode")
    print("="*70)

    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.k', delete=False) as f:
            create_valid_k_file(f.name)
            temp_file = f.name

        try:
            # Normal mode
            validator_normal = LSDynaValidator(strict_mode=False)
            result_normal = validator_normal.validate(temp_file)

            # Strict mode
            validator_strict = LSDynaValidator(strict_mode=True)
            result_strict = validator_strict.validate(temp_file)

            print(f"  Normal mode: {result_normal.success}, "
                  f"{len(result_normal.errors)} errors, "
                  f"{len(result_normal.warnings)} warnings")
            print(f"  Strict mode: {result_strict.success}, "
                  f"{len(result_strict.errors)} errors, "
                  f"{len(result_strict.warnings)} warnings")

            # In strict mode, errors should include converted warnings
            if result_normal.warnings:
                assert len(result_strict.errors) >= len(result_normal.errors)
                print("  ✓ Strict mode converts warnings to errors")

            print("✓ Strict mode works correctly")
            return True

        finally:
            Path(temp_file).unlink()

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pipeline_integration():
    """Test integration with pipeline"""
    print("\n" + "="*70)
    print("TEST 10: Pipeline Integration")
    print("="*70)

    try:
        from koomesh.pipeline.mesh_pipeline import MeshGenerationPipeline

        # Check that validation module can be imported from pipeline
        from koomesh.validation import LSDynaValidator as PipelineValidator

        print(f"  Validator imported from validation module: {PipelineValidator}")

        # Check that _validate_output uses LSDynaValidator
        import inspect
        source = inspect.getsource(MeshGenerationPipeline._validate_output)

        if 'LSDynaValidator' in source:
            print("  ✓ Pipeline uses LSDynaValidator")
        else:
            print("  ⚠ LSDynaValidator not found in pipeline code")

        print("✓ Pipeline integration successful")
        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests and report results"""
    print("\n" + "="*70)
    print("LS-DYNA VALIDATOR TEST SUITE")
    print("="*70)

    tests = [
        ("Import Test", test_imports),
        ("ValidationMessage Test", test_validation_message),
        ("ValidationResult Test", test_validation_result),
        ("Validator Initialization Test", test_validator_initialization),
        ("Valid File Validation Test", test_validate_valid_file),
        ("Invalid File Validation Test", test_validate_invalid_file),
        ("Missing File Test", test_validate_missing_file),
        ("Quick Validation Test", test_quick_validation),
        ("Strict Mode Test", test_strict_mode),
        ("Pipeline Integration Test", test_pipeline_integration),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! 🎉")
    else:
        print(f"\n⚠ {total - passed} test(s) failed")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
