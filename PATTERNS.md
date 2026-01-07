# Design Patterns

Common patterns used in measure-ai-proficiency.

## Dataclass Pattern

Used for all data structures to get automatic `__init__`, `__repr__`, and type hints.

```python
from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class LevelScore:
    level: int
    name: str
    description: str
    matched_files: List[FileMatch] = field(default_factory=list)
    coverage_percent: float = 0.0

# Usage
score = LevelScore(level=2, name="Basic", description="...")
print(score.level)  # 2
```

**When to use:** Any structured data that will be passed between functions.

## Factory Pattern

Used for creating reporters based on format string.

```python
def get_reporter(format: str, verbose: bool = False) -> Reporter:
    reporters = {
        "terminal": TerminalReporter(verbose=verbose),
        "json": JsonReporter(),
        "markdown": MarkdownReporter(),
        "csv": CsvReporter(),
    }
    return reporters.get(format, TerminalReporter(verbose=verbose))

# Usage
reporter = get_reporter("json")
reporter.report_single(score)
```

**When to use:** Creating objects based on runtime configuration.

## Dispatch Pattern

Used for level-specific recommendation generation.

```python
def _generate_recommendations(self, score: RepoScore) -> List[str]:
    handlers = {
        1: lambda: self._recommendations_level_1(score, tools),
        2: lambda: self._recommendations_level_2(score, tools, config),
        3: lambda: self._recommendations_level_3(score, tools, config),
        # ...
    }

    handler = handlers.get(score.overall_level)
    if handler:
        return handler()
    return []
```

**When to use:** Different logic paths based on a discrete value.

## Optional Dependency Pattern

Used for YAML support without requiring installation.

```python
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

def load_config(path: Path) -> Config:
    config_file = path / ".ai-proficiency.yaml"
    if config_file.exists() and YAML_AVAILABLE:
        with open(config_file) as f:
            data = yaml.safe_load(f)
        # Use data...
    else:
        # Use defaults
```

**When to use:** Optional features that shouldn't block core functionality.

## Property Getter with Fallback

Used for config values that may not be set.

```python
@property
def _max_file_size(self) -> int:
    return self.config.max_file_size if self.config else 100_000

@property
def _word_threshold_full(self) -> int:
    return self.config.word_threshold_full if self.config else 200
```

**When to use:** Config values with sensible defaults.

## Glob Pattern Matching

Used for flexible file detection.

```python
from pathlib import Path

def _match_patterns(self, patterns: List[str]) -> List[Path]:
    matched = []
    for pattern in patterns:
        matched.extend(self.repo_path.glob(pattern))
    return matched

# Patterns
patterns = [
    "CLAUDE.md",           # Exact file
    "docs/*.md",           # Files in docs/
    "**/*.md",             # Recursive
    ".claude/skills/*",    # Directories
]
```

**When to use:** File system pattern matching.

## Context Manager for Resources

Used for file output handling.

```python
output = sys.stdout
if args.output:
    try:
        output = open(args.output, "w")
    except (OSError, IOError) as e:
        print(f"Error: Cannot write to file: {e}", file=sys.stderr)
        sys.exit(1)

try:
    reporter.report_single(score, output)
finally:
    if args.output:
        output.close()
```

**When to use:** Resources that need cleanup.

## Temporary Directory for Tests

Used for isolated test environments.

```python
import tempfile
from pathlib import Path

def test_scanner(self):
    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup
        Path(tmpdir, "CLAUDE.md").write_text("# Test\n" + "x" * 200)

        # Test
        scanner = RepoScanner(tmpdir)
        score = scanner.scan()

        # Assert
        assert score.overall_level >= 2
    # tmpdir automatically cleaned up
```

**When to use:** Tests that need filesystem access.

## Regex Pattern Groups

Used for cross-reference detection.

```python
CROSS_REF_PATTERNS = {
    "markdown_link": re.compile(r'\[([^\]]+)\]\(([^)]+\.md)\)', re.IGNORECASE),
    "file_mention": re.compile(r'["`]([A-Z][A-Z0-9_-]*\.md)["`]', re.IGNORECASE),
    "relative_path": re.compile(r'\.\/([a-zA-Z0-9_/-]+\.md)', re.IGNORECASE),
}

def find_references(content: str) -> List[str]:
    refs = []
    for pattern_name, pattern in CROSS_REF_PATTERNS.items():
        for match in pattern.finditer(content):
            refs.append(match.group(2) if pattern_name == "markdown_link" else match.group(1))
    return refs
```

**When to use:** Extracting structured data from text.

## Subprocess with Timeout

Used for git operations.

```python
import subprocess

def get_commit_count(file_path: Path, timeout: int = 5) -> int:
    try:
        result = subprocess.run(
            ["git", "log", "--follow", "--oneline", "--", str(file_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=file_path.parent,
        )
        if result.returncode == 0:
            return len(result.stdout.strip().split("\n"))
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return 0
```

**When to use:** External commands that might hang.

## Skip Directories Pattern

Used to exclude dependency folders from scanning.

```python
SKIP_DIRS = {
    "node_modules", "venv", ".venv", "env", ".env",
    "dist", "build", "__pycache__", ".git", ".svn",
    "vendor", "packages", ".tox", "eggs",
}

def should_skip(path: Path) -> bool:
    return path.name in SKIP_DIRS or path.name.startswith(".")

for item in directory.iterdir():
    if item.is_dir() and not should_skip(item):
        scan_directory(item)
```

**When to use:** Recursive directory traversal.
