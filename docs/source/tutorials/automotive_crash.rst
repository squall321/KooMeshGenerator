Automotive Crash Simulation Tutorial
=====================================

Step-by-step tutorial for setting up an automotive crash simulation.

Overview
--------

In this tutorial, you will:

1. Load automotive parts (body, hood, door)
2. Generate meshes with contact refinement
3. Assign materials automatically
4. Detect and classify contacts
5. Validate for LS-DYNA
6. Export complete model

Prerequisites
-------------

- KooMeshGenerator installed
- Basic CLI knowledge
- STEP files of automotive parts

Tutorial Files
--------------

Download example files::

   # Download sample automotive assembly
   wget https://koomesh.io/examples/automotive_crash.zip
   unzip automotive_crash.zip
   cd automotive_crash/

Files included:
- ``body.step``
- ``hood_outer.step``
- ``door_fl_outer.step``
- ``pillar_a_left.step``

Step 1: Project Setup
----------------------

Create project structure::

   mkdir crash_simulation
   cd crash_simulation
   mkdir geometry meshes materials contacts

   # Copy STEP files
   cp *.step geometry/

Step 2: Generate Meshes
------------------------

Generate with contact-aware meshing::

   koomesh generate geometry/*.step \
       --contact-aware-meshing \
       --mesh-size 2.0 \
       --refinement-factor 0.5 \
       --output meshes/assembly.k

Expected output::

   ✓ Loaded 4 STEP files
   ✓ Detected 6 contact zones
   ✓ Applied contact refinement
   ✓ Generated 45,234 elements
   ✓ Saved to meshes/assembly.k

Step 3: Assign Materials
-------------------------

Use automotive crash template::

   koomesh material assign geometry/*.step \
       --template automotive_crash \
       --output materials/assignments.yaml

Review assignments::

   cat materials/assignments.yaml

Expected assignments:
- ``hood_outer.step`` → ``Aluminum_5052``
- ``body.step`` → ``Steel_HighStrength``
- ``pillar_a_left.step`` → ``Steel_UltraHighStrength``

Step 4: Detect Contacts
------------------------

Auto-detect and classify::

   koomesh contact meshes/assembly.k \
       --auto-classify \
       --validate \
       --tolerance 1.0 \
       --output contacts/contacts.k \
       --report contacts/report.html

Open ``contacts/report.html`` to review detected contacts.

Step 5: Quality Check
----------------------

Validate mesh quality::

   koomesh quality check meshes/assembly.k \
       --report quality_report.html

Expected results:
- Aspect ratio: min=1.1, avg=2.3, max=4.8
- Poor elements: <1%

Step 6: Validate for LS-DYNA
-----------------------------

::

   koomesh validate meshes/assembly.k \
       --solver lsdyna \
       --simulation-type crash \
       --report validation_report.html

Step 7: Export Final Model
---------------------------

::

   koomesh export meshes/assembly.k final_crash_model.k \
       --include-materials \
       --include-contacts \
       --precision 8

Your final model is ready for LS-DYNA!

Next Steps
----------

- Run the simulation in LS-DYNA
- Post-process results in LS-PrePost
- Try :doc:`forming_simulation` tutorial

Complete Code
-------------

All steps in one script::

   #!/bin/bash
   # crash_simulation_setup.sh

   # 1. Generate mesh
   koomesh generate geometry/*.step \
       --contact-aware-meshing \
       --mesh-size 2.0 \
       --output meshes/assembly.k

   # 2. Assign materials
   koomesh material assign geometry/*.step \
       --template automotive_crash \
       --output materials/assignments.yaml

   # 3. Detect contacts
   koomesh contact meshes/assembly.k \
       --auto-classify \
       --validate \
       --output contacts/contacts.k

   # 4. Validate
   koomesh validate meshes/assembly.k \
       --solver lsdyna \
       --simulation-type crash

   # 5. Export
   koomesh export meshes/assembly.k final_crash_model.k \
       --include-materials \
       --include-contacts

   echo "✓ Crash model ready!"

See Also
--------

* :doc:`../user_guide/contact_aware_meshing`
* :doc:`../user_guide/material_assignment`
* :doc:`../api/contact`
