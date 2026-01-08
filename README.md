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
# Install from source
git clone https://github.com/pskoett/measuring-ai-proficiency
cd measuring-ai-proficiency
pip install -e .

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

  Overall Level: Level 2: Basic Instructions
  Overall Score: 24.5/100
  AI Tools: Claude Code, GitHub Copilot

  Level Breakdown:
    ✓ Level 1: Zero AI           [████████████████████] 100.0%
    ✓ Level 2: Basic Instructions [████████░░░░░░░░░░░░] 40.0%
    ○ Level 3: Comprehensive      [██░|░░░░░░░░░░░░░░░░] 12.7%/15%

  Recommendations:
    → 📚 Add ARCHITECTURE.md, CONVENTIONS.md, TESTING.md
    → 🎨 Add PATTERNS.md: Document common design patterns
```

## Installation

```bash
# Clone and install
git clone https://github.com/pskoett/measuring-ai-proficiency
cd measuring-ai-proficiency
pip install -e .
```

*PyPI package coming soon.*

## Usage

### Basic Commands

```bash
# Scan current directory
measure-ai-proficiency

# Scan specific repository
measure-ai-proficiency /path/to/repo

# Scan multiple repositories
measure-ai-proficiency /path/to/repo1 /path/to/repo2

# Scan all repos in a directory (GitHub org)
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

### Terminal (Full)

```
============================================================
 AI Proficiency Report: my-project
============================================================

  Overall Level: Level 3: Comprehensive Context
  Overall Score: 32.4/100
  AI Tools: Claude Code, GitHub Copilot

  Level Breakdown:

    ✓ Level 1: Zero AI
      [████████████████████] 100.0%  (1 files)

    ✓ Level 2: Basic Instructions
      [████████░░░░░░░░░░░░] 40.0%  (2 files)

    ✓ Level 3: Comprehensive Context
      [██████|░░░░░░░░░░░░░] 28.5%/15% ✓ (12 files)

    ○ Level 4: Skills & Automation
      [██░|░░░░░░░░░░░░░░░░] 8.2%/12% needs +3.8% (4 files)

    ○ Level 5: Multi-Agent Ready
      [░|░░░░░░░░░░░░░░░░░░] 0.0%/10% needs +10.0% (0 files)

    ○ Level 6: Fleet Infrastructure
      [░|░░░░░░░░░░░░░░░░░░] 0.0%/8% needs +8.0% (0 files)

    ○ Level 7: Agent Fleet
      [░|░░░░░░░░░░░░░░░░░░] 0.0%/6% needs +6.0% (0 files)

    ○ Level 8: Custom Orchestration
      [░|░░░░░░░░░░░░░░░░░░] 0.0%/5% needs +5.0% (0 files)

  Cross-References & Quality:

    References: 12 found in 3 files
    Unique targets: 8
    Resolved: 10/12 (83%)

    Content Quality:
      CLAUDE.md: 8.2/10 (450 words) [§ ⌘ $ ! ↻8]
      AGENTS.md: 9.5/10 (820 words) [§ ⌘ $ ↻12]
      .github/copilot-instructions.md: 7.8/10 (320 words) [§ ⌘ $ ↻5]

    Quality indicators:
      §=sections  ⌘=paths  $=commands  !=constraints  ↻N=commits

    Bonus: +7.2 points

  Recommendations:

    → 🔍 Detected AI tools: Claude Code, GitHub Copilot. Recommendations tailored accordingly.
    → 📚 Add comprehensive documentation - ARCHITECTURE.md, API.md, CONVENTIONS.md, TESTING.md.
    → 🎨 Add PATTERNS.md: Document common design patterns used in your codebase.

============================================================
```

### JSON

```json
{
  "repo_path": "/path/to/my-project",
  "repo_name": "my-project",
  "overall_level": 3,
  "overall_score": 32.4,
  "detected_tools": ["claude-code", "github-copilot"],
  "level_scores": {
    "1": {"name": "Level 1: Zero AI", "coverage_percent": 100.0},
    "2": {"name": "Level 2: Basic Instructions", "coverage_percent": 40.0}
  },
  "cross_references": {
    "total_count": 12,
    "resolved_count": 10,
    "bonus_points": 7.2
  },
  "recommendations": ["..."]
}
```

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

---

## Discover Repos in Your Organization

Before scanning, find which repositories have context engineering artifacts:

```bash
./scripts/find-org-repos.sh your-org-name

# Example output:
# Organization: anthropics
# Active repositories: 45
# Repos with AI context artifacts: 12 (26.7%)
```

Requires [GitHub CLI (gh)](https://cli.github.com/) and [jq](https://stedolan.github.io/jq/).

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
5. **Bonus**: Up to +10 points from cross-references and quality

### Understanding Your Score

**Low score but lots of files?** This is normal! The tool includes hundreds of patterns. Your team likely uses different file names - customize the patterns for accurate scoring.

---

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
- [Claude Code Skills](https://code.claude.com/docs/en/skills) | [GitHub Copilot Skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills) | [Agent Skills Standard](https://agentskills.io/)
