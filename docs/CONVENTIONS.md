# Conventions

Coding standards and conventions for measure-ai-proficiency.

## Code Style

### Python Version
- Python 3.10+ required
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

### Exit Codes

The CLI uses three exit codes:

| Code | Meaning |
|------|---------|
| `0` | Success: one or more repositories scanned and assessed |
| `1` | No repositories found or scan error |
| `2` | All repositories are at Level 1 (no AI context detected) |

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

## Scoring Constants

Level minimum scores control when a repository advances to the next level. These values are enforced in `measure_ai_proficiency/scanner.py` (`LEVEL_MINIMUM_SCORES`):

| Level | Minimum Score | Name |
|-------|--------------|------|
| L2 | 15 | Basic instructions |
| L3 | 30 | Comprehensive context |
| L4 | 45 | Skills and automation |
| L5 | 55 | Multi-agent ready |
| L6 | 70 | Fleet infrastructure |
| L7 | 85 | Agent fleet |
| L8 | 95 | Custom orchestration |

Do not change these constants without a corresponding update to this table.

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

## Writing Style

These rules apply to all documentation, commit messages, PR descriptions, and comments.

- **No em-dashes.** Use commas, colons, or periods instead. An em-dash (`—`) or double-dash (`--` used as an em-dash) is never acceptable in prose.
- Short sentences. Strong declarative statements.
- Lead with the answer. No throat-clearing opening sentences.
- No sweeping generalizations (for example, "most teams").
- If you cite data, link to the source.
