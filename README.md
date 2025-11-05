# KooMeshGenerator

**Automated mesh generation from STEP files with intelligent geometry analysis**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

## Overview

KooMeshGenerator is a comprehensive tool for automatic mesh generation from STEP files with intelligent geometry analysis. It automatically determines the optimal mesh type (hexahedral or tetrahedral) based on geometry classification and outputs LS-DYNA keyword format.

### Key Features

- ✅ **Automatic Geometry Classification**: Analyzes STEP files to determine optimal mesh strategy
- ✅ **Hexahedral Mesh Priority**: Generates structured hex meshes when geometry permits
- ✅ **Tetrahedral Fallback**: Automatically switches to tet mesh for complex geometries
- ✅ **Hybrid Meshing**: Combines hex and tet elements intelligently
- ✅ **Hierarchy-Based Contact**: Automatic contact generation based on assembly structure
- ✅ **LS-DYNA Output**: Direct output to LS-DYNA keyword format
- ✅ **Cross-Platform**: Linux and Windows support

## Architecture

```
STEP File → Geometry Analysis → Mesh Classification → Mesh Generation → LS-DYNA Output
                ↓                       ↓                    ↓
         Hierarchy Parse        Hex/Tet/Hybrid      Contact Generation
```

## Installation

### Prerequisites

- Python 3.9 or higher
- PythonOCC (OpenCASCADE)
- GMSH

### Quick Install

```bash
# Clone the repository
git clone https://github.com/yourorg/KooMeshGenerator.git
cd KooMeshGenerator

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Building PythonOCC and GMSH

See [build/README.md](build/README.md) for detailed instructions on building PythonOCC and GMSH from source.

## Quick Start

### Command Line Interface

```bash
# Generate mesh from STEP file
koomesh generate input.step --mesh-size 1.0

# Analyze STEP structure without meshing
koomesh analyze input.step

# Validate LS-DYNA output file
koomesh validate output.k
```

### Python API

```python
from koomesh.core.pipeline import MeshGenerationPipeline

# Create pipeline
pipeline = MeshGenerationPipeline({})

# Run complete mesh generation
output_file = pipeline.run('model.step', mesh_size=0.5)

print(f"Mesh generated: {output_file}")
```

## Usage

### Basic Mesh Generation

```bash
koomesh generate assembly.step --mesh-size 2.0 -o output.k
```

### Advanced Options

```python
from koomesh.geometry.shape_classifier import ShapeClassifier
from koomesh.io.step_reader import STEPReader

# Read STEP file
reader = STEPReader()
shape = reader.read_file('complex_part.step')

# Classify geometry
classifier = ShapeClassifier()
mesh_type = classifier.classify(shape)

print(f"Recommended mesh type: {mesh_type.value}")
```

## Project Structure

```
KooMeshGenerator/
├── koomesh/                  # Main package
│   ├── core/                 # Core functionality
│   ├── io/                   # Input/Output modules
│   ├── geometry/             # Geometry analysis
│   ├── meshing/              # Mesh generation
│   ├── contact/              # Contact management
│   ├── export/               # LS-DYNA export
│   └── utils/                # Utilities
├── build/                    # Build scripts
│   ├── docker/               # Docker environments
│   ├── scripts/              # Build automation
│   └── cmake/                # CMake configuration
├── tests/                    # Test suite
├── examples/                 # Example scripts
└── docs/                     # Documentation
```

## Development Roadmap

See [PROJECT_MASTER_PLAN.md](PROJECT_MASTER_PLAN.md) for detailed development plan.

- [x] Phase 1: Development environment setup
- [ ] Phase 2: STEP file analysis and hierarchy parsing
- [ ] Phase 3: Mesh generation engine
- [ ] Phase 4: Contact generation
- [ ] Phase 5: LS-DYNA output
- [ ] Phase 6: Automation pipeline
- [ ] Phase 7: Testing and optimization
- [ ] Phase 8: Deployment and documentation

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Citation

If you use KooMeshGenerator in your research, please cite:

```bibtex
@software{koomeshgenerator,
  title = {KooMeshGenerator: Automated Mesh Generation from STEP Files},
  author = {KooMesh Team},
  year = {2025},
  url = {https://github.com/yourorg/KooMeshGenerator}
}
```

## Support

- Documentation: [docs/](docs/)
- Issues: [GitHub Issues](https://github.com/yourorg/KooMeshGenerator/issues)
- Discussions: [GitHub Discussions](https://github.com/yourorg/KooMeshGenerator/discussions)

## Acknowledgments

- OpenCASCADE for geometry kernel
- GMSH for mesh generation
- PythonOCC for Python bindings
