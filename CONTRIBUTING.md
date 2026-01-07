# Contributing to measure-ai-proficiency

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

Be respectful, inclusive, and considerate in all interactions. We're here to build something useful together.

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Git
- (Optional) PyYAML for `.ai-proficiency.yaml` support

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/pskoett/measuring-ai-proficiency.git
   cd measuring-ai-proficiency
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install in development mode**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Install pre-commit hooks** (optional but recommended)
   ```bash
   pip install pre-commit
   pre-commit install
   ```

5. **Run tests to verify setup**
   ```bash
   pytest
   ```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=measure_ai_proficiency --cov-report=html

# Run specific test file
pytest tests/test_scanner.py

# Run specific test
pytest tests/test_scanner.py::TestRepoScanner::test_claude_md_returns_level_2
```

### Code Quality

We use several tools to maintain code quality:

```bash
# Format code with black
black measure_ai_proficiency tests

# Lint with ruff
ruff check measure_ai_proficiency tests

# Type check with mypy
mypy measure_ai_proficiency
```

Or run all checks at once (if you installed pre-commit hooks):
```bash
pre-commit run --all-files
```

### Running the Tool Locally

```bash
# Run from source
python -m measure_ai_proficiency

# Scan a specific directory
python -m measure_ai_proficiency /path/to/repo

# Test different output formats
python -m measure_ai_proficiency --format json
python -m measure_ai_proficiency --format markdown
```

## Making Changes

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation changes
- `refactor/description` - Code refactoring
- `test/description` - Test additions/changes

### Commit Messages

Follow conventional commits format:

```
type(scope): short description

Longer explanation if needed.

- Bullet points for details
- Keep lines under 72 characters
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Test additions or changes
- `chore`: Build process or auxiliary tool changes

**Examples:**
```
feat(scanner): add cross-reference detection for AI instruction files

fix(reporter): correct progress bar display for custom thresholds

docs(readme): update installation instructions for PyPI

test(scanner): add tests for quality scoring calculation
```

### Pull Request Process

1. **Create a branch** from `main`
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clear, documented code
   - Add tests for new functionality
   - Update documentation as needed
   - Ensure all tests pass
   - Run code quality checks

3. **Update CHANGELOG.md**
   - Add your changes under `[Unreleased]`
   - Use appropriate section (Added, Changed, Fixed, etc.)

4. **Push your branch**
   ```bash
   git push -u origin feature/your-feature-name
   ```

5. **Create a Pull Request**
   - Use a clear, descriptive title
   - Reference any related issues
   - Describe what changed and why
   - Include any testing notes

6. **Address review feedback**
   - Respond to comments
   - Make requested changes
   - Push updates to the same branch

## What to Contribute

### Areas of Interest

- **New file patterns** - Add support for new AI tools or patterns
- **Quality metrics** - Improve content quality evaluation
- **Output formats** - Add new reporting formats
- **Documentation** - Improve guides, examples, and explanations
- **Tests** - Increase test coverage or add edge case tests
- **Bug fixes** - Fix issues reported in GitHub Issues
- **Performance** - Optimize scanning or analysis speed

### Ideas for Contributions

1. **Tool Support**
   - Add patterns for new AI coding tools
   - Improve detection accuracy for existing tools
   - Add tool-specific recommendations

2. **Scanning Features**
   - Support for remote repository scanning (GitHub API)
   - Historical tracking and trend analysis
   - Comparison between repositories
   - Team/organization dashboards

3. **Quality Metrics**
   - Additional quality indicators
   - Machine learning-based quality scoring
   - Best practice detection

4. **Integration**
   - IDE extensions (VS Code, JetBrains)
   - CI/CD plugins
   - GitHub App for automated scanning
   - Slack/Discord notifications

5. **Documentation**
   - Case studies and examples
   - Video tutorials
   - Blog posts about context engineering
   - Translation to other languages

## Adding New File Patterns

To add support for new AI context files:

1. **Edit `measure_ai_proficiency/config.py`**
   ```python
   # Add to appropriate level (2-8)
   LEVEL_X_PATTERNS = LevelConfig(
       name="Level X: Name",
       description="Description",
       file_patterns=[
           # Add your pattern here
           "YOUR_FILE.md",
           ".your-tool/config/*.yaml",
           # ...
       ],
       weight=1.0
   )
   ```

2. **Add tests** in `tests/test_scanner.py`
   ```python
   def test_your_new_pattern():
       with tempfile.TemporaryDirectory() as tmpdir:
           Path(tmpdir, "YOUR_FILE.md").write_text("content" + "x" * 200)
           scanner = RepoScanner(tmpdir)
           score = scanner.scan()
           assert score.level_scores.get(X).file_count > 0
   ```

3. **Update documentation**
   - Add pattern to README.md
   - Update CHANGELOG.md
   - Consider adding to CLAUDE.md

## Style Guide

### Python Style

- Follow PEP 8
- Use type hints for all function parameters and returns
- Maximum line length: 100 characters (configured in pyproject.toml)
- Use dataclasses for data structures
- Prefer pathlib.Path over os.path

### Documentation Style

- Use clear, concise language
- Include code examples
- Explain the "why" not just the "what"
- Keep line length reasonable (~80 chars for prose)

### Testing Style

- One test per behavior
- Use descriptive test names: `test_what_when_then`
- Use pytest fixtures for common setup
- Test edge cases and error conditions

## Questions?

- **GitHub Issues**: For bug reports and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Pull Requests**: For code contributions with questions in comments

Thank you for contributing to measure-ai-proficiency!
