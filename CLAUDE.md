# Project Context

This is `measure-ai-proficiency`, a CLI tool for measuring AI coding proficiency based on context engineering artifacts.

## Overview

The tool scans repositories for files like `CLAUDE.md`, `.cursorrules`, `.github/copilot-instructions.md`, `.github/skills/*/SKILL.md`, and `AGENTS.md` to assess how effectively teams are preparing context for AI coding assistants.

**Key Features:**
- 8-level maturity scoring aligned with Steve Yegge's model
- Cross-reference detection between AI instruction files
- Content quality evaluation (sections, commands, constraints)
- Multiple output formats (terminal, JSON, markdown, CSV)
- **Dual scanning modes**: Local scanning (default) OR GitHub CLI (optional, no cloning!)
  - Local: Scan repositories on disk
  - GitHub CLI: Scan remote repos without cloning (--github-repo, --github-org)
- **MCP Server**: Real-time AI context awareness via Model Context Protocol
  - Makes AI assistant aware of its own proficiency level
  - Provides tools for scanning, validation, and recommendations
  - Creates meta-improvement loop for better AI context

## MCP Server

The project now includes an **MCP (Model Context Protocol) server** that makes AI proficiency measurement accessible to AI assistants in real-time.

**Entry point:** `measure_ai_proficiency/mcp_server.py`
**Script:** `measure-ai-proficiency-mcp` (installed via pyproject.toml)

**Available MCP Tools:**
- `scan_current_repo` - Analyze AI proficiency of current repository
- `get_recommendations` - Get specific improvement suggestions
- `check_cross_references` - Validate references between AI context files
- `get_level_requirements` - Show requirements for next maturity level
- `scan_github_repo` - Analyze remote GitHub repo without cloning
- `scan_github_org` - Analyze entire GitHub organization
- `validate_file_quality` - Check quality score of specific file

**Configuration:** Add to `.mcp.json`:
```json
{
  "mcpServers": {
    "measure-ai-proficiency": {
      "command": "measure-ai-proficiency-mcp"
    }
  }
}
```

**Why it matters:** Creates a meta-improvement loop where AI assistants can:
1. Check their own proficiency level while working
2. Validate cross-references as they write them
3. Get real-time recommendations for improvements
4. Scan entire organizations without leaving the conversation

See `MCP.md` for full documentation, examples, and troubleshooting.

## Architecture

```
measure_ai_proficiency/
├── __init__.py        # Package exports
├── __main__.py        # CLI entry point
├── mcp_server.py      # MCP server for AI assistant integration
├── config.py          # Level definitions and file patterns
├── scanner.py         # Repository scanning logic + cross-reference detection
├── github_scanner.py  # GitHub CLI integration for remote scanning
├── reporter.py        # Output formatting (terminal, JSON, markdown, CSV)
└── repo_config.py     # Repository configuration and tool auto-detection

scripts/
├── find-org-repos.sh  # GitHub org discovery script (uses gh CLI)
└── README.md          # Script documentation
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

- Add new file patterns: Edit `measure_ai_proficiency/config.py`, add to appropriate `LevelConfig`
- Add new output format: Add new reporter class in `measure_ai_proficiency/reporter.py`
- Adjust scoring thresholds: Edit `_calculate_overall_level` in `measure_ai_proficiency/scanner.py`
- Add new cross-reference patterns: Edit `CROSS_REF_PATTERNS` in `measure_ai_proficiency/scanner.py`
- Add new quality indicators: Edit `QUALITY_PATTERNS` in `measure_ai_proficiency/scanner.py`
- Add new MCP tools: Add handler in `measure_ai_proficiency/mcp_server.py`, update `list_tools()` and `call_tool()`

## Scanning Options

The tool supports **two scanning modes** - use whichever fits your workflow:

### Local Scanning (Default)
Scan repositories on disk. Works offline, no authentication needed.

```bash
# Scan current directory
measure-ai-proficiency

# Scan specific repository
measure-ai-proficiency /path/to/repo

# Scan multiple repositories
measure-ai-proficiency repo1 repo2 repo3

# Scan all repos in a directory (cloned org)
measure-ai-proficiency --org /path/to/org-repos
```

### GitHub CLI Scanning (Optional)
Scan GitHub repositories without cloning. Requires `gh` CLI and authentication.

```bash
# Scan single GitHub repo
measure-ai-proficiency --github-repo owner/repo

# Scan entire GitHub org
measure-ai-proficiency --github-org org-name

# Limit number of repos
measure-ai-proficiency --github-org org-name --limit 50

# Combine with output formats
measure-ai-proficiency --github-org org --format json --output report.json
```

**Why use GitHub CLI mode?**
- No need to clone repositories (saves disk space)
- Faster for large organizations (only downloads relevant files)
- Works with private repos (if authenticated)
- Discover repos in GitHub org: Run `scripts/find-org-repos.sh <org-name>` to find active repos with AI artifacts

**Both modes support:**
- All output formats (terminal, JSON, markdown, CSV)
- All CLI flags (--format, --output, -q, --min-level)
- Cross-reference detection and quality scoring

### Improving Repository AI Context
Use the **AI Context Improvement Agent** in `.claude/agents/improve-ai-context.agent.md` to systematically create/improve context files. Works with both scanning modes.

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
