# SprintForge Backend

FastAPI-based backend for SprintForge project management system with advanced scheduling algorithms and Excel generation capabilities.

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** (Python 3.12+ recommended)
- **uv** - Modern Python package manager ([Install uv](https://github.com/astral-sh/uv))
- **PostgreSQL 12+** (for full functionality)
- **Redis 6+** (for caching and background tasks)

### Installation

```bash
# 1. Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Navigate to backend directory
cd backend

# 3. Install dependencies (uv will create virtual environment automatically)
uv pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# 5. Run database migrations (when database is available)
# uv run alembic upgrade head

# 6. Start the development server
uv run python -m app.main
```

The API will be available at:
- **API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **API Docs (ReDoc)**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🧪 Running Tests

**CRITICAL**: This project uses `uv` for package management. All test commands MUST use `uv run` to ensure correct Python environment.

### Basic Test Commands

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/services/test_scheduler.py

# Run specific test class
uv run pytest tests/services/test_scheduler.py::TestTaskGraph

# Run specific test method
uv run pytest tests/services/test_scheduler.py::TestTaskGraph::test_add_node
```

### Test Coverage

```bash
# Run tests with coverage report
uv run pytest --cov=app tests/ --cov-report=term-missing

# Generate HTML coverage report
uv run pytest --cov=app tests/ --cov-report=html
# Open htmlcov/index.html in browser

# Check coverage for specific module
uv run pytest --cov=app.services.scheduler tests/services/scheduler/ --cov-report=term-missing
```

### Test Categories

```bash
# Run only unit tests
uv run pytest -m unit

# Run only integration tests
uv run pytest -m integration

# Run tests by directory
uv run pytest tests/api/           # API endpoint tests
uv run pytest tests/services/      # Service layer tests
uv run pytest tests/excel/         # Excel generation tests
uv run pytest tests/integration/   # Integration tests
```

### Parallel Test Execution

```bash
# Run tests in parallel (faster)
uv run pytest -n auto

# Run with specific number of workers
uv run pytest -n 4
```

## ⚠️ Common Issues & Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'openpyxl'` (or other packages)

**Cause**: Running `pytest` directly instead of `uv run pytest`

**Solution**: Always use `uv run`:
```bash
# ❌ WRONG - uses system Python
pytest

# ✅ CORRECT - uses uv-managed environment
uv run pytest
```

**Why**: This project uses `uv` to manage Python packages. Running `pytest` directly uses your system Python, which doesn't have the project dependencies installed.

### Issue: Tests collecting but failing to import `app.*` modules

**Cause**: Running pytest from wrong directory

**Solution**: Always run from `/backend` directory:
```bash
cd /path/to/sprintforge/backend
uv run pytest
```

### Issue: `ImportError: cannot import name 'X' from 'app.Y'`

**Solutions**:
1. Ensure you're in the backend directory
2. Verify dependencies are installed: `uv pip install -r requirements.txt`
3. Clear Python cache: `find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null`

### Issue: Database connection errors during tests

**Solution**: Tests use SQLite by default for unit tests. PostgreSQL tests are skipped automatically when database is unavailable.

To run PostgreSQL-dependent tests:
```bash
# Start PostgreSQL (if using Docker)
docker-compose up -d postgres

# Run all tests including PostgreSQL
uv run pytest
```

## 📁 Project Structure

```
backend/
├── app/
│   ├── api/                  # REST API endpoints
│   │   ├── endpoints/        # Route handlers
│   │   └── dependencies.py   # Dependency injection
│   ├── core/                 # Core configuration
│   │   ├── config.py         # Settings management
│   │   ├── security.py       # Security middleware
│   │   └── csrf.py           # CSRF protection
│   ├── models/               # SQLAlchemy database models
│   │   ├── project.py
│   │   ├── user.py
│   │   └── simulation_result.py
│   ├── services/             # Business logic layer
│   │   ├── scheduler/        # Scheduling algorithms
│   │   │   ├── task_graph.py
│   │   │   ├── cpm.py
│   │   │   └── work_calendar.py
│   │   ├── simulation/       # Monte Carlo simulation
│   │   │   ├── pert_distribution.py
│   │   │   ├── lhs_sampler.py
│   │   │   └── monte_carlo_engine.py
│   │   └── excel_generation_service.py
│   ├── excel/                # Excel generation engine
│   │   ├── engine.py
│   │   ├── templates/
│   │   └── components/
│   ├── schemas/              # Pydantic models (API schemas)
│   ├── utils/                # Utility functions
│   └── main.py               # Application entry point
├── tests/                    # Test suite
│   ├── api/                  # API endpoint tests
│   ├── services/             # Service layer tests
│   ├── excel/                # Excel generation tests
│   └── integration/          # Integration tests
├── requirements.txt          # Python dependencies
├── pytest.ini                # Pytest configuration
└── README.md                 # This file
```

## 🛠️ Development

### Code Quality Tools

```bash
# Format code with Black
uv run black app/ tests/

# Sort imports with isort
uv run isort app/ tests/

# Lint with flake8
uv run flake8 app/ tests/

# Type checking with mypy
uv run mypy app/
```

### Database Management

```bash
# Create new migration
uv run alembic revision --autogenerate -m "Description of changes"

# Apply migrations
uv run alembic upgrade head

# Rollback one migration
uv run alembic downgrade -1

# View migration history
uv run alembic history
```

### Running in Development Mode

```bash
# With auto-reload
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# With debug logging
uv run uvicorn app.main:app --reload --log-level debug
```

## 🐳 Docker Development

```bash
# Build and run with docker-compose
docker-compose up --build

# Run only backend service
docker-compose up backend

# Run with database services
docker-compose up postgres redis backend
```

## 🔧 Environment Variables

Create a `.env` file in the backend directory:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost/sprintforge

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret

# Redis
REDIS_URL=redis://localhost:6379

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# Environment
ENVIRONMENT=development
DEBUG=true
```

## 📊 API Documentation

Once the server is running, interactive API documentation is available:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Key API endpoints:

- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/projects` - List projects
- `POST /api/v1/projects` - Create project
- `POST /api/v1/projects/{id}/simulate` - Run Monte Carlo simulation
- `GET /api/v1/projects/{id}/excel` - Generate Excel file

## 🧪 Test Requirements

All new features must meet these quality standards:

- ✅ **Minimum 85% code coverage**
- ✅ **100% test pass rate**
- ✅ **All tests run with `uv run pytest`**
- ✅ **Type hints on all functions**
- ✅ **Docstrings on public APIs**

## 📚 Additional Documentation

- **Test Documentation**: See [tests/excel/README.md](tests/excel/README.md) for Excel test suite
- **Testing Guide**: See [TESTING.md](TESTING.md) for comprehensive testing guide
- **Project Documentation**: See [../claudedocs/](../claudedocs/) for implementation reports
- **Main README**: See [../README.md](../README.md) for overall project info

## 🤝 Contributing

1. Create feature branch: `git checkout -b feature/my-feature`
2. Write tests first (TDD approach)
3. Implement feature
4. Ensure tests pass: `uv run pytest`
5. Check coverage: `uv run pytest --cov=app tests/`
6. Format code: `uv run black app/ tests/`
7. Commit: `git commit -m "feat: add my feature"`
8. Push and create PR

## 📝 Key Technologies

- **FastAPI** - Modern async web framework
- **SQLAlchemy** - ORM with async support
- **Pydantic** - Data validation and settings
- **OpenPyXL** - Excel file generation
- **NumPy/SciPy** - Scientific computing for simulations
- **Redis** - Caching and task queue
- **PostgreSQL** - Primary database
- **pytest** - Testing framework

## 🎯 Key Features

### Scheduling Engine
- Task graph with dependency resolution
- Critical Path Method (CPM) calculation
- Work calendar with holiday support
- Resource-constrained scheduling

### Monte Carlo Simulation
- PERT and Triangular distributions
- Latin Hypercube Sampling
- Confidence interval calculation (P50, P75, P90, P95)
- Critical path probability analysis

### Excel Generation
- Macro-free XLSX generation
- 67 formula templates
- Gantt chart visualization
- Data validation and conditional formatting

## 📄 License

MIT License - see [../LICENSE](../LICENSE) for details.

---

**Need help?** Check [TESTING.md](TESTING.md) for detailed testing guide or create an issue on GitHub.
