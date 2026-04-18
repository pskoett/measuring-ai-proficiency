---
plan-id: plan-240
status: active
target-files:
  - .github/workflows/sync-factory-state.yml
  - docs/AGENT_FACTORY.md
  - docs/FACTORY_STATE_MACHINE.md
  - docs/AGENT_FACTORY_ANALYSIS.md
  - .learnings/LEARNINGS.md
---
# Plan 240: Harden `sync-factory-state` against missed `pull_request` events

**Source issue**: #240
**Status**: Ready for implementation

## Problem Statement

`sync-factory-state.yml` is the one-way mirror from factory labels and item state onto the Projects v2 board. Today it listens for `pull_request` events plus a 10-minute reconcile cron. Issue #240 documents multiple same-day misses on `pull_request.opened`, `pull_request.closed`, and `pull_request.labeled` for PRs touched through `gh` CLI, `gh api`, and Copilot-created draft PRs. When those events do not arrive, the board and `your-turn` label drift until a human manually dispatches the workflow or the next scheduled reconcile runs.

That lag is now large enough to erode operator trust and to break at least one automation path entirely: `needs-rebase` never becomes visible on the board if the labeling event does not trigger the sync workflow.

## Interview Synthesis

The issue body provides enough detail to simulate the planning interview without extra human input.

### Technical constraints

- Keep `sync-factory-state.yml` as a plain GitHub Actions workflow. Do not convert it into a gh-aw workflow.
- Preserve the current control-plane contract: labels remain authoritative, and the Projects board stays a derived view.
- Keep the existing per-item event triggers in place. The short-term fix should improve recovery from missed events, not replace working event paths.
- Use the existing Projects PAT path and current board mapping logic unless the investigation proves a different auth path is required.
- Treat root-cause investigation as a first-class implementation step. The fix should leave behind enough observability to explain which event/auth paths are unreliable.

### Scope boundaries

- Cover the sync workflow, the directly related board-state docs, and the requested learning entry.
- Include a bounded test or repro harness that exercises PR open and close behavior against the shortened reconcile window.
- Do not redesign the factory board, label taxonomy, or activity tracker as part of this issue.
- Do not add auth-path-specific dispatch hooks such as ad hoc `workflow_dispatch` calls from unrelated workflows unless the investigation shows the cron-tightening path is insufficient.

### Risk tolerance

- Prefer a low-risk resilience improvement now, even if the exact GitHub-side root cause remains partially opaque.
- Accept modest extra runner usage from a tighter reconcile cadence if it materially reduces stale board state.
- Avoid brittle fixes that only cover one producer path, such as Copilot-only or CLI-only patches, unless a single root cause is proven.

### Success signal

- `sync-factory-state.yml` reconciles often enough that missed PR events no longer leave stale board state for roughly 10 minutes.
- The repo gains a documented, repeatable way to investigate or demonstrate missed webhook behavior.
- Operators can read the docs and understand the expected maximum lag between reality and the board.
- The reliability pattern is captured in `.learnings/LEARNINGS.md` under the issue's requested pattern key.

## Decision Frame

Use a two-track implementation:

1. **Immediate resilience**: tighten the reconcile cron in `sync-factory-state.yml` from 10 minutes to a smaller window, with 2 minutes as the default target unless investigation shows a meaningful runner-cost or rate-limit concern.
2. **Targeted diagnosis**: add enough logging, documentation, or a reproducible smoke path to distinguish "event missed entirely" from "event fired but update failed," and to capture which producer paths are affected.

This is the safest first move. The issue already shows the current webhook path is not reliable enough to stand alone. A shorter reconcile window reduces user-visible drift across all producer paths, while the investigation work preserves the ability to add a narrower upstream fix later if the root cause becomes clear.

## Success Criteria

- `.github/workflows/sync-factory-state.yml` changes its scheduled reconcile from every 10 minutes to every 2 to 5 minutes, with the final value documented in the workflow comments and board docs.
- The sync workflow's comments or adjacent documentation explicitly describe the new cron as a safety net for missed `pull_request` events, not just generic drift repair.
- A repeatable test case or smoke harness covers PR creation and closure, and verifies that board state converges within the configured cron window without manual `workflow_dispatch`.
- `docs/AGENT_FACTORY.md` documents the expected maximum board lag and explains that webhook delivery can be missed on some PR mutation paths.
- Any other directly user-facing board-state reference that still promises a 10-minute window is updated to match, including `docs/FACTORY_STATE_MACHINE.md` and `docs/AGENT_FACTORY_ANALYSIS.md` if their wording would otherwise become stale.
- `.learnings/LEARNINGS.md` gains a new entry with `Pattern-Key: sync-factory-state-webhook-missed` that captures the recurrence pattern and prevention rule.

## Risk Assessment

**Blast radius**: Medium. The change is small in code volume, but it affects the repo's primary state-mirroring workflow and the operator expectations around board freshness.

**Rollback**: Straightforward. Revert the cron, the small observability additions, the doc wording, and the learning entry.

**Key risks and mitigations**

- **Risk**: A shorter cron increases runner use or hits GitHub API limits on full-board reconcile runs. **Mitigation**: keep the change bounded to 2 to 5 minutes, preserve the current per-item path, and validate that the reconcile loop still works within existing limits.
- **Risk**: The team overfits to one auth path, then misses the broader reliability problem. **Mitigation**: treat auth-path-specific workarounds as follow-on options, not the default implementation.
- **Risk**: The requested "test case" becomes impossible to automate deterministically because webhook loss is intermittent and GitHub-hosted. **Mitigation**: define the test around convergence within the cron window, not around forcing GitHub to drop an event every run, and document any manual trigger steps if full automation is not feasible.
- **Risk**: Docs drift because multiple files still describe the old 10-minute guarantee. **Mitigation**: update every directly adjacent board-state reference in the same PR as the workflow change.

## Affected Files/Areas

- `.github/workflows/sync-factory-state.yml`
- `docs/AGENT_FACTORY.md`
- `docs/FACTORY_STATE_MACHINE.md`
- `docs/AGENT_FACTORY_ANALYSIS.md`
- `.learnings/LEARNINGS.md`
- Any small helper or test surface added to make the sync behavior reproducible and reviewable

## Open Questions

- [ ] What is the lightest-weight reproducible test shape for this repo: a scripted manual smoke test, a workflow-dispatchable harness, or a small extracted helper with fixture-driven assertions? Can proceed.
- [ ] Does the investigation produce enough evidence to justify a narrower auth-path-specific resync hook later, or should that remain explicitly out of scope for this issue? Can proceed.
- [ ] Should the final cron land at 2 minutes or 5 minutes after the runner-cost review? Can proceed.

## Implementation Checklist

- [ ] Reproduce the currently observed drift path as far as practical from existing logs, workflow history, or a fresh smoke run, and note which `pull_request` event types and producer paths are affected.
- [ ] Tighten the scheduled reconcile cadence in `.github/workflows/sync-factory-state.yml` from `*/10` to the chosen 2 to 5 minute value, and update the inline workflow comments to match.
- [ ] Review the workflow's concurrency and reconcile behavior to ensure the shorter schedule does not create stale-overwrites or queue buildup.
- [ ] Add lightweight observability or debugging aids that help distinguish missed webhook delivery from downstream sync failure, keeping the workflow plain Actions and low complexity.
- [ ] Add the chosen repeatable test or smoke harness for PR open and close convergence within the cron window, and document how it should be run.
- [ ] Update `docs/AGENT_FACTORY.md` to document the expected board lag and the fact that reconcile is the safety net for missed PR events.
- [ ] Update `docs/FACTORY_STATE_MACHINE.md` and `docs/AGENT_FACTORY_ANALYSIS.md` anywhere they still state or imply a 10-minute reconcile window.
- [ ] Add a `.learnings/LEARNINGS.md` entry with `Pattern-Key: sync-factory-state-webhook-missed`, tied to the repeated misses observed on 2026-04-18.
- [ ] Verify the board converges for a PR open and close case within the new cron window without manual dispatch.

## Rejected Alternatives

**Only shorten the cron and skip the investigation**: Rejected. It reduces drift, but it leaves the team blind to whether the underlying GitHub event path is degrading further.

**Add explicit `workflow_dispatch` calls from every workflow that mutates a PR**: Rejected as the default direction. It broadens scope, duplicates responsibility, and still would not cover every producer path unless the investigation proves this is the only reliable option.

**Treat the 10-minute reconcile as good enough**: Rejected. The issue provides same-day evidence that this window is too large for both operator trust and automation correctness.

## Recommended implementer

**Choice**: copilot
**Rationale**: Auto-assignable via `implementer-dispatcher`. The work is bounded, but it spans a plain Actions workflow, board-state docs, and a learning artifact, so a plan file with a crisp checklist is the right handoff.
