# Project Context

This is `measure-ai-proficiency`, a CLI tool for measuring AI coding proficiency based on context engineering artifacts.

## Overview

The tool scans repositories for files like `CLAUDE.md`, `.cursorrules`, `.github/copilot-instructions.md`, `.github/skills/*/SKILL.md`, and `AGENTS.md` to assess how effectively teams are preparing context for AI coding assistants.

**Key Features:**
- 8-level maturity scoring aligned with Steve Yegge's model
- Cross-reference detection between AI instruction files
- Content quality evaluation (sections, commands, constraints)
- Multiple output formats (terminal, JSON, markdown, CSV)

## Architecture

```
measure_ai_proficiency/
├── __init__.py      # Package exports
├── __main__.py      # CLI entry point
├── config.py        # Level definitions and file patterns
├── scanner.py       # Repository scanning logic + cross-reference detection
├── reporter.py      # Output formatting (terminal, JSON, markdown, CSV)
└── repo_config.py   # Repository configuration and tool auto-detection
```

## Key Abstractions

- **LevelConfig**: Defines file patterns and weights for each maturity level
- **RepoScanner**: Scans a repository and builds a RepoScore
- **RepoScore**: Contains level scores, overall level, cross-references, and recommendations
- **CrossReference**: A detected reference between files (source, target, type, resolved status)
- **ContentQuality**: Quality metrics for an instruction file (sections, commands, constraints, commits)
- **CrossReferenceResult**: Summary of all cross-references and quality scores
- **Reporter**: Formats output in various formats

## Conventions

- Pure Python, no external dependencies for core functionality
- Type hints throughout
- Dataclasses for data structures
- Exit codes: 0 = success, 1 = no repos found, 2 = all repos at Level 1 (no AI context)

## Supported Skill Locations

Agent Skills follow the [Agent Skills](https://agentskills.io/) open standard:
- Claude Code: `.claude/skills/*/SKILL.md`
- GitHub Copilot: `.github/skills/*/SKILL.md` or `.copilot/skills/*/SKILL.md`
- Cursor: `.cursor/skills/*/SKILL.md`
- OpenAI Codex: `.codex/skills/*/SKILL.md`
- Generic: `skills/*/SKILL.md`

## Testing

```bash
pytest tests/ -v
```

## Common Tasks

- Add new file patterns: Edit `config.py`, add to appropriate `LevelConfig`
- Add new output format: Add new reporter class in `reporter.py`
- Adjust scoring thresholds: Edit `_calculate_overall_level` in `scanner.py`
- Add new cross-reference patterns: Edit `CROSS_REF_PATTERNS` in `scanner.py`
- Add new quality indicators: Edit `QUALITY_PATTERNS` in `scanner.py`

## Cross-Reference Detection

The scanner analyzes the content of AI instruction files to detect references:

**Files Scanned** (defined in `INSTRUCTION_FILES`):
- `CLAUDE.md`, `AGENTS.md`, `.cursorrules`, `CODEX.md`
- `.github/copilot-instructions.md`, `.copilot-instructions.md`
- Scoped instruction files and skills

**Reference Patterns** (defined in `CROSS_REF_PATTERNS`):
- `markdown_link`: `[text](file.md)` links
- `file_mention`: `"FILE.md"` or `` `FILE.md` `` in quotes/backticks
- `relative_path`: `./path/file.md` relative paths
- `directory_ref`: `skills/`, `.claude/commands/` directory references

**Quality Indicators** (defined in `QUALITY_PATTERNS` + git history):
- `sections`: Markdown headers (`##`)
- `paths`: Concrete file paths (`/src/`, `~/config/`)
- `commands`: CLI commands in backticks
- `constraints`: "never", "avoid", "don't", "must not"
- `commits`: Git commit count via `git log --follow` (5+ = 2pts, 3-4 = 1pt)

**Bonus Calculation**: Up to +10 points based on cross-references and quality scores.

## Boris Cherny's Best Practices

Key patterns from the creator of Claude Code:

- **Team-maintained CLAUDE.md**: Check into git, update when Claude makes mistakes
- **Slash commands**: Store in `.claude/commands/`, use for frequent workflows
- **MCP config sharing**: Use `.mcp.json` at root level, commit to git
- **Permission presets**: Configure `.claude/settings.json` with team-safe defaults
- **Verification loops**: Always give Claude a way to verify its work (tests, linters, etc.)
- **PostToolUse hooks**: Format code automatically after edits
