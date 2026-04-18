# Plan 209: Plan-file retirement status markers

**Source issue**: #209
**Status**: Ready for implementation

## Problem Statement

`docs/plans/` is now large enough that agents can mistake merged historical plans for current design. The current directory gives no quick signal for whether a plan was shipped, superseded, abandoned, or still active, so a cold-start agent has to read every file and infer lifecycle state from surrounding history.

This issue asks for a lightweight retirement signal. The preferred direction is to keep plan files in place, add an explicit status marker, and teach factory prompts to treat shipped or superseded plans as historical context rather than current design.

## Interview Synthesis

The issue body provides enough detail to simulate the planning interview:

### Technical constraints

- Keep the existing `docs/plans/plan-NNN-<slug>.md` layout. Do not introduce an archive tree unless the status-field approach proves unworkable.
- Preserve the current handoff flow: `spec-refiner` opens a plan PR, a human merges it, and `plan-merged-dispatcher` activates the source issue.
- Treat workflow markdown in `.github/workflows/` as the control plane. Recompile lock files for any gh-aw workflow prompt that changes.
- Keep the status signal cheap to read. A future agent should be able to tell whether a plan is historical with one quick file read.

### Scope boundaries

- Cover the plan-file convention, the merge-time status update, the backfill for the newer merged plans, and the prompt guidance that consumes the new status.
- Keep the backfill bounded to the current merged plan cohort called out in the issue, `plan-097` through `plan-194`.
- Do not turn this into a broader plan taxonomy redesign or a general archival system.
- Do not expand the issue into unrelated factory-doc cleanup unless a file would otherwise become directly misleading.

### Risk tolerance

- Prefer a small, explicit metadata contract over implicit heuristics.
- Accept a narrow repo-write automation path if that is what the merge-time status update requires, but keep it deterministic and auditable.
- Avoid a solution that forces agents to infer freshness from git history alone.

### Success signal

- `docs/plans/README.md` documents the status convention and how to read it.
- Newly merged plan files gain `status: shipped` and `shipped-in: #NN` automatically at merge time.
- Existing merged plans in the scoped cohort are backfilled with accurate lifecycle state in one sweep.
- `spec-refiner` and `reviewer` explicitly treat `status: shipped` and `status: superseded` as historical context, not current design.

## Decision Frame

Choose **Option A** from the issue: add plan-file lifecycle metadata and keep plans in `docs/plans/`.

The implementation should treat the status field as the primary freshness signal:

```text
active      -> current design or open planning artifact
shipped     -> historical plan that was implemented
superseded  -> historical plan replaced by a newer plan or design
abandoned   -> historical plan that was intentionally not completed
```

The merge-time automation should update plan files deterministically. If `plan-merged-dispatcher` cannot safely mutate repository contents in its current form, the implementation should keep the observable behavior from the issue, document the constraint, and use the narrowest repo-write mechanism that still marks merged plans as shipped automatically.

## Success Criteria

- `docs/plans/README.md` defines the lifecycle metadata contract, including the supported `status` values and companion fields such as `shipped-in` and `superseded-by`.
- `docs/plans/README.md` explains that `shipped`, `superseded`, and `abandoned` plans are historical artifacts and should not be treated as the current design without additional corroboration.
- `plan-merged-dispatcher` automatically marks a newly merged plan file as `status: shipped` and records the source issue as `shipped-in: #NN` when those fields are missing.
- The merge-time update is idempotent. Re-running the dispatcher does not duplicate or corrupt the status block.
- The historical backfill updates the scoped merged plans from `plan-097` through `plan-194` with the correct lifecycle metadata in one PR.
- `.github/workflows/spec-refiner.md` and `.github/workflows/reviewer.md` instruct future agents to treat `status: shipped` and `status: superseded` as historical context.
- `.github/workflows/spec-refiner.lock.yml` and `.github/workflows/reviewer.lock.yml` are regenerated from the updated workflow sources.

## Risk Assessment

**Blast radius**: Medium. The change touches plan-file conventions, prompt guidance, and post-merge automation that runs on every future plan PR.

**Rollback**: Moderate. Documentation and prompt changes are easy to revert. The merge-time status writer is also reversible, but it changes repository contents after PR merge and should be backed out carefully if it writes incorrect metadata.

**Key risks and mitigations**

- **Risk**: `plan-merged-dispatcher` currently edits issues only, so adding plan-file mutation may require new permissions or a commit path that is easy to get wrong. **Mitigation**: prove the repo-write path early, keep the change idempotent, and scope it to the merged plan file only.
- **Risk**: historical plans could be mislabeled during the backfill. **Mitigation**: keep the sweep narrowly scoped, document the evidence for each non-`shipped` status in the PR summary, and prefer conservative `shipped` defaults unless there is clear supersession or abandonment evidence.
- **Risk**: agents may continue to treat old plans as current because only docs changed, not runtime prompts. **Mitigation**: update both workflow prompts and recompile their lock files in the same PR.
- **Risk**: the metadata shape may drift across files. **Mitigation**: define one canonical contract in `docs/plans/README.md` and have automation insert the same field names and ordering every time.

## Affected Files/Areas

- `docs/plans/README.md`
- `docs/plans/plan-097-*.md` through `docs/plans/plan-194-*.md`, limited to the merged plans in that scoped cohort
- `.github/workflows/plan-merged-dispatcher.yml`
- `.github/workflows/spec-refiner.md`
- `.github/workflows/spec-refiner.lock.yml`
- `.github/workflows/reviewer.md`
- `.github/workflows/reviewer.lock.yml`
- Directly related factory docs only if they would otherwise contradict the new status semantics after implementation

## Open Questions

- [ ] Should the lifecycle metadata be represented as YAML frontmatter at the top of each plan file, or as a standardized metadata block immediately below the title? Can proceed.
- [ ] What is the safest implementation shape for the merge-time `status: shipped` update in `plan-merged-dispatcher`: direct commit to the default branch, or a narrow helper flow that preserves the same observable behavior? Can proceed.
- [ ] Which scoped plans, if any, have clear evidence that they should be marked `superseded` or `abandoned` instead of the default `shipped`? Can proceed.

## Implementation Checklist

- [ ] Define the canonical lifecycle metadata contract in `docs/plans/README.md`, including supported `status` values, companion fields, and the rule that historical statuses are not current design.
- [ ] Choose and document the concrete plan-file syntax for the metadata block, favoring a format that is easy for agents and simple automation to read and prepend.
- [ ] Extend `.github/workflows/plan-merged-dispatcher.yml` so a merged plan file gains `status: shipped` and `shipped-in: #NN` automatically when the metadata is missing.
- [ ] Make the merge-time status update idempotent and scoped to the merged plan file only.
- [ ] Update `.github/workflows/spec-refiner.md` so future planning runs treat `shipped` and `superseded` plans as historical context rather than authoritative current design.
- [ ] Update `.github/workflows/reviewer.md` with the same historical-plan guidance for review-time plan reads.
- [ ] Recompile `.github/workflows/spec-refiner.lock.yml` and `.github/workflows/reviewer.lock.yml`.
- [ ] Backfill lifecycle metadata for the scoped merged plans from `plan-097` through `plan-194` in one sweep, using `shipped` as the default unless there is clear evidence for `superseded` or `abandoned`.
- [ ] Summarize any non-default backfill decisions in the implementation PR so reviewers can verify the historical classification.
- [ ] Verify that the post-merge plan handoff still works: checklist extraction remains intact, the source issue still transitions to `ready-for-implementation`, and the new status marker is present on the merged plan file.

## Rejected Alternatives

**Archive superseded plans into `docs/plans/archive/`**: Rejected for this issue. It hides history behind file moves, adds path churn, and still needs a policy for shipped-but-not-superseded plans. The issue explicitly prefers a lightweight freshness signal in place.

**Leave plan freshness implicit in git history**: Rejected. The problem is cold-start agent ambiguity, and raw history does not provide a fast, local answer.

## Recommended implementer

**Choice**: copilot
**Rationale**: Auto-assignable via `implementer-dispatcher`. The work is a bounded factory-maintenance change with a clear checklist, but it spans workflow prompts, plan docs, automation, and a historical backfill, so it benefits from the structured handoff this plan provides.
