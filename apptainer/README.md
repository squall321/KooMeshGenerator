# KooMesh Apptainer Container

Apptainer/Singularity container for KooMeshGenerator - automated mesh generation from STEP files.

## Quick Start

### 1. Install Apptainer

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y apptainer
```

**RHEL/CentOS:**
```bash
sudo yum install -y apptainer
```

**From source:**
```bash
# See https://apptainer.org/docs/admin/main/installation.html
```

### 2. Clone Repository

```bash
git clone https://github.com/yourrepo/KooMeshGenerator.git
cd KooMeshGenerator
```

### 3. Build Container

```bash
./apptainer/build.sh
```

This creates `koomesh.sif` (~800 MB) in the project root.

**Build time:** 10-20 minutes (first time)

### 4. Use Container

```bash
# Generate mesh from STEP file
apptainer run koomesh.sif generate model.step -s 2.0 -o output.k

# Batch processing
apptainer run koomesh.sif batch input_dir/ output_dir/ -s 1.0 -w 4

# Interactive shell
apptainer shell koomesh.sif

# Run tests
apptainer exec koomesh.sif python3 -m pytest tests/
```

## Included Software

- **Ubuntu 22.04** base
- **Python 3.10+** with scientific stack
- **GMSH 4.15** - mesh generation
- **CadQuery 2.6** - CAD operations
- **NumPy, SciPy** - numerical computing
- **KooMesh** - our mesh generation system

## Usage Examples

### Example 1: Single File

```bash
# Create STEP file (using CadQuery inside container)
apptainer exec koomesh.sif python3 << EOF
import cadquery as cq
box = cq.Workplane('XY').box(100, 50, 20)
box.val().exportStep('test_box.step')
EOF

# Generate mesh
apptainer run koomesh.sif generate test_box.step -s 5.0 -o box.k

# Check output
ls -lh box.k
```

### Example 2: Batch Processing

```bash
# Process all STEP files in directory
apptainer run koomesh.sif batch step_models/ lsdyna_output/ -s 2.0 -w 8 --recursive
```

### Example 3: Custom Python Script

```bash
apptainer exec koomesh.sif python3 << 'EOF'
from koomesh.meshing.mesh_data import create_structured_box_mesh
from koomesh.export.lsdyna_writer import LSDynaWriter
from koomesh.io.hierarchy_parser import HierarchyNode

# Create mesh
mesh = create_structured_box_mesh(100, 100, 100, 10, 10, 10)
print(f"Generated: {mesh.num_nodes()} nodes, {mesh.num_elements()} elements")

# Export
root = HierarchyNode(name='Box', level=0)
with LSDynaWriter('custom.k') as writer:
    writer.write_complete_model([mesh], [], root)

print("Exported to custom.k")
EOF
```

### Example 4: Quality Analysis

```bash
apptainer exec koomesh.sif python3 << 'EOF'
from koomesh.meshing.mesh_data import create_structured_box_mesh
from koomesh.meshing.quality_checker import QualityChecker

mesh = create_structured_box_mesh(100, 100, 100, 5, 5, 5)
checker = QualityChecker()
report = checker.check_mesh(mesh)

print(f"Mesh Quality Report:")
print(f"  Elements: {report.num_elements}")
print(f"  Min Jacobian: {report.jacobian['min']:.3f}")
print(f"  Max Jacobian: {report.jacobian['max']:.3f}")
print(f"  Bad elements: {report.num_bad_elements}")
EOF
```

## File Binding

Apptainer automatically binds your home directory and current working directory.

**Manual binding:**
```bash
# Bind specific directories
apptainer run --bind /scratch:/scratch koomesh.sif generate /scratch/model.step -s 2.0

# Bind with different mount point
apptainer run --bind /data:/mnt koomesh.sif generate /mnt/model.step -s 2.0
```

## HPC Usage

### SLURM Example

```bash
#!/bin/bash
#SBATCH --job-name=koomesh
#SBATCH --nodes=1
#SBATCH --ntasks=8
#SBATCH --time=01:00:00

module load apptainer

# Process batch
apptainer run koomesh.sif batch input/ output/ -s 2.0 -w 8
```

### PBS Example

```bash
#!/bin/bash
#PBS -N koomesh
#PBS -l nodes=1:ppn=8
#PBS -l walltime=01:00:00

cd $PBS_O_WORKDIR
module load singularity

apptainer run koomesh.sif batch input/ output/ -s 2.0 -w 8
```

## Development

### Update Code and Rebuild

```bash
# Update source
git pull

# Rebuild container
./apptainer/build.sh

# Quick test
apptainer run koomesh.sif --version
```

### Run Tests Inside Container

```bash
# Unit tests
apptainer exec koomesh.sif python3 -m pytest tests/unit/ -v

# Integration tests
apptainer exec koomesh.sif python3 -m pytest tests/integration/ -v

# All tests
apptainer exec koomesh.sif python3 -m pytest tests/ -v
```

### Interactive Development

```bash
# Open shell
apptainer shell koomesh.sif

# Inside container
Apptainer> cd /opt/KooMeshGenerator
Apptainer> python3 -m pytest tests/
Apptainer> python3 -c "from koomesh.config import KooMeshConfig; print('OK')"
```

## Troubleshooting

### Build fails with "permission denied"

```bash
# Try with sudo
sudo ./apptainer/build.sh
```

### "command not found: apptainer"

Install Apptainer first (see Quick Start step 1)

### Container runs but imports fail

```bash
# Check if KooMesh is installed
apptainer exec koomesh.sif python3 -c "import koomesh; print(koomesh.__version__)"

# Check Python path
apptainer exec koomesh.sif python3 -c "import sys; print(sys.path)"

# Rebuild if needed
./apptainer/build.sh
```

### GMSH errors

```bash
# Check if GMSH is installed
apptainer exec koomesh.sif python3 -c "import gmsh; print(gmsh.__version__)"

# Check OpenGL libraries
apptainer exec koomesh.sif ldd /usr/local/lib/python3.*/dist-packages/gmsh*.so
```

### Files not accessible

```bash
# Apptainer binds $HOME and $PWD by default
# For other directories, use --bind:
apptainer run --bind /data:/data koomesh.sif generate /data/model.step -s 2.0
```

## Performance Tips

1. **Use --bind for large datasets** instead of copying into container
2. **Adjust worker count** with `-w N` for batch processing
3. **Use local scratch space** in HPC environments
4. **Pre-compile Python** with `python3 -m compileall` inside container

## Container Specifications

| Item | Specification |
|------|---------------|
| Base OS | Ubuntu 22.04 |
| Size | ~800 MB |
| Python | 3.10+ |
| GMSH | 4.15.0 |
| CadQuery | 2.6.1 |
| Build Time | 10-20 min |

## Support

- **Documentation**: See main README.md
- **Issues**: GitHub Issues
- **Examples**: See `examples/` directory

## License

Same as KooMeshGenerator project license.
