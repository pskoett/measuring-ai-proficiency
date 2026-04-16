---
eval-id: EVAL-002
source-learning: plan-003 sibling PR awareness (multi-PR plan scenario)
target: .github/workflows/reviewer.md
method: grep-check
expect: found
pattern: "Deferred: covered by #NN"
created: 2026-04-16
last-run: 2026-04-16
last-result: pass
---

# EVAL-002: Reviewer classifies sibling-covered criteria as `Deferred: covered by #NN`

## Scenario

A plan is split across multiple sibling PRs. When the reviewer processes the active PR,
any plan criterion that is covered by a sibling PR must be classified as
`Deferred: covered by #NN`, not `Missed`.

Full scenario: `.evals/fixtures/multi-pr-plan-scenario.md` (Case A)

## Regression path

This eval checks that the exact output format `Deferred: covered by #NN` appears in the
reviewer workflow instructions. Its presence confirms:

1. The reviewer has a named `Deferred` classification for sibling-covered criteria.
2. The reviewer cites the covering sibling's PR number in the verdict.
3. The reviewer can distinguish a sibling-covered criterion from a genuinely uncovered one.

## Check

`grep -q "Deferred: covered by #NN" .github/workflows/reviewer.md` exits with code 0.

## Pass condition

The string `Deferred: covered by #NN` is present in `.github/workflows/reviewer.md`,
confirming the sibling-coverage classification path exists.

## Fail condition

The string is absent, indicating the `Deferred` output format was removed or was never
added. A reviewer without this format would fall back to classifying sibling-covered
criteria as `Missed`, reproducing the false `needs-changes` verdict from issue #62.
