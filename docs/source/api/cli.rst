Command-Line Interface
=======================

Complete reference for the KooMeshGenerator CLI.

.. automodule:: koomesh.cli
   :members:
   :undoc-members:
   :show-inheritance:

Core Commands
-------------

generate
^^^^^^^^

Generate mesh from geometry files.

.. code-block:: bash

   koomesh generate [OPTIONS] INPUT_FILE

**Options**:

``--mesh-size FLOAT``
   Target mesh element size (default: 2.0)

``--element-type CHOICE``
   Element type: tet4, tet10, hex8, hex20, hex27 (default: tet4)

``--output PATH``
   Output file path (default: auto-generated)

``--contact-aware-meshing``
   Enable contact-aware mesh refinement

``--refinement-factor FLOAT``
   Mesh size multiplier at contact zones (default: 0.5)

``--contact-tolerance FLOAT``
   Maximum gap for contact detection in mm (default: 1.0)

**Examples**::

   # Basic mesh generation
   koomesh generate input.step --mesh-size 2.0

   # With contact-aware meshing
   koomesh generate assembly.step \
       --contact-aware-meshing \
       --refinement-factor 0.5 \
       --contact-tolerance 1.0

   # Specify element type
   koomesh generate input.step --mesh-size 1.5 --element-type hex8

contact
^^^^^^^

Detect and manage contact definitions.

.. code-block:: bash

   koomesh contact [OPTIONS] INPUT_FILE

**Options**:

``--tolerance FLOAT``
   Contact search tolerance in mm (default: 1.0)

``--auto-classify``
   Automatically classify contact types

``--validate``
   Validate contact quality

``--output PATH``
   Output contact definitions file

``--report PATH``
   Generate HTML contact report

``--format CHOICE``
   Output format: lsdyna, nastran (default: lsdyna)

**Examples**::

   # Basic contact detection
   koomesh contact assembly.k --tolerance 1.0

   # With automatic classification
   koomesh contact assembly.k --auto-classify

   # Full workflow
   koomesh contact assembly.k \
       --auto-classify \
       --validate \
       --tolerance 0.5 \
       --report contacts_report.html

material
^^^^^^^^

Material assignment and management.

.. code-block:: bash

   koomesh material COMMAND [OPTIONS]

**Subcommands**:

``assign``
   Assign materials to parts

``validate``
   Validate material assignments

``recommend``
   Get material recommendations

``list``
   List available materials

``info``
   Show material properties

**Examples**::

   # Assign materials using template
   koomesh material assign *.step --template automotive

   # Validate material
   koomesh material validate Steel_Mild --simulation-type crash

   # Get recommendations
   koomesh material recommend \
       --simulation-type crash \
       --min-strength 400 \
       --max-density 8000

   # List all materials
   koomesh material list

   # Show material info
   koomesh material info Aluminum_6061

export
^^^^^^

Export mesh to various formats.

.. code-block:: bash

   koomesh export [OPTIONS] INPUT_FILE OUTPUT_FILE

**Options**:

``--format CHOICE``
   Output format (auto-detected from extension)

``--include-materials``
   Include material definitions

``--include-contacts``
   Include contact definitions

``--precision INTEGER``
   Number precision (default: 8)

``--unit-system CHOICE``
   Unit system: SI, CGS, Imperial (default: SI)

**Examples**::

   # Export to LS-DYNA
   koomesh export mesh.msh output.k

   # With materials and contacts
   koomesh export mesh.msh output.k \
       --include-materials \
       --include-contacts

   # Export to multiple formats
   koomesh export mesh.msh output.k --format lsdyna
   koomesh export mesh.msh output.inp --format abaqus
   koomesh export mesh.msh output.vtu --format vtk

quality
^^^^^^^

Check and improve mesh quality.

.. code-block:: bash

   koomesh quality COMMAND [OPTIONS] INPUT_FILE

**Subcommands**:

``check``
   Check mesh quality metrics

``report``
   Generate quality report

``improve``
   Improve mesh quality

**Options**:

``--report PATH``
   Generate HTML quality report

``--min-aspect-ratio FLOAT``
   Minimum acceptable aspect ratio

``--min-jacobian FLOAT``
   Minimum acceptable Jacobian

``--fix``
   Automatically fix quality issues

**Examples**::

   # Check quality
   koomesh quality check mesh.k

   # Generate detailed report
   koomesh quality check mesh.k --report quality.html

   # Check with thresholds
   koomesh quality check mesh.k \
       --min-aspect-ratio 3.0 \
       --min-jacobian 0.4

   # Auto-fix issues
   koomesh quality improve mesh.k --fix

validate
^^^^^^^^

Validate mesh for FEA solvers.

.. code-block:: bash

   koomesh validate [OPTIONS] INPUT_FILE

**Options**:

``--solver CHOICE``
   Target solver: lsdyna, nastran, abaqus (default: lsdyna)

``--simulation-type CHOICE``
   Simulation type: crash, forming, impact

``--check-topology``
   Check mesh topology

``--fix``
   Fix validation errors

``--report PATH``
   Generate validation report

**Examples**::

   # Validate for LS-DYNA
   koomesh validate mesh.k --solver lsdyna

   # Validate for crash simulation
   koomesh validate mesh.k \
       --solver lsdyna \
       --simulation-type crash

   # Check and fix topology
   koomesh validate mesh.k --check-topology --fix

Utility Commands
----------------

convert
^^^^^^^

Convert between mesh formats.

.. code-block:: bash

   koomesh convert [OPTIONS] INPUT_FILE

**Options**:

``--to CHOICE``
   Target format

``--output PATH``
   Output file path

``--element-type CHOICE``
   Convert element type

**Examples**::

   # Convert format
   koomesh convert input.msh --to lsdyna -o output.k

   # Convert element type
   koomesh convert input.k --element-type tet10 -o output.k

   # Batch conversion
   koomesh convert *.msh --to lsdyna --output-dir lsdyna_files/

repair
^^^^^^

Repair mesh issues.

.. code-block:: bash

   koomesh repair [OPTIONS] INPUT_FILE

**Options**:

``--fix-normals``
   Fix inverted element normals

``--merge-duplicates``
   Merge duplicate nodes

``--fill-holes``
   Fill mesh holes

``--remove-degenerate``
   Remove degenerate elements

``--tolerance FLOAT``
   Tolerance for operations (default: 1e-6)

**Examples**::

   # Fix normals
   koomesh repair mesh.k --fix-normals

   # Merge duplicate nodes
   koomesh repair mesh.k --merge-duplicates --tolerance 1e-6

   # Full repair
   koomesh repair mesh.k \
       --fix-normals \
       --merge-duplicates \
       --fill-holes \
       --remove-degenerate

smooth
^^^^^^

Apply mesh smoothing.

.. code-block:: bash

   koomesh smooth [OPTIONS] INPUT_FILE

**Options**:

``--iterations INTEGER``
   Number of smoothing iterations (default: 5)

``--method CHOICE``
   Smoothing method: laplacian, taubin (default: laplacian)

``--preserve-boundaries``
   Keep boundary nodes fixed

**Examples**::

   # Basic smoothing
   koomesh smooth mesh.k --iterations 5

   # Taubin smoothing (better quality preservation)
   koomesh smooth mesh.k --method taubin --iterations 10

   # Smooth with fixed boundaries
   koomesh smooth mesh.k --preserve-boundaries

Global Options
--------------

These options work with all commands:

``--verbose, -v``
   Enable verbose output

``--quiet, -q``
   Suppress output

``--config PATH``
   Configuration file path

``--log-file PATH``
   Write log to file

``--no-color``
   Disable colored output

``--version``
   Show version and exit

``--help, -h``
   Show help message

**Examples**::

   # Verbose mode
   koomesh generate input.step -v

   # Use config file
   koomesh generate input.step --config my_config.yaml

   # Save log
   koomesh generate input.step --log-file generation.log

Configuration File
------------------

YAML configuration file format:

.. code-block:: yaml

   # koomesh_config.yaml

   # Meshing options
   meshing:
     mesh_size: 2.0
     element_type: tet4
     contact_aware: true
     refinement_factor: 0.5
     contact_tolerance: 1.0

   # Contact detection
   contact:
     auto_classify: true
     validate_quality: true
     tolerance: 1.0

   # Material assignment
   material:
     template: automotive_crash
     strategy: filename
     fallback_to_geometry: true

   # Export options
   export:
     format: lsdyna
     include_materials: true
     include_contacts: true
     precision: 8
     unit_system: SI

   # Quality thresholds
   quality:
     min_aspect_ratio: 3.0
     min_jacobian: 0.4
     max_warpage: 15.0
     max_skewness: 0.7

   # Logging
   logging:
     level: INFO
     file: koomesh.log
     console: true

**Usage**::

   koomesh generate input.step --config koomesh_config.yaml

Environment Variables
---------------------

``KOOMESH_CONFIG``
   Default configuration file path

``KOOMESH_MATERIAL_LIB``
   Material library directory

``KOOMESH_LOG_LEVEL``
   Default log level (DEBUG, INFO, WARNING, ERROR)

``KOOMESH_CACHE_DIR``
   Cache directory for temporary files

**Example**::

   export KOOMESH_CONFIG=~/.koomesh/config.yaml
   export KOOMESH_LOG_LEVEL=DEBUG
   koomesh generate input.step

Exit Codes
----------

=====  ================================
Code   Meaning
=====  ================================
0      Success
1      General error
2      Invalid input
3      Validation failed
4      File not found
5      Permission denied
10     Mesh generation failed
11     Contact detection failed
12     Material assignment failed
20     Quality below threshold
=====  ================================

Common Workflows
----------------

Automotive Crash Simulation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   #!/bin/bash

   # 1. Generate mesh with contact-aware meshing
   koomesh generate assembly.step \
       --contact-aware-meshing \
       --mesh-size 2.0 \
       --output assembly.k

   # 2. Assign materials
   koomesh material assign assembly/*.step \
       --template automotive_crash \
       --output materials.yaml

   # 3. Detect contacts
   koomesh contact assembly.k \
       --auto-classify \
       --validate \
       --output contacts.k

   # 4. Validate mesh
   koomesh validate assembly.k \
       --solver lsdyna \
       --simulation-type crash \
       --report validation.html

   # 5. Export final model
   koomesh export assembly.k final_model.k \
       --include-materials \
       --include-contacts

Forming Simulation
^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Assign materials for forming
   koomesh material assign blank.step die.step punch.step \
       --template forming

   # Generate mesh
   koomesh generate blank.step --mesh-size 1.0

   # Detect tool-blank contacts
   koomesh contact forming_assembly.k \
       --auto-classify \
       --tolerance 0.5

   # Validate and export
   koomesh validate forming_assembly.k --simulation-type forming
   koomesh export forming_assembly.k final.k --include-contacts

See Also
--------

* :doc:`../user_guide/cli_reference` - Detailed CLI reference
* :doc:`../user_guide/workflows` - Complete workflow examples
* :doc:`../tutorials/automotive_crash` - Step-by-step tutorial
