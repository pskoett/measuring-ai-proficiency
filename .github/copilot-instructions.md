# Copilot Instructions for measure-ai-proficiency

This is a CLI tool for measuring AI coding proficiency based on context engineering artifacts.

## Project Overview

The tool scans repositories for AI context files (like `CLAUDE.md`, `.cursorrules`, `.github/copilot-instructions.md`, and skill files) and calculates a maturity score based on an 8-level model (1-8) aligned with Steve Yegge's stages.

## Architecture

```
measure_ai_proficiency/
├── __init__.py      # Package exports
├── __main__.py      # CLI entry point
├── config.py        # Level definitions and file patterns
├── scanner.py       # Repository scanning logic
└── reporter.py      # Output formatting (terminal, JSON, markdown, CSV)
```

## Key Patterns

### Adding New File Patterns

To add detection for new AI context files, edit `config.py`:

```python
# Add to appropriate level (1-8) in the LevelConfig
file_patterns=[
    "your-new-pattern.md",
    ".your-tool/config/*.md",
]
```

### Skill Locations (Agent Skills Standard)

All major AI tools now support the [Agent Skills](https://agentskills.io/) open standard:
- Claude Code: `.claude/skills/*/SKILL.md`
- GitHub Copilot: `.github/skills/*/SKILL.md`
- OpenAI Codex: `.codex/skills/*/SKILL.md`

### Output Formats

The tool supports: terminal (default), JSON, markdown, CSV. Add new formats in `reporter.py`.

## Coding Conventions

- Pure Python with no external dependencies for core functionality
- Type hints on all functions and methods
- Dataclasses for data structures
- Exit codes: 0 = success, 1 = no repos found, 2 = all repos at Level 1

## Testing

```bash
pytest tests/ -v
```

## Common Tasks

| Task | Location |
|------|----------|
| Add file patterns | `config.py` → appropriate `LevelConfig` |
| Add output format | `reporter.py` → new reporter class |
| Adjust thresholds | `scanner.py` → `_calculate_overall_level()` |
| Add recommendations | `scanner.py` → `_generate_recommendations()` |

## Documentation Files

- `README.md` - User-facing documentation
- `CLAUDE.md` - Claude Code context
- `CUSTOMIZATION.md` - How to customize patterns
- `AGENT_REFERENCES.md` - Best practices for agent references
- `measuring-ai-proficiency-context-engineering.md` - Full article on context engineering
