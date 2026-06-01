---
eval-id: EVAL-013
source-learning: June 2026 — conciseness/context-hygiene: always-on files (CLAUDE.md/AGENTS.md) should be concise; oversized monolithic files are a permanent context tax and make results worse
target: measure_ai_proficiency/scanner.py
method: grep-check
expect: found
pattern: "def _analyze_conciseness"
created: 2026-06-02
last-run: 2026-06-02
last-result: pass
---

# EVAL-013: conciseness / anti-bloat detection for always-on files

## Scenario

The hierarchical/scoped-context research (and the Claude Code memory/best-practices
docs) establish that always-loaded instruction files are a permanent context tax:
large monolithic CLAUDE.md/AGENTS.md files degrade results. Mature setups keep a
thin routing layer and push detail into scoped, on-demand files (skills, "See X.md"
pointers). The scanner previously only rewarded word count (more = "substance") and
never penalized bloat — the opposite of the principle.

## Regression path

`measure_ai_proficiency/scanner.py` defines `_analyze_conciseness`, which flags
always-on files over the (configurable) `word_threshold_bloat` as bloated, emits a
`BLOAT:` warning, and adds a context-hygiene penalty. On-demand skill bodies are
exempt (progressive disclosure).

## Check

`scanner.py` must contain the literal `def _analyze_conciseness`.

## Pass condition

`grep -qF 'def _analyze_conciseness' measure_ai_proficiency/scanner.py` exits 0.

## Fail condition

Conciseness detection removed; the tool again rewards length without penalizing
oversized always-on files.

## Companion evals

- EVAL-007..012: the 2026 signal groups + the L6-L8 gating rewire.
