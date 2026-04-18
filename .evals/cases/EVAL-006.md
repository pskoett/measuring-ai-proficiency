---
eval-id: EVAL-006
source-learning: spec-refiner emitted closing keyword in plan PR body despite prompt prohibition (plan PR #236, source issue #234, 2026-04-18)
target: .github/workflows/reviewer.md
method: grep-check
expect: found
pattern: "Check for forbidden closing keyword (plan PRs only)"
created: 2026-04-18
last-run: 2026-04-18
last-result: pass
---

# EVAL-006: reviewer runtime check for closing keywords in plan PR bodies

## Scenario

EVAL-004 verifies that `spec-refiner.md` contains the NEVER-closing-keyword prohibition in its prompt. But on 2026-04-18 the model emitted `Closes #234` in plan PR #236's body despite the prohibition. GitHub auto-closed issue #234 on merge. `plan-merged-dispatcher` caught and reopened it as defense-in-depth, but the merge-and-reopen churn is avoidable if reviewer catches the violating PR body *before* merge.

Prompt-level prohibition alone is insufficient; a runtime output check is the second layer of defense.

## Regression path

Reviewer Step 3b (added 2026-04-18) greps plan PR bodies for `(close[sd]?|fix(es|ed)?|resolve[sd]?)\s+#\d+` and applies `needs-changes` if any match is found. This eval verifies the step is still in the workflow source.

## Check

`.github/workflows/reviewer.md` must contain the literal string `Check for forbidden closing keyword (plan PRs only)` — the exact step heading used in the 2026-04-18 addition.

## Pass condition

`grep -qF 'Check for forbidden closing keyword (plan PRs only)' .github/workflows/reviewer.md` exits with code 0.

## Fail condition

Step 3b has been removed from reviewer.md. Plan PRs could again merge with closing keywords, auto-closing source issues. `plan-merged-dispatcher`'s auto-reopen still catches it, but the pre-merge guard is gone and the churn returns.

## Companion evals

- EVAL-004: prompt-side prohibition in `spec-refiner.md`.
- EVAL-005: reviewer check for REQUIRED closing keywords in impl PRs (the opposite direction).
- EVAL-006 (this one): reviewer check for FORBIDDEN closing keywords in plan PRs.

All three must pass for the full defense chain to be in place.
