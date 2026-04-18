# Plan 194: Raise eval-creator-ci visibility with a regression label

**Source issue**: #194
**Status**: Ready for implementation

## Problem Statement

`eval-creator-ci` currently posts an advisory comment on each PR, but it does not change routing state when evals fail. That makes a regression look like ordinary comment noise, even when every eval is red. The recent EVAL-001, EVAL-002, and EVAL-003 failures show the gap: the signal existed, but the factory did not surface it where a human already looks for action.

This plan follows the issue's recommended Option A. Add an `eval-regression` label path for failing eval runs, wire that label into the existing board-state mapping, and clear the label again when the eval signal returns to green so the board does not accumulate stale regressions.

## Interview Synthesis

The issue body is specific enough to simulate the planning interview:

- **Technical constraints**: Keep the eval workflow advisory. Reuse the existing label-driven factory control plane instead of opening a second notification channel. Update the workflow's safe outputs and compiled lock file together.
- **Scope boundaries**: Do Option A only. Do not add issue creation, do not change merge-gating behavior, and do not redesign the eval framework itself.
- **Risk tolerance**: Prefer a conservative change that increases visibility without adding alert spam. A stale regression label is worse than no label, so the clear-on-green path is part of the first cut.
- **Success signal**: A PR with one or more eval failures is visibly routed into the 👉 Your turn lane through `eval-regression`, the label disappears after a green rerun, and the docs describe the new label semantics.

## Success Criteria

- `eval-creator-ci` adds `eval-regression` to the PR when its own report detects one or more failed evals.
- `eval-creator-ci` removes `eval-regression` from the PR when a later run reports zero failed evals, so the label does not stick after the regression is fixed.
- The workflow remains advisory. It still posts the eval table comment and does not turn eval failures into a merge-blocking gate.
- The workflow source and `.github/workflows/eval-creator-ci.lock.yml` stay in sync after the prompt and safe-output changes.
- `sync-factory-state.yml` treats `eval-regression` as a 👉 Your turn signal with the same priority tier as `needs-changes`.
- `docs/FACTORY_STATE_MACHINE.md` documents `eval-regression` in both the label-to-lane mapping and the label reference table.
- Any adjacent factory documentation that would become inaccurate after the new label is added is updated in the same change, rather than leaving stale descriptions behind.
- The implementation includes one verification path that demonstrates the label is added on a failing eval run and cleared on a later green run.

## Risk Assessment

**Blast radius**: Medium. The change touches one PR workflow, the board-state mapper, and factory operator documentation.

**Rollback**: Straightforward. Revert the eval workflow changes, the board-state mapping, and the docs update.

**Primary risks and mitigations**

- A failure label that never clears would train humans to ignore the signal. Mitigation: treat add and remove as one feature, not two follow-up tasks.
- The workflow prompt may describe label behavior that the compiled lock file does not yet enforce. Mitigation: recompile `eval-creator-ci` in the same change and review the lock diff.
- The new label may not exist in the repository at implementation time. Mitigation: inspect the repo's current label-management path early and either add the bootstrap step to the change or document the one-time human setup explicitly.
- The board docs can drift from the workflow mapping. Mitigation: update `sync-factory-state.yml` and `docs/FACTORY_STATE_MACHINE.md` together, and check for any nearby docs that still list the old set of Your turn signals.

## Affected Files/Areas

- `.github/workflows/eval-creator-ci.md` - add failure-state labeling guidance and the clear-on-green rule
- `.github/workflows/eval-creator-ci.lock.yml` - compiled workflow output after `gh aw compile eval-creator-ci`
- `.github/workflows/sync-factory-state.yml` - include `eval-regression` in the Your turn priority rule
- `docs/FACTORY_STATE_MACHINE.md` - document the new label in the lane mapping and label tables
- `docs/AGENT_FACTORY.md` or another adjacent factory doc, only if its workflow inventory or label reference would otherwise become stale
- Repository label configuration or bootstrap path, if this repo manages labels as code rather than manual setup

## Open Questions

- [ ] How should the repository create the first `eval-regression` label: through an existing labels-as-code path, through a one-time scripted bootstrap, or through documented manual setup? Can proceed. Choose the smallest path already used in this repo.
- [ ] Should the eval workflow clear `eval-regression` only when `fail_count == 0`, or only when the workflow also has at least one passing eval? Can proceed. Default to clearing on `fail_count == 0` so a fully green rerun removes the stale signal.

## Implementation Checklist

- [ ] Inspect `.github/workflows/eval-creator-ci.md` and the compiled lock file to locate the current comment-only safe-output contract and the exact place where eval counts are summarized.
- [ ] Update the workflow frontmatter so `eval-creator-ci` can add `eval-regression` on failures and remove it on green reruns, while still posting exactly one eval-results comment.
- [ ] Update the workflow instructions so the agent treats `fail_count > 0` as a PR-label signal and treats `fail_count == 0` as the clear condition for any existing `eval-regression` label.
- [ ] Recompile the workflow so `.github/workflows/eval-creator-ci.lock.yml` matches the edited markdown source.
- [ ] Update `.github/workflows/sync-factory-state.yml` so `eval-regression` routes a PR into the 👉 Your turn lane at the same priority tier as `needs-changes`.
- [ ] Update `docs/FACTORY_STATE_MACHINE.md` to add `eval-regression` to the lane-mapping table and label reference.
- [ ] Search for nearby factory docs that enumerate reviewer or Your turn labels, and update only the references that would become wrong after the new label ships.
- [ ] Resolve the initial label bootstrap path so `eval-regression` exists before the first failing eval run tries to apply it.
- [ ] Verify the behavior with a controlled failing eval scenario, then rerun with a green fix and confirm the label clears.

## Rejected Alternatives

**Option B, open an issue when all evals fail**: Rejected for this first cut. The issue already identifies labels as the lower-noise path, and the factory already has board semantics for label-driven escalation.

**Only add the label, do not clear it automatically**: Rejected. A stale regression label would quickly become background noise and would undermine the visibility gain that motivated the change.

## Recommended implementer

**Choice**: copilot
**Rationale**: Auto-assignable via `implementer-dispatcher`. For manual hand-off to Claude or Codex, a human can swap the label on the source issue before merging the plan PR.
