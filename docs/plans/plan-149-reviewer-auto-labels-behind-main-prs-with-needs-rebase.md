---
plan-id: plan-149
status: shipped
shipped-in: "#149"
---
# Plan 149: Reviewer auto-labels behind-main PRs with `needs-rebase`

**Source issue**: #149
**Status**: Ready for implementation

## Problem Statement

PRs can fall behind `main` while they sit in the factory. The repo already has a `conflict-resolver` path, but it depends on a human noticing the stale-branch banner and applying `needs-rebase` by hand.

This change should teach `reviewer` to detect that condition during its normal PR pass, add `needs-rebase` when the branch is behind, and still complete the review comment and verdict in the same run.

## Interview Synthesis

The issue body provides enough specificity to simulate the planning interview:

**Technical constraints**
- Read the PR merge state once per reviewer run from the existing PR context. Prefer the GitHub pull request toolset over shelling out to `gh`.
- Run the behind-main check before the normal review steps so the label is available as early as possible in the workflow.
- Extend the reviewer workflow's safe-output label allowlist to include `needs-rebase`.

**Scope boundaries**
- Keep the automation inside `reviewer.md`. Do not add a second polling workflow.
- Do not change `conflict-resolver` behavior.
- Do not let the rebase check replace or short-circuit the review comment and verdict.

**Risk tolerance**
- Prefer the smallest workflow change that preserves the existing choreography through labels.
- Accept a conservative check that labels only when the PR is clearly `BEHIND`.
- Avoid label churn on clean PRs or ambiguous states.

**Success signal**
- Reviewer reads merge state once, labels `needs-rebase` only for behind branches, still posts its normal verdict comment, and the factory docs describe reviewer as a setter for that label.

## Success Criteria

- `reviewer.md` reads the PR merge state exactly once per run before the main review flow.
- The reviewer workflow's safe-output `add-labels.allowed` list includes `needs-rebase`.
- When the PR merge state is `BEHIND`, reviewer applies `needs-rebase`.
- When the PR is not `BEHIND`, reviewer does not add `needs-rebase`.
- Reviewer still posts its normal structured verdict comment regardless of rebase state.
- The reviewer comment notes when `needs-rebase` was applied so operators understand why `conflict-resolver` will run next.
- `.github/workflows/reviewer.lock.yml` is recompiled from the updated workflow source.
- `docs/AGENT_FACTORY.md` states that reviewer, not only a human, can set `needs-rebase`.

## Risk Assessment

**Blast radius**: Medium. This is one workflow and one doc update, but it changes behavior on every reviewed PR and can trigger branch-mutation automation downstream.

**Rollback**: Low. Revert the reviewer workflow, its compiled lock file, and the doc update.

**Primary risks and mitigations**

- Wrong merge-state field or state mapping causes false positives. Mitigation: inspect the existing PR metadata surface first, then gate labeling strictly on `BEHIND`.
- Labeling logic accidentally bypasses the review verdict path. Mitigation: place the check as an additive pre-step and keep the existing comment path unchanged.
- Safe-output validation fails because `needs-rebase` is not allowlisted. Mitigation: update the workflow frontmatter and compile the lock file in the same change.
- Docs drift from behavior. Mitigation: update the label reference and any reviewer-related wording in the same PR.

## Affected Files/Areas

- `.github/workflows/reviewer.md`: add the behind-main detection step, allow `needs-rebase`, and mention label application in the review comment path.
- `.github/workflows/reviewer.lock.yml`: compiled workflow artifact from `gh aw compile reviewer`.
- `docs/AGENT_FACTORY.md`: update the label reference and reviewer workflow description to reflect automatic `needs-rebase` labeling.

## Open Questions

None. The issue body fixes the trigger, the desired label contract, the out-of-scope items, and the doc target well enough to proceed.

## Implementation Checklist

- [ ] Inspect the reviewer workflow's current PR-reading path and confirm which GitHub tool call exposes the merge state cleanly.
- [ ] Add a pre-review step in `.github/workflows/reviewer.md` that reads merge state once and records whether the PR is `BEHIND`.
- [ ] Extend `safe-outputs.add-labels.allowed` in `reviewer.md` to include `needs-rebase` without changing the existing verdict labels.
- [ ] When the PR is `BEHIND`, apply `needs-rebase` as an additive label and continue with the rest of the review flow.
- [ ] Update the required reviewer comment structure so it notes that `needs-rebase` was applied when relevant, while keeping the normal verdict section intact.
- [ ] Leave clean PRs unchanged so reviewer does not add labels for non-`BEHIND` merge states.
- [ ] Recompile the workflow with `gh aw compile reviewer` and commit the generated `.github/workflows/reviewer.lock.yml`.
- [ ] Update `docs/AGENT_FACTORY.md` so the label reference and workflow narrative say reviewer can set `needs-rebase`.
- [ ] Run the existing repo validation used for workflow and documentation changes after the edits land.

## Rejected Alternatives

**A separate scheduled workflow that scans all open PRs for behind-main state**: Rejected. The issue explicitly rejects the extra workflow and runner cost for a check reviewer can do while it already has PR context.

**Trigger `conflict-resolver` directly from reviewer without the `needs-rebase` label**: Rejected. The issue explicitly keeps labels as the handoff mechanism between workflows.

## Recommended implementer

**Choice**: claude-sonnet-4.6
**Rationale**: This is a scoped workflow change plus a doc update, but it still affects every reviewer run and must preserve the existing verdict path exactly. That is a medium blast-radius fit for Claude Sonnet.
