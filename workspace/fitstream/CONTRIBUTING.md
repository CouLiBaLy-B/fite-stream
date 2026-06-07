# 🤝 Contributing to FitStream

Thank you for your interest in contributing to FitStream! This document provides guidelines for contributing.

## Getting Started

### 1. Fork and Clone

```bash
git clone https://github.com/YOUR_USERNAME/fitstream.git
cd fitstream
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies (no GPU needed for development)
pip install pyyaml loguru click rich pydantic pytest
pip install fastapi uvicorn python-multipart httpx
pip install pillow numpy scipy opencv-python-headless imageio
pip install ruff black

# Run tests to verify setup
PYTHONPATH=. python -m pytest tests/ -v
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

## Development Workflow

### Code Style

- **Python**: Formatted with `black`, linted with `ruff`
- **Docstrings**: Google style
- **Type hints**: Required for public functions
- **Max line length**: 100 characters

```bash
# Format code
black fitstream/ tests/

# Lint
ruff check fitstream/ tests/

# Fix lint errors automatically
ruff check --fix fitstream/ tests/
```

### Running Tests

```bash
# All tests (no GPU needed)
PYTHONPATH=. python -m pytest tests/ -v

# Specific test file
PYTHONPATH=. python -m pytest tests/test_api.py -v

# With coverage
PYTHONPATH=. python -m pytest tests/ --cov=fitstream --cov-report=html
```

### End-to-End Demo

```bash
# Verify the full pipeline works (no GPU)
PYTHONPATH=. python scripts/demo.py
```

## What to Contribute

### Good First Issues
- Add more visual styles to `prompt_utils.py`
- Add garment keywords to `tryon.py` categories
- Improve image quality analysis in `preprocessing.py`
- Add more unit tests for edge cases
- Documentation improvements

### Medium Contributions
- New pipeline (e.g., style transfer, face swap)
- Frontend improvements (new tab, better UX)
- CLI enhancements
- Performance optimizations

### Large Contributions
- New model integration (e.g., native LoomVideo, SkyReels)
- Mobile app (React Native)
- E-commerce integrations (Shopify plugin)
- Distributed job queue (Redis/Celery)

## Pull Request Process

1. **Tests**: All 70+ tests must pass
2. **Lint**: No ruff/black errors
3. **Demo**: `scripts/demo.py` must run without errors
4. **Docs**: Update relevant documentation
5. **Changelog**: Add entry to `CHANGELOG.md`

### PR Template

```markdown
## What does this PR do?
Brief description.

## Type of change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation

## Checklist
- [ ] Tests pass (`pytest tests/ -v`)
- [ ] Code formatted (`black`)
- [ ] Lint clean (`ruff check`)
- [ ] Demo runs (`python scripts/demo.py`)
- [ ] Docs updated (if applicable)
```

## Project Structure

```
fitstream/
├── fitstream/           # Main Python package
│   ├── api/             # REST API + WebSocket
│   ├── core/            # Core logic
│   │   ├── models/      # Model management
│   │   ├── pipelines/   # Generation pipelines (animate, story, tryon, loom, extend)
│   │   └── utils/       # Shared utilities
│   ├── cli.py           # CLI interface
│   └── config.py        # Configuration
├── frontend/            # Web UI (single HTML file)
├── tests/               # Test suite
├── docs/                # Documentation
├── scripts/             # Setup & utility scripts
└── config/              # YAML configuration
```

## Code of Conduct

Be respectful, inclusive, and constructive. We're all here to build something great.

## Questions?

Open a GitHub Issue or Discussion. We're happy to help!
