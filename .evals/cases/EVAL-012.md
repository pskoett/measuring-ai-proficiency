---
eval-id: EVAL-012
source-learning: June 2026 rewire — Levels 6-8 require 2026 context-engineering signals (not file coverage alone); gates resolved in scanner._compute_signal_gates
target: measure_ai_proficiency/scanner.py
method: grep-check
expect: found
pattern: "def _compute_signal_gates"
created: 2026-06-02
last-run: 2026-06-02
last-result: pass
---

# EVAL-012: L6-L8 signal-gate rewire is present

## Scenario

The headline June 2026 change rewires the maturity ladder: reaching L6/L7/L8 now requires the matching context-engineering signals (structured skills + hooks + subagents + verification for L6; eval loops + telemetry + anti-drift for L7; orchestration + plugins + measured outcomes for L8) in addition to file coverage. The gates are resolved by `_compute_signal_gates` and applied in `_calc_level_with_thresholds`.

## Regression path

`measure_ai_proficiency/scanner.py` defines `def _compute_signal_gates` and passes its `gates` into `_calc_level_with_thresholds`. Removing it reverts to file-presence-only leveling, undoing the rewire.

## Check

`scanner.py` must contain the literal `def _compute_signal_gates`.

## Pass condition

`grep -qF 'def _compute_signal_gates' measure_ai_proficiency/scanner.py` exits 0.

## Fail condition

The gating method has been removed; L6-L8 can again be reached on file coverage alone without the required signals.

## Companion evals

- EVAL-007..011: the individual signal groups the gates depend on.
