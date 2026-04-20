# Contributing to PBL

Thank you for your interest in contributing to the PBL project! We appreciate all contributions, whether they're bug reports, feature requests, documentation improvements, or code contributions.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/PBL.git`
3. Create a feature branch: `git checkout -b feature/your-feature`
4. Make your changes
5. Commit your changes: `git commit -m 'Add your feature'`
6. Push to your fork: `git push origin feature/your-feature`
7. Create a Pull Request

## Development Setup

See the [README.md](README.md) for detailed setup instructions for both backend and frontend development.

## Reporting Issues

When reporting issues, please include:
- A clear description of the issue
- Steps to reproduce
- Expected behavior
- Actual behavior
- Screenshots (if applicable)
- System information (OS, Python version, Node version)

## Code Style

### Python
- Follow PEP 8 guidelines
- Use meaningful variable names
- Add docstrings to functions and classes
- Aim for > 80% code coverage

```bash
# Lint your code
pylint backend/*.py

# Format code
python -m black backend/
```

### TypeScript/React
- Follow ESLint configuration
- Use meaningful component names
- Add comments for complex logic
- Keep components focused and reusable

```bash
# Lint
npm run lint

# Format
npm run format
```

## Commit Messages

Use clear, descriptive commit messages:
- ✨ `feat: Add new feature description`
- 🐛 `fix: Fix bug description`
- 📝 `docs: Documentation updates`
- 🎨 `refactor: Code refactoring`
- 🧪 `test: Add/update tests`
- ⚡ `perf: Performance improvements`

## Pull Request Process

1. Update README.md with new features or changes
2. Add tests for new functionality
3. Ensure all tests pass: `pytest` (backend), `npm run test` (frontend)
4. Update documentation if needed
5. Provide a clear description of changes in the PR

## Areas for Contribution

### Backend
- Improve ML model accuracy
- Add new retrieval methods
- Optimize performance
- Enhance error handling
- Write tests

### Frontend
- Improve UI/UX
- Add new components
- Enhance accessibility
- Improve performance
- Write tests

### Documentation
- Improve README
- Add API documentation
- Create tutorials
- Add code examples
- Improve docstrings

## Questions?

- Open an issue with your question
- Start a discussion
- Check existing documentation

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for making PBL better! 🙌
