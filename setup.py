"""Setup script for KooMeshGenerator."""

from setuptools import setup, find_packages
from pathlib import Path

# Read long description from README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read version from package
version = "0.1.0"

setup(
    name="koomesh",
    version=version,
    author="KooMesh Team",
    author_email="koomesh@example.com",
    description="Automated mesh generator for LS-DYNA FEA simulations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/KooMeshGenerator",
    packages=find_packages(exclude=["tests", "tests.*", "docs", "examples"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Physics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.20.0",
        "scipy>=1.7.0",
        "click>=8.0.0",
        "pyyaml>=5.4.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "isort>=5.10.0",
            "mypy>=0.950",
            "pre-commit>=2.17.0",
            "bandit>=1.7.0",
            "safety>=2.0.0",
        ],
        "docs": [
            "sphinx>=4.5.0",
            "sphinx_rtd_theme>=1.0.0",
            "myst-parser>=0.18.0",
        ],
        "cad": [
            "pythonocc-core>=7.5.0",  # Optional CAD geometry support
        ],
        "mesh": [
            "gmsh>=4.9.0",  # Optional GMSH integration
        ],
    },
    entry_points={
        "console_scripts": [
            "koomesh=koomesh.cli.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
