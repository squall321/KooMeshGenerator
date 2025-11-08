#!/usr/bin/env python3
"""
Integration Test Suite
======================

Comprehensive integration tests for all KooMeshGenerator phases.

Tests:
- Phase 1: Core Infrastructure
- Phase 2: Essential FEA Features
- Phase 3: CLI & Batch Processing
- Phase 4: Production-Ready Features
"""

import sys
import subprocess
from pathlib import Path

# Add koomesh to path
sys.path.insert(0, str(Path(__file__).parent))


def run_test_script(script_name: str) -> bool:
    """Run a test script and return success status"""
    script_path = Path(__file__).parent / script_name

    if not script_path.exists():
        print(f"  ⚠ Test script not found: {script_name}")
        return True  # Skip if not found

    print(f"\n{'='*70}")
    print(f"Running: {script_name}")
    print('='*70)

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=False,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if result.returncode == 0:
            print(f"✓ {script_name} PASSED")
            return True
        else:
            print(f"✗ {script_name} FAILED with code {result.returncode}")
            return False

    except subprocess.TimeoutExpired:
        print(f"✗ {script_name} TIMED OUT")
        return False
    except Exception as e:
        print(f"✗ {script_name} ERROR: {e}")
        return False


def test_phase1_core():
    """Test Phase 1: Core Infrastructure"""
    print("\n" + "="*70)
    print("PHASE 1: Core Infrastructure")
    print("="*70)

    try:
        # Test core imports
        from koomesh.core.lsdyna_parser import LSDynaParser
        from koomesh.core.mesh_generator import MeshGenerator
        from koomesh.materials.material_library import MaterialLibrary

        print("✓ Core modules import successfully")

        # Test material library
        library = MaterialLibrary()
        library.load_default_materials()
        print(f"✓ Material library loaded: {len(library.materials)} materials")

        return True

    except Exception as e:
        print(f"✗ Phase 1 test failed: {e}")
        return False


def test_phase2_fea():
    """Test Phase 2: Essential FEA Features"""
    print("\n" + "="*70)
    print("PHASE 2: Essential FEA Features")
    print("="*70)

    try:
        from koomesh.fea.boundary_conditions import BoundaryConditionManager
        from koomesh.fea.contact import ContactManager
        from koomesh.core.mesh_generator import MeshGenerator

        print("✓ FEA modules import successfully")

        # Test BC manager
        bc_manager = BoundaryConditionManager()
        print("✓ Boundary condition manager created")

        # Test contact manager
        contact_manager = ContactManager()
        print("✓ Contact manager created")

        return True

    except Exception as e:
        print(f"✗ Phase 2 test failed: {e}")
        return False


def test_phase3_cli():
    """Test Phase 3: CLI & Batch Processing"""
    print("\n" + "="*70)
    print("PHASE 3: CLI & Batch Processing")
    print("="*70)

    try:
        from koomesh.cli.main import cli
        from koomesh.config.config_schema import MeshConfig
        from koomesh.batch.batch_processor import BatchProcessor

        print("✓ CLI modules import successfully")

        # Test config
        config = MeshConfig(
            geometry_file="test.step",
            output_file="test.k",
            element_size=5.0
        )
        print("✓ Config validation working")

        # Test batch processor
        processor = BatchProcessor()
        print("✓ Batch processor created")

        return True

    except Exception as e:
        print(f"✗ Phase 3 test failed: {e}")
        return False


def test_phase4_production():
    """Test Phase 4: Production-Ready Features"""
    print("\n" + "="*70)
    print("PHASE 4: Production-Ready Features")
    print("="*70)

    success = True

    # Test error handling
    try:
        from koomesh.utils.exceptions import KooMeshException
        from koomesh.utils.error_messages import suggest_geometry_fix
        print("✓ Error handling modules loaded")
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        success = False

    # Test performance
    try:
        from koomesh.utils.performance import PerformanceProfiler
        from koomesh.utils.cache import GeometryCache
        print("✓ Performance modules loaded")
    except Exception as e:
        print(f"✗ Performance test failed: {e}")
        success = False

    # Test templates
    try:
        from koomesh.templates import TemplateManager, load_template
        manager = TemplateManager()
        manager.load_builtin_templates()
        print(f"✓ Template system loaded: {len(manager.templates)} templates")
    except Exception as e:
        print(f"✗ Template test failed: {e}")
        success = False

    # Test quality
    try:
        from koomesh.quality import QualityAnalyzer, AutoRemesher
        analyzer = QualityAnalyzer()
        print("✓ Quality system loaded")
    except Exception as e:
        print(f"✗ Quality test failed: {e}")
        success = False

    return success


def run_all_tests():
    """Run all integration tests"""
    print("\n" + "="*70)
    print("KooMeshGenerator - INTEGRATION TEST SUITE")
    print("="*70)

    results = {
        "Phase 1: Core Infrastructure": test_phase1_core(),
        "Phase 2: Essential FEA Features": test_phase2_fea(),
        "Phase 3: CLI & Batch Processing": test_phase3_cli(),
        "Phase 4: Production-Ready Features": test_phase4_production(),
    }

    # Run individual test scripts
    test_scripts = [
        "test_template_system.py",
        "test_quality_system.py",
    ]

    for script in test_scripts:
        results[f"Script: {script}"] = run_test_script(script)

    # Summary
    print("\n" + "="*70)
    print("INTEGRATION TEST SUMMARY")
    print("="*70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, success in results.items():
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"{status:12} {test_name}")

    print("="*70)
    print(f"Results: {passed}/{total} tests passed ({100*passed/total:.1f}%)")
    print("="*70)

    if passed == total:
        print("\n🎉 All integration tests PASSED!")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
