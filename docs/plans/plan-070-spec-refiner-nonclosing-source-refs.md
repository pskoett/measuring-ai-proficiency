---
plan-id: plan-070
status: shipped
shipped-in: "#70"
---
# Plan 070: Keep source issues open when plan PRs merge

**Source issue**: #70
**Status**: Ready for implementation

## Problem Statement

`spec-refiner` creates plan PRs that can use a closing keyword such as `Closes #70` in the PR body. When a maintainer merges that plan PR, GitHub closes the source issue before `/plan` creates implementation sub-issues and before the actual fix ships. That breaks the parent issue's role as the tracking anchor for the rest of the factory.

The fix should make plan PRs reference the source issue without closing it. The source issue should stay open through the planning and implementation window, and the docs should say so explicitly.

## Success Criteria

- `spec-refiner` plan PRs reference the source issue without auto-closing it on merge.
- After a plan PR merges, the source issue remains `open`.
- `docs/AGENT_FACTORY.md` explains when the source issue is expected to close.
- No regression in how `/plan` and `implementer-dispatcher` find the parent issue.

## Risk Assessment

**Blast radius**: Medium. This changes the default handoff behavior for every future `spec-refiner` run.
**Rollback**: Trivial. Revert the workflow markdown change and the compiled lock file.
**Risk**: The workflow instructions and docs could drift, or the change could accidentally imply a broader parent-issue closing policy than intended. Mitigation: keep the implementation scoped to plan PR body language, recompile `spec-refiner.lock.yml`, and document that the actual parent-issue closing path is still separate.

## Affected Files/Areas

- `.github/workflows/spec-refiner.md` - Change the plan PR instructions to require a non-closing source issue reference such as `Refs #NN`.
- `.github/workflows/spec-refiner.lock.yml` - Recompile after editing the workflow markdown.
- `docs/AGENT_FACTORY.md` - Document that merging a plan PR should leave the source issue open, and explain that the source issue closes later in the implementation lifecycle.
- Factory integration check - Confirm `/plan` and `implementer-dispatcher` still rely on plan files, plan references, and parent issue links rather than PR closing keywords.

## Open Questions

None. The issue already chooses Option A and accepts a separate follow-up path for final parent-issue closure.

## Implementation Checklist

- [ ] Update `.github/workflows/spec-refiner.md` so the required PR body format uses a non-closing reference to the source issue, for example `Refs #NN`, instead of any closing keyword.
- [ ] Add a brief instruction in `.github/workflows/spec-refiner.md` that the source issue must remain open after the plan PR merges.
- [ ] Recompile the workflow so `.github/workflows/spec-refiner.lock.yml` stays in sync with the markdown source.
- [ ] Update `docs/AGENT_FACTORY.md` to state that the plan PR references the source issue without closing it, and that the source issue is expected to close only after implementation is complete.
- [ ] Search for any other plan-PR-specific guidance that still implies the plan PR closes the source issue, and fix only direct contradictions discovered during implementation.
- [ ] Verify the workflow still preserves the parent-issue discovery paths used by `/plan` and `implementer-dispatcher`.

## Rejected Alternatives

**Add parent-issue auto-close logic in the same change**: This bundles a workflow-policy bug fix with a new lifecycle automation feature. The issue explicitly prefers the simpler change first.

**Rely on implementation PR authors to close the parent issue manually without changing `spec-refiner`**: This leaves the early-close bug in place and keeps the bad default.

## Recommended implementer

**Choice**: claude-sonnet-4.6
**Rationale**: This is a focused workflow and docs change with medium blast radius, a short checklist, and a required compile step. Sonnet is the right default for this level of scoped factory maintenance work.
