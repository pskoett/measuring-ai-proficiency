# Plan 152: Loosen workflow protected prefixes and add reviewer self-tamper guard

**Source issue**: #152
**Status**: Ready for implementation

## Problem Statement

Two factory maintenance workflows, `pr-fix` and `conflict-resolver`, are blocked on the repository's most common PR shape: changes under `.github/workflows/`. Their safe-output handler still protects the entire `.github/` path prefix, so any attempt to push a fix or a clean merge to a workflow-touching PR is rejected before the workflow can do its job.

That protection made sense as an early conservative default. It now overlaps with stronger guards that already exist in this repository: reviewer, contribution-checker, lock-file-sync, and the human merge gate. The result is worse than the original risk. The automation fails on normal factory-development PRs and hands routine work back to humans.

The fix has two parts:

1. Remove `.github/` from `push_to_pull_request_branch.protected_path_prefixes` in `pr-fix` and `conflict-resolver`, while keeping `.agents/` protected and leaving `protected_files` unchanged.
2. Add an early self-tamper stop in `reviewer.md` so the reviewer refuses to operate on PRs that modify its own instructions or adjacent guardrail files.

## Interview Synthesis

**Technical constraints**
- Preserve the current `protected_files` lists. Those file-level protections serve a different threat model than path-prefix protection.
- Limit the prefix loosening to `pr-fix` and `conflict-resolver`. Do not generalize the change to unrelated workflows in the same pass.
- Implement the reviewer self-tamper guard before the main review flow. It should inspect the PR diff and stop early when the diff touches `.github/workflows/reviewer.md`, `.github/workflows/self-improvement-meta.md`, or `.github/copilot-instructions.md`.
- Keep workflow sources and compiled lock files in sync. Every touched `.md` workflow file needs a matching `.lock.yml` recompile.

**Scope boundaries**
- In scope: `.github/workflows/pr-fix.md`, `.github/workflows/conflict-resolver.md`, `.github/workflows/reviewer.md`, their compiled lock files, and `docs/AGENT_FACTORY.md`.
- In scope: reviewer label allowlist updates needed to add `human-review`.
- In scope: operator documentation for the new behavior and the self-tamper stop.
- Out of scope: changing `protected_files`, loosening `.agents/`, adding new workflows, or broad reviewer policy changes beyond the early self-tamper noop.

**Risk tolerance**
- Favor a narrow permissions change over a broader safe-output rewrite.
- Prefer an explicit early stop to clever partial-review behavior. If reviewer self-modification is in play, hand the PR to humans.
- Accept a manual validation step on a throwaway workflow-touching PR rather than speculative automation changes beyond the issue's scope.

**Success signal**
- `pr-fix` can push a fix to a PR that modifies `.github/workflows/*.md`.
- `conflict-resolver` can push a clean merge commit when `origin/main` changed `.github/workflows/*.md`.
- Reviewer adds `human-review` and noops before normal review when a PR diff touches one of the guarded self-modifying paths.
- Docs describe both the new write permission and the reviewer self-tamper guard clearly enough for operators to predict the behavior.

## Success Criteria

- `pr-fix.md` sets `push_to_pull_request_branch.protected_path_prefixes` to `[".agents/"]`, with no change to its `protected_files` list, and the compiled lock file matches.
- `conflict-resolver.md` sets `push_to_pull_request_branch.protected_path_prefixes` to `[".agents/"]`, with no change to its `protected_files` list, and the compiled lock file matches.
- `reviewer.md` gains an early self-tamper check that inspects the PR diff, adds `human-review`, and calls `noop` before Step 1 when the diff includes `.github/workflows/reviewer.md`, `.github/workflows/self-improvement-meta.md`, or `.github/copilot-instructions.md`.
- `reviewer.md` safe-output label allowlist includes `human-review`, and the compiled lock file matches.
- `docs/AGENT_FACTORY.md` documents that `pr-fix` and `conflict-resolver` can now write to `.github/workflows/*`, and that reviewer will stop on self-tampering PRs by applying `human-review`.
- The existing lock-file-sync guard stays green after the workflow edits.
- A small workflow-touching smoke test confirms the intended behavior for both `/pr-fix` and `conflict-resolver`.

## Risk Assessment

**Blast radius**: High. This changes how automated workflows can write back to PR branches under `.github/workflows/`, which is the factory's control surface.

**Rollback**: Straightforward. Revert the three workflow markdown files, their lock files, and the docs update.

**Risk**: The loosened prefix could let an automated fix push changes to sensitive workflow instructions that previously hard-failed. Mitigation: keep `protected_files` intact, keep `.agents/` protected, and add the reviewer self-tamper stop so a PR that edits reviewer or adjacent guardrails is immediately labeled for human handling. A second risk is drift between workflow markdown sources and lock files. Mitigation: recompile in the same change and confirm the lock-file-sync guard remains clean.

## Affected Files/Areas

- `.github/workflows/pr-fix.md` and `.github/workflows/pr-fix.lock.yml`
- `.github/workflows/conflict-resolver.md` and `.github/workflows/conflict-resolver.lock.yml`
- `.github/workflows/reviewer.md` and `.github/workflows/reviewer.lock.yml`
- `docs/AGENT_FACTORY.md`
- Directly related workflow-health validation, including the existing lock-file-sync CI guard and a throwaway workflow-touching PR path

## Open Questions

None. The issue already specifies the guarded file list, the retained protections, and the validation path with enough precision to implement directly.

## Implementation Checklist

- [ ] Update `.github/workflows/pr-fix.md` so `push_to_pull_request_branch.protected_path_prefixes` is explicitly `[".agents/"]`, preserving the existing `protected_files` behavior.
- [ ] Update `.github/workflows/conflict-resolver.md` so `push_to_pull_request_branch.protected_path_prefixes` is explicitly `[".agents/"]`, preserving the existing `protected_files` behavior.
- [ ] Add an early self-tamper step to `.github/workflows/reviewer.md` that checks the PR diff for `.github/workflows/reviewer.md`, `.github/workflows/self-improvement-meta.md`, or `.github/copilot-instructions.md`.
- [ ] Extend reviewer safe-outputs so it can add the `human-review` label when the self-tamper condition triggers.
- [ ] Ensure the reviewer self-tamper path adds `human-review` and calls `noop` before the normal plan lookup and review sequence starts.
- [ ] Recompile every touched workflow so the `.lock.yml` files stay in sync with the markdown sources.
- [ ] Update `docs/AGENT_FACTORY.md` prerequisites, quick-start, and workflow descriptions to explain the new `.github/workflows/*` write behavior and the reviewer self-tamper guard.
- [ ] Search for any nearby operator-facing wording that still claims workflow-touching PRs cannot be auto-pushed, and fix only direct contradictions found during implementation.
- [ ] Run the existing workflow validation path, including the lock-file-sync guard.
- [ ] Exercise a throwaway workflow-touching PR scenario to confirm `/pr-fix` and `conflict-resolver` behave as intended.

## Rejected Alternatives

**Keep the `.github/` protected prefix and rely on humans**: Rejected. The issue documents current failures on routine factory-development PRs. Leaving the prefix in place preserves known automation dead ends.

**Allowlist individual workflow files under `.github/workflows/`**: Rejected. The maintenance burden scales with every new workflow, while the practical end state still trends toward allowing the directory.

**Loosen protections for every workflow safe-output in the same change**: Rejected. This issue is about two concrete blocked workflows plus a reviewer guard. Broadening the change would increase blast radius without supporting evidence.

**Rely only on lock-file-sync and human merge review without a reviewer self-tamper stop**: Rejected. The additional early stop is cheap defense in depth and directly addresses the self-modifying-reviewer case.

## Recommended implementer

**Choice**: claude-opus
**Rationale**: This is a multi-file factory change on a high-sensitivity surface. It modifies workflow write permissions, reviewer guardrails, compiled lock files, and operator docs in one pass. The scope is still clear, but precise adherence matters and the checklist is long enough to justify Claude Opus.
