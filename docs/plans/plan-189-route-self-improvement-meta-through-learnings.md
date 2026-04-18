# Plan 189: Route self-improvement-meta through `.learnings/` instead of straight to harness

**Source issue**: #189
**Status**: Needs plan review

## Problem Statement

`self-improvement-meta` currently mixes two different jobs in one nightly run: it extracts patterns from recent workflow activity and promotes those patterns directly into harness files in the same PR. That design starves `.learnings/` as a durable intermediate store, weakens cross-run deduplication, and collapses two separate human decisions into one review step.

The weekly `learning-aggregator-ci` workflow already expects `.learnings/` to contain accumulated entries that it can group by `Pattern-Key`. Today that path is underfed by construction. The outer loop needs to be restored to the intended shape: capture first, aggregate second, promote third, regress-test after promotion.

## Interview Synthesis

**Technical constraints**
- Preserve the factory's two-loop model: nightly capture, weekly aggregation, then a separate human-gated promotion step.
- Keep the existing transcript-candidate handoff from `learning-aggregator-ci`, but change the nightly workflow so those candidates land in `.learnings/` instead of going straight to harness files.
- Prefer narrow workflow permissions and file allowlists. The nightly workflow should only need to write under `.learnings/`.
- Keep workflow source and compiled lock files in sync. Any workflow markdown change must be followed by `gh aw compile`.
- Resolve the current learnings-schema mismatch if it blocks the new flow. The checked-in `.learnings/` files still advertise an older status vocabulary than the workflow prompts and shared guidance.

**Scope boundaries**
- Fix the outer-loop capture and aggregation path end to end.
- Make promotion a separate human-gated step with its own PR title and workflow boundary.
- Keep this issue focused on the routing split. Do not redesign unrelated factory workflows.
- Coordinate with companion issue #188, but do not leave #189 dependent on nightly promotion staying in `self-improvement-meta`.

**Risk tolerance**
- Prefer explicit state transitions and separate workflows over prompt wording alone.
- Accept adding a dedicated promotion workflow if that is the cleanest way to keep capture and promotion separate.
- Avoid solutions that let nightly runs continue mutating harness files, even as a fallback.

**Success signal**
- A nightly `self-improvement-meta` run writes structured `Status: pending` entries to `.learnings/LEARNINGS.md` or `.learnings/ERRORS.md`, not a harness PR.
- A weekly `learning-aggregator-ci` run can group real `.learnings/` content in Phase 1 and identify promotion candidates from that data.
- Promotion happens only through a separate, human-gated step with a distinct PR title such as `[promote] ...`.
- The existing 2026-04-17 spec-refiner closing-keyword error can flow through the new capture, aggregate, and promotion pipeline as the first end-to-end case.

## Decision

Adopt an explicit three-step outer loop:

1. **Capture**: `self-improvement-meta` writes new or updated learning records under `.learnings/` only.
2. **Aggregate**: `learning-aggregator-ci` groups `.learnings/` entries, ranks promotion candidates, and makes the promotion queue visible.
3. **Promote**: a separate, human-gated promotion workflow opens a `[promote]` PR that updates harness files, and later coordinates with eval creation work tracked in #188.

This keeps nightly runs cheap and append-only, gives the weekly aggregator real history to work with, and restores a visible approval boundary between "we observed a pattern" and "we want this to become a durable rule."

## Success Criteria

- `.github/workflows/self-improvement-meta.md` no longer instructs the agent to promote learnings directly into `AGENTS.md`, `.github/copilot-instructions.md`, `CLAUDE.md`, or workflow files during the nightly run.
- The nightly workflow instead writes structured pending entries to `.learnings/LEARNINGS.md` and `.learnings/ERRORS.md`, with a file allowlist narrowed to the paths it actually needs.
- `.github/workflows/self-improvement-meta.lock.yml` is recompiled so runtime behavior matches the updated source workflow.
- `.github/workflows/learning-aggregator-ci.md` explicitly treats `.learnings/` as its primary Phase 1 input and flags high-recurrence entries as ready for promotion in its output issue.
- `.github/workflows/learning-aggregator-ci.lock.yml` is recompiled after the source change.
- A separate promotion path exists with a distinct PR title prefix such as `[promote]`, and that path is gated by human action rather than being folded into the nightly `[learnings]` run.
- The outer-loop docs and shared guidance describe the new capture -> aggregate -> promote flow accurately.
- The Apr 17 spec-refiner error entry remains usable as the first real item that can move through the new pipeline.

## Risk Assessment

**Blast radius**: High. This changes the architecture of the factory's nightly and weekly learning loop, and may add a new workflow to the control plane.

**Rollback**: Moderate. Reverting workflow and doc changes is straightforward, but it would restore the current coupling that starves `.learnings/`.

**Key risks and mitigations**
- **Risk**: The nightly workflow switches to `.learnings/` writes, but the entry schema does not match what the aggregator expects. **Mitigation**: treat schema alignment as part of this implementation, not a later cleanup.
- **Risk**: Promotion ownership becomes ambiguous between this issue and #188. **Mitigation**: define a clear workflow boundary in this change, and keep eval-case creation as a compatible follow-on rather than part of the nightly capture path.
- **Risk**: The new promoter path is under-specified and becomes another stalled handoff. **Mitigation**: make the human gate, trigger condition, and PR title contract explicit in the workflow prompt and docs.
- **Risk**: Existing docs keep describing nightly promotion and mislead future agents. **Mitigation**: update the closest factory docs and shared guidance in the same change.

## Affected Files/Areas

- `.github/workflows/self-improvement-meta.md`: convert the nightly workflow from direct promotion to capture-only behavior.
- `.github/workflows/self-improvement-meta.lock.yml`: compiled output after the workflow change.
- `.github/workflows/learning-aggregator-ci.md`: tighten the aggregation prompt around `.learnings/` as the source of truth and promotion-candidate signaling.
- `.github/workflows/learning-aggregator-ci.lock.yml`: compiled output after the workflow change.
- A new promotion workflow source and compiled lock file, if a dedicated workflow is added for the human-gated promotion step.
- `.learnings/LEARNINGS.md` and `.learnings/ERRORS.md`: seed structure or metadata guidance if schema cleanup is needed for the new flow.
- `docs/AGENT_FACTORY.md` and any directly related factory docs that currently describe nightly promotion.
- Shared guidance files such as `AGENTS.md` and `CLAUDE.md` if they need wording changes to keep the capture and promotion lifecycle consistent.

## Open Questions

- [ ] Should the promotion workflow also create eval cases in the same PR, or should that remain the follow-on work in #188? **Can proceed.** The routing split in this issue should leave a clean interface either way.
- [ ] Should the `.learnings/` status vocabulary be normalized in the same implementation PR or in a tightly coupled follow-up? **Can proceed.** The implementation should choose one vocabulary and make the touched workflows, docs, and seed files agree.

## Implementation Checklist

- [ ] Audit the current nightly and weekly learning workflows, plus the shared docs that describe them, and confirm where direct nightly promotion is still encoded.
- [ ] Rewrite `.github/workflows/self-improvement-meta.md` so the nightly run captures structured entries in `.learnings/LEARNINGS.md` and `.learnings/ERRORS.md` with `Status: pending`, rather than promoting directly into harness files.
- [ ] Narrow the nightly workflow's `create-pull-request` allowlist to the `.learnings/` paths it actually needs, and remove obsolete harness-edit expectations from the prompt.
- [ ] Recompile `.github/workflows/self-improvement-meta.lock.yml`.
- [ ] Update `.github/workflows/learning-aggregator-ci.md` so its output makes promotion-ready groups explicit and preserves the handoff contract from aggregation to a later promotion step.
- [ ] Recompile `.github/workflows/learning-aggregator-ci.lock.yml`.
- [ ] Add or extend a dedicated promotion workflow so promotion is a separate, human-gated step with a `[promote]`-style PR title, not part of the nightly `[learnings]` path.
- [ ] Define how the promotion step consumes approved candidates from the weekly gap report, including how the Apr 17 spec-refiner error becomes the first end-to-end pipeline case.
- [ ] Align the `.learnings/` metadata guidance that the touched workflows rely on, so capture and aggregation read the same schema.
- [ ] Update the closest factory docs and shared guidance to describe the new outer-loop path accurately.
- [ ] Verify the final behavior preserves the intended sequence: nightly capture only, weekly aggregation over real learnings, human-gated promotion, then eval creation work routed through the separate promotion path.

## Rejected Alternatives

**Keep nightly promotion and also write `.learnings/` as a side effect**: This would populate `.learnings/`, but it would still conflate discovery with promotion and keep the human approval boundary muddy.

**Teach `eval-creator-ci` to own promotion directly**: This puts a PR-creating promotion path on a workflow that runs on every PR update. The cadence and trigger model are wrong for the explicit human-gated promotion step this issue asks for.

## Recommended implementer

**Choice**: copilot
**Rationale**: Auto-assignable via `implementer-dispatcher`. The work spans multiple workflow sources, compiled lock files, and factory docs, but the intended direction is now explicit enough to hand off cleanly.
