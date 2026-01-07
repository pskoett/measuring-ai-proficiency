# API Reference

## CLI Usage

```bash
measure-ai-proficiency [OPTIONS] [PATHS...]
```

### Arguments

| Argument | Description |
|----------|-------------|
| `PATHS` | Repository paths to scan (default: current directory) |

### Options

| Option | Description |
|--------|-------------|
| `-f, --format FORMAT` | Output format: `terminal`, `json`, `markdown`, `csv` |
| `-o, --output FILE` | Write output to file instead of stdout |
| `-q, --quiet` | Hide detailed file matches (summary only) |
| `--min-level N` | Only show repos at or above level N (1-8) |
| `--org PATH` | Scan all subdirectories as separate repos |
| `--version` | Show version and exit |
| `-h, --help` | Show help message |

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success - at least one repo has AI context |
| 1 | Error - invalid path or no repos found |
| 2 | All repos at Level 1 (no AI context files) |

### Examples

```bash
# Scan current directory
measure-ai-proficiency

# Scan with quiet output (summary only)
measure-ai-proficiency -q

# Scan specific repo
measure-ai-proficiency /path/to/repo

# Multiple repos
measure-ai-proficiency repo1 repo2 repo3

# JSON output for CI
measure-ai-proficiency --format json > report.json

# Scan GitHub org clone
measure-ai-proficiency --org ~/github/my-org

# Filter by minimum level
measure-ai-proficiency --min-level 3 --org ~/projects

# CSV export for analysis
measure-ai-proficiency --org ~/work --format csv -o proficiency.csv
```

## Python API

### RepoScanner

```python
from measure_ai_proficiency import RepoScanner

# Default: verbose=True (shows detailed file matches)
scanner = RepoScanner("/path/to/repo")
score = scanner.scan()

print(f"Level: {score.overall_level}")
print(f"Score: {score.overall_score}")
print(f"Tools: {score.detected_tools}")

# For quiet mode (summary only):
scanner = RepoScanner("/path/to/repo", verbose=False)
```

### RepoScore Properties

```python
score.repo_name          # str: Repository name
score.repo_path          # str: Full path
score.overall_level      # int: 1-8
score.overall_score      # float: 0-100+
score.recommendations    # List[str]: Improvement suggestions
score.detected_tools     # List[str]: AI tools in use
score.has_any_ai_files   # bool: Has any AI context files
score.level_scores       # Dict[int, LevelScore]: Per-level details
score.cross_references   # CrossReferenceResult: Link analysis
score.config             # RepoConfig: Loaded configuration
```

### LevelScore Properties

```python
level_score = score.level_scores[3]

level_score.level            # int: Level number
level_score.name             # str: "Level 3: Comprehensive Context"
level_score.matched_files    # List[FileMatch]: Files found
level_score.coverage_percent # float: Pattern coverage
level_score.total_patterns   # int: Patterns checked
```

### Multiple Repos

```python
from measure_ai_proficiency import scan_multiple_repos, scan_github_org

# Scan multiple paths
scores = scan_multiple_repos(["/repo1", "/repo2"])

# Scan org directory
scores = scan_github_org("/path/to/org")

for score in scores:
    print(f"{score.repo_name}: Level {score.overall_level}")
```

### Reporters

```python
from measure_ai_proficiency import get_reporter

# Terminal output (verbose=True is now the default)
reporter = get_reporter("terminal")
reporter.report_single(score)

# Quiet mode (summary only)
reporter = get_reporter("terminal", verbose=False)
reporter.report_single(score)

# JSON output
reporter = get_reporter("json")
reporter.report_single(score, output=open("report.json", "w"))

# Multiple repos
reporter = get_reporter("csv")
reporter.report_multiple(scores, output=open("report.csv", "w"))
```

## JSON Output Schema

### Single Repo

```json
{
  "repo_name": "my-project",
  "repo_path": "/path/to/my-project",
  "overall_level": 3,
  "overall_score": 45.5,
  "detected_tools": ["claude-code", "github-copilot"],
  "level_scores": {
    "1": {"coverage_percent": 100.0, "matched_count": 1},
    "2": {"coverage_percent": 40.0, "matched_count": 2},
    "3": {"coverage_percent": 15.5, "matched_count": 12}
  },
  "cross_references": {
    "total_count": 25,
    "resolved_count": 20,
    "bonus_points": 4.5
  },
  "quality_scores": {
    "CLAUDE.md": {"score": 8.5, "word_count": 450}
  },
  "recommendations": [
    "Create ARCHITECTURE.md",
    "Add CONVENTIONS.md"
  ]
}
```

### Multiple Repos (--org)

```json
{
  "scan_time": "2024-01-15T10:30:00",
  "total_repos": 5,
  "distribution": {
    "level_1": 1,
    "level_2": 2,
    "level_3": 2,
    "level_4": 0
  },
  "average_score": 35.2,
  "repos": [
    { "repo_name": "...", "overall_level": 2 }
  ]
}
```

## Configuration File

`.ai-proficiency.yaml` in repository root:

```yaml
# AI tools (auto-detected if not specified)
tools:
  - claude-code
  - github-copilot

# Custom file locations
documentation:
  architecture: "docs/SYSTEM_DESIGN.md"
  conventions: "CODING_STANDARDS.md"

# Level thresholds (coverage % needed)
thresholds:
  level_3: 15
  level_4: 12
  level_5: 10

# Skip recommendations
skip_recommendations:
  - gastown
  - beads

# Focus areas (only show these)
focus_areas:
  - documentation
  - skills

# Quality scoring
quality:
  max_file_size: 100000
  word_threshold_full: 200
  git_timeout: 5
```
