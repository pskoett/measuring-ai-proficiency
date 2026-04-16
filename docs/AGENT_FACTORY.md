# Agent Factory: End-to-End Agentic Workflows

A complete **triage, spec, plan, implement, review, fix, learn** agent factory powered by [GitHub Agentic Workflows (gh-aw)](https://github.github.com/gh-aw/). Fourteen workflows chain together through GitHub events (labels, PRs, comments). No orchestrator, no DAG. Each workflow does one job, hands off via a label swap, and the next workflow picks it up. This is choreography, not orchestration.

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
PR labeled needs-rebase? ---> conflict-resolver (merge origin/main; push on clean merge, hand off on conflict)
  |
  v
CI failure on main? ---> ci-cleaner (lint, test, compile fix loop)
  |
  v
nightly ---> self-improvement-meta (extract learnings, commit guardrails)
```

State lives in GitHub, not in memory. Each agent starts cold. Every handoff is mediated by a file, a label, or a PR. This makes the chain debuggable: you can inspect the state at any point by looking at the repo.

## Prerequisites

### Local tooling

- [GitHub CLI](https://cli.github.com/) installed and authenticated (`gh auth login`)
- [gh-aw extension](https://github.com/github/gh-aw): `gh extension install github/gh-aw`
- Git 2.40+ (required by gh-aw for sparse checkouts)

### Repository settings

Apply these in **Settings** on the repo hosting the factory. Skipping any of these is the most common cause of the factory stalling between steps.

| Setting | Path | Value | Why |
|---------|------|-------|-----|
| Workflow permissions | Settings > Actions > General > Workflow permissions | **Read and write permissions** | Workflows need write access to push fixes, open PRs, move labels |
| Allow PR creation | Same page | **Allow GitHub Actions to create and approve pull requests** (checked) | `/pr-fix`, `ci-cleaner`, `self-improvement-meta` all open PRs |
| Outside contributor approval | Settings > Actions > General > Approval for outside collaborators | **Require approval for first-time contributors who are new to GitHub** | Default is stricter and blocks Copilot PRs behind a manual approval click |
| Copilot cloud agent | Settings > Copilot > Coding agent | **Enabled** | Required for `impl:copilot` sub-issue assignment |
| Copilot code review | Settings > Copilot > Code review | **Enabled for this repo** | Lets the Copilot SWE agent annotate PRs inline |
| Actions permissions | Settings > Actions > General > Actions permissions | **Allow all actions and reusable workflows** | Some factory workflows pull from `githubnext/agentics` and `github/gh-aw-actions` |

### Required secrets

Add these under **Settings > Secrets and variables > Actions**. `GITHUB_TOKEN` is provided by GitHub automatically and does not need to be created.

| Secret | Required by | How to get it |
|--------|-------------|---------------|
| `COPILOT_GITHUB_TOKEN` | Every custom gh-aw workflow (agent runtime auth) | Personal access token with `copilot` scope, or a fine-grained token with Copilot access |
| `GH_AW_GITHUB_TOKEN` | gh-aw runtime (fallback auth for checkout, label writes) | Same or broader PAT than `COPILOT_GITHUB_TOKEN`; can alias the same token |
| `GH_AW_GITHUB_MCP_SERVER_TOKEN` | github-mcp-server container inside each workflow | PAT with `repo`, `read:org`, `issues`, `pull_requests` scopes |
| `GH_AW_AGENT_TOKEN` | `implementer-dispatcher` when assigning to agents | PAT allowed to assign issues to the Copilot agent user |
| `GH_AW_CI_TRIGGER_TOKEN` | `ci-cleaner`, `simplify-and-harden-ci` (bypasses workflow-triggering-workflow restriction) | PAT scoped to `actions: write` on this repo |
| `ANTHROPIC_API_KEY` | **Optional** - only if you enable `ai-proficiency-claude.yml` | Get from console.anthropic.com; skip if you stick to the Copilot-powered `ai-proficiency-pr-review` |

You can reuse the same PAT across several of these if it has the union of scopes. Keep them separate if you want to rotate or revoke them independently.

### Required labels

The factory is choreographed through labels. Create these once in **Issues > Labels** or run `scripts/setup-factory-labels.sh` (if present).

| Label | Purpose |
|-------|---------|
| `needs-spec`, `needs-plan`, `spec-refined` | Spec refinement flow |
| `blocked-on-human` | Agent needs human input before proceeding |
| `ready-for-implementation`, `assigned-to-agent` | Implementation dispatch flow |
| `impl:claude-opus`, `impl:claude-sonnet`, `impl:copilot`, `impl:codex` | Implementer routing |
| `ai-reviewed`, `needs-changes`, `fast-track`, `spec-drift` | Reviewer verdicts |
| `human-review` | Emergency stop: all agents call noop |
| `needs-rebase` | PR branch needs a merge from main; triggers conflict-resolver |
| `self-improvement`, `ci-fix`, `plan-file` | Provenance on factory-generated PRs |
| `workflow-health` | Tracking issues for data-layer failures |
| `automation`, `low-risk` | Applied to routine factory PRs |
| `ai-generated` | Applied to sub-issues created by `/plan` |
| `pr-fix` | Applied to commits pushed by `/pr-fix` |
| `task` | Applied to sub-issues created by `/plan` |

Without these labels, workflows that try to `add-labels: allowed: [...]` will fail their safe-output validation.

### Installed GitHub Apps

- **GitHub Copilot** (coding agent + code review) - required for `impl:copilot` routing and inline review annotations
- **`githubnext/agentics`** workflows - installed via `gh aw add githubnext/agentics/<name>` (pulls `/plan`, `/pr-fix`, `issue-triage`)

### First-run checklist

- [ ] All local tooling installed and `gh auth status` clean
- [ ] Repository settings applied (workflow permissions, approval, Copilot)
- [ ] All required secrets present in Actions secrets (not environment or Dependabot)
- [ ] All required labels created
- [ ] `gh aw compile` run once locally so every `.md` workflow has a matching `.lock.yml`
- [ ] Test issue opened and labeled `needs-spec` to verify `spec-refiner` fires


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

Merge the plan PR. The plan PR references the source issue with a non-closing link (e.g. `Refs #NN`), so merging it does not close the source issue. The source issue stays open as the tracking anchor through the planning and implementation window. It should only be closed after all implementation sub-issues are resolved and the actual fix ships.

The `needs-plan` label triggers the `/plan` workflow, which breaks the plan into sub-issues labeled `ready-for-implementation`.

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
| [`conflict-resolver.md`](../.github/workflows/conflict-resolver.md) | PR labeled `needs-rebase` | Merge `origin/main` into PR branch; push on clean merge, hand off on conflict |
| [`self-improvement-meta.md`](../.github/workflows/self-improvement-meta.md) | Nightly (~2am) | Extract learnings from failures, commit prevention rules |

| [`contribution-checker.md`](../.github/workflows/contribution-checker.md) | PR opened / updated | Evaluate PR against CONTRIBUTING.md guidelines |
| [`simplify-and-harden-ci.md`](../.github/workflows/simplify-and-harden-ci.md) | PR opened / updated | Scan changed files for simplicity and security issues |
| [`learning-aggregator-ci.md`](../.github/workflows/learning-aggregator-ci.md) | Weekly (Monday) | Aggregate learnings, rank promotion candidates, create gap report |
| [`eval-creator-ci.md`](../.github/workflows/eval-creator-ci.md) | PR opened / updated | Run regression checks against promoted learnings |

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
| [`ai-proficiency-pr-review.md`](../.github/workflows/ai-proficiency-pr-review.md) | `/assess-proficiency` comment or manual dispatch | AI proficiency score (on-demand only, no auto-trigger) |
| [`ai-proficiency-weekly-report.md`](../.github/workflows/ai-proficiency-weekly-report.md) | Weekly (Monday 9am UTC) | Track proficiency trends over time |
| [`simplify-and-harden-ci.md`](../.github/workflows/simplify-and-harden-ci.md) | PR opened / updated | Post-completion quality and security sweep |
| [`learning-aggregator-ci.md`](../.github/workflows/learning-aggregator-ci.md) | Weekly (Monday) | Cross-session pattern detection and promotion ranking |
| [`eval-creator-ci.md`](../.github/workflows/eval-creator-ci.md) | PR opened / updated | Create regression test cases from promoted learnings |

## Skills Used by the Factory

| Skill | Used by | Purpose |
|-------|---------|---------|
| [`plan-interview`](../.claude/skills/plan-interview/SKILL.md) | spec-refiner | Structured requirements interview before planning |
| `self-improvement` | self-improvement-meta | Learning capture, categorization, and promotion (skill instructions embedded in the workflow; no standalone SKILL.md file) |
| [`intent-framed-agent`](../.claude/skills/intent-framed-agent/SKILL.md) | reviewer | Scope drift detection against plan intent |
| [`simplify-and-harden`](../.claude/skills/simplify-and-harden/SKILL.md) | simplify-and-harden-ci | Post-completion quality and security sweep |
| [`learning-aggregator`](../.claude/skills/learning-aggregator/SKILL.md) | learning-aggregator-ci | Cross-session pattern detection and promotion ranking |
| [`eval-creator`](../.claude/skills/eval-creator/SKILL.md) | eval-creator-ci | Create regression test cases from promoted learnings |
| [`measure-ai-proficiency`](../.claude/skills/measure-ai-proficiency/SKILL.md) | ai-proficiency-pr-review, ai-proficiency-weekly-report | Run AI proficiency assessments |
| [`context-surfing`](../.claude/skills/context-surfing/SKILL.md) | (available) | Context window health monitoring |
| [`verify-gate`](../.claude/skills/verify-gate/SKILL.md) | (available) | Machine verification gate before quality review |
| [`customize-measurement`](../.claude/skills/customize-measurement/SKILL.md) | (available) | Configure measurement for specific repos |
| [`agentic-workflow`](../.claude/skills/agentic-workflow/SKILL.md) | (available) | GitHub agentic workflow creation |
| [`pre-flight-check`](../.claude/skills/pre-flight-check/SKILL.md) | (available) | Session-start scan of relevant learnings and eval status |

Skills live in `.claude/skills/` and work identically in Claude Code, Codex CLI, and gh-aw. Update a skill once, every consumer gets the fix. The gh-aw workflows read skill files at runtime, not at compile time.

## Label Reference

| Label | Meaning | Set by |
|-------|---------|--------|
| `needs-spec` | Issue needs a structured plan file | Human |
| `needs-plan` | Spec is ready, /plan creates sub-issues | spec-refiner |
| `needs-rebase` | PR branch is behind main and needs a merge | Human |
| `blocked-on-human` | Agent needs human input before proceeding | spec-refiner, conflict-resolver (and other workflows) |
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
| `needs-rebase` | PR branch is behind main and needs a merge | Human |
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
