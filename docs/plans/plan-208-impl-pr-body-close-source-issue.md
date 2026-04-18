---
plan-id: plan-208
status: shipped
shipped-in: "#208"
---
# Plan 208: impl PR body must close its source issue

**Source issue**: #208
**Status**: Ready for implementation

## Problem Statement

The factory now guards one half of the GitHub issue lifecycle. `spec-refiner` plan PRs are explicitly forbidden from using closing keywords against the source issue, and `EVAL-004` protects that rule. The opposite side is still missing: implementation PRs can merge without `Closes #NN`, `Fixes #NN`, or `Resolves #NN`, which leaves the source issue open after the work ships.

Issue #208 points at the recent failure on #187 for source issue #186. The code merged, but the issue had to be closed by hand. The next change should add a symmetric close-the-loop guard so bot-authored implementation PRs are flagged when they fail to close their source issue in the PR body.

## Interview Synthesis

**Technical constraints**
- Keep GitHub's native closing-keyword behavior for implementation PRs. The fix should enforce the existing convention, not replace it with a custom issue-closing path.
- Prefer the reviewer path over new eval machinery unless codebase exploration proves reviewer integration cannot support the check cleanly.
- Treat workflow source and compiled lock files as one unit. If `.github/workflows/reviewer.md` or `.github/workflows/pr-fix.md` changes, recompile the matching `.lock.yml` files.

**Scope boundaries**
- Scope the implementation to the close-the-loop guard for bot-authored implementation PRs and the follow-up remediation path in `/pr-fix`.
- Do not redesign the reviewer workflow beyond the minimum prompt and verdict logic needed for this check.
- Do not broaden this into a generic PR metadata framework unless the chosen path cannot satisfy the acceptance criteria.

**Risk tolerance**
- Prefer a deterministic, explicit check over soft guidance in prose.
- Accept a reviewer prompt expansion if it stays small and specific.
- Avoid changes that could make plan PRs start closing source issues again, or that block human-authored PRs unnecessarily.

**Success signal**
- Reviewer flags bot-authored implementation PRs that are missing a closing keyword for the source issue.
- The reviewer applies `needs-changes` with a concrete message that tells the implementer to add `Closes #NN` to the PR body.
- `/pr-fix` guidance makes adding the missing closing keyword an explicit repair path.
- The implementation includes a concrete validation path for a deliberately missing closing-keyword case.

## Decision

Implement the first version in the reviewer workflow, not as a new eval case.

The current repo already uses reviewer comments and verdict labels as the enforcement point for PR-quality failures. The issue's recommended path fits that model, and codebase exploration shows no existing eval that reads live PR bodies. Adding EVAL-005 would therefore require new verification plumbing on top of the actual rule. The reviewer path keeps the implementation smaller and aligns the failure with the workflow that already emits `needs-changes`.

## Success Criteria

- `.github/workflows/reviewer.md` instructs reviewer to detect missing closing keywords in bot-authored implementation PR bodies and treat the absence as a Critical finding.
- The reviewer guidance clearly scopes the check to implementation PRs, not plan PRs, using the existing `plan-file` label or equivalent PR metadata already available in the workflow.
- Reviewer verdict guidance makes the missing-closing-keyword case produce `needs-changes` with the explicit message: `impl PR must close its source issue. Add \`Closes #NN\` to the body.`
- `.github/workflows/reviewer.lock.yml` is recompiled from the updated workflow source.
- `.github/workflows/pr-fix.md` is updated so `/pr-fix` explicitly repairs missing PR-body closing keywords when reviewer identifies that failure.
- `.github/workflows/pr-fix.lock.yml` is recompiled from the updated workflow source.
- The implementation includes a repeatable validation path for a bot-authored implementation PR that intentionally omits the closing keyword, and the result demonstrates that reviewer would mark it `needs-changes`.

## Risk Assessment

**Blast radius**: Medium. The change touches shared PR review and PR-fix automation used across the factory.

**Rollback**: Moderate. Reverting the prompt and lock-file changes is straightforward, but a bad rule could create false-positive review failures on normal implementation PRs until reverted.

**Key risks and mitigations**
- **Risk**: Reviewer cannot reliably tell a plan PR from an implementation PR. **Mitigation**: anchor the rule to existing signals already documented in the repo, especially the `plan-file` label and bot-author detection, and make that branch of logic explicit in the prompt.
- **Risk**: The reviewer detects the problem but does not emit a concrete enough remediation message. **Mitigation**: include the exact required sentence in the workflow source instead of leaving wording to improvisation.
- **Risk**: `/pr-fix` still ignores reviewer findings about PR-body metadata and only focuses on code changes. **Mitigation**: update its workflow prompt to name missing `Closes #NN` as a supported repair case.
- **Risk**: Workflow source changes land without recompiling lock files. **Mitigation**: treat `gh aw compile reviewer` and `gh aw compile pr-fix` as required checklist items and review the lock diffs.

## Affected Files/Areas

- `.github/workflows/reviewer.md`: add the close-the-loop check, scope, and verdict wording.
- `.github/workflows/reviewer.lock.yml`: compiled reviewer workflow after `gh aw compile reviewer`.
- `.github/workflows/pr-fix.md`: add explicit instructions to repair missing `Closes #NN` in implementation PR bodies.
- `.github/workflows/pr-fix.lock.yml`: compiled `/pr-fix` workflow after `gh aw compile pr-fix`.
- Existing reviewer fixtures or documentation, if needed, to demonstrate and preserve the missing-closing-keyword validation path.

## Open Questions

No blocking questions from the issue context. Implementation can proceed without human input.

## Implementation Checklist

- [ ] Inspect the reviewer workflow's available PR metadata and identify the most reliable source-issue signal it can use when checking for closing keywords in bot-authored implementation PRs.
- [ ] Update `.github/workflows/reviewer.md` so the review process explicitly checks bot-authored implementation PR bodies for `Closes #NN`, `Fixes #NN`, or `Resolves #NN`, and skips that rule for plan PRs.
- [ ] Add the exact Critical finding text for the failure case: `impl PR must close its source issue. Add \`Closes #NN\` to the body.`
- [ ] Recompile `.github/workflows/reviewer.lock.yml` with `gh aw compile reviewer`.
- [ ] Update `.github/workflows/pr-fix.md` so `/pr-fix` treats missing closing keywords in the PR body as an expected reviewer-directed fix path.
- [ ] Recompile `.github/workflows/pr-fix.lock.yml` with `gh aw compile pr-fix`.
- [ ] Add or document a deliberate missing-closing-keyword validation case so maintainers can verify reviewer would return `needs-changes` for the exact failure in issue #208.
- [ ] Review the final diffs to confirm the new rule only targets bot-authored implementation PRs and does not interfere with the existing non-closing plan PR guard.

## Rejected Alternatives

**Add EVAL-005 first**: This is attractive as a durable regression artifact, but the current eval system is read-only and file-oriented. A new PR-body eval path would require extra machinery before it can enforce the actual rule. Start with the reviewer guard, then add an eval later if the team still wants a second line of defense.

## Recommended implementer

**Choice**: copilot
**Rationale**: Auto-assignable via `implementer-dispatcher`. The implementation is a focused workflow-maintenance change with a clear checklist and existing reviewer and `/pr-fix` patterns to extend.
