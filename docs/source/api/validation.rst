Validation Module
==================

This module provides comprehensive mesh validation for various FEA solvers, particularly LS-DYNA.

LS-DYNA Validation
------------------

.. automodule:: koomesh.validation.lsdyna_validator
   :members:
   :undoc-members:
   :show-inheritance:

General Validation
------------------

.. automodule:: koomesh.validation.mesh_validator
   :members:
   :undoc-members:
   :show-inheritance:

Quality Metrics
---------------

.. automodule:: koomesh.validation.quality_metrics
   :members:
   :undoc-members:
   :show-inheritance:

Topology Validation
-------------------

.. automodule:: koomesh.validation.topology_validator
   :members:
   :undoc-members:
   :show-inheritance:

Usage Examples
--------------

LS-DYNA Validation
^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from koomesh.validation.lsdyna_validator import LSDynaValidator

   # Initialize validator
   validator = LSDynaValidator()

   # Validate mesh for LS-DYNA
   report = validator.validate(mesh)

   # Check results
   if report.is_valid:
       print("✓ Mesh is valid for LS-DYNA")
   else:
       print("✗ Validation failed:")
       for error in report.errors:
           print(f"  - {error}")

   # Check warnings
   for warning in report.warnings:
       print(f"  ⚠ {warning}")

Compatibility Checks
^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from koomesh.validation.lsdyna_validator import LSDynaValidator

   validator = LSDynaValidator()

   # Check specific aspects
   checks = validator.run_checks(mesh)

   # Element type compatibility
   if checks['element_types']['passed']:
       print("✓ Element types compatible")
   else:
       print(f"✗ Incompatible elements: {checks['element_types']['issues']}")

   # Node numbering
   if checks['node_numbering']['passed']:
       print("✓ Node numbering valid")

   # Material IDs
   if checks['material_ids']['passed']:
       print("✓ Material IDs valid")

Quality Validation
^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from koomesh.validation.quality_metrics import QualityMetrics

   # Calculate quality metrics
   metrics = QualityMetrics()
   results = metrics.calculate_all(mesh)

   # Check against thresholds
   thresholds = {
       'aspect_ratio': 5.0,
       'jacobian': 0.3,
       'warpage': 15.0,
       'skewness': 0.7
   }

   for metric, threshold in thresholds.items():
       if metric in results:
           value = results[metric]['min']
           if value < threshold:
               print(f"⚠ {metric}: {value:.3f} (threshold: {threshold})")
           else:
               print(f"✓ {metric}: {value:.3f}")

Topology Validation
^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from koomesh.validation.topology_validator import TopologyValidator

   validator = TopologyValidator()

   # Check topology
   topology_report = validator.validate(mesh)

   # Free edges (should be 0 for closed mesh)
   if topology_report.num_free_edges > 0:
       print(f"⚠ Found {topology_report.num_free_edges} free edges")

   # Duplicate nodes
   if topology_report.num_duplicate_nodes > 0:
       print(f"⚠ Found {topology_report.num_duplicate_nodes} duplicate nodes")
       # Get duplicate node IDs
       print(f"  Duplicate IDs: {topology_report.duplicate_node_ids}")

   # Non-manifold edges
   if topology_report.num_non_manifold_edges > 0:
       print(f"⚠ Found {topology_report.num_non_manifold_edges} non-manifold edges")

   # Element normals
   if topology_report.num_inverted_elements > 0:
       print(f"✗ Found {topology_report.num_inverted_elements} inverted elements")

Validation Reports
^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from koomesh.validation.mesh_validator import MeshValidator

   # Comprehensive validation
   validator = MeshValidator()
   report = validator.validate_all(
       mesh,
       solver='lsdyna',
       simulation_type='crash'
   )

   # Generate HTML report
   report.to_html('validation_report.html')

   # Or JSON
   report.to_json('validation_report.json')

   # Print summary
   print(report.summary())

Custom Validation Rules
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from koomesh.validation.mesh_validator import MeshValidator, ValidationRule

   # Define custom rule
   class CustomRule(ValidationRule):
       def __init__(self, max_element_size):
           self.max_element_size = max_element_size

       def validate(self, mesh):
           issues = []
           for i, elem in enumerate(mesh.elements):
               size = self.calculate_element_size(elem, mesh.nodes)
               if size > self.max_element_size:
                   issues.append(f"Element {i} size {size:.3f} > {self.max_element_size}")
           return issues

   # Use custom rule
   validator = MeshValidator()
   validator.add_rule(CustomRule(max_element_size=10.0))
   report = validator.validate(mesh)

CLI Usage
---------

LS-DYNA Validation::

   # Validate for LS-DYNA
   koomesh validate mesh.k --solver lsdyna

   # With detailed report
   koomesh validate mesh.k --solver lsdyna --report validation.html

   # Check specific simulation type
   koomesh validate mesh.k --solver lsdyna --simulation crash

Quality Validation::

   # Check quality metrics
   koomesh quality check mesh.k

   # With thresholds
   koomesh quality check mesh.k \
       --min-aspect-ratio 3.0 \
       --min-jacobian 0.4

Topology Validation::

   # Check topology
   koomesh validate mesh.k --check-topology

   # Fix common issues
   koomesh validate mesh.k --check-topology --fix

Validation Thresholds
---------------------

Default quality thresholds for different simulation types:

Crash Analysis
^^^^^^^^^^^^^^

========  ==============  =================
Metric    Minimum         Recommended
========  ==============  =================
Aspect    < 5.0           < 3.0
Jacobian  > 0.3           > 0.5
Warpage   < 15°           < 10°
Skewness  < 0.7           < 0.5
========  ==============  =================

Forming Analysis
^^^^^^^^^^^^^^^^

========  ==============  =================
Metric    Minimum         Recommended
========  ==============  =================
Aspect    < 4.0           < 2.5
Jacobian  > 0.4           > 0.6
Warpage   < 12°           < 8°
Skewness  < 0.6           < 0.4
========  ==============  =================

General FEA
^^^^^^^^^^^

========  ==============  =================
Metric    Minimum         Recommended
========  ==============  =================
Aspect    < 10.0          < 5.0
Jacobian  > 0.2           > 0.4
Warpage   < 20°           < 15°
Skewness  < 0.8           < 0.6
========  ==============  =================

Troubleshooting
---------------

Common Validation Issues
^^^^^^^^^^^^^^^^^^^^^^^^

**Issue**: "Element type not supported by LS-DYNA"

**Solution**: Convert to supported types::

   koomesh convert mesh.k --element-type tet4

**Issue**: "Negative volume elements detected"

**Solution**: Fix element normals::

   koomesh repair mesh.k --fix-normals

**Issue**: "Duplicate nodes found"

**Solution**: Merge duplicate nodes::

   koomesh repair mesh.k --merge-duplicates --tolerance 1e-6

**Issue**: "Poor element quality"

**Solution**: Apply mesh smoothing::

   koomesh smooth mesh.k --iterations 5

See Also
--------

* :doc:`meshing` - Mesh generation
* :doc:`contact` - Contact validation
* :doc:`materials` - Material validation
* :doc:`../user_guide/workflows` - Validation workflows
