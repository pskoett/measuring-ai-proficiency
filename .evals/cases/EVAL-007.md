---
eval-id: EVAL-007
source-learning: June 2026 signal enhancement — verification is the docs' #1 signal yet absent from the original proposal; added as an L6 gate requirement
target: measure_ai_proficiency/signals.py
method: grep-check
expect: found
pattern: 'key="verification"'
created: 2026-06-02
last-run: 2026-06-02
last-result: pass
---

# EVAL-007: verification signal group is defined

## Scenario

The proficiency-signals research ranks verification (adversarial/clean-context review, TDD, asserts, binary completion criteria) as the single most important 2026 signal — the "biggest unlock" and a top regret-minimizer. The original June 2026 proposal omitted it. It was added as a registered signal group and as an L6 gate requirement.

## Regression path

`measure_ai_proficiency/signals.py` defines a `SignalGroup` with `key="verification"`. Removing it would silently drop the highest-priority signal and break the L6 gate.

## Check

`signals.py` must contain the literal `key="verification"`.

## Pass condition

`grep -qF 'key="verification"' measure_ai_proficiency/signals.py` exits 0.

## Fail condition

The verification signal group has been removed. L6 gating loses its verification requirement and the docs' top signal goes undetected.

## Companion evals

- EVAL-008..011: other 2026 signal groups.
- EVAL-012: the L6-L8 signal-gate rewire that consumes these signals.
