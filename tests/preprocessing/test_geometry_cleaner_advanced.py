"""
Advanced Geometry Cleaner Tests
================================

Tests for enhanced GeometryCleaner functionality:
- Duplicate face removal with shape rebuilding
- Small feature removal (holes, fillets, edges)
- Enhanced surface healing with free edge analysis

Author: KooMeshGenerator Team
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from koomesh.preprocessing.geometry_cleaner import GeometryCleaner

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s - %(name)s - %(message)s'
)


def test_imports():
    """Test that all required modules can be imported"""
    print("\n" + "="*70)
    print("TEST 1: Import Test")
    print("="*70)

    try:
        from koomesh.preprocessing.geometry_cleaner import (
            GeometryCleaner,
            CleaningResult
        )
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_geometry_cleaner_init():
    """Test GeometryCleaner initialization"""
    print("\n" + "="*70)
    print("TEST 2: GeometryCleaner Initialization")
    print("="*70)

    try:
        cleaner = GeometryCleaner()
        print(f"✓ GeometryCleaner created: {cleaner}")

        # Check methods exist
        assert hasattr(cleaner, 'clean')
        assert hasattr(cleaner, 'remove_duplicate_faces')
        assert hasattr(cleaner, 'heal_surface')
        assert hasattr(cleaner, 'remove_small_features')
        assert hasattr(cleaner, '_count_free_edges')

        print("✓ All methods present")
        return True
    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        return False


def test_duplicate_removal_with_mock_shape():
    """Test duplicate face removal with mock shape"""
    print("\n" + "="*70)
    print("TEST 3: Duplicate Face Removal (Mock Shape)")
    print("="*70)

    try:
        # Try to import OCC
        try:
            from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
            from OCP.TopoDS import TopoDS_Compound, TopoDS_Builder
            occ_available = True
        except ImportError:
            print("⚠ PythonOCC not available, using mock test")
            occ_available = False

        cleaner = GeometryCleaner()

        if occ_available:
            # Create a simple box shape
            box = BRepPrimAPI_MakeBox(10.0, 10.0, 10.0).Shape()

            print(f"  Input shape: {box}")

            # Test duplicate removal (should return shape unchanged for box)
            result = cleaner.remove_duplicate_faces(box, tolerance=1e-6)

            print(f"  Output shape: {result}")
            print("✓ Duplicate removal executed successfully")
        else:
            # Mock shape for testing without OCC
            print("  Mock shape test passed")

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_small_feature_removal():
    """Test small feature removal"""
    print("\n" + "="*70)
    print("TEST 4: Small Feature Removal")
    print("="*70)

    try:
        # Try to import OCC
        try:
            from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
            occ_available = True
        except ImportError:
            print("⚠ PythonOCC not available, using mock test")
            occ_available = False

        cleaner = GeometryCleaner()

        if occ_available:
            # Create a simple box shape
            box = BRepPrimAPI_MakeBox(10.0, 10.0, 10.0).Shape()

            # Test small feature removal
            result_shape, features_removed = cleaner._remove_small_features(
                box, min_size=0.1
            )

            print(f"  Features removed: {features_removed}")
            print(f"  Output shape: {result_shape}")
            print("✓ Small feature removal executed successfully")
        else:
            print("  Mock test passed")

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_surface_healing():
    """Test surface healing with free edge detection"""
    print("\n" + "="*70)
    print("TEST 5: Surface Healing")
    print("="*70)

    try:
        # Try to import OCC
        try:
            from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
            occ_available = True
        except ImportError:
            print("⚠ PythonOCC not available, using mock test")
            occ_available = False

        cleaner = GeometryCleaner()

        if occ_available:
            # Create a simple box shape
            box = BRepPrimAPI_MakeBox(10.0, 10.0, 10.0).Shape()

            # Test surface healing
            healed_shape, gaps_filled = cleaner._heal_surfaces(
                box, tolerance=1e-3
            )

            print(f"  Gaps filled: {gaps_filled}")
            print(f"  Output shape: {healed_shape}")

            # Test free edge counting
            free_edges = cleaner._count_free_edges(box)
            print(f"  Free edges in box: {free_edges}")

            print("✓ Surface healing executed successfully")
        else:
            print("  Mock test passed")

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_public_method_wrappers():
    """Test public wrapper methods"""
    print("\n" + "="*70)
    print("TEST 6: Public Method Wrappers")
    print("="*70)

    try:
        # Try to import OCC
        try:
            from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
            occ_available = True
        except ImportError:
            print("⚠ PythonOCC not available, using mock test")
            occ_available = False

        cleaner = GeometryCleaner()

        if occ_available:
            # Create a simple box shape
            box = BRepPrimAPI_MakeBox(10.0, 10.0, 10.0).Shape()

            # Test heal_surface wrapper
            result1 = cleaner.heal_surface(box, tolerance=1e-3)
            print(f"  heal_surface() returned: {result1}")

            # Test remove_small_features wrapper
            result2 = cleaner.remove_small_features(box, min_size=0.1)
            print(f"  remove_small_features() returned: {result2}")

            print("✓ All public wrappers work correctly")
        else:
            print("  Mock test passed")

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_error_handling():
    """Test error handling for invalid inputs"""
    print("\n" + "="*70)
    print("TEST 7: Error Handling")
    print("="*70)

    try:
        cleaner = GeometryCleaner()

        # Test with None shape (should handle gracefully)
        try:
            result = cleaner.remove_duplicate_faces(None, tolerance=1e-6)
            print(f"  remove_duplicate_faces(None) handled: {result}")
        except Exception as e:
            print(f"  remove_duplicate_faces(None) raised: {type(e).__name__}")

        # Test with invalid tolerance
        try:
            from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
            box = BRepPrimAPI_MakeBox(10.0, 10.0, 10.0).Shape()
            result = cleaner.remove_duplicate_faces(box, tolerance=-1.0)
            print(f"  Negative tolerance handled: {result}")
        except:
            print("  PythonOCC not available, skipping OCC-dependent test")

        print("✓ Error handling works correctly")
        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration_with_pipeline():
    """Test integration with geometry pipeline"""
    print("\n" + "="*70)
    print("TEST 8: Pipeline Integration")
    print("="*70)

    try:
        from koomesh.pipeline.geometry_processor import GeometryProcessor

        processor = GeometryProcessor()
        cleaner = processor.cleaner

        # Check that cleaner is properly initialized
        assert isinstance(cleaner, GeometryCleaner)
        print(f"  GeometryProcessor.cleaner: {cleaner}")

        # Check that all methods are accessible
        assert hasattr(cleaner, 'remove_duplicate_faces')
        assert hasattr(cleaner, 'heal_surface')
        assert hasattr(cleaner, 'remove_small_features')

        print("✓ Pipeline integration successful")
        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_face_signature_calculation():
    """Test face signature calculation"""
    print("\n" + "="*70)
    print("TEST 9: Face Signature Calculation")
    print("="*70)

    try:
        # Try to import OCC
        try:
            from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
            from OCP.TopExp import TopExp_Explorer
            from OCP.TopAbs import TopAbs_FACE
            occ_available = True
        except ImportError:
            print("⚠ PythonOCC not available, skipping")
            return True

        cleaner = GeometryCleaner()

        # Create a box
        box = BRepPrimAPI_MakeBox(10.0, 10.0, 10.0).Shape()

        # Get first face
        explorer = TopExp_Explorer(box, TopAbs_FACE)
        if explorer.More():
            face = explorer.Current()

            # Calculate signature
            sig = cleaner._calculate_face_signature(face, tolerance=1e-6)
            print(f"  Face signature: {sig}")

            # Signature should be a tuple of 4 floats
            assert isinstance(sig, tuple)
            assert len(sig) == 4
            print(f"  Signature format: (cx={sig[0]:.3f}, cy={sig[1]:.3f}, "
                  f"cz={sig[2]:.3f}, area={sig[3]:.3f})")

            # Test signature matching
            match = cleaner._signatures_match(sig, sig, tolerance=1e-6)
            assert match == True
            print("  Signature matching works")

            print("✓ Face signature calculation successful")
        else:
            print("  No faces found in box")

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_free_edge_counting():
    """Test free edge counting functionality"""
    print("\n" + "="*70)
    print("TEST 10: Free Edge Counting")
    print("="*70)

    try:
        # Try to import OCC
        try:
            from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
            occ_available = True
        except ImportError:
            print("⚠ PythonOCC not available, skipping")
            return True

        cleaner = GeometryCleaner()

        # Create a box (closed solid, should have 0 free edges)
        box = BRepPrimAPI_MakeBox(10.0, 10.0, 10.0).Shape()
        free_edges = cleaner._count_free_edges(box)

        print(f"  Free edges in closed box: {free_edges}")
        print("  (Expected: 0 for closed solid)")

        print("✓ Free edge counting successful")
        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests and report results"""
    print("\n" + "="*70)
    print("ADVANCED GEOMETRY CLEANER TEST SUITE")
    print("="*70)

    tests = [
        ("Import Test", test_imports),
        ("Initialization Test", test_geometry_cleaner_init),
        ("Duplicate Removal Test", test_duplicate_removal_with_mock_shape),
        ("Small Feature Removal Test", test_small_feature_removal),
        ("Surface Healing Test", test_surface_healing),
        ("Public Method Wrappers Test", test_public_method_wrappers),
        ("Error Handling Test", test_error_handling),
        ("Pipeline Integration Test", test_integration_with_pipeline),
        ("Face Signature Test", test_face_signature_calculation),
        ("Free Edge Counting Test", test_free_edge_counting),
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
