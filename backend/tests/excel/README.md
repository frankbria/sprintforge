# Excel Generation Tests

Comprehensive test suite for SprintForge Excel generation components.

## Test Infrastructure

### Prerequisites

**IMPORTANT**: This project uses `uv` for Python package management. Always use `uv run` for all commands.

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# From backend directory - install dependencies
uv pip install -r requirements.txt
```

This installs:
- `pytest==7.4.3` - Test framework
- `pytest-asyncio==0.21.1` - Async test support
- `pytest-cov==4.1.0` - Coverage reporting
- `pydantic==2.5.1` - Data validation (required by code)

### Running Tests

**CRITICAL**: Always use `uv run pytest` instead of direct `pytest` commands.

```bash
# Run all Excel tests
uv run pytest tests/excel/ -v

# Run specific test file
uv run pytest tests/excel/test_config.py -v
uv run pytest tests/excel/test_sprint_parser.py -v

# Run with coverage
uv run pytest tests/excel/ --cov=app.excel --cov-report=html

# Run specific test class
uv run pytest tests/excel/test_config.py::TestProjectConfig -v

# Run specific test method
uv run pytest tests/excel/test_config.py::TestProjectConfig::test_minimal_project_config -v
```

**Why `uv run`?** The project uses `uv` for dependency management. Running `pytest` directly will use your system Python, which won't have the required packages (like `openpyxl`) installed.

### Test Markers

Tests are organized with markers for selective execution:

```bash
# Run only configuration tests
uv run pytest -m config

# Run only unit tests
uv run pytest -m unit

# Run only Excel generation tests
uv run pytest -m excel
```

## Test Coverage

### test_config.py (Configuration Models)

**Classes Tested:**
- `WorkingDaysConfig` - Working days and holidays validation
- `SprintConfig` - Sprint pattern configuration
- `ProjectFeatures` - Feature flags
- `ProjectConfig` - Complete project configuration

**Test Categories:**
- Default configurations
- Custom configurations
- Validation (invalid inputs)
- Edge cases
- Realistic examples (Agile, SAFe, Waterfall)

**Coverage:**
- ✅ All Pydantic validators
- ✅ Model serialization (to_legacy_dict)
- ✅ Feature flag management
- ✅ Configuration immutability

### test_sprint_parser.py (Sprint Pattern Parsing)

**Classes Tested:**
- `SprintParser` - Sprint number calculation and parsing

**Test Categories:**
- YY.Q.# pattern (Year-Quarter-Number)
- PI-N.Sprint-M pattern (SAFe Program Increment)
- YYYY.WW pattern (ISO Calendar Week)
- Custom patterns with placeholders
- Sprint range calculations
- Edge cases (year transitions, leap years)

**Coverage:**
- ✅ All sprint pattern types
- ✅ Bidirectional conversion (date ↔ sprint ID)
- ✅ Custom pattern placeholders
- ✅ Sprint range generation

## Test Data

### Realistic Scenarios

**Agile/Scrum:**
- 2-week sprints
- YY.Q.# pattern
- Burndown charts enabled

**SAFe/PI:**
- 2-week sprints
- PI-N.Sprint-M pattern
- 5 sprints per Program Increment
- Baseline tracking enabled

**Waterfall:**
- 1-week tracking
- YYYY.WW pattern
- Critical path and EVM enabled

## Running Individual Test Classes

### Configuration Tests

```bash
# Working days configuration
uv run pytest tests/excel/test_config.py::TestWorkingDaysConfig -v

# Sprint configuration
uv run pytest tests/excel/test_config.py::TestSprintConfig -v

# Project features
uv run pytest tests/excel/test_config.py::TestProjectFeatures -v

# Complete project config
uv run pytest tests/excel/test_config.py::TestProjectConfig -v

# Example scenarios
uv run pytest tests/excel/test_config.py::TestProjectConfigExamples -v
```

### Sprint Parser Tests

```bash
# Year-Quarter-Number pattern
uv run pytest tests/excel/test_sprint_parser.py::TestYearQuarterNumberPattern -v

# PI-Sprint pattern
uv run pytest tests/excel/test_sprint_parser.py::TestPISprintPattern -v

# Calendar week pattern
uv run pytest tests/excel/test_sprint_parser.py::TestCalendarWeekPattern -v

# Custom patterns
uv run pytest tests/excel/test_sprint_parser.py::TestCustomPattern -v

# Sprint ranges
uv run pytest tests/excel/test_sprint_parser.py::TestSprintRange -v

# Edge cases
uv run pytest tests/excel/test_sprint_parser.py::TestEdgeCases -v
```

## Expected Test Results

All tests should pass with 100% success rate:

```
tests/excel/test_config.py ...................... [ XX%]
tests/excel/test_sprint_parser.py ............... [100%]

==================== XX passed in X.XXs ====================
```

## Continuous Integration

These tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run Excel Tests
  run: |
    cd backend
    uv run pytest tests/excel/ -v --cov=app.excel
```

## Troubleshooting

### ModuleNotFoundError: No module named 'openpyxl' (or other packages)

**Cause**: Running `pytest` directly instead of `uv run pytest`

**Solution**:
```bash
# ❌ WRONG - uses system Python
pytest

# ✅ CORRECT - uses uv-managed environment
uv run pytest
```

### Import Errors

```bash
# Ensure you're in the backend directory
cd backend

# Install dependencies
uv pip install -r requirements.txt

# Verify pytest is installed
uv run pytest --version
```

### ModuleNotFoundError: app.excel

```bash
# Ensure Python path includes backend directory
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or run pytest from backend directory
cd backend && uv run pytest tests/excel/
```

### Pydantic ValidationError

If tests fail with ValidationError:
1. Check test data matches model constraints
2. Review model validators in app/excel/config.py
3. Ensure date formats are correct (YYYY-MM-DD)

## Adding New Tests

When adding new functionality:

1. **Create test file**: `tests/excel/test_<feature>.py`
2. **Follow naming convention**: `Test<ClassName>` for test classes
3. **Add docstrings**: Describe what each test validates
4. **Use pytest fixtures**: For shared test data
5. **Add markers**: Categorize tests appropriately
6. **Test edge cases**: Invalid inputs, boundaries, etc.

Example:

```python
"""Tests for new feature."""

import pytest
from app.excel.new_feature import NewFeature


class TestNewFeature:
    """Test new feature functionality."""

    def test_basic_functionality(self):
        """Test basic feature works correctly."""
        feature = NewFeature()
        result = feature.do_something()
        assert result == expected_value

    def test_invalid_input(self):
        """Test validation catches invalid input."""
        with pytest.raises(ValueError):
            NewFeature(invalid_param="bad")
```

## Performance

Test suite performance targets:
- **test_config.py**: < 1 second
- **test_sprint_parser.py**: < 1 second
- **All Excel tests**: < 5 seconds

If tests run slower, consider:
- Reducing test data size
- Using pytest fixtures for expensive setup
- Marking slow tests with `@pytest.mark.slow`
