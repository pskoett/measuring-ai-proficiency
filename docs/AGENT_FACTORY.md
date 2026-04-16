# Agent Factory: End-to-End Agentic Workflows

A complete **triage, spec, plan, implement, review, fix, learn** agent factory powered by [GitHub Agentic Workflows (gh-aw)](https://github.github.com/gh-aw/). Ten workflows chain together through GitHub events (labels, PRs, comments). No orchestrator, no DAG. Each agent does one job, hands off via a label swap, and the next agent picks it up. This is choreography, not orchestration.

## The Complete Chain

```
issue opened
  |
  v
issue-triage (auto-labels by type, detects spam)
  |
  v
human adds "needs-spec" label
  |
  v
spec-refiner (structured plan file + implementer recommendation)
  |
  v
/plan (breaks plan into sub-issues)
  |
  v
human assigns sub-issues to Claude / Copilot / Codex
  |
  v
PR opened
  |
  +---> reviewer (plan-aware code review with implementer calibration)
  +---> contribution-checker (CONTRIBUTING.md compliance)
  |
  v
needs-changes? ---> /pr-fix (auto-fix CI failures)
  |
  v
CI failure on main? ---> ci-cleaner (lint, test, compile fix loop)
  |
  v
nightly ---> self-improvement-meta (extract learnings, commit guardrails)
```

State lives in GitHub, not in memory. Each agent starts cold. Every handoff is mediated by a file, a label, or a PR. This makes the chain debuggable: you can inspect the state at any point by looking at the repo.

## Prerequisites

- [GitHub CLI](https://cli.github.com/) installed and authenticated
- [gh-aw extension](https://github.com/github/gh-aw): `gh extension install github/gh-aw`
- A `COPILOT_GITHUB_TOKEN` secret in the repo (for gh-aw agent runtime)
- Copilot cloud agent enabled on the repo (Settings > Copilot > Cloud agent)
- Optional: `DX_MCP_TOKEN` secret if using DX Data Cloud integration in the reviewer

## Quick Start: Your First Run

### Step 1: Open an Issue

Create a new issue describing a feature, bug fix, or refactor. Keep it concrete: what should change, why, and any constraints you know about.

The `issue-triage` workflow fires automatically on new issues. It reads the content, selects appropriate labels (bug, enhancement, question, documentation), detects spam, and posts analysis notes with debugging strategies and context from similar issues.

### Step 2: Label for Spec Refinement

After triage, add the `needs-spec` label to start the factory chain.

The `spec-refiner` workflow triggers. It reads the issue, runs the `plan-interview` skill, and produces:
- A plan file at `docs/plans/plan-NNN-<slug>.md` (opened as a PR)
- A recommended implementer (Claude Opus 4.6, Claude Sonnet 4.6, Copilot, or Codex)
- A label swap: `needs-spec` removed, `needs-plan` added

If the agent cannot answer something from context alone, it marks the gap with **NEEDS HUMAN INPUT** and adds the `blocked-on-human` label. Add a comment with the missing context, remove the label, and re-trigger.

### Step 3: Review and Approve the Plan

Read the plan PR. Check the success criteria, the implementation checklist, and the recommended implementer. If it looks right, merge it.

The `needs-plan` label triggers the `/plan` workflow, which breaks the plan into sub-issues labeled `ready-for-implementation`.

### Step 4: Assign an Implementer

Open each sub-issue on github.com. Go to the Agents tab and assign it to the recommended agent:

| Implementer | When to use |
|-------------|-------------|
| **Claude Opus 4.6** | Multi-file refactors, high blast radius, 6+ checklist items |
| **Claude Sonnet 4.6** | Single-component features, medium complexity |
| **Copilot** | Trivial fixes, dependency bumps, config changes |
| **Codex GPT-5.4** | A/B comparison, different reasoning style |

The agent opens a PR with its implementation.

### Step 5: Automated Review

Two workflows trigger on the new PR:

**Reviewer** checks the PR against the plan file:
1. Finds the plan and checks every success criterion: Met, Partial, Missed, or Drifted
2. Detects the implementer and applies calibration:
   - Claude PRs: checked for scope drift (tends to over-implement)
   - Copilot PRs: checked for test coverage gaps (tends to under-test)
   - Codex PRs: checked for correctness on unusual control flow
   - Human PRs: standard rigor
3. Pulls team baseline from DX Data Cloud (if configured) for context
4. Posts a structured review comment with a verdict: `ai-reviewed`, `needs-changes`, or `fast-track`

**Contribution checker** evaluates the PR against `docs/CONTRIBUTING.md`: on-topic, focused, has tests, has description, skills synced.

### Step 6: Fix Loop

If the reviewer labels the PR `needs-changes`, comment `/pr-fix` to trigger the automated fix workflow. It analyzes failing CI checks, identifies root causes from error logs, implements fixes, and pushes corrections to the PR branch.

If CI fails on `main` after a merge, the `ci-cleaner` workflow triggers automatically. It runs `ruff check --fix`, `pytest`, and `gh aw compile` in sequence, then opens a PR with the fixes. It includes a mandatory exit protocol (always produces a PR or noop) and a file-count guard (refuses to create PRs with 50+ changed files).

### Step 7: The Outer Loop (Nightly)

`self-improvement-meta` runs every night around 2am. It:

1. Reads the last 24 hours of workflow run logs
2. Extracts failure patterns and categorizes them (prompt, tool, context, data)
3. Deduplicates against existing entries in `.learnings/LEARNINGS.md`
4. Opens a PR that adds prevention rules to `AGENTS.md` or the relevant workflow file

When you merge that PR, the next run of the affected agent reads the updated instructions. The factory gets smarter every day. If there are no failures, it calls noop. Silence is the correct signal when the factory is healthy.

## Controlling the Chain

| Action | How |
|--------|-----|
| **Pause any step** | Add the `human-review` label. All agents check for it and call noop. |
| **Skip spec-refinement** | Label the issue `needs-plan` directly instead of `needs-spec` |
| **Skip automated review** | Label the PR `human-review` and review it yourself |
| **Trigger manually** | Every workflow has `workflow_dispatch` enabled. Run from the Actions tab. |
| **Fix a failing PR** | Comment `/pr-fix` on the PR |
| **Break a plan into tasks** | Comment `/plan` on the issue |
| **Fast-forward simple changes** | For trivial fixes, skip the whole chain: just open a PR directly |

## All Workflows

### Factory Chain (custom, skill-backed)

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| [`spec-refiner.md`](../.github/workflows/spec-refiner.md) | Issue labeled `needs-spec` | Structured plan file from issue context using plan-interview skill |
| [`reviewer.md`](../.github/workflows/reviewer.md) | PR opened / updated | Plan-aware code review with implementer calibration |
| [`self-improvement-meta.md`](../.github/workflows/self-improvement-meta.md) | Nightly (~2am) | Extract learnings from failures, commit prevention rules |
| [`ci-cleaner.md`](../.github/workflows/ci-cleaner.md) | CI failure on main | Auto-fix lint, test, and compilation issues |
| [`contribution-checker.md`](../.github/workflows/contribution-checker.md) | PR opened / updated | Evaluate PR against CONTRIBUTING.md guidelines |

These are thin adapter shells. The actual agent logic lives in skills in `.claude/skills/`.

### Support Workflows (from githubnext/agentics)

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| [`issue-triage.md`](../.github/workflows/issue-triage.md) | Issue opened / reopened | Label, categorize, detect spam, provide analysis notes |
| [`plan.md`](../.github/workflows/plan.md) | `/plan` slash command | Break plan into sub-issues labeled `ready-for-implementation` |
| [`pr-fix.md`](../.github/workflows/pr-fix.md) | `/pr-fix` slash command | Analyze failing CI, implement fixes, push to PR branch |

Installed via `gh aw add githubnext/agentics/<name>`. These are general-purpose and work out of the box.

### Project-Specific Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| [`ai-proficiency-pr-review.md`](../.github/workflows/ai-proficiency-pr-review.md) | PR opened / `/assess-proficiency` | AI proficiency score on every PR |
| [`ai-proficiency-weekly-report.md`](../.github/workflows/ai-proficiency-weekly-report.md) | Weekly (Monday 9am UTC) | Track proficiency trends over time |

## Skills Used by the Factory

| Skill | Used by | Purpose |
|-------|---------|---------|
| [`plan-interview`](../.claude/skills/plan-interview/SKILL.md) | spec-refiner | Structured requirements interview before planning |
| [`self-improvement`](../.claude/skills/self-improvement/SKILL.md) | self-improvement-meta | Learning capture, categorization, and promotion |
| [`dx-data-navigator`](../.claude/skills/dx-data-navigator/SKILL.md) | reviewer | DORA metrics from DX Data Cloud (optional) |
| [`intent-framed-agent`](../.claude/skills/intent-framed-agent/SKILL.md) | reviewer | Scope drift detection against plan intent |
| [`context-surfing`](../.claude/skills/context-surfing/SKILL.md) | (available) | Context window health monitoring |

Skills live in `.claude/skills/` and work identically in Claude Code, Codex CLI, and gh-aw. Update a skill once, every consumer gets the fix. The gh-aw workflows read skill files at runtime, not at compile time.

## Label Reference

| Label | Meaning | Set by |
|-------|---------|--------|
| `needs-spec` | Issue needs a structured plan file | Human |
| `needs-plan` | Spec is ready, /plan creates sub-issues | spec-refiner |
| `blocked-on-human` | Agent needs human input before proceeding | spec-refiner |
| `spec-refined` | Spec refinement is complete | spec-refiner |
| `ready-for-implementation` | Sub-issue ready for a coding agent | /plan |
| `ai-reviewed` | PR passed automated review, ready for human review | reviewer |
| `needs-changes` | PR has critical findings or spec drift | reviewer |
| `fast-track` | Small, well-tested, matches plan, zero findings | reviewer |
| `spec-drift` | PR does things the plan did not ask for | reviewer |
| `human-review` | Emergency stop: all agents call noop | Human |
| `self-improvement` | PR was created by the nightly learning loop | self-improvement-meta |
| `ci-fix` | PR was created by the CI cleaner | ci-cleaner |
| `plan-file` | PR contains a plan file | spec-refiner |

## Implementer Routing

The full routing rules live in `AGENTS.md` under "Agent routing guidelines". Summary:

- **Claude Opus 4.6**: complex, multi-file, architecturally risky. More than three modules, high blast radius, non-trivial rollback.
- **Claude Sonnet 4.6**: straightforward single-component features. Clear scope, existing patterns, medium blast radius.
- **Copilot cloud agent**: trivial or highly constrained. Dependency bumps, one-line fixes, config changes.
- **Codex GPT-5.4**: opportunistic. Different reasoning style as a sanity check, A/B data on agent quality.

The spec-refiner recommends. The human decides. The reviewer calibrates based on who actually produced the code.

## Debugging

```bash
# Check workflow status
gh aw status

# View logs for a specific workflow
gh aw logs spec-refiner

# Audit a failed run
gh aw audit <run-id>

# Recompile after editing a workflow
gh aw compile <workflow-name>

# Recompile all workflows
gh aw compile

# Remove orphaned lock files
gh aw compile --purge
```

## Architecture

See [`chain.md`](chain.md) for the full layered architecture diagram and the design rationale for choreography over orchestration.
