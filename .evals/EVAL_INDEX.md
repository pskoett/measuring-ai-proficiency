# Eval Index

Eval cases created from promoted learnings. Each case is a regression test that verifies a promoted rule still holds.

Managed by `eval-creator-ci`. Do not edit manually unless adding a hand-crafted eval.

## Cases

| Eval ID | Source | Target | Method | Pattern |
|---------|--------|--------|--------|---------|
| [EVAL-001](.evals/cases/EVAL-001.md) | plan-003 sibling PR awareness | `.github/workflows/reviewer.md` | grep-check | `Deferred` |

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
