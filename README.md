# Measure AI Proficiency

A CLI tool for measuring AI coding proficiency based on context engineering artifacts.

## The Problem

Adoption ≠ proficiency. Some developers save 10+ hours a week with AI. Others get slower with the same tools.

**How do you measure actual AI proficiency?**

## The Solution

Measure context engineering. Look at whether teams are creating files like `CLAUDE.md`, `.cursorrules`, `.github/copilot-instructions.md`, and `AGENTS.md`. These artifacts indicate that someone has moved beyond treating AI as fancy autocomplete and started deliberately shaping how AI understands their work.

This tool scans repositories for context engineering artifacts and calculates a maturity score based on an 8-level model aligned with [Steve Yegge's stages](https://steve-yegge.medium.com/welcome-to-gas-town-4f25ee16dd04).

## Quick Start

```bash
# Install from PyPI
pip install measure-ai-proficiency

# Run on any repository
cd /path/to/your-project
measure-ai-proficiency
```

That's it! The tool scans for files like `CLAUDE.md`, `.cursorrules`, `.github/copilot-instructions.md`, and calculates a maturity score.

## What You'll See

```
============================================================
 AI Proficiency Report: my-project
============================================================

  Overall Level: Level 5: Multi-Agent Ready
  Overall Score: 59.8/100
  AI Tools: Claude Code, GitHub Copilot

  Level Breakdown:
    ✓ Level 1: Zero AI            [████████████████████] 100.0%
    ✓ Level 2: Basic Instructions [█████████████░░░░░░░] 66.7%
    ✓ Level 3: Comprehensive      [███|░░░░░░░░░░░░░░░░] 19.0%/15% ✓
    ✓ Level 4: Skills & Automation[██|░░░░░░░░░░░░░░░░░] 14.5%/12% ✓
    ✓ Level 5: Multi-Agent Ready  [██|░░░░░░░░░░░░░░░░░] 13.9%/10% ✓
    ○ Level 6: Fleet Ready        [░|░░░░░░░░░░░░░░░░░░] 0.0%/8% needs +8%

  Validation Warnings:
    📋 TEMPLATE: CLAUDE.md contains template markers (your-org-name)
    ⚠️ MISSING REF: CLAUDE.md references 'old-file.ts' (deleted)

    Penalty: -2.0 points

  Behavioral Indicators (Levels 6-8):
    ✓ CI/CD Agent Integration (L6)
    ○ Agent Handoffs (L7): 3 agents
    ○ Measured Outcomes (L8)

  Recommendations:
    → 🎯 FLEET READY: Add fleet infrastructure for parallel agents
    → 🧠 Set up Beads for persistent memory across sessions
    → 🔄 Add workflows/ for multi-step process definitions
```

## Installation

```bash
pip install measure-ai-proficiency
```

Or install from source:

```bash
git clone https://github.com/pskoett/measuring-ai-proficiency.git
cd measuring-ai-proficiency
pip install -e .
```

## Usage

The tool supports **two scanning modes** - choose the one that fits your workflow:

### Mode 1: Local Scanning (Default)

Scan repositories on your local disk. Works offline, no authentication needed.

```bash
# Scan current directory
measure-ai-proficiency

# Scan specific repository
measure-ai-proficiency /path/to/repo

# Scan multiple repositories
measure-ai-proficiency /path/to/repo1 /path/to/repo2

# Scan all repos in a directory (cloned GitHub org)
measure-ai-proficiency --org /path/to/cloned-org
```

**Best for:**
- Local development
- Offline scanning
- Repos already on disk
- No GitHub authentication needed

### Mode 2: GitHub CLI Scanning (Optional)

Scan GitHub repositories directly **without cloning** them using the GitHub CLI:

```bash
# Scan a single GitHub repository
measure-ai-proficiency --github-repo owner/repo

# Scan an entire GitHub organization
measure-ai-proficiency --github-org anthropic

# Limit the number of repos scanned
measure-ai-proficiency --github-org anthropic --limit 50

# Combine with output formats
measure-ai-proficiency --github-org your-org --format json --output report.json
```

**Best for:**
- Scanning organizations without cloning
- Large-scale analysis
- Private repos (with authentication)
- Quick assessments of remote repos

**Requirements:**
- [GitHub CLI (gh)](https://cli.github.com/) must be installed
- Must be authenticated: `gh auth login`

**How it works:**
1. Uses GitHub API to fetch repository file tree
2. Downloads only relevant AI proficiency files (no full clone!)
3. Scans the files locally in a temporary directory
4. Cleans up automatically after scanning

**Advantages over cloning:**
- ✅ Much faster (only downloads relevant files)
- ✅ No disk space needed for full repositories
- ✅ Works with hundreds of repos efficiently
- ✅ Automatic cleanup after scanning

### Choosing Between Modes

| Feature | Local Scanning | GitHub CLI Scanning |
|---------|----------------|---------------------|
| **Setup** | None | Requires `gh` CLI + auth |
| **Network** | Works offline | Requires internet |
| **Speed** | Fast for local repos | Fast for remote repos |
| **Disk Space** | Uses existing repos | Minimal (temp files only) |
| **Authentication** | Not needed | GitHub auth required |
| **Private Repos** | Must clone first | Works if authenticated |
| **Best Use** | Local development | Organization-wide analysis |

**Note:** Both scanning modes support all features:
- All output formats (terminal, JSON, markdown, CSV)
- All CLI flags (--format, --output, -q, --min-level)
- Cross-reference detection and quality scoring
- Tool auto-detection
- Custom configuration (`.ai-proficiency.yaml`)

### Output Formats

Both scanning modes work with all output formats:

```bash
# Terminal output (default, with colors)
measure-ai-proficiency

# JSON output
measure-ai-proficiency --format json

# Markdown report
measure-ai-proficiency --format markdown

# CSV (for spreadsheets)
measure-ai-proficiency --format csv

# Save to file
measure-ai-proficiency --format markdown --output report.md
```

### Other Options

```bash
# Quiet mode (summary only)
measure-ai-proficiency -q

# Filter by minimum level
measure-ai-proficiency --org /path/to/org --min-level 2
```

## Maturity Levels

The tool measures maturity on an 8-level scale aligned with [Steve Yegge's stages](https://steve-yegge.medium.com/welcome-to-gas-town-4f25ee16dd04):

| Level | Name | Description |
|-------|------|-------------|
| 1 | Zero AI | No AI-specific files (baseline) |
| 2 | Basic Instructions | Basic context files (CLAUDE.md, .cursorrules, etc.) |
| 3 | Comprehensive Context | Architecture, conventions, patterns documented |
| 4 | Skills & Automation | Hooks, commands, memory files, workflows |
| 5 | Multi-Agent Ready | Multiple agents, MCP configs, handoffs |
| 6 | Fleet Infrastructure | Beads, shared context, workflow pipelines |
| 7 | Agent Fleet | Governance, scheduling, 10+ agents |
| 8 | Custom Orchestration | Gas Town, meta-automation, frontier |

## Supported Tools

The tool auto-detects and supports all major AI coding tools:

- **Claude Code**: `CLAUDE.md`, `AGENTS.md`, `.claude/`
- **GitHub Copilot**: `.github/copilot-instructions.md`, `.github/agents/`, `.github/skills/`
- **Cursor**: `.cursorrules`, `.cursor/rules/`, `.cursor/skills/`
- **OpenAI Codex CLI**: `CODEX.md`, `.codex/`, `AGENTS.md`
- **VSCode AI**: `.vscode/*.md`

**Smart Scanning**: Automatically excludes `node_modules/`, `venv/`, `dist/`, `build/`, and other dependency folders.

## Example Output

### Terminal

```
============================================================
 AI Proficiency Report: measuring-ai-proficiency
============================================================

  Overall Level: Level 4: Skills & Automation
  Overall Score: 18.8/100
  AI Tools: Claude Code, GitHub Copilot

  Level Breakdown:

    ✓ Level 1: Zero AI
      [████████████████████] 100.0%  (1 files)
        ● README.md

    ✓ Level 2: Basic Instructions
      [█████████████░░░░░░░] 66.7%  (2 files)
        ● CLAUDE.md
        ● .github/copilot-instructions.md

    ✓ Level 3: Comprehensive Context
      [███|░░░░░░░░░░░░░░░░] 19.0%/15% ✓ (59 files)
        ● docs/ARCHITECTURE.md
        ● CONVENTIONS.md
        ● CONTRIBUTING.md
        ... and 56 more

    ✓ Level 4: Skills & Automation
      [██|░░░░░░░░░░░░░░░░░] 14.5%/12% ✓ (20 files)
        ● .claude/skills/measure-ai-proficiency/SKILL.md
        ● .github/skills/agentic-workflow/SKILL.md
        ... and 18 more

    ○ Level 5: Multi-Agent Ready
      [█░|░░░░░░░░░░░░░░░░░] 8.3%/10% needs +1.7% (5 files)
        ● .github/agents/create-agentic-workflow.agent.md
        ● .github/agents/debug-agentic-workflow.agent.md

  Cross-References & Quality:

    References: 102 found in 10 files
    Unique targets: 33
    Resolved: 62/102 (61%)

    Content Quality:
      CLAUDE.md: 10.0/10 (565 words) [§ ⌘ $ ! ↻8]
      .github/copilot-instructions.md: 10.0/10 (598 words) [§ ⌘ $ ↻6]
      .claude/skills/measure-ai-proficiency/SKILL.md: 10.0/10 (851 words) [§ ⌘ $ ! ↻9]

    Quality indicators:
      §=sections  ⌘=paths  $=commands  !=constraints  ↻N=commits

    Bonus: +8.8 points

  Recommendations:

    → 🔍 Detected AI tools: Claude Code, GitHub Copilot.
    → 🚀 Configure multiple specialized agents and MCP integrations.
    → 🤝 Create agents/HANDOFFS.md for agent coordination.

============================================================
```

### JSON

```json
{
  "repo_name": "measuring-ai-proficiency",
  "overall_level": 4,
  "overall_score": 18.83,
  "detected_tools": ["claude-code", "github-copilot"],
  "level_scores": {
    "1": {"name": "Level 1: Zero AI", "coverage_percent": 100.0, "file_count": 1},
    "2": {"name": "Level 2: Basic Instructions", "coverage_percent": 66.67, "file_count": 2},
    "3": {"name": "Level 3: Comprehensive Context", "coverage_percent": 18.99, "file_count": 59},
    "4": {"name": "Level 4: Skills & Automation", "coverage_percent": 14.49, "file_count": 20}
  },
  "cross_references": {
    "total_count": 102,
    "resolved_count": 62,
    "resolution_rate": 60.78,
    "bonus_points": 8.83
  },
  "recommendations": ["..."]
}
```

### Markdown

The markdown format produces a detailed report with tables:

| Level | Coverage | Files | Status |
|-------|----------|-------|--------|
| Level 1: Zero AI | 100.0% | 1 | ✓ |
| Level 2: Basic Instructions | 66.7% | 2 | ✓ |
| Level 3: Comprehensive Context | 19.0% | 59 | ✓ |
| Level 4: Skills & Automation | 14.5% | 20 | ✓ |
| Level 5: Multi-Agent Ready | 8.3% | 5 | ○ |

**Content Quality:**

| File | Score | Words | Commits |
|------|-------|-------|---------|
| `CLAUDE.md` | 10.0/10 | 565 | 8 |
| `.github/copilot-instructions.md` | 10.0/10 | 598 | 6 |
| `.claude/skills/measure-ai-proficiency/SKILL.md` | 10.0/10 | 851 | 9 |

---

## Files Detected by Level

### Level 2: Basic Instructions

| Tool | Files |
|------|-------|
| Claude Code | `CLAUDE.md`, `AGENTS.md` |
| GitHub Copilot | `.github/copilot-instructions.md`, `.github/AGENTS.md` |
| Cursor | `.cursorrules`, `.cursor/*.md` |
| OpenAI Codex | `CODEX.md`, `.codex/*.md` |

### Level 3: Comprehensive Context

| Category | Files |
|----------|-------|
| Architecture | `ARCHITECTURE.md`, `docs/ARCHITECTURE.md`, `DESIGN.md` |
| API & Data | `API.md`, `docs/API.md`, `DATA_MODEL.md` |
| Standards | `CONVENTIONS.md`, `STYLE.md`, `CONTRIBUTING.md`, `PATTERNS.md`, `PR_REVIEW.md` |
| Development | `DEVELOPMENT.md`, `TESTING.md`, `DEBUGGING.md`, `DEPLOYMENT.md` |

### Level 4: Skills & Automation

| Category | Files |
|----------|-------|
| Skills | `.claude/skills/*/SKILL.md`, `.github/skills/*/SKILL.md`, `.cursor/skills/*/SKILL.md` |
| Workflows | `.claude/commands/`, `WORKFLOWS.md`, `scripts/` |
| Memory | `MEMORY.md`, `LEARNINGS.md`, `DECISIONS.md` |
| Hooks | `.claude/hooks/`, `.claude/settings.json` |

### Level 5+: Multi-Agent & Fleet

| Category | Files |
|----------|-------|
| Agents | `.github/agents/*.agent.md`, `agents/HANDOFFS.md` |
| MCP | `.mcp.json`, `.mcp/*.json` |
| Orchestration | `orchestration.yaml`, `workflows/*.yaml` |

---

## Cross-Reference Detection & Quality

The tool analyzes the *content* of your AI instruction files, not just their existence.

### Quality Scoring (0-10)

| Indicator | What We Look For | Points |
|-----------|------------------|--------|
| **Sections** | Markdown headers (`##`) - 5+ headers = full points | 0-2 |
| **Paths** | Concrete file paths (`/src/`, `~/config/`) | 0-2 |
| **Commands** | CLI commands in backticks (`` `npm test` ``) | 0-2 |
| **Constraints** | "never", "avoid", "don't", "must not", "always" | 0-2 |
| **Substance** | Word count (200+ = 2pts, 50-200 = 1pt) | 0-2 |
| **Commits** | Git history (5+ = 2pts, 3-4 = 1pt) | 0-2 |

*Quality score is capped at 10.*

### Bonus Points (up to +10)

- **Cross-reference bonus (up to 5 pts)**: References between docs, resolution rate
- **Quality bonus (up to 5 pts)**: Half of average quality score

---

## Customization

### For Your Team

Different teams use different file names. The tool works best when customized:

1. Run the tool to see what it detects
2. Review patterns in `measure_ai_proficiency/config.py`
3. Add your team's specific file names
4. Adjust thresholds if needed

📖 **[Read the full customization guide](CUSTOMIZATION.md)**

### Configuration File

Create `.ai-proficiency.yaml` in your repository:

```yaml
# Specify which AI tools your team uses
tools:
  - claude-code
  - github-copilot

# Adjust level thresholds (lower = easier to advance)
thresholds:
  level_3: 10   # Default: 15
  level_4: 8    # Default: 12

# Skip certain recommendations
skip_recommendations:
  - hooks
  - gastown
```

### Add Custom Patterns

```python
# In config.py, add your team's files:
file_patterns=[
    "SYSTEM_DESIGN.md",      # Instead of ARCHITECTURE.md
    "documentation/*.md",    # Instead of docs/
    "CODING_STANDARDS.md",   # Instead of CONVENTIONS.md
]
```

---

## GitHub Action

Automatically assess AI proficiency on every PR:

```bash
# Quick setup with GitHub Agentic Workflows
gh extension install githubnext/gh-aw
gh aw add pskoett/measuring-ai-proficiency/.github/workflows/ai-proficiency-pr-review --create-pull-request
```

📖 **[Full GitHub Action documentation](GITHUB_ACTION.md)**

---

## Agent Skills

Want AI to help improve your context engineering? Add skills to your repository:

### Available Skills

| Skill | Description |
|-------|-------------|
| **measure-ai-proficiency** | Assess repository AI maturity |
| **customize-measurement** | Generate a customized `.ai-proficiency.yaml` |
| **plan-interview** | Structured requirements gathering |
| **agentic-workflow** | Create natural language GitHub Actions |

### Install Skills

**For Claude Code:**
```bash
mkdir -p .claude/skills/measure-ai-proficiency
curl -o .claude/skills/measure-ai-proficiency/SKILL.md \
  https://raw.githubusercontent.com/pskoett/measuring-ai-proficiency/main/skill-template/measure-ai-proficiency/SKILL.md
```

**For GitHub Copilot:**
```bash
mkdir -p .github/skills/measure-ai-proficiency
curl -o .github/skills/measure-ai-proficiency/SKILL.md \
  https://raw.githubusercontent.com/pskoett/measuring-ai-proficiency/main/skill-template/measure-ai-proficiency/SKILL.md
```

Then ask your AI: *"Assess my AI proficiency"* or *"What context files should I add?"*

### AI Agents

For systematic improvement workflows, use the **AI Context Improvement Agent**:

**Available in this repo:**
- `.github/agents/improve-ai-context.agent.md` - For GitHub Copilot
- `.claude/agents/improve-ai-context.agent.md` - For Claude Code

**Integrated workflow using three skills:**

1. **plan-interview** - Gathers requirements about your team's goals and constraints
2. **customize-measurement** - Creates tailored `.ai-proficiency.yaml` configuration
3. **measure-ai-proficiency** - Assesses and systematically improves your context

**What it does:**
- Interviews you about team goals, tools, and target maturity level
- Creates custom configuration matching your needs
- Runs AI proficiency assessment with your config
- Analyzes gaps and quality scores
- Creates missing context files systematically
- Improves existing files with low quality scores
- Re-scans to verify improvements
- Works with single repos or entire organizations

**How to use:**

Ask your AI assistant:
- *"Improve my AI proficiency"* (full workflow with interview and config)
- *"Help me understand what context I need"* (starts with plan-interview)
- *"Configure measurement for my team"* (uses customize-measurement)
- *"Create missing context files"* (quick assessment and improvement)
- *"Fix my low quality score"* (focused on quality improvements)
- *"Advance to Level 4"* (goal-oriented improvement)

The agent will guide you through requirements gathering, create a custom configuration, scan your repo, identify gaps, and systematically create or improve files to advance your maturity level.

---

## Discover & Scan GitHub Organizations

You can now scan entire GitHub organizations without cloning any repositories:

```bash
# Scan all repos in an organization
measure-ai-proficiency --github-org your-org-name --format json --output report.json
```

Alternatively, use the discovery script to first see which repos have AI artifacts:

```bash
./scripts/find-org-repos.sh your-org-name

# Example output:
# Organization: anthropics
# Active repositories: 45
# Repos with AI context artifacts: 12 (26.7%)
```

Both methods require [GitHub CLI (gh)](https://cli.github.com/) to be installed and authenticated. The discovery script also requires [jq](https://stedolan.github.io/jq/).

---

## Use Cases

### Engineering Leadership

```bash
# Assess AI proficiency across your organization
measure-ai-proficiency --org /path/to/all-repos --format csv --output proficiency.csv
```

### CI/CD Integration

```yaml
- name: Check AI Proficiency
  run: |
    pip install git+https://github.com/pskoett/measuring-ai-proficiency.git
    measure-ai-proficiency --min-level 1
```

### Team Onboarding

```bash
# Show new team members what context engineering looks like
measure-ai-proficiency
```

---

## Scoring Algorithm

1. **File Detection**: Scan for patterns at each level (1-8)
2. **Substantiveness Check**: Files must have >100 bytes to count
3. **Coverage Calculation**: Percentage of patterns matched per level
4. **Level Achievement**:
   - Level 2: At least one AI context file
   - Level 3: Level 2 + ≥15% coverage
   - Level 4: Level 3 + ≥12% coverage
   - Level 5+: Progressive thresholds (≥10%, ≥8%, ≥6%, ≥5%)
5. **Minimum Score Guarantees**: Each level achieved guarantees a minimum score:
   - Level 2: 15, Level 3: 30, Level 4: 45, Level 5: 55
   - Level 6: 70, Level 7: 85, Level 8: 95
6. **Bonus**: Up to +10 points from cross-references and quality
7. **Validation Penalties**: Up to -10 points for issues (see below)

### Content Validation

The tool validates your context files beyond just counting them:

| Validation | What It Checks | Penalty |
|------------|----------------|---------|
| **Freshness** | Files updated within 90 days of code changes | -2 pts per stale file (max -6) |
| **Alignment** | Referenced files actually exist | -1 pt per missing ref (max -4) |
| **Templates** | Detects copy-pasted boilerplate markers | -2 pts if majority are templates |

**Warnings displayed:**
- `STALE: CLAUDE.md last updated 120 days ago` - Your context is outdated
- `MISSING REF: CLAUDE.md references 'src/old.ts' (deleted)` - Broken references
- `TEMPLATE: CLAUDE.md contains template markers` - Uncustomized boilerplate

### Behavioral Indicators (Levels 6-8)

Higher levels now have concrete behavioral requirements beyond file patterns:

| Level | Indicator | What It Checks |
|-------|-----------|----------------|
| **L6** | CI/CD Integration | GitHub Actions workflows that invoke agents |
| **L7** | Agent Handoffs | 2+ agents with documented handoff protocols |
| **L8** | Measured Outcomes | Metrics files, logs, or success tracking |

These indicators are displayed in the output but don't affect scoring (yet).

### Understanding Your Score

**Low score but lots of files?** This is normal! The tool includes hundreds of patterns. Your team likely uses different file names - customize the patterns for accurate scoring.

**Got validation warnings?** These identify issues that reduce AI effectiveness:
- Stale context files mislead AI with outdated information
- Broken references confuse AI about your codebase structure
- Template content provides generic rather than project-specific guidance

---

## Contributing

Contributions welcome! Areas of interest:
- Additional file patterns for new tools
- ✅ ~~Integration with GitHub API for remote scanning~~ (implemented via GitHub CLI)
- Historical tracking and trend analysis
- IDE extensions

## License

MIT

## Related

- [Context Engineering Article](./measuring-ai-proficiency-context-engineering.md) - The thinking behind this tool
- [Steve Yegge's Gas Town](https://steve-yegge.medium.com/welcome-to-gas-town-4f25ee16dd04) - Behavioral maturity model inspiration
- [Claude Code Skills](https://code.claude.com/docs/en/skills) | [GitHub Copilot Skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills) | [Agent Skills Standard](https://agentskills.io/)
