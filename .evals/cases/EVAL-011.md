---
eval-id: EVAL-011
source-learning: June 2026 signal enhancement — curricula on-ramps (Anthropic Academy, Google 5-Day AI Agents) as a light content signal grounding levels in official learning paths
target: measure_ai_proficiency/signals.py
method: grep-check
expect: found
pattern: 'key="curricula"'
created: 2026-06-02
last-run: 2026-06-02
last-result: pass
---

# EVAL-011: curricula on-ramp signal group is defined

## Scenario

Official free curricula (Anthropic Academy; Google 5-Day AI Agents, whose Day 3 covers Context Engineering) ground the maturity model in real learning paths. Curricula are the weakest per-repo scannable signal, so they carry the lowest weight and are detected as a light content reference.

## Regression path

`measure_ai_proficiency/signals.py` defines a `SignalGroup` with `key="curricula"`. It powers the curricula_alignment MCP tool.

## Check

`signals.py` must contain the literal `key="curricula"`.

## Pass condition

`grep -qF 'key="curricula"' measure_ai_proficiency/signals.py` exits 0.

## Fail condition

The curricula signal group has been removed; curricula_alignment loses its detector.

## Companion evals

- EVAL-007..010: other 2026 signal groups.
- EVAL-012: the L6-L8 signal-gate rewire.
