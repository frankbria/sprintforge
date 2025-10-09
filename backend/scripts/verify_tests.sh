#!/bin/bash
# Verify all test files are syntactically correct and infrastructure is ready

set -e

echo "=========================================="
echo "SprintForge Test Verification"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in backend directory
if [ ! -d "tests/excel" ]; then
    echo -e "${RED}Error: tests/excel directory not found${NC}"
    echo "Please run this script from the backend directory"
    exit 1
fi

# Verify Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1)
echo -e "${GREEN}✓${NC} $PYTHON_VERSION"
echo ""

# Compile all test files
echo "Verifying test file syntax..."
TEST_FILES=(
    "tests/excel/test_config.py"
    "tests/excel/test_sprint_parser.py"
    "tests/excel/test_critical_path.py"
    "tests/excel/test_gantt.py"
    "tests/excel/test_earned_value.py"
    "tests/excel/test_formulas.py"
    "tests/excel/test_engine.py"
)

PASSED=0
FAILED=0

for test_file in "${TEST_FILES[@]}"; do
    if [ -f "$test_file" ]; then
        if python3 -m py_compile "$test_file" 2>/dev/null; then
            echo -e "${GREEN}✓${NC} $test_file"
            ((PASSED++))
        else
            echo -e "${RED}✗${NC} $test_file - Syntax error"
            ((FAILED++))
        fi
    else
        echo -e "${YELLOW}⊘${NC} $test_file - Not found (may not be created yet)"
    fi
done

echo ""
echo "==========================================    "
echo "Syntax Verification Results:"
echo "  Passed: $PASSED files"
if [ $FAILED -gt 0 ]; then
    echo -e "  ${RED}Failed: $FAILED files${NC}"
else
    echo -e "  ${GREEN}Failed: 0 files${NC}"
fi
echo "=========================================="
echo ""

# Check pytest configuration
echo "Checking pytest configuration..."
if [ -f "pytest.ini" ]; then
    echo -e "${GREEN}✓${NC} pytest.ini found"
else
    echo -e "${YELLOW}⊘${NC} pytest.ini not found"
fi
echo ""

# Check requirements.txt includes pytest
echo "Checking test dependencies in requirements.txt..."
if grep -q "pytest" requirements.txt; then
    PYTEST_VERSION=$(grep "pytest==" requirements.txt | head -1)
    echo -e "${GREEN}✓${NC} $PYTEST_VERSION"
else
    echo -e "${RED}✗${NC} pytest not in requirements.txt"
fi

if grep -q "pydantic" requirements.txt; then
    PYDANTIC_VERSION=$(grep "pydantic==" requirements.txt | head -1)
    echo -e "${GREEN}✓${NC} $PYDANTIC_VERSION"
else
    echo -e "${RED}✗${NC} pydantic not in requirements.txt"
fi
echo ""

# Check for test documentation
echo "Checking test documentation..."
if [ -f "tests/excel/README.md" ]; then
    LINE_COUNT=$(wc -l < tests/excel/README.md)
    echo -e "${GREEN}✓${NC} tests/excel/README.md ($LINE_COUNT lines)"
else
    echo -e "${YELLOW}⊘${NC} tests/excel/README.md not found"
fi
echo ""

# Summary
echo "=========================================="
echo "Test Infrastructure Status:"
echo "=========================================="

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All test files compile successfully${NC}"
    echo -e "${GREEN}✓ Test infrastructure is ready${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Install dependencies: pip install -r requirements.txt"
    echo "  2. Run tests: pytest tests/excel/ -v"
    echo "  3. Run with coverage: pytest tests/excel/ --cov=app.excel"
    exit 0
else
    echo -e "${RED}✗ Some test files have syntax errors${NC}"
    echo "Please fix syntax errors before running tests"
    exit 1
fi
