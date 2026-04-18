# Agent Factory: End-to-End Agentic Workflows

A complete **triage, spec, plan, implement, review, fix, learn** agent factory powered by [GitHub Agentic Workflows (gh-aw)](https://github.github.com/gh-aw/). Workflows chain together through GitHub events (labels, PRs, comments). No orchestrator, no DAG. Each workflow does one job, hands off via a label swap, and the next workflow picks it up. This is choreography, not orchestration.

The source issue is the unit of work end-to-end. A plan PR produces one consolidated checklist on the source issue itself; there is no sub-issue layer.

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
spec-refiner (classifies issue, chooses one of three paths)
  |
  +---> [plan-worthy] plan file PR + impl:copilot + needs-plan
  |       |
  |       v
  |     human reviews plan PR, optionally swaps implementer label  <-- ONE decision
  |       |
  |       v
  |     human merges plan PR
  |       |
  |       v
  |     plan-merged-dispatcher (plain Actions: writes plan checklist onto source issue body,
  |                             transitions needs-plan -> ready-for-implementation)
  |       |
  +---> [direct route] no plan PR; impl:copilot + ready-for-implementation added directly
  |
  v
implementer-dispatcher (auto-assigns the source issue based on its impl:* label)
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

**Blocked path**: if spec-refiner classifies the issue as terminal or blocked (spam, duplicate, missing context), it removes `needs-spec`, adds `blocked-on-human`, and posts a comment. No plan PR, no dispatch. A human resolves.

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
| Outside contributor approval | Settings > Actions > General > Approval for outside collaborators | **Require approval for first-time contributors** (not "...who are new to GitHub") | The "...new to GitHub" option does NOT exempt the Copilot bot; this one does after the first merged Copilot PR |
| Copilot workflow approval | Settings > Copilot > Coding agent > Actions workflow approval | **Off** (recommended) or **On** (belt-and-suspenders) | Separate from the outside-contributor setting above. When **On**, every Copilot PR requires a manual "Approve and run" click before any factory workflow runs. Safe to turn off once `reviewer` + `contribution-checker` + your merge gate are in place. |
| Copilot cloud agent | Settings > Copilot > Coding agent | **Enabled** | Required for `impl:copilot` issue assignment |
| Copilot code review | Settings > Copilot > Code review | **Enabled for this repo** | Lets the Copilot SWE agent annotate PRs inline |
| Actions permissions | Settings > Actions > General > Actions permissions | **Allow all actions and reusable workflows** | Some factory workflows pull from `githubnext/agentics` and `github/gh-aw-actions` |

### Required secrets

Add these under **Settings > Secrets and variables > Actions**. `GITHUB_TOKEN` is provided by GitHub automatically and does not need to be created.

| Secret | Required by | How to get it |
|--------|-------------|---------------|
| `COPILOT_GITHUB_TOKEN` | Every custom gh-aw workflow (agent runtime auth) | Personal access token with `copilot` scope, or a fine-grained token with Copilot access |
| `GH_AW_AGENT_TOKEN` | `implementer-dispatcher` (assigning Copilot) and `plan-merged-dispatcher` (label cascades into `implementer-dispatcher`) | PAT with `issues: write`, `contents: write`, and cascade-capable (i.e. a user/installation PAT, not `GITHUB_TOKEN`) |
| `PROJECTS_PAT` | `sync-factory-state` (writes issue/PR state onto the AI Agent Factory Projects v2 board) | Classic PAT with `repo` + `project` scopes. `GITHUB_TOKEN` cannot be used — Projects v2 only accepts a user PAT. Fine-grained PATs are unreliable for user-owned Projects. |
| `ANTHROPIC_API_KEY` | **Optional** — only if you enable `ai-proficiency-claude.yml` | Get from console.anthropic.com; skip if you stick to the Copilot-powered `ai-proficiency-pr-review` |

You can reuse the same PAT across these if it has the union of scopes. Keep them separate if you want to rotate or revoke them independently.

**Historical note:** earlier versions of this doc listed `GH_AW_GITHUB_TOKEN`, `GH_AW_GITHUB_MCP_SERVER_TOKEN`, and `GH_AW_CI_TRIGGER_TOKEN` as required secrets. Those names appear in every compiled `.lock.yml` because gh-aw's default template references them, but none are actually required for this factory — gh-aw falls back to `GITHUB_TOKEN` when they are missing. Do **not** create them unless you have a specific need; the extra tokens just create more things to rotate.

### Required labels

The factory is choreographed through labels. Create these once in **Issues > Labels**. There is no automated label-setup script in this repository; create labels manually via the GitHub web UI or the `gh` CLI (for example: `gh label create needs-rebase --color e4e669 --description "PR branch needs merging with origin/main"`).

| Label | Purpose |
|-------|---------|
| `needs-spec`, `needs-plan`, `spec-refined` | Spec refinement flow |
| `blocked-on-human` | Agent needs human input before proceeding |
| `ready-for-implementation`, `assigned-to-agent` | Implementation dispatch flow |
| `impl:copilot` | Implementer routing (factory auto-routes to Copilot only) |
| `ai-reviewed`, `needs-changes`, `fast-track`, `spec-drift` | Reviewer verdicts |
| `human-review` | Emergency stop: all agents call noop |
| `needs-rebase` | PR branch needs a merge from main; triggers conflict-resolver |
| `eval-regression` | One or more eval cases failed on this PR; set by `eval-creator-ci`, cleared on next green run |
| `self-improvement`, `ci-fix`, `plan-file` | Provenance on factory-generated PRs |
| `workflow-health` | Tracking issues for data-layer failures |
| `automation`, `low-risk` | Applied to routine factory PRs |
| `pr-fix` | Applied to commits pushed by `/pr-fix` |
| `your-turn` | Derived by `sync-factory-state`: item is in the 👉 Your turn lane on the Projects board (human action required) |
| `agent-working` | Derived by `agent-activity-tracker`: at least one factory workflow is currently running on this item |
| `model:<name>` | Derived by `agent-activity-tracker` from the running workflow's `engine.model` (e.g. `model:gpt-5.4`, `model:claude-sonnet-4-6`); auto-created on demand |

Without these labels, workflows that try to `add-labels: allowed: [...]` will fail their safe-output validation.

### Installed GitHub Apps

- **GitHub Copilot** (coding agent + code review) - required for `impl:copilot` routing and inline review annotations
- **`githubnext/agentics`** workflows - installed via `gh aw add githubnext/agentics/<name>` (pulls `/pr-fix`, `issue-triage`)

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

The `spec-refiner` workflow triggers and classifies the issue into one of three paths:

**Plan-worthy (most issues):** spec-refiner reads the issue, runs the `plan-interview` skill, and produces:
- A plan file at `docs/plans/plan-NNN-<slug>.md` where **NNN is the source issue number** (for example, issue #61 produces `plan-061-*.md`). This prevents numbering races when parallel plans land and guarantees one plan per issue (opened as a PR).
- An `impl:copilot` label on the source issue. Only Copilot is auto-assignable today; see Step 3 for the reasoning.
- A label swap: `needs-spec` removed, `needs-plan` added.

**Direct route (simple, clearly bounded issues):** spec-refiner skips the plan file entirely. It removes `needs-spec`, adds `impl:copilot`, `ready-for-implementation`, and `assigned-to-agent`, calls `assign-to-agent` to assign Copilot in the same run, and posts a short comment. No plan PR, no Step 3 merge gate, no dependency on `implementer-dispatcher`. Typical examples: single-file bug fix, dependency bump, one-line config change.

**Terminal or blocked:** spec-refiner removes `needs-spec`, adds `blocked-on-human`, and posts a comment explaining what a human must do. This covers spam, duplicates, issues with missing context, and issues already labeled `human-review`. No further automation runs until a human acts.

After the workflow runs, every `needs-spec` issue is in exactly one of these three next states: waiting for a plan PR review, routed to implementation, or clearly labeled `blocked-on-human`. No issue stays stuck in `needs-spec` after spec-refiner has run.

If the agent cannot answer something from context alone, it marks the gap with **NEEDS HUMAN INPUT** and adds the `blocked-on-human` label. Add a comment with the missing context, remove the label, and re-trigger.

### Step 3: Review the Plan and Choose an Implementer

*This step applies to the plan-worthy path only. Direct-route issues skip to Step 4.*

Read the plan PR. Check the success criteria, the implementation checklist, and the recommended implementer.

Spec-refiner always applies `impl:copilot`. The factory auto-routes to Copilot only; `implementer-dispatcher` calls `assign-to-agent` for that label. If you want to hand off to a different implementer (Claude, Codex), do that outside the factory via the GitHub UI assignees picker after `plan-merged-dispatcher` activates the source issue.

Merge the plan PR. The plan PR references the source issue with a non-closing link (e.g. `Refs #NN`), so merging it does not close the source issue. The source issue stays open as the single tracking anchor through implementation. It is closed by the implementation PR that ships the fix.

On merge, `plan-merged-dispatcher` (a plain GitHub Actions workflow) reads the merged plan file, extracts its `## Implementation Checklist` section, writes that checklist into the **source issue body** inside a delimited block (`<!-- plan-checklist:plan-NNN-slug:begin -->...<!-- ...:end -->`), removes `needs-plan`, and adds `ready-for-implementation`. The delimited block makes re-runs idempotent.

### Step 4: Auto-Assignment (No Manual Work)

For the **plan-worthy path**, `implementer-dispatcher` triggers when the source issue receives the `ready-for-implementation` label from `plan-merged-dispatcher`. It reads the `impl:*` label and calls `assign-to-agent` for `impl:copilot`.

For the **direct-route path**, `spec-refiner` calls `assign-to-agent` in the same run that fast-tracks the issue, bypassing `implementer-dispatcher` entirely. GitHub's anti-loop rule blocks `GITHUB_TOKEN` label events from triggering downstream workflows, so direct-route assignment must happen in the same run.

No sub-issue layer, no parent-issue lookup, no manual assignment.

The agent opens a PR with its implementation.

**Re-dispatching an issue manually.** The dispatcher (plan-worthy path) calls `noop` if the issue already has the `assigned-to-agent` label (prevents double-dispatch). If you ever need to force re-assignment, strip **both** `ready-for-implementation` and `assigned-to-agent`, then re-add `ready-for-implementation`. Re-adding alone is not enough because the noop guard on `assigned-to-agent` still fires.

### Step 5: Automated Review

Two workflows trigger on the new PR:

**Reviewer** checks the PR against the plan file:
1. Loads the plan. Each plan maps to exactly one implementation PR, so there is no sibling-PR discovery step.
2. Self-tamper guard: if the PR diff touches `.github/workflows/reviewer.md`, `.github/workflows/self-improvement-meta.md`, or `.github/copilot-instructions.md`, reviewer applies `human-review` and noops before doing anything else. Human review is required for PRs that could modify the reviewer's own instructions or adjacent guardrails.
3. Detects the implementer and applies calibration:
   - Claude PRs: checked for scope drift (tends to over-implement)
   - Copilot PRs: checked for test coverage gaps (tends to under-test)
   - Codex PRs: checked for correctness on unusual control flow
   - Human PRs: standard rigor
4. Posts a structured review comment. Each criterion is labeled `Met`, `Partial`, `Missed`, or `Drifted`. Verdict: `ai-reviewed`, `needs-changes`, or `fast-track`.

**Contribution checker** evaluates the PR against `docs/CONTRIBUTING.md`: on-topic, focused, has tests, has description, skills synced.

### Step 6: Fix Loop

If the reviewer labels the PR `needs-changes`, comment `/pr-fix` to trigger the automated fix workflow. It analyzes failing CI checks, identifies root causes from error logs, implements fixes, and pushes corrections to the PR branch — including changes to `.github/workflows/` files when the fix requires updating a workflow source or recompiling a lock file.

If CI fails on `main` after a merge, the `ci-cleaner` workflow triggers automatically. It runs `ruff check --fix`, `pytest`, and `gh aw compile` in sequence, then opens a PR with the fixes. It includes a mandatory exit protocol (always produces a PR or noop) and a file-count guard (refuses to create PRs with 50+ changed files).

### Step 7: The Outer Loop (Nightly)

`self-improvement-meta` runs every night around 2am. It:

1. Reads the last 24 hours of workflow run logs
2. Extracts failure patterns and categorizes them (prompt, tool, context, data)
3. Deduplicates against existing entries in `.learnings/LEARNINGS.md`
4. For each promoted learning with a testable prevention rule, generates a matching `.evals/cases/EVAL-NNN.md` file and updates `.evals/EVAL_INDEX.md`
5. Opens a PR that adds prevention rules to `AGENTS.md` or the relevant workflow file, and includes any new eval artifacts in the same commit

When you merge that PR, the next run of the affected agent reads the updated instructions and `eval-creator-ci` can immediately verify the new rule. Promotion and regression-test creation are atomic: one PR, one review gate. If there are no failures, it calls noop. Silence is the correct signal when the factory is healthy.

## Controlling the Chain

| Action | How |
|--------|-----|
| **Pause any step** | Add the `human-review` label. All agents check for it and call noop. |
| **Skip spec-refinement** | Label the issue `needs-plan` directly instead of `needs-spec`. `trigger-plan` fires automatically and activates the issue into `ready-for-implementation`. |
| **Skip automated review** | Label the PR `human-review` and review it yourself |
| **Trigger manually** | Every workflow has `workflow_dispatch` enabled. Run from the Actions tab. |
| **Fix a failing PR** | Comment `/pr-fix` on the PR |
| **Fast-forward simple changes** | For trivial fixes, skip the whole chain: just open a PR directly |

## Landing a PR that modifies a protected workflow file

The reviewer's [self-tamper guard](../.github/workflows/reviewer.md) applies the `human-review` label and noops before running any checks if the PR diff touches any of these paths:

- `.github/workflows/reviewer.md`
- `.github/workflows/self-improvement-meta.md`
- `.github/copilot-instructions.md`

This is intentional: these files can alter the reviewer's own instructions or adjacent guardrails, so a model review of them is not a meaningful signal. Human eyes are required.

### What happens automatically

1. Reviewer applies `human-review` and calls noop.
2. `contribution-checker`, `simplify-and-harden-ci`, and `eval-creator-ci` also noop — they respect the `human-review` label as an emergency stop.
3. CI (tests, lockfile sync) still runs normally and must pass.

### How to unblock the PR

1. Read the diff yourself. Pay attention to whether it weakens guards, changes the self-tamper list, or alters review logic.
2. If the change is correct and intentional, **remove the `human-review` label** from the PR. The quality-gate workflows will NOT rerun on label removal by design — you are now the reviewer of record.
3. Merge the PR.

If the change needs work, leave `human-review` on and either push fixes to the branch yourself or ask the PR author to.

### When the guard fires on an unrelated PR

Sometimes a PR touches a protected file as a side effect of an otherwise routine change (e.g. a lockfile regeneration after a frontmatter tweak). Two options:

- Split the PR. Land the non-protected changes through the normal factory chain, then land the protected file change as a separate PR with your own review.
- Or review the whole PR yourself using the procedure above.

Do not disable the guard to let the PR through. The guard is one line of `case` logic in [`reviewer.md`](../.github/workflows/reviewer.md) — disabling it for convenience defeats the purpose.

## All Workflows

### Factory Chain (custom, skill-backed)

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| [`spec-refiner.md`](../.github/workflows/spec-refiner.md) | Issue labeled `needs-spec` | Structured plan file from issue context using plan-interview skill |
| [`plan-merged-dispatcher.yml`](../.github/workflows/plan-merged-dispatcher.yml) | Plan PR merged (path filter on `docs/plans/plan-*.md`) | Write plan checklist onto source issue body, apply `ready-for-implementation`. Plain GitHub Actions, not gh-aw. |
| [`trigger-plan.yml`](../.github/workflows/trigger-plan.yml) | Issue labeled `needs-plan` | Activate issue when `needs-plan` is applied manually (skip-spec shortcut). Three-path: merged-plan recovery, skip-spec direct activation, or leave-alone when plan PR is still in flight. Plain GitHub Actions, not gh-aw. |
| [`implementer-dispatcher.md`](../.github/workflows/implementer-dispatcher.md) | Issue labeled `ready-for-implementation` | Assign source issue to Copilot cloud agent based on its `impl:*` label |
| [`reviewer.md`](../.github/workflows/reviewer.md) | PR opened / updated | Plan-aware code review with implementer calibration. Refuses to review PRs that modify its own instructions (`.github/workflows/reviewer.md`, `.github/workflows/self-improvement-meta.md`, `.github/copilot-instructions.md`); applies `human-review` and noops instead. |
| [`conflict-resolver.md`](../.github/workflows/conflict-resolver.md) | PR labeled `needs-rebase` | Merge `origin/main` into PR branch; push on clean merge (including workflow file changes), hand off on conflict |
| [`ci-cleaner.md`](../.github/workflows/ci-cleaner.md) | CI failure on `main` | Run `ruff`, `pytest`, `gh aw compile` fix loop; open a PR with repairs; mandatory noop if no changes |
| [`self-improvement-meta.md`](../.github/workflows/self-improvement-meta.md) | Nightly (~2am) | Extract learnings from failures, commit prevention rules, and create eval artifacts for promoted learnings with testable patterns |
| [`contribution-checker.md`](../.github/workflows/contribution-checker.md) | PR opened / updated | Evaluate PR against CONTRIBUTING.md guidelines |
| [`simplify-and-harden-ci.md`](../.github/workflows/simplify-and-harden-ci.md) | PR opened / updated | Scan changed files for simplicity and security issues |
| [`learning-aggregator-ci.md`](../.github/workflows/learning-aggregator-ci.md) | Weekly (Monday) | Aggregate learnings, rank promotion candidates, create gap report |
| [`eval-creator-ci.md`](../.github/workflows/eval-creator-ci.md) | PR opened / updated | Run regression checks against promoted learnings (read-only verifier; eval creation happens in `self-improvement-meta`) |
| [`sync-factory-state.yml`](../.github/workflows/sync-factory-state.yml) | Issue/PR label/state change, cron every 10 min, `workflow_dispatch` | One-way mirror of factory labels onto the "AI Agent Factory" Projects v2 Status field; applies/removes the `your-turn` label as a side effect. Plain GitHub Actions, not gh-aw. |
| [`agent-activity-tracker.yml`](../.github/workflows/agent-activity-tracker.yml) | Cron every 5 min, `workflow_dispatch` | Applies `agent-working` and `model:<name>` labels to items with at least one in-progress factory workflow; sweeps labels off when runs finish. Plain GitHub Actions, not gh-aw. |

These are thin adapter shells. The actual agent logic lives in skills in `.claude/skills/`.

### Support Workflows (from githubnext/agentics)

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| [`issue-triage.md`](../.github/workflows/issue-triage.md) | Issue opened / reopened | Label, categorize, detect spam, provide analysis notes |
| [`pr-fix.md`](../.github/workflows/pr-fix.md) | `/pr-fix` slash command | Analyze failing CI, implement fixes, push to PR branch (including `.github/workflows/` changes) |

Installed via `gh aw add githubnext/agentics/<name>`. These are general-purpose and work out of the box.

### Project-Specific Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| [`ai-proficiency-pr-review.md`](../.github/workflows/ai-proficiency-pr-review.md) | `/assess-proficiency` comment or manual dispatch | AI proficiency score (on-demand only, no auto-trigger) |
| [`ai-proficiency-weekly-report.md`](../.github/workflows/ai-proficiency-weekly-report.md) | Weekly (Monday 9am UTC) | Track proficiency trends over time |
| [`factory-health.md`](../.github/workflows/factory-health.md) | Weekly (Sunday) | Factory-wide health report: workflow run outcomes, failure categorization, handoff latency, unresolved signals, and human override rate |

## Skills Used by the Factory

| Skill | Used by | Purpose |
|-------|---------|---------|
| [`plan-interview`](../.claude/skills/plan-interview/SKILL.md) | spec-refiner | Structured requirements interview before planning |
| `self-improvement` | self-improvement-meta | Learning capture, categorization, and promotion (skill instructions embedded in the workflow; no standalone SKILL.md file) |
| [`intent-framed-agent`](../.claude/skills/intent-framed-agent/SKILL.md) | reviewer | Scope drift detection against plan intent |
| [`simplify-and-harden`](../.claude/skills/simplify-and-harden/SKILL.md) | simplify-and-harden-ci | Post-completion quality and security sweep |
| [`learning-aggregator`](../.claude/skills/learning-aggregator/SKILL.md) | learning-aggregator-ci | Cross-session pattern detection and promotion ranking |
| [`eval-creator`](../.claude/skills/eval-creator/SKILL.md) | eval-creator-ci | Verify regression test cases from promoted learnings (creation happens in `self-improvement-meta`) |
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
| `needs-plan` | Spec is ready, waiting for a plan PR | spec-refiner |
| `needs-rebase` | PR branch is behind main and needs a merge | Human or reviewer |
| `blocked-on-human` | Agent needs human input before proceeding | spec-refiner, conflict-resolver (and other workflows) |
| `spec-refined` | Spec refinement is complete | spec-refiner |
| `ready-for-implementation` | Source issue ready for a coding agent | plan-merged-dispatcher (plan-worthy path), spec-refiner (direct-route path) |
| `impl:copilot` | Assign to Copilot cloud agent (factory auto-routes) | spec-refiner (or human) |
| `assigned-to-agent` | Issue has been dispatched to an agent | implementer-dispatcher |
| `ai-reviewed` | PR passed automated review, ready for human review | reviewer |
| `needs-changes` | PR has critical findings or spec drift | reviewer |
| `fast-track` | Small, well-tested, matches plan, zero findings | reviewer |
| `spec-drift` | PR does things the plan did not ask for | reviewer |
| `human-review` | Emergency stop: all agents call noop | Human, or reviewer (self-tamper guard) |
| `self-improvement` | PR was created by the nightly learning loop | self-improvement-meta |
| `ci-fix` | PR was created by the CI cleaner | ci-cleaner |
| `plan-file` | PR contains a plan file | spec-refiner |

## Implementer Routing

The factory auto-routes to Copilot only. `impl:copilot` is the one routing signal; `implementer-dispatcher` calls `assign-to-agent` for that label. If you want to hand off to a different implementer (Claude, Codex), do that outside the factory via the GitHub UI assignees picker after `plan-merged-dispatcher` activates the source issue.

## Migration note: issues that predate the sub-issue removal

If you have an issue that was in-flight through the old `/plan` → sub-issue factory chain when this refactor landed, the sub-issues and the old dispatcher path no longer exist. The source issue is now the direct unit of work.

To restart the chain for any stranded source issue, apply `ready-for-implementation` directly:

```bash
gh issue edit <issue-number> --add-label ready-for-implementation
```

This triggers `implementer-dispatcher`, which assigns Copilot to the source issue and resumes the factory chain from that point. Remove any stale sub-issues manually — they are orphaned and will not be picked up.

## Stale lock file failure mode

Every `.github/workflows/*.md` source file has a paired `.lock.yml` compiled by `gh aw compile`. The `frontmatter_hash` embedded in the lock file must match the source. When they diverge, gh-aw rejects the next workflow run with a hash mismatch error.

This is a delayed break: the repo stays green until someone triggers the stale workflow. A PR-time guard catches it early.

### CI guard

`.github/workflows/lock-file-sync.yml` runs on every pull request that touches `*.md` or `*.lock.yml` files in `.github/workflows/`. It calls `scripts/check-workflow-lock-sync.sh`, which:

1. Tries `gh aw compile --check-only` when the installed gh-aw version supports it (read-only, no side effects).
2. Falls back to running `gh aw compile` and checking `git diff` for changed lock files when `--check-only` is unavailable.

The job fails with one actionable error per stale pair, including the exact repair command.

### How to fix a stale lock file

1. Identify the stale workflow from the CI failure message.
2. Recompile it locally:
   ```bash
   gh aw compile <workflow-name>
   ```
3. Commit both the `.md` and the regenerated `.lock.yml`:
   ```bash
   git add .github/workflows/<workflow-name>.md .github/workflows/<workflow-name>.lock.yml
   git commit -m "chore: recompile <workflow-name> lock file"
   ```
4. Push. The lock-file-sync check will pass on the next run.

To recompile all workflows at once: `gh aw compile` then commit all changed `.lock.yml` files.

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

# Run the lock-file sync check locally (same check as CI)
bash scripts/check-workflow-lock-sync.sh
```

## Architecture

See [`chain.md`](chain.md) for the full layered architecture diagram and the design rationale for choreography over orchestration.

See [`FACTORY_STATE_MACHINE.md`](FACTORY_STATE_MACHINE.md) for the one-page operator reference: label-to-lane mapping, workflow trigger table, and the happy-path sequence diagram.

## GitHub Projects Board

The factory has a companion **GitHub Projects v2** board that gives you a single-glance view of every issue and PR in flight. Labels remain authoritative; the board is a derived, read-only visualization. Never make decisions on the board — move labels, let the board follow.

**Board**: [AI Agent Factory](https://github.com/users/pskoett/projects/3) (private, user-scope).

### Status lanes (the 4-column overview)

The board's built-in `Status` field is renamed into these four lanes. No other custom fields are used — the goal is one signal at a glance, not a data model.

| Status | Meaning |
|--------|---------|
| 📥 **Waiting for spec** | Fresh issue, or something not yet picked up by the factory. Human needs to add `needs-spec` or triage it. |
| 🤖 **Factory building** | Spec/plan done or dispatched; an agent will pick it up or is already running. Humans can ignore this lane. |
| 👉 **Your turn** | Agents are done for now; a human needs to act (review, resolve conflict, unblock, merge). |
| ✅ **Done** | Issue/PR closed. |

### Label → Status mapping

Evaluated top-down in [`sync-factory-state.yml`](../.github/workflows/sync-factory-state.yml) — the first matching rule wins.

| Priority | Condition | Lane |
|----------|-----------|------|
| 1 | Item is `closed` | ✅ Done |
| 2 | Has any of: `needs-changes`, `needs-rebase`, `human-review`, `blocked-on-human`, `ai-reviewed`, `plan-file`, `eval-regression` | 👉 Your turn |
| 3 | Is an open PR (no other signal) | 👉 Your turn |
| 4 | Has any of: `ready-for-implementation`, `assigned-to-agent`, `needs-plan` | 🤖 Factory building |
| 5 | Everything else | 📥 Waiting for spec |

Items in the 👉 Your turn lane also receive a `your-turn` label; it is stripped when they move out. That lets you filter the issue/PR lists the same way the board does.

### Activity labels (what's running right now)

`agent-activity-tracker.yml` polls in-progress workflow runs every 5 minutes and applies:

- `agent-working` — at least one factory workflow is currently running on this item.
- `model:<name>` — the `engine.model` of the running workflow (`model:gpt-5.4`, `model:claude-sonnet-4-6`, etc.). Auto-created on first use.

Labels are swept off when the run completes. Issue-triggered workflows (under ~3 min) may be missed between polls by design — the tracker only covers PR-triggered runs where GitHub exposes the triggering number on the run object.

### Setup steps (for replicating this in another repo or org)

1. **Create the project.**
   ```bash
   gh project create --owner <user-or-org> --title "AI Agent Factory" --format json
   ```
   Note the project number (shown in the URL, e.g. `/projects/3`) and the `id` field from the JSON output (the `PVT_...` node ID).

2. **Rename the built-in `Status` field options** to match the four lanes above (📥 Waiting for spec, 🤖 Factory building, 👉 Your turn, ✅ Done). Do this in the web UI — `gh project` cannot edit built-in field option names. Skip creating custom fields; the board is intentionally minimal.

3. **Grab the Status field ID and the four option IDs.**
   ```bash
   gh project field-list <number> --owner <user-or-org> --format json \
     | jq '.fields[] | select(.name=="Status") | {id, options}'
   ```
   Copy the field's `id` (the `PVTSSF_...` value) and each option's `id` into `sync-factory-state.yml` (`PROJECT_ID`, `FIELD_ID`, and the `OPT` array). The values currently committed point at this repo's board — update them before using the workflow elsewhere.

4. **Create the `PROJECTS_PAT` secret.** Generate a classic PAT with `repo` + `project` scopes (fine-grained PATs are unreliable against user-scope Projects). Add it under Settings > Secrets and variables > Actions as `PROJECTS_PAT`.

5. **Enable the built-in "Auto-add to project" workflow** on the project with a filter like `is:issue,pr repo:<owner>/<name>`. This makes every new issue and PR show up on the board automatically; `sync-factory-state` does not add new items, it only moves existing ones.

6. **Create the supporting labels.** `your-turn`, `agent-working`, and the `model:*` pattern are in the labels table above. The sync workflow and activity tracker will auto-create `model:<name>` labels on demand; the other two must exist up front.

7. **Commit both workflows.** `.github/workflows/sync-factory-state.yml` (label → Status mirror) and `.github/workflows/agent-activity-tracker.yml` (agent-working / model:* labels). Neither compiles through gh-aw — they are plain GitHub Actions.

8. **Dispatch a full reconcile once** to backfill the board:
   ```bash
   gh workflow run sync-factory-state.yml
   ```
   Leave the `issue_number` input blank to sweep all open items plus the 30 most recent closed ones.

### Recommended saved views

Two views cover ~all daily operation; resist adding more.

- **Board grouped by Status** — the default. One glance, full picture.
- **Table filtered `label:your-turn`** — just the items you need to act on, sortable by update time.

### Guard rails and known limits

- **Labels stay authoritative.** `sync-factory-state` is one-way (labels → board). Dragging a card does not change labels; the 10-minute reconcile cron will snap it back. This is deliberate — the board is a view, not a control plane.
- **Activity tracker misses short issue-triggered runs.** GitHub doesn't expose the issue number on `workflow_runs` for `issues` events, and the tracker polls every 5 min. Acceptable trade-off for a visualization layer.
- **One board per repo today.** Cross-repo aggregation is possible by pointing multiple repos' `sync-factory-state.yml` at the same project ID, but this repo has not exercised that path.
- **Stale lock on the sync workflow.** `sync-factory-state.yml` is plain Actions, not gh-aw, so the lock-file-sync guard does not apply. Edits land as-is.

## Observability

Every factory workflow captures its full session as a GitHub Actions artifact. This section explains where to find transcripts, what they contain, how long they live, and how they feed the outer learning loop.

### Session transcript artifacts

Every gh-aw agent workflow uploads an `agent` artifact after the agent step completes. The artifact is uploaded unconditionally (`if: always()`) with `if-no-files-found: ignore`, so it never causes a workflow failure when the agent does not produce output.

**Artifact name**: `agent`

**Contents**:

| File | Contents |
|------|----------|
| `agent-stdio.log` | Full session: prompt, all tool calls, tool outputs, and final agent responses in order |
| `sandbox/agent/logs/` | Structured agent logs with timestamps and tool metadata |
| `safeoutputs.jsonl` | Every safe-output action taken (issues created, comments posted, PRs opened) |
| `agent_output.json` | Final structured output payload |
| `agent_usage.json` | Token usage: prompt tokens, completion tokens, total |
| `aw-prompts/prompt.txt` | The rendered system prompt that was sent to the agent |
| `mcp-logs/` | MCP gateway request/response logs |

**Artifact retention**: 90 days (GitHub Actions default). After 90 days the artifact is deleted automatically. Raw transcripts are never committed to git history.

### Finding transcripts

```bash
# List recent runs for a specific workflow and see their IDs
gh run list --workflow spec-refiner.lock.yml --limit 10 \
  --json databaseId,displayTitle,conclusion,createdAt

# Download the agent artifact for a specific run
mkdir -p /tmp/transcript-<run-id>
gh run download <run-id> --name agent --dir /tmp/transcript-<run-id>

# Read the session transcript
cat /tmp/transcript-<run-id>/agent-stdio.log

# Check token usage
cat /tmp/transcript-<run-id>/agent_usage.json

# See what safe outputs the agent took
cat /tmp/transcript-<run-id>/safeoutputs.jsonl | jq .
```

You can also browse artifacts in the GitHub UI: navigate to Actions, select the workflow run, and look for the `agent` artifact in the run summary.

### Retention and access

Transcripts are stored as GitHub Actions run artifacts. They are:

- **Scoped to the repository** — same access as Actions logs (repo read access required)
- **Retained for 90 days** — the default for GitHub Actions artifacts; configurable in Settings > Actions > Artifact and log retention
- **Automatically deleted** after the retention period
- **Never committed to git** — raw transcript data stays in artifact storage only

The `.entire/metadata/` directory in this repository does NOT store raw transcript data. See `.entire/metadata/README.md` for its purpose and layout.

### Privacy and PII

Session transcripts may contain content from:
- Issue bodies and titles (which users authored)
- Commit messages and PR descriptions
- File contents from the repository
- Error messages and log output

**Policy**:
- Do not share transcript artifacts outside the repository
- Do not copy raw transcript content into issues, comments, or `.learnings/` entries
- When analyzing transcripts, extract only structural patterns (tool sequences, error categories, retry counts)
- Use abstract summaries in learning entries: "agent retried file-read 5 times" not the actual file content

### How transcripts feed the learning loop

The `learning-aggregator-ci` workflow runs weekly (Monday) and:

1. Reads accumulated entries in `.learnings/` (explicit, manually logged patterns)
2. Downloads `agent` artifacts from the last 7 days of each factory workflow run using `gh run download <run-id> --name agent --dir /tmp/transcripts/<run-id>`
3. Verifies the download with `ls /tmp/transcripts/<run-id>/` — failures are logged explicitly, not silently skipped
4. Reads `agent-stdio.log` from the canonical path `/tmp/transcripts/<run-id>/agent-stdio.log` and parses it for structural patterns (retry loops, noop misfires, approach changes, token anomalies)
5. Merges transcript findings with `.learnings/` entries, deduplicating by `Pattern-Key`
6. Creates a weekly gap report issue with promotion candidates

**Observable output**: The weekly issue reports `Transcript artifacts read: M` and `Transcript patterns extracted: P` separately. When `M > 0` and `P = 0`, the issue explicitly states "artifacts read: M, patterns extracted: 0 — transcripts were parseable but yielded no new patterns." This distinguishes a successful empty parse from a failed read.

**Extraction behavior**: `gh run download` extracts artifact contents directly into `--dir` — it does not leave a ZIP file. Files (`agent-stdio.log`, `agent_usage.json`, `safeoutputs.jsonl`) appear directly in the target directory.

Transcript-derived patterns labeled `**TRANSCRIPT CANDIDATE**` in the weekly issue are routed to `self-improvement-meta` for addition to `.learnings/LEARNINGS.md` via a reviewed PR. This preserves the two-step write path: discover in transcript analysis, land in a PR that a human approves.

### What `self-improvement-meta` uses

`self-improvement-meta` (nightly) reads workflow-level telemetry from `gh aw audit` and `gh run list` as its primary signal source. This covers conclusion outcomes (success, failure, noop), token usage summaries, and error categories surfaced by gh-aw's detection steps.

For the MVP, `self-improvement-meta` does not download individual `agent` artifacts. It relies on the weekly `learning-aggregator-ci` run to surface transcript-derived patterns. This avoids running expensive transcript downloads nightly when weekly cadence is sufficient.

### Weekly factory health report

The `factory-health` workflow runs every Sunday and produces one `[health]` issue covering the previous 7 days of factory activity. It answers five questions:

1. **Workflow run outcomes** — success / failure / skipped / cancelled counts per workflow, overall success rate, and noop-heavy workflows (skip% > 50).
2. **Failure categorization** — each failure in the window classified as infra, workflow-bug, agent-error, or unknown with a one-line evidence snippet.
3. **Handoff latency** — median time from `needs-spec` label applied to plan PR opened (spec-to-plan path).
4. **Unresolved signals** — open `workflow-health` issues, open `[aw] ... failed` issues, and plan PRs older than 48 hours.
5. **Human override rate** — merged PRs that still carried `needs-changes` at merge time.

The report uses `close-older-issues: true` so only the current week's issue is open at any time. Consecutive weekly issues have stable headers and table shapes, making week-to-week diffs meaningful.

Source data is `gh run list`, `gh issue list`, and `gh pr list`. No external telemetry is required.
