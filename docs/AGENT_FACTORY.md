# Agent Factory: End-to-End Agentic Workflows

A complete **spec, plan, implement, review, learn** agent factory powered by [GitHub Agentic Workflows (gh-aw)](https://github.github.com/gh-aw/). Five specialist agents chain together through GitHub events (labels, PRs, comments). No orchestrator, no DAG. Each agent does one job, hands off via a label swap, and the next agent picks it up.

## How the Chain Works

```
1. Open issue, add label "needs-spec"
       |
       v
2. spec-refiner writes a plan file, recommends an implementer
       |
       v
3. /plan breaks the plan into sub-issues
       |
       v
4. Human assigns sub-issues to Claude / Copilot / Codex
       |
       v
5. reviewer checks the PR against the plan
       |
       v
6. self-improvement-meta (nightly) turns failures into guardrails
```

State between phases lives in GitHub, not in memory. Each agent starts cold. The spec gets written back to the issue body so the planner can read it. The plan sub-issues get labeled so the implementer can find them. The reviewer reads the plan file from disk. Every handoff is mediated by a file, a label, or a PR.

## Prerequisites

- [GitHub CLI](https://cli.github.com/) installed and authenticated
- [gh-aw extension](https://github.com/github/gh-aw): `gh extension install github/gh-aw`
- A `COPILOT_GITHUB_TOKEN` secret in the repo (for gh-aw agent runtime)
- Copilot cloud agent enabled on the repo (Settings > Copilot > Cloud agent)
- Optional: `DX_MCP_TOKEN` secret if using DX Data Cloud integration in the reviewer

## Quick Start: Your First Run

### Step 1: Open an Issue

Create a new issue describing a feature, bug fix, or refactor. Keep it concrete: what should change, why, and any constraints you know about.

Add the `needs-spec` label.

### Step 2: Watch spec-refiner Work

The `spec-refiner` workflow triggers automatically. It reads the issue, runs the `plan-interview` skill against the issue context, and produces:

- A plan file at `docs/plans/plan-NNN-<slug>.md` (opened as a PR)
- A recommended implementer (Claude Opus 4.6, Claude Sonnet 4.6, Copilot, or Codex)
- A label swap: `needs-spec` removed, `needs-plan` added

If the agent cannot answer something from context alone, it marks the gap with **NEEDS HUMAN INPUT** and adds the `blocked-on-human` label instead. Add a comment with the missing context, remove the label, and re-trigger.

### Step 3: Review and Approve the Plan

Read the plan PR. Check the success criteria, the implementation checklist, and the recommended implementer. If it looks right, merge it.

The `needs-plan` label triggers the `/plan` workflow (from [githubnext/agentics](https://github.com/githubnext/agentics)), which breaks the plan into sub-issues labeled `ready-for-implementation`.

### Step 4: Assign an Implementer

Open each sub-issue on github.com. Go to the Agents tab and assign it to the recommended agent. The spec-refiner wrote a recommendation in the plan file based on complexity:

| Implementer | When to use |
|-------------|-------------|
| **Claude Opus 4.6** | Multi-file refactors, high blast radius, 6+ checklist items |
| **Claude Sonnet 4.6** | Single-component features, medium complexity |
| **Copilot** | Trivial fixes, dependency bumps, config changes |
| **Codex GPT-5.4** | A/B comparison, different reasoning style |

The agent opens a PR with its implementation.

### Step 5: Automated Review

The `reviewer` workflow triggers on the new PR. It:

1. **Finds the plan file** and checks every success criterion: Met, Partial, Missed, or Drifted
2. **Detects the implementer** from the PR author and applies calibration:
   - Claude PRs: checked for scope drift (tends to over-implement)
   - Copilot PRs: checked for test coverage gaps (tends to under-test)
   - Codex PRs: checked for correctness on unusual control flow
   - Human PRs: standard rigor
3. **Pulls team baseline** from DX Data Cloud (if configured) for context
4. **Posts a structured review comment** with a verdict: `ai-reviewed`, `needs-changes`, or `fast-track`

If the verdict is `needs-changes`, the `/pr-fix` workflow can auto-fix CI failures. Otherwise, a human does the final review and merges.

### Step 6: The Outer Loop (Nightly)

`self-improvement-meta` runs every night around 2am. It:

1. Reads the last 24 hours of workflow run logs
2. Extracts failure patterns and categorizes them (prompt, tool, context, data)
3. Deduplicates against existing entries in `.learnings/LEARNINGS.md`
4. Opens a PR that adds prevention rules to `AGENTS.md` or the relevant workflow file

When you merge that PR, the next run of the affected agent reads the updated instructions. The factory gets smarter every day.

If there are no failures, it calls noop. Silence is the correct signal when the factory is healthy.

## Controlling the Chain

| Action | How |
|--------|-----|
| **Pause any step** | Add the `human-review` label. All agents check for it and call noop. |
| **Skip spec-refinement** | Label the issue `needs-plan` directly instead of `needs-spec` |
| **Skip automated review** | Label the PR `human-review` and review it yourself |
| **Trigger manually** | Every workflow has `workflow_dispatch` enabled. Run from the Actions tab. |
| **Fast-forward simple changes** | For trivial fixes, skip the whole chain: just open a PR directly |

## The Workflows

| File | Trigger | Purpose |
|------|---------|---------|
| [`spec-refiner.md`](../.github/workflows/spec-refiner.md) | Issue labeled `needs-spec` | Structured plan file from issue context |
| [`plan.md`](../.github/workflows/plan.md) | `/plan` slash command | Break plan into sub-issues with task labels |
| [`reviewer.md`](../.github/workflows/reviewer.md) | PR opened / updated | Plan-aware code review with implementer calibration |
| [`pr-fix.md`](../.github/workflows/pr-fix.md) | `/pr-fix` slash command | Auto-fix failing CI on PR branches |
| [`self-improvement-meta.md`](../.github/workflows/self-improvement-meta.md) | Nightly (~2am) | Extract learnings from failures, commit prevention rules |
| [`issue-triage.md`](../.github/workflows/issue-triage.md) | Issue opened / reopened | Label, categorize, and provide analysis notes |
| [`ci-cleaner.md`](../.github/workflows/ci-cleaner.md) | CI failure on main | Auto-fix lint, test, and compilation issues |
| [`contribution-checker.md`](../.github/workflows/contribution-checker.md) | PR opened / updated | Evaluate PR against CONTRIBUTING.md guidelines |

The factory workflows (`spec-refiner`, `reviewer`, `self-improvement-meta`) are thin adapter shells. The actual agent logic lives in skills. The support workflows (`plan`, `pr-fix`, `issue-triage`) come from the [githubnext/agentics](https://github.com/githubnext/agentics) sample pack.

## Skills Used by the Factory

| Skill | Used by | Purpose |
|-------|---------|---------|
| [`plan-interview`](../.claude/skills/plan-interview/SKILL.md) | spec-refiner | Structured requirements interview |
| [`self-improvement`](../.claude/skills/self-improvement/SKILL.md) | self-improvement-meta | Learning capture and promotion |
| [`dx-data-navigator`](../.claude/skills/dx-data-navigator/SKILL.md) | reviewer | DORA metrics from DX Data Cloud (optional) |
| [`intent-framed-agent`](../.claude/skills/intent-framed-agent/SKILL.md) | reviewer | Scope drift detection |
| [`context-surfing`](../.claude/skills/context-surfing/SKILL.md) | (available) | Context window health monitoring |

Skills live in `.claude/skills/` and work identically in Claude Code, Codex CLI, and gh-aw. Update a skill once, every consumer gets the fix.

## Label Reference

| Label | Meaning | Set by |
|-------|---------|--------|
| `needs-spec` | Issue needs a structured plan file | Human |
| `needs-plan` | Spec is ready, waiting for /plan to create sub-issues | spec-refiner |
| `blocked-on-human` | Agent needs human input before proceeding | spec-refiner |
| `spec-refined` | Spec refinement is complete | spec-refiner |
| `ready-for-implementation` | Sub-issue ready for a coding agent | /plan |
| `ai-reviewed` | PR passed automated review, ready for human review | reviewer |
| `needs-changes` | PR has critical findings or spec drift | reviewer |
| `fast-track` | Small, well-tested, matches plan, zero findings | reviewer |
| `spec-drift` | PR does things the plan did not ask for | reviewer |
| `human-review` | Emergency stop: all agents call noop | Human |
| `self-improvement` | PR was created by the nightly learning loop | self-improvement-meta |
| `plan-file` | PR contains a plan file | spec-refiner |

## Installing Additional Workflows

The factory works best with two complementary workflows from the [githubnext/agentics](https://github.com/githubnext/agentics) sample pack:

```bash
# Break plans into sub-issues
gh aw add githubnext/agentics/plan

# Auto-fix CI failures on PRs
gh aw add githubnext/agentics/pr-fix

# Compile and commit
gh aw compile
git add .github/workflows/
git commit -m "Add plan and pr-fix workflows"
```

## Implementer Routing Guidelines

The routing rules live in `AGENTS.md` under "Agent routing guidelines". The short version:

**Claude Opus 4.6**: complex, multi-file, architecturally risky work. More than three modules, high blast radius, non-trivial rollback, six or more checklist items.

**Claude Sonnet 4.6**: straightforward single-component features. Clear scope, existing patterns to follow, medium blast radius.

**Copilot cloud agent**: trivial or highly constrained work. Dependency bumps, one-line fixes, config changes, mechanical edits.

**Codex GPT-5.4**: opportunistic. Different reasoning style as a sanity check, A/B data on agent quality.

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
```

## Architecture

See [`chain.md`](chain.md) for the full architecture diagram, the layered adapter pattern, and the design rationale for choreography over orchestration.
