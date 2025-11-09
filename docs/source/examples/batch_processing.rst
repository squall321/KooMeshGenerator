Batch Processing Examples
==========================

Processing multiple files efficiently.

Batch Script
------------

.. code-block:: bash

   for file in parts/*.step; do
       koomesh generate "$file"
   done

See :doc:`../user_guide/workflows` for complete workflows.
