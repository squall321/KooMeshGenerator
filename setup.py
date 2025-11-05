#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
KooMeshGenerator - Automated mesh generation from STEP files
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text() if (this_directory / "README.md").exists() else ""

setup(
    name='koomesh',
    version='1.0.0',
    description='Automated mesh generation from STEP files with LS-DYNA output',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='KooMesh Team',
    author_email='info@koomesh.dev',
    url='https://github.com/yourorg/KooMeshGenerator',
    license='MIT',

    # Package configuration
    packages=find_packages(exclude=['tests', 'tests.*', 'benchmarks', 'docs']),
    include_package_data=True,
    zip_safe=False,

    # Python version requirement
    python_requires='>=3.9',

    # Dependencies
    install_requires=[
        'numpy>=1.20.0',
        'scipy>=1.7.0',
        'click>=8.0.0',
        'tqdm>=4.60.0',
        'dataclasses-json>=0.5.7',
        'pyyaml>=5.4.0',
    ],

    # Optional dependencies
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=3.0.0',
            'pytest-benchmark>=3.4.1',
            'black>=22.0.0',
            'flake8>=4.0.0',
            'mypy>=0.950',
            'sphinx>=4.5.0',
            'sphinx-rtd-theme>=1.0.0',
        ],
        'gmsh': [
            'gmsh>=4.9.0',
        ],
        # Note: pythonocc-core needs to be built separately
    },

    # CLI entry points
    entry_points={
        'console_scripts': [
            'koomesh=koomesh.cli.main:cli',
        ],
    },

    # Classifiers for PyPI
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Computer Aided Engineering (CAE)',
        'Topic :: Scientific/Engineering :: Mathematics',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Operating System :: OS Independent',
        'Environment :: Console',
    ],

    # Keywords for search
    keywords='mesh generation CAD STEP finite-element FEM LS-DYNA hexahedral tetrahedral',
)
