# Eval Index

Eval cases created from promoted learnings. Each case is a regression test that verifies a promoted rule still holds.

Managed by `self-improvement-meta` (creates eval cases for promoted learnings) and verified by `eval-creator-ci` on every PR. Do not edit manually unless adding a hand-crafted eval.

## Cases

| Eval ID | Source | Target | Method | Pattern |
|---------|--------|--------|--------|---------|
| [EVAL-004](.evals/cases/EVAL-004.md) | spec-refiner `Fixes #NN` bug (`.learnings/ERRORS.md`, 2026-04-17) — prompt-side | `.github/workflows/spec-refiner.md` | grep-check | `Before finalizing the body, grep your own draft` |
| [EVAL-005](.evals/cases/EVAL-005.md) | impl PR #187 merged without `Closes #186`, issue hand-closed (2026-04-18) — reviewer requires keyword | `.github/workflows/reviewer.md` | grep-check | `impl PR must close its source issue` |
| [EVAL-006](.evals/cases/EVAL-006.md) | spec-refiner slipped `Closes #234` into plan PR #236 despite prompt prohibition (2026-04-18) — reviewer forbids keyword on plan PRs | `.github/workflows/reviewer.md` | grep-check | `Check for forbidden closing keyword (plan PRs only)` |
| [EVAL-007](.evals/cases/EVAL-007.md) | June 2026 signal enhancement — verification signal (docs' #1, L6 gate) | `measure_ai_proficiency/signals.py` | grep-check | `key="verification"` |
| [EVAL-008](.evals/cases/EVAL-008.md) | June 2026 signal enhancement — anti-drift maintenance hygiene (L7 gate) | `measure_ai_proficiency/signals.py` | grep-check | `key="maintenance_hygiene"` |
| [EVAL-009](.evals/cases/EVAL-009.md) | June 2026 signal enhancement — harness-engineering proxy | `measure_ai_proficiency/signals.py` | grep-check | `key="harness_engineering"` |
| [EVAL-010](.evals/cases/EVAL-010.md) | June 2026 signal enhancement — dynamic workflows / orchestration (L8 gate) | `measure_ai_proficiency/signals.py` | grep-check | `key="dynamic_workflows"` |
| [EVAL-011](.evals/cases/EVAL-011.md) | June 2026 signal enhancement — curricula on-ramps | `measure_ai_proficiency/signals.py` | grep-check | `key="curricula"` |
| [EVAL-012](.evals/cases/EVAL-012.md) | June 2026 rewire — L6-L8 require context-engineering signals, not file coverage alone | `measure_ai_proficiency/scanner.py` | grep-check | `def _compute_signal_gates` |
| [EVAL-013](.evals/cases/EVAL-013.md) | June 2026 — conciseness/anti-bloat for always-on files (CLAUDE.md/AGENTS.md) | `measure_ai_proficiency/scanner.py` | grep-check | `def _analyze_conciseness` |

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
