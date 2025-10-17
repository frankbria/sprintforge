# SprintForge

> **Open-source, macro-free project management system that generates sophisticated Excel spreadsheets with Gantt chart capabilities and probabilistic timeline predictions.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![TypeScript](https://img.shields.io/badge/typescript-5.0+-blue.svg)](https://www.typescriptlang.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-15.5.3-black.svg)](https://nextjs.org/)
[![React](https://img.shields.io/badge/React-19.1.0-blue.svg)](https://reactjs.org/)

## 🚀 Overview

SprintForge addresses the critical gap between sophisticated project management capabilities and enterprise security requirements. Unlike existing solutions that rely on macros or proprietary formats, SprintForge generates pure XLSX files with complex formulas, making them compatible with any Excel version while maintaining enterprise-grade security.

### 🎯 Core Differentiators

- **🔒 Macro-free architecture** - Enterprise deployable without security warnings
- **📊 Sprint-native planning** - First-class support for agile methodologies  
- **📈 Probabilistic scheduling** - Monte Carlo simulations for confidence intervals
- **👥 Collaboration layer** - Multi-user updates with Excel as source of truth
- **🌟 Truly open source** - MIT licensed core with transparent pricing
- **🤖 AI-enhanced** - Optional AI assistance for planning and estimation

## 📊 Current Development Status

**Version**: 1.0 (MVP) - **IN PROGRESS**
**Last Updated**: October 17, 2025
**Sprint**: Sprint 4 Complete | Sprint 5 Planning

### ✅ Completed Milestones
- **Sprint 1-2**: Authentication & User Management (100% complete)
- **Sprint 3**: Excel Generation Engine (100% complete)
- **Sprint 4**: Project Management API (100% complete - all 6 tasks done)
- **Task 5.1**: Advanced Monte Carlo Simulation (100% complete - all 4 phases)
- **Task 5.2**: Critical Path Enhancement with CCPM (100% complete - all 4 phases)

### ✅ Sprint 4 - ALL TASKS COMPLETE
- ✅ Task 4.1: Project CRUD API
- ✅ Task 4.2: Excel Generation API
- ✅ Task 4.3: Rate Limiting & Abuse Prevention
- ✅ Task 4.4: Public Sharing System
- ✅ Task 4.5: Project Setup Wizard
- ✅ Task 4.6: Project Dashboard

### 🎯 Next Up
- **Sprint 5**: Advanced Features & Analytics (planning phase)
- Sprint 6: Collaboration & Real-time Updates (Q1 2026)

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
│   │   ├── ui/      # Base UI components (Card, Input, Progress, etc.)
│   │   └── wizard/  # Project setup wizard components
│   ├── hooks/       # Custom React hooks
│   ├── lib/         # Utility libraries and API clients
│   ├── types/       # TypeScript type definitions
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
- **Framework**: Next.js 15.5.3 with App Router
- **UI Library**: React 19.1.0
- **Language**: TypeScript 5+
- **Authentication**: NextAuth.js 4.24+
- **Forms**: React Hook Form 7.65+ with Zod validation
- **State Management**: TanStack Query (React Query)
- **UI Components**: Radix UI primitives with custom components
- **Styling**: TailwindCSS v4 with Framer Motion animations
- **Icons**: Lucide React
- **Testing**: Jest with React Testing Library
- **API Client**: Axios 1.12+

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
   - API Documentation (Swagger): http://localhost:8000/docs
   - API Documentation (ReDoc): http://localhost:8000/redoc

### Docker Development

```bash
# Build and run with docker-compose
docker-compose up --build

# Or run individual services
docker-compose up backend
docker-compose up frontend
```

## 🎯 Key Features

### ✅ Completed Features (Version 1.0 MVP)

#### 🔐 Authentication & User Management
- **User Registration & Login** - Secure JWT-based authentication
- **Email Verification** - Automated verification flow
- **Session Management** - NextAuth.js integration
- **User Profiles** - Profile management and settings

#### 📊 Sprint Planning Engine
- **Custom Sprint Patterns** - 4 pattern types (YY.Q.#, PI-Sprint, Sequential, YY.WW)
- **Sprint Configuration** - Duration (1-8 weeks), working days, hours per day
- **Holiday Calendars** - Preset calendars (US, UK, EU) + custom holidays
- **Sprint Calculator** - Automatic sprint-to-date conversion

#### 📋 Project Management
- **Project CRUD API** - Complete project lifecycle management
- **Project Wizard** - 6-step guided project setup
  - Project basics and template selection
  - Sprint configuration with live preview
  - Holiday calendar management
  - Advanced feature toggles
  - Configuration review and creation
- **Template System** - 5 predefined templates (Agile/Waterfall/Hybrid)
- **Configuration Storage** - JSONB-based flexible configuration

#### 📈 Excel Generation Engine
- **Template Generation** - Clean XLSX output with no macros
- **Formula Engine** - 67 formula templates across 8 categories
- **Gantt Charts** - Visual timeline with conditional formatting
- **Interactive Features** - Data validation dropdowns
- **Advanced Analytics** - Critical Path, EVM, Monte Carlo simulation support
- **Excel API** - Streaming response for large files
- **Cross-platform** - Windows, Mac, Web Excel compatibility

#### 🔗 Sharing & Collaboration
- **Public Sharing** - Secure "viewable by link" functionality
- **Access Control** - Token-based public access
- **Share Management** - Enable/disable/revoke share links
- **Rate Limiting** - Abuse prevention (100 req/min, 1000 req/hour)

### 🚀 Recently Completed (October 2025)

#### 📊 Advanced Monte Carlo Simulation (Task 5.1)
- **Phase A**: Foundation scheduler with CPM and dependency resolution
- **Phase B**: Monte Carlo engine with LHS sampling and PERT distributions
- **Phase C**: REST API integration with database persistence
- **Phase D**: Complete Excel workflow (upload → simulate → download)
- **Quality**: 85%+ test coverage, 100% pass rate, performance targets exceeded

#### 🎯 Critical Path Enhancement (Task 5.2)
- Resource management and allocation
- Resource-constrained scheduling
- CCPM buffer management
- Risk integration with Monte Carlo analysis

#### 📊 Project Dashboard (Task 4.6)
- Project listing and management interface
- Quick actions and project statistics
- Recent activity feed
- Full-featured responsive UI

### 🔮 Planned Features (Future Versions)

#### Version 1.5 - Collaboration Layer (Q1 2026)
- **Two-Way Sync** - Excel upload and parsing with change detection
- **Conflict Resolution** - Audit trail and version history
- **Multi-User Updates** - Real-time collaboration
- **Comment System** - Task-level discussions
- **Notifications** - Email and in-app notifications

#### Version 2.0 - Intelligence Layer (Q2 2026)
- **Advanced Monte Carlo** - Enhanced probabilistic scheduling
- **AI Planning Assistant** - Natural language project creation
- **Task Recommendations** - AI-powered task breakdown
- **Dependency Inference** - Automatic dependency detection
- **Risk Analysis** - Predictive risk identification

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

**IMPORTANT**: This project uses `uv` for Python package management. Always run tests with `uv run`:

```bash
cd backend
uv run pytest                          # Run all tests
uv run pytest --cov=app tests/        # With coverage
uv run pytest -v                      # Verbose output
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

### Quick Links for Contributors

- **Development Setup**: See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed setup
- **Claude Code Guide**: See [CLAUDE.md](CLAUDE.md) for AI-assisted development
- **Test Documentation**: See [tests/docs/](tests/docs/) for testing guides
- **Sprint History**: See [docs/archive/](docs/archive/) for completed sprint tasks

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
- **Testing**: Aim for >90% code coverage (see [tests/docs/](tests/docs/))
- **Commits**: Conventional commit format

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Licensing Model
- **Core Engine**: MIT License (fully open)
- **API & Web UI**: MIT License  
- **Enterprise Features**: Commercial license (future)
- **Documentation**: Creative Commons BY-SA 4.0

## 🛟 Support & Community

- **GitHub Issues**: [Report Bugs & Request Features](https://github.com/frankbria/sprintforge/issues)
- **GitHub Discussions**: [Community Q&A](https://github.com/frankbria/sprintforge/discussions)
- **Documentation**: See [docs/](docs/) directory for technical guides
- **Contributing**: See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines
- **Development Guide**: See [CLAUDE.md](CLAUDE.md) for AI-assisted development

> **Note**: Live demo and community Discord coming with Version 1.0 release

## 🗺️ Roadmap

### Completed
- **✅ Q1-Q2 2025**: Sprints 1-2 - Authentication & User Management
- **✅ Q3 2025**: Sprint 3 - Excel Generation Engine (67 formulas, 5 templates, 150+ tests)
- **✅ Q4 2025**: Sprint 4 - Project Management API (100% complete - all 6 tasks done)
- **✅ October 2025**: Tasks 5.1 & 5.2 - Monte Carlo Simulation & Critical Path Enhancement

### Upcoming
- **Q4 2025**: Sprint 5 - Advanced Features & Analytics
- **Q1 2026**: Sprint 6 - Collaboration & Real-time Updates (Version 1.5)
- **Q2 2026**: Version 2.0 - AI assistance and enhanced Monte Carlo
- **Q3 2026**: Version 2.5 - Enterprise features and integrations
- **Q4 2026**: Version 3.0 - Multi-project portfolio management

## 🙏 Acknowledgments

- Inspired by the need for macro-free project management in enterprise environments
- Built with modern web technologies and best practices
- Community-driven development with transparent governance

---

**SprintForge** - Making sophisticated project management accessible to everyone, without compromising on security or collaboration.