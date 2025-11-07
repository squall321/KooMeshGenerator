# KooMeshGenerator

**Automated mesh generation from STEP files with intelligent geometry analysis**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

---

## 🚀 Next Session? START HERE!

**📌 다음 세션 시작 가이드 (3개 중 하나 선택)**:

1. **[NEXT_SESSION.md](NEXT_SESSION.md)** ⭐ **가장 추천!**
   - 모든 문서 인덱스 + 빠른 시작 가이드
   - 5개 문서 설명 및 찾는 방법
   - Day 2 작업 미리보기

2. **[START_HERE.md](START_HERE.md)** ⭐ 빠른 시작
   - 30초 빠른 시작 가이드
   - Day 2 작업 상세 (코드 예제)

3. **[SESSION_SUMMARY.md](SESSION_SUMMARY.md)** 📚 완전 참조
   - Week 1-3 전체 계획
   - 모든 코드 예제

**Current Status**:
- ✅ Day 1 Complete (Pipeline Foundation)
- ⏳ Day 2 Next (Geometry Processing)
- 📊 Progress: 4.8% (1/21 days)

---

## Overview

KooMeshGenerator is a comprehensive tool for automatic mesh generation from STEP files with intelligent geometry analysis. It automatically determines the optimal mesh type (hexahedral or tetrahedral) based on geometry classification and outputs LS-DYNA keyword format.

### Key Features

#### Core Meshing
- ✅ **Automatic Geometry Classification**: Analyzes STEP files to determine optimal mesh strategy
- ✅ **Hexahedral Mesh Priority**: Generates structured hex meshes when geometry permits
- ✅ **Tetrahedral Fallback**: Automatically switches to tet mesh for complex geometries
- ✅ **Hybrid Meshing**: Combines hex and tet elements intelligently
- ✅ **Boundary Layer Meshing**: Generate boundary layers for CFD applications
- ✅ **Mesh Coarsening**: Reduce mesh density using vertex clustering algorithms

#### Mesh Utilities
- ✅ **Mesh Copy & Merge**: Copy meshes and merge multiple meshes with tolerance-based deduplication
- ✅ **Mesh Transformation**: Translate, scale, rotate, and mirror mesh geometries
- ✅ **Mesh Repair**: Fix degenerate elements and quality issues
- ✅ **Mesh Partitioning**: Partition meshes for parallel computation

#### Contact & Analysis
- ✅ **Contact Surface Detection**: Automatically detect contact surfaces between parts
- ✅ **Hierarchy-Based Contact**: Automatic contact generation based on assembly structure
- ✅ **Quality Metrics**: Comprehensive mesh quality analysis with 6+ metrics
- ✅ **Auto-Remeshing**: Quality-driven automatic refinement with 5 strategies

#### Format Support
- ✅ **LS-DYNA Output**: Direct output to LS-DYNA keyword format
- ✅ **Multi-Format Export**: VTK, Abaqus INP, Nastran BDF, STL, PLY, OBJ
- ✅ **Format Conversion**: Convert between different mesh formats
- ✅ **Cross-Platform**: Linux and Windows support

#### Production Features (Phase 4)
- ✅ **Enhanced Error Handling**: 14 custom exception classes with helpful suggestions
- ✅ **Performance Optimization**: Caching system, streaming processor, benchmarking
- ✅ **Material Database**: 74+ engineering materials across 13 categories
- ✅ **Simulation Templates**: 21+ industry-specific templates (automotive, aerospace, biomedical, etc.)
- ✅ **Template Validation**: Comprehensive validation with physics-based rules
- ✅ **CI/CD Pipeline**: Automated testing with GitHub Actions and Apptainer
- ✅ **Quality-Driven Remeshing**: Automatic refinement based on Jacobian, aspect ratio, skewness

## Architecture

```
STEP File → Geometry Analysis → Mesh Classification → Mesh Generation → LS-DYNA Output
                ↓                       ↓                    ↓
         Hierarchy Parse        Hex/Tet/Hybrid      Contact Generation
```

## Installation

### Option 1: Apptainer/Singularity (Recommended for HPC)

**Fastest way to get started - zero configuration needed!**

```bash
# Clone the repository
git clone https://github.com/yourorg/KooMeshGenerator.git
cd KooMeshGenerator

# Build container (one-time, 10-20 minutes)
./apptainer/build.sh

# Use immediately
apptainer run koomesh.sif generate model.step -s 2.0 -o output.k
```

See [apptainer/README.md](apptainer/README.md) for detailed usage.

### Option 2: Manual Installation

**Prerequisites:**
- Python 3.9 or higher
- PythonOCC (OpenCASCADE)
- GMSH

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
koomesh generate input.step --mesh-size 2.0 -o output.k

# Analyze geometry
koomesh geometry info input.step

# Check mesh quality
koomesh quality check output.k --report html

# Batch process multiple files
koomesh batch-convert "cad/*.step" --output-dir meshes/ --mesh-size 2.0

# Run workflow from config
koomesh run workflow.yaml
```

See [CLI Usage Guide](docs/CLI_GUIDE.md) for complete documentation.

### Python API

```python
from koomesh.core.pipeline import MeshGenerationPipeline

# Create pipeline
pipeline = MeshGenerationPipeline({})

# Run complete mesh generation
output_file = pipeline.run('model.step', mesh_size=0.5)

print(f"Mesh generated: {output_file}")
```

## CLI Features

KooMeshGenerator provides a comprehensive command-line interface with the following capabilities:

### Core Commands

- **`koomesh generate`** - Generate mesh from STEP file with automatic geometry analysis
- **`koomesh analyze`** - Analyze STEP file structure and geometry
- **`koomesh batch`** - Batch process multiple files in parallel

### New CLI Features (Phase 3)

- **`koomesh run`** - Execute complete workflows from YAML configuration files
- **`koomesh batch-convert`** - Batch convert using glob patterns
- **`koomesh batch-mesh`** - Batch process from CSV/Excel with custom parameters
- **`koomesh geometry`** - Geometry preprocessing tools (info, clean, compare, simplify)
- **`koomesh quality`** - Mesh quality checking and reporting
- **`koomesh contact`** - Contact zone detection and export
- **`koomesh material`** - Material library management
- **`koomesh visualize`** - Mesh visualization and screenshots

### Quick Examples

```bash
# Configuration-based workflow
koomesh run crash_analysis.yaml --override meshing.mesh_size=1.5

# Clean problematic geometry
koomesh geometry clean input.step --output cleaned.step --heal-surfaces

# Batch process with parameters
koomesh batch-mesh parts_list.csv --parallel --jobs 8

# Quality check with HTML report
koomesh quality check mesh.k --report html -o report.html

# Detect contacts
koomesh contact detect assembly.k --tolerance 0.1 --export lsdyna
```

### Documentation & Examples

- **[Complete CLI Guide](docs/CLI_GUIDE.md)** - Comprehensive command reference
- **[Example Workflows](examples/workflows/)** - Ready-to-use workflow scripts
- **[Batch Processing Guide](examples/batch/README.md)** - Batch processing examples
- **[Configuration Templates](templates/)** - YAML config templates for common scenarios

## Usage

### Basic Mesh Generation

```bash
koomesh generate assembly.step --mesh-size 2.0 -o output.k
```

### Advanced Options

#### Mesh Coarsening
```python
from koomesh.meshing.tet_mesher import TetMesher

# Coarsen an existing mesh
mesher = TetMesher()
coarsened_mesh = mesher.coarsen_mesh(mesh, coarsening_factor=0.5)
# Factor 0.5 = approximately half as many elements
```

#### Mesh Utilities
```python
from koomesh.utils.mesh_copy import copy_mesh
from koomesh.utils.mesh_merge import merge_meshes, merge_meshes_with_tolerance
from koomesh.utils.mesh_transform import translate_mesh, scale_mesh

# Copy mesh
mesh_copy = copy_mesh(original_mesh)

# Merge multiple meshes
merged = merge_meshes([mesh1, mesh2, mesh3])

# Merge with tolerance (eliminates duplicate nodes)
merged = merge_meshes_with_tolerance([mesh1, mesh2], tolerance=1e-6)

# Transform mesh
translate_mesh(mesh, dx=10.0, dy=5.0)
scale_mesh(mesh, sx=2.0, sy=2.0, sz=2.0)
```

#### Contact Surface Detection
```python
from koomesh.utils.contact_detection import ContactSurfaceDetector

# Detect contact surfaces between parts
detector = ContactSurfaceDetector()
contacts = detector.detect_contacts(mesh, tolerance=0.1)

# Export contact definitions
detector.export_contact_pairs(contacts, "contacts.inp", format="abaqus")
```

#### Format Conversion
```python
from koomesh.io.format_converter import MeshFormatConverter

# Convert between formats
converter = MeshFormatConverter()
converter.export_vtk(mesh, "output.vtk")
converter.export_abaqus(mesh, "output.inp")
converter.export_nastran(mesh, "output.bdf")

# Import from VTK
mesh = converter.import_from_vtk("input.vtk")
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
