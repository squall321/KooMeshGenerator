# Batch Processing Examples

This directory contains examples for batch processing multiple mesh generation jobs.

## Overview

KooMeshGenerator supports two batch processing modes:

1. **Glob Pattern Mode** (`batch-convert`): Process multiple files matching a pattern
2. **Parameter File Mode** (`batch-mesh`): Process files with individual parameters from CSV/Excel

## Examples

### Example 1: Simple Batch Convert

Convert all STEP files in a directory with the same settings:

```bash
# Convert all STEP files in input/ directory
koomesh batch-convert "input/*.step" --output-dir meshes/

# With custom mesh size
koomesh batch-convert "input/*.step" \
  --output-dir meshes/ \
  --mesh-size 1.5

# Recursive search
koomesh batch-convert "cad/**/*.step" --output-dir output/

# Parallel processing with 8 workers
koomesh batch-convert "input/*.step" \
  --output-dir meshes/ \
  --parallel \
  --jobs 8
```

### Example 2: Batch from CSV

Process files with different parameters for each file:

```bash
# Process from simple CSV
koomesh batch-mesh parts_list_simple.csv

# Process with parallel execution
koomesh batch-mesh automotive_parts.csv \
  --parallel \
  --jobs 8

# Dry run to preview jobs
koomesh batch-mesh automotive_parts.csv --dry-run

# With retry logic and result logging
koomesh batch-mesh automotive_parts.csv \
  --max-retries 5 \
  --save-results results.csv
```

### Example 3: Batch from Excel

Process files from Excel spreadsheet:

```bash
# Process from first sheet
koomesh batch-mesh parts.xlsx

# Process from specific sheet
koomesh batch-mesh parts.xlsx --sheet "Parts List"

# Process with sheet index
koomesh batch-mesh parts.xlsx --sheet 1
```

## CSV File Format

### Simple Format (`parts_list_simple.csv`)

Minimal CSV with just input/output and common parameters:

```csv
id,input_file,output_file,mesh_size,element_type
part_001,input/part1.step,output/part1.k,2.0,tet4
part_002,input/part2.step,output/part2.k,2.0,tet4
part_003,input/part3.step,output/part3.k,2.0,tet4
```

**Required columns:**
- `input_file`: Input STEP file path
- `output_file`: Output mesh file path

**Optional columns:**
- `id`: Job identifier (auto-generated if not provided)
- `mesh_size`: Target mesh element size
- `element_type`: Element type (tet4, hex8, auto)
- Any other parameter you want to pass

### Advanced Format (`automotive_parts.csv`)

CSV with material assignments and quality thresholds:

```csv
id,input_file,output_file,mesh_size,element_type,material,quality_threshold
body_01,cad/body_front.step,meshes/body_front.k,2.0,tet4,Steel_HighStrength,5.0
chassis_01,cad/chassis.step,meshes/chassis.k,2.5,tet4,Steel_Mild,6.0
bumper,cad/bumper.step,meshes/bumper.k,1.5,tet4,Aluminum_6061_T6,4.0
```

**Custom parameters:**
- `material`: Material name for assignment
- `quality_threshold`: Quality threshold for this part
- Add any custom columns you need

## Excel File Format

Excel files follow the same format as CSV, but you can:
- Use multiple sheets
- Have formatted headers
- Include notes/comments in separate columns

Example structure:
```
Sheet: "Parts List"
A         B              C                  D          E
id        input_file     output_file        mesh_size  element_type
part_001  input/p1.step  output/p1.k        2.0        tet4
part_002  input/p2.step  output/p2.k        1.5        tet4
```

## Features

### 1. Parallel Processing

Process multiple files simultaneously:

```bash
# Use all available cores
koomesh batch-convert "input/*.step" --output-dir meshes/ --parallel

# Use specific number of workers
koomesh batch-convert "input/*.step" \
  --output-dir meshes/ \
  --parallel \
  --jobs 4
```

**Performance tips:**
- For small files (<1000 elements): Use sequential mode
- For large files (>10000 elements): Use parallel with n_jobs = CPU cores - 1
- Balance: n_jobs = -2 (all cores except one)

### 2. Progress Tracking

Automatic progress bars show:
- Current job being processed
- Percentage complete
- Estimated time remaining
- Processing speed (jobs/second)

```bash
Processing jobs: 100%|████████████| 50/50 [02:30<00:00, 3.00s/job]
```

### 3. Error Recovery and Retry

Automatic retry for failed jobs:

```bash
# Default: 3 retry attempts
koomesh batch-mesh parts.csv

# Custom retry count
koomesh batch-mesh parts.csv --max-retries 5

# No retries (fail fast)
koomesh batch-mesh parts.csv --max-retries 0
```

**Retry behavior:**
- Failed jobs are automatically retried
- 1 second delay between retries
- Error messages logged for debugging
- Final status report shows all failures

### 4. Result Logging

Save batch results to CSV for analysis:

```bash
koomesh batch-mesh parts.csv --save-results results.csv
```

**Results CSV contains:**
- Job ID and status (completed/failed)
- Input/output file paths
- Error messages (if failed)
- Number of retries
- Processing duration
- All job parameters

Example `results.csv`:
```csv
id,input_file,output_file,status,error,retries,duration,mesh_size,element_type
part_001,input/p1.step,output/p1.k,completed,,0,12.5,2.0,tet4
part_002,input/p2.step,output/p2.k,failed,File not found,3,2.1,2.0,tet4
part_003,input/p3.step,output/p3.k,completed,,1,15.2,2.0,tet4
```

### 5. Dry Run Mode

Preview jobs without executing:

```bash
koomesh batch-mesh parts.csv --dry-run
```

Output shows:
- Total number of jobs
- Preview of first 5 jobs
- All parameters for each job
- No actual execution

## Common Workflows

### Workflow 1: Simple Batch Convert

```bash
#!/bin/bash
# batch_convert_simple.sh

# Convert all STEP files with default settings
koomesh batch-convert "input/*.step" \
  --output-dir output/ \
  --mesh-size 2.0 \
  --parallel \
  --jobs 8 \
  --save-results batch_results.csv

echo "Done! Check batch_results.csv for details"
```

### Workflow 2: Parametric Batch

```bash
#!/bin/bash
# batch_parametric.sh

# Create CSV with parameters
cat > parts.csv << EOF
id,input_file,output_file,mesh_size
fine,input/critical.step,output/critical.k,0.5
medium,input/body.step,output/body.k,2.0
coarse,input/base.step,output/base.k,5.0
EOF

# Process with retries
koomesh batch-mesh parts.csv \
  --parallel \
  --max-retries 5 \
  --save-results results.csv

# Check results
echo "Success rate:"
python -c "
import pandas as pd
df = pd.read_csv('results.csv')
success = (df['status'] == 'completed').sum()
total = len(df)
print(f'{success}/{total} ({success/total*100:.1f}%)')
"
```

### Workflow 3: Assembly Processing

```bash
#!/bin/bash
# batch_assembly.sh

# Process multiple assemblies
koomesh batch-mesh assembly_list.csv \
  --parallel \
  --jobs 4 \
  --save-results assembly_results.csv

# Generate quality reports for each
while IFS=, read -r id input output rest; do
  if [ -f "$output" ]; then
    koomesh quality "$output" \
      --report html \
      --output "reports/${id}_quality.html"
  fi
done < assembly_results.csv
```

## Tips and Best Practices

### 1. File Organization

Organize files for efficient batch processing:

```
project/
├── input/           # All STEP files
├── output/          # Generated meshes
├── reports/         # Quality reports
├── batch/
│   ├── parts.csv    # Parameter files
│   └── results.csv  # Result logs
└── scripts/
    └── batch.sh     # Batch scripts
```

### 2. Parameter Selection

**Mesh size guidelines:**
- Fine detail parts: 0.5 - 1.0
- Standard parts: 1.5 - 3.0
- Large/coarse parts: 3.0 - 10.0

**Element type:**
- `auto`: Let system decide (recommended)
- `tet4`: General purpose, reliable
- `hex8`: Better quality, limited geometry support

### 3. Parallel Processing

**When to use parallel:**
- ✅ Multiple large files (>5000 elements)
- ✅ Long processing time per file (>10 seconds)
- ✅ 4+ CPU cores available

**When to avoid parallel:**
- ❌ Small files (<1000 elements)
- ❌ Few files (<5 total)
- ❌ Limited memory

### 4. Error Handling

**Common errors and solutions:**

1. **File not found**: Check paths in CSV are correct
   ```bash
   # Use absolute paths or paths relative to working directory
   input_file,output_file
   /full/path/to/input.step,/full/path/to/output.k
   ```

2. **Out of memory**: Reduce parallel workers
   ```bash
   --jobs 2  # Instead of --jobs 8
   ```

3. **Permission denied**: Check output directory permissions
   ```bash
   mkdir -p output && chmod 755 output
   ```

### 5. Performance Optimization

**For best performance:**

1. **Use SSD storage** for input/output files
2. **Batch size**: Process 10-50 files at once (not thousands)
3. **Memory**: Allocate 2-4 GB RAM per worker
4. **CPU**: Use n_jobs = CPU cores - 1 for best balance

## Troubleshooting

### Issue: Slow parallel processing

**Solution**: Check if parallel overhead is too high
```bash
# Test with sequential first
koomesh batch-mesh parts.csv

# Then try parallel
koomesh batch-mesh parts.csv --parallel --jobs 4

# Compare timings
```

### Issue: Jobs failing randomly

**Solution**: Increase retry count and check logs
```bash
koomesh batch-mesh parts.csv \
  --max-retries 10 \
  --save-results results.csv \
  --verbose

# Check failed jobs in results.csv
```

### Issue: CSV encoding errors

**Solution**: Save CSV as UTF-8
```python
# In Excel: Save As → CSV UTF-8
# In Python:
df.to_csv('parts.csv', encoding='utf-8', index=False)
```

## Need Help?

- Run `koomesh batch-convert --help` for command options
- Run `koomesh batch-mesh --help` for parameter file options
- Check examples in this directory
- See main documentation in `docs/`
