---
name: use-agent-factory
description: |
  How to drive the 14-workflow agent factory in this repo from a Claude session. Covers: when to use the factory vs. direct edits, how to start the chain, where the human gates are, how to pick an implementer, how to recover from stuck PRs, and all the failure modes learned to date.

  Use this skill when the user asks you to ship a feature, fix, or refactor through the factory; when they reference an existing issue or PR in the factory chain; when a workflow is stuck or misbehaving; or when you need to file issues or plan files that the factory will pick up.

  Do NOT use this skill for: single-file scratch edits on an untracked branch, research questions, one-shot script runs, or any work that does not produce a PR to main.
---

# Use the Agent Factory

## Purpose

This repo runs a gh-aw agent factory plus one plain Actions workflow. Every non-trivial change should flow through it end to end: `issue > spec > plan PR merged > source issue activated > implementer > review > fix > merge > learn`. The source issue is the unit of work; there is no sub-issue layer. This skill tells you how to drive that flow correctly, where to stop and wait for a human, and what to do when something stalls.

## When to invoke

Activate this skill when any of these hold:

- User asks you to add, fix, refactor, or ship something that will end up on `main`
- User references an issue number, PR number, or plan file that belongs to the factory chain
- User asks about factory status, stuck PRs, or the `needs-spec` / `needs-changes` / `fast-track` labels
- A PR in this repo has been labeled by the factory and you need to decide the next action
- User asks to file a new `needs-spec` issue or to spec-refine an existing issue

**Skip** this skill for: local scratch work that never reaches `main`, questions about the codebase that don't require any edits, read-only audits, or small doc tweaks the user explicitly says should bypass the factory.

## Prerequisites the user must have already done

Before the factory works end to end, these one-time setup items must be in place. If any PR stalls with symptoms like "waiting for approval" or "labels don't stick", suspect these first. Full table in `docs/AGENT_FACTORY.md#prerequisites`.

| Category | What must be true |
|----------|-------------------|
| Repo settings | `Settings > Actions > General`: **Read and write permissions**, **Allow GitHub Actions to create and approve pull requests** checked, **Approval for outside collaborators = Require approval for first-time contributors who are new to GitHub** |
| Copilot | `Settings > Copilot > Coding agent` enabled; `Settings > Copilot > Code review` enabled |
| Secrets | `COPILOT_GITHUB_TOKEN`, `GH_AW_GITHUB_TOKEN`, `GH_AW_GITHUB_MCP_SERVER_TOKEN`, `GH_AW_AGENT_TOKEN`, `GH_AW_CI_TRIGGER_TOKEN` all present in Actions secrets |
| Labels | All factory labels from the Label Reference table must exist |

If any of these is unset, stop and tell the user which setting is missing. Do not try to work around a misconfigured factory by hand-rolling PRs.

## The chain, in one page

```
[human] opens issue
     |
     v
issue-triage  (auto: labels, spam check)
     |
[human] adds `needs-spec` label
     |
     v
spec-refiner  (classifies issue: plan-worthy, direct-route, or blocked)
     |
     +--[plan-worthy]----> produces docs/plans/plan-NNN-<slug>.md as PR + implementer label
     |                         |
     |               [human] merges plan PR  <-- GATE 1 (plan-worthy only)
     |                         |
     |                         v
     |                 plan-merged-dispatcher  (auto: writes plan checklist onto source issue,
     |                                          moves label needs-plan -> ready-for-implementation)
     |
     +--[direct route]--> adds impl:copilot + ready-for-implementation directly
     |                    (no plan PR, no GATE 1)
     |
     +--[blocked]--------> adds blocked-on-human; human resolves before anything else runs
     |
     v (ready-for-implementation)
implementer-dispatcher  (auto: assigns source issue to the chosen agent)
     |
     v
coding agent opens PR
     |
     +--> reviewer           (verdict: ai-reviewed | needs-changes | fast-track)
     +--> contribution-checker
     |
[human] merges PR  <-- GATE 2
     |
     v
ci-cleaner  (auto: runs on main if CI breaks)
     |
     v (nightly)
self-improvement-meta  (opens learnings PR)
     |
[human] approves learnings PR  <-- GATE 3
```

Two or three human decisions depending on the path: for plan-worthy issues: approve plan PR (GATE 1), merge feature PR (GATE 2), approve learnings PR (GATE 3). For direct-route issues: GATE 1 is skipped. Everything else is choreographed.

## How to start a new piece of work

1. **Clarify intent**: before filing anything, make sure you and the user agree on what should change and why. Ask 2 or 3 targeted questions if requirements are vague. Do not guess.

2. **File the issue** via `mcp__github__issue_write` with `method: create`. Include:
   - Problem statement in plain language
   - Evidence (file paths, line numbers, specific observed behavior) where relevant
   - Acceptance criteria as a checkbox list
   - Non-goals or rejected approaches (this helps spec-refiner avoid overreach)
   - Labels: `needs-spec` + one type label (`bug`, `enhancement`, etc.)

3. **Do not** manually write the plan file. Let `spec-refiner` produce it. Your job at this stage is to write a crisp issue, not a plan.

4. **Stop and wait**. Spec-refiner will fire and open a plan PR within a few minutes. Tell the user to review it.

## How to pick an implementer

Spec-refiner recommends one of four labels. Defaults from `docs/AGENT_FACTORY.md`:

| Label | Use when |
|-------|---------|
| `impl:claude-opus` | Multi-file refactor, architectural risk, 6+ checklist items |
| `impl:claude-sonnet` | Single-component feature, medium blast radius, existing patterns |
| `impl:copilot` | Trivial fix, dependency bump, config change |
| `impl:codex` | Opportunistic A/B comparison against another agent |

If spec-refiner picked one and you disagree, tell the user to swap the label on the issue before merging the plan PR. Do not swap it yourself.

## How to drive existing PRs in the factory

Match the PR's labels to the action:

| Label on PR | What it means | Your move |
|-------------|--------------|-----------|
| `ai-reviewed` | Reviewer approved, no findings | Tell the user it's ready for merge (GATE 2) |
| `fast-track` | Small, clean, plan-matching, zero findings | Tell the user it's ready for merge |
| `needs-changes` | Reviewer found warnings or spec drift | Post `/pr-fix` as a comment. Check back after the next commit lands |
| `spec-drift` | PR does things the plan did not ask for | Ask the user whether to expand the plan or scope down the PR. Do not auto-fix |
| `human-review` | Emergency stop | Do nothing until the user removes the label |
| no verdict label | Reviewer did not post a verdict | Flip PR to draft then back to ready-for-review to retrigger |

After `/pr-fix` pushes a fix commit, the reviewer should re-run automatically. If it does not, retrigger as above.

## Failure modes seen in real runs

These are the concrete failure modes this factory has hit. When you see symptoms from this list, apply the fix immediately instead of debugging from scratch.

### Symptom: PR CI shows many `conclusion: skipped` jobs

**Cause**: Normal. gh-aw fires many workflows for each event; each one's inner guard decides whether to actually run. Most skip. This is not a failure.

**Action**: None. Check only the non-skipped jobs for real CI.

### Symptom: First PR from Copilot is gated behind "Approve and run"

**Cause**: Repo `Approval for outside collaborators` is set to the stricter default, and Copilot is treated as a first-time contributor.

**Action**: Tell the user to flip the setting to **Require approval for first-time contributors who are new to GitHub**, then the next push will run cleanly. After the first Copilot PR merges, this gets less strict automatically.

### Symptom: PR has merge conflicts; "Update branch" button fails

**Cause**: PR branch is behind `origin/main`.

**Action**: Add the `needs-rebase` label. The `conflict-resolver` workflow will merge `origin/main` into the branch automatically. If conflicts exist, it posts a comment listing the files and adds `blocked-on-human`. Clone locally, resolve the conflicts, and push. Remove `blocked-on-human` after the push. Do not let `/pr-fix` near a conflicted branch; it is not designed for rebase work.

### Symptom: Reviewer did not post a verdict after the PR was opened

**Cause**: Workflow triggered while the PR was still in draft, or got stuck before reaching the agent step.

**Action**: Flip the PR to draft then back to ready-for-review (`update_pull_request` twice). Reviewer will re-fire.

### Symptom: Plan PR does not appear after labeling the issue `needs-spec`

**Cause**: Two possibilities. First: spec-refiner classified the issue as direct-route and fast-tracked it without a plan PR. Check the issue for a comment from spec-refiner and an `impl:copilot` + `ready-for-implementation` label. If both are present, no plan PR is expected. Second: the workflow failed. Usually a missing secret (`COPILOT_GITHUB_TOKEN`), Copilot coding agent not enabled, or the `blocked-on-human` label already on the issue.

**Action for direct-route**: No action needed. The issue is queued for `implementer-dispatcher`. If you want a plan PR anyway, remove `ready-for-implementation`, add `needs-spec`, and comment on the issue to ask spec-refiner to treat it as plan-worthy.

**Action for workflow failure**: Check `gh aw status` and the most recent run in the Actions tab. If the run shows "NEEDS HUMAN INPUT", read its comment for the missing context, answer in the issue, remove `blocked-on-human`, and re-trigger.

### Symptom: lock-file-sync CI job fails with "stale pair" errors

**Cause**: A workflow `.md` file was edited without rerunning `gh aw compile`. The `frontmatter_hash` in the paired `.lock.yml` no longer matches the source. This guard runs on every PR that touches `.github/workflows/*.md` or `.github/workflows/*.lock.yml` files. Refs pskoett/measuring-ai-proficiency#95.

**Action**: Recompile the stale workflow and commit the updated lock file.

1. Find the stale workflow name in the CI failure output.
2. Run `gh aw compile <workflow-name>` locally (or `gh aw compile` to fix all at once).
3. Commit the updated `.lock.yml` alongside the `.md` change.
4. Push. The CI check will pass on the next run.

Do not edit `.lock.yml` files by hand. Always regenerate them with `gh aw compile`.

### Symptom: ai-proficiency-pr-review auto-fired on a PR you didn't expect

**Cause**: Regression: something re-added the `pull_request` trigger. It should be on `issue_comment` + `workflow_dispatch` only (see `.github/workflows/ai-proficiency-pr-review.md` and `ai-proficiency-claude.yml`).

**Action**: Do not ignore. Check both workflow files for a `pull_request` trigger; if present, remove it and recompile, or edit both `.md` and `.lock.yml` directly. This was a known regression source in earlier sessions.

## How to bypass the factory when appropriate

Some changes should not go through the factory. These include:

- Changes to factory workflows themselves (`.github/workflows/*.md`) that the factory could get caught in a loop on
- Emergency fixes when the factory is broken
- Pure Claude-session context files that are user-visible only (`.claude/skills/*`)
- Plan-numbering collisions or label cleanups

For these cases:

1. Work on a `claude/<slug>` branch directly
2. Open a draft PR with a clear description
3. Do not expect reviewer, contribution-checker, or plan-aware review to run usefully
4. Ask the user to merge once ready

If you are unsure whether to use the factory, ask the user. Defaulting to the factory is usually correct, but these exceptions exist.

## Commit and PR hygiene

Every PR you open into this repo, factory or bypass, must:

- Target the branch the user specified in this session's config; otherwise `main` directly when running for factory-bypass work
- End the commit message and PR body with the current Claude Code session URL (`https://claude.ai/code/session_...`) for provenance
- Be opened as a **draft** first; only mark ready-for-review once you have confirmed the change compiles, renders, or tests pass locally when that is possible

## After a change lands

- If the change touched a workflow, run `gh aw status` mentally (check the Actions tab) to confirm the next scheduled run behaves as expected
- If the change closed a `needs-spec` issue, check that the issue actually closed. If it did not, the plan PR did not correctly reference `Closes #N`
- If the change was large, remind the user that `self-improvement-meta` runs nightly and may open a learnings PR tomorrow that is worth a quick review

## One-line summary for your own reference

The factory is an issue-first, label-driven choreography: write a crisp issue with `needs-spec`, let spec-refiner classify it (plan PR for complex work, direct route for trivial work), merge the plan PR if one exists, let the implementer open the feature PR, let the reviewer verdict, react to the label, let the user merge, and file any gaps you see as new `needs-spec` issues so the factory improves itself.
