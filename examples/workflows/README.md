# Example Workflows

This directory contains complete workflow examples demonstrating how to use KooMeshGenerator CLI for various meshing tasks.

## Available Workflows

### 1. Simple Part Workflow
**Script:** `01_simple_part_workflow.sh`

Basic workflow for converting a single STEP file to mesh.

**Steps:**
1. Analyze geometry
2. Generate mesh
3. Check quality
4. Create visualization

**Usage:**
```bash
# Edit script to set your input file
vim 01_simple_part_workflow.sh

# Run workflow
bash 01_simple_part_workflow.sh
```

**Best for:**
- Single part meshing
- Learning KooMeshGenerator basics
- Quick mesh generation

---

### 2. Geometry Cleaning Workflow
**Script:** `02_geometry_cleaning_workflow.sh`

Demonstrates how to clean problematic geometry before meshing.

**Steps:**
1. Analyze original geometry
2. Clean geometry (heal, fill gaps, remove small features)
3. Compare before/after
4. Generate mesh from cleaned geometry
5. Quality check

**Usage:**
```bash
bash 02_geometry_cleaning_workflow.sh
```

**Best for:**
- Real-world CAD files with issues
- Geometry with gaps or overlaps
- Improving mesh quality

---

### 3. Batch Processing Workflow
**Script:** `03_batch_processing_workflow.sh`

Process multiple STEP files in parallel.

**Steps:**
1. Setup directories
2. Preview batch operation (dry run)
3. Batch convert all files in parallel
4. Quality check all generated meshes
5. Generate summary

**Usage:**
```bash
# Place STEP files in cad_files/ directory
mkdir -p cad_files
cp *.step cad_files/

# Run batch workflow
bash 03_batch_processing_workflow.sh
```

**Best for:**
- Processing multiple similar parts
- Automated mesh generation
- Production pipelines

---

### 4. Configuration-Based Workflow
**Script:** `04_config_based_workflow.sh`

Use YAML configuration files for complex, repeatable workflows.

**Steps:**
1. Create/use configuration file
2. Validate configuration
3. Preview workflow (dry run)
4. Execute complete workflow
5. Summary

**Usage:**
```bash
# Create config directory
mkdir -p configs

# Copy and customize template
cp ../../templates/crash_analysis.yaml configs/my_config.yaml

# Edit configuration
vim configs/my_config.yaml

# Run workflow
bash 04_config_based_workflow.sh
```

**Best for:**
- Complex meshing workflows
- Repeatable processes
- Team collaboration
- Production environments

---

### 5. Assembly Workflow
**Script:** `05_assembly_workflow.sh`

Complete workflow for multi-part assemblies.

**Steps:**
1. Process all parts from CSV
2. Combine meshes
3. Detect contact zones
4. Quality check assembly
5. Create visualization

**Usage:**
```bash
# Create parts list CSV
cat > parts_list.csv << EOF
id,input_file,output_file,mesh_size,element_type,material
body,cad/body.step,meshes/body.k,2.0,tet4,Steel_HighStrength
chassis,cad/chassis.step,meshes/chassis.k,2.5,tet4,Steel_Mild
EOF

# Run assembly workflow
bash 05_assembly_workflow.sh
```

**Best for:**
- Multi-part assemblies
- Contact detection
- Complete simulation setup

---

## General Tips

### Before Running Workflows

1. **Make scripts executable:**
   ```bash
   chmod +x *.sh
   ```

2. **Check dependencies:**
   ```bash
   koomesh info
   ```

3. **Prepare input files:**
   - STEP files for geometry
   - CSV files for batch processing
   - YAML configs for complex workflows

### Customizing Workflows

All scripts can be customized by editing the configuration variables at the top:

```bash
# Example: Change mesh size
MESH_SIZE=2.0  # Change this value

# Example: Change output directory
OUTPUT_DIR="my_output"  # Customize path
```

### Running in Production

For production use:

1. **Add error handling:**
   ```bash
   set -euo pipefail
   ```

2. **Add logging:**
   ```bash
   exec 1> >(tee -a workflow.log)
   exec 2>&1
   ```

3. **Add notifications:**
   ```bash
   # On success
   echo "Workflow complete" | mail -s "Mesh Job Done" user@example.com
   ```

### Parallel Processing

For batch operations, adjust parallel jobs based on your system:

```bash
# Use all CPU cores
--jobs -1

# Use specific number of cores
--jobs 4

# Disable parallelization (for debugging)
--no-parallel
```

---

## Creating Custom Workflows

### Template for New Workflows

```bash
#!/bin/bash
# My Custom Workflow
# Description of what this workflow does

set -e  # Exit on error

# Configuration
INPUT_FILE="input.step"
OUTPUT_FILE="output.k"

echo "Starting workflow..."

# Step 1
echo "[1/N] Step description..."
koomesh command args
echo ""

# Step 2
echo "[2/N] Step description..."
koomesh command args
echo ""

# Summary
echo "Workflow complete!"
echo "Output: $OUTPUT_FILE"
```

### Best Practices

1. **Use clear variable names**
2. **Add comments explaining each step**
3. **Include error checking**
4. **Print progress messages**
5. **Provide summary at end**
6. **Make configurable (variables at top)**

---

## Integration with Build Systems

### Makefile Example

```makefile
# Makefile
.PHONY: all clean mesh quality

INPUT_FILES := $(wildcard cad/*.step)
MESH_FILES := $(patsubst cad/%.step,meshes/%.k,$(INPUT_FILES))

all: $(MESH_FILES)

meshes/%.k: cad/%.step
	@mkdir -p meshes
	koomesh generate $< --mesh-size 2.0 -o $@

quality: $(MESH_FILES)
	@for mesh in $(MESH_FILES); do \
		koomesh quality check $$mesh --report json -o $$mesh.quality.json; \
	done

clean:
	rm -rf meshes/
```

### CMake Example

```cmake
# Add custom target for mesh generation
add_custom_command(
    OUTPUT ${CMAKE_BINARY_DIR}/mesh.k
    COMMAND koomesh generate ${CMAKE_SOURCE_DIR}/model.step
            --mesh-size 2.0
            -o ${CMAKE_BINARY_DIR}/mesh.k
    DEPENDS ${CMAKE_SOURCE_DIR}/model.step
    COMMENT "Generating mesh from STEP file"
)

add_custom_target(generate_mesh ALL
    DEPENDS ${CMAKE_BINARY_DIR}/mesh.k
)
```

---

## Troubleshooting

### Common Issues

1. **Permission denied:**
   ```bash
   chmod +x workflow.sh
   ```

2. **Command not found:**
   ```bash
   # Ensure KooMeshGenerator is installed
   pip install -e /path/to/KooMeshGenerator
   ```

3. **Files not found:**
   ```bash
   # Check working directory
   pwd
   ls -la
   ```

4. **Workflow fails midway:**
   ```bash
   # Remove set -e to continue on errors
   # Or add error handling for specific commands
   koomesh command args || echo "Warning: command failed"
   ```

---

## Contributing

Have a useful workflow? Share it!

1. Create new workflow script
2. Add to this README
3. Submit pull request

---

**For more information, see:**
- [CLI Usage Guide](../../docs/CLI_GUIDE.md)
- [Configuration Guide](../../templates/README.md)
- [Batch Processing Guide](../batch/README.md)
