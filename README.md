# SprintForge

> **Open-source, macro-free project management system that generates sophisticated Excel spreadsheets with Gantt chart capabilities and probabilistic timeline predictions.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![TypeScript](https://img.shields.io/badge/typescript-5.0+-blue.svg)](https://www.typescriptlang.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-15+-black.svg)](https://nextjs.org/)

## 🚀 Overview

SprintForge addresses the critical gap between sophisticated project management capabilities and enterprise security requirements. Unlike existing solutions that rely on macros or proprietary formats, SprintForge generates pure XLSX files with complex formulas, making them compatible with any Excel version while maintaining enterprise-grade security.

### 🎯 Core Differentiators

- **🔒 Macro-free architecture** - Enterprise deployable without security warnings
- **📊 Sprint-native planning** - First-class support for agile methodologies  
- **📈 Probabilistic scheduling** - Monte Carlo simulations for confidence intervals
- **👥 Collaboration layer** - Multi-user updates with Excel as source of truth
- **🌟 Truly open source** - MIT licensed core with transparent pricing
- **🤖 AI-enhanced** - Optional AI assistance for planning and estimation

## 📁 Project Structure

```
sprintforge/
├── backend/           # FastAPI Python backend
│   ├── app/          # Application code
│   │   ├── api/      # API endpoints
│   │   ├── core/     # Core configuration
│   │   ├── models/   # Database models
│   │   ├── services/ # Business logic
│   │   └── utils/    # Utility functions
│   ├── tests/        # Backend tests
│   └── requirements.txt
├── frontend/         # Next.js TypeScript frontend
│   ├── app/         # App Router pages
│   ├── components/  # Reusable components
│   ├── lib/         # Utility libraries
│   └── public/      # Static assets
├── core/            # Core scheduling algorithms (MIT)
├── docs/           # Documentation
├── tests/          # Integration tests
└── scripts/        # Deployment and utility scripts
```

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI with Python 3.11+
- **Database**: PostgreSQL with SQLAlchemy
- **Cache**: Redis
- **Excel Processing**: OpenPyXL with advanced formula generation
- **Authentication**: JWT with FastAPI-authentication
- **Background Tasks**: Celery
- **Testing**: pytest with pytest-cov and pytest-asyncio

### Frontend
- **Framework**: Next.js 15+ with TypeScript
- **Authentication**: NextAuth.js
- **State Management**: TanStack Query (React Query)
- **Styling**: TailwindCSS
- **Testing**: Jest with React Testing Library
- **API Client**: Axios

### Core Engine
- **Language**: Python (NumPy, Pandas for calculations)
- **Dependencies**: Pure Python dependency solver
- **Sprint Calculator**: Custom sprint pattern support
- **Monte Carlo**: Probabilistic simulation engine

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 12+
- Redis 6+

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/frankbria/sprintforge.git
   cd sprintforge
   ```

2. **Set up the backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   
   # Copy environment template
   cp .env.example .env
   # Edit .env with your configuration
   
   # Run the backend
   python -m app.main
   ```

3. **Set up the frontend**
   ```bash
   cd ../frontend
   npm install
   
   # Copy environment template
   cp .env.example .env.local
   # Edit .env.local with your configuration
   
   # Run the frontend
   npm run dev
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Live Demo: https://SprintForge.app

### Docker Development

```bash
# Build and run with docker-compose
docker-compose up --build

# Or run individual services
docker-compose up backend
docker-compose up frontend
```

## 🎯 Key Features

### Version 1.0 - Core MVP (Target: Q2 2025)

#### ✅ Sprint Planning Engine
- Custom sprint pattern definition (YY.Q.WW, PI-N.Sprint-M, etc.)
- Sprint duration configuration with blackout period support
- Sprint-to-date conversion with velocity tracking

#### ✅ Task Management  
- Task creation with dependencies and parent-child hierarchies
- Work breakdown structure (WBS) with duration estimation
- Progress tracking with multiple dependency types (FS, SS, FF, SF)

#### ✅ Excel Generation
- Clean XLSX output with no macros required
- Interactive dropdowns via data validation
- Conditional formatting for timeline visualization
- Formula-based date calculations with print-optimized layouts

### Version 1.5 - Collaboration Layer (Target: Q3 2025)

#### 🔄 Two-Way Sync
- Excel upload and parsing with change detection
- Conflict resolution with audit trail
- Version history with rollback capabilities

#### 👥 Multi-User Features
- Web-based task updates with comment system
- Email notifications and change tracking
- Role-based access (viewer, editor, owner)

### Version 2.0 - Intelligence Layer (Target: Q4 2025)

#### 🎲 Monte Carlo Simulation
- Three-point estimation with historical analysis
- Confidence intervals (50%, 75%, 90%, 95%)
- Risk-adjusted critical path with buffer calculation

#### 🤖 AI Planning Assistant
- Natural language project creation
- Task breakdown suggestions with duration estimation
- Dependency inference and risk identification

## 🔧 Configuration

### Backend Configuration

Key environment variables in `backend/.env`:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost/sprintforge

# Security
SECRET_KEY=your-secret-key-here

# Redis
REDIS_URL=redis://localhost:6379

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

### Frontend Configuration

Key environment variables in `frontend/.env.local`:

```env
# API
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# Authentication
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-nextauth-secret
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest
pytest --cov=app tests/  # With coverage
pytest -v  # Verbose output
```

### Frontend Tests
```bash
cd frontend
npm test
npm run test:coverage
npm run test:watch
```

### Integration Tests
```bash
# Run from project root
python -m pytest tests/integration/
```

## 🚀 Deployment

### Production Deployment

1. **Using Docker**
   ```bash
   # Build production images
   docker-compose -f docker-compose.prod.yml build
   
   # Deploy
   docker-compose -f docker-compose.prod.yml up -d
   ```

2. **Manual Deployment**
   - Set up PostgreSQL and Redis
   - Configure environment variables
   - Build and deploy backend with uvicorn
   - Build and deploy frontend with static export

### Environment-Specific Configurations

- **Development**: Full debugging, auto-reload
- **Staging**: Production-like with debug endpoints
- **Production**: Optimized, secure, monitored

## 📊 Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Web Interface (React/TypeScript)      │
├─────────────────────────────────────────────────────────┤
│                    API Layer (Python/FastAPI)            │
├─────────────────────────────────────────────────────────┤
│  Core Engine (Python)  │  AI Services  │  Export Engine │
│  - Dependency Solver   │  - Planning   │  - Excel Gen   │
│  - Sprint Calculator   │  - Estimation │  - PDF Export  │
│  - Monte Carlo Sim     │  - NLP Parser │  - API Export  │
└─────────────────────────────────────────────────────────┘
```

### Excel-Server Sync Architecture

SprintForge implements enterprise-friendly two-way synchronization:

1. **Upload Direction (Excel → Server)**
   - File validation and macro stripping
   - Change detection via embedded metadata
   - Conflict resolution with audit trail
   
2. **Download Direction (Server → Excel)**
   - Smart formula generation
   - Preservation of user customizations
   - Version tracking and change highlighting

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following our coding standards
4. Add tests for new functionality
5. Run the test suite (`npm test` and `pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Coding Standards

- **Python**: Black formatting, type hints required, docstrings for all functions
- **TypeScript**: ESLint + Prettier, strict mode enabled
- **Testing**: Aim for >90% code coverage
- **Commits**: Conventional commit format

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Licensing Model
- **Core Engine**: MIT License (fully open)
- **API & Web UI**: MIT License  
- **Enterprise Features**: Commercial license (future)
- **Documentation**: Creative Commons BY-SA 4.0

## 🛟 Support & Community

- **Live Demo**: [SprintForge.app](https://SprintForge.app)
- **Documentation**: [docs.sprintforge.com](https://docs.sprintforge.com)
- **Issues**: [GitHub Issues](https://github.com/frankbria/sprintforge/issues)
- **Discussions**: [GitHub Discussions](https://github.com/frankbria/sprintforge/discussions)
- **Discord**: [SprintForge Community](https://discord.gg/sprintforge)

## 🗺️ Roadmap

- **Q2 2025**: Version 1.0 - Core MVP with sprint planning and Excel generation
- **Q3 2025**: Version 1.5 - Collaboration features and two-way sync  
- **Q4 2025**: Version 2.0 - AI assistance and Monte Carlo simulations
- **Q1 2026**: Version 2.5 - Enterprise features and integrations
- **Q2 2026**: Version 3.0 - Multi-project management and mobile apps

## 🙏 Acknowledgments

- Inspired by the need for macro-free project management in enterprise environments
- Built with modern web technologies and best practices
- Community-driven development with transparent governance

---

**SprintForge** - Making sophisticated project management accessible to everyone, without compromising on security or collaboration.