---
eval-id: EVAL-009
source-learning: June 2026 signal enhancement — harness engineering captured as a 2026 frontier proxy signal grounded in official harness research (arXiv:2603.28052, arXiv:2605.22166)
target: measure_ai_proficiency/signals.py
method: grep-check
expect: found
pattern: 'key="harness_engineering"'
created: 2026-06-02
last-run: 2026-06-02
last-result: pass
---

# EVAL-009: harness-engineering proxy signal group is defined

## Scenario

The 2026 progression Model -> Prompt -> Context -> Harness names harness engineering (the system around the model) as the frontier. Static scans cannot measure runtime harness efficacy, so the scanner detects documented proxies (the keyword framing, feedback loops, worktree isolation).

## Regression path

`measure_ai_proficiency/signals.py` defines a `SignalGroup` with `key="harness_engineering"`. Removing it drops the harness proxy from the harness-orchestration MCP tool and reports.

## Check

`signals.py` must contain the literal `key="harness_engineering"`.

## Pass condition

`grep -qF 'key="harness_engineering"' measure_ai_proficiency/signals.py` exits 0.

## Fail condition

The harness-engineering signal group has been removed.

## Companion evals

- EVAL-007, EVAL-008, EVAL-010, EVAL-011: other 2026 signal groups.
- EVAL-012: the L6-L8 signal-gate rewire.
