# Plan 161: Add one-page factory state-machine doc

**Source issue**: #161
**Status**: Ready for implementation

## Problem Statement

The factory's state machine is real, but the operator view is fragmented. Label semantics live across workflow files, harness docs, and older analysis notes. A human cannot answer simple routing questions quickly without tracing labels and triggers by hand.

Issue #161 asks for a single reference page that makes the live flow legible: which labels correspond to which board lanes, which workflows fire on which events, and what happens on the main path from issue creation to merged implementation PR. The implementation must document the current factory exactly as it exists today, without changing behavior or inventing a second source of truth.

## Interview Synthesis

**Technical constraints**
- Keep this docs-only. Do not change workflows, labels, or automation behavior.
- Treat the workflow sources in `.github/workflows/` as authoritative for triggers, filters, and outputs.
- Derive lane mapping from the current label semantics and existing board-state analysis, but keep labels as the control plane and the board as a visualization layer.
- Do not duplicate the chain diagram already in `docs/chain.md`. Link to it where it adds context.

**Scope boundaries**
- Create `docs/FACTORY_STATE_MACHINE.md` with the three requested elements: label-to-lane table, workflow trigger table, and happy-path sequence diagram.
- Add one cross-link from `docs/AGENT_FACTORY.md` and one from `docs/chain.md`.
- Limit the trigger table to the live workflow files in `.github/workflows/`.
- Do not rename labels, add labels, or expand into workflow cleanup.

**Risk tolerance**
- Favor factual precision over polish. This is an operator reference, not a narrative rewrite.
- Prefer direct tables and terse explanations over prose-heavy documentation.
- Accept a derived mapping for labels that are clearly transitional or attention-oriented, as long as the doc says the board is observational and labels remain authoritative.

**Success signal**
- An operator can identify the expected state after common transitions such as `needs-spec`, merged plan PR, `ready-for-implementation`, `needs-rebase`, and PR merge by reading one page.
- The new doc stays consistent with the current workflow files and does not conflict with `docs/AGENT_FACTORY.md` or `docs/chain.md`.
- The cross-links make the new page discoverable from the existing factory docs.

## Success Criteria

- `docs/FACTORY_STATE_MACHINE.md` exists and includes a label-to-lane mapping table aligned to the six board lanes named in the issue: Inbox, Planning, In flight, Review, Needs Attention, Done.
- `docs/FACTORY_STATE_MACHINE.md` includes a workflow trigger table that covers the workflow files in `.github/workflows/` and states, for each one, the activating event and filter plus the output or side effect it produces.
- `docs/FACTORY_STATE_MACHINE.md` includes a happy-path sequence diagram from issue opened through implementation PR merged, with every automated label transition and each human gate called out.
- `docs/FACTORY_STATE_MACHINE.md` links to `docs/chain.md` for the broader architecture view instead of duplicating that diagram.
- `docs/AGENT_FACTORY.md` and `docs/chain.md` each include a direct cross-link to `docs/FACTORY_STATE_MACHINE.md`.
- No workflow behavior, labels, or GitHub automation files change as part of implementation.

## Risk Assessment

**Blast radius**: Low. The implementation should touch only documentation.

**Rollback**: Trivial. Revert the doc commit if the new page introduces an inaccurate mapping or stale claim.

**Risk**: The main failure mode is documenting stale or inferred behavior as fact, especially in the lane mapping where Projects is derived from labels rather than driving the workflows. Mitigation: ground every trigger and transition in the workflow files on `main`, keep the board mapping explicitly descriptive, and avoid documenting provenance labels or one-off labels as if they were workflow states.

## Affected Files/Areas

- `docs/FACTORY_STATE_MACHINE.md`: new operator reference page.
- `docs/AGENT_FACTORY.md`: add a discoverability link to the new reference page.
- `docs/chain.md`: add a discoverability link to the new reference page.
- `.github/workflows/*.md` and `.github/workflows/plan-merged-dispatcher.yml`: source material for trigger and output tables. Read-only in this task.
- `docs/AGENT_FACTORY_ANALYSIS.md`: supporting context for the board-state framing and label-as-authority principle. Read-only in this task.

## Open Questions

No unresolved questions from the current issue and repository context. Implementation can proceed without human input.

## Implementation Checklist

- [ ] Read the current workflow files under `.github/workflows/` and note, for each one, the event type, trigger filter, and observable output or side effect.
- [ ] Derive the six-lane label mapping for the factory board, keeping labels authoritative and the board descriptive.
- [ ] Draft `docs/FACTORY_STATE_MACHINE.md` with a short framing note that explains the page is a static operator reference, not a control plane.
- [ ] Add the label-to-lane mapping table. Include only state-carrying and attention-carrying labels that help an operator understand current flow.
- [ ] Add the workflow trigger table for the factory's workflow files. Summarize each workflow's activation condition and output in one row.
- [ ] Add the happy-path sequence diagram from issue opened to PR merged. Show all human gates and automated label transitions on that path.
- [ ] Link to `docs/chain.md` from the new page for the broader architecture view instead of copying its existing chain diagram.
- [ ] Add one cross-link to `docs/FACTORY_STATE_MACHINE.md` from `docs/AGENT_FACTORY.md`.
- [ ] Add one cross-link to `docs/FACTORY_STATE_MACHINE.md` from `docs/chain.md`.
- [ ] Review the final docs set for factual consistency so the new reference does not contradict the existing factory docs.

## Recommended implementer

**Choice**: copilot
**Rationale**: Auto-assignable via `implementer-dispatcher`. The task is docs-only, tightly scoped, and grounded in existing workflow files, so Copilot is the right default path for the implementation PR.
