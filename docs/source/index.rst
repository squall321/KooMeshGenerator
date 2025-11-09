.. KooMeshGenerator documentation master file

Welcome to KooMeshGenerator Documentation
==========================================

**KooMeshGenerator** is a powerful, production-ready CLI tool for generating high-quality finite element meshes for LS-DYNA simulations.

Features
--------

* 🔧 **Production-Ready CLI**: Comprehensive command-line interface for all meshing operations
* 🎯 **Advanced Contact Detection**: Automatic contact-aware meshing with spatial hashing optimization
* 🧪 **Material Automation**: Intelligent material assignment based on geometry and templates
* 📊 **Quality Validation**: Built-in mesh quality checking and contact validation
* ⚡ **High Performance**: Parallel processing and optimized algorithms for large assemblies
* 🔌 **Multiple Formats**: Support for LS-DYNA, NASTRAN, VTK, and more

Quick Start
-----------

Installation::

   pip install -e .

Basic Usage::

   # Generate mesh from STEP file
   koomesh generate input.step --mesh-size 2.0

   # Detect contacts in assembly
   koomesh contact assembly.k --auto-classify --validate

   # Assign materials automatically
   koomesh material assign *.step --template automotive

Documentation Contents
----------------------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   user_guide/installation
   user_guide/quickstart
   user_guide/cli_reference
   user_guide/contact_aware_meshing
   user_guide/material_assignment
   user_guide/workflows

.. toctree::
   :maxdepth: 2
   :caption: Tutorials

   tutorials/automotive_crash
   tutorials/forming_simulation
   tutorials/assembly_meshing
   tutorials/advanced_contacts

.. toctree::
   :maxdepth: 3
   :caption: API Reference

   api/meshing
   api/contact
   api/materials
   api/validation
   api/io
   api/cli

.. toctree::
   :maxdepth: 1
   :caption: Examples

   examples/basic_meshing
   examples/contact_detection
   examples/material_automation
   examples/batch_processing

.. toctree::
   :maxdepth: 1
   :caption: Development

   development/contributing
   development/architecture
   development/testing
   development/changelog

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
