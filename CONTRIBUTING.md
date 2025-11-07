# Contributing to KooMeshGenerator

Thank you for your interest in contributing to KooMeshGenerator! This document provides guidelines and instructions for contributing.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Making Changes](#making-changes)
5. [Testing](#testing)
6. [Code Style](#code-style)
7. [Commit Messages](#commit-messages)
8. [Pull Request Process](#pull-request-process)

## Code of Conduct

This project follows a Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Set up the development environment
4. Create a branch for your changes
5. Make your changes
6. Test your changes
7. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.9 or higher
- PythonOCC (optional, for STEP file handling)
- GMSH (optional, for meshing)

### Installation

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/KooMeshGenerator.git
cd KooMeshGenerator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/cli/test_cli_commands.py

# Run with coverage
pytest --cov=koomesh --cov-report=html

# Run only fast tests (skip integration tests)
pytest -m "not integration"
```

## Making Changes

### Branch Naming

Use descriptive branch names:
- `feature/add-new-meshing-algorithm`
- `bugfix/fix-geometry-loader`
- `docs/update-cli-guide`
- `refactor/improve-error-handling`

### Code Organization

```
koomesh/
├── cli/              # CLI commands
├── core/             # Core meshing engine
├── io/               # Input/output
├── geometry/         # Geometry analysis
├── meshing/          # Mesh generation
├── preprocessing/    # Geometry preprocessing
├── utils/            # Utilities
└── config/           # Configuration
```

## Testing

### Test Structure

```
tests/
├── unit/             # Unit tests
├── cli/              # CLI tests
└── integration/      # Integration tests
```

### Writing Tests

```python
# Example test
def test_geometry_analyzer():
    """Test geometry analyzer functionality"""
    from koomesh.preprocessing.geometry_analyzer import GeometryAnalyzer

    analyzer = GeometryAnalyzer()
    # Test implementation
    assert analyzer is not None
```

### Test Coverage

- Aim for >80% code coverage
- All new features must include tests
- Bug fixes should include regression tests

## Code Style

### Python Style Guide

We follow PEP 8 with some modifications:

- Line length: 120 characters
- Use Black for formatting
- Use isort for import sorting

### Formatting

```bash
# Format code with Black
black koomesh tests examples

# Sort imports
isort koomesh tests examples

# Check with flake8
flake8 koomesh

# Type check with mypy
mypy koomesh
```

### Pre-commit Hooks

Pre-commit hooks will automatically check your code:

```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Run specific hook
pre-commit run black --all-files
```

### Documentation

- Add docstrings to all public functions/classes
- Use Google-style docstrings
- Update README.md when adding features
- Update docs/CLI_GUIDE.md for CLI changes

Example docstring:
```python
def analyze_geometry(step_file: str) -> GeometryInfo:
    """
    Analyze STEP file geometry.

    Args:
        step_file: Path to STEP file

    Returns:
        GeometryInfo object with analysis results

    Raises:
        FileNotFoundError: If STEP file doesn't exist
        GeometryLoadError: If geometry cannot be loaded

    Example:
        >>> info = analyze_geometry("part.step")
        >>> print(f"Volume: {info.volume}")
    """
```

## Commit Messages

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, etc.)
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **chore**: Maintenance tasks

### Examples

```
feat(cli): add batch-mesh command for CSV processing

Implement batch-mesh command that reads parameters from CSV/Excel
files and processes multiple parts in parallel.

- Add BatchProcessor class
- Support custom parameters per part
- Add progress tracking
- Closes #123

fix(geometry): handle self-intersecting geometry

Fix crash when loading geometry with self-intersections.
Now raises InvalidGeometryError with helpful suggestion.

Fixes #456
```

## Pull Request Process

### Before Submitting

1. **Update your branch** from main
   ```bash
   git checkout main
   git pull upstream main
   git checkout your-branch
   git rebase main
   ```

2. **Run tests**
   ```bash
   pytest
   ```

3. **Check code style**
   ```bash
   pre-commit run --all-files
   ```

4. **Update documentation** if needed

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] Added new tests
- [ ] Updated existing tests

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests added/updated
- [ ] All tests pass
```

### Review Process

1. Maintainers will review your PR
2. Address feedback if requested
3. Once approved, PR will be merged
4. Your changes will be included in next release

### CI/CD Checks

All PRs must pass:
- ✅ Python tests (3.9, 3.10, 3.11)
- ✅ Code linting (flake8, black, isort)
- ✅ Type checking (mypy)
- ✅ Integration tests
- ✅ Apptainer container build

## Code Review Guidelines

### For Contributors

- Keep PRs focused and small
- Respond to feedback promptly
- Be open to suggestions
- Update PR based on feedback

### For Reviewers

- Be respectful and constructive
- Provide specific, actionable feedback
- Approve when ready
- Suggest improvements, don't demand perfection

## Reporting Bugs

### Bug Report Template

```markdown
**Describe the bug**
Clear description of the bug

**To Reproduce**
Steps to reproduce:
1. Run command '...'
2. With input file '...'
3. See error

**Expected behavior**
What you expected to happen

**Actual behavior**
What actually happened

**Environment:**
- OS: [e.g., Ubuntu 22.04]
- Python version: [e.g., 3.11]
- KooMesh version: [e.g., 1.0.0]

**Additional context**
Any other relevant information
```

## Feature Requests

### Feature Request Template

```markdown
**Feature description**
Clear description of proposed feature

**Use case**
Why is this feature needed?

**Proposed solution**
How should this work?

**Alternatives considered**
Other approaches you've considered

**Additional context**
Any other relevant information
```

## Questions?

- Check the [documentation](docs/CLI_GUIDE.md)
- Search [existing issues](https://github.com/yourorg/KooMeshGenerator/issues)
- Ask in [discussions](https://github.com/yourorg/KooMeshGenerator/discussions)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to KooMeshGenerator!** 🎉
