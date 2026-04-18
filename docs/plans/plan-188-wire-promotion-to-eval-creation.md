# Plan 188: Wire promotion to eval creation

**Source issue**: #188
**Status**: Ready for implementation

## Problem Statement

The outer loop currently stops after promotion. `self-improvement-meta` can promote a prevention rule into the harness files, and `eval-creator-ci` can validate existing eval cases, but no workflow creates a new `.evals/cases/EVAL-NNN.md` file or updates `.evals/EVAL_INDEX.md` when a learning is promoted.

This leaves the factory with a broken regress-test handshake. Promoted rules become durable instructions, but they do not become durable evals unless a human hand-writes them. The repo documentation and skill text still imply that eval creation already happens automatically, which no current workflow actually does.

## Interview Synthesis

Because this is a single-shot spec-refiner run, the interview is synthesized from issue #188 and the current repo state.

**Technical constraints**
- Keep `eval-creator-ci` read-only unless the plan explicitly chooses the broader redesign. The issue recommends avoiding that path.
- Reuse the eval format that the current repo already reads: `.evals/EVAL_INDEX.md` plus `.evals/cases/EVAL-NNN.md` with `eval-id`, `source-learning`, `target`, `method`, `expect`, `pattern`, `created`, `last-run`, and `last-result`.
- Keep promotion and eval creation in the same reviewed PR so the regression artifact lands atomically with the promoted rule.
- Update workflow source and compiled lock output together.

**Scope boundaries**
- Choose one implementation path. Do not partially implement both Option A and Option B.
- Focus on the promotion-to-eval gap. Do not redesign the whole outer loop or replace the existing eval verification workflow.
- Update only the docs and skill guidance that actively describe this handoff and would be wrong after the chosen implementation.
- Treat issue #186's protected-files work as a prerequisite that is already complete, not as part of this change.

**Risk tolerance**
- Prefer the smaller deterministic design that closes the loop in one place over a wider per-PR PR-creation path.
- Accept a modest amount of workflow complexity inside `self-improvement-meta` if it removes the current manual gap.
- Avoid silent fallback behavior. If a promoted learning cannot produce a valid eval, surface that fact in the PR or skip it under explicit, documented rules.

**Success signal**
- A promoted learning with a clear pass/fail assertion causes the nightly promotion PR to update the harness file(s), add a new `.evals/cases/EVAL-NNN.md`, and update `.evals/EVAL_INDEX.md` in the same commit or PR.
- The generated eval matches the format and vocabulary that `eval-creator-ci` already consumes.
- Factory docs explain that `self-improvement-meta` creates evals during promotion and `eval-creator-ci` verifies them afterward.

## Decision

Adopt **Option B: extend `self-improvement-meta` to create eval artifacts during promotion**.

This keeps promotion and regress-test creation atomic. It also preserves `eval-creator-ci` as a read-only verifier, which matches its current frontmatter, tool allowlist, and prompt. The alternative, adding PR-writing behavior to a per-PR workflow, would widen risk and make accidental eval proliferation easier if candidate detection misfires.

## Success Criteria

- `self-improvement-meta` can create eval artifacts for promoted learnings with testable patterns in the same PR that updates the harness files.
- The workflow has a deterministic rule for when to create an eval and when to skip one because the learning is not yet testable as a regression case.
- New eval files use the existing repository format consumed by `eval-creator-ci`.
- `.github/workflows/self-improvement-meta.lock.yml` is recompiled so runtime behavior matches the markdown source.
- `docs/AGENT_FACTORY.md` describes the new outer-loop path accurately.
- The implementation PR includes a short decision note that records why Option B was chosen over Option A.

## Risk Assessment

**Blast radius**: Medium. The change touches one nightly workflow, eval artifacts under `.evals/`, and the operator docs for the outer loop.

**Rollback**: Moderate. Reverting the workflow and eval artifact logic is straightforward, but it would reopen the current manual gap between promotion and regression coverage.

**Key risks and mitigations**
- **Risk**: The workflow creates evals for vague learnings that do not have a stable assertion. **Mitigation**: gate creation on an explicit testable-pattern rule and leave non-testable promotions without eval generation.
- **Risk**: Eval ID allocation or index updates drift from the existing repo format. **Mitigation**: derive the next `EVAL-NNN` from the current index or case set and update both the index and case file in the same change.
- **Risk**: Workflow source changes without a lock recompile leave runtime behavior stale. **Mitigation**: recompile immediately and review the lock diff.
- **Risk**: Documentation keeps claiming that `eval-creator-ci` creates evals. **Mitigation**: search for contradictory guidance and update only the files that actively describe the promotion and regress-test path.

## Affected Files/Areas

- `.github/workflows/self-improvement-meta.md`: extend the promotion flow so promoted learnings with clear assertions also produce eval artifacts.
- `.github/workflows/self-improvement-meta.lock.yml`: compiled workflow output after the markdown change.
- `.evals/EVAL_INDEX.md`: append the new eval entry when one is generated.
- `.evals/cases/`: add `EVAL-NNN.md` files in the existing repo format.
- `docs/AGENT_FACTORY.md`: update the outer-loop section so the promotion-to-eval path is explicit.
- Any directly contradictory guidance discovered during implementation, likely including `eval-creator` skill or workflow descriptions that currently imply eval creation happens inside `eval-creator-ci`.

## Open Questions

None at plan time. The issue recommends Option B, the prerequisite issue is already closed, and implementation can proceed without extra human input.

## Implementation Checklist

- [ ] Update `.github/workflows/self-improvement-meta.md` so its promotion flow creates eval artifacts for promoted learnings that have a clear pass/fail assertion.
- [ ] Define the workflow rule for eligible eval generation, including how to skip promoted learnings that are valuable but not yet testable as a regression case.
- [ ] Generate the next `EVAL-NNN` case file and matching `EVAL_INDEX.md` entry using the repository's current eval schema.
- [ ] Keep promotion and eval creation in one reviewed PR, and ensure the implementation PR body carries a short decision note for Option B.
- [ ] Recompile `.github/workflows/self-improvement-meta.lock.yml` after the markdown workflow change.
- [ ] Update `docs/AGENT_FACTORY.md` and any directly contradictory skill or workflow guidance so they describe `self-improvement-meta` as the eval-creation point and `eval-creator-ci` as the verifier.
- [ ] Demonstrate the new path with a representative promoted-learning scenario and record the outcome in the implementation PR so reviewers can confirm the end-to-end handshake.
- [ ] Run the repository's existing verification command set after the workflow and documentation changes land.

## Rejected Alternatives

**Option A, extend `eval-creator-ci` to write PRs**: This would put PR-creation behavior into a workflow that runs on every PR. The issue correctly calls out the proliferation risk. It also conflicts with the workflow's current read-only design, so it is a wider redesign than needed.

## Recommended implementer

**Choice**: copilot
**Rationale**: Auto-assignable via `implementer-dispatcher`. The work is a focused workflow-and-docs change with a clear checklist, concrete acceptance criteria, and no unresolved design decision left after planning.
