# Testing Guide - SprintForge Backend

Comprehensive testing guide for SprintForge backend with troubleshooting and best practices.

## Table of Contents
- [Quick Start](#quick-start)
- [Environment Setup](#environment-setup)
- [Running Tests](#running-tests)
- [Troubleshooting](#troubleshooting)
- [Writing Tests](#writing-tests)
- [CI/CD Integration](#cicd-integration)

## Quick Start

**TL;DR**: Always use `uv run pytest` instead of plain `pytest`.

```bash
# Install uv (one-time setup)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
cd backend
uv pip install -r requirements.txt

# Run tests
uv run pytest
```

## Environment Setup

### Why `uv`?

This project uses **`uv`** ([astral.sh/uv](https://github.com/astral-sh/uv)) for Python package management because:

1. **Fast**: 10-100x faster than pip
2. **Reliable**: Deterministic dependency resolution
3. **Modern**: Built in Rust, designed for modern Python workflows
4. **Compatible**: Drop-in replacement for pip/venv

### Installation

#### Linux/macOS
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Windows (PowerShell)
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### Alternative: pipx
```bash
pipx install uv
```

### Verify Installation

```bash
uv --version
# Should show: uv 0.x.x or higher
```

### Project Setup

```bash
# Navigate to backend directory
cd /path/to/sprintforge/backend

# Install all dependencies
uv pip install -r requirements.txt

# Verify installation
uv run pytest --version
# Should show: pytest 7.4.3 or higher
```

## Running Tests

### Basic Commands

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run with very verbose output (shows test names during execution)
uv run pytest -vv

# Run tests and stop at first failure
uv run pytest -x

# Run tests and show local variables on failure
uv run pytest -l
```

### Test Discovery

```bash
# Run specific test file
uv run pytest tests/services/test_scheduler.py

# Run specific test class
uv run pytest tests/services/test_scheduler.py::TestTaskGraph

# Run specific test method
uv run pytest tests/services/test_scheduler.py::TestTaskGraph::test_add_node

# Run tests matching pattern
uv run pytest -k "scheduler"
uv run pytest -k "test_add"
```

### Test Categories

```bash
# Run tests by directory
uv run pytest tests/api/              # API tests only
uv run pytest tests/services/         # Service layer tests
uv run pytest tests/excel/            # Excel generation tests
uv run pytest tests/integration/      # Integration tests

# Run tests by marker
uv run pytest -m unit                 # Unit tests only
uv run pytest -m integration          # Integration tests only
uv run pytest -m "not slow"           # Skip slow tests
```

### Coverage Reports

```bash
# Run with coverage (terminal report)
uv run pytest --cov=app tests/ --cov-report=term-missing

# Generate HTML coverage report
uv run pytest --cov=app tests/ --cov-report=html
# Then open: htmlcov/index.html

# Coverage for specific module
uv run pytest --cov=app.services.scheduler tests/services/scheduler/

# Show lines missing coverage
uv run pytest --cov=app tests/ --cov-report=term-missing

# Fail if coverage below threshold
uv run pytest --cov=app tests/ --cov-fail-under=85
```

### Performance Testing

```bash
# Show slowest tests
uv run pytest --durations=10

# Show all test durations
uv run pytest --durations=0

# Run tests in parallel (requires pytest-xdist)
uv run pytest -n auto              # Auto-detect CPU count
uv run pytest -n 4                 # Use 4 workers
```

### Output Control

```bash
# Quiet output (minimal)
uv run pytest -q

# Show print statements
uv run pytest -s

# Show full diff on assertion failures
uv run pytest -vv

# Capture output (default, can be disabled with -s)
uv run pytest --capture=no
```

## Troubleshooting

### ❌ Error: `ModuleNotFoundError: No module named 'openpyxl'`

**Cause**: Running `pytest` directly instead of `uv run pytest`

**Solution**:
```bash
# WRONG ❌
pytest
pytest tests/

# CORRECT ✅
uv run pytest
uv run pytest tests/
```

**Explanation**: Direct `pytest` uses your system Python, which doesn't have project dependencies. `uv run pytest` uses the uv-managed environment with all packages installed.

---

### ❌ Error: `ModuleNotFoundError: No module named 'app'`

**Cause**: Running tests from wrong directory or PYTHONPATH not set

**Solution**:
```bash
# Always run from backend directory
cd /path/to/sprintforge/backend
uv run pytest
```

If still failing:
```bash
# Set PYTHONPATH explicitly
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
uv run pytest
```

---

### ❌ Error: `ImportError: cannot import name 'X' from 'app.Y'`

**Possible Causes**:
1. Stale `__pycache__` files
2. Dependencies not installed
3. Circular imports

**Solutions**:

```bash
# 1. Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete

# 2. Reinstall dependencies
uv pip install -r requirements.txt --force-reinstall

# 3. Check for circular imports
uv run pytest --tb=short
```

---

### ❌ Error: Tests fail with database connection errors

**Cause**: PostgreSQL not running or configured incorrectly

**Solution**:

Unit tests use **SQLite** by default and don't require PostgreSQL. PostgreSQL tests are automatically skipped when database is unavailable.

To run PostgreSQL tests:
```bash
# Start PostgreSQL (Docker)
docker-compose up -d postgres

# Or system PostgreSQL
sudo systemctl start postgresql

# Then run tests
uv run pytest
```

To skip PostgreSQL tests explicitly:
```bash
uv run pytest -m "not postgres"
```

---

### ❌ Error: `pytest: command not found` when using `uv run pytest`

**Cause**: pytest not installed in uv environment

**Solution**:
```bash
# Reinstall dependencies
uv pip install -r requirements.txt

# Verify pytest is available
uv run pytest --version
```

---

### ❌ Error: Collect errors or import failures

**Diagnosis**:
```bash
# See detailed collection errors
uv run pytest --collect-only -v

# Show full traceback
uv run pytest --tb=long
```

**Common fixes**:
1. Ensure you're in backend directory: `cd backend`
2. Clear cache: `find . -name __pycache__ -exec rm -rf {} +`
3. Reinstall: `uv pip install -r requirements.txt`

---

### ⚠️ Warning: Deprecation warnings during test run

**Examples**:
- `PytestDeprecationWarning: asyncio_default_fixture_loop_scope`
- `PydanticDeprecatedSince20: Using extra keyword arguments`

**Solution**: These are warnings, not errors. Tests still pass. Track in technical debt.

To hide warnings:
```bash
uv run pytest -p no:warnings
```

To show only errors:
```bash
uv run pytest --tb=short -p no:warnings
```

---

## Writing Tests

### Test File Structure

```python
"""Tests for feature X."""

import pytest
from app.services.feature import FeatureService


class TestFeatureService:
    """Test suite for FeatureService."""

    def test_basic_functionality(self):
        """Test basic feature works correctly."""
        service = FeatureService()
        result = service.do_something()
        assert result == expected_value

    def test_validation_error(self):
        """Test validation catches invalid input."""
        service = FeatureService()
        with pytest.raises(ValueError, match="Invalid input"):
            service.do_something(invalid_param="bad")

    @pytest.mark.asyncio
    async def test_async_operation(self):
        """Test async operation completes successfully."""
        service = FeatureService()
        result = await service.async_operation()
        assert result is not None
```

### Fixtures

```python
import pytest
from app.services.feature import FeatureService


@pytest.fixture
def feature_service():
    """Create FeatureService instance for testing."""
    return FeatureService()


@pytest.fixture
def sample_data():
    """Provide sample test data."""
    return {
        "id": "test-123",
        "name": "Test Item",
        "value": 42
    }


def test_with_fixtures(feature_service, sample_data):
    """Test using fixtures."""
    result = feature_service.process(sample_data)
    assert result["id"] == "test-123"
```

### Parametrized Tests

```python
import pytest


@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
    (10, 20),
])
def test_doubling(input, expected):
    """Test doubling function with various inputs."""
    assert double(input) == expected


@pytest.mark.parametrize("invalid_input", [
    None,
    "string",
    [],
    {},
])
def test_validation(invalid_input):
    """Test validation rejects invalid inputs."""
    with pytest.raises(ValueError):
        double(invalid_input)
```

### Async Tests

```python
import pytest


@pytest.mark.asyncio
async def test_async_function():
    """Test async function."""
    result = await async_function()
    assert result == expected


@pytest.mark.asyncio
async def test_async_context_manager():
    """Test async context manager."""
    async with AsyncResource() as resource:
        result = await resource.do_something()
        assert result is not None
```

### Test Markers

```python
import pytest


@pytest.mark.unit
def test_unit():
    """Unit test."""
    pass


@pytest.mark.integration
def test_integration():
    """Integration test."""
    pass


@pytest.mark.slow
def test_slow():
    """Slow test (skipped in quick runs)."""
    pass


@pytest.mark.skipif(condition, reason="Reason to skip")
def test_conditional():
    """Test skipped based on condition."""
    pass
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Backend Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Install dependencies
        run: |
          cd backend
          uv pip install -r requirements.txt

      - name: Run tests
        run: |
          cd backend
          uv run pytest --cov=app tests/ --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: ./backend/coverage.xml
```

### GitLab CI

```yaml
test:
  image: python:3.12
  before_script:
    - curl -LsSf https://astral.sh/uv/install.sh | sh
    - cd backend
    - uv pip install -r requirements.txt
  script:
    - uv run pytest --cov=app tests/ --cov-report=term-missing
  coverage: '/TOTAL.*\s+(\d+%)$/'
```

### Docker

```dockerfile
FROM python:3.12-slim

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

WORKDIR /app
COPY requirements.txt .

# Install dependencies
RUN uv pip install -r requirements.txt

COPY . .

# Run tests
CMD ["uv", "run", "pytest", "--cov=app", "tests/"]
```

## Test Organization

### Directory Structure

```
tests/
├── api/                      # API endpoint tests
│   ├── endpoints/
│   │   ├── test_auth.py
│   │   ├── test_projects.py
│   │   └── test_simulation.py
│   └── conftest.py          # API fixtures
├── services/                 # Service layer tests
│   ├── scheduler/
│   │   ├── test_task_graph.py
│   │   ├── test_cpm.py
│   │   └── test_work_calendar.py
│   └── simulation/
│       ├── test_pert_distribution.py
│       └── test_monte_carlo_engine.py
├── excel/                    # Excel generation tests
│   ├── test_engine.py
│   ├── test_templates.py
│   └── README.md            # Excel test docs
├── integration/              # Integration tests
│   └── test_excel_end_to_end.py
├── conftest.py              # Root fixtures
└── pytest.ini               # Pytest configuration
```

### Test Naming Conventions

- **Files**: `test_<module_name>.py`
- **Classes**: `Test<ClassName>` or `Test<Feature>`
- **Methods**: `test_<what_it_tests>`

Examples:
```python
# tests/services/test_scheduler.py
class TestTaskGraph:
    def test_add_node_creates_task(self):
        pass

    def test_add_edge_validates_node_exists(self):
        pass
```

## Best Practices

### 1. Test Isolation

Each test should be independent:
```python
# ✅ GOOD - isolated
def test_feature():
    service = FeatureService()  # New instance
    result = service.do_something()
    assert result == expected

# ❌ BAD - shared state
service = FeatureService()  # Global

def test_feature():
    result = service.do_something()  # Uses shared instance
    assert result == expected
```

### 2. Clear Assertions

```python
# ✅ GOOD - specific assertion
assert result["status"] == "success"
assert len(result["items"]) == 3

# ❌ BAD - vague assertion
assert result  # What are we checking?
```

### 3. Test One Thing

```python
# ✅ GOOD - focused
def test_validation_rejects_none():
    with pytest.raises(ValueError):
        validate(None)

def test_validation_rejects_empty_string():
    with pytest.raises(ValueError):
        validate("")

# ❌ BAD - testing multiple things
def test_validation():
    with pytest.raises(ValueError):
        validate(None)
    with pytest.raises(ValueError):
        validate("")
    with pytest.raises(ValueError):
        validate([])
```

### 4. Descriptive Names

```python
# ✅ GOOD - clear intent
def test_task_graph_rejects_circular_dependency():
    pass

def test_monte_carlo_returns_confidence_intervals():
    pass

# ❌ BAD - unclear
def test_graph():
    pass

def test_simulation():
    pass
```

## Performance Targets

- **Unit Tests**: < 0.1s per test
- **Integration Tests**: < 1s per test
- **Full Suite**: < 30s total
- **Coverage**: ≥ 85%
- **Pass Rate**: 100%

## Quality Standards

All tests must:
- ✅ Pass consistently (100% pass rate)
- ✅ Be isolated (no dependencies between tests)
- ✅ Be fast (< 1s for most tests)
- ✅ Have clear assertions
- ✅ Include docstrings
- ✅ Cover edge cases

## Resources

- **Backend README**: [README.md](README.md)
- **Excel Tests**: [tests/excel/README.md](tests/excel/README.md)
- **pytest Documentation**: https://docs.pytest.org/
- **uv Documentation**: https://github.com/astral-sh/uv

## Getting Help

- **Test failures**: Check [Troubleshooting](#troubleshooting) section
- **Environment issues**: See [Environment Setup](#environment-setup)
- **Writing tests**: See [Writing Tests](#writing-tests)
- **GitHub Issues**: https://github.com/frankbria/sprintforge/issues

---

**Remember**: Always use `uv run pytest` - it's the key to avoiding 99% of test environment issues! 🎯
