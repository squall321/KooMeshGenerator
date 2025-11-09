CLI Reference
=============

Complete command-line interface reference.

See :doc:`../api/cli` for detailed API documentation.

Command Overview
----------------

Core Commands
^^^^^^^^^^^^^

* ``generate`` - Generate mesh from geometry
* ``contact`` - Detect and manage contacts
* ``material`` - Material assignment and management
* ``export`` - Export mesh to various formats
* ``quality`` - Check and improve mesh quality
* ``validate`` - Validate mesh for FEA solvers

Utility Commands
^^^^^^^^^^^^^^^^

* ``convert`` - Convert between formats
* ``repair`` - Repair mesh issues
* ``smooth`` - Apply mesh smoothing
* ``info`` - Show mesh information

Quick Reference
---------------

Most Common Commands::

   # Generate mesh
   koomesh generate input.step --mesh-size 2.0

   # With contact-aware meshing
   koomesh generate assembly.step --contact-aware-meshing

   # Detect contacts
   koomesh contact assembly.k --auto-classify --validate

   # Assign materials
   koomesh material assign *.step --template automotive

   # Check quality
   koomesh quality check mesh.k

   # Validate
   koomesh validate mesh.k --solver lsdyna

For detailed command documentation, see :doc:`../api/cli`.
