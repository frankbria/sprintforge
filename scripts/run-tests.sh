#!/bin/bash

# SprintForge Test Runner Script
# Runs all tests for backend and frontend with proper reporting

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker Compose is available
check_docker_compose() {
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    elif docker-compose --version &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        print_error "Docker Compose is not available. Please install Docker Compose."
        exit 1
    fi
}

# Check if services are running
check_services() {
    print_status "Checking if development services are running..."

    if ! $COMPOSE_CMD -f docker-compose.dev.yml ps | grep -q "Up"; then
        print_warning "Development services are not running. Starting them..."
        $COMPOSE_CMD -f docker-compose.dev.yml up -d

        # Wait for services to be ready
        print_status "Waiting for services to be ready..."
        sleep 10
    fi

    print_success "Services are running"
}

# Run backend tests
run_backend_tests() {
    print_status "Running backend tests..."

    echo "🐍 Python Backend Tests"
    echo "======================="

    # Run pytest with coverage
    if $COMPOSE_CMD -f docker-compose.dev.yml exec -T backend pytest --cov=app --cov-report=term-missing --cov-report=html tests/; then
        print_success "✅ Backend tests passed"
        BACKEND_SUCCESS=true
    else
        print_error "❌ Backend tests failed"
        BACKEND_SUCCESS=false
    fi

    echo ""
}

# Run frontend tests
run_frontend_tests() {
    print_status "Running frontend tests..."

    echo "⚛️  React Frontend Tests"
    echo "========================"

    # Run Jest tests
    if $COMPOSE_CMD -f docker-compose.dev.yml exec -T frontend npm test -- --coverage --watchAll=false; then
        print_success "✅ Frontend tests passed"
        FRONTEND_SUCCESS=true
    else
        print_error "❌ Frontend tests failed"
        FRONTEND_SUCCESS=false
    fi

    echo ""
}

# Run Excel generation tests
run_excel_tests() {
    print_status "Running Excel generation tests..."

    echo "📊 Excel Generation Tests"
    echo "========================="

    # Run specific Excel tests
    if $COMPOSE_CMD -f docker-compose.dev.yml exec -T backend pytest tests/excel/ -v; then
        print_success "✅ Excel generation tests passed"
        EXCEL_SUCCESS=true
    else
        print_error "❌ Excel generation tests failed"
        EXCEL_SUCCESS=false
    fi

    echo ""
}

# Run integration tests
run_integration_tests() {
    print_status "Running integration tests..."

    echo "🔗 Integration Tests"
    echo "==================="

    # Run integration tests
    if $COMPOSE_CMD -f docker-compose.dev.yml exec -T backend pytest tests/integration/ -v; then
        print_success "✅ Integration tests passed"
        INTEGRATION_SUCCESS=true
    else
        print_error "❌ Integration tests failed"
        INTEGRATION_SUCCESS=false
    fi

    echo ""
}

# Run code quality checks
run_code_quality() {
    print_status "Running code quality checks..."

    echo "🔍 Code Quality Checks"
    echo "======================"

    # Backend code quality
    echo "Backend code formatting..."
    if $COMPOSE_CMD -f docker-compose.dev.yml exec -T backend black --check .; then
        print_success "✅ Backend code formatting is correct"
        BACKEND_FORMAT_SUCCESS=true
    else
        print_error "❌ Backend code formatting issues found"
        BACKEND_FORMAT_SUCCESS=false
    fi

    echo "Backend import sorting..."
    if $COMPOSE_CMD -f docker-compose.dev.yml exec -T backend isort --check-only .; then
        print_success "✅ Backend import sorting is correct"
        BACKEND_IMPORT_SUCCESS=true
    else
        print_error "❌ Backend import sorting issues found"
        BACKEND_IMPORT_SUCCESS=false
    fi

    echo "Backend linting..."
    if $COMPOSE_CMD -f docker-compose.dev.yml exec -T backend flake8 .; then
        print_success "✅ Backend linting passed"
        BACKEND_LINT_SUCCESS=true
    else
        print_error "❌ Backend linting issues found"
        BACKEND_LINT_SUCCESS=false
    fi

    echo "Backend type checking..."
    if $COMPOSE_CMD -f docker-compose.dev.yml exec -T backend mypy app/; then
        print_success "✅ Backend type checking passed"
        BACKEND_TYPE_SUCCESS=true
    else
        print_error "❌ Backend type checking issues found"
        BACKEND_TYPE_SUCCESS=false
    fi

    # Frontend code quality
    echo "Frontend linting..."
    if $COMPOSE_CMD -f docker-compose.dev.yml exec -T frontend npm run lint; then
        print_success "✅ Frontend linting passed"
        FRONTEND_LINT_SUCCESS=true
    else
        print_error "❌ Frontend linting issues found"
        FRONTEND_LINT_SUCCESS=false
    fi

    echo "Frontend type checking..."
    if $COMPOSE_CMD -f docker-compose.dev.yml exec -T frontend npm run type-check; then
        print_success "✅ Frontend type checking passed"
        FRONTEND_TYPE_SUCCESS=true
    else
        print_error "❌ Frontend type checking issues found"
        FRONTEND_TYPE_SUCCESS=false
    fi

    echo ""
}

# Show test results summary
show_summary() {
    echo "📊 Test Results Summary"
    echo "======================"

    # Count successes and failures
    TOTAL_CHECKS=0
    PASSED_CHECKS=0

    # Test results
    if [ "${RUN_BACKEND:-true}" = "true" ]; then
        TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
        if [ "$BACKEND_SUCCESS" = "true" ]; then
            echo "✅ Backend Tests: PASSED"
            PASSED_CHECKS=$((PASSED_CHECKS + 1))
        else
            echo "❌ Backend Tests: FAILED"
        fi
    fi

    if [ "${RUN_FRONTEND:-true}" = "true" ]; then
        TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
        if [ "$FRONTEND_SUCCESS" = "true" ]; then
            echo "✅ Frontend Tests: PASSED"
            PASSED_CHECKS=$((PASSED_CHECKS + 1))
        else
            echo "❌ Frontend Tests: FAILED"
        fi
    fi

    if [ "${RUN_EXCEL:-true}" = "true" ]; then
        TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
        if [ "$EXCEL_SUCCESS" = "true" ]; then
            echo "✅ Excel Tests: PASSED"
            PASSED_CHECKS=$((PASSED_CHECKS + 1))
        else
            echo "❌ Excel Tests: FAILED"
        fi
    fi

    if [ "${RUN_INTEGRATION:-true}" = "true" ]; then
        TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
        if [ "$INTEGRATION_SUCCESS" = "true" ]; then
            echo "✅ Integration Tests: PASSED"
            PASSED_CHECKS=$((PASSED_CHECKS + 1))
        else
            echo "❌ Integration Tests: FAILED"
        fi
    fi

    # Code quality results
    if [ "${RUN_QUALITY:-true}" = "true" ]; then
        quality_checks=("BACKEND_FORMAT_SUCCESS" "BACKEND_IMPORT_SUCCESS" "BACKEND_LINT_SUCCESS" "BACKEND_TYPE_SUCCESS" "FRONTEND_LINT_SUCCESS" "FRONTEND_TYPE_SUCCESS")

        for check in "${quality_checks[@]}"; do
            TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
            if [ "${!check}" = "true" ]; then
                PASSED_CHECKS=$((PASSED_CHECKS + 1))
            fi
        done

        echo ""
        echo "Code Quality Checks:"
        [ "$BACKEND_FORMAT_SUCCESS" = "true" ] && echo "✅ Backend Formatting" || echo "❌ Backend Formatting"
        [ "$BACKEND_IMPORT_SUCCESS" = "true" ] && echo "✅ Backend Imports" || echo "❌ Backend Imports"
        [ "$BACKEND_LINT_SUCCESS" = "true" ] && echo "✅ Backend Linting" || echo "❌ Backend Linting"
        [ "$BACKEND_TYPE_SUCCESS" = "true" ] && echo "✅ Backend Types" || echo "❌ Backend Types"
        [ "$FRONTEND_LINT_SUCCESS" = "true" ] && echo "✅ Frontend Linting" || echo "❌ Frontend Linting"
        [ "$FRONTEND_TYPE_SUCCESS" = "true" ] && echo "✅ Frontend Types" || echo "❌ Frontend Types"
    fi

    echo ""
    echo "Overall Result: $PASSED_CHECKS/$TOTAL_CHECKS checks passed"

    if [ $PASSED_CHECKS -eq $TOTAL_CHECKS ]; then
        print_success "🎉 All tests and checks passed!"
        return 0
    else
        print_error "💥 Some tests or checks failed!"
        return 1
    fi
}

# Fix code quality issues
fix_code_quality() {
    print_status "Fixing code quality issues..."

    echo "🔧 Auto-fixing Code Quality Issues"
    echo "=================================="

    # Fix backend formatting
    echo "Fixing backend code formatting..."
    $COMPOSE_CMD -f docker-compose.dev.yml exec -T backend black .

    echo "Fixing backend import sorting..."
    $COMPOSE_CMD -f docker-compose.dev.yml exec -T backend isort .

    # Fix frontend formatting
    echo "Fixing frontend code formatting..."
    $COMPOSE_CMD -f docker-compose.dev.yml exec -T frontend npm run lint:fix

    print_success "Code formatting fixes applied"
    print_warning "Please review the changes and commit them if they look correct"
}

# Show help
show_help() {
    echo "SprintForge Test Runner"
    echo ""
    echo "Usage: $0 [options] [test-type]"
    echo ""
    echo "Test Types:"
    echo "  all           Run all tests and quality checks (default)"
    echo "  backend       Run only backend tests"
    echo "  frontend      Run only frontend tests"
    echo "  excel         Run only Excel generation tests"
    echo "  integration   Run only integration tests"
    echo "  quality       Run only code quality checks"
    echo ""
    echo "Options:"
    echo "  --fix         Auto-fix code quality issues"
    echo "  --no-quality  Skip code quality checks"
    echo "  --coverage    Generate coverage reports"
    echo "  --help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Run all tests"
    echo "  $0 backend            # Run only backend tests"
    echo "  $0 --fix              # Fix code quality issues"
    echo "  $0 backend --coverage # Run backend tests with coverage"
}

# Main execution
main() {
    echo "🧪 SprintForge Test Runner"
    echo "=========================="

    # Check if we're in the right directory
    if [ ! -f "docker-compose.dev.yml" ]; then
        print_error "docker-compose.dev.yml not found. Please run this script from the SprintForge root directory."
        exit 1
    fi

    check_docker_compose
    check_services

    # Parse arguments
    SHOULD_FIX=false
    RUN_QUALITY=true
    TEST_TYPE="all"

    while [[ $# -gt 0 ]]; do
        case $1 in
            --fix)
                SHOULD_FIX=true
                shift
                ;;
            --no-quality)
                RUN_QUALITY=false
                shift
                ;;
            --coverage)
                # Coverage is already included in test runs
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            backend|frontend|excel|integration|quality|all)
                TEST_TYPE=$1
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # Fix code quality if requested
    if [ "$SHOULD_FIX" = "true" ]; then
        fix_code_quality
        exit 0
    fi

    # Set flags based on test type
    case $TEST_TYPE in
        "backend")
            RUN_BACKEND=true
            RUN_FRONTEND=false
            RUN_EXCEL=false
            RUN_INTEGRATION=false
            ;;
        "frontend")
            RUN_BACKEND=false
            RUN_FRONTEND=true
            RUN_EXCEL=false
            RUN_INTEGRATION=false
            ;;
        "excel")
            RUN_BACKEND=false
            RUN_FRONTEND=false
            RUN_EXCEL=true
            RUN_INTEGRATION=false
            ;;
        "integration")
            RUN_BACKEND=false
            RUN_FRONTEND=false
            RUN_EXCEL=false
            RUN_INTEGRATION=true
            ;;
        "quality")
            RUN_BACKEND=false
            RUN_FRONTEND=false
            RUN_EXCEL=false
            RUN_INTEGRATION=false
            RUN_QUALITY=true
            ;;
        "all")
            RUN_BACKEND=true
            RUN_FRONTEND=true
            RUN_EXCEL=true
            RUN_INTEGRATION=true
            ;;
    esac

    # Run selected tests
    [ "${RUN_BACKEND:-false}" = "true" ] && run_backend_tests
    [ "${RUN_FRONTEND:-false}" = "true" ] && run_frontend_tests
    [ "${RUN_EXCEL:-false}" = "true" ] && run_excel_tests
    [ "${RUN_INTEGRATION:-false}" = "true" ] && run_integration_tests
    [ "${RUN_QUALITY:-false}" = "true" ] && run_code_quality

    # Show summary and exit with appropriate code
    if show_summary; then
        exit 0
    else
        exit 1
    fi
}

# Handle script execution
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi