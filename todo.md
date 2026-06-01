# TODO — June 2026 Context-Engineering Signal Enhancements

**Goal:** Evolve the scanner from presence detection toward structural quality,
harness/orchestration maturity, maintenance hygiene, verification, and curricula
signals. **Rewire L6–L8** so they require these signals (not just file coverage).
All detection grounded in **official documentation only** (no X handles).

## Decisions (locked with user)
- **Scoring:** Rewire L6–L8 ladder — signals gate the level number. Full primitive
  + harness gating (file presence AND content signals both required). Plus a
  bounded signal bonus to overall_score.
- **Gates:**
  - L6 ← structured skills + hooks + subagents + verification
  - L7 ← L6 + eval-loops + telemetry + anti-drift (maintenance hygiene)
  - L8 ← L7 + orchestration (.claude/workflows) + plugins + measured outcomes
- **Faithfulness:** Adapt & improve — add the docs' #1 signals (verification, hooks)
  the proposal omitted; scope runtime concepts to detectable proxies; curricula light.
- **Scope:** Code + tests + evals + docs in this repo; update personalclaude wiki; file GitHub issue/PR.

## Grounding (official sources only)
- Claude Code docs: https://docs.claude.com/en/docs/claude-code
- Dynamic Workflows: https://code.claude.com/docs/en/workflows
- Hooks / Skills / Sub-agents / Plugins / MCP: docs.claude.com/en/docs/claude-code/{hooks,skills,sub-agents,plugins,mcp}
- Agent Skills standard: https://agentskills.io
- Harness research: arXiv:2603.28052 (Meta-Harness), arXiv:2605.22166 (Life-Harness)
- Anthropic Academy + Google 5-day AI Agents course (Day 3 Context engineering)

## Plan
- [x] 1. config.py — added `.claude/workflows`, plugin manifests, `.evals` artifacts; refreshed L6–L8 descriptions.
- [x] 2. signals.py (NEW) — `SignalGroup` registry (10 groups) + `LEVEL_GATE_REQUIREMENTS`, official references only.
- [x] 3. scanner.py — SignalHit/StructuralQuality/HarnessSignals; `_analyze_signals` + `_detect_structural_quality` + `_compute_signal_gates`; **rewired** L6–L8 gating in `_calc_level_with_thresholds`; signal bonus; signal-gap recommendations.
- [x] 4. reporter.py — signals in all 4 reporters' single report + `_score_to_dict`; CSV columns; markdown multi gate column.
- [x] 5. mcp_server.py — 5 new tools.
- [x] 6. github_scanner.py — artifact-dir special-casing for remote scans.
- [x] 7. __init__.py — exported new public types; bumped to 0.6.0.
- [x] 8. tests — TestSignals (6) + TestLevelGating (5) + 6 MCP signal-tool tests.
- [x] 9. .evals — EVAL-007..012 + EVAL_INDEX.md.
- [x] 10. docs — CLAUDE.md, README.md, docs/MCP.md, new docs/SIGNALS.md.
- [x] 11. Verify — `pytest tests/` → 137 passed; eval grep-checks 6/6.
- [x] 12. wiki — personalclaude index.md updated.
- [ ] 13. GitHub — branch, commit, push, open PR + tracking issue.
- [x] 14. simplify-and-harden review pass (3 parallel auditors) — findings triaged + fixed.

## Review

**Outcome:** Implemented the June 2026 enhancement. The scanner now detects 10
context-engineering signals (grounded only in official docs) and **rewires L6–L8**
so they require signals + file coverage, not coverage alone. Surfaced across all
reporters, JSON/CSV, and 5 new MCP tools. 137 tests pass; 6 eval cases guard the
new signals/gating.

**Key design adaptations (vs. the proposal):**
- The proposal's literal `LevelConfig(category=, patterns=, maturity_impact=, examples=)`
  does not match the real dataclass; signals live in a dedicated `signals.py` module
  instead of bolted onto level configs.
- Added the two signals the proposal omitted but the official-doc research ranks #1:
  **verification** and **hooks** (both are L6 gate requirements).
- Scoped runtime-only concepts (dynamic workflows, harness engineering) to
  statically-detectable proxies, per the docs' "static scans can't measure runtime" caveat.
- No X/social-media handles in any detection pattern or recommendation — official sources only.

**Adversarial audit (simplify + harden + spec) findings fixed:**
- subagents gate aligned to `>= 2` (matched the human-facing label).
- verification gate decoupled from `.evals` infra (was conflated with L7 eval_loops).
- `measured_outcomes` surfaced as a visible signal hit (was gate-only).
- de-duplicated `_has_eval_infra()` call; bounded `_concat_instruction_text` file reads.
- memoized `_find_instruction_files` per scan (removes 3 redundant filesystem walks).
- **Drive-by fix:** pre-existing crash in `scan_github_repo_handler` / `scan_github_org_handler`
  (they passed raw temp-dir Paths/tuples to `format_score_result`; now wrap with
  `RepoScanner` + clean up temp dirs + fixed the `limit`-as-`verbose` positional bug).
  Updated 2 tests that had been mocking the buggy contract.
- Added a path-traversal guard and a JSON-decode guard in `github_scanner.py`.

**Deferred (pre-existing, out of scope):** tool-name dict duplication, a couple of
redundant inner imports, `ContentQuality` rebuild ergonomics — noted, not changed.
