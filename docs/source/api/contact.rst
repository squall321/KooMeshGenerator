Contact Detection and Management
=================================

This module provides advanced contact detection, classification, and quality validation for multi-part assemblies.

Contact-Aware Meshing
---------------------

.. automodule:: koomesh.meshing.contact_aware_mesher
   :members:
   :undoc-members:
   :show-inheritance:

Contact Type Classification
----------------------------

.. automodule:: koomesh.contact.contact_classifier
   :members:
   :undoc-members:
   :show-inheritance:

Contact Quality Validation
---------------------------

.. automodule:: koomesh.contact.contact_quality
   :members:
   :undoc-members:
   :show-inheritance:

Assembly Contact Management
----------------------------

.. automodule:: koomesh.contact.assembly_contact
   :members:
   :undoc-members:
   :show-inheritance:

Usage Examples
--------------

Basic Contact Detection
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from koomesh.contact.assembly_contact import AssemblyContactManager

   # Load parts
   parts = [
       ('Body', body_mesh),
       ('Door', door_mesh),
       ('Hood', hood_mesh)
   ]

   # Detect contacts
   manager = AssemblyContactManager()
   contact_pairs = manager.detect_contacts(
       parts,
       tolerance=1.0,
       auto_classify=True
   )

   # Review contacts
   for pair in contact_pairs:
       print(f"{pair.master_part} - {pair.slave_part}")
       print(f"  Type: {pair.contact_type}")
       print(f"  Friction: {pair.parameters.fs}")

Contact-Aware Meshing
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from koomesh.meshing.contact_aware_mesher import ContactAwareMesher

   # Detect contact zones
   mesher = ContactAwareMesher()
   contact_zones = mesher.detect_potential_contact_zones(
       shapes,
       tolerance=1.0
   )

   # Apply refinement at contact zones
   mesher.apply_contact_refinement(
       gmsh_model,
       contact_zones,
       base_mesh_size=2.0,
       refinement_factor=0.5
   )

Contact Quality Validation
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from koomesh.contact.contact_quality import ContactQualityChecker

   # Check contact quality
   checker = ContactQualityChecker()
   report = checker.check_contact_quality(
       mesh1, mesh2,
       contact_surfaces1, contact_surfaces2,
       tolerance=0.1
   )

   # Review issues
   if not report.passed:
       for issue in report.issues:
           print(f"{issue.severity}: {issue.message}")
           print(f"  Fix: {issue.fix_suggestion}")

CLI Usage
---------

Contact Detection::

   # Detect all contacts
   koomesh contact assembly.k --tolerance 1.0

   # With automatic classification
   koomesh contact assembly.k --auto-classify

   # With quality validation
   koomesh contact assembly.k --validate --tolerance 0.1

Contact-Aware Meshing::

   # Enable contact-aware meshing during generation
   koomesh generate assembly.step --contact-aware-meshing --refinement-factor 0.5

See Also
--------

* :doc:`../user_guide/contact_aware_meshing`
* :doc:`../tutorials/assembly_meshing`
* :doc:`../tutorials/advanced_contacts`
