# Eval Index

Eval cases created from promoted learnings. Each case is a regression test that verifies a promoted rule still holds.

Managed by `eval-creator-ci`. Do not edit manually unless adding a hand-crafted eval.

## Cases

| Eval ID | Source | Target | Method | Pattern |
|---------|--------|--------|--------|---------|
| [EVAL-004](.evals/cases/EVAL-004.md) | spec-refiner `Fixes #NN` bug (`.learnings/ERRORS.md`, 2026-04-17) | `.github/workflows/spec-refiner.md` | grep-check | ``NEVER** write `Closes`` |

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
