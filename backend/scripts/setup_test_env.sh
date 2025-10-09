#!/bin/bash
# Setup test environment for SprintForge backend

set -e  # Exit on error

echo "======================================"
echo "SprintForge Test Environment Setup"
echo "======================================"
echo ""

# Check if we're in the backend directory
if [ ! -f "requirements.txt" ]; then
    echo "Error: requirements.txt not found"
    echo "Please run this script from the backend directory"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip --quiet

# Install dependencies
echo ""
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt --quiet
echo "✓ Dependencies installed"

# Verify pytest installation
echo ""
echo "Verifying pytest installation..."
PYTEST_VERSION=$(pytest --version 2>&1 | head -1)
echo "✓ $PYTEST_VERSION"

# Verify pydantic installation
echo ""
echo "Verifying pydantic installation..."
python3 -c "import pydantic; print(f'✓ Pydantic {pydantic.__version__}')"

# Run syntax check on test files
echo ""
echo "Checking test file syntax..."
python3 -m py_compile tests/excel/test_config.py
python3 -m py_compile tests/excel/test_sprint_parser.py
python3 -m py_compile tests/excel/test_critical_path.py
python3 -m py_compile tests/excel/test_gantt.py
python3 -m py_compile tests/excel/test_earned_value.py
echo "✓ All test files compile successfully"

# Check if pytest can collect tests
echo ""
echo "Collecting tests..."
TEST_COUNT=$(pytest --collect-only tests/excel/ -q 2>&1 | grep "test" | wc -l)
echo "✓ Found $TEST_COUNT test cases"

echo ""
echo "======================================"
echo "Test Environment Setup Complete!"
echo "======================================"
echo ""
echo "To activate the environment:"
echo "  source venv/bin/activate"
echo ""
echo "To run tests:"
echo "  pytest tests/excel/ -v"
echo ""
echo "To run with coverage:"
echo "  pytest tests/excel/ --cov=app.excel --cov-report=html"
echo ""
