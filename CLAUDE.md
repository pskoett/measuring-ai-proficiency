# Agent Instructions

## Workflow Orchestration

### 1. Plan Mode Default
- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)
- If something goes sideways, STOP and re-plan immediately - don't keep pushing
- Use plan mode for verification steps, not just building
- Write detailed specs upfront to reduce ambiguity

### 2. Subagent Strategy
- Use subagents liberally to keep main context window clean
- Offload research, exploration, and parallel analysis to subagents
- For complex problems, throw more compute at it via subagents
- One task per subagent for focused execution

### 3. Self-Improvement Loop
- After ANY correction from the user: use `/self-improvement` to log:
- Write rules for yourself that prevent the same mistake
- Ruthlessly iterate on these lessons until mistake rate drops
- Review lessons at session start for relevant project

## Self-Improvement Workflow

When errors or corrections occur:
1. Log to `.learnings/ERRORS.md`, `LEARNINGS.md`, or `FEATURE_REQUESTS.md`
2. Review and promote broadly applicable learnings to:
   - `CLAUDE.md` - project facts and conventions
   - `AGENTS.md` - workflows and automation
   - `.github/copilot-instructions.md` - Copilot context
3. If the user requests a commit cadence (for example, "commit after each iteration"), create a commit at the end of each completed iteration before asking for the next test.

### 4. Verification Before Done
- Never mark a task complete without proving it works
- Diff behavior between main and your changes when relevant
- Ask yourself: "Would a staff engineer approve this?"
- Run tests, check logs, demonstrate correctness

### 5. Demand Elegance (Balanced)
- For non-trivial changes: pause and ask "is there a more elegant way?"
- If a fix feels hacky: "Knowing everything I know now, implement the elegant solution"
- Skip this for simple, obvious fixes - don't over-engineer
- Challenge your own work before presenting it

### 6. Autonomous Bug Fixing
- When given a bug report: just fix it. Don't ask for hand-holding
- Point at logs, errors, failing tests - then resolve them
- Zero context switching required from the user
- Go fix failing CI tests without being told how

## Task Management

1. **Plan First**: Write plan to `/todo.md` with checkable items
2. **Verify Plan**: Check in before starting implementation
3. **Track Progress**: Mark items complete as you go
4. **Explain Changes**: High-level summary at each step
5. **Document Results**: Add review section to `/todo.md`
6. **Capture Lessons**: Update `.learnings` files after corrections in `/self-improvement`
7. **Review Before Done**: Final review of the session use the '/simplify-and-harden skill' to ensure everything is clear and robust

## Core Principles

- **Simplicity First**: Make every change as simple as possible. Impact minimal code.
- **No Laziness**: Find root causes. No temporary fixes. Senior developer standards.
- **Minimal Impact**: Changes should only touch what's necessary. Avoid introducing bugs.
- **Learn and Improve**: Every mistake is a learning opportunity. Log it, learn from it, and prevent it in the future.

# Project Context

This is `measure-ai-proficiency`, a CLI tool for measuring AI coding proficiency based on context engineering artifacts.

## Overview

The tool scans repositories for files like `CLAUDE.md`, `.cursorrules`, `.github/copilot-instructions.md`, `.github/skills/*/SKILL.md`, and `AGENTS.md` to assess how effectively teams are preparing context for AI coding assistants.

**Key Features:**
- 8-level maturity scoring aligned with Steve Yegge's model
- **2026 context-engineering signals** (verification, hooks, eval loops, telemetry, anti-drift maintenance hygiene, dynamic-workflow orchestration, plugins, harness engineering, curricula) — grounded in official docs only; see `docs/SIGNALS.md`
- **L6-L8 are signal-gated**: reaching those levels requires the matching primitives/harness/orchestration signals AND file coverage (not coverage alone)
- Structural quality scoring of the 6 primitives (skill frontmatter/executable content/verification, hook events, subagents, workflows, plugins)
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
- `check_harness_orchestration_quality` - 2026 harness/orchestration maturity + L6-L8 signal gates
- `scan_for_maintenance_hygiene` - Anti-drift maintenance hygiene (sentinel/canary, audit/detox, steward, decay)
- `get_dynamic_workflow_recommendations` - Adopt Dynamic Workflows + verification (scoped to detectable artifacts)
- `curricula_alignment` - Official learning on-ramp references (Anthropic Academy, Google 5-Day AI Agents)
- `cheapest_primitive_decision_tree_report` - Primitive decision discipline (Skill → MCP → Subagent → Hook → Plugin)

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

See `docs/MCP.md` for full documentation, examples, and troubleshooting.

## Agent Factory

This repo runs an agent factory via [GitHub Agentic Workflows (gh-aw)](https://github.github.com/gh-aw/) plus two plain GitHub Actions workflows (`plan-merged-dispatcher`, `trigger-plan`). The chain flows: triage, spec, plan, implement, review, fix, learn. The source issue is the unit of work end-to-end; there is no sub-issue layer.

**Workflows** live in `.github/workflows/*.md` and compile to `.lock.yml` files via `gh aw compile`.

**Key files:**
- `docs/AGENT_FACTORY.md` - Full usage guide with step-by-step instructions
- `docs/chain.md` - Architecture diagram and design rationale
- `AGENTS.md` - Shared context read by every workflow at run start

**Common tasks:**
- Add a new workflow: create `.github/workflows/<name>.md`, run `gh aw compile <name>`
- Edit a workflow: modify the `.md` file, run `gh aw compile <name>`, commit both `.md` and `.lock.yml`
- Update gh-aw: `gh extension upgrade gh-aw`, then `gh aw compile` to recompile all lock files
- Add a skill for workflows: create `.claude/skills/<name>/SKILL.md`, reference it from the workflow body
- Debug a run: `gh aw logs <workflow>` or `gh aw audit <run-id>`

**Factory chain:** issue-triage > spec-refiner (classifies: plan-worthy, direct-route, or blocked) > [plan-worthy: plan PR merged > plan-merged-dispatcher >] implementer-dispatcher > reviewer + contribution-checker > /pr-fix > ci-cleaner > self-improvement-meta (nightly)

**Human decisions:** (1) for plan-worthy issues: review and merge the plan PR, (2) merge the final PR, (3) approve learnings. Direct-route issues skip step 1. Everything else is automated.

## Architecture

```
measure_ai_proficiency/
├── __init__.py        # Package exports
├── __main__.py        # CLI entry point
├── mcp_server.py      # MCP server for AI assistant integration
├── config.py          # Level definitions and file patterns
├── signals.py         # 2026 context-engineering signal registry + L6-8 gate requirements (official-doc grounded)
├── scanner.py         # Repository scanning logic + cross-reference detection + signal analysis + L6-8 gating
├── github_scanner.py  # GitHub CLI integration for remote scanning
├── reporter.py        # Output formatting (terminal, JSON, markdown, CSV)
└── repo_config.py     # Repository configuration and tool auto-detection

scripts/
├── find-org-repos.sh  # GitHub org discovery script (uses gh CLI)
└── README.md          # Script documentation

.github/workflows/     # Agentic workflows (gh-aw)
├── spec-refiner.md              # Plan file from issue context
├── reviewer.md                  # Plan-aware PR review
├── self-improvement-meta.md     # Nightly learnings extraction
├── ci-cleaner.md                # Auto-fix CI on main
├── contribution-checker.md      # CONTRIBUTING.md compliance
├── issue-triage.md              # Auto-label issues (githubnext/agentics)
├── plan-merged-dispatcher.yml   # Activates source issue on plan PR merge (plain Actions)
├── trigger-plan.yml             # Activates issue when needs-plan is applied manually (plain Actions)
├── pr-fix.md                    # /pr-fix slash command (githubnext/agentics)
├── ai-proficiency-pr-review.md  # Proficiency score per PR
├── ai-proficiency-weekly-report.md  # Weekly proficiency trends
└── *.lock.yml                   # Compiled GitHub Actions YAML
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
- Add a new 2026 signal: Add a `SignalGroup` to `SIGNAL_GROUPS` in `measure_ai_proficiency/signals.py` (keyword patterns + weight + an **official** reference). To gate a level, add its key to `LEVEL_GATE_REQUIREMENTS` and resolve it in `RepoScanner._compute_signal_gates`. Add a regression eval under `.evals/cases/`. See `docs/SIGNALS.md`.
- Adjust L6-8 gating: Edit `LEVEL_GATE_REQUIREMENTS` (signals.py) and `_compute_signal_gates` (scanner.py). Levels 6-8 require signals AND file coverage; the `gates` dict flows into `_calc_level_with_thresholds`.
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
