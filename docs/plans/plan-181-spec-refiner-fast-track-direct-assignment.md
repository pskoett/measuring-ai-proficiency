# Plan 181: Spec-refiner fast-track direct assignment

**Source issue**: #181
**Status**: Ready for implementation

## Problem Statement

`spec-refiner` now has a direct-route path for simple, clearly bounded issues. That path adds `impl:copilot` and `ready-for-implementation` on the source issue without opening a plan PR.

The handoff stalls because those labels are applied through gh-aw safe outputs, which run under `GITHUB_TOKEN`. GitHub does not let `GITHUB_TOKEN`-attributed label events trigger downstream workflows. The issue lands in the right visible state, but `implementer-dispatcher` never runs, Copilot is never assigned, and the factory needs a human to toggle the label again.

## Interview Synthesis

**Technical constraints**
- Keep the existing plan-worthy path intact. `plan-merged-dispatcher` already uses `GH_AW_AGENT_TOKEN` and should continue to hand off through `ready-for-implementation`.
- Reuse the factory's existing Copilot assignment primitive, `assign-to-agent`, instead of introducing a second assignment mechanism.
- Stay within the current routing reality: only `impl:copilot` is auto-assignable today.
- Update workflow source and compiled lock output together.

**Scope boundaries**
- Fix the broken fast-track path end to end.
- Preserve the merged-plan path unless a directly related documentation correction is needed.
- Do not redesign `implementer-dispatcher` into a broad state reconciler in this change.
- Do not add a new label taxonomy.

**Risk tolerance**
- Prefer the smallest deterministic fix over a larger resilience project.
- Accept a little duplication between fast-track assignment and dispatcher assignment if it removes the anti-loop dependency.
- Avoid solutions that depend on undocumented safe-output targeting behavior for scheduled runs.

**Success signal**
- A direct-route issue from `spec-refiner` is assigned to Copilot in the same workflow run, with no dependence on a downstream label-triggered cascade.
- The regular plan-merge path still hands off through `plan-merged-dispatcher` and `implementer-dispatcher`.
- Factory docs clearly distinguish the two assignment paths so operators know what to expect.

## Decision

Adopt **direct Copilot assignment inside `spec-refiner` for the fast-track path**.

On the direct-route branch, `spec-refiner` should:

1. Remove `needs-spec`.
2. Add `impl:copilot`, `ready-for-implementation`, and `assigned-to-agent`.
3. Call `assign-to-agent` for Copilot in the same run.
4. Post a short comment that the issue was fast-tracked and assigned directly.

Keep `implementer-dispatcher` as the assignment path for the plan-worthy flow that comes through `plan-merged-dispatcher`.

This removes the failing dependency on a `GITHUB_TOKEN` label event without turning `implementer-dispatcher` into a scheduled sweeper. It also keeps the fix local to the workflow that introduced the broken fast-track branch.

## Success Criteria

- `spec-refiner` can complete the fast-track path without relying on `ready-for-implementation` to trigger `implementer-dispatcher`.
- A fast-tracked issue ends the `spec-refiner` run with Copilot assigned and the source issue labeled `assigned-to-agent`.
- The plan-worthy path continues to route through `plan-merged-dispatcher` and `implementer-dispatcher` unchanged.
- `.github/workflows/spec-refiner.lock.yml` is recompiled so runtime behavior matches the updated markdown source.
- Directly related factory documentation and shared guidance no longer claim that every direct-route issue is picked up by `implementer-dispatcher`.

## Risk Assessment

**Blast radius**: Medium. The change touches one factory workflow's behavior and any docs that describe direct-route dispatch semantics.

**Rollback**: Moderate. Reverting the workflow and docs is easy, but it would reintroduce the current fast-track stall.

**Key risks and mitigations**
- **Risk**: Fast-track and plan-worthy assignment paths drift apart over time. **Mitigation**: keep the direct-route branch narrow, reuse the same `assign-to-agent` primitive, and update the docs so the split is explicit.
- **Risk**: `spec-refiner` forgets to add the visible provenance label after assignment. **Mitigation**: treat `assigned-to-agent` as part of the same fast-track checklist, not an optional follow-up.
- **Risk**: Workflow source changes without a lock recompile leave runtime behavior stale. **Mitigation**: recompile immediately and review the lock diff.

## Affected Files/Areas

- `.github/workflows/spec-refiner.md`: add `assign-to-agent` to safe outputs and change the direct-route instructions from "label-only handoff" to "assign in place."
- `.github/workflows/spec-refiner.lock.yml`: compiled workflow output after the source change.
- `docs/AGENT_FACTORY.md`: update the quick-start and dispatcher sections so direct-route issues are described as assigned by `spec-refiner`, not by a downstream cascade.
- `docs/chain.md`: refresh the direct-route branch in the flow narrative.
- `docs/FACTORY_STATE_MACHINE.md`: update the trigger table and happy-path sequence where they currently imply a single assignment path.
- `AGENTS.md`, `CLAUDE.md`, and `.claude/skills/use-agent-factory/SKILL.md`: align shared factory guidance if it still says direct-route issues are picked up by `implementer-dispatcher`.

## Open Questions

None at plan time. The issue already frames the decision space, and the direct-assignment approach is actionable without extra human input.

## Implementation Checklist

- [ ] Update `.github/workflows/spec-refiner.md` so its direct-route branch assigns Copilot in the same run instead of depending on a label-triggered cascade.
- [ ] Extend the workflow's safe-output configuration to allow `assign-to-agent` and the `assigned-to-agent` label on the fast-track path.
- [ ] Tighten the direct-route comment and handoff text so the issue history clearly shows that assignment happened inside `spec-refiner`.
- [ ] Recompile `.github/workflows/spec-refiner.lock.yml` after the markdown workflow change.
- [ ] Search the repo for guidance that says direct-route issues are picked up by `implementer-dispatcher`, then update only the files that actively describe that behavior.
- [ ] Verify the plan-worthy path documentation still describes `plan-merged-dispatcher` followed by `implementer-dispatcher`.
- [ ] Run the repo's existing verification command set after the workflow and documentation changes land.

## Rejected Alternatives

**Custom PAT-backed label mutation inside `spec-refiner`**: This stays closer to the current choreography, but it pushes the workflow toward bespoke shell logic just to work around safe-output semantics. Direct assignment is simpler and uses an existing supported primitive.

**Scheduled reconcile in `implementer-dispatcher`**: This is a valid resilience enhancement, but it broadens scope into multi-item recovery, scheduled execution, and dispatcher targeting semantics. The issue's confirmed failure can be solved without that extra surface.

## Recommended implementer

**Choice**: copilot
**Rationale**: Auto-assignable via the existing factory primitives. The implementation is a focused workflow-and-docs change with a concrete checklist and no unresolved design work left after this plan.
