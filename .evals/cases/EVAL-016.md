---
eval-id: EVAL-016
source-learning: v0.7.0 security invariant — the sandbox must never use shell=True
target: measure_ai_proficiency/efficacy.py
method: grep-check
expect: not_found
pattern: "shell=True"
created: 2026-06-02
last-run: 2026-06-02
last-result: pass
---

# EVAL-016: efficacy sandbox never uses shell=True

## Scenario

The executor runs repo-defined commands. Using `shell=True` would open a shell-injection
vector; commands must run from an argv list only.

## Regression path

`_run_sandboxed` calls `subprocess.run(argv, ...)` with no `shell=True`.

## Check

`efficacy.py` must NOT contain `shell=True`.

## Pass condition

`grep -qF 'shell=True' measure_ai_proficiency/efficacy.py` exits NON-zero (pattern absent).

## Fail condition

`shell=True` was introduced — a shell-injection vector via repo-defined commands.
