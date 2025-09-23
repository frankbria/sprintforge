#!/bin/bash

# SprintForge Development Environment Setup Script
# This script sets up a complete development environment for SprintForge

set -e  # Exit on any error

echo "🚀 Setting up SprintForge development environment..."

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

# Check if Docker is installed and running
check_docker() {
    print_status "Checking Docker installation..."

    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker Desktop and try again."
        echo "Download from: https://www.docker.com/products/docker-desktop"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker Desktop and try again."
        exit 1
    fi

    print_success "Docker is installed and running"
}

# Check if Docker Compose is available
check_docker_compose() {
    print_status "Checking Docker Compose..."

    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    elif docker-compose --version &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        print_error "Docker Compose is not available. Please install Docker Compose and try again."
        exit 1
    fi

    print_success "Docker Compose is available: $COMPOSE_CMD"
}

# Create environment files from examples
setup_environment_files() {
    print_status "Setting up environment files..."

    # Backend environment
    if [ ! -f "backend/.env" ]; then
        if [ -f "backend/.env.example" ]; then
            cp backend/.env.example backend/.env
            print_success "Created backend/.env from example"
        else
            print_warning "No backend/.env.example found, creating basic .env"
            cat > backend/.env << EOF
DEBUG=true
DATABASE_URL=postgresql://dev:dev@postgres:5432/sprintforge
S3_ENDPOINT=http://minio:9000
S3_BUCKET=sprintforge-dev
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
NEXTAUTH_SECRET=dev-secret-change-in-production
ENVIRONMENT=development
EOF
        fi
    else
        print_success "Backend .env already exists"
    fi

    # Frontend environment
    if [ ! -f "frontend/.env.local" ]; then
        if [ -f "frontend/.env.example" ]; then
            cp frontend/.env.example frontend/.env.local
            print_success "Created frontend/.env.local from example"
        else
            print_warning "No frontend/.env.example found, creating basic .env.local"
            cat > frontend/.env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=dev-secret-change-in-production
EOF
        fi
    else
        print_success "Frontend .env.local already exists"
    fi
}

# Build and start development services
start_development_services() {
    print_status "Building and starting development services..."

    # Stop any existing services
    $COMPOSE_CMD -f docker-compose.dev.yml down 2>/dev/null || true

    # Build and start services
    print_status "This may take several minutes on first run..."
    $COMPOSE_CMD -f docker-compose.dev.yml up --build -d

    print_success "Development services started"
}

# Wait for services to be healthy
wait_for_services() {
    print_status "Waiting for services to be ready..."

    # Wait for database
    echo "⏳ Waiting for database..."
    for i in {1..30}; do
        if $COMPOSE_CMD -f docker-compose.dev.yml exec -T postgres pg_isready -U dev -d sprintforge &>/dev/null; then
            break
        fi
        sleep 2
        echo -n "."
    done
    echo ""

    # Wait for backend
    echo "⏳ Waiting for backend API..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/health &>/dev/null; then
            break
        fi
        sleep 2
        echo -n "."
    done
    echo ""

    # Wait for frontend
    echo "⏳ Waiting for frontend..."
    for i in {1..30}; do
        if curl -s http://localhost:3000 &>/dev/null; then
            break
        fi
        sleep 2
        echo -n "."
    done
    echo ""

    print_success "All services are ready!"
}

# Run initial database migrations and sample data
setup_database() {
    print_status "Setting up database..."

    # Run migrations
    $COMPOSE_CMD -f docker-compose.dev.yml exec -T backend python -m app.database.migrations || {
        print_warning "Migration command failed, database might already be set up"
    }

    print_success "Database setup complete"
}

# Verify the installation
verify_installation() {
    print_status "Verifying installation..."

    # Check backend health
    if curl -s http://localhost:8000/health | grep -q "healthy"; then
        print_success "✅ Backend API is healthy"
    else
        print_error "❌ Backend API health check failed"
        return 1
    fi

    # Check frontend
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 | grep -q "200"; then
        print_success "✅ Frontend is accessible"
    else
        print_error "❌ Frontend is not accessible"
        return 1
    fi

    # Check database connection
    if $COMPOSE_CMD -f docker-compose.dev.yml exec -T postgres psql -U dev -d sprintforge -c "SELECT 1;" &>/dev/null; then
        print_success "✅ Database connection working"
    else
        print_error "❌ Database connection failed"
        return 1
    fi

    # Check MinIO (S3 mock)
    if curl -s http://localhost:9000/minio/health/live &>/dev/null; then
        print_success "✅ MinIO (S3 mock) is running"
    else
        print_warning "⚠️  MinIO health check failed (may still work)"
    fi

    print_success "🎉 Installation verification complete!"
}

# Show service information
show_service_info() {
    echo ""
    echo "🌟 SprintForge Development Environment Ready!"
    echo ""
    echo "📱 Available Services:"
    echo "   Frontend:        http://localhost:3000"
    echo "   Backend API:     http://localhost:8000"
    echo "   API Docs:        http://localhost:8000/docs"
    echo "   Database:        localhost:5432 (dev/dev)"
    echo "   MinIO Console:   http://localhost:9001 (minioadmin/minioadmin)"
    echo ""
    echo "🔧 Useful Commands:"
    echo "   View logs:       $COMPOSE_CMD -f docker-compose.dev.yml logs -f"
    echo "   Stop services:   $COMPOSE_CMD -f docker-compose.dev.yml down"
    echo "   Restart:         $COMPOSE_CMD -f docker-compose.dev.yml restart"
    echo "   Run tests:       ./scripts/run-tests.sh"
    echo ""
    echo "📚 Next Steps:"
    echo "   1. Read DEVELOPMENT.md for detailed development guide"
    echo "   2. Check CONTRIBUTING.md for contribution guidelines"
    echo "   3. Join our Discord: https://discord.gg/sprintforge"
    echo ""
    echo "🐛 Troubleshooting:"
    echo "   - Check logs: $COMPOSE_CMD -f docker-compose.dev.yml logs <service>"
    echo "   - Reset database: $COMPOSE_CMD -f docker-compose.dev.yml down -v"
    echo "   - Clean Docker: docker system prune -a"
    echo ""
}

# Cleanup on failure
cleanup_on_failure() {
    print_error "Setup failed! Cleaning up..."
    $COMPOSE_CMD -f docker-compose.dev.yml down 2>/dev/null || true
    exit 1
}

# Set up error handling
trap cleanup_on_failure ERR

# Main execution
main() {
    echo "🏗️  SprintForge Development Environment Setup"
    echo "=============================================="

    # Check if we're in the right directory
    if [ ! -f "docker-compose.dev.yml" ]; then
        print_error "docker-compose.dev.yml not found. Please run this script from the SprintForge root directory."
        exit 1
    fi

    # Run setup steps
    check_docker
    check_docker_compose
    setup_environment_files
    start_development_services
    wait_for_services
    setup_database

    # Verify everything is working
    if verify_installation; then
        show_service_info
    else
        print_error "Installation verification failed. Check the logs above for details."
        exit 1
    fi
}

# Handle script arguments
case "${1:-}" in
    "clean")
        print_status "Cleaning up development environment..."
        $COMPOSE_CMD -f docker-compose.dev.yml down -v
        docker system prune -f
        print_success "Cleanup complete"
        ;;
    "status")
        print_status "Checking service status..."
        $COMPOSE_CMD -f docker-compose.dev.yml ps
        ;;
    "logs")
        $COMPOSE_CMD -f docker-compose.dev.yml logs -f
        ;;
    "help"|"-h"|"--help")
        echo "SprintForge Development Environment Setup"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  (no command)  Set up development environment"
        echo "  clean         Clean up all containers and volumes"
        echo "  status        Show service status"
        echo "  logs          Show service logs"
        echo "  help          Show this help message"
        ;;
    "")
        main
        ;;
    *)
        print_error "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac