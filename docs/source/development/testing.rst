Testing Guide
=============

Running tests for KooMeshGenerator.

Quick Start
-----------

::

   # Run all tests
   pytest tests/

   # With coverage
   pytest --cov=koomesh tests/

   # Specific test
   pytest tests/test_contact.py -v

Test Organization
-----------------

- ``tests/unit/`` - Unit tests
- ``tests/integration/`` - Integration tests
- ``tests/contact/`` - Contact module tests
- ``tests/materials/`` - Material tests

Writing Tests
-------------

Use pytest fixtures::

   import pytest
   
   def test_contact_detection():
       # Test code here
       assert result == expected

See ``tests/`` directory for examples.
