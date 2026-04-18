# Plan 204: Broaden `pr-fix` allowed-files for reviewer follow-ups

**Source issue**: #204
**Status**: Ready for implementation

## Problem Statement

`/pr-fix` can generate the right patch for a PR review, then fail at the final push because its `safe-outputs.push-to-pull-request-branch.allowed-files` list is narrower than the files reviewers commonly require. Issue #204 captures a concrete failure on PR #201: the agent produced the requested `docs/CHANGELOG.md` entry and test update, then safe outputs rejected the patch because neither path was allowlisted.

The workflow already sits behind reviewer feedback and a human merge gate. The next change should make the push allowlist match the real file surfaces the workflow is expected to edit in this repository, while keeping the configuration explicit and keeping the compiled lock file in sync.

## Interview Synthesis

**Technical constraints**
- Update the local workflow source at `.github/workflows/pr-fix.md` and recompile `.github/workflows/pr-fix.lock.yml` so runtime behavior matches the source change.
- Verify the final `allowed-files` syntax against the active gh-aw schema or compiler behavior before merging. Do not assume the example globs are correct without checking.
- Keep using `push-to-pull-request-branch`. Do not replace the push path with a weaker fallback that hides a failed fix attempt.

**Scope boundaries**
- Scope the implementation to `pr-fix` and the directly required follow-up tracking item for a harness-wide audit.
- Cover at minimum the paths called out in the issue: `CHANGELOG.md`, `docs/CHANGELOG.md`, `tests/**`, `docs/**`, `scripts/**`, `.evals/**`, `.learnings/**`, `.github/**`, `.claude/**`, plus broad file-type globs for `*.py`, `*.md`, `*.yml`, and `*.yaml`.
- Do not turn this issue into the full audit itself. The broad audit is a separate follow-up task.

**Risk tolerance**
- Prefer a broad, explicit allowlist over another narrow one-off exception. The workflow is already gated by reviewer instructions and human merge review.
- Avoid `protected-files: fallback-to-issue` for this repair unless the compiler or schema makes the explicit allowlist impossible, and document that trade-off if it becomes necessary.
- Keep the change local to the workflow and its compiled output unless directly related guidance must move with it.

**Success signal**
- `/pr-fix` can push reviewer-requested changes when they land in changelog, docs, tests, scripts, workflow, learning, or eval paths that are part of this repo's normal review cycle.
- The compiled lock file reflects the updated source workflow.
- A follow-up audit task exists so maintainers can reconcile other workflows' `allowed-files` entries with the paths their prompts actually touch.

## Decision

Adopt a broader explicit allowlist in `pr-fix` rather than adding only the two paths from the failure.

The failure mode is not unique to `docs/CHANGELOG.md` and `tests/test_workflow_contracts.py`. Reviewer-driven fixes in this repository regularly span docs, tests, workflow files, scripts, and learning artifacts. The plan should therefore widen the allowlist to the repo surfaces `pr-fix` is reasonably expected to edit here, then rely on the existing reviewer verdict and human merge gate as the higher-level control.

## Success Criteria

- `.github/workflows/pr-fix.md` defines `safe-outputs.push-to-pull-request-branch.allowed-files` that covers at minimum: `CHANGELOG.md`, `docs/CHANGELOG.md`, `tests/**`, `docs/**`, `scripts/**`, `.evals/**`, `.learnings/**`, `.github/**`, `.claude/**`, `**/*.py`, `**/*.md`, `**/*.yml`, and `**/*.yaml`.
- The implementation confirms the chosen glob syntax is accepted by the current gh-aw toolchain, either by matching current schema guidance or by a successful `gh aw compile pr-fix`.
- `.github/workflows/pr-fix.lock.yml` is recompiled and committed with the source change.
- The implementation records a follow-up task to audit every factory workflow's `safe-outputs.*.allowed-files` coverage against the file paths its prompt can legitimately touch.
- The change preserves the intended behavior of `/pr-fix`: analyze the PR, apply the requested fix, verify it, and push the patch back to the PR branch instead of failing on an allowlist mismatch.

## Risk Assessment

**Blast radius**: Medium. The change alters a shared factory workflow that can write back to PR branches.

**Rollback**: Moderate. Reverting the workflow source and compiled lock file is easy, but it would reintroduce the current failure on common reviewer asks.

**Key risks and mitigations**
- **Risk**: The allowlist remains too narrow and a nearby file class still fails at push time. **Mitigation**: choose the broader repo-specific surface described in the issue, not just the single failing paths.
- **Risk**: The allowlist becomes broader than intended. **Mitigation**: keep it explicit, keep it limited to file classes the prompt already contemplates, and avoid catch-all fallback behavior.
- **Risk**: Workflow source changes without a lock recompile leave runtime behavior stale. **Mitigation**: treat `gh aw compile pr-fix` as part of the same checklist, then review the lock diff.
- **Risk**: The audit follow-up gets forgotten once the immediate bug is fixed. **Mitigation**: make the follow-up artifact an explicit deliverable of the implementation, not an implied later task.

## Affected Files/Areas

- `.github/workflows/pr-fix.md`: expand `safe-outputs.push-to-pull-request-branch.allowed-files` to cover the real review-driven edit surface.
- `.github/workflows/pr-fix.lock.yml`: compiled workflow output after the source change.
- Follow-up tracking artifact for the harness-wide audit, likely a new issue in this repository unless the implementation path chooses an equally visible tracker.

## Open Questions

No blocking questions from the issue context. Implementation can proceed without human input.

## Implementation Checklist

- [ ] Inspect the current gh-aw workflow syntax for `push-to-pull-request-branch.allowed-files` and choose the exact glob form that the active compiler accepts.
- [ ] Update `.github/workflows/pr-fix.md` so its `allowed-files` list covers the minimum path set named in issue #204 and reflects the broader reviewer-driven edit surface in this repository.
- [ ] Recompile `.github/workflows/pr-fix.lock.yml` with `gh aw compile pr-fix`.
- [ ] Review the compiled diff to confirm the runtime workflow reflects the allowlist change and no unrelated frontmatter drift was introduced.
- [ ] Add the required harness-wide audit follow-up task for all workflow `allowed-files` entries, using a visible tracking artifact that maintainers can act on.
- [ ] Confirm the final change still keeps `/pr-fix` on the explicit push path, rather than downgrading failures into a quieter fallback.

## Recommended implementer

**Choice**: copilot
**Rationale**: Auto-assignable via `implementer-dispatcher`. The implementation is a focused workflow-maintenance change with a concrete checklist and no unresolved design work left after this plan.
