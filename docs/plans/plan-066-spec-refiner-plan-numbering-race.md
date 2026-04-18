---
plan-id: plan-066
status: shipped
shipped-in: "#66"
---
# Plan 066: Fix spec-refiner plan numbering races

**Source issue**: #66
**Status**: Ready for implementation

## Problem Statement

Concurrent `spec-refiner` runs choose the next plan number by reading the current contents of `main`. Two runs that start close together can pick the same number and open duplicate `Plan NNN` pull requests. The workflow needs a numbering rule that is unique by construction and does not depend on repository state at runtime.

## Interview Synthesis

**Technical constraints**
- Keep plan files in `docs/plans/`.
- Preserve the current human-readable naming pattern and plan PR titles.
- Update all synced skill copies and workflow docs together so every runtime uses the same rule.

**Scope boundaries**
- Fix numbering for new plan files only.
- Do not rename or renumber existing plan files.
- Do not redesign the broader factory chain or add an external coordination system.

**Risk tolerance**
- Prefer the simplest deterministic rule over retry loops or reservation files.
- Accept a small naming-convention change if it removes the race completely.

**Success signal**
- Future concurrent `spec-refiner` runs produce distinct plan filenames and PR titles without manual intervention.

## Success Criteria

- New plan files derive their number from the source issue number, not from scanning existing files on `main`.
- Two `spec-refiner` runs triggered in the same second produce unique plan filenames and unique `Plan NNN` PR titles.
- Existing plan files remain unchanged.
- `docs/plans/README.md` documents the new numbering rule.
- `spec-refiner` instructions tell the agent to use the source issue number.
- All plan-interview skill copies and shared guidance that currently describe sequential numbering are updated or explicitly confirmed unaffected.

## Risk Assessment

**Blast radius**: Medium. The change touches workflow instructions, shared skills, and plan documentation used across multiple agent runtimes.
**Rollback**: Moderate. Reverting the change is easy, but it would reintroduce the race and leave any newly created issue-numbered plans under the newer convention.
**Risk**: A partial update leaves one runtime or doc set on the old sequential rule. Mitigation: update the workflow, shared harness guidance, and all synced skill copies in the same change, then do a repo-wide search for the old wording.

## Affected Files/Areas

- `.github/workflows/spec-refiner.md` - Change plan filename and PR-title instructions to use the source issue number.
- `.github/workflows/spec-refiner.lock.yml` - Recompiled workflow output after updating the markdown source.
- `.claude/skills/plan-interview/SKILL.md` - Update the canonical skill to describe the new numbering rule.
- `.github/skills/plan-interview/SKILL.md` - Synced copy for Copilot runtimes.
- `skill-template/plan-interview/SKILL.md` - Synced template copy.
- `docs/plans/README.md` - Document the naming rule and examples.
- `AGENTS.md` - Update the shared harness guidance that still says plan numbers are sequential.
- `docs/AGENT_FACTORY.md` and `docs/chain.md` - Update user-facing factory docs if they describe the old naming convention.

## Open Questions

None at plan time. The plan can proceed.

## Implementation Checklist

- [ ] Update `.github/workflows/spec-refiner.md` so plan filenames and PR titles use the source issue number.
- [ ] Define the formatting rule precisely: zero-pad issue numbers to at least three digits, and allow wider numbers unchanged once the issue number exceeds three digits.
- [ ] Recompile the workflow so `.github/workflows/spec-refiner.lock.yml` matches the markdown source.
- [ ] Update `.claude/skills/plan-interview/SKILL.md` to replace sequential numbering guidance with the issue-number rule.
- [ ] Sync the same plan-interview wording change to `.github/skills/plan-interview/SKILL.md` and `skill-template/plan-interview/SKILL.md`.
- [ ] Update `docs/plans/README.md` to document "plan number = source issue number" and refresh examples.
- [ ] Update `AGENTS.md` so the shared harness guidance matches the new rule.
- [ ] Audit `docs/AGENT_FACTORY.md` and `docs/chain.md`, then update any wording that still implies sequential numbering.
- [ ] Run a repo-wide search for the old sequential-numbering language and remove any stale references that would mislead future agents or humans.

## Rejected Alternatives

**Commit-and-retry loop**: Preserves a global sequence, but it adds retry behavior to a workflow that should stay deterministic and cheap.

**Reservation file in `docs/plans/`**: Removes the race only if every run updates shared state correctly. It is more coordination than this workflow needs.

**Random suffixes**: Avoids collisions, but it weakens readability and makes plan titles noisier for humans.

## Recommended implementer

**Choice**: claude-opus-4.6
**Rationale**: This is a cross-cutting workflow change across the spec-refiner prompt, synced skills, and shared factory docs. The checklist is long, the rule must stay consistent across runtimes, and partial updates would leave the factory in an inconsistent state.
