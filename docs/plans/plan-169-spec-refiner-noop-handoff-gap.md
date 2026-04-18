---
plan-id: plan-169
status: shipped
shipped-in: "#169"
---
# Plan 169: Close the spec-refiner noop handoff gap

**Source issue**: #169
**Status**: Ready for implementation

## Problem Statement

`spec-refiner` currently treats "not plan-worthy" as a terminal `noop`. For simple but actionable issues, that leaves the source issue stuck with `needs-spec`, no plan PR, no implementer assignment, and no clearly labeled human next step.

The factory already has a working implementation path once an issue reaches `ready-for-implementation`. The gap is in `spec-refiner`'s classification logic and handoff rules, not in the downstream dispatcher.

## Interview Synthesis

**Technical constraints**
- Preserve a true `noop` path for spam, duplicates, `human-review`, and other cases that should not produce implementation work.
- Reuse the existing `ready-for-implementation` plus `impl:copilot` dispatch path for simple, actionable issues instead of inventing a parallel workflow.
- Keep the source issue as the single tracking anchor. Do not require a synthetic "tiny plan" PR for trivial work.
- Update workflow source, compiled lock files, and operator docs together so the chain stays consistent.

**Scope boundaries**
- Fix the `needs-spec` limbo for issues that do not need a full plan.
- Leave the normal plan PR path intact for plan-worthy work.
- Do not redesign `implementer-dispatcher` beyond any prompt updates needed to reflect the new entry path.
- Do not remove `noop` entirely.

**Risk tolerance**
- Prefer the smallest change that guarantees every `needs-spec` issue exits into a real next state.
- Accept a small increase in `spec-refiner` decision logic if it removes manual rescue work.
- Avoid introducing a new label taxonomy unless the existing labels cannot express the needed states.

**Success signal**
- After `spec-refiner` runs, the issue always lands in one of three outcomes: plan PR opened, direct route to implementation, or clearly labeled human/terminal state.
- No issue remains in `needs-spec` after the workflow has deliberately decided not to create a plan.

## Decision

Adopt **direct routing for simple but actionable issues**.

Use this decision tree inside `spec-refiner`:

1. **Plan-worthy work**: keep the current behavior. Write the plan file, open the plan PR, remove `needs-spec`, add `impl:copilot`, and add `needs-plan` unless human input is required.
2. **Simple but actionable work**: do not create a plan file. Remove `needs-spec`, add `impl:copilot`, add `ready-for-implementation`, and post a short comment that this issue was intentionally fast-tracked without a plan.
3. **Non-actionable or terminal work**: keep `noop`, but do not leave the issue in limbo. Remove `needs-spec` and transition to a visible end state, such as `blocked-on-human` for missing context or `closed` for spam, duplicates, and intentionally dropped work.

This reuses the factory's existing automation. It avoids a new "no-plan-needed" label and avoids polluting `docs/plans/` with one-line placeholder plans.

## Success Criteria

- `spec-refiner` no longer leaves actionable issues labeled `needs-spec` after deciding they are not plan-worthy.
- For simple actionable issues, `spec-refiner` can route directly to `ready-for-implementation` with `impl:copilot` and no plan PR.
- For blocked or terminal issues, `spec-refiner` clears `needs-spec` and leaves a clearly visible human or terminal state.
- `implementer-dispatcher` documentation matches the new reality that `ready-for-implementation` may come from a merged plan PR or a direct fast-track from `spec-refiner`.
- Operator docs explain both entry paths so humans know when to expect a plan PR and when not to.
- The examples from #153 and #162 would no longer require a manual rescue PR to move forward.

## Risk Assessment

**Blast radius**: Medium. This changes the default handoff behavior for a subset of `needs-spec` issues and touches workflow prompts, compiled workflow output, and operator documentation.

**Rollback**: Moderate. Reverting the workflow and docs is easy, but it would reintroduce the limbo state for future simple issues.

**Risk**: The workflow could classify too aggressively and skip plan creation for work that actually needed a plan. Mitigation: write explicit criteria and examples for the direct-route branch, keep the default biased toward plan creation when uncertain, and document the human override path.

## Affected Files/Areas

- `.github/workflows/spec-refiner.md` - Define the new classification and handoff rules, including the direct-route path and the non-limbo terminal path.
- `.github/workflows/spec-refiner.lock.yml` - Recompiled workflow output after editing the markdown source.
- `.github/workflows/implementer-dispatcher.md` - Update wording that currently assumes `ready-for-implementation` only comes from `plan-merged-dispatcher`.
- `.github/workflows/implementer-dispatcher.lock.yml` - Recompiled workflow output if the workflow markdown changes.
- `docs/AGENT_FACTORY.md` - Document that `needs-spec` can produce either a plan PR or a direct implementation handoff, depending on issue complexity.
- `docs/CONTRIBUTING.md` - Update contributor guidance that currently says `needs-spec` always writes a plan PR.
- `docs/chain.md` - Refresh the chain narrative and routing explanation for the fast-track branch.
- `AGENTS.md` and `CLAUDE.md` - Update shared harness context if it still describes plan PR creation as the only `needs-spec` outcome.
- `.claude/skills/use-agent-factory/SKILL.md` - Update operator guidance if it still assumes every `needs-spec` issue yields a plan PR.

## Open Questions

None at plan time. The issue already authorizes choosing the routing strategy, and the direct-route approach fits the existing factory architecture.

## Implementation Checklist

- [ ] Update `.github/workflows/spec-refiner.md` to distinguish plan-worthy, direct-route, and terminal/blocked outcomes.
- [ ] Extend the safe-output instructions in `.github/workflows/spec-refiner.md` so the workflow can apply `ready-for-implementation` on the direct-route path.
- [ ] Define explicit guardrails for when `spec-refiner` may skip plan creation and fast-track an issue to implementation.
- [ ] Define explicit non-limbo end states for true `noop` cases, including when to add `blocked-on-human` and when to close the issue.
- [ ] Keep the normal plan PR path unchanged for plan-worthy work, including non-closing `Refs #NN` plan PR bodies.
- [ ] Update `.github/workflows/implementer-dispatcher.md` so its prompt matches the new upstream handoff sources for `ready-for-implementation`.
- [ ] Recompile any changed workflow markdown files so the corresponding `.lock.yml` files stay in sync.
- [ ] Update `docs/AGENT_FACTORY.md`, `docs/CONTRIBUTING.md`, and `docs/chain.md` so operator docs describe the direct-route branch accurately.
- [ ] Audit shared guidance in `AGENTS.md`, `CLAUDE.md`, and `.claude/skills/use-agent-factory/SKILL.md`, then fix any wording that incorrectly states every `needs-spec` issue produces a plan PR.
- [ ] Run the existing repo verification commands after the workflow and docs changes land.

## Rejected Alternatives

**New `no-plan-needed` label**: This makes board filtering clearer, but it adds a new state to manage when the existing `ready-for-implementation`, `blocked-on-human`, and `closed` states already cover the needed outcomes.

**One-line placeholder plan files**: This preserves the current chain shape, but it adds busywork and repository noise for issues the workflow has already judged too small for a real plan.

**Keep `noop` and rely on humans to notice**: This is the current failure mode. It breaks the factory's handoff contract and forces manual rescue work.

## Recommended implementer

**Choice**: copilot
**Rationale**: Auto-assignable via `implementer-dispatcher`. For manual hand-off to Claude or Codex through the GitHub UI, a human can swap the label on the source issue before merging the plan PR.
