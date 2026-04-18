---
plan-id: plan-210
status: shipped
shipped-in: "#215"
---
# Plan 210: Factory health weekly report

**Source issue**: #210
**Status**: Ready for implementation

## Problem Statement

The factory has no built-in weekly health view. Operators currently have to reconstruct basic signals by hand from workflow runs, issues, and PRs to answer questions about success rate, skipped noise, failure modes, handoff latency, and human overrides.

Issue #210 asks for a dedicated weekly workflow, `factory-health`, that produces one stable `[health]` issue summarizing the factory's recent operating state. The implementation should stay inside the current GitHub-native factory model: scheduled workflow, repository data only, stable report shape, and no extra telemetry system.

## Interview Synthesis

**Technical constraints**
- Add a new agentic workflow at `.github/workflows/factory-health.md` and compile the matching `.lock.yml`.
- Trigger the workflow on a Sunday schedule plus `workflow_dispatch`, so it runs before the existing Monday weekly workflows.
- Use GitHub-native repository data only: workflow runs, issues, PRs, labels, and timestamps. Do not add external telemetry, storage, or services.
- Emit one issue titled `[health] Factory weekly report YYYY-MM-DD` using `create-issue` with `close-older-issues: true`.
- Keep the report limited to the metrics named in the issue: workflow outcomes, failure categorization, handoff latency, unresolved signals, and human override rate. Do not add aspirational metrics.

**Scope boundaries**
- Implement the new workflow and its compiled lock file.
- Update `docs/AGENT_FACTORY.md` with an observability section or equivalent discoverable reference to the new weekly cadence.
- Update `docs/FACTORY_STATE_MACHINE.md` so the workflow trigger table reflects the new scheduled report.
- Reuse existing weekly-report workflow patterns where they fit. Do not fold this work into `self-improvement-meta` or redesign the rest of the factory.
- Do not add a dashboard, database, or cross-repo aggregation layer in this pass.

**Risk tolerance**
- Prefer deterministic heuristics and explicit caveats over broad but shaky inference.
- Preserve existing factory behavior. This is an additive observability workflow, not a routing change.
- Favor a stable report template with fixed headers and table shapes so week-to-week diffs are meaningful.

**Success signal**
- A manual or scheduled run creates a `[health]` issue that answers the requested weekly operational questions in a stable format.
- The report includes at least the requested sections for workflow outcomes, failure categorization, handoff latency, unresolved signals, and human override rate.
- `docs/AGENT_FACTORY.md` and `docs/FACTORY_STATE_MACHINE.md` both reflect the new workflow and cadence.

## Success Criteria

- `.github/workflows/factory-health.md` exists and defines a Sunday schedule plus `workflow_dispatch`.
- `.github/workflows/factory-health.lock.yml` is committed and matches the workflow source.
- A run of `factory-health` creates one issue titled `[health] Factory weekly report YYYY-MM-DD`.
- The health issue contains stable headers and stable table shapes covering:
  - workflow run counts by workflow and conclusion
  - failure categorization for failures in the reporting window
  - handoff latency for the spec-to-plan path
  - unresolved signals: open `workflow-health` issues, open `[aw] ... failed` issues, and plan PRs older than 48 hours
  - merged PRs that still carried `needs-changes`
- The workflow uses `create-issue` with `close-older-issues: true`.
- `docs/AGENT_FACTORY.md` includes a discoverable observability note that points operators to the weekly health cadence.
- `docs/FACTORY_STATE_MACHINE.md` includes `factory-health` in the workflow trigger table.

## Risk Assessment

**Blast radius**: Medium. The change adds one new workflow plus small factory-doc updates.

**Rollback**: Moderate. Reverting the new workflow and doc references cleanly removes the feature if the report proves noisy or misleading.

**Key risks and mitigations**
- **Risk**: Handoff latency may be computed from incomplete event data if label-transition timestamps are not directly exposed by the default read paths. **Mitigation**: plan for a GitHub-native primary source such as timeline or event API data, and fall back to an explicit `n/a` or documented proxy instead of inventing a number.
- **Risk**: Failure categorization can become noisy if the classifier is too broad. **Mitigation**: seed the first version with narrow, auditable heuristics tied to concrete log text or conclusions, then bucket unknown cases explicitly.
- **Risk**: Weekly reports can drift in structure and become hard to diff. **Mitigation**: define a fixed issue template with stable section order and table columns from the first implementation.
- **Risk**: The workflow may duplicate existing reporting or blend into the learnings loop. **Mitigation**: keep the workflow scoped to observability only and document the distinction from `learning-aggregator-ci` and `self-improvement-meta`.

## Affected Files/Areas

- `.github/workflows/factory-health.md`: new weekly observability workflow source.
- `.github/workflows/factory-health.lock.yml`: compiled workflow artifact.
- `docs/AGENT_FACTORY.md`: operator-facing factory guide and workflow inventory.
- `docs/FACTORY_STATE_MACHINE.md`: workflow trigger table for the live factory state machine.
- `.github/workflows/learning-aggregator-ci.md`: reference pattern for weekly issue creation and `close-older-issues`. Read-only unless implementation finds a directly related doc cross-link worth adding.
- `.github/workflows/ai-proficiency-weekly-report.md`: reference pattern for a weekly reporting workflow. Read-only in this task.
- `.github/workflows/self-improvement-meta.md`: reference pattern for failure-oriented weekly or scheduled analysis. Read-only in this task.

## Open Questions

- [ ] What is the authoritative data source for `needs-spec` → plan PR latency in this repo, issue/PR timeline events via `gh api` or another GitHub-native event surface? - Can proceed
- [ ] Which initial failure-signature patterns are specific enough to separate infra, workflow bug, and agent error without turning the first classifier into a grab bag? - Can proceed
- [ ] Should the human-override denominator include all merged PRs in the repo, or only PRs that entered the factory review path and therefore could have carried `needs-changes` meaningfully? - Can proceed

## Implementation Checklist

- [ ] Review existing reporting workflows and choose the frontmatter pattern for `factory-health`: Sunday schedule, `workflow_dispatch`, read permissions, GitHub toolsets, and `create-issue` with `close-older-issues: true`.
- [ ] Create `.github/workflows/factory-health.md` with instructions that gather the last reporting window's workflow runs, open workflow-health issues, open `[aw] ... failed` issues, open stale plan PRs, and merged PRs carrying `needs-changes`.
- [ ] Define a fixed report template with stable section order and stable table columns for outcomes, failure categories, handoff latency, unresolved signals, and human overrides.
- [ ] Add a narrow first-pass failure categorization rubric for infra vs workflow bug vs agent error, with an explicit unknown bucket when evidence is insufficient.
- [ ] Implement the handoff-latency calculation for the spec-to-plan path, including a documented fallback when exact label-event timestamps are unavailable.
- [ ] Recompile the workflow so `.github/workflows/factory-health.lock.yml` matches the new source.
- [ ] Update `docs/AGENT_FACTORY.md` with an observability section or equivalent note that explains what `factory-health` reports and when it runs.
- [ ] Update `docs/FACTORY_STATE_MACHINE.md` so the workflow trigger table includes `factory-health` and its primary output.
- [ ] Run one manual-dispatch validation of the new workflow and confirm it produces the expected `[health]` issue format.
- [ ] Review the final issue template and doc wording for stable naming, stable section order, and consistency with the issue's non-aspirational metric list.

## Rejected Alternatives

**Fold the report into `self-improvement-meta`**: Rejected. That workflow already owns learning capture and promotion. Mixing weekly observability into the nightly learning loop would blur responsibilities and make failures harder to debug.

**Add an external dashboard or metrics store**: Rejected. The issue explicitly scopes v1 to GitHub-native data already available from workflow runs, issues, and PRs.

## Recommended implementer

**Choice**: copilot
**Rationale**: Auto-assignable via `implementer-dispatcher`. The work is bounded to one new workflow, one compiled lock file, and two doc updates, with strong prior art already in the repository.
