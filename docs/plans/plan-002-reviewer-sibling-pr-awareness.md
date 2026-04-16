# Plan 002: Give reviewer sibling-PR awareness for multi-PR plans

**Source issue**: #62
**Status**: Ready for implementation

## Problem Statement

The reviewer workflow evaluates each PR against the full plan file in isolation. That breaks down when `/plan` splits one plan into multiple sibling PRs. The recent `plan-001` run showed the failure mode: PR #54 was marked `needs-changes` for criteria that were actually being implemented in sibling PRs #51, #52, #53, and #55.

This plan scopes the first fix to the reviewer workflow itself. The goal is to downgrade criteria already covered by sibling PRs from `Missed` to `Deferred`, and to keep those deferred items from forcing a false `needs-changes` verdict.

## Success Criteria

- Reviewer checks sibling PRs before classifying a criterion as `Missed` when the current PR is part of a multi-PR plan.
- Reviewer output uses `Deferred: covered by #NN` when another open or recently merged sibling PR covers the criterion.
- Reviewer output uses `Missed` only when neither the current PR nor any sibling PR covers the criterion.
- Reviewer does not emit `needs-changes` solely because of deferred items.
- The implementation includes one regression path for the multi-PR case, either a hand-crafted eval case or an equivalent workflow-level verification artifact that fits this repo.
- Workflow instructions stay local to the reviewer path for this first cut. Do not modify `intent-framed-agent` unless the reviewer-only approach proves insufficient.

## Risk Assessment

**Blast radius**: Medium. This changes review behavior for every PR evaluated by the `reviewer` workflow.
**Rollback**: Straightforward. Revert the reviewer workflow change and its compiled lock file.
**Risk**: The reviewer may misidentify unrelated PRs as siblings, or incorrectly treat partial overlap as full coverage. Mitigation: require explicit linkage to the same plan file, keep the sibling search bounded, and have the reviewer cite the covering PR number in the verdict.

## Affected Files/Areas

- `.github/workflows/reviewer.md` - add the sibling-PR cross-check step and update verdict guidance
- `.github/workflows/reviewer.lock.yml` - compiled workflow output after `gh aw compile reviewer`
- `.evals/` or another existing verification surface - add one regression path for the multi-PR case if the implementation chooses eval coverage
- `docs/AGENT_FACTORY.md` or adjacent workflow docs, only if reviewer behavior documentation needs to reflect the new `Deferred` state

## Open Questions

- [ ] What should count as "recently merged" for sibling lookup: a fixed PR recency window or only PRs still linked to the same plan? Can proceed. Pick a bounded rule during implementation and document it in the reviewer instructions.
- [ ] What is the lightest-weight regression artifact that fits this repo today: a hand-crafted eval case under `.evals/` or a workflow-focused verification fixture? Can proceed. Choose the path that can run in current CI without inventing a new test harness.

## Implementation Checklist

- [ ] Read the current reviewer workflow prompt and isolate the exact step where success criteria are classified.
- [ ] Define the sibling-discovery rule: same plan reference, open or bounded-recent merged state, and enough evidence in title, body, or diff to treat the PR as related.
- [ ] Update `.github/workflows/reviewer.md` so the reviewer cross-checks sibling PRs before labeling any criterion `Missed`.
- [ ] Update the review comment format guidance so criteria can be reported as `Deferred: covered by #NN` with brief evidence.
- [ ] Update verdict guidance so deferred items do not trigger `needs-changes` on their own.
- [ ] Recompile the workflow and commit the resulting `.github/workflows/reviewer.lock.yml`.
- [ ] Add one regression path for the multi-PR scenario using an existing repo mechanism, and document the coverage choice in the PR description.
- [ ] Confirm the new instructions still preserve the existing `Met`, `Partial`, `Missed`, and `Drifted` behavior for single-PR plans.

## Rejected Alternatives

**Option B, move the logic into `intent-framed-agent`**: Rejected for the first cut. The defect is in the reviewer workflow, and the skill explicitly says it is for coding-task execution, not planning-only or documentation-only work. Pushing review-specific cross-PR logic into that skill would widen the blast radius without proving the local fix first.

**Option C, create a `plan-progress-tracker` workflow**: Rejected for now. It adds a new stateful workflow, new coordination rules, and a bigger rollback surface. The issue asks for reviewer awareness, and the reviewer can likely solve the false-negative case without a new subsystem.

## Recommended implementer

**Choice**: claude-sonnet-4.6
**Rationale**: This is a bounded workflow change with medium blast radius, a clear first-cut approach, and a small number of affected files. Sonnet is the right default for a targeted prompt and verification update like this.
