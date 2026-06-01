---
eval-id: EVAL-014
source-learning: v0.7.0 efficacy harness — the proving engine must stay present
target: measure_ai_proficiency/efficacy.py
method: grep-check
expect: found
pattern: "class EfficacyAnalyzer"
created: 2026-06-02
last-run: 2026-06-02
last-result: pass
---

# EVAL-014: efficacy proving engine is present

## Scenario

v0.7.0 turns the scanner from a context linter into a context proving harness: a
`--prove` pass that runs the repo's artifacts and reports a report-only Efficacy Score.

## Regression path

`measure_ai_proficiency/efficacy.py` defines `EfficacyAnalyzer` (commands/hooks/context-budget provers).

## Check

`efficacy.py` must contain `class EfficacyAnalyzer`.

## Pass condition

`grep -qF 'class EfficacyAnalyzer' measure_ai_proficiency/efficacy.py` exits 0.

## Fail condition

The efficacy engine was removed.
