---
plan-id: plan-234
status: active
---
# Plan 234: Auto-activate issues when `needs-plan` is applied directly

**Source issue**: #234
**Status**: Ready for implementation

## Problem Statement

The factory docs advertise a manual shortcut: skip `needs-spec` and label an issue `needs-plan` directly. Today that shortcut is dead. No workflow listens for a manually applied `needs-plan` label on an issue, so the issue stalls unless it came from a merged plan PR.

This issue re-files the previously attempted fix from closed PR #225 against current `main`, after several shared-harness docs were rewritten and made the earlier branch structurally unmergeable. The new plan should preserve the intended `trigger-plan.yml` design while rebasing the doc edits onto the live factory docs.

## Interview Synthesis

The issue body and the closed PR #225 description provide enough detail to simulate the planning interview without additional human input.

### Technical constraints

- Add a new plain GitHub Actions workflow at `.github/workflows/trigger-plan.yml`. Do not model this as a gh-aw workflow.
- Reuse the workflow shape from closed PR #225 instead of re-deriving a new trigger model.
- Preserve the existing factory boundary where `ready-for-implementation` is the handoff into `implementer-dispatcher`. The new workflow must use a PAT-capable path so the downstream dispatch still fires.
- Reuse the same plan-checklist marker format as `plan-merged-dispatcher` when a merged plan file already exists and needs recovery activation.

### Scope boundaries

- Cover the new workflow plus the directly affected documentation updates only.
- Keep the docs edits paragraph-level and limited to the specific contradictory rows or chain descriptions called out in the issue.
- Update `AGENTS.md` and `CLAUDE.md` because their current factory overview still says there is only one plain GitHub Actions workflow.
- Do not broaden this issue into unrelated factory cleanup, plan-format changes, or workflow redesign.

### Risk tolerance

- Prefer a small, reversible wrapper workflow over changes to the existing gh-aw workflows.
- Accept modest guard logic if it keeps the new trigger idempotent and prevents accidental double-activation.
- Avoid duplicate activation paths when a plan PR is still open or `plan-merged-dispatcher` already owns the issue.

### Success signal

- Applying `needs-plan` directly to an issue produces the same observable end state as the intended shortcut: the issue reaches `assigned-to-agent` and Copilot is assigned promptly.
- The new workflow coexists cleanly with `plan-merged-dispatcher` and `implementer-dispatcher`.
- `docs/AGENT_FACTORY.md`, `docs/FACTORY_STATE_MACHINE.md`, `docs/chain.md`, `AGENTS.md`, and `CLAUDE.md` all describe the shortcut accurately after the change.

## Decision Frame

Implement `trigger-plan.yml` as the manual-label side branch for the factory:

1. If a merged plan file for the issue already exists on `main`, recover the normal plan activation flow by copying the implementation checklist into the source issue body with the same delimited marker format used by `plan-merged-dispatcher`, then transition the issue into dispatch.
2. If no plan file exists and the issue was labeled `needs-plan` as a deliberate skip-spec shortcut, transition it directly into dispatch with `impl:copilot` and `ready-for-implementation`.
3. If no plan file exists but the issue still carries the signal that spec refinement has already happened and a plan PR is still in flight, leave the issue alone so the merge-time dispatcher remains the sole owner of that path.

This keeps the new workflow aligned with the closed #225 design and avoids teaching multiple workflows to make conflicting decisions about the same issue.

## Success Criteria

- `.github/workflows/trigger-plan.yml` exists and listens for `issues: [labeled]`.
- The workflow reacts only when the applied label is `needs-plan`.
- The workflow guards against closed issues, `human-review`, and already-activated issues so reruns are safe.
- When a merged plan file exists, the workflow writes the `## Implementation Checklist` into the source issue body using the same marker contract as `plan-merged-dispatcher`, then removes `needs-plan` and adds `ready-for-implementation`.
- When no plan file exists and the issue is using the manual skip-spec shortcut, the workflow removes `needs-plan`, ensures `impl:copilot`, and adds `ready-for-implementation` in a way that still cascades into `implementer-dispatcher`.
- The issue reaches `assigned-to-agent` and Copilot assignment within the expected downstream window after the manual `needs-plan` shortcut is used.
- `docs/AGENT_FACTORY.md`, `docs/FACTORY_STATE_MACHINE.md`, `docs/chain.md`, `AGENTS.md`, and `CLAUDE.md` contain consistent, current wording about the shortcut and the added plain Actions workflow.

## Risk Assessment

**Blast radius**: Medium. This changes the activation path for any issue that a human labels `needs-plan` directly, and it touches shared factory documentation.

**Rollback**: Straightforward. Revert `trigger-plan.yml` and the paragraph-level doc updates.

**Key risks and mitigations**

- **Risk**: The new workflow could race with `plan-merged-dispatcher` or activate an issue twice. **Mitigation**: add explicit guards for already-active issues and preserve the "plan PR still open" branch from #225.
- **Risk**: The shortcut could add labels without triggering downstream dispatch if the wrong token path is used. **Mitigation**: use the PAT-backed edit path already proven by the existing dispatcher workflow.
- **Risk**: The docs could drift again because several files describe the chain in different ways. **Mitigation**: update only the directly contradictory rows and one-line overviews, and verify the wording stays consistent across all touched docs.

## Affected Files/Areas

- `.github/workflows/trigger-plan.yml`
- `.github/workflows/plan-merged-dispatcher.yml` as the behavior reference for checklist marker format and activation semantics
- `.github/workflows/implementer-dispatcher.md` as the downstream contract that consumes `ready-for-implementation`
- `docs/AGENT_FACTORY.md`
- `docs/FACTORY_STATE_MACHINE.md`
- `docs/chain.md`
- `AGENTS.md`
- `CLAUDE.md`

## Open Questions

None. The issue body plus closed PR #225 define the intended workflow shape tightly enough to proceed.

## Implementation Checklist

- [ ] Confirm the exact contradictory factory-doc text on current `main`, including whether `AGENTS.md` and `CLAUDE.md` now need one-line updates because they still describe only one plain Actions workflow.
- [ ] Add `.github/workflows/trigger-plan.yml` as a plain GitHub Actions workflow on `issues: [labeled]`, gated to the `needs-plan` label.
- [ ] Implement the guard conditions from the prior design: skip closed issues, issues labeled `human-review`, and issues already past the activation stage.
- [ ] Reuse the closed #225 three-path behavior so the workflow can distinguish merged-plan recovery, manual skip-spec activation, and the "plan PR still in flight" case.
- [ ] Reuse the same issue-body checklist markers as `plan-merged-dispatcher` when activating from an existing merged plan file.
- [ ] Ensure the workflow uses the PAT-backed edit path that allows the `ready-for-implementation` label event to cascade into `implementer-dispatcher`.
- [ ] Update only the targeted paragraphs in `docs/AGENT_FACTORY.md`, `docs/FACTORY_STATE_MACHINE.md`, `docs/chain.md`, `AGENTS.md`, and `CLAUDE.md` so they describe the shortcut as live and mention the added plain Actions workflow.
- [ ] Verify the end-to-end handoff: applying `needs-plan` directly leads to `assigned-to-agent` and Copilot assignment via the existing dispatcher path.

## Rejected Alternatives

**Leave the shortcut undocumented in practice**: Rejected. The current state teaches an operator action that silently does nothing.

**Patch `spec-refiner` or `implementer-dispatcher` instead of adding a new listener**: Rejected. Neither workflow listens for manually applied `needs-plan`, so that does not solve the trigger gap.

**Broaden the change into a larger factory-routing redesign**: Rejected. The issue asks for a targeted recovery of a documented shortcut, not a new dispatch model.

## Recommended implementer

**Choice**: copilot
**Rationale**: Auto-assignable via `implementer-dispatcher`. The implementation is bounded but touches one new workflow plus a handful of shared docs, so a clear checklist and the existing factory handoff are enough.
