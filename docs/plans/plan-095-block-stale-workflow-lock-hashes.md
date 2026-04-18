---
plan-id: plan-095
status: shipped
shipped-in: "#95"
---
# Plan 095: Block PRs with stale workflow lock-file hashes

**Source issue**: #95
**Status**: Ready for implementation

## Problem Statement

Editing a gh-aw workflow markdown file can invalidate the paired `.lock.yml` file without breaking the PR that introduced the change. The repo stays green until someone later triggers the affected workflow, at which point gh-aw rejects the run because the compiled `frontmatter_hash` no longer matches.

This is a delayed factory-break condition. It has already hit multiple times in one day across `/plan`, `/pr-fix`, and other workflow edits. The repo needs a PR-time guard that fails early and tells the author exactly how to repair the mismatch before merge.

## Interview Synthesis

**Technical constraints**
- Use a normal GitHub Actions workflow for the guard, not a gh-aw markdown workflow. The protection must stay outside the compile-and-lock path it validates.
- Keep the check deterministic. Pin the gh-aw install path or version used in CI so the result does not drift across runs.
- Prefer `gh aw compile --check-only` if the pinned gh-aw version supports it. If not, use an equivalent fallback that recompiles and fails on any resulting `.lock.yml` diff.

**Scope boundaries**
- Cover PR-time detection for stale `.github/workflows/*.md` and matching `.lock.yml` pairs.
- Update the operational docs in `docs/AGENT_FACTORY.md` and `.claude/skills/use-agent-factory/SKILL.md`.
- Do not auto-regenerate and commit lock files in CI.
- Do not relax gh-aw's runtime hash enforcement.

**Risk tolerance**
- Prefer a durable repo-level guard over local-only hooks.
- Accept a small amount of CI setup complexity to get broad coverage for local edits, cloud agents, and GitHub web edits.
- Keep the implementation reversible and explicit. CI should fail loudly, not silently repair state.

**Success signal**
- A PR that changes workflow markdown without regenerating the paired lock file fails before merge.
- The failure output names the offending workflow, shows the repair command, and points back to issue #95.
- A PR with synced workflow source and lock files passes the new guard.

## Success Criteria

- A new PR-time workflow, likely `.github/workflows/lock-file-sync.yml`, runs on `pull_request` for at least `opened`, `synchronize`, and `reopened`.
- The workflow checks gh-aw workflow markdown and compiled lock files for sync, using `gh aw compile --check-only` if available in the pinned tool version or a documented equivalent fallback if not.
- On mismatch, the job fails with an actionable message that includes the specific workflow file, the fix command, and `Refs #95`.
- The guard protects both repo-local gh-aw workflows and agentics-derived workflows that compile into checked-in `.lock.yml` files.
- `docs/AGENT_FACTORY.md` documents this as a protected failure mode and explains the expected fix path.
- `.claude/skills/use-agent-factory/SKILL.md` adds the same failure mode and remediation guidance so operators stop debugging this from scratch.

## Risk Assessment

**Blast radius**: Medium. This adds a required PR gate for every future workflow edit.

**Rollback**: Straightforward. Remove the new CI workflow and revert the matching docs updates.

**Risk**: The check could be flaky if CI installs a different gh-aw version than contributors use locally, or if the fallback detection is too broad and reports noisy diffs. Mitigation: pin the tool version, scope the diff to workflow lock files, and validate the failure path against an intentionally stale `.md` and `.lock.yml` pair before merging.

## Affected Files/Areas

- `.github/workflows/lock-file-sync.yml` or equivalent plain GitHub Actions workflow that runs the sync guard on PR events.
- `.github/workflows/*.md` and `.github/workflows/*.lock.yml` as the files inspected by the guard.
- Any helper script added under `scripts/` only if the workflow logic becomes clearer or more testable when extracted from inline shell.
- `docs/AGENT_FACTORY.md` for the factory failure-mode documentation and repair instructions.
- `.claude/skills/use-agent-factory/SKILL.md` for the operator-facing failure-mode table and remediation guidance.

## Open Questions

- [ ] Which gh-aw install path is the cleanest in CI for this repo, the official setup action or a pinned `gh` extension install? - Can proceed
- [ ] Does the pinned gh-aw version support `gh aw compile --check-only`, or should the implementation standardize on a compile-and-diff fallback from the start? - Can proceed

## Implementation Checklist

- [ ] Inspect how workflow markdown and `.lock.yml` files are laid out today, including agentics-derived workflows and repo-local workflow files, so the guard validates the full checked-in set.
- [ ] Choose a plain GitHub Actions workflow design for the guard and pin the gh-aw installation method and version used in CI.
- [ ] Add `.github/workflows/lock-file-sync.yml` that runs on pull request events for new, updated, and reopened PRs, and skips cleanly when no workflow markdown or lock files changed.
- [ ] Implement the validation step with `gh aw compile --check-only` if available, otherwise run `gh aw compile` in CI and fail when it would modify checked-in workflow lock files.
- [ ] Make the failure output identify each stale workflow pair and print the exact repair command, for example `gh aw compile <workflow-name>`, plus `Refs #95`.
- [ ] Validate the unhappy path against an intentionally stale workflow pair so the job fails before merge and the output stays readable.
- [ ] Validate the happy path on synced workflow files so the new guard does not block unrelated PR traffic.
- [ ] Update `docs/AGENT_FACTORY.md` to document the stale-lock failure mode, the CI gate, and the repair command.
- [ ] Add the same failure mode to `.claude/skills/use-agent-factory/SKILL.md`, including when to stop debugging and simply recompile the workflow.
- [ ] Search for other operator guidance that still treats stale lock files as an ad hoc debugging problem, then fix only direct contradictions discovered during implementation.

## Rejected Alternatives

**Pre-commit or pre-push hooks only**: Rejected. They help local contributors but do not protect cloud agents or GitHub web edits.

**Auto-regenerate lock files in CI**: Rejected by issue scope. It hides the change behind automation and weakens explicit review of workflow updates.

**Documentation-only warning**: Rejected. This failure mode already proved that reminders are not enough.

**Implement the guard as another gh-aw markdown workflow**: Rejected. That would put the protection inside the same compile-and-lock system it is meant to defend.

## Recommended implementer

**Choice**: copilot
**Rationale**: Auto-assignable via `implementer-dispatcher`. For manual hand-off to Claude or Codex, a human can swap the label on the source issue before merging the plan PR.
