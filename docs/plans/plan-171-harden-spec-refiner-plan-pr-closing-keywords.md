---
plan-id: plan-171
status: shipped
shipped-in: "#171"
---
# Plan 171: Harden spec-refiner plan PR bodies against closing keywords

**Source issue**: #171
**Status**: Ready for implementation

## Problem Statement

Plan PRs must keep the source issue open through the planning handoff. Issue #171 documents a recent failure where merged plan PR #164 included `Fixes #161` in its body, which caused GitHub to auto-close source issue #161 and stalled the factory until a human reopened it.

The factory already intends plan PRs to use `Refs #NN` only. The current guardrail was not strong enough. The next change should add defense in depth so the bad PR-body pattern is harder to generate, and the factory can recover automatically if it happens again.

## Interview Synthesis

**Technical constraints**
- Preserve GitHub closing-keyword behavior for normal implementation PRs. The fix is specific to plan PRs.
- Keep the current plan handoff model intact: plan PR merges, the source issue stays open, `plan-merged-dispatcher` writes the checklist, and `implementer-dispatcher` activates from labels.
- Treat workflow sources and directly related skill or doc guidance as the control plane. Recompile workflow lock files when workflow markdown changes.

**Scope boundaries**
- Focus on plan PR creation and plan-merge recovery paths.
- Include a retrospective audit path for already merged plan PRs, but do not turn this into a broad workflow redesign.
- Do not change unrelated plan PR body content requirements beyond the closing-keyword protection.

**Risk tolerance**
- Prefer deterministic guardrails over prompt wording alone.
- Favor a small number of high-signal changes over a larger review-layer expansion.
- Avoid changes that would interfere with normal issue-closing behavior for implementation PRs.

**Success signal**
- A future spec-refiner run should produce a plan PR body that references the source issue with `Refs #NN` and never uses `Closes`, `Fixes`, or `Resolves` against that issue.
- If a bad plan PR body still slips through and the source issue closes on merge, the factory should reopen the issue during the dispatcher cycle and leave a visible warning.
- Historical merged plan PRs should be auditable so orphaned source issues can be found and corrected.

## Success Criteria

- `.github/workflows/spec-refiner.md` makes the prohibition explicit and prominent: plan PR bodies must use `Refs #NN` for the source issue and must never contain `Closes`, `Fixes`, or `Resolves` targeting that issue anywhere in the body.
- `.github/workflows/spec-refiner.lock.yml` is recompiled so the runtime prompt matches the markdown source.
- `plan-merged-dispatcher` gains a defensive recovery step: after applying the checklist and labels, it checks whether the source issue is closed and, if so, reopens it and leaves a warning comment that points at the merged plan PR body problem.
- Directly contradictory factory guidance discovered during implementation is aligned with the non-closing plan PR rule.
- The implementation includes a retrospective audit pass, or a durable scripted procedure, for merged plan PRs so maintainers can identify any past source issues that were auto-closed by the same mistake.
- The change does not alter GitHub's normal closing-keyword behavior for implementation PRs.

## Risk Assessment

**Blast radius**: Medium. The change touches factory workflow behavior that applies to every future plan PR.

**Rollback**: Moderate. Prompt-only changes are easy to revert. Dispatcher reopen logic is also reversible, but it affects issue state transitions and should be backed out carefully if it misfires.

**Key risks and mitigations**
- **Risk**: Prompt wording changes without a compiled lock update leave runtime behavior unchanged. **Mitigation**: recompile the workflow and review the lock diff.
- **Risk**: Reopen logic could reopen the wrong issue or produce duplicate warning comments. **Mitigation**: derive the issue number from the plan filename as the dispatcher already does, keep the reopen path scoped to closed source issues only, and make the warning message clearly plan-specific.
- **Risk**: Contradictory guidance elsewhere in the repo could reintroduce the bug later. **Mitigation**: search for direct contradictions to the non-closing plan PR rule and fix only the ones that actively conflict with the intended behavior.
- **Risk**: Historical audit work could become open-ended. **Mitigation**: scope it to merged plan PRs and the specific closing-keyword pattern against their paired source issues.

## Affected Files/Areas

- `.github/workflows/spec-refiner.md`: strengthen the plan PR body instruction so the ban on closing keywords is explicit and hard to miss.
- `.github/workflows/spec-refiner.lock.yml`: compiled workflow output that must stay in sync with the source prompt.
- `.github/workflows/plan-merged-dispatcher.yml`: add self-correction for source issues that were auto-closed by a merged plan PR.
- Directly related factory guidance, if contradictory text is found during implementation, for example `.claude/skills/use-agent-factory/SKILL.md`.
- GitHub history for merged `plan-file` PRs: source material for the retrospective audit.

## Open Questions

No unresolved questions from the issue context. Implementation can proceed without human input.

## Implementation Checklist

- [ ] Update `.github/workflows/spec-refiner.md` so the plan PR body instruction uses a prominent negative rule: `Refs #NN` for the source issue, never `Closes`, `Fixes`, or `Resolves` anywhere in the plan PR body for that issue.
- [ ] Recompile the workflow so `.github/workflows/spec-refiner.lock.yml` matches the updated source prompt.
- [ ] Extend `.github/workflows/plan-merged-dispatcher.yml` so it checks the source issue state after applying the checklist and labels, reopens the issue if GitHub auto-closed it, and posts a warning that identifies the plan-PR-body failure mode.
- [ ] Search the repo for direct contradictions to the non-closing plan PR rule and fix only the guidance that would mislead future agents or operators.
- [ ] Run a retrospective audit over merged plan PRs to find any source issues that were auto-closed by closing keywords in plan PR bodies.
- [ ] Document the audit result in the implementation PR summary, and reopen or file a follow-up for any affected source issues discovered during that audit.
- [ ] Verify the final behavior still preserves the factory's intended handoff: merged plan PR keeps the source issue open, dispatcher writes the checklist, and implementation routing still depends on labels rather than PR closing semantics.

## Rejected Alternatives

**Add the reviewer-side check as the primary defense**: Reviewer can detect a bad plan PR body, but it runs later, adds another workflow hop, and changes to reviewer trigger the self-tamper guard. Keep the first implementation focused on the direct creation path plus dispatcher recovery.

**Disable closing keywords globally**: This would fix the symptom by removing useful GitHub behavior from normal implementation PRs. The issue explicitly rejects that direction.

## Recommended implementer

**Choice**: copilot
**Rationale**: Auto-assignable via `implementer-dispatcher`. This is a focused factory-maintenance change with a clear checklist and existing workflow patterns to follow, so Copilot is the correct default path.
