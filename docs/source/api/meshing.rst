Meshing Module
===============

This module provides core mesh generation functionality including geometry processing, mesh generation, and quality optimization.

Core Meshing
------------

.. automodule:: koomesh.meshing.gmsh_wrapper
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: koomesh.meshing.mesh_generator
   :members:
   :undoc-members:
   :show-inheritance:

Mesh Data Structures
---------------------

.. automodule:: koomesh.meshing.mesh_data
   :members:
   :undoc-members:
   :show-inheritance:

Contact-Aware Meshing
----------------------

.. automodule:: koomesh.meshing.contact_aware_mesher
   :members:
   :undoc-members:
   :show-inheritance:

Mesh Quality
------------

.. automodule:: koomesh.meshing.mesh_quality
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: koomesh.meshing.quality_checker
   :members:
   :undoc-members:
   :show-inheritance:

Mesh Repair
-----------

.. automodule:: koomesh.meshing.mesh_repair
   :members:
   :undoc-members:
   :show-inheritance:

Usage Examples
--------------

Basic Mesh Generation
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from koomesh.meshing.mesh_generator import MeshGenerator

   # Initialize generator
   generator = MeshGenerator()

   # Generate mesh from STEP file
   mesh = generator.generate_from_step(
       'input.step',
       mesh_size=2.0,
       element_type='tet4'
   )

   # Access mesh data
   print(f"Nodes: {len(mesh.nodes)}")
   print(f"Elements: {len(mesh.elements)}")

Contact-Aware Meshing
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from koomesh.meshing.contact_aware_mesher import ContactAwareMesher
   from koomesh.meshing.mesh_generator import MeshGenerator

   # Initialize
   mesher = ContactAwareMesher()
   generator = MeshGenerator()

   # Load geometry
   shapes = generator.load_step_files(['part1.step', 'part2.step'])

   # Detect contact zones
   contact_zones = mesher.detect_potential_contact_zones(
       shapes,
       tolerance=1.0
   )

   # Generate mesh with refinement at contacts
   gmsh_model = generator.create_gmsh_model(shapes)
   mesher.apply_contact_refinement(
       gmsh_model,
       contact_zones,
       base_mesh_size=2.0,
       refinement_factor=0.5
   )

   mesh = generator.generate_mesh(gmsh_model)

Quality Checking
^^^^^^^^^^^^^^^^

.. code-block:: python

   from koomesh.meshing.quality_checker import QualityChecker

   # Initialize checker
   checker = QualityChecker()

   # Check mesh quality
   report = checker.check_quality(mesh)

   # Review results
   print(f"Min aspect ratio: {report.min_aspect_ratio}")
   print(f"Poor elements: {report.num_poor_elements}")

   # Get detailed metrics
   metrics = checker.calculate_metrics(mesh)
   print(f"Average Jacobian: {metrics['jacobian']['mean']}")

Mesh Repair
^^^^^^^^^^^

.. code-block:: python

   from koomesh.meshing.mesh_repair import MeshRepair

   # Initialize repair tool
   repair = MeshRepair()

   # Fix common issues
   repaired_mesh = repair.repair_mesh(
       mesh,
       fix_normals=True,
       remove_duplicates=True,
       fill_holes=True
   )

   print(f"Repaired {repair.num_fixes} issues")

CLI Usage
---------

Basic Mesh Generation::

   # Generate mesh
   koomesh generate input.step --mesh-size 2.0

   # With element type
   koomesh generate input.step --mesh-size 2.0 --element-type hex8

Contact-Aware Meshing::

   # Enable contact-aware meshing
   koomesh generate assembly.step \
       --contact-aware-meshing \
       --refinement-factor 0.5

   # With specific tolerance
   koomesh generate assembly.step \
       --contact-aware-meshing \
       --contact-tolerance 1.0

Quality Checking::

   # Check mesh quality
   koomesh quality check mesh.k

   # Generate detailed report
   koomesh quality check mesh.k --report quality_report.html

See Also
--------

* :doc:`contact` - Contact detection and management
* :doc:`validation` - Mesh validation tools
* :doc:`../user_guide/quickstart` - Quick start guide
* :doc:`../tutorials/assembly_meshing` - Assembly meshing tutorial
