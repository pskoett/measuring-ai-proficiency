# Measure AI Proficiency

A CLI tool for measuring AI coding proficiency based on context engineering artifacts.

## ⚠️ Important: Customize for Your Organization

**This tool provides a baseline assessment** but works best when customized to your team's conventions. Different organizations use different file names, structures, and patterns for context engineering.

**What to do:**
1. Run the tool to see what it detects
2. Review the patterns in `measure_ai_proficiency/config.py`
3. Add your team's specific file names and patterns
4. Adjust thresholds if needed for your organization

📖 **[Read the full customization guide](CUSTOMIZATION.md)** for detailed examples and instructions.

**Example:** If your team uses `SYSTEM_DESIGN.md` instead of `ARCHITECTURE.md`, or stores documentation in `/documentation` instead of `/docs`, you'll need to add those patterns. The tool is designed to be extended, not prescriptive.

## The Problem

Adoption ≠ proficiency. Some developers save X+ hours a week with AI. Others get slower with the same tools.

**How do you measure actual AI proficiency?**

## The Solution

Measure context engineering. Look at whether teams are creating files like `CLAUDE.md`, `.cursorrules`, `.github/copilot-instructions.md`, and `AGENTS.md`. These artifacts indicate that someone has moved beyond treating AI as fancy autocomplete and started deliberately shaping how AI understands their work.

This tool scans repositories for context engineering artifacts and calculates a maturity score based on an 8-level model aligned with Steve Yegge's stages.

**New: Cross-Reference Detection & Quality Evaluation** - The tool now analyzes the *content* of your AI instruction files, detecting cross-references between documents and evaluating quality indicators like sections, constraints, and commands.

## Maturity Levels

| Level | Name | Yegge Stage | Description |
|-------|------|-------------|-------------|
| 1 | Zero AI | Stage 1 | Autocomplete and chat only. No AI-specific files. |
| 2 | Basic Instructions | Stage 2 | Basic context files (CLAUDE.md, .cursorrules, etc.) |
| 3 | Comprehensive Context | Stage 3 | Detailed architecture, conventions, patterns |
| 4 | Skills & Automation | Stage 4 | Hooks, commands, memory files, workflows |
| 5 | Multi-Agent Ready | Stage 5 | Multiple agents, MCP configs, handoffs |
| 6 | Fleet Infrastructure | Stage 6 | Beads, shared context, workflow pipelines |
| 7 | Agent Fleet | Stage 7 | Governance, scheduling, 10+ agents |
| 8 | Custom Orchestration | Stage 8 | Gas Town, meta-automation, frontier |

## Supported Tools

Supports all major AI coding tools and scans **all directories** for context engineering artifacts:

- **Claude Code**: `CLAUDE.md`, `AGENTS.md`, `.claude/agents/`, `.claude/skills/`, `.claude/hooks/`, `.claude/commands/`
- **GitHub Copilot**: `.github/copilot-instructions.md`, `.github/AGENTS.md`, `.github/instructions/`, `.github/agents/`, `.github/skills/`, `.github/*.md`
- **Cursor**: `.cursorrules`, `.cursor/rules/`, `.cursor/*.md`
- **VSCode AI**: `.vscode/*.md`
- **OpenAI Codex CLI**: `.codex/*.md`, `.codex/skills/`, `AGENTS.md`
- **Documentation**: `docs/`, `*/docs/` (recursively scans all subdirectories)

**Agent Skills**: Claude Code, GitHub Copilot, and OpenAI Codex all support the [Agent Skills](https://agentskills.io/) open standard. Skills are stored in `.claude/skills/`, `.github/skills/`, or `.codex/skills/` directories with `SKILL.md` files containing instructions for specialized tasks.

**Smart Scanning**: Automatically excludes `node_modules/`, `venv/`, `dist/`, `build/`, and other dependency folders.

## Auto-Detection & Configuration

### Auto-Detection

The tool automatically detects which AI tools you're using based on files in your repository:

```
============================================================
 AI Proficiency Report: my-project
============================================================

  Overall Level: Level 2: Basic Instructions
  Overall Score: 45.3/100
  AI Tools: Claude Code, Github Copilot    ← Auto-detected!
```

Recommendations are tailored to your detected tools. If you use Claude Code, you'll get Claude-specific recommendations. If you use GitHub Copilot, you'll get Copilot-specific recommendations.

### Custom Configuration

Create a `.ai-proficiency.yaml` file in your repository root to customize behavior:

```yaml
# .ai-proficiency.yaml

# Specify which AI tools your team uses (auto-detected if not specified)
tools:
  - claude-code
  - github-copilot

# Custom file locations (map standard names to your team's conventions)
documentation:
  architecture: "docs/SYSTEM_DESIGN.md"
  conventions: "CODING_STANDARDS.md"
  api: "docs/api/README.md"

# Adjust level thresholds (lower = easier to advance)
thresholds:
  level_3: 10   # Default: 15
  level_4: 8    # Default: 12
  level_5: 6    # Default: 10

# Skip certain recommendation types
skip_recommendations:
  - hooks           # Don't recommend hooks
  - gastown         # Don't recommend Gas Town

# Only show recommendations for specific areas
focus_areas:
  - documentation
  - skills
  - testing
```

When a config file is present, you'll see:

```
  Config: .ai-proficiency.yaml loaded
```

## Scanning Coverage

The tool comprehensively scans for .md files in:

- **AI Tool Directories**: `.github/`, `.claude/`, `.cursor/`, `.vscode/`, `.codex/`, `.copilot/`
- **Documentation**: `docs/`, `backend/docs/`, and any `*/docs/` subdirectories
- **Root Files**: `CLAUDE.md`, `AGENTS.md`, `ARCHITECTURE.md`, `CONTRIBUTING.md`, etc.
- **Skills & Workflows**: `.claude/skills/`, `.github/skills/`, `.codex/skills/`, `scripts/`, `Makefile`, hooks, commands
- **Custom Locations**: Detects files wherever you place them in your repository

**Exclusions**: Automatically skips `node_modules/`, `venv/`, `.venv/`, `env/`, `dist/`, `build/`, `__pycache__/`, `.git/`, `vendor/`, `target/`, `coverage/`, and other common dependency/build directories.

📖 **See Also**: [AGENT_REFERENCES.md](AGENT_REFERENCES.md) for best practices on agent document references and [CUSTOMIZATION.md](CUSTOMIZATION.md) for customization guidance.

## Installation

```bash
# From PyPI (when published)
pip install measure-ai-proficiency

# From source
git clone https://github.com/pskoett/measuring-ai-proficiency
cd measuring-ai-proficiency
pip install -e .
```

## Agent Skill

Want AI to help improve your context engineering automatically? Add the skill to your repository:

**For Claude Code:**
```bash
# Create the skills directory
mkdir -p .claude/skills/measure-ai-proficiency

# Download the skill
curl -o .claude/skills/measure-ai-proficiency/SKILL.md \
  https://raw.githubusercontent.com/pskoett/measuring-ai-proficiency/main/skill-template/measure-ai-proficiency/SKILL.md
```

**For GitHub Copilot:**
```bash
# Create the skills directory
mkdir -p .github/skills/measure-ai-proficiency

# Download the skill
curl -o .github/skills/measure-ai-proficiency/SKILL.md \
  https://raw.githubusercontent.com/pskoett/measuring-ai-proficiency/main/skill-template/measure-ai-proficiency/SKILL.md
```

**For OpenAI Codex:**
```bash
# Create the skills directory
mkdir -p .codex/skills/measure-ai-proficiency

# Download the skill
curl -o .codex/skills/measure-ai-proficiency/SKILL.md \
  https://raw.githubusercontent.com/pskoett/measuring-ai-proficiency/main/skill-template/measure-ai-proficiency/SKILL.md
```

Then ask your AI assistant: "Assess my repository's AI proficiency" or "Help me improve my context engineering"

The skill will automatically scan your repo, explain your maturity level, and offer to create missing context files. See [skill-template/](skill-template/) for the full skill content.

## GitHub Action

Automatically assess AI proficiency on every PR and track progress over time.

### Quick Setup with GitHub Agentic Workflows

```bash
# Install the CLI extension
gh extension install githubnext/gh-aw

# Add the PR review workflow
gh aw add pskoett/measuring-ai-proficiency/.github/workflows/ai-proficiency-pr-review --create-pull-request

# Add the weekly report workflow
gh aw add pskoett/measuring-ai-proficiency/.github/workflows/ai-proficiency-weekly-report --create-pull-request
```

### Alternative: Claude Code Action

For Anthropic API users:

```bash
# In Claude Code terminal
/install-github-app
```

Then copy `.github/workflows/ai-proficiency-claude.yml` to your repository.

### What You Get

- **PR Comments**: Automatic proficiency assessment on every PR
- **Weekly Reports**: GitHub issue tracking progress over time
- **Manual Trigger**: Comment `/assess-proficiency` on any PR or issue

📖 **[Full GitHub Action documentation](GITHUB_ACTION.md)** with setup instructions, customization options, and troubleshooting.

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

  Overall Level: Level 3: Comprehensive Context
  Overall Score: 38.7/100
  AI Tools: Claude Code, Github Copilot

  Level Breakdown:

    ✓ Level 1: Zero AI
      [████████████████████] 100.0% (1 files)

    ✓ Level 2: Basic Instructions
      [████████░░░░░░░░░░░░] 40.0% (2 files)

    ✓ Level 3: Comprehensive Context
      [██████░░░░░░░░░░░░░░] 28.5% (12 files)

    ○ Level 4: Skills & Automation
      [██░░░░░░░░░░░░░░░░░░] 8.2% (4 files)

    ○ Level 5: Multi-Agent Ready
      [░░░░░░░░░░░░░░░░░░░░] 0.0% (0 files)

    ○ Level 6: Fleet Infrastructure
      [░░░░░░░░░░░░░░░░░░░░] 0.0% (0 files)

    ○ Level 7: Agent Fleet
      [░░░░░░░░░░░░░░░░░░░░] 0.0% (0 files)

    ○ Level 8: Custom Orchestration
      [░░░░░░░░░░░░░░░░░░░░] 0.0% (0 files)

  Cross-References & Quality:

    References: 12 found in 3 files
    Unique targets: 8
    Resolved: 10/12 (83%)

    Content Quality:
      CLAUDE.md: 7.2/10 (450 words, 8 sections)
      AGENTS.md: 8.5/10 (820 words, 14 sections)
      .github/copilot-instructions.md: 6.8/10 (320 words, 10 sections)

    Bonus: +6.2 points

  Recommendations:

    → 🔍 Detected AI tools: Claude Code, Github Copilot. Recommendations tailored accordingly.
    → 📚 Add comprehensive documentation - ARCHITECTURE.md, API.md, CONVENTIONS.md, TESTING.md.
    → 🎨 Add PATTERNS.md: Document common design patterns used in your codebase.

============================================================
```

### JSON

```json
{
  "repo_path": "/path/to/my-project",
  "repo_name": "my-project",
  "scan_time": "2026-01-05T12:00:00.000000",
  "overall_level": 3,
  "overall_score": 38.7,
  "detected_tools": ["claude-code", "github-copilot"],
  "config_loaded": false,
  "level_scores": {
    "1": {
      "name": "Level 1: Zero AI",
      "coverage_percent": 100.0,
      "matched_files": [{"path": "README.md", "size_bytes": 4096, "is_substantive": true}]
    },
    "2": {
      "name": "Level 2: Basic Instructions",
      "coverage_percent": 40.0,
      "matched_files": [
        {"path": "CLAUDE.md", "size_bytes": 2048, "is_substantive": true},
        {"path": ".github/copilot-instructions.md", "size_bytes": 1024, "is_substantive": true}
      ]
    }
  },
  "cross_references": {
    "total_count": 12,
    "source_files_scanned": 3,
    "unique_targets": ["ARCHITECTURE.md", "CONVENTIONS.md", "AGENTS.md", "docs/"],
    "resolved_count": 10,
    "resolution_rate": 83.33,
    "bonus_points": 6.2,
    "references": [
      {"source_file": "CLAUDE.md", "target": "ARCHITECTURE.md", "reference_type": "markdown_link", "line_number": 12, "is_resolved": true},
      {"source_file": "CLAUDE.md", "target": "AGENTS.md", "reference_type": "file_mention", "line_number": 8, "is_resolved": true}
    ],
    "quality_scores": {
      "CLAUDE.md": {"quality_score": 7.2, "word_count": 450, "section_count": 8, "has_sections": true, "has_constraints": true},
      "AGENTS.md": {"quality_score": 8.5, "word_count": 820, "section_count": 14, "has_sections": true, "has_constraints": true}
    }
  },
  "recommendations": [
    "🔍 Detected AI tools: Claude Code, Github Copilot. Recommendations tailored accordingly.",
    "📚 Add comprehensive documentation - ARCHITECTURE.md, API.md, CONVENTIONS.md, TESTING.md."
  ]
}
```

## Files Detected

### Level 1: Zero AI (Baseline)

Baseline level - only README.md present, no AI-specific context files.

| File | Purpose |
|------|--------|
| `README.md` | Basic project documentation |

### Level 2: Basic Instructions

Core AI context files that indicate intentional AI tool usage.

| Tool | Files |
|------|-------|
| Claude Code | `CLAUDE.md`, `AGENTS.md` |
| GitHub Copilot | `.github/copilot-instructions.md`, `.github/AGENTS.md`, `.github/*.md` |
| Cursor | `.cursorrules`, `.cursor/*.md` |
| VSCode AI | `.vscode/*.md` |
| Codex CLI | `.codex/*.md` |

### Level 3: Comprehensive Context

| Category | Files |
|----------|-------|
| AI Instructions | `.github/instructions/*.md`, `.cursor/rules/*.md`, `.vscode/*.md`, `.codex/*.md` |
| Architecture | `ARCHITECTURE.md`, `docs/ARCHITECTURE.md`, `docs/architecture/*.md`, `DESIGN.md`, `TECHNICAL_OVERVIEW.md` |
| API & Data | `API.md`, `docs/API.md`, `docs/api/*.md`, `DATA_MODEL.md`, `DOMAIN.md` |
| Standards | `CONVENTIONS.md`, `STYLE.md`, `CONTRIBUTING.md`, `PATTERNS.md`, `CODE_REVIEW.md`, **`PR_REVIEW.md`** ⭐ |
| Development | `DEVELOPMENT.md`, `TESTING.md`, `docs/TESTING.md`, `DEBUGGING.md`, `DEPLOYMENT.md`, `docs/DEPLOYMENT.md` |
| Documentation | `docs/*.md`, `*/docs/*.md` (scans all documentation directories) |

**⭐ PR_REVIEW.md is critical** - This file should define your PR review process, criteria, checklist, and standards. AI tools use this to provide contextual code review feedback.

### Level 4: Skills & Automation

| Category | Files |
|----------|-------|
| Skills | `SKILL.md`, `skills/`, `.claude/skills/*/SKILL.md`, `.github/skills/*/SKILL.md`, `.copilot/skills/*/SKILL.md`, `.codex/skills/*/SKILL.md`, `CAPABILITIES.md` |
| Agents | `.claude/agents/*.md`, `.github/agents/*.md`, `agents/*.md`, `agents/references.md` |
| Workflows | `WORKFLOWS.md`, `.claude/commands/`, `COMMANDS.md`, `scripts/` |
| Memory | `MEMORY.md`, `LEARNINGS.md`, `DECISIONS.md`, `.memory/` |
| Hooks | `.claude/hooks/`, `.claude/settings.json` |
| MCP | `mcp.json`, `.mcp/*.json`, `mcp-config.json` |

**💡 Agent Reference Pattern**: Agents should reference other documentation (ARCHITECTURE.md, CONVENTIONS.md, PR_REVIEW.md) in their instruction files. Create `agents/references.md` or `.claude/agents/references.md` listing all docs agents should consult.

### Level 5: Multi-Agent Ready

| Category | Files |
|----------|-------|
| Agents | `.github/agents/*.agent.md`, `agents/HANDOFFS.md`, `agents/ORCHESTRATION.md`, `agents/REFERENCES.md` |
| PR Review Agents | `.github/agents/reviewer.agent.md`, `.github/agents/pr-reviewer.agent.md`, `.github/agents/code-reviewer.agent.md` |
| Orchestration | `orchestration.yaml`, `workflows/*.yaml` |
| Shared Context | `SHARED_CONTEXT.md`, `packages/*/CLAUDE.md` |
| Memory Systems | `.beads/`, `memory/global/`, `.agent_state/` |

**🔗 Document References in Agents**: For effective multi-agent systems, each agent file should explicitly reference the documentation it needs. For example:
- PR reviewer agents → reference `PR_REVIEW.md`, `CONVENTIONS.md`, `PATTERNS.md`
- Architecture agents → reference `ARCHITECTURE.md`, `DESIGN.md`, `API.md`
- Test agents → reference `TESTING.md`, `CONVENTIONS.md`

## Cross-Reference Detection & Quality Evaluation

The tool analyzes the *content* of your AI instruction files, not just their existence. This provides deeper insight into context engineering maturity.

### What Gets Scanned

AI instruction files are scanned for cross-references and quality:
- `CLAUDE.md`, `AGENTS.md`, `.cursorrules`, `CODEX.md`
- `.github/copilot-instructions.md`, `.copilot-instructions.md`
- Scoped instruction files (`.github/instructions/*.md`, `.cursor/rules/*.md`)
- Skills (`*.claude/skills/*/SKILL.md`, `.github/skills/*/SKILL.md`)

### Cross-Reference Detection

The tool detects references between your documentation files:

| Type | Pattern | Example |
|------|---------|---------|
| Markdown links | `[text](file.md)` | `[architecture](ARCHITECTURE.md)` |
| File mentions | `"FILE.md"`, `` `FILE.md` `` | `"AGENTS.md"`, `` `CONVENTIONS.md` `` |
| Relative paths | `./path/file.md` | `./docs/ARCHITECTURE.md` |
| Directory refs | `skills/`, `.claude/commands/` | `.claude/skills/`, `docs/` |

**Resolution tracking**: The tool checks if referenced files actually exist, helping identify broken links.

### Content Quality Evaluation

Each instruction file is scored (0-10) based on quality indicators inspired by [best-in-class examples](https://github.com/steipete/agent-scripts/blob/main/AGENTS.MD):

| Indicator | What We Look For | Points |
|-----------|------------------|--------|
| **Sections** | Markdown headers (`##`) | 0-2 |
| **Paths** | Concrete file/dir paths (`/src/`, `~/config/`) | 0-2 |
| **Commands** | CLI commands in backticks (`` `npm test` ``) | 0-2 |
| **Constraints** | "never", "avoid", "don't", "must not" | 0-2 |
| **Substance** | Word count (200+ words = full points) | 0-2 |
| **Commits** | Git history (5+ commits = full points) | 0-2 |

### Bonus Points

Cross-references and quality contribute up to **+10 bonus points** to your overall score:

- **Cross-reference bonus (up to 5 pts)**:
  - +3 pts for unique targets referenced (max at 6 unique)
  - +2 pts for resolution rate (100% resolved = full points)

- **Quality bonus (up to 5 pts)**:
  - Half of average quality score across all instruction files

### Example Output

```
Cross-References & Quality:

  References: 12 found in 3 files
  Unique targets: 8
  Resolved: 10/12 (83%)

  Content Quality:
    CLAUDE.md: 8.2/10 (450 words) [§ ⌘ $ ! ↻8]
    AGENTS.md: 9.5/10 (820 words) [§ ⌘ $ ↻12]

  Quality indicators:
    §=sections  ⌘=paths  $=commands  !=constraints  ↻N=commits

  Bonus: +7.2 points
```

### Improving Your Cross-Reference Score

1. **Link your docs**: Add `[architecture](ARCHITECTURE.md)` links in your CLAUDE.md
2. **Reference other files**: Mention `"CONVENTIONS.md"` or `` `TESTING.md` `` when relevant
3. **Use sections**: Organize with `## Architecture`, `## Conventions`, etc.
4. **Add constraints**: Include clear rules like "Never modify production directly"
5. **Include commands**: Show tool usage like `` `npm run test` ``

## Scoring Algorithm

1. **File Detection**: Scan for patterns at each level (1-8)
2. **Substantiveness Check**: Files must have >100 bytes to count
3. **Coverage Calculation**: Percentage of patterns matched per level
4. **Cross-Reference Detection**: Scan AI instruction files for references to other docs
5. **Quality Evaluation**: Evaluate instruction file quality (sections, commands, constraints)
6. **Level Achievement**:
   - Level 1: Baseline (always achieved)
   - Level 2: At least one AI context file (CLAUDE.md, .cursorrules, etc.)
   - Level 3: Level 2 + >20% coverage of comprehensive context patterns
   - Level 4: Level 3 + >15% coverage of skills & automation patterns
   - Level 5: Level 4 + >10% coverage of multi-agent patterns
   - Level 6-8: Progressive thresholds for fleet infrastructure and orchestration
7. **Overall Score**: Weighted combination of coverage, substantiveness, and cross-reference bonus (up to +10 points)

### Understanding Your Score

⚠️ **Low score but lots of files detected?** This is normal! The tool includes hundreds of possible patterns for comprehensive scanning. Your team likely uses different file names and organization structures.

**How to interpret:**
- **File count matters more than percentage**: If you see 50+ documentation files detected, you have good context engineering regardless of the percentage
- **Focus on what you have**: Look at the actual files detected in verbose mode (`-v`) to see your context engineering artifacts
- **Customize the patterns**: Add your team's specific file names to `config.py` to get more accurate scores
- **The maturity model is a guide**: Level 1 with 100+ files is better than Level 3 with 5 files

## Customizing for Your Organization

The tool is designed to be extended with your team's conventions. Edit `measure_ai_proficiency/config.py` to:

### Add Your File Patterns

```python
# In LEVEL_2_PATTERNS, add your team's documentation files:
file_patterns=[
    # Your custom patterns
    "SYSTEM_DESIGN.md",           # Instead of ARCHITECTURE.md
    "documentation/*.md",          # Instead of docs/
    "eng-docs/*.md",               # Your custom doc folder
    "CODING_STANDARDS.md",         # Instead of CONVENTIONS.md
    # ... existing patterns
]
```

### Adjust Thresholds

If your scoring seems too strict or too lenient, edit `scanner.py`:

```python
# Change coverage thresholds in _calculate_overall_level()
level_2 = level_scores.get(2)
if level_2 and level_2.coverage_percent >= 10:  # Changed from 20
    current_level = 2
```

### Add Custom Directories

```python
directory_patterns=[
    "your-custom-dir",
    "team-docs",
    # ... existing patterns
]
```

### Example: Finance Team Configuration

```python
# Add fintech-specific patterns
"COMPLIANCE.md",
"SECURITY_STANDARDS.md",
"regulatory/",
"audit-docs/",
```

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
