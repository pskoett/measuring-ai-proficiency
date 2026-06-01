---
eval-id: EVAL-008
source-learning: June 2026 signal enhancement — anti-drift maintenance hygiene (sentinel/canary, audit/detox, steward, decay) added as an L7 gate requirement
target: measure_ai_proficiency/signals.py
method: grep-check
expect: found
pattern: 'key="maintenance_hygiene"'
created: 2026-06-02
last-run: 2026-06-02
last-result: pass
---

# EVAL-008: maintenance-hygiene (anti-drift) signal group is defined

## Scenario

The living-context research treats static instruction files as artifacts that rot silently (disk-memory drift). Mature teams add sentinel/canary drift checks, periodic CLAUDE.md/AGENTS.md audits (detox), steward self-healing loops, and decay schedules. This is an L7 gate requirement.

## Regression path

`measure_ai_proficiency/signals.py` defines a `SignalGroup` with `key="maintenance_hygiene"`. Removing it would drop anti-drift detection and break the L7 gate.

## Check

`signals.py` must contain the literal `key="maintenance_hygiene"`.

## Pass condition

`grep -qF 'key="maintenance_hygiene"' measure_ai_proficiency/signals.py` exits 0.

## Fail condition

The maintenance-hygiene signal group has been removed; L7 gating loses its anti-drift requirement.

## Companion evals

- EVAL-007, EVAL-009..011: other 2026 signal groups.
- EVAL-012: the L6-L8 signal-gate rewire.
