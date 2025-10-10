# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SprintForge is an open-source, macro-free project management system that generates sophisticated Excel spreadsheets with Gantt chart capabilities and probabilistic timeline predictions. It's built as a monorepo with separate backend and frontend applications.

## Architecture

This is a full-stack application with:
- **Backend**: FastAPI (Python 3.11+) with PostgreSQL database
- **Frontend**: Next.js 15+ with TypeScript and React 19
- **Core**: Python scheduling algorithms and Excel generation engine
- **Infrastructure**: Docker Compose for development, Redis for caching

## Development Commands

### Backend (FastAPI)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m app.main  # Starts on http://localhost:8000
```

### Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev        # Development server on http://localhost:3000
npm run build      # Production build
npm run lint       # ESLint
npm run type-check # TypeScript checking
```

### Testing
```bash
# Backend tests
cd backend && pytest
pytest --cov=app tests/  # With coverage
pytest -v               # Verbose

# Frontend tests
cd frontend && npm test
npm run test:coverage    # With coverage
npm run test:watch       # Watch mode

# Integration tests (from project root)
python -m pytest tests/integration/
```

### Code Quality
```bash
# Python (backend)
cd backend
black .              # Code formatting
isort .              # Import sorting
flake8 .             # Linting
mypy app/            # Type checking

# TypeScript (frontend)
cd frontend
npm run lint         # ESLint + Prettier
npm run type-check   # TypeScript validation
```

### Docker Development
```bash
# Full stack with docker-compose
docker-compose up --build

# Individual services
docker-compose up backend
docker-compose up frontend
```

## Project Structure

### Backend (`/backend/app/`)
- `main.py` - FastAPI application entry point with CORS, middleware, and structured logging
- `core/config.py` - Centralized configuration using Pydantic Settings with environment variables
- `api/` - REST API endpoints and routers
- `models/` - SQLAlchemy database models
- `services/` - Business logic layer
- `utils/` - Utility functions and helpers

### Frontend (`/frontend/`)
- `app/` - Next.js App Router pages and layouts
- `components/` - Reusable React components
- `lib/` - Utility libraries and API clients

### Core (`/core/`)
- Python algorithms for scheduling, dependency solving, and Excel generation
- Sprint calculation and Monte Carlo simulation engines

## Key Technologies & Patterns

### Backend Stack
- **FastAPI**: Async web framework with automatic OpenAPI documentation
- **SQLAlchemy**: ORM with async PostgreSQL support (`asyncpg`)
- **Pydantic**: Data validation and settings management
- **Structlog**: Structured JSON logging
- **Celery**: Background task processing with Redis
- **OpenPyXL**: Excel file generation without macros

### Frontend Stack
- **Next.js 15**: React framework with App Router
- **TypeScript**: Strict typing enabled
- **TanStack Query**: Server state management
- **NextAuth.js**: Authentication
- **TailwindCSS**: Utility-first styling
- **Axios**: HTTP client

### Development Patterns
- Environment-based configuration using `.env` files
- Async/await throughout the backend
- Type hints required for all Python functions
- Structured logging with contextual information
- Test-driven development with high coverage targets (>90%)

## Environment Setup

### Backend Environment (`.env`)
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost/sprintforge
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key
ENVIRONMENT=development
DEBUG=true
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

### Frontend Environment (`.env.local`)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-nextauth-secret
```

## Coding Standards

### Python (Backend)
- Black formatting (line length 88)
- Import sorting with isort (Black profile)
- Type hints required (`mypy` strict mode)
- Docstrings for all public functions
- Async/await for all I/O operations

### TypeScript (Frontend)
- Strict TypeScript mode enabled
- ESLint with Next.js configuration
- Prettier for code formatting
- React 19 with hooks and functional components
- TanStack Query for server state

## Database & Migrations

- SQLAlchemy with Alembic for migrations
- PostgreSQL as primary database
- Redis for caching and Celery task queue
- Database models in `backend/app/models/`

## Excel Generation Architecture

SprintForge's core differentiator is generating sophisticated Excel files without macros:
- Pure XLSX format using OpenPyXL
- Complex formulas for date calculations and Gantt charts
- Data validation for interactive dropdowns
- Conditional formatting for visual timelines
- Enterprise-compatible (no security warnings)

## API Documentation

- Development: http://localhost:8000/docs (Swagger UI)
- Alternative: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json
- API prefix: `/api/v1`

## Feature Development Quality Standards

**CRITICAL**: All new features MUST meet the following mandatory requirements before being considered complete.

### Testing Requirements

- **Minimum Coverage**: 85% code coverage ratio required for all new code
- **Test Pass Rate**: 100% - all tests must pass, no exceptions
- **Test Types Required**:
  - Unit tests for all business logic and services
  - Integration tests for API endpoints
  - End-to-end tests for critical user workflows (using Playwright when applicable)
- **Coverage Validation**: Run coverage reports before marking features complete:
  ```bash
  # Backend
  pytest --cov=app tests/ --cov-report=term-missing

  # Frontend
  npm run test:coverage
  ```
- **Test Quality**: Tests must validate behavior, not just achieve coverage metrics
- **Test Documentation**: Complex test scenarios must include comments explaining the test strategy

### Git Workflow Requirements

Before moving to the next feature, ALL changes must be:

1. **Committed with Clear Messages**:
   ```bash
   git add .
   git commit -m "feat(module): descriptive message following conventional commits"
   ```
   - Use conventional commit format: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, etc.
   - Include scope when applicable: `feat(api):`, `fix(frontend):`, `test(services):`
   - Write descriptive messages that explain WHAT changed and WHY

2. **Pushed to Remote Repository**:
   ```bash
   git push origin <branch-name>
   ```
   - Never leave completed features uncommitted
   - Push regularly to maintain backup and enable collaboration
   - Ensure CI/CD pipelines pass before considering feature complete

3. **Branch Hygiene**:
   - Work on feature branches, never directly on `main`
   - Branch naming convention: `feature/<feature-name>`, `fix/<issue-name>`, `docs/<doc-update>`
   - Create pull requests for all significant changes

### Documentation Requirements

**ALL implementation documentation MUST remain synchronized with the codebase**:

1. **API Documentation**:
   - Update OpenAPI specifications when endpoints change
   - Document all request/response schemas
   - Include example requests and responses
   - Document error responses and status codes

2. **Code Documentation**:
   - Python: Docstrings for all public functions, classes, and modules
   - TypeScript: JSDoc comments for complex functions and components
   - Update inline comments when implementation changes
   - Remove outdated comments immediately

3. **Implementation Documentation**:
   - Update relevant markdown files in `claudedocs/` directory
   - Keep architecture diagrams current
   - Update configuration examples when defaults change
   - Document breaking changes prominently

4. **README Updates**:
   - Keep feature lists current
   - Update setup instructions when dependencies change
   - Maintain accurate command examples
   - Update version compatibility information

5. **CLAUDE.md Maintenance**:
   - Add new patterns to "Development Patterns" section
   - Update "Key Technologies & Patterns" when stack changes
   - Keep command examples accurate and tested
   - Document new testing patterns or quality gates

### Feature Completion Checklist

Before marking ANY feature as complete, verify:

- [ ] All tests pass (`pytest` for backend, `npm test` for frontend)
- [ ] Code coverage meets 85% minimum threshold
- [ ] Coverage report reviewed for meaningful test quality
- [ ] Code formatted and linted (Black, isort, flake8, ESLint)
- [ ] Type checking passes (mypy for Python, tsc for TypeScript)
- [ ] All changes committed with conventional commit messages
- [ ] All commits pushed to remote repository
- [ ] API documentation updated (if applicable)
- [ ] Implementation documentation updated
- [ ] Inline code comments updated or added
- [ ] CLAUDE.md updated (if new patterns introduced)
- [ ] Breaking changes documented
- [ ] CI/CD pipeline passes

### Rationale

These standards ensure:
- **Quality**: High test coverage and pass rates prevent regressions
- **Traceability**: Git commits provide clear history of changes
- **Maintainability**: Current documentation reduces onboarding time and prevents knowledge loss
- **Collaboration**: Pushed changes enable team visibility and code review
- **Reliability**: Consistent quality gates maintain production stability

**Enforcement**: AI agents should automatically apply these standards to all feature development tasks without requiring explicit instruction for each task.