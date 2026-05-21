# Eval Index

Eval cases created from promoted learnings. Each case is a regression test that verifies a promoted rule still holds.

Managed by `self-improvement-meta` (creates eval cases for promoted learnings) and verified by `eval-creator-ci` on every PR. Do not edit manually unless adding a hand-crafted eval.

## Cases

| Eval ID | Source | Target | Method | Pattern |
|---------|--------|--------|--------|---------|
| [EVAL-004](.evals/cases/EVAL-004.md) | spec-refiner `Fixes #NN` bug (`.learnings/ERRORS.md`, 2026-04-17) — prompt-side | `.github/workflows/spec-refiner.md` | grep-check | `Before finalizing the body, grep your own draft` |
| [EVAL-005](.evals/cases/EVAL-005.md) | impl PR #187 merged without `Closes #186`, issue hand-closed (2026-04-18) — reviewer requires keyword | `.github/workflows/reviewer.md` | grep-check | `impl PR must close its source issue` |
| [EVAL-006](.evals/cases/EVAL-006.md) | spec-refiner slipped `Closes #234` into plan PR #236 despite prompt prohibition (2026-04-18) — reviewer forbids keyword on plan PRs | `.github/workflows/reviewer.md` | grep-check | `Check for forbidden closing keyword (plan PRs only)` |
| [EVAL-007](.evals/cases/EVAL-007.md) | `sync-factory-state` exceeded the GitHub GraphQL `first` limit (2026-05-20), workflow page-size guardrail | `AGENTS.md` | grep-check | GitHub GraphQL connections hard-limit `first` to 100 records. |

## Retired cases

| Eval ID | Retired | Reason |
|---------|---------|--------|
| EVAL-001 / EVAL-002 / EVAL-003 | 2026-04-18 | All three tested sibling-PR awareness strings (`Deferred`, `Deferred: covered by #NN`, `neither the current PR nor any sibling PR`) in `reviewer.md`. The #138 refactor deliberately removed the sibling-PR model, so every eval failed on every PR by design. Lesson: evals must track current product, not historical implementations. |

## Format

Each case lives in `.evals/cases/<eval-id>.md` with this frontmatter:

```yaml
---
eval-id: EVAL-NNN
source-learning: LRN-NNN
target: path/to/file
method: grep-check | command-check | file-check | rule-check
expect: found | not_found | exit_0 | contains
pattern: "the thing to check for"
created: YYYY-MM-DD
last-run: YYYY-MM-DD
last-result: pass | fail | skip
---
```
