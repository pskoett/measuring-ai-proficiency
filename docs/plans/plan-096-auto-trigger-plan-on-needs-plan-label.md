# Plan 096: Auto-trigger /plan when `needs-plan` label is applied

**Source issue**: #96
**Status**: Ready for implementation

## Problem Statement

The factory docs describe `needs-plan` as the handoff from spec refinement to task generation, but the installed `/plan` workflow still triggers only on a human `/plan` comment. In practice, merging a plan PR leaves the source issue sitting on `needs-plan` until someone manually posts `/plan`.

That breaks the intended label-driven chain and adds a fragile human step between plan approval and sub-issue creation. The first real use of the chain on issues #61, #62, #66, and #70 exposed the gap immediately.

## Interview Synthesis

**Technical constraints**
- Keep the upstream `githubnext/agentics` `/plan` workflow unchanged for this first fix.
- Use a wrapper workflow in `.github/workflows/` to translate the `needs-plan` label into a `/plan` comment.
- Prevent duplicate `/plan` runs when the issue already has `ai-generated` child work items.

**Scope boundaries**
- Automate only the `needs-plan` to `/plan` handoff and the label cleanup that follows successful task creation.
- Do not change `/plan` sub-issue content, parent-child linking, or the implementer-dispatcher workflow.
- Do not retroactively process old `needs-plan` issues in this change.

**Risk tolerance**
- Prefer the simplest reversible wrapper over patching the upstream workflow source.
- Accept a bounded polling or follow-up check if that is the cleanest way to remove `needs-plan` only after sub-issues exist.
- Avoid brittle logic that could post repeated `/plan` comments or strip the label before task creation succeeds.

**Success signal**
- Applying `needs-plan` to a freshly spec-refined issue causes `/plan` to run without human intervention.
- The issue loses `needs-plan` only after `/plan` has produced the expected `ai-generated` sub-issues.

## Success Criteria

- A new workflow, likely `.github/workflows/trigger-plan.yml`, runs on `issues.labeled`.
- The workflow reacts only when the applied label is `needs-plan`.
- The workflow skips issues that already have `ai-generated` sub-issues or equivalent evidence that planning already ran.
- The workflow posts `/plan` to the source issue using a GitHub Actions token, without editing the upstream `/plan` workflow.
- After `/plan` succeeds and sub-issues exist, the automation removes `needs-plan` from the source issue.
- `docs/AGENT_FACTORY.md` documents the automatic `needs-plan` handoff and the label lifecycle accurately.
- Any adjacent factory guidance that still implies a manual `/plan` comment after plan-PR merge is updated or explicitly confirmed accurate.

## Risk Assessment

**Blast radius**: Medium. This changes the default handoff behavior for every future issue that reaches `needs-plan`.

**Rollback**: Straightforward. Remove the new wrapper workflow and revert the doc updates.

**Risk**: The wrapper could post duplicate `/plan` comments, remove `needs-plan` too early, or fail to detect task creation reliably if the duplicate guard is too weak. Mitigation: bound the trigger to the label event, key duplicate detection off existing `ai-generated` child issues or parent links, and remove the label only after the workflow can prove sub-issues were created.

## Affected Files/Areas

- `.github/workflows/trigger-plan.yml` - new wrapper workflow that listens for `needs-plan`, posts `/plan`, and handles post-success cleanup.
- `.github/workflows/plan.md` - read-only integration surface to confirm the wrapper preserves the current slash-command contract and sub-issue labels.
- `docs/AGENT_FACTORY.md` - update the chain description and label lifecycle so it matches the new automatic trigger.
- `.claude/skills/use-agent-factory/SKILL.md` - update the factory skill so it no longer tells users to post `/plan` manually after merging a plan PR.
- `docs/chain.md` and other factory-facing guidance - update only if implementation finds wording that still describes the old manual handoff.

## Open Questions

None. The issue already chooses the wrapper-workflow approach and explicitly leaves `/plan` internals out of scope.

## Implementation Checklist

- [ ] Inspect the current `/plan` workflow and recent factory artifacts to confirm what labels, parent links, and issue relationships can be used as the duplicate guard.
- [ ] Add a wrapper workflow in `.github/workflows/trigger-plan.yml` that runs on `issues.labeled` and exits unless the new label is `needs-plan`.
- [ ] In that workflow, add guard conditions for closed issues, `human-review`, and issues that already have `ai-generated` child tasks or equivalent evidence that `/plan` has already run.
- [ ] Post the `/plan` comment from the workflow using `actions/github-script` or an equivalent first-party action, with the repository token scoped only to what the comment and label update need.
- [ ] Add bounded follow-up logic so the wrapper checks whether `/plan` produced sub-issues, then removes `needs-plan` only on success and leaves the label in place on failure or timeout.
- [ ] Update `docs/AGENT_FACTORY.md` to show the automatic `needs-plan` to `/plan` handoff and explain when the label is expected to disappear.
- [ ] Update `.claude/skills/use-agent-factory/SKILL.md` so the chain description and operator guidance match the new automation.
- [ ] Search for other direct contradictions about manual `/plan` triggering, then fix only the references that would mislead future operators.

## Rejected Alternatives

**Patch `.github/workflows/plan.md` directly**: Rejected for the first cut. It forks an upstream-managed workflow and increases future merge and maintenance cost for a problem that can be solved at the trigger boundary.

**Drop the `needs-plan` convention and require manual `/plan` comments**: Rejected. That preserves the current gap and weakens the label-driven factory model the docs already teach.

**Remove `needs-plan` immediately after posting `/plan`**: Rejected. It would erase the retry signal even when `/plan` fails before creating sub-issues.

## Recommended implementer

**Choice**: claude-sonnet-4.6
**Rationale**: This is a scoped factory automation change across one new workflow and a small set of docs, with medium blast radius and a clear preferred approach. Sonnet is the right default for that class of work.
