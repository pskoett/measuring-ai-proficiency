# Plan 136: Remove the sub-issue layer from the factory chain

**Source issue**: #136
**Status**: Ready for implementation

## Problem Statement

The factory still carries a planning and dispatch layer that was designed for multi-issue fan-out. That layer no longer matches how this repo operates.

Issue #135 already collapsed `/plan` output to one consolidated sub-issue. `impl:copilot` is now the only auto-routable implementer label. The remaining sub-issue machinery adds labels, workflows, and failure modes without adding routing or parallelism value.

This change removes that extra layer and makes the original issue the unit of work from spec refinement through implementation.

## Interview Synthesis

**Technical constraints**
- Keep the source issue open as the durable work anchor until the implementation PR ships.
- Preserve the current plan-file contract in `docs/plans/plan-NNN-<slug>.md` so `spec-refiner` and `reviewer` still share one source of truth.
- When the merged plan activates implementation, update the original issue body surgically. Preserve the issue narrative and insert or refresh the implementation checklist in a stable section rather than replacing the whole body.
- Recompile every edited gh-aw workflow so `.md` and `.lock.yml` stay in sync.

**Scope boundaries**
- Remove the `/plan` sub-issue creation step and the parent-issue discovery logic that exists only because of sub-issues.
- Keep single-issue routing through `impl:copilot`. Do not revive `impl:claude-*` or `impl:codex` auto-assignment.
- Do not redesign unrelated workflows or the broader label taxonomy beyond what this chain simplification requires.
- Treat truly parallel work as a separate issue-splitting decision made by humans before spec refinement, not as a responsibility of the default factory path.

**Risk tolerance**
- Prefer a direct, explicit handoff over compatibility shims that keep dead sub-issue paths half-alive.
- Accept targeted workflow restructuring across several files if it removes recurring failure modes and simplifies operator mental load.
- Preserve rollback clarity. The new path should be easy to reason about and easy to revert if plan activation or issue-body mutation misbehaves.

**Success signal**
- A `needs-spec` issue produces one plan PR and no implementation sub-issue.
- Merging that plan PR writes the implementation checklist onto the original issue and moves the issue to `ready-for-implementation`.
- `implementer-dispatcher` assigns Copilot directly from the original issue.
- Reviewer logic no longer accounts for sibling PRs created by `/plan`.

## Success Criteria

- `spec-refiner` still creates exactly one plan PR for a `needs-spec` issue, and that PR references the source issue with `Refs #136` rather than a closing keyword.
- Merging the plan PR activates the original issue directly. The issue body gains a stable implementation-checklist section derived from the plan file without destroying the original problem statement.
- The source issue loses `needs-plan` and gains `ready-for-implementation` after successful plan activation.
- No intermediate task issue is created anywhere in the default chain.
- `implementer-dispatcher` runs against the original issue, reads its own `impl:*` label, and assigns Copilot without any parent-issue lookup path.
- Reviewer no longer performs sibling-PR discovery or defers criteria to sibling PRs.
- The obsolete `/plan` workflow is removed or reduced to an inert compatibility stub that cannot create new work items.
- Factory docs and shared harness guidance describe the single-issue flow accurately.

## Risk Assessment

**Blast radius**: High. This changes the default lifecycle of every spec-refined issue and touches workflow triggers, issue-body mutation, reviewer assumptions, and operator docs.

**Rollback**: Moderate. Revert the plan-activation handoff, restore `/plan` and the old dispatcher assumptions, and recompile the affected workflow lock files.

**Risk**: The highest risk is breaking the handoff between plan approval and implementation, either by failing to project the checklist onto the source issue, applying `ready-for-implementation` too early, or leaving reviewer and docs logic partially on the old model. Mitigation: make one workflow the sole owner of the post-merge activation step, use a stable issue-body island for checklist updates, keep dispatcher logic single-path, and update every doc surface that currently describes sub-issues as the default.

## Affected Files/Areas

- `.github/workflows/spec-refiner.md` and `.github/workflows/spec-refiner.lock.yml` to keep plan creation and label handoff wording aligned with the new chain.
- A new plan-activation workflow in `.github/workflows/` plus its compiled `.lock.yml` to react to merged plan PRs, project the checklist onto the original issue, and add `ready-for-implementation`.
- `.github/workflows/implementer-dispatcher.md` and `.github/workflows/implementer-dispatcher.lock.yml` to dispatch from the original issue instead of discovering a parent.
- `.github/workflows/reviewer.md` and `.github/workflows/reviewer.lock.yml` to delete sibling-PR discovery and any deferred-criterion logic tied to multi-PR plans.
- `.github/workflows/plan.md` and `.github/workflows/plan.lock.yml` to delete or stub the sub-issue workflow.
- `docs/AGENT_FACTORY.md`, `docs/chain.md`, and `AGENTS.md` to document the new single-issue lifecycle.
- `CLAUDE.md` and `.github/copilot-instructions.md` if they still describe sub-issues or manual `/plan` progression as the standard flow.

## Open Questions

None. The issue already chooses the direction: remove the sub-issue layer, route directly from the original issue, and keep multi-agent parallelism out of the default path.

## Implementation Checklist

- [ ] Trace the current `needs-spec` to implementation path across `spec-refiner`, `/plan`, `implementer-dispatcher`, and `reviewer`, and identify every place that assumes sub-issues or sibling PRs exist.
- [ ] Introduce one post-merge workflow that activates a merged plan PR by locating the source issue, extracting the plan checklist, updating a stable checklist section on the original issue body, removing `needs-plan`, and adding `ready-for-implementation`.
- [ ] Decide whether `spec-refiner` itself or the new activation workflow owns any remaining label transitions, then keep that ownership single-path and explicit in workflow instructions.
- [ ] Simplify `implementer-dispatcher` so it triggers on the original issue's `ready-for-implementation` label, skips parent discovery entirely, and preserves the existing `impl:copilot` versus manual-label behavior.
- [ ] Remove `/plan` from the active chain, either by deleting the workflow and compiled lock file or replacing it with a clearly inert compatibility stub that cannot create sub-issues.
- [ ] Remove reviewer sibling-PR discovery, deferred-criterion handling, and any wording that assumes one plan can map to several concurrent PRs.
- [ ] Update docs and harness files to describe the new chain: original issue, plan PR, merged-plan activation, direct dispatch, one implementation PR.
- [ ] Recompile every changed workflow with `gh aw compile`, and make sure deleted workflows do not leave stale compiled artifacts behind.
- [ ] Validate the end-to-end state model against the acceptance criteria in issue #136, especially "one plan PR, zero intermediate issues."

## Rejected Alternatives

**Keep `/plan`, but force it to emit exactly one sub-issue forever**: Rejected. That preserves the overhead and failure modes that this issue is trying to remove.

**Teach `implementer-dispatcher` more fallback parent-discovery strategies**: Rejected. Parent discovery is the accidental complexity created by sub-issues. Improving it would harden the wrong abstraction.

**Leave reviewer sibling-PR logic in place as a harmless fallback**: Rejected. Dead workflow assumptions create maintenance drag and increase the chance of future false positives when the chain changes again.

## Recommended implementer

**Choice**: copilot
**Rationale**: Auto-assignable via `implementer-dispatcher`. For manual hand-off to Claude or Codex, a human can swap the label on the source issue before merging the plan PR.
