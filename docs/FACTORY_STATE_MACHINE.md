# Factory State Machine: Operator Reference

Static one-page reference for the agent factory. Answers routing and debugging questions in under 30 seconds.

This page documents the live state machine. **Labels are the control plane. The board is a visualization layer.** Do not use the Projects board to make routing decisions — update labels.

For the layered architecture and the design rationale, see [`chain.md`](chain.md).

---

## Label-to-Lane Mapping

Six board lanes, derived from label semantics. An issue or PR belongs to the lane whose highest-priority matching label fires.

| Label | Board lane | Meaning | Set by |
|-------|------------|---------|--------|
| _(no factory label)_ | **Inbox** | Opened, not yet triaged | — |
| `needs-spec` | **Planning** | Needs a structured plan file | Human |
| `needs-plan` | **Planning** | Spec done; plan PR in flight | `spec-refiner` |
| `blocked-on-human` | **Needs Attention** | Agent cannot proceed without human input | `spec-refiner`, `conflict-resolver` |
| `spec-refined` | **Planning** | Spec refinement complete (informational) | `spec-refiner` |
| `impl:copilot` | **Planning** | Implementer chosen (Copilot, auto-dispatch) | `spec-refiner` (or human) |
| `impl:claude-opus` | **Planning** | Implementer chosen (Claude Opus, manual only) | human |
| `impl:claude-sonnet` | **Planning** | Implementer chosen (Claude Sonnet, manual only) | human |
| `impl:codex` | **Planning** | Implementer chosen (Codex, manual only) | human |
| `ready-for-implementation` | **In flight** | Source issue ready; awaiting agent PR | `plan-merged-dispatcher` |
| `assigned-to-agent` | **In flight** | Issue dispatched to Copilot cloud agent | `implementer-dispatcher` |
| `ai-reviewed` | **Review** | Reviewer passed; ready for human review | `reviewer` |
| `fast-track` | **Review** | Small, well-tested, zero findings | `reviewer` |
| `spec-drift` | **Review** | PR does things the plan did not ask for | `reviewer` |
| `needs-changes` | **Needs Attention** | Critical findings or missed criteria | `reviewer` |
| `needs-rebase` | **Needs Attention** | PR branch is behind main | `reviewer` or human |
| `human-review` | **Needs Attention** | Emergency stop; all agents call noop | human or `reviewer` (self-tamper guard) |
| _(PR merged / issue closed)_ | **Done** | Implementation shipped | — |

**Provenance labels** (on factory-generated PRs, not on source issues):

| Label | Meaning | Set by |
|-------|---------|--------|
| `plan-file` | PR contains a plan file | `spec-refiner` |
| `self-improvement` | PR created by the nightly learning loop | `self-improvement-meta` |
| `ci-fix` | PR created by CI cleaner | `ci-cleaner` |
| `automation` | Routine factory PR | various |
| `low-risk` | Low-risk automated change | various |
| `workflow-health` | Tracking issue for a data-layer failure | `self-improvement-meta` |

---

## Workflow Trigger Table

All factory workflows. Plain GitHub Actions workflows are marked **[Actions]**; all others are gh-aw workflows.

| Workflow | Activates on | Filter | Primary output / side effect |
|----------|-------------|--------|------------------------------|
| `issue-triage` | `issues: [opened, reopened]` | Any issue | Applies type/priority labels, posts analysis comment |
| `spec-refiner` | `issues: [labeled]` | `needs-spec` label | Opens plan PR (`[plan] Plan NNN`), adds `needs-plan` + `impl:copilot`, removes `needs-spec` |
| `plan-merged-dispatcher` **[Actions]** | `pull_request: [closed]` (merged) | Path `docs/plans/plan-*.md` | Writes plan checklist onto source issue body, removes `needs-plan`, adds `ready-for-implementation` |
| `implementer-dispatcher` | `issues: [labeled]` | `ready-for-implementation` label | Assigns source issue to Copilot cloud agent (`assign-to-agent`), adds `assigned-to-agent` |
| `reviewer` | `pull_request: [opened, ready_for_review, synchronize]` | Bot authors only | Posts structured review comment, applies `ai-reviewed` / `needs-changes` / `fast-track`; adds `needs-rebase` when PR is behind main |
| `contribution-checker` | `pull_request: [opened, synchronize, ready_for_review]` | Bot authors only | Posts CONTRIBUTING.md compliance check comment |
| `simplify-and-harden-ci` | `pull_request: [opened, synchronize, reopened, ready_for_review]` | Bot authors; ignores `docs/plans/**` | Posts simplify/harden/document scan report |
| `eval-creator-ci` | `pull_request: [opened, synchronize, reopened, ready_for_review]` | Bot authors; ignores `docs/plans/**` | Runs eval cases in `.evals/`; posts pass/fail/skip table |
| `conflict-resolver` | `pull_request: [labeled]` | `needs-rebase` label | Merges `origin/main` into PR branch; removes `needs-rebase` on clean merge or adds `blocked-on-human` on conflict |
| `pr-fix` | `slash_command: pr-fix` | Comment containing `/pr-fix` | Analyzes CI failures, pushes fix commits to PR branch |
| `ci-cleaner` | `workflow_run` (CI completed) | CI workflow, `main` branch, failed | Runs lint + test + recompile, opens `[ci-fix]` PR |
| `self-improvement-meta` | `schedule` (daily ~2am) | — | Extracts failure patterns from last 24h of runs; opens `[learnings]` PR updating harness files |
| `learning-aggregator-ci` | `schedule` (weekly, Monday) | — | Aggregates `.learnings/` + session transcript artifacts; opens gap-report issue |
| `ai-proficiency-pr-review` | `issue_comment: [created]` | Comment contains `/assess-proficiency` | Posts AI proficiency assessment comment on the PR |
| `ai-proficiency-weekly-report` | `schedule` (Monday 9am UTC) | — | Creates weekly proficiency tracking issue |

---

## Happy-Path Sequence Diagram

From issue opened to implementation PR merged. Human gates are labeled **[HUMAN]**.

```
Issue opened
  │
  └─► issue-triage fires
        └─► applies type/priority labels, posts analysis comment

[HUMAN] Human adds "needs-spec" label
  │
  └─► spec-refiner fires
        ├─► creates plan file at docs/plans/plan-NNN-<slug>.md
        ├─► opens plan PR titled "[plan] Plan NNN: ..."
        │     (body uses "Refs #NNN" — non-closing link)
        ├─► adds "needs-plan" + "impl:copilot" to source issue
        └─► removes "needs-spec" from source issue

[HUMAN] Human reviews plan PR
        ├─► (optional) swaps "impl:copilot" to another "impl:*" label for manual routing
        └─► merges plan PR

  └─► plan-merged-dispatcher fires (plain GitHub Actions)
        ├─► reads Implementation Checklist from merged plan file
        ├─► writes checklist into source issue body (delimited, idempotent)
        ├─► removes "needs-plan" from source issue
        └─► adds "ready-for-implementation" to source issue

  └─► implementer-dispatcher fires
        ├─► reads "impl:copilot" label
        ├─► calls assign-to-agent → Copilot cloud agent
        └─► adds "assigned-to-agent" to source issue

Copilot opens implementation PR
  │
  ├─► reviewer fires
  │     ├─► checks merge state → adds "needs-rebase" if PR is behind main
  │     ├─► finds plan file, evaluates each success criterion
  │     ├─► applies implementer calibration (Copilot: test coverage focus)
  │     ├─► posts structured review comment
  │     └─► adds verdict label: "ai-reviewed" | "needs-changes" | "fast-track"
  │
  ├─► contribution-checker fires
  │     └─► posts CONTRIBUTING.md compliance check
  │
  ├─► simplify-and-harden-ci fires
  │     └─► posts simplify/harden/document scan
  │
  └─► eval-creator-ci fires
        └─► runs eval regression cases

[HUMAN] Human reviews "ai-reviewed" PR and merges it
        (fast-track PRs may skip deeper human review at human's discretion)

  └─► PR merged → source issue closed
```

### Side branches (off happy path)

```
"needs-rebase" applied to PR
  └─► conflict-resolver fires
        ├─► clean merge: pushes merge commit, removes "needs-rebase"
        └─► conflict: adds "blocked-on-human", posts conflicted-file list

"needs-changes" applied to PR
  └─► [HUMAN] Human comments "/pr-fix"
        └─► pr-fix fires
              ├─► analyzes CI failures, pushes fix commits
              └─► loops back to reviewer on next push

CI fails on main after a merge
  └─► ci-cleaner fires
        ├─► runs ruff + pytest + gh aw compile
        └─► opens "[ci-fix]" PR

Nightly (independent of main chain)
  └─► self-improvement-meta fires
        ├─► reads last 24h workflow run logs
        ├─► extracts failure patterns
        └─► opens "[learnings]" PR updating AGENTS.md, CLAUDE.md, workflow files

Weekly (independent of main chain)
  └─► learning-aggregator-ci fires
        ├─► reads .learnings/ + session transcript artifacts
        └─► opens gap-report issue with promotion candidates
```

---

## Quick-Answer Key

| Question | Answer |
|----------|--------|
| "Which label moves an issue from spec to planning?" | `needs-spec` triggers `spec-refiner`, which adds `needs-plan` |
| "Which label fires the implementer?" | `ready-for-implementation` triggers `implementer-dispatcher` |
| "What happens when a human merges a plan PR?" | `plan-merged-dispatcher` writes the checklist and adds `ready-for-implementation` |
| "What triggers when a reviewer applies `needs-rebase`?" | `conflict-resolver` fires and attempts an automatic merge |
| "How do I pause the chain?" | Add `human-review` to the issue or PR; all agents call noop |
| "How do I skip spec-refinement?" | Label the issue `needs-plan` directly |
| "What auto-routes vs. requires manual assignment?" | Only `impl:copilot` auto-routes; all other `impl:*` labels require UI assignment |
