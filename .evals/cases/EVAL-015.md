---
eval-id: EVAL-015
source-learning: v0.7.0 security invariant — execution must be hard-blocked on remote/GitHub-scanned repos
target: measure_ai_proficiency/efficacy.py
method: grep-check
expect: found
pattern: "bool(execute) and not is_remote"
created: 2026-06-02
last-run: 2026-06-02
last-result: pass
---

# EVAL-015: efficacy execution is hard-blocked on remote repos

## Scenario

`--prove-exec` runs repo-defined code. Running it against a remote/GitHub-scanned repo
(untrusted) would be dangerous, so EfficacyAnalyzer forces execution off when is_remote.

## Regression path

The analyzer computes `self.execute = bool(execute) and not is_remote`.

## Check

`efficacy.py` must contain the literal `bool(execute) and not is_remote`.

## Pass condition

`grep -qF 'bool(execute) and not is_remote' measure_ai_proficiency/efficacy.py` exits 0.

## Fail condition

The remote-exec block was removed; remote scans could execute untrusted repo code.
