# Contributing to measure-ai-proficiency

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

Be respectful, inclusive, and considerate in all interactions. We're here to build something useful together.

## Getting Started

### Prerequisites

- Python 3.10 or higher
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
   pytest tests/ -v
   ```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=measure_ai_proficiency --cov-report=html

# Run specific test file
pytest tests/test_scanner.py -v

# Run specific test
pytest tests/test_scanner.py::TestRepoScanner::test_claude_md_returns_level_2 -v
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

## Agent Factory Chain

This repository uses a 10-workflow agent factory built on [GitHub Agentic Workflows (gh-aw)](https://github.github.com/gh-aw/). Understanding the chain helps you work alongside the agents rather than against them.

### How Issues Flow Through the Chain

```
issue opened
  |
  v
issue-triage (auto-labels by type)
  |
  v
human adds "needs-spec" label
  |
  v
spec-refiner (classifies issue: plan-worthy, direct-route, or blocked)
  |
  +---> [plan-worthy] creates plan file PR + implementer label
  |       |
  |       v
  |     human approves plan PR (the one decision point)
  |       |
  |       v
  |     plan-merged-dispatcher (writes checklist onto source issue,
  |                             moves needs-plan -> ready-for-implementation)
  |       |
  +---> [direct route] adds impl:copilot + ready-for-implementation directly
  |
  v
implementer-dispatcher (assigns source issue to chosen agent)
  |
  v
PR opened
  |
  +---> reviewer (plan-aware code review)
  +---> contribution-checker (CONTRIBUTING.md compliance)
  |
  v
/pr-fix if changes needed, ci-cleaner if CI breaks on main
  |
  v
nightly: self-improvement-meta (extracts learnings)
```

### What This Means for Human Contributors

- File an issue normally. The `issue-triage` workflow will label it automatically.
- Add `needs-spec` to trigger `spec-refiner`. For plan-worthy issues, spec-refiner writes a plan PR for your review. For simple, clearly bounded issues (dependency bumps, single-file fixes), spec-refiner fast-tracks directly to implementation with no plan PR needed.
- For plan-worthy issues: review and approve (or edit) the plan PR. This is the one human decision gate.
- After plan approval (or direct-route fast-track), agents handle implementation, review, and CI fixes.
- You can still contribute code directly by opening a PR. The `reviewer` and `contribution-checker` workflows will review it.

### Labels Used by the Factory

| Label | Purpose |
|-------|---------|
| `needs-spec` | Trigger spec-refiner to write a plan |
| `needs-changes` | Flag a PR for /pr-fix |
| `human-review` | Halt all workflows on this issue/PR |
| `impl:claude-opus` | Assign implementation to Claude Opus 4.6 |
| `impl:claude-sonnet` | Assign implementation to Claude Sonnet 4.6 |
| `impl:copilot` | Assign implementation to Copilot cloud agent |

See `docs/AGENT_FACTORY.md` for the full usage guide.

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
