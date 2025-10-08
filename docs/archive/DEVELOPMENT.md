# SprintForge Development Guide

This guide covers the technical details for setting up and contributing to SprintForge development.

## 🚀 Quick Development Setup

### One-Command Setup
```bash
# Clone and start development environment
git clone https://github.com/frankbria/sprintforge.git
cd sprintforge

# Start all services with hot reload
docker-compose -f docker-compose.dev.yml up --build

# Verify setup
curl http://localhost:8000/health    # Backend health check
open http://localhost:3000           # Frontend application
```

### Services Available
- **Frontend**: http://localhost:3000 (Next.js with hot reload)
- **Backend API**: http://localhost:8000 (FastAPI with hot reload)
- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **Database**: PostgreSQL on localhost:5432
- **S3 Storage**: MinIO on localhost:9000 (minioadmin/minioadmin)
- **S3 Console**: http://localhost:9001 (MinIO management interface)

## 🏗️ Architecture Overview

### Technology Stack
```
Frontend:  Next.js 15 + TypeScript + TailwindCSS
Backend:   FastAPI + Python 3.11 + PostgreSQL
Excel:     OpenPyXL + Formula Templates
Storage:   AWS S3 (MinIO for development)
Auth:      NextAuth.js (Google + Microsoft OAuth)
```

### Component Architecture
```
┌─────────────────────────────────────────────────┐
│               Frontend (Next.js)                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │Setup Wizard │ │Project Mgmt │ │ Excel Export││
│  └─────────────┘ └─────────────┘ └─────────────┘│
└─────────────────────┬───────────────────────────┘
                      │ REST API
┌─────────────────────┼───────────────────────────┐
│            Backend Services (FastAPI)           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │Excel Engine │ │Formula Gen  │ │ Sync Service││
│  └─────────────┘ └─────────────┘ └─────────────┘│
└─────────────────────┼───────────────────────────┘
                      │
┌─────────────────────┼───────────────────────────┐
│                Data Layer                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │PostgreSQL   │ │     S3      │ │   Redis     ││
│  │(Users/Proj) │ │(File Store) │ │(Optional)   ││
│  └─────────────┘ └─────────────┘ └─────────────┘│
└─────────────────────────────────────────────────┘
```

## 🔧 Development Environment Details

### Docker Development Services

#### Backend Service
```yaml
# Hot reload Python development
volumes:
  - ./backend:/app           # Source code hot reload
  - backend_cache:/app/.cache # Cache dependencies

environment:
  - DEBUG=true
  - DATABASE_URL=postgresql://dev:dev@postgres:5432/sprintforge
  - S3_ENDPOINT=http://minio:9000
```

#### Frontend Service
```yaml
# Hot reload Next.js development
volumes:
  - ./frontend:/app          # Source code hot reload
  - /app/node_modules       # Preserve node_modules
  - /app/.next              # Preserve Next.js cache

environment:
  - NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

### Local Development (Alternative)

If you prefer running services locally instead of Docker:

#### Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-dev.txt

# Set up environment
cp .env.example .env
# Edit .env with your local database settings

# Run migrations
python -m app.database.migrations

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Set up environment
cp .env.example .env.local
# Edit .env.local with your API URL

# Start development server
npm run dev
```

## 📊 Database Development

### Schema Management
```bash
# Create new migration
# 1. Add SQL file to backend/migrations/
# 2. Name it: 002_add_feature_name.sql

# Apply migrations (automatic in Docker)
docker-compose exec backend python -m app.database.migrations

# Reset database (development only)
docker-compose down -v  # Destroys all data
docker-compose up postgres -d
```

### Sample Data
Development environment automatically loads sample data:
- Dev user: dev@sprintforge.com
- Sample project with agile configuration
- Test sprint patterns and formulas

### Database Access
```bash
# Connect to development database
docker-compose exec postgres psql -U dev -d sprintforge

# Common queries
\dt                              # List tables
SELECT * FROM users;             # View users
SELECT * FROM projects;          # View projects
SELECT config FROM projects;     # View project configurations
```

## 🧮 Excel Generation Development

### Formula Template System

SprintForge uses a modular formula system that's easy for contributors to extend:

#### Adding New Formulas
```bash
# 1. Create formula template file
touch backend/app/excel/components/templates/my_formulas.json

# 2. Add formulas with metadata
{
  "_metadata": {
    "description": "Custom project formulas",
    "contributor": "@your-github-username",
    "version": "1.0"
  },
  "my_formula": {
    "formula": "=IF($condition, $true_value, $false_value)",
    "description": "Conditional calculation for project metrics",
    "parameters": {
      "condition": "Boolean condition to evaluate",
      "true_value": "Value when condition is true",
      "false_value": "Value when condition is false"
    }
  }
}

# 3. Add tests
# backend/tests/excel/test_my_formulas.py

# 4. Register in component (if needed)
# backend/app/excel/components/formulas.py
```

#### Testing Excel Generation
```bash
# Test formula generation
docker-compose exec backend pytest tests/excel/ -v

# Test complete Excel generation
docker-compose exec backend python -c "
from app.excel.engine import ExcelTemplateEngine
from app.models.schemas import ProjectConfig

config = ProjectConfig(
    project_name='Test',
    sprint_pattern='YY.Q.#',
    features={'monte_carlo': True}
)

engine = ExcelTemplateEngine()
excel_bytes = engine.generate_template(config)
print(f'Generated {len(excel_bytes)} bytes')
"
```

### Formula Development Guidelines

#### Modern Excel Functions
SprintForge targets Excel 2019+ and can use modern functions:
```excel
XLOOKUP()    # Improved lookup function
FILTER()     # Dynamic array filtering
SORT()       # Dynamic array sorting
LET()        # Variable assignment (Excel 365)
LAMBDA()     # Custom functions (Excel 365)
```

#### Formula Templates
```json
{
  "dependency_calculation": "=IF(ISBLANK({predecessor_finish}), {task_start}, MAX({task_start}, {predecessor_finish} + {lag_days}))",

  "critical_path_detection": "=IF(AND({total_float}=0, {duration}>0), \"CRITICAL\", \"\")",

  "monte_carlo_simulation": "=NORM.INV(RAND(), {mean_duration}, {standard_deviation})",

  "sprint_velocity": "=AVERAGE(OFFSET({completed_points}, -{sprint_count}, 0, {sprint_count}, 1))"
}
```

## 🧪 Testing Framework

### Backend Testing
```bash
# Run all backend tests
docker-compose exec backend pytest

# Run specific test categories
docker-compose exec backend pytest tests/excel/      # Excel generation
docker-compose exec backend pytest tests/api/       # API endpoints
docker-compose exec backend pytest tests/database/  # Database operations

# Run with coverage
docker-compose exec backend pytest --cov=app tests/

# Run specific test
docker-compose exec backend pytest tests/excel/test_formulas.py::test_dependency_formula -v
```

### Frontend Testing
```bash
# Run all frontend tests
docker-compose exec frontend npm test

# Run specific test categories
docker-compose exec frontend npm test -- --testPathPattern=components
docker-compose exec frontend npm test -- --testPathPattern=pages

# Run with coverage
docker-compose exec frontend npm run test:coverage

# Watch mode
docker-compose exec frontend npm run test:watch
```

### Integration Testing
```bash
# Test complete user workflows
docker-compose exec backend pytest tests/integration/ -v

# Test Excel generation end-to-end
docker-compose exec backend pytest tests/integration/test_excel_workflow.py
```

## 🔍 Code Quality Tools

### Automated Code Formatting
```bash
# Backend formatting
docker-compose exec backend black .
docker-compose exec backend isort .

# Frontend formatting
docker-compose exec frontend npm run lint:fix
```

### Code Quality Checks
```bash
# Backend linting
docker-compose exec backend flake8 .
docker-compose exec backend mypy app/

# Frontend linting
docker-compose exec frontend npm run lint
docker-compose exec frontend npm run type-check
```

### Pre-commit Hooks
```bash
# Install pre-commit hooks (optional but recommended)
pip install pre-commit
pre-commit install

# Manual run
pre-commit run --all-files
```

## 🐛 Debugging

### Backend Debugging
```bash
# View backend logs
docker-compose logs -f backend

# Debug specific requests
docker-compose exec backend python -c "
import requests
response = requests.get('http://localhost:8000/api/v1/projects')
print(response.status_code)
print(response.json())
"

# Access Python shell with app context
docker-compose exec backend python -c "
from app.main import app
from app.database.connection import get_database
# Interactive debugging here
"
```

### Frontend Debugging
```bash
# View frontend logs
docker-compose logs -f frontend

# Check Next.js build
docker-compose exec frontend npm run build

# Debug API calls
# Add console.log statements to frontend code
# They'll appear in: docker-compose logs frontend
```

### Database Debugging
```bash
# View database logs
docker-compose logs postgres

# Monitor database queries (development only)
# Add to backend/.env: DATABASE_LOGGING=true

# Connect to database directly
docker-compose exec postgres psql -U dev -d sprintforge
```

## 📦 Building and Deployment

### Production Build
```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Test production build locally
docker-compose -f docker-compose.prod.yml up
```

### Environment Configuration
```bash
# Development (.env.example)
DEBUG=true
DATABASE_URL=postgresql://dev:dev@postgres:5432/sprintforge
S3_ENDPOINT=http://minio:9000

# Production
DEBUG=false
DATABASE_URL=postgresql://user:pass@prod-db:5432/sprintforge
S3_BUCKET=sprintforge-prod
S3_ACCESS_KEY=prod-key
S3_SECRET_KEY=prod-secret
```

## 🚀 Performance Optimization

### Backend Performance
```bash
# Profile Excel generation
docker-compose exec backend python -c "
import time
from app.excel.engine import ExcelTemplateEngine

start = time.time()
# Generate Excel file
end = time.time()
print(f'Generation took {end - start:.2f} seconds')
"

# Database query profiling
# Add EXPLAIN ANALYZE to queries in development
```

### Frontend Performance
```bash
# Analyze bundle size
docker-compose exec frontend npm run build
docker-compose exec frontend npx @next/bundle-analyzer

# Performance testing
# Use Chrome DevTools on http://localhost:3000
```

## 🔐 Security Development

### Security Testing
```bash
# Dependency scanning
docker-compose exec backend pip-audit
docker-compose exec frontend npm audit

# Code security scanning
docker-compose exec backend bandit -r app/
```

### Secrets Management
```bash
# Never commit secrets to git
# Use .env files (gitignored)
# Rotate secrets regularly in production
# Use environment-specific secrets
```

## 📚 Documentation Development

### API Documentation
```bash
# Auto-generated API docs available at:
# http://localhost:8000/docs (Swagger UI)
# http://localhost:8000/redoc (ReDoc)

# Generate OpenAPI spec
curl http://localhost:8000/openapi.json > docs/api/openapi.json
```

### Formula Documentation
```bash
# Generate formula reference
python scripts/generate-formula-docs.py > docs/excel/formula-reference.md
```

## 🤝 Contribution Workflow

### Branch Management
```bash
# Create feature branch
git checkout -b feature/issue-123-excel-optimization

# Keep branch updated
git fetch origin
git rebase origin/main

# Push feature branch
git push origin feature/issue-123-excel-optimization
```

### Pull Request Checklist
- [ ] Tests pass locally
- [ ] Code formatted and linted
- [ ] Documentation updated
- [ ] Commit messages follow convention
- [ ] No secrets committed
- [ ] Performance impact considered

### Code Review Process
1. Automated CI checks run
2. Maintainer reviews code
3. Feedback addressed
4. Final approval and merge

## 🆘 Troubleshooting

### Common Issues

#### Docker Issues
```bash
# Clear Docker cache
docker system prune -a

# Rebuild containers
docker-compose down
docker-compose up --build

# Reset volumes (destroys data)
docker-compose down -v
```

#### Database Issues
```bash
# Reset database
docker-compose down
docker volume rm sprintforge_postgres_data
docker-compose up postgres -d

# Check database connection
docker-compose exec backend python -c "
import asyncpg
import asyncio
async def test():
    conn = await asyncpg.connect('postgresql://dev:dev@postgres:5432/sprintforge')
    result = await conn.fetchval('SELECT 1')
    print(f'Database connection: {result}')
    await conn.close()
asyncio.run(test())
"
```

#### Port Conflicts
```bash
# Check what's using ports
lsof -i :3000  # Frontend
lsof -i :8000  # Backend
lsof -i :5432  # PostgreSQL

# Kill processes if needed
kill -9 <PID>
```

### Getting Help
- Check GitHub Issues for known problems
- Join Discord for real-time help
- Review logs: `docker-compose logs <service>`
- Ask in GitHub Discussions

---

**Happy Developing! 🎉**

This development guide covers the technical setup and workflows. For contribution guidelines and community standards, see [CONTRIBUTING.md](CONTRIBUTING.md).