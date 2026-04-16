# Agents

This document defines agent roles, behavioral guidelines, and factory chain context for AI assistants working on the measure-ai-proficiency project.

## Agent Roles

### Code Implementer

**Purpose:** Implement features, fix bugs, and maintain the codebase.

**Key behaviors:**
- Follow pure Python conventions (no external dependencies for core functionality)
- Use type hints on all functions and methods
- Use dataclasses for data structures
- Maintain backwards compatibility with Python 3.9+
- Run `pytest tests/ -v` before committing changes

**Files to modify:**
- `measure_ai_proficiency/scanner.py` - Core scanning logic
- `measure_ai_proficiency/config.py` - Level definitions and patterns
- `measure_ai_proficiency/reporter.py` - Output formatting
- `measure_ai_proficiency/repo_config.py` - Configuration handling
- `measure_ai_proficiency/github_scanner.py` - GitHub CLI integration

### Documentation Writer

**Purpose:** Keep documentation accurate and helpful.

**Key behaviors:**
- Update README.md when features change
- Keep docs/CUSTOMIZATION.md current with config options
- Sync skill files across all locations when updating:
  - `.claude/skills/*/SKILL.md`
  - `.github/skills/*/SKILL.md`
  - `skill-template/*/SKILL.md`
- Update `.ai-proficiency.yaml.example` when adding config options

**Constraints:**
- Never add features to docs that don't exist in code
- Always include examples with documentation
- Keep the example output in README.md current

### Skill Developer

**Purpose:** Create and maintain agent skills for this tool.

**Key behaviors:**
- Skills should be self-contained and follow the Agent Skills standard
- Include clear triggers and workflow steps
- Test skills work with both Claude Code and GitHub Copilot
- Sync skills to all three locations after changes

**Available skills:**
- `measure-ai-proficiency` - Run assessments
- `customize-measurement` - Configure for specific repos
- `plan-interview` - Interview-based planning
- `agentic-workflow` - GitHub agentic workflow creation
- `self-improvement` - Learning capture and prevention rule promotion
- `dx-data-navigator` - DX Data Cloud queries for DORA metrics
- `intent-framed-agent` - Intent contract to prevent scope drift
- `context-surfing` - Context window health monitoring

### Reviewer

**Purpose:** Review changes for quality and consistency.

**Key behaviors:**
- Verify type hints are present
- Check for backwards compatibility
- Ensure tests pass
- Validate documentation is updated
- Check skill files are synced across locations

## Behavioral Guidelines

### All Agents

1. **Test before committing:** Always run `pytest tests/ -v`
2. **Keep skills synced:** Changes to skills must be copied to all three locations
3. **Update version:** Bump version in `pyproject.toml` for releases
4. **Document config options:** New options go in:
   - `repo_config.py` (implementation)
   - `docs/CUSTOMIZATION.md` (documentation)
   - `.ai-proficiency.yaml.example` (example)
   - Skills that use the option

### Exit Codes

Maintain these exit codes:
- `0` - Success
- `1` - No repositories found
- `2` - All repositories at Level 1 (no AI context)

### Scoring System

When modifying scoring:
- Minimum scores per level: L2=15, L3=30, L4=45, L5=55, L6=70, L7=85, L8=95
- Validation penalty: max -4 points
- Cross-reference bonus: max +5 points
- Quality bonus: max +5 points

### Pattern Detection

When adding new patterns:
- Add to appropriate level in `config.py`
- Consider tool-specific filtering (Claude, Copilot, Cursor, Codex)
- Update KNOWN_TARGETS if it's an instruction file
- Add to INSTRUCTION_FILES if it should be scanned for cross-references

## Handoffs

### Implementation to Documentation
After implementing a feature, hand off to documentation:
- Describe what was added/changed
- Note any new config options
- List affected files

### Documentation to Skills
After updating documentation, update skills:
- measure-ai-proficiency skill for assessment features
- customize-measurement skill for config options

---

## Agent Factory: Shared Context

The sections below are read by every agentic workflow in the factory chain. The factory consists of 10 workflows organized in three tiers:

**Factory chain** (custom, skill-backed): `spec-refiner`, `reviewer`, `self-improvement-meta`, `ci-cleaner`, `contribution-checker`
**Support workflows** (from githubnext/agentics): `issue-triage`, `plan`, `pr-fix`
**Project-specific**: `ai-proficiency-pr-review`, `ai-proficiency-weekly-report`

See `docs/AGENT_FACTORY.md` for the full guide with step-by-step usage instructions, label reference, and debugging commands.

### Core principles

1. **Move forward, fail fast, fail forward.** Do not stall on ambiguity. Make the best decision with the information available, document the assumption, and keep moving.
2. **Knowledge is for sharing.** When you learn something non-obvious, write it down in `.learnings/` so the next agent does not repeat the mistake.
3. **Skills are the new software.** Treat instructions as code. Version them, review them, improve them over time.
4. **Harness engineering is the differentiator.** The prompt is never the bottleneck. The structure around the prompt is.

### Skill discovery

This repository contains reusable agent skills in `.claude/skills/`. Every skill follows the [Agent Skills specification](https://agentskills.io/specification):

```
.claude/skills/
  skill-name/
    SKILL.md         # Instructions + YAML frontmatter
    scripts/         # Optional executable code
    references/      # Optional reference material loaded on demand
    assets/          # Optional templates and data files
```

When a workflow tells you to use a skill, read `.claude/skills/<skill-name>/SKILL.md` in full and follow its process. If the skill references additional files in `references/` or `assets/`, read those on demand as the skill instructs.

Currently available skills:
- `.claude/skills/plan-interview/`: structured requirements interview before planning
- `.claude/skills/self-improvement/`: learning capture and prevention rule promotion
- `.claude/skills/dx-data-navigator/`: DX Data Cloud queries for DORA metrics and PR analytics
- `.claude/skills/intent-framed-agent/`: explicit intent contract to prevent scope drift
- `.claude/skills/context-surfing/`: context window health monitoring with clean exits
- `.claude/skills/measure-ai-proficiency/`: run AI proficiency assessments
- `.claude/skills/customize-measurement/`: configure measurement for specific repos
- `.claude/skills/agentic-workflow/`: GitHub agentic workflow creation

### Adapting skills for single-shot gh-aw runs

The skills in `.claude/skills/` were originally written for live agent sessions with Claude Code, Codex CLI, or GitHub Copilot CLI. gh-aw runs are single-shot and ephemeral. When a skill assumes interactivity or cross-turn state that gh-aw cannot provide, follow these rules:

1. **Interview-style skills**: When a skill expects to ask the user questions, simulate the interview by answering from available context (issue body, linked PRs, repo files). Mark any answer you cannot give with confidence using `**NEEDS HUMAN INPUT**` and a specific question, then route to `blocked-on-human` via labels.
2. **Hook-based skills**: gh-aw has no PostToolUse or UserPromptSubmit hooks. When a skill expects hook activation, apply its logic at natural phase boundaries in your run (after planning, after major tool calls, before exit).
3. **Session-state skills**: Skills that monitor context window health or track state across turns cannot observe gh-aw runs directly. Apply their discipline as self-checks: read the skill, enumerate its checks, and run each one manually before committing output.
4. **Script-bundled skills**: If a skill has scripts in `scripts/`, those scripts must be explicitly allowlisted in the workflow frontmatter's `bash: allowed:` block. Instruction-only skills work everywhere with no configuration.

### Writing style for all agent-authored content

These rules apply to every comment, issue body, PR description, and commit message you produce.

- Never use em-dashes or double dashes. Use commas, colons, or periods.
- No "most teams" generalizations.
- No throat-clearing opening sentences. Lead with the answer.
- Short sentences. Strong declarative statements.
- If you quote data, link to the source.

### Spec and plan files

Plans live in `docs/plans/plan-NNN-<slug>.md` where NNN is a three-digit zero-padded sequence. The format is defined in `.claude/skills/plan-interview/SKILL.md`. Downstream agents use these files as the source of truth for implementation and review.

### Learnings

Learnings live in `.learnings/LEARNINGS.md` and follow this format:

```
## [LRN-NNN] Short title

**Status**: pending | promoted_to_skill | regressed
**Priority**: low | medium | high
**Area**: backend | frontend | infra | ci | docs | process
**Pattern-Key**: <stable-dedupe-key>
**Discovered**: YYYY-MM-DD via <workflow-run-url>

### What went wrong
[One paragraph]

### Root cause
[One paragraph]

### Prevention rule
[One short, checkable rule written in the imperative]

### See also
- LRN-XXX
```

Never log secrets, tokens, private keys, or full source files. Prefer short summaries over raw output. The full specification of this format lives in `.claude/skills/self-improvement/SKILL.md`.

#### Promotion targets

When a learning is promoted (high priority, recurrent pattern, broadly applicable), it must be written to **all three harness files** so every agent runtime benefits:

1. **`AGENTS.md`**: read by gh-aw workflows and GitHub Copilot agents at run start
2. **`.github/copilot-instructions.md`**: read by GitHub Copilot in IDE and cloud coding agent
3. **`CLAUDE.md`**: read by Claude Code at session start

If the rule is workflow-specific (only applies to one workflow), also add it to that workflow's `.md` file body. Generic rules go in the harness files only.

### Agent routing guidelines

As of April 2026, GitHub offers three cloud coding agents, all bundled with the Copilot subscription: Copilot cloud agent, Claude (Sonnet 4.5/4.6, Opus 4.5/4.6), and Codex (GPT-5.2/5.3/5.4-Codex). Model selection happens when a task is kicked off on github.com. For workflows in this pack, `spec-refiner` recommends an implementer in the plan file, and a human confirms the assignment via the web UI.

Use these rules when recommending or choosing an implementer:

**Claude Opus 4.6**: default for complex, multi-file, or architecturally risky work
- Multi-file refactors touching more than three modules
- Plan files with `Blast radius: high`
- Anything with a non-trivial rollback path
- Plan files with more than six items in the implementation checklist
- Work that needs precise spec adherence because drift would matter

**Claude Sonnet 4.6**: default for straightforward single-component features
- Single-module feature additions with clear scope
- New API endpoints with existing patterns to follow
- Plan files with `Blast radius: medium`
- Bug fixes that require moderate investigation
- Anything where Opus would be overkill but you still want Claude's reasoning

**Copilot cloud agent**: default for trivial or highly-constrained work
- Dependency version bumps
- Obvious one-line fixes where the fix is already in the issue body
- Config file updates
- Repetitive mechanical changes across many files
- Plan files with `Blast radius: low` and a checklist under three items

**Codex (GPT-5.4)**: opportunistic use for specific strengths
- Tasks that benefit from a different reasoning style as a sanity check on Claude
- When the team wants A/B data on agent quality

#### Why Claude is the default for non-trivial work

The skills in `.claude/skills/` were originally designed for Claude Code. Running them on their native runtime gives better fidelity than any translation layer. The `plan-interview` structure, the intent framing discipline, the simplify-and-harden pass: all of it was tuned against Claude's reasoning patterns.

#### How the recommendation gets made

`spec-refiner` adds a `## Recommended implementer` section to every plan file and adds the corresponding `impl:*` label to the parent issue (e.g., `impl:claude-opus`). The human reviews the plan PR and can swap the label if they disagree. When `/plan` creates sub-issues, the `implementer-dispatcher` workflow reads the `impl:*` label from the parent issue and auto-assigns each sub-issue to the chosen agent. One decision at the plan level, zero manual assignment per sub-issue.

#### A note on gh-aw engine selection

The routing rules above are about the **implementer step** (who writes the code from a sub-issue). The gh-aw engine that runs the workflows in this pack (`spec-refiner`, `reviewer`, `self-improvement-meta`) is a separate choice in each workflow's frontmatter. All workflows here currently use Copilot as the engine because it is bundled with the existing `COPILOT_GITHUB_TOKEN` secret. When gh-aw supports running the Claude engine through the same bundled subscription (expected soon based on the April 2026 changelog), flipping these workflows to `engine: claude` will be a one-line change per workflow.

### Tooling available to agents in this repo

- GitHub toolset (read-only by default, write via safe-outputs only)
- `cache-memory` and `repo-memory` for cross-run state
- `bash: true` for shell commands (ci-cleaner, pr-fix)
- `edit:` for file modifications (ci-cleaner, pr-fix)
- `web-fetch:` for external content (issue-triage, pr-fix)
- DX Data Cloud MCP server (configured per workflow that needs it, optional for PoC). Reviewer agents should use this for context when available.

### Workflow inventory

| Workflow | Trigger | Safe outputs | Skill |
|----------|---------|-------------|-------|
| `spec-refiner` | Issue labeled `needs-spec` | update-issue, add-comment, create-pull-request, add-labels, remove-labels | plan-interview |
| `implementer-dispatcher` | Sub-issue labeled `ready-for-implementation` | assign-to-agent, add-comment, add-labels | (none, reads parent issue labels) |
| `reviewer` | PR opened / updated | add-comment, add-labels | dx-data-navigator, intent-framed-agent |
| `self-improvement-meta` | Nightly (~2am) | create-pull-request, create-issue | self-improvement |
| `ci-cleaner` | CI failure on main | create-pull-request | (none, uses bash/edit directly) |
| `contribution-checker` | PR opened / updated | add-comment | (none, reads CONTRIBUTING.md) |
| `issue-triage` | Issue opened / reopened | add-labels, add-comment | (none, githubnext/agentics) |
| `plan` | `/plan` slash command | create-issue | (none, githubnext/agentics) |
| `pr-fix` | `/pr-fix` slash command | push-to-pull-request-branch, add-comment, create-issue | (none, githubnext/agentics) |
| `ai-proficiency-pr-review` | PR opened / `/assess-proficiency` | add-comment | measure-ai-proficiency |
| `ai-proficiency-weekly-report` | Weekly (Monday 9am) | create-issue | measure-ai-proficiency |

### Human circuit breaker

Any workflow can be halted by adding the `human-review` label to the issue or PR it is operating on. When you see this label, call `noop` immediately and explain what you would have done.
