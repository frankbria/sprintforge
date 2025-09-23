# Contributing to SprintForge

We love your input! We want to make contributing to SprintForge as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## Development Process

We use GitHub to host code, to track issues and feature requests, as well as accept pull requests.

### Pull Requests

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code lints.
6. Issue that pull request!

### Development Setup

See the [README.md](README.md) for detailed setup instructions.

## Coding Standards

### Python (Backend)

- Use Python 3.11+
- Follow PEP 8 style guidelines
- Use type hints for all function signatures
- Format code with Black: `black .`
- Sort imports with isort: `isort .`
- Lint with flake8: `flake8 .`
- Type check with mypy: `mypy app/`
- Write docstrings for all public functions

### TypeScript (Frontend)

- Use TypeScript strict mode
- Follow the existing ESLint configuration
- Format code with Prettier
- Use camelCase for variables and functions
- Use PascalCase for React components
- Write JSDoc comments for complex functions

### Testing

- Write tests for all new functionality
- Aim for >90% code coverage
- Use descriptive test names
- Backend: pytest with async support
- Frontend: Jest with React Testing Library

### Commit Messages

Use conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Changes that do not affect the meaning of the code
- `refactor`: A code change that neither fixes a bug nor adds a feature
- `test`: Adding missing tests or correcting existing tests
- `chore`: Changes to the build process or auxiliary tools

Examples:
```
feat(backend): add Monte Carlo simulation engine
fix(frontend): resolve sprint date calculation bug
docs: update API documentation for sync endpoints
```

## Bug Reports

We use GitHub issues to track public bugs. Report a bug by [opening a new issue](https://github.com/frankbria/sprintforge/issues/new).

**Great Bug Reports** tend to have:

- A quick summary and/or background
- Steps to reproduce
  - Be specific!
  - Give sample code if you can
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

## Feature Requests

We welcome feature requests! Please:

1. Check if the feature is already requested
2. Explain the use case and why it's important
3. Consider if it fits with the project's goals
4. Be willing to help implement it

## Licensing

When you submit code changes, your submissions are understood to be under the same [MIT License](LICENSE) that covers the project.

## Architecture Decisions

### Backend Structure

```
backend/
├── app/
│   ├── api/          # API routes and endpoints
│   ├── core/         # Configuration and security
│   ├── models/       # Database models
│   ├── services/     # Business logic
│   └── utils/        # Utility functions
└── tests/           # Test files mirroring app structure
```

### Frontend Structure

```
frontend/
├── app/             # Next.js App Router pages
├── components/      # Reusable React components
├── lib/            # Utility libraries and API clients
└── __tests__/      # Test files
```

### Design Principles

1. **Security First**: All features must consider enterprise security requirements
2. **Performance**: Excel generation must be fast (< 2s for 500 tasks)
3. **Compatibility**: Support Excel 2016+ without macros
4. **Testing**: High test coverage with both unit and integration tests
5. **Documentation**: All public APIs must be documented

## Getting Help

- Join our [Discord community](https://discord.gg/sprintforge)
- Check the [documentation](https://docs.sprintforge.com)
- Search existing [GitHub issues](https://github.com/frankbria/sprintforge/issues)
- Start a [GitHub discussion](https://github.com/frankbria/sprintforge/discussions)

## Recognition

Contributors will be recognized in:
- The project README
- Release notes for significant contributions
- The project's contributors page

Thank you for contributing to SprintForge! 🚀