---
eval-id: EVAL-003
source-learning: plan-003 sibling PR awareness (multi-PR plan scenario)
target: .github/workflows/reviewer.md
method: grep-check
expect: found
pattern: "neither the current PR nor any sibling PR"
created: 2026-04-16
last-run: 2026-04-16
last-result: pass
---

# EVAL-003: Reviewer classifies uncovered criteria as `Missed` when no sibling provides coverage

## Scenario

A plan is split across multiple sibling PRs. When the reviewer processes the active PR,
any plan criterion that is covered by neither the active PR nor any sibling PR must still
be classified as `Missed` and must trigger `needs-changes`.

Full scenario: `.evals/fixtures/multi-pr-plan-scenario.md` (Case B)

## Regression path

This eval checks that the reviewer workflow instructions retain the `Missed` rule for
genuinely uncovered criteria. Its presence confirms:

1. The reviewer defines `Missed` as applying only when no PR (current or sibling) covers
   the criterion.
2. The `Deferred` path does not accidentally absorb criteria that have no actual coverage.
3. The `Missed` verdict still triggers `needs-changes` for uncovered work.

## Check

`grep -q "neither the current PR nor any sibling PR" .github/workflows/reviewer.md`
exits with code 0.

## Pass condition

The phrase `neither the current PR nor any sibling PR` is present in
`.github/workflows/reviewer.md`, confirming the `Missed` classification is correctly
scoped to criteria with no coverage from any PR.

## Fail condition

The phrase is absent, indicating the `Missed` classification no longer guards against
uncovered criteria. Without this guard, criteria with no coverage in any PR would go
unreported, allowing genuine work gaps to pass review silently.
