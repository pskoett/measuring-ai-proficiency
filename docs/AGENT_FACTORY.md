# Agent Factory: End-to-End Agentic Workflows

A complete **triage, spec, plan, implement, review, fix, learn** agent factory powered by [GitHub Agentic Workflows (gh-aw)](https://github.github.com/gh-aw/). Eleven workflows chain together through GitHub events (labels, PRs, comments). No orchestrator, no DAG. Each agent does one job, hands off via a label swap, and the next agent picks it up. This is choreography, not orchestration.

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
spec-refiner (plan file + implementer label on issue)
  |
  v
human reviews plan PR, optionally swaps implementer label  <-- ONE decision
  |
  v
/plan (breaks plan into sub-issues)
  |
  v
implementer-dispatcher (auto-assigns sub-issues from parent label)
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


## Quick Start: Your First Run

### Step 1: Open an Issue

Create a new issue describing a feature, bug fix, or refactor. Keep it concrete: what should change, why, and any constraints you know about.

The `issue-triage` workflow fires automatically on new issues. It reads the content, selects appropriate labels (bug, enhancement, question, documentation), detects spam, and posts analysis notes with debugging strategies and context from similar issues.

### Step 2: Label for Spec Refinement

After triage, add the `needs-spec` label to start the factory chain.

The `spec-refiner` workflow triggers. It reads the issue, runs the `plan-interview` skill, and produces:
- A plan file at `docs/plans/plan-NNN-<slug>.md` (opened as a PR)
- A recommended implementer (Claude Opus 4.6, Claude Sonnet 4.6, Copilot, or Codex)
- An implementer label on the issue (`impl:claude-opus`, `impl:claude-sonnet`, `impl:copilot`, or `impl:codex`)
- A label swap: `needs-spec` removed, `needs-plan` added

If the agent cannot answer something from context alone, it marks the gap with **NEEDS HUMAN INPUT** and adds the `blocked-on-human` label. Add a comment with the missing context, remove the label, and re-trigger.

### Step 3: Review the Plan and Choose an Implementer

Read the plan PR. Check the success criteria, the implementation checklist, and the recommended implementer.

The spec-refiner already added an implementer label (e.g., `impl:claude-opus`) to the issue based on its complexity assessment. If you disagree with the recommendation, swap the label before proceeding:

| Label | Agent | When to use |
|-------|-------|-------------|
| `impl:claude-opus` | Claude Opus 4.6 | Multi-file refactors, high blast radius, 6+ checklist items |
| `impl:claude-sonnet` | Claude Sonnet 4.6 | Single-component features, medium complexity |
| `impl:copilot` | Copilot | Trivial fixes, dependency bumps, config changes |
| `impl:codex` | Codex GPT-5.4 | A/B comparison, different reasoning style |

Merge the plan PR. The `needs-plan` label triggers the `/plan` workflow, which breaks the plan into sub-issues labeled `ready-for-implementation`.

### Step 4: Auto-Assignment (No Manual Work)

The `implementer-dispatcher` workflow triggers automatically when sub-issues receive the `ready-for-implementation` label. It reads the implementer label from the parent issue and assigns each sub-issue to the chosen agent via `assign-to-agent`.

You assigned once at Step 3. Every sub-issue inherits that choice. No manual assignment needed.

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
3. Posts a structured review comment with a verdict: `ai-reviewed`, `needs-changes`, or `fast-track`

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
| [`implementer-dispatcher.md`](../.github/workflows/implementer-dispatcher.md) | Sub-issue labeled `ready-for-implementation` | Auto-assign to agent based on parent issue's implementer label |
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
| `self-improvement` | self-improvement-meta | Learning capture, categorization, and promotion |
| [`intent-framed-agent`](../.claude/skills/intent-framed-agent/SKILL.md) | reviewer | Scope drift detection against plan intent |
| [`context-surfing`](../.claude/skills/context-surfing/SKILL.md) | (available) | Context window health monitoring |
| [`simplify-and-harden`](../.claude/skills/simplify-and-harden/SKILL.md) | (available) | Post-completion quality and security sweep |
| [`verify-gate`](../.claude/skills/verify-gate/SKILL.md) | (available) | Machine verification gate before quality review |
| [`eval-creator`](../.claude/skills/eval-creator/SKILL.md) | eval-creator-ci | Regression test cases from promoted learnings |
| [`learning-aggregator`](../.claude/skills/learning-aggregator/SKILL.md) | learning-aggregator-ci | Cross-session pattern detection and promotion ranking |
| [`pre-flight-check`](../.claude/skills/pre-flight-check/SKILL.md) | (available) | Session-start scan of relevant learnings and eval status |
| [`measure-ai-proficiency`](../.claude/skills/measure-ai-proficiency/SKILL.md) | ai-proficiency-pr-review | Run AI proficiency assessments |
| [`customize-measurement`](../.claude/skills/customize-measurement/SKILL.md) | (available) | Configure measurement for specific repos |
| [`agentic-workflow`](../.claude/skills/agentic-workflow/SKILL.md) | (available) | GitHub agentic workflow creation |

Skills live in `.claude/skills/` and work identically in Claude Code, Codex CLI, and gh-aw. Update a skill once, every consumer gets the fix. The gh-aw workflows read skill files at runtime, not at compile time.

## Label Reference

| Label | Meaning | Set by |
|-------|---------|--------|
| `needs-spec` | Issue needs a structured plan file | Human |
| `needs-plan` | Spec is ready, /plan creates sub-issues | spec-refiner |
| `blocked-on-human` | Agent needs human input before proceeding | spec-refiner |
| `spec-refined` | Spec refinement is complete | spec-refiner |
| `ready-for-implementation` | Sub-issue ready for a coding agent | /plan |
| `impl:claude-opus` | Assign to Claude Opus 4.6 | spec-refiner (or human) |
| `impl:claude-sonnet` | Assign to Claude Sonnet 4.6 | spec-refiner (or human) |
| `impl:copilot` | Assign to Copilot cloud agent | spec-refiner (or human) |
| `impl:codex` | Assign to Codex GPT-5.4 | spec-refiner (or human) |
| `assigned-to-agent` | Sub-issue has been dispatched | implementer-dispatcher |
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
