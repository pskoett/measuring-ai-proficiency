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
spec-refiner (plan file + implementer label on issue)
  |
  v
human reviews plan PR, optionally swaps implementer label  <-- ONE decision
  |
  v
human merges plan PR
  |
  v
plan-merged-dispatcher (plain Actions: writes plan checklist onto source issue body,
                        transitions needs-plan -> ready-for-implementation)
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
| Copilot Partner Agents (Claude, Codex) | Settings > Copilot > Coding agent > Partner Agents | Optional: On if you plan to hand-assign Claude/Codex via the GitHub UI | Partner Agents appear in the assignees picker when enabled, but the factory cannot auto-dispatch to them today (see "Implementer Routing" below for why). |
| Copilot cloud agent | Settings > Copilot > Coding agent | **Enabled** | Required for `impl:copilot` issue assignment |
| Copilot code review | Settings > Copilot > Code review | **Enabled for this repo** | Lets the Copilot SWE agent annotate PRs inline |
| Actions permissions | Settings > Actions > General > Actions permissions | **Allow all actions and reusable workflows** | Some factory workflows pull from `githubnext/agentics` and `github/gh-aw-actions` |

### Required secrets

Add these under **Settings > Secrets and variables > Actions**. `GITHUB_TOKEN` is provided by GitHub automatically and does not need to be created.

| Secret | Required by | How to get it |
|--------|-------------|---------------|
| `COPILOT_GITHUB_TOKEN` | Every custom gh-aw workflow (agent runtime auth) | Personal access token with `copilot` scope, or a fine-grained token with Copilot access |
| `GH_AW_AGENT_TOKEN` | `implementer-dispatcher` (assigning Copilot) and `plan-merged-dispatcher` (label cascades into `implementer-dispatcher`) | PAT with `issues: write`, `contents: write`, and cascade-capable (i.e. a user/installation PAT, not `GITHUB_TOKEN`) |
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
| `impl:claude-opus`, `impl:claude-sonnet`, `impl:copilot`, `impl:codex` | Implementer routing |
| `ai-reviewed`, `needs-changes`, `fast-track`, `spec-drift` | Reviewer verdicts |
| `human-review` | Emergency stop: all agents call noop |
| `needs-rebase` | PR branch needs a merge from main; triggers conflict-resolver |
| `self-improvement`, `ci-fix`, `plan-file` | Provenance on factory-generated PRs |
| `workflow-health` | Tracking issues for data-layer failures |
| `automation`, `low-risk` | Applied to routine factory PRs |
| `pr-fix` | Applied to commits pushed by `/pr-fix` |

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

The `spec-refiner` workflow triggers. It reads the issue, runs the `plan-interview` skill, and produces:
- A plan file at `docs/plans/plan-NNN-<slug>.md` where **NNN is the source issue number** (for example, issue #61 produces `plan-061-*.md`). This prevents numbering races when parallel plans land and guarantees one plan per issue (opened as a PR).
- An `impl:copilot` label on the source issue. Only Copilot is auto-assignable today; see Step 3 for the reasoning.
- A label swap: `needs-spec` removed, `needs-plan` added

If the agent cannot answer something from context alone, it marks the gap with **NEEDS HUMAN INPUT** and adds the `blocked-on-human` label. Add a comment with the missing context, remove the label, and re-trigger.

### Step 3: Review the Plan and Choose an Implementer

Read the plan PR. Check the success criteria, the implementation checklist, and the recommended implementer.

Spec-refiner always applies `impl:copilot` today. Only Copilot has a real GitHub agent user that `implementer-dispatcher` can assign to via `assign-to-agent`. If the recommendation looks wrong (for example, you want to hand a complex refactor to Claude Opus yourself), swap the label on the source issue before proceeding. `impl:claude-*` and `impl:codex` exist for this manual-override case only — they will _not_ auto-route to an agent.

| Label | Who can auto-assign | Use when |
|-------|---------------------|----------|
| `impl:copilot` | **Yes** — Copilot cloud agent | Default for everything today |
| `impl:claude-opus` | **No, manual only** | You will hand the issue to Claude Opus yourself via claude.ai/code |
| `impl:claude-sonnet` | **No, manual only** | Same, for Claude Sonnet |
| `impl:codex` | **No, manual only** | Same, for Codex |

Merge the plan PR. The plan PR references the source issue with a non-closing link (e.g. `Refs #NN`), so merging it does not close the source issue. The source issue stays open as the single tracking anchor through implementation. It is closed by the implementation PR that ships the fix.

On merge, `plan-merged-dispatcher` (a plain GitHub Actions workflow) reads the merged plan file, extracts its `## Implementation Checklist` section, writes that checklist into the **source issue body** inside a delimited block (`<!-- plan-checklist:plan-NNN-slug:begin -->...<!-- ...:end -->`), removes `needs-plan`, and adds `ready-for-implementation`. The delimited block makes re-runs idempotent.

### Step 4: Auto-Assignment (No Manual Work)

The `implementer-dispatcher` workflow triggers when the **source issue** receives the `ready-for-implementation` label. It reads the `impl:*` label from that same issue and calls `assign-to-agent` when the label is `impl:copilot`.

You assigned once at Step 3. No sub-issue layer, no parent-issue lookup, no manual assignment.

The agent opens a PR with its implementation.

**Re-dispatching an issue manually.** The dispatcher calls `noop` if the issue already has the `assigned-to-agent` label (prevents double-dispatch). If you ever need to force dispatcher to re-run — for example, you changed the `impl:*` label and want the new routing to take effect — strip **both** `ready-for-implementation` and `assigned-to-agent`, then re-add `ready-for-implementation`. Re-adding alone is not enough because the noop guard on `assigned-to-agent` still fires.

### Step 5: Automated Review

Two workflows trigger on the new PR:

**Reviewer** checks the PR against the plan file:
1. Loads the plan. Each plan maps to exactly one implementation PR, so there is no sibling-PR discovery step.
2. Detects the implementer and applies calibration:
   - Claude PRs: checked for scope drift (tends to over-implement)
   - Copilot PRs: checked for test coverage gaps (tends to under-test)
   - Codex PRs: checked for correctness on unusual control flow
   - Human PRs: standard rigor
3. Posts a structured review comment. Each criterion is labeled `Met`, `Partial`, `Missed`, or `Drifted`. Verdict: `ai-reviewed`, `needs-changes`, or `fast-track`.

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
| **Fast-forward simple changes** | For trivial fixes, skip the whole chain: just open a PR directly |

## All Workflows

### Factory Chain (custom, skill-backed)

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| [`spec-refiner.md`](../.github/workflows/spec-refiner.md) | Issue labeled `needs-spec` | Structured plan file from issue context using plan-interview skill |
| [`plan-merged-dispatcher.yml`](../.github/workflows/plan-merged-dispatcher.yml) | Plan PR merged (path filter on `docs/plans/plan-*.md`) | Write plan checklist onto source issue body, apply `ready-for-implementation`. Plain GitHub Actions, not gh-aw. |
| [`implementer-dispatcher.md`](../.github/workflows/implementer-dispatcher.md) | Issue labeled `ready-for-implementation` | Assign source issue to Copilot cloud agent based on its `impl:*` label |
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
| `needs-plan` | Spec is ready, waiting for a plan PR | spec-refiner |
| `needs-rebase` | PR branch is behind main and needs a merge | Human or reviewer |
| `blocked-on-human` | Agent needs human input before proceeding | spec-refiner, conflict-resolver (and other workflows) |
| `spec-refined` | Spec refinement is complete | spec-refiner |
| `ready-for-implementation` | Source issue ready for a coding agent | plan-merged-dispatcher |
| `impl:claude-opus` | Assign to Claude Opus 4.6 | spec-refiner (or human) |
| `impl:claude-sonnet` | Assign to Claude Sonnet 4.6 | spec-refiner (or human) |
| `impl:copilot` | Assign to Copilot cloud agent | spec-refiner (or human) |
| `impl:codex` | Assign to Codex GPT-5.4 | spec-refiner (or human) |
| `assigned-to-agent` | Issue has been dispatched to an agent | implementer-dispatcher |
| `ai-reviewed` | PR passed automated review, ready for human review | reviewer |
| `needs-changes` | PR has critical findings or spec drift | reviewer |
| `fast-track` | Small, well-tested, matches plan, zero findings | reviewer |
| `spec-drift` | PR does things the plan did not ask for | reviewer |
| `human-review` | Emergency stop: all agents call noop | Human |
| `self-improvement` | PR was created by the nightly learning loop | self-improvement-meta |
| `ci-fix` | PR was created by the CI cleaner | ci-cleaner |
| `plan-file` | PR contains a plan file | spec-refiner |

## Implementer Routing

Only `impl:copilot` auto-routes today. The other `impl:*` labels exist as human-override signals for manual assignment via the GitHub UI.

| Label | Auto-route | Use |
|-------|------------|-----|
| `impl:copilot` | **Yes** — `assign-to-agent` → Copilot cloud agent | Default for everything the factory dispatches. |
| `impl:claude-opus` | **No, manual only** | Swap this label on the source issue and use the GitHub UI assignees picker to assign `Claude`. |
| `impl:claude-sonnet` | **No, manual only** | Same as above, different mental calibration for reviewer. |
| `impl:codex` | **No, manual only** | Swap label, assign `Codex` via the UI picker. |

### Why Claude and Codex are UI-only

GitHub's REST API assignees endpoint accepts `Copilot` as a valid assignee but silently drops Partner Agents (`Claude`, `Codex`). It returns HTTP 200 with a "success" response, but the actual assignee list stays empty and no `assigned` timeline event fires. The UI assignees picker uses a different backend path that Partner Agents live on. Confirmed twice on #149 (both `claude[bot]` and plain `Claude` silently dropped).

Until GitHub exposes proper REST-based assignment for Partner Agents, the factory cannot auto-dispatch to Claude or Codex. When that ships, re-introduce `assign-to-user` in `implementer-dispatcher.md` and widen spec-refiner's recommendation.

Spec-refiner always recommends `impl:copilot`. A human can swap to a Partner-Agent label before merging the plan PR, then do the UI assignment manually after `plan-merged-dispatcher` activates the source issue. Reviewer still calibrates based on who actually opened the implementation PR.

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
2. Downloads `agent` artifacts from the last 7 days of each factory workflow run
3. Parses `agent-stdio.log` for structural patterns (retry loops, noop misfires, approach changes, token anomalies)
4. Merges transcript findings with `.learnings/` entries, deduplicating by `Pattern-Key`
5. Creates a weekly gap report issue with promotion candidates

Transcript-derived patterns labeled `**TRANSCRIPT CANDIDATE**` in the weekly issue are routed to `self-improvement-meta` for addition to `.learnings/LEARNINGS.md` via a reviewed PR. This preserves the two-step write path: discover in transcript analysis, land in a PR that a human approves.

### What `self-improvement-meta` uses

`self-improvement-meta` (nightly) reads workflow-level telemetry from `gh aw audit` and `gh run list` as its primary signal source. This covers conclusion outcomes (success, failure, noop), token usage summaries, and error categories surfaced by gh-aw's detection steps.

For the MVP, `self-improvement-meta` does not download individual `agent` artifacts. It relies on the weekly `learning-aggregator-ci` run to surface transcript-derived patterns. This avoids running expensive transcript downloads nightly when weekly cadence is sufficient.
