# Architecture

System design for measure-ai-proficiency CLI tool.

## Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI Layer                             │
│  __main__.py - Argument parsing, output routing              │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                     Scanner Layer                            │
│  scanner.py - Repository scanning, scoring, recommendations  │
│  repo_config.py - Configuration loading, tool detection      │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                    Config Layer                              │
│  config.py - Level definitions, file patterns, weights       │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                   Reporter Layer                             │
│  reporter.py - Terminal, JSON, Markdown, CSV output          │
└─────────────────────────────────────────────────────────────┘
```

## Components

### CLI Entry Point (`__main__.py`)

- Parses command-line arguments using argparse
- Supports single repo, multiple repos, and org-wide scanning
- Routes output to appropriate reporter based on `--format`
- Handles file output with `--output`
- Exit codes: 0=success, 1=error, 2=no AI context

### Scanner (`scanner.py`)

**RepoScanner class:**
- Scans repository for context engineering artifacts
- Calculates level scores based on file pattern matching
- Detects cross-references between AI instruction files
- Evaluates content quality (sections, paths, commands, constraints)
- Generates recommendations based on current level

**Key methods:**
- `scan()` - Main entry point, returns RepoScore
- `_scan_level()` - Scans for patterns at a specific level
- `_calculate_overall_level()` - Determines maturity level from scores
- `_analyze_cross_references()` - Finds links between files
- `_evaluate_content_quality()` - Scores file content
- `_generate_recommendations()` - Level-specific suggestions

### Configuration (`config.py`)

**LEVELS dict:**
- Maps level numbers (1-8) to LevelConfig objects
- Each level has: name, description, file_patterns, directory_patterns, weight

**Pattern types:**
- File patterns: glob-style matching (`*.md`, `docs/**/*.md`)
- Directory patterns: folder existence checks (`.claude/skills`)

### Repository Config (`repo_config.py`)

**RepoConfig dataclass:**
- Stores per-repo configuration
- Loaded from `.ai-proficiency.yaml` if present
- Configurable: tools, thresholds, skip_recommendations, focus_areas

**Auto-detection:**
- Detects AI tools from existing files (CLAUDE.md → Claude Code)
- Supports: claude-code, github-copilot, cursor, openai-codex

### Reporters (`reporter.py`)

| Reporter | Output | Use Case |
|----------|--------|----------|
| TerminalReporter | Colored ASCII | Human viewing |
| JsonReporter | JSON | CI/CD integration |
| MarkdownReporter | Markdown tables | Documentation |
| CsvReporter | CSV | Spreadsheet analysis |

## Data Flow

```
1. CLI receives path(s) to scan
         │
         ▼
2. RepoScanner loads RepoConfig (auto-detect + yaml)
         │
         ▼
3. Scanner iterates levels 1-8, matching patterns
         │
         ▼
4. Cross-reference analysis on AI instruction files
         │
         ▼
5. Quality scoring on matched files
         │
         ▼
6. Overall level calculated from coverage + bonus
         │
         ▼
7. Recommendations generated based on level
         │
         ▼
8. Reporter formats RepoScore for output
```

## Key Data Structures

### RepoScore
```python
@dataclass
class RepoScore:
    repo_name: str
    repo_path: str
    level_scores: Dict[int, LevelScore]
    overall_level: int
    overall_score: float
    recommendations: List[str]
    detected_tools: List[str]
    config: RepoConfig
    cross_references: CrossReferenceResult
```

### LevelScore
```python
@dataclass
class LevelScore:
    level: int
    name: str
    description: str
    matched_files: List[FileMatch]
    matched_directories: List[str]
    total_patterns: int
    coverage_percent: float
```

### CrossReferenceResult
```python
@dataclass
class CrossReferenceResult:
    references: List[CrossReference]
    source_files_scanned: int
    resolved_count: int
    quality_scores: Dict[str, ContentQuality]
    bonus_points: float
```

## Scoring Algorithm

1. **Level coverage**: Files matched / Total patterns in level
2. **Threshold check**: Coverage must exceed level threshold (configurable)
3. **Quality bonus**: Up to +5 points from content quality
4. **Cross-ref bonus**: Up to +5 points from cross-references
5. **Overall score**: Weighted sum of level scores + bonuses

## Extension Points

- **Add patterns**: Edit `LEVELS` in `config.py`
- **New reporter**: Implement `report_single()` and `report_multiple()`
- **Custom scoring**: Override thresholds in `.ai-proficiency.yaml`
- **New quality indicators**: Add to `QUALITY_PATTERNS` in `scanner.py`
