Installation Guide
==================

This guide covers installing KooMeshGenerator on various platforms.

Requirements
------------

System Requirements
^^^^^^^^^^^^^^^^^^^

**Minimum**:
- Python 3.9 or later
- 4 GB RAM
- 2 GB disk space

**Recommended**:
- Python 3.10 or later
- 8 GB RAM
- 10 GB disk space (for large models)
- Multi-core CPU for parallel processing

Dependencies
^^^^^^^^^^^^

**Core dependencies** (installed automatically):

- ``numpy >= 1.20.0`` - Numerical computations
- ``scipy >= 1.7.0`` - Scientific computing
- ``click >= 8.0.0`` - CLI framework
- ``tqdm >= 4.60.0`` - Progress bars
- ``pyyaml >= 5.4.0`` - Configuration files

**Optional dependencies**:

- ``gmsh`` - Mesh generation engine
- ``pythonocc`` - CAD geometry processing
- ``vtk`` - Visualization
- ``matplotlib`` - Plotting

Installation Methods
--------------------

Method 1: From PyPI (Recommended)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Install latest stable version
   pip install koomesh

   # Install with optional dependencies
   pip install koomesh[viz]  # Visualization tools
   pip install koomesh[dev]  # Development tools
   pip install koomesh[all]  # Everything

   # Verify installation
   koomesh --version

Method 2: From Source
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Clone repository
   git clone https://github.com/yourorg/KooMeshGenerator.git
   cd KooMeshGenerator

   # Install in development mode
   pip install -e .

   # Or install with extras
   pip install -e .[dev,viz]

   # Verify installation
   koomesh --version
   pytest tests/  # Run tests

Method 3: Using Docker
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Pull image
   docker pull koomesh/koomeshgenerator:latest

   # Run container
   docker run -it --rm \
       -v $(pwd):/workspace \
       koomesh/koomeshgenerator:latest \
       koomesh generate /workspace/input.step

   # Or use docker-compose
   docker-compose up

Method 4: Using Conda
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Create conda environment
   conda create -n koomesh python=3.10
   conda activate koomesh

   # Install from conda-forge
   conda install -c conda-forge koomesh

   # Or install from PyPI in conda env
   pip install koomesh

Platform-Specific Instructions
-------------------------------

Linux (Ubuntu/Debian)
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Update system
   sudo apt update

   # Install Python and dependencies
   sudo apt install python3-pip python3-dev

   # Install build essentials (for compiling extensions)
   sudo apt install build-essential

   # Install KooMesh
   pip3 install koomesh

   # Install optional dependencies
   sudo apt install libgmsh-dev  # GMSH
   sudo apt install libvtk9-dev  # VTK

Linux (CentOS/RHEL)
^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Install Python
   sudo yum install python3 python3-pip python3-devel

   # Install development tools
   sudo yum groupinstall "Development Tools"

   # Install KooMesh
   pip3 install koomesh

macOS
^^^^^

.. code-block:: bash

   # Install Homebrew (if not installed)
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

   # Install Python
   brew install python@3.10

   # Install KooMesh
   pip3 install koomesh

   # Install optional dependencies
   brew install gmsh
   brew install vtk

Windows
^^^^^^^

.. code-block:: powershell

   # Install Python from python.org or Microsoft Store
   # Ensure pip is installed

   # Install KooMesh
   pip install koomesh

   # Install Visual C++ Build Tools (if needed)
   # Download from: https://visualstudio.microsoft.com/downloads/

**Alternative: Windows Subsystem for Linux (WSL)**

.. code-block:: bash

   # Install WSL2
   wsl --install

   # In WSL Ubuntu
   sudo apt update
   sudo apt install python3-pip
   pip3 install koomesh

Installing Optional Components
-------------------------------

GMSH
^^^^

**Linux**::

   sudo apt install gmsh  # Ubuntu/Debian
   sudo yum install gmsh  # CentOS/RHEL

**macOS**::

   brew install gmsh

**Windows**:

Download from https://gmsh.info/

PythonOCC (CAD Engine)
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Using conda (recommended)
   conda install -c conda-forge pythonocc-core

   # Using pip (may require compilation)
   pip install pythonocc-core

VTK (Visualization)
^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Linux
   sudo apt install python3-vtk9

   # macOS
   brew install vtk

   # Using pip
   pip install vtk

Verifying Installation
----------------------

Check Version
^^^^^^^^^^^^^

.. code-block:: bash

   koomesh --version

Expected output::

   KooMeshGenerator version 1.0.0

Check Components
^^^^^^^^^^^^^^^^

.. code-block:: python

   import koomesh
   print(koomesh.__version__)

   # Check optional components
   try:
       import gmsh
       print("✓ GMSH available")
   except ImportError:
       print("✗ GMSH not installed")

   try:
       from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
       print("✓ PythonOCC available")
   except ImportError:
       print("✗ PythonOCC not installed")

Run Tests
^^^^^^^^^

.. code-block:: bash

   # Quick test
   pytest tests/ -k "not slow"

   # Full test suite
   pytest tests/

   # With coverage
   pytest --cov=koomesh tests/

Generate Test Mesh
^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Create test geometry
   python -c "
   from koomesh.examples import create_box
   box = create_box(10, 10, 10)
   box.export('test_box.step')
   "

   # Generate mesh
   koomesh generate test_box.step --mesh-size 2.0

   # Should create: test_box.k

Troubleshooting
---------------

Import Error: No module named 'koomesh'
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Cause**: Package not installed or wrong Python environment

**Solution**::

   # Check Python path
   which python
   which pip

   # Reinstall
   pip install --upgrade koomesh

   # Or specify Python version
   python3.10 -m pip install koomesh

Error: numpy not found
^^^^^^^^^^^^^^^^^^^^^^

**Cause**: Missing dependency

**Solution**::

   pip install numpy scipy

Permission Denied
^^^^^^^^^^^^^^^^^

**Cause**: No write access to Python directory

**Solution**::

   # Install for user only
   pip install --user koomesh

   # Or use virtual environment
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   pip install koomesh

GMSH not found
^^^^^^^^^^^^^^

**Cause**: GMSH not in PATH

**Solution**::

   # Linux: Add to PATH
   export PATH=$PATH:/usr/local/bin

   # Windows: Add GMSH install dir to PATH
   # System Properties > Environment Variables > Path

   # Or specify GMSH path
   export GMSH_PATH=/path/to/gmsh

Compilation Error (Windows)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Cause**: Missing Visual C++ compiler

**Solution**:

1. Install Visual Studio Build Tools
2. Download from: https://visualstudio.microsoft.com/downloads/
3. Select "C++ build tools" during installation
4. Retry installation

Updating
--------

Update to Latest Version
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Update from PyPI
   pip install --upgrade koomesh

   # Update from source
   cd KooMeshGenerator
   git pull
   pip install -e . --upgrade

Check for Updates
^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Check current version
   koomesh --version

   # Check latest version on PyPI
   pip index versions koomesh

Uninstalling
------------

.. code-block:: bash

   # Uninstall package
   pip uninstall koomesh

   # Remove configuration files
   rm -rf ~/.koomesh/

   # Remove cache
   rm -rf ~/.cache/koomesh/

Configuration
-------------

First-Time Setup
^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Create config directory
   mkdir -p ~/.koomesh

   # Generate default config
   koomesh config init

   # Edit config
   nano ~/.koomesh/config.yaml

Environment Setup
^^^^^^^^^^^^^^^^^

Add to your ``.bashrc`` or ``.zshrc``:

.. code-block:: bash

   # KooMeshGenerator settings
   export KOOMESH_CONFIG=~/.koomesh/config.yaml
   export KOOMESH_MATERIAL_LIB=~/.koomesh/materials/
   export KOOMESH_LOG_LEVEL=INFO
   export KOOMESH_CACHE_DIR=~/.cache/koomesh/

License Activation
^^^^^^^^^^^^^^^^^^

For enterprise users:

.. code-block:: bash

   # Activate license
   koomesh license activate YOUR_LICENSE_KEY

   # Check license status
   koomesh license status

   # Deactivate
   koomesh license deactivate

Next Steps
----------

After installation:

1. **Quick Start**: :doc:`quickstart`
2. **CLI Reference**: :doc:`cli_reference`
3. **Tutorials**: :doc:`../tutorials/automotive_crash`
4. **Examples**: See ``examples/`` directory

Getting Help
------------

- **Documentation**: https://koomesh.readthedocs.io/
- **Issues**: https://github.com/yourorg/KooMeshGenerator/issues
- **Discussions**: https://github.com/yourorg/KooMeshGenerator/discussions
- **Email**: support@koomesh.dev
