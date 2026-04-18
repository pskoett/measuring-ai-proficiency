---
eval-id: EVAL-005
source-learning: impl PR #187 merged without Closes #186, issue had to be hand-closed (2026-04-18)
target: .github/workflows/reviewer.md
method: grep-check
expect: found
pattern: "impl PR must close its source issue"
created: 2026-04-18
last-run: 2026-04-18
last-result: pass
---

# EVAL-005: reviewer checks for closing keyword in bot-authored impl PR bodies

## Scenario

A bot-authored implementation PR merges without `Closes #NN`, `Fixes #NN`, or `Resolves #NN` in its body. GitHub does not auto-close the source issue. The factory chain completes but the issue stays open and requires manual cleanup.

This happened on 2026-04-18 with impl PR #187 for source issue #186. The fix shipped but #186 had to be closed by hand.

## Regression path

The fix is an explicit check in the reviewer workflow. For bot-authored PRs that are not labeled `plan-file`, reviewer must detect the absence of a closing keyword and add a Critical finding with the exact message: `impl PR must close its source issue. Add \`Closes #NN\` to the body.`

## Check

`.github/workflows/reviewer.md` must contain the literal string `impl PR must close its source issue`. This confirms the close-the-loop check is still in place.

## Pass condition

`grep -qF 'impl PR must close its source issue' .github/workflows/reviewer.md` exits with code 0.

## Fail condition

The close-the-loop check has been removed or weakened. Bot-authored implementation PRs can once again merge without closing their source issue, leaving the issue open.

## Adjacent rules worth testing (future evals)

- EVAL-004 (symmetric guard): plan PRs must NOT include closing keywords.
- The `plan-file` label exclusion: ensure plan PRs are still exempt from this check.
- Branch name pattern scope: `copilot/*` branch names should trigger the check.
