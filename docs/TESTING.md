# Testing Guide

How to run and write tests for measure-ai-proficiency.

## Running Tests

### Quick Run
```bash
pytest tests/ -v
```

### With Coverage
```bash
pytest tests/ -v --cov=measure_ai_proficiency --cov-report=term-missing
```

### Single Test File
```bash
pytest tests/test_scanner.py -v
```

### Single Test
```bash
pytest tests/test_scanner.py::TestRepoScanner::test_empty_repo_returns_level_1 -v
```

## Test Structure

```
tests/
├── test_scanner.py    # Core scanning logic
├── test_reporter.py   # Output formatting
└── test_main.py       # CLI integration
```

## Test Categories

### Scanner Tests (`test_scanner.py`)

| Test Class | Coverage |
|------------|----------|
| TestRepoScanner | Basic scanning, level detection |
| TestLevelConfig | Level configuration validation |
| TestRepoScore | Score dataclass properties |
| TestHigherLevels | Level 4+ detection |
| TestAutoDetection | AI tool detection |
| TestRepoConfig | YAML config loading |
| TestCrossReferences | Link detection, quality scoring |

### Reporter Tests (`test_reporter.py`)

| Test Class | Coverage |
|------------|----------|
| TestFormatToolName | Tool name capitalization |
| TestGetReporter | Reporter factory |
| TestTerminalReporter | Terminal output |
| TestJsonReporter | JSON output |
| TestMarkdownReporter | Markdown output |
| TestCsvReporter | CSV output |

### CLI Tests (`test_main.py`)

| Test Class | Coverage |
|------------|----------|
| TestCLIBasic | --help, --version |
| TestCLIExitCodes | Exit code behavior |
| TestCLIOutputFormats | --format options |
| TestCLIMinLevel | --min-level filtering |
| TestCLIOutputFile | --output file handling |
| TestCLIOrgMode | --org directory scanning |

## Writing Tests

### Use Temporary Directories
```python
import tempfile
from pathlib import Path

def test_something(self):
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        Path(tmpdir, "CLAUDE.md").write_text("# Test\n" + "x" * 200)

        # Run scanner
        scanner = RepoScanner(tmpdir)
        score = scanner.scan()

        # Assert
        assert score.overall_level >= 2
```

### Test File Content
```python
# Substantive file (>100 bytes)
Path(tmpdir, "CLAUDE.md").write_text("# Project\n" + "x" * 200)

# Stub file (won't count as substantive)
Path(tmpdir, "CLAUDE.md").write_text("# TODO")
```

### Test YAML Config
```python
def test_config_loaded_from_yaml(self):
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / ".ai-proficiency.yaml"
        config_file.write_text("""
tools:
  - cursor
thresholds:
  level_3: 5
""")
        scanner = RepoScanner(tmpdir)
        score = scanner.scan()

        assert score.config.from_file
        assert "cursor" in score.config.tools
```

### Test CLI with Subprocess
```python
import subprocess
import sys

def test_help_flag(self):
    result = subprocess.run(
        [sys.executable, "-m", "measure_ai_proficiency", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "usage:" in result.stdout.lower()
```

## Test Patterns

### Testing Level Detection
```python
def test_comprehensive_repo_detects_level_3_files(self):
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create Level 2 base
        Path(tmpdir, "CLAUDE.md").write_text("# Project\n" + "x" * 200)

        # Create Level 3 files
        Path(tmpdir, "ARCHITECTURE.md").write_text("# Arch\n" + "x" * 500)
        Path(tmpdir, "CONVENTIONS.md").write_text("# Conv\n" + "x" * 500)

        scanner = RepoScanner(tmpdir)
        score = scanner.scan()

        # Check files detected (not overall level - that depends on thresholds)
        level_3 = score.level_scores.get(3)
        assert level_3 is not None
        assert level_3.coverage_percent > 0
        assert len(level_3.matched_files) >= 2
```

### Testing Cross-References
```python
def test_detects_markdown_links(self):
    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "CLAUDE.md").write_text("""
# Project
See [architecture](ARCHITECTURE.md) for details.
""" + "x" * 200)
        Path(tmpdir, "ARCHITECTURE.md").write_text("# Arch\n" + "x" * 200)

        scanner = RepoScanner(tmpdir)
        score = scanner.scan()

        refs = score.cross_references.references
        assert any(r.target == "ARCHITECTURE.md" for r in refs)
```

### Testing Reporters
```python
import io

def test_outputs_valid_json(self):
    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "README.md").write_text("# Test\n" + "x" * 200)

        scanner = RepoScanner(tmpdir)
        score = scanner.scan()

        reporter = JsonReporter()
        output = io.StringIO()
        reporter.report_single(score, output)

        data = json.loads(output.getvalue())
        assert "overall_level" in data
```

## Common Issues

### Test Fails Due to Threshold
Level thresholds may cause tests to fail if expecting specific overall levels.

**Fix:** Test file detection (coverage > 0) instead of overall level.

### Test Fails Due to Git History
Quality scoring checks git commit count.

**Fix:** Temp directories have no git history, so commit_count will be 0.

### Test Fails Due to File Size
Files under 100 bytes aren't counted as substantive.

**Fix:** Add padding: `"# Test\n" + "x" * 200`
