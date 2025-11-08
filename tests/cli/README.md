# CLI Tests

This directory contains tests for the KooMeshGenerator CLI.

## Test Organization

- `test_cli_commands.py` - Tests for all CLI commands
- `test_config_system.py` - Tests for YAML configuration system
- `test_batch_processing.py` - Tests for batch processing functionality
- `test_integration.py` - Integration tests for complete workflows

## Running Tests

### Install Test Dependencies

```bash
pip install pytest pytest-cov
```

### Run All CLI Tests

```bash
# From project root
pytest tests/cli/ -v

# With coverage
pytest tests/cli/ --cov=koomesh.cli --cov-report=html

# Run specific test file
pytest tests/cli/test_cli_commands.py -v

# Run specific test class
pytest tests/cli/test_cli_commands.py::TestCLIBasics -v

# Run specific test
pytest tests/cli/test_cli_commands.py::TestCLIBasics::test_cli_help -v
```

### Run Integration Tests Only

```bash
pytest tests/cli/test_integration.py -v -m integration
```

### Test Coverage

```bash
# Generate coverage report
pytest tests/cli/ --cov=koomesh.cli --cov-report=html

# View report
open htmlcov/index.html
```

## Writing New Tests

### Test Structure

```python
import pytest
from click.testing import CliRunner
from koomesh.cli.main import cli

class TestNewFeature:
    """Test new feature"""

    def test_feature_help(self):
        """Test feature help output"""
        runner = CliRunner()
        result = runner.invoke(cli, ['feature', '--help'])
        assert result.exit_code == 0
        assert 'expected text' in result.output

    def test_feature_execution(self):
        """Test feature execution"""
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Test code here
            result = runner.invoke(cli, ['feature', 'args'])
            assert result.exit_code == 0
```

### Best Practices

1. **Use Click's CliRunner** for testing CLI commands
2. **Use isolated_filesystem()** for tests that create files
3. **Test both success and failure cases**
4. **Check exit codes** (0 for success, non-zero for errors)
5. **Verify output** contains expected messages
6. **Test edge cases** (missing files, invalid input, etc.)

## CI/CD Integration

### GitHub Actions

```yaml
name: CLI Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Run CLI tests
        run: pytest tests/cli/ -v --cov=koomesh.cli
```

## Test Results

Expected test results:

- **test_cli_commands.py**: ~30 tests (all CLI command help and basic functionality)
- **test_config_system.py**: ~20 tests (config loading, validation, overrides)
- **test_batch_processing.py**: ~15 tests (batch processing, CSV parsing, parallel execution)
- **test_integration.py**: ~10 tests (end-to-end workflows)

**Total**: ~75 CLI tests

## Troubleshooting

### Tests Failing

1. **Import errors**: Ensure KooMeshGenerator is installed (`pip install -e .`)
2. **File not found**: Use `isolated_filesystem()` or proper path handling
3. **Command not registered**: Check command is added in `main.py`

### Slow Tests

Integration tests may be slower due to actual command execution. Use markers to skip:

```bash
# Skip slow tests
pytest tests/cli/ -v -m "not integration"
```

## Contributing

When adding new CLI features:

1. Add tests in appropriate test file
2. Test both help output and execution
3. Include error cases
4. Update this README if needed
5. Ensure all tests pass before committing
