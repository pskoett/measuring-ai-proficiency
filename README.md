# Measure AI Proficiency

A CLI tool for measuring AI coding proficiency based on context engineering artifacts.

## The Problem

91% of developers use AI tools. But adoption ≠ proficiency. Some developers save 4+ hours a week with AI. Others get slower with the same tools.

**How do you measure actual AI proficiency?**

## The Solution

Measure context engineering. Look at whether teams are creating files like `CLAUDE.md`, `.cursorrules`, `.github/copilot-instructions.md`, and `AGENTS.md`. These artifacts indicate that someone has moved beyond treating AI as fancy autocomplete and started deliberately shaping how AI understands their work.

This tool scans repositories for context engineering artifacts and calculates a maturity score based on a 5-level model.

## Maturity Levels

| Level | Name | Description |
|-------|------|-------------|
| 0 | No Context Engineering | Autocomplete and chat only. No AI-specific files. |
| 1 | Basic Instructions | Basic context files exist (CLAUDE.md, .cursorrules, etc.) |
| 2 | Comprehensive Context | Detailed architecture, conventions, patterns documented |
| 3 | Skills, Memory & Workflows | Hooks, commands, memory files, custom workflows |
| 4 | Multi-Agent Orchestration | Specialized agents, orchestration, shared context |

## Supported Tools

Focused on the big four AI coding tools:

- **Claude Code**: `CLAUDE.md`, `AGENTS.md`, `.claude/hooks/`, `.claude/commands/`
- **GitHub Copilot**: `.github/copilot-instructions.md`, `.github/instructions/`, `.github/agents/`
- **Cursor**: `.cursorrules`, `.cursor/rules/`
- **OpenAI Codex CLI**: `AGENTS.md`

## Installation

```bash
# From PyPI (when published)
pip install measure-ai-proficiency

# From source
git clone https://github.com/pskoett/measuring-ai-proficiency
cd measuring-ai-proficiency
pip install -e .
```

## Usage

### Scan Current Directory

```bash
measure-ai-proficiency
```

### Scan Specific Repository

```bash
measure-ai-proficiency /path/to/repo
```

### Scan Multiple Repositories

```bash
measure-ai-proficiency /path/to/repo1 /path/to/repo2 /path/to/repo3
```

### Scan All Repos in a Directory (GitHub Org)

```bash
measure-ai-proficiency --org /path/to/cloned-org
```

### Output Formats

```bash
# Terminal output (default, with colors)
measure-ai-proficiency

# JSON output
measure-ai-proficiency --format json

# Markdown report
measure-ai-proficiency --format markdown

# CSV (for spreadsheets)
measure-ai-proficiency --format csv
```

### Save to File

```bash
measure-ai-proficiency --format markdown --output report.md
measure-ai-proficiency --format json --output results.json
```

### Verbose Mode

```bash
# Show matched files
measure-ai-proficiency -v
```

### Filter by Level

```bash
# Only show repos at Level 2 or above
measure-ai-proficiency --org /path/to/org --min-level 2
```

## Example Output

### Terminal

```
============================================================
 AI Proficiency Report: my-project
============================================================

  Overall Level: Level 2: Comprehensive Context
  Overall Score: 45.3/100

  Level Breakdown:

    ✓ Level 1: Basic Instructions
      [████████████░░░░░░░░] 60.0% (3 files)

    ✓ Level 2: Comprehensive Context
      [██████░░░░░░░░░░░░░░] 28.5% (12 files)

    ○ Level 3: Skills, Memory & Workflows
      [██░░░░░░░░░░░░░░░░░░] 8.2% (4 files)

    ○ Level 4: Multi-Agent Orchestration
      [░░░░░░░░░░░░░░░░░░░░] 0.0% (0 files)

  Recommendations:

    → Add .claude/hooks/ with PostToolUse hooks for auto-formatting.
    → Add MEMORY.md or LEARNINGS.md for persistent context.
    → Add custom slash commands in .claude/commands/.

============================================================
```

### JSON

```json
{
  "repo_name": "my-project",
  "overall_level": 2,
  "overall_score": 45.3,
  "level_scores": {
    "1": {
      "name": "Level 1: Basic Instructions",
      "coverage_percent": 60.0,
      "file_count": 3,
      "matched_files": [
        {"path": "CLAUDE.md", "size_bytes": 2048},
        {"path": ".cursorrules", "size_bytes": 512},
        {"path": "README.md", "size_bytes": 4096}
      ]
    }
  },
  "recommendations": [
    "Add .claude/hooks/ with PostToolUse hooks for auto-formatting."
  ]
}
```

## Files Detected

### Level 1: Basic Instructions

| Tool | Files |
|------|-------|
| Claude Code | `CLAUDE.md`, `AGENTS.md` |
| GitHub Copilot | `.github/copilot-instructions.md` |
| Cursor | `.cursorrules` |
| General | `README.md` |

### Level 2: Comprehensive Context

| Category | Files |
|----------|-------|
| Agent Instructions | `.github/instructions/*.instructions.md`, `.cursor/rules/` |
| Architecture | `ARCHITECTURE.md`, `docs/architecture/`, `docs/adr/` |
| Specifications | `spec.md`, `DESIGN.md`, `API.md`, `DATA_MODEL.md` |
| Conventions | `CONVENTIONS.md`, `STYLE.md`, `PATTERNS.md`, `ANTI_PATTERNS.md` |
| Development | `TESTING.md`, `DEBUGGING.md`, `DEPLOYMENT.md` |

### Level 3: Skills, Memory & Workflows

| Category | Files |
|----------|-------|
| Skills | `SKILL.md`, `skills/`, `CAPABILITIES.md` |
| Workflows | `WORKFLOWS.md`, `.claude/commands/`, `COMMANDS.md` |
| Memory | `MEMORY.md`, `LEARNINGS.md`, `DECISIONS.md`, `.memory/` |
| Hooks | `.claude/hooks/`, `.claude/settings.json` |
| MCP | `mcp.json`, `.mcp/`, `mcp-config.json` |

### Level 4: Multi-Agent Orchestration

| Category | Files |
|----------|-------|
| Agents | `.github/agents/*.agent.md`, `agents/HANDOFFS.md` |
| Orchestration | `orchestration.yaml`, `workflows/*.yaml` |
| Shared Context | `SHARED_CONTEXT.md`, `packages/*/CLAUDE.md` |
| Memory Systems | `.beads/`, `memory/global/`, `.agent_state/` |

## Scoring Algorithm

1. **File Detection**: Scan for patterns at each level
2. **Substantiveness Check**: Files must have >100 bytes to count
3. **Coverage Calculation**: Percentage of patterns matched per level
4. **Level Achievement**:
   - Level 1: At least one core AI file with content
   - Level 2: Level 1 + >20% coverage of Level 2 patterns
   - Level 3: Level 2 + >15% coverage of Level 3 patterns
   - Level 4: Level 3 + >10% coverage of Level 4 patterns
5. **Overall Score**: Weighted combination of coverage and substantiveness

## Use Cases

### Engineering Leadership

```bash
# Assess AI proficiency across your organization
measure-ai-proficiency --org /path/to/all-repos --format csv --output proficiency.csv

# Track progress quarterly
measure-ai-proficiency --org /path/to/all-repos --format json --output q1-2025.json
```

### CI/CD Integration

```yaml
# .github/workflows/ai-proficiency.yml
- name: Check AI Proficiency
  run: |
    pip install measure-ai-proficiency
    measure-ai-proficiency --min-level 1 || echo "No context engineering detected"
```

### Team Onboarding

```bash
# Show new team members what context engineering looks like
measure-ai-proficiency -v
```

## Contributing

Contributions welcome! Areas of interest:

- Additional file patterns for new tools
- Integration with GitHub API for remote scanning
- Historical tracking and trend analysis
- IDE extensions

## License

MIT

## Related

- [Context Engineering Article](./measuring-ai-proficiency-context-engineering.md) - The thinking behind this tool
- [Steve Yegge's Gas Town](https://steve-yegge.medium.com/welcome-to-gas-town-4f25ee16dd04) - Behavioral maturity model inspiration
- [Anthropic Claude Code Docs](https://docs.anthropic.com/en/docs/claude-code)
- [GitHub Copilot Custom Instructions](https://docs.github.com/en/copilot)
