# Project Context

This is `measure-ai-proficiency`, a CLI tool for measuring AI coding proficiency based on context engineering artifacts.

## Overview

The tool scans repositories for files like `CLAUDE.md`, `.cursorrules`, and `.github/copilot-instructions.md` to assess how effectively teams are preparing context for AI coding assistants.

## Architecture

```
measure_ai_proficiency/
├── __init__.py      # Package exports
├── __main__.py      # CLI entry point
├── config.py        # Level definitions and file patterns
├── scanner.py       # Repository scanning logic
└── reporter.py      # Output formatting (terminal, JSON, markdown, CSV)
```

## Key Abstractions

- **LevelConfig**: Defines file patterns and weights for each maturity level
- **RepoScanner**: Scans a repository and builds a RepoScore
- **RepoScore**: Contains level scores, overall level, and recommendations
- **Reporter**: Formats output in various formats

## Conventions

- Pure Python, no external dependencies for core functionality
- Type hints throughout
- Dataclasses for data structures
- Exit codes: 0 = success, 1 = no repos found, 2 = all repos at Level 0

## Testing

```bash
pytest tests/ -v
```

## Common Tasks

- Add new file patterns: Edit `config.py`, add to appropriate `LevelConfig`
- Add new output format: Add new reporter class in `reporter.py`
- Adjust scoring thresholds: Edit `_calculate_overall_level` in `scanner.py`
