# Plan 002: Add conflict-resolver workflow for parallel PR merges

**Source issue**: #61
**Status**: Ready for implementation

## Problem Statement

Parallel sub-issues are an explicit part of this factory. Parallel PRs are therefore normal, not exceptional. Today the factory has no automated path for the second or third PR that collides with earlier merges on `main`. When a PR becomes dirty, a human has to fetch, merge, resolve, and push outside the factory.

The first cut should add a workflow that handles the textual merge case only. It should merge `origin/main` into the PR branch when a maintainer applies `needs-rebase`, remove that label on success, and hand conflicts back to a human with a precise file list.

## Interview Summary

The issue body provides enough specificity to simulate the planning interview:

- **Technical constraints**: Trigger from `needs-rebase`, perform a real Git merge of `origin/main` into the PR branch, and keep safe outputs limited to comment and label management.
- **Scope boundaries**: No semantic conflict resolution. No automatic detection or labeling of dirty PRs in this first cut.
- **Risk tolerance**: Prefer a conservative textual merge path over a broader automation feature. Stop cleanly on conflicts.
- **Success criteria**: Add the new workflow and compiled lock file, document it in the factory docs, and add `needs-rebase` to the label reference.

## Success Criteria

- A new workflow exists at `.github/workflows/conflict-resolver.md`.
- The workflow compiles to `.github/workflows/conflict-resolver.lock.yml`.
- The workflow triggers when a pull request is labeled `needs-rebase`.
- The workflow fetches `origin/main` and attempts a plain Git merge into the PR branch.
- On a clean merge, the workflow pushes the merge commit back to the PR branch and removes `needs-rebase`.
- On merge conflict, the workflow comments on the PR with the conflicted files, adds `blocked-on-human`, and exits without pushing partial conflict markers.
- The workflow uses only the allowed safe outputs from the issue: `add-comment`, `add-labels` for `blocked-on-human`, and `remove-labels` for `needs-rebase`.
- `docs/AGENT_FACTORY.md` includes the workflow in the chain description or workflow table and documents the `needs-rebase` label.

## Risk Assessment

**Blast radius**: Medium. This is one new workflow, but it mutates live pull request branches and can retrigger CI on active work.

**Rollback**: Medium. Reverting the workflow files is easy. Reverting an unwanted merge commit on a branch is also possible, but it creates operational churn for anyone already working from that branch.

**Primary risks and mitigations**

- Wrong event or permission model prevents the workflow from seeing PR context. Mitigation: follow an existing PR-oriented workflow pattern and verify the event exposes the branch ref needed for checkout and push.
- The workflow leaves the repository in a conflicted state. Mitigation: abort the merge on conflict, collect filenames from Git, and only push on a clean merge.
- The workflow silently fails on unsupported PR shapes, such as fork branches. Mitigation: add an explicit guard and a human-readable comment or noop path instead of attempting an unsafe push.
- The workflow introduces stale labels. Mitigation: define the first-cut label contract clearly, `needs-rebase` is removed only on success, `blocked-on-human` is added only on conflict.

## Affected Files/Areas

- `.github/workflows/conflict-resolver.md`: new workflow definition, trigger, permissions, tools, bash flow, safe outputs
- `.github/workflows/conflict-resolver.lock.yml`: compiled workflow artifact from `gh aw compile`
- `docs/AGENT_FACTORY.md`: workflow inventory, chain description, and label reference
- `docs/chain.md`: chain diagram and workflow layer list, if the new workflow is shown there as part of the factory narrative

## Open Questions

- [ ] Should the workflow handle same-repo pull requests only, or also attempt pushes to fork-based PRs? Default to same-repo only. Can proceed.
- [ ] Should `docs/chain.md` be updated alongside `docs/AGENT_FACTORY.md` even though the issue only requires the factory docs? Likely yes, to keep the chain narrative in sync. Can proceed.
- [ ] Should a later successful rerun clear a pre-existing `blocked-on-human` label? Not in this first cut because the requested safe outputs do not include that removal. Can proceed.

## Implementation Checklist

- [ ] Read the existing PR-oriented workflow patterns, especially `pr-fix.md`, and the Git-mutation workflow pattern in `ci-cleaner.md`, then choose the event model that gives safe access to PR branch metadata.
- [ ] Create `.github/workflows/conflict-resolver.md` with a trigger tied to the `needs-rebase` label on pull requests.
- [ ] Configure permissions, tools, and safe outputs so the workflow can inspect PR context, run git commands, add a conflict comment, add `blocked-on-human`, and remove `needs-rebase` on success.
- [ ] Add guardrails for unsupported situations before attempting a merge, especially fork-based PR branches or missing branch refs.
- [ ] Implement the bash sequence to fetch `origin/main`, attempt the merge, detect success versus conflict, and abort the merge cleanly when conflicts occur.
- [ ] Capture conflicted file paths from Git and format them into a concise PR comment when the merge fails.
- [ ] Push the merge commit back to the PR branch only after a clean merge.
- [ ] Remove `needs-rebase` only after the push succeeds.
- [ ] Add `blocked-on-human` only on conflict, not on transient infrastructure failures.
- [ ] Compile the workflow with `gh aw compile conflict-resolver` and commit the generated `.lock.yml`.
- [ ] Update `docs/AGENT_FACTORY.md` workflow tables, chain description, and label reference to include `conflict-resolver` and `needs-rebase`.
- [ ] Update `docs/chain.md` if the workflow layer or chain diagram should reflect the new repair path for dirty pull requests.
- [ ] Run the repo test suite and any workflow validation already used in this project after the workflow and docs changes land.

## Rejected Alternatives

**Semantic conflict resolution in the first cut**: Rejected. The issue explicitly scopes this out. The workflow should stop at textual merge and hand semantic work to a human.

**Auto-detect dirty PRs in the same change**: Rejected. The issue explicitly makes auto-labeling a follow-up. The first cut starts when `needs-rebase` is already present.

**Rebase instead of merge**: Rejected. The requested behavior says to fetch `origin/main` and merge it into the PR branch. A merge commit is the intended first-cut behavior.

## Recommended implementer

**Choice**: claude-opus-4.6
**Rationale**: This adds branch-mutating automation with event, permission, and git edge cases across workflow, docs, and compiled artifacts. The blast radius is medium and the checklist is long enough that Opus is the safer default.
