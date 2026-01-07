# Conventions

Coding standards and conventions for measure-ai-proficiency.

## Code Style

### Python Version
- Python 3.8+ required
- Use type hints throughout

### Formatting
- No external formatters required (keep it simple)
- 4-space indentation
- Max line length: 100 characters (soft limit)
- Use double quotes for strings

### Imports
```python
# Standard library first
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Third-party (minimal - only yaml is optional)
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

# Local imports
from .config import LEVELS, LevelConfig
from .scanner import RepoScanner
```

## Naming Conventions

### Files
- Lowercase with underscores: `repo_config.py`
- Test files: `test_<module>.py`

### Classes
- PascalCase: `RepoScanner`, `LevelConfig`
- Dataclasses for data structures

### Functions/Methods
- snake_case: `scan_level()`, `get_reporter()`
- Private methods prefixed with underscore: `_calculate_score()`

### Variables
- snake_case: `level_scores`, `matched_files`
- Constants: UPPERCASE: `LEVELS`, `QUALITY_PATTERNS`

## Data Structures

### Use Dataclasses
```python
from dataclasses import dataclass, field

@dataclass
class LevelScore:
    level: int
    name: str
    matched_files: List[FileMatch] = field(default_factory=list)
```

### Type Hints
```python
def scan_level(self, level: int) -> LevelScore:
    ...

def get_reporter(format: str) -> Union[TerminalReporter, JsonReporter]:
    ...
```

## Error Handling

### User-Facing Errors
- Print to stderr with clear message
- Exit with appropriate code

```python
if not path.exists():
    print(f"Error: Path does not exist: {path}", file=sys.stderr)
    sys.exit(1)
```

### Internal Errors
- Log warnings for non-fatal issues
- Continue processing when possible

```python
try:
    with open(config_file) as f:
        data = yaml.safe_load(f)
except yaml.YAMLError as e:
    print(f"Warning: Failed to parse {config_file}: {e}", file=sys.stderr)
    # Continue with defaults
```

## Dependencies

### Core Principle
- Zero external dependencies for core functionality
- Only `pyyaml` as optional dependency for config files

### Why?
- Easy installation: `pip install measure-ai-proficiency`
- No version conflicts
- Works in restricted environments

## File Organization

```
measure_ai_proficiency/
├── __init__.py      # Public exports only
├── __main__.py      # CLI entry point (thin)
├── config.py        # Static configuration (LEVELS, patterns)
├── scanner.py       # Core logic (scanning, scoring)
├── reporter.py      # Output formatting (all formats)
└── repo_config.py   # Runtime config (yaml loading)
```

## Testing

### Test Location
- All tests in `tests/` directory
- Mirror source structure: `test_scanner.py` tests `scanner.py`

### Test Style
```python
class TestRepoScanner:
    """Tests for RepoScanner class."""

    def test_empty_repo_returns_level_1(self):
        """Empty repository should return Level 1."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = RepoScanner(tmpdir)
            score = scanner.scan()
            assert score.overall_level == 1
```

### Run Tests
```bash
pytest tests/ -v
```

## Git Conventions

### Commits
- Present tense: "Add feature" not "Added feature"
- First line: summary (50 chars max)
- Include emoji for type: fix, feat, docs, refactor

### Branches
- `main` is primary branch
- Feature branches: `feature/description`
- Bug fixes: `fix/description`

## Documentation

### Docstrings
```python
def scan(self) -> RepoScore:
    """
    Scan the repository and calculate proficiency score.

    Returns:
        RepoScore with level breakdown and recommendations.
    """
```

### Comments
- Explain "why", not "what"
- Use sparingly - prefer clear code

```python
# Skip hidden directories to avoid scanning .git, .venv, etc.
if item.name.startswith("."):
    continue
```
