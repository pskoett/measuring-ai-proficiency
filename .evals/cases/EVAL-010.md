---
eval-id: EVAL-010
source-learning: June 2026 signal enhancement — dynamic workflows / orchestration scoped to detectable artifacts (.claude/workflows) as the L8 orchestration gate; grounded in code.claude.com/docs/en/workflows
target: measure_ai_proficiency/signals.py
method: grep-check
expect: found
pattern: 'key="dynamic_workflows"'
created: 2026-06-02
last-run: 2026-06-02
last-result: pass
---

# EVAL-010: dynamic-workflows / orchestration signal group is defined

## Scenario

Official Dynamic Workflows (May 28 2026) are a runtime feature; static scans can only detect committed artifacts (a .claude/workflows directory, orchestration scripts) and documented patterns. This signal feeds the L8 orchestration gate and the get_dynamic_workflow_recommendations MCP tool.

## Regression path

`measure_ai_proficiency/signals.py` defines a `SignalGroup` with `key="dynamic_workflows"`. The config also adds `.claude/workflows/` artifacts to Level 8. Removing the signal breaks the L8 orchestration gate.

## Check

`signals.py` must contain the literal `key="dynamic_workflows"`.

## Pass condition

`grep -qF 'key="dynamic_workflows"' measure_ai_proficiency/signals.py` exits 0.

## Fail condition

The dynamic-workflows signal group has been removed; L8 gating loses its orchestration requirement.

## Companion evals

- EVAL-007..009, EVAL-011: other 2026 signal groups.
- EVAL-012: the L6-L8 signal-gate rewire.
