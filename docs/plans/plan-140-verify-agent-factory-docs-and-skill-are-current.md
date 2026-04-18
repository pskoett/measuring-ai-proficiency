---
plan-id: plan-140
status: shipped
shipped-in: "#140"
---
# Plan 140: Verify agent-factory docs and skill are current

**Source issue**: #140
**Status**: Ready for implementation

## Problem Statement

The factory refactor in #138 removed the sub-issue layer and simplified the handoff chain around the source issue. Issue #140 is a smoke test for that path. The implementation must compare the current workflow behavior on `main` against the doc and skill surfaces that describe the factory, then close any factual gaps with the smallest possible edits.

The source of truth for this audit is:

- `.github/workflows/plan-merged-dispatcher.yml`
- `.github/workflows/implementer-dispatcher.md`
- `.github/workflows/reviewer.md`
- `.github/workflows/spec-refiner.md`

The audit surface is:

- `docs/AGENT_FACTORY.md`
- `docs/chain.md`
- `CLAUDE.md`
- `AGENTS.md`
- `.claude/skills/use-agent-factory/SKILL.md`
- `.github/copilot-instructions.md`

## Interview Synthesis

**Technical constraints**
- Treat the four workflow files above as authoritative. Doc and skill text must match them exactly, even if older harness guidance disagrees.
- Keep edits surgical. This is a consistency audit, not a rewrite.
- Do not edit workflow `.md`, `.lock.yml`, or `.yml` files as part of implementation. The issue says the workflows themselves are out of scope.
- Preserve the current single-issue factory model: plan PR merges, `plan-merged-dispatcher` writes the checklist onto the source issue, then `implementer-dispatcher` routes from the source issue's labels.

**Scope boundaries**
- Only audit the six named doc and skill surfaces plus the four workflow source files.
- Look specifically for drift around `/plan`, sub-issues, parent-issue lookup, sibling-PR discovery, deferred review states, workflow counts, label flow, and stale paths or workflow names.
- Do not expand into a broader doc cleanup or style pass.
- A clean implementation PR with no repo edits is acceptable if the PR body explicitly says no gaps were found.

**Risk tolerance**
- Prefer precision over coverage theater. A short list of real mismatches is better than broad restyling.
- Accept documentation-only edits. No compatibility shims or speculative workflow changes.
- Avoid changing wording that is already correct just to make sections read better.

**Success signal**
- Every named doc and skill surface matches the workflows on `main` after the audit.
- Any detected drift is corrected with the minimum necessary edits.
- If no drift exists, the implementation PR explicitly records that clean result instead of inventing changes.

## Success Criteria

- `docs/AGENT_FACTORY.md`, `docs/chain.md`, `CLAUDE.md`, `AGENTS.md`, `.claude/skills/use-agent-factory/SKILL.md`, and `.github/copilot-instructions.md` agree with the behavior in `.github/workflows/plan-merged-dispatcher.yml`, `.github/workflows/implementer-dispatcher.md`, `.github/workflows/reviewer.md`, and `.github/workflows/spec-refiner.md`.
- No audited surface still describes `/plan`, sub-issue creation, parent-issue lookup, sibling-PR discovery, or `Deferred` review classifications as live factory behavior.
- Workflow-count claims and chain descriptions match the current workflow inventory on `main`.
- Label-flow descriptions match the current handoff: `needs-spec` -> plan PR -> `needs-plan` -> merged plan checklist written onto the source issue -> `ready-for-implementation` on the source issue -> implementer dispatch.
- If the audit finds no gaps, the implementation PR body explicitly says the pass was clean and no repo edits were required.

## Risk Assessment

**Blast radius**: Low. The implementation should touch only documentation and skill text, or possibly no tracked files at all.

**Rollback**: Trivial. Revert the implementation commit if an edit accidentally introduces a new mismatch.

**Risk**: The main failure mode is false positives, where implementation edits wording that was already correct or expands beyond the named surfaces. Mitigation: compare every proposed doc claim directly to the four source-of-truth workflow files and keep changes surgical.

## Affected Files/Areas

- `.github/workflows/plan-merged-dispatcher.yml`: source of truth for plan-merge activation, checklist injection, and `needs-plan` -> `ready-for-implementation`.
- `.github/workflows/implementer-dispatcher.md`: source of truth for implementer routing and the `impl:copilot` constraint.
- `.github/workflows/reviewer.md`: source of truth for review classifications, plan lookup, and absence of sibling-PR logic.
- `.github/workflows/spec-refiner.md`: source of truth for plan PR creation, implementer recommendation, and label swap rules.
- `docs/AGENT_FACTORY.md`: operator guide and workflow inventory.
- `docs/chain.md`: architecture diagram and routing narrative.
- `CLAUDE.md`: project-context and factory-chain summary for Claude sessions.
- `AGENTS.md`: shared factory context, routing rules, and workflow inventory.
- `.claude/skills/use-agent-factory/SKILL.md`: factory-driving instructions and failure-mode guidance.
- `.github/copilot-instructions.md`: Copilot-facing harness summary that may still carry stale factory claims.

## Open Questions

- [ ] If the audit finds zero mismatches, should implementation still open a PR with no tracked file changes? - Can proceed. The issue explicitly allows a clean no-op PR whose body records that result.
- [ ] When a statement is partly stale and partly accurate, should implementation rewrite the full paragraph or only the incorrect clause? - Can proceed. Prefer the smallest edit that restores factual accuracy.

## Implementation Checklist

- [ ] Read the four workflow source-of-truth files in full and note the live behavior for plan merge, implementer routing, reviewer behavior, and spec-refiner label flow.
- [ ] Audit `docs/AGENT_FACTORY.md` against those workflows. Flag only factual mismatches.
- [ ] Audit `docs/chain.md` against those workflows. Flag only factual mismatches.
- [ ] Audit `CLAUDE.md` and `AGENTS.md` against those workflows, focusing on chain prose, workflow counts, label flow, and implementer routing.
- [ ] Audit `.claude/skills/use-agent-factory/SKILL.md` for stale mentions of `/plan`, sub-issues, sibling PRs, numbering races, or closing-plan-PR behavior that no longer exists.
- [ ] Audit `.github/copilot-instructions.md` for any factory-chain claims that drift from the workflows on `main`.
- [ ] If mismatches exist, update only the affected files with the minimum edits needed to restore consistency.
- [ ] If no mismatches exist, create the implementation PR anyway and state clearly in the PR body that the audit was clean and no file edits were necessary.
- [ ] In either path, verify the final PR description names the source-of-truth workflows and summarizes whether the audit produced edits or a clean pass.

## Recommended implementer

**Choice**: copilot
**Rationale**: Auto-assignable via `implementer-dispatcher`. For manual hand-off to Claude or Codex, a human can swap the label on the source issue before merging the plan PR.
