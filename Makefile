.PHONY: help install install-dev test lint format type-check clean docs build publish

help:
	@echo "KooMeshGenerator Development Commands"
	@echo "======================================"
	@echo "make install          - Install package in production mode"
	@echo "make install-dev      - Install package in development mode with all dev dependencies"
	@echo "make test             - Run test suite with coverage"
	@echo "make test-fast        - Run tests without coverage (faster)"
	@echo "make lint             - Run all linters (flake8, pylint)"
	@echo "make format           - Format code with black and isort"
	@echo "make format-check     - Check code formatting without modifying"
	@echo "make type-check       - Run mypy type checking"
	@echo "make security         - Run security checks (bandit, safety)"
	@echo "make clean            - Remove build artifacts and cache files"
	@echo "make docs             - Build documentation"
	@echo "make docs-serve       - Build and serve documentation locally"
	@echo "make build            - Build distribution packages"
	@echo "make publish          - Publish to PyPI (requires credentials)"
	@echo "make pre-commit       - Install pre-commit hooks"
	@echo "make all              - Run format, lint, type-check, and test"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"
	pip install -r requirements-dev.txt

test:
	pytest tests/ -v --cov=koomesh --cov-report=term-missing --cov-report=html --cov-report=xml

test-fast:
	pytest tests/ -v

test-watch:
	pytest-watch -- tests/ -v

lint:
	@echo "Running flake8..."
	flake8 koomesh/ tests/ --max-line-length=100 --extend-ignore=E203,W503
	@echo "Running pylint..."
	pylint koomesh/ --max-line-length=100 --disable=C0111,R0903,R0913

format:
	@echo "Running isort..."
	isort koomesh/ tests/ --profile=black --line-length=100
	@echo "Running black..."
	black koomesh/ tests/ --line-length=100

format-check:
	@echo "Checking isort..."
	isort koomesh/ tests/ --check-only --profile=black --line-length=100
	@echo "Checking black..."
	black koomesh/ tests/ --check --line-length=100

type-check:
	mypy koomesh/ --ignore-missing-imports

security:
	@echo "Running bandit..."
	bandit -r koomesh/ -ll
	@echo "Running safety..."
	safety check --json

clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/ dist/ *.egg-info
	@echo "Cleaning Python cache files..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	@echo "Cleaning test artifacts..."
	rm -rf .pytest_cache/ .coverage htmlcov/ coverage.xml
	@echo "Cleaning mypy cache..."
	rm -rf .mypy_cache/
	@echo "Cleaning documentation build..."
	rm -rf docs/_build/

docs:
	cd docs && make html

docs-serve:
	cd docs && make html && python -m http.server 8000 --directory _build/html

build: clean
	python -m build

publish: build
	twine upload dist/*

pre-commit:
	pre-commit install

all: format lint type-check test
	@echo "All checks passed!"

# Development workflow shortcuts
dev-setup: install-dev pre-commit
	@echo "Development environment ready!"

quick-check: format-check lint test-fast
	@echo "Quick checks passed!"
