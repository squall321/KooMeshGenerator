Complete Workflows
==================

End-to-end workflows for common simulation scenarios.

Automotive Crash Workflow
--------------------------

Complete workflow for crash simulation setup.

Step 1: Prepare Geometry
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Organize files
   mkdir -p crash_model/{geometry,mesh,materials,contacts}
   cd crash_model

Step 2: Generate Mesh
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Generate with contact-aware meshing
   koomesh generate geometry/*.step \
       --contact-aware-meshing \
       --mesh-size 2.0 \
       --refinement-factor 0.5 \
       --output mesh/assembly.k

Step 3: Assign Materials
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Auto-assign materials
   koomesh material assign geometry/*.step \
       --template automotive_crash \
       --output materials/assignments.yaml

Step 4: Detect Contacts
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Detect and classify
   koomesh contact mesh/assembly.k \
       --auto-classify \
       --validate \
       --tolerance 1.0 \
       --output contacts/contacts.k \
       --report contacts/report.html

Step 5: Validate
^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Validate for LS-DYNA crash
   koomesh validate mesh/assembly.k \
       --solver lsdyna \
       --simulation-type crash \
       --report validation_report.html

Step 6: Export
^^^^^^^^^^^^^^^

.. code-block:: bash

   # Create final model
   koomesh export mesh/assembly.k final_model.k \
       --include-materials \
       --include-contacts \
       --precision 8

Forming Simulation Workflow
----------------------------

Sheet metal forming setup.

Step 1: Prepare Parts
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Organize
   mkdir forming_sim
   cd forming_sim

   # Parts needed:
   # - blank.step (sheet metal)
   # - die_upper.step
   # - die_lower.step
   # - holder.step

Step 2: Assign Materials
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   koomesh material assign *.step --template forming

   # Should assign:
   # blank → Aluminum_5052 (formable)
   # dies → Steel_ToolSteel (hard)
   # holder → Steel_Mild (general)

Step 3: Generate Meshes
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Fine mesh for blank
   koomesh generate blank.step --mesh-size 1.0

   # Coarser for tools (rigid)
   koomesh generate die_upper.step --mesh-size 3.0
   koomesh generate die_lower.step --mesh-size 3.0
   koomesh generate holder.step --mesh-size 3.0

Step 4: Detect Contacts
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   koomesh contact forming_assembly.k \
       --auto-classify \
       --tolerance 0.5  # Tight tolerance for forming

Step 5: Export
^^^^^^^^^^^^^^^

.. code-block:: bash

   koomesh export forming_assembly.k final.k \
       --include-materials \
       --include-contacts

Assembly Workflow
-----------------

General multi-part assembly.

Batch Processing
^^^^^^^^^^^^^^^^

.. code-block:: bash

   #!/bin/bash
   # process_assembly.sh

   PARTS_DIR="parts"
   OUTPUT_DIR="output"

   mkdir -p $OUTPUT_DIR

   # Generate all meshes
   for part in $PARTS_DIR/*.step; do
       name=$(basename "$part" .step)
       echo "Processing $name..."

       koomesh generate "$part" \
           --mesh-size 2.0 \
           --output "$OUTPUT_DIR/${name}.k"
   done

   # Combine
   cat $OUTPUT_DIR/*.k > $OUTPUT_DIR/assembly.k

   # Detect contacts
   koomesh contact $OUTPUT_DIR/assembly.k \
       --auto-classify \
       --output $OUTPUT_DIR/contacts.k

Best Practices
--------------

1. **Start Simple**: Basic mesh first, add complexity later
2. **Validate Early**: Check quality at each step
3. **Use Templates**: Leverage industry templates for materials
4. **Document**: Save configuration files for reproducibility
5. **Version Control**: Track mesh versions

See Also
--------

* :doc:`../tutorials/automotive_crash` - Detailed tutorial
* :doc:`../tutorials/forming_simulation` - Forming tutorial
* :doc:`contact_aware_meshing` - Advanced contact features
* :doc:`material_assignment` - Material automation
