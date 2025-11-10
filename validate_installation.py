#!/usr/bin/env python3
"""
Quick validation script for KooMeshGenerator installation.
Run this after installing to verify everything is working.
"""

import sys
import importlib.util

def check_module(module_name, description=""):
    """Check if a module can be imported."""
    try:
        spec = importlib.util.find_spec(module_name)
        if spec is not None:
            print(f"✓ {module_name:30s} - OK {description}")
            return True
        else:
            print(f"✗ {module_name:30s} - NOT FOUND {description}")
            return False
    except Exception as e:
        print(f"✗ {module_name:30s} - ERROR: {e}")
        return False

def main():
    print("=" * 70)
    print("KooMeshGenerator Installation Validation")
    print("=" * 70)
    print()
    
    # Check core dependencies
    print("Core Dependencies:")
    print("-" * 70)
    deps = {
        'numpy': '(required - scientific computing)',
        'scipy': '(required - scientific library)',
        'click': '(required - CLI framework)',
        'yaml': '(required - config files)',
    }
    
    core_ok = True
    for dep, desc in deps.items():
        if not check_module(dep, desc):
            core_ok = False
    print()
    
    # Check koomesh package
    print("KooMesh Package:")
    print("-" * 70)
    
    # Try to import koomesh
    sys.path.insert(0, '.')
    
    try:
        import koomesh
        print(f"✓ koomesh package found")
        print(f"  Version: {koomesh.__version__}")
        print(f"  Author: {koomesh.__author__}")
        print()
    except Exception as e:
        print(f"✗ Failed to import koomesh: {e}")
        core_ok = False
        print()
    
    # Check koomesh modules
    print("KooMesh Modules:")
    print("-" * 70)
    
    modules = [
        ('koomesh.utils', 'Utility functions'),
        ('koomesh.utils.config_loader', 'Config file loader'),
        ('koomesh.utils.validation_utils', 'Validation utilities'),
        ('koomesh.utils.logging_utils', 'Logging and performance'),
        ('koomesh.meshing', 'Meshing modules'),
        ('koomesh.contact', 'Contact detection'),
        ('koomesh.materials', 'Material management'),
        ('koomesh.cli', 'Command-line interface'),
    ]
    
    modules_ok = True
    for module, desc in modules:
        if not check_module(module, f'({desc})'):
            modules_ok = False
    print()
    
    # Test basic functionality
    if core_ok:
        print("Basic Functionality Tests:")
        print("-" * 70)
        
        try:
            from koomesh.utils import validate_positive_number
            validate_positive_number(5.0, "test")
            print("✓ validate_positive_number works")
        except Exception as e:
            print(f"✗ validate_positive_number failed: {e}")
            modules_ok = False
        
        try:
            from koomesh.utils import ConfigLoader
            loader = ConfigLoader()
            print("✓ ConfigLoader instantiation works")
        except Exception as e:
            print(f"✗ ConfigLoader failed: {e}")
            modules_ok = False
        
        print()
    
    # Check optional dependencies
    print("Optional Dependencies:")
    print("-" * 70)
    
    optional = {
        'gmsh': '(optional - mesh generation)',
        'OCC': '(optional - CAD geometry, pythonocc-core)',
    }
    
    for dep, desc in optional.items():
        check_module(dep, desc)
    print()
    
    # Check dev dependencies
    print("Development Dependencies:")
    print("-" * 70)
    
    dev_deps = {
        'pytest': '(testing framework)',
        'black': '(code formatter)',
        'flake8': '(linter)',
        'mypy': '(type checker)',
        'sphinx': '(documentation)',
    }
    
    for dep, desc in dev_deps.items():
        check_module(dep, desc)
    print()
    
    # Summary
    print("=" * 70)
    print("Summary:")
    print("=" * 70)
    
    if core_ok and modules_ok:
        print("✓ Installation SUCCESSFUL - Ready to use!")
        print()
        print("Next steps:")
        print("  1. Run tests: make test")
        print("  2. Try examples: python examples/01_basic_contact_detection.py")
        print("  3. Build docs: make docs")
        print("  4. See TESTING_CHECKLIST.md for full validation")
        return 0
    elif core_ok:
        print("⚠ Partial installation - Core dependencies OK but some modules failed")
        print()
        print("Troubleshooting:")
        print("  1. pip install -e .")
        print("  2. Check import errors above")
        return 1
    else:
        print("✗ Installation INCOMPLETE - Missing core dependencies")
        print()
        print("To fix:")
        print("  1. pip install -r requirements.txt")
        print("  2. pip install -r requirements-dev.txt")
        print("  3. pip install -e '.[dev]'")
        print("  4. Run this script again")
        return 1

if __name__ == "__main__":
    sys.exit(main())
