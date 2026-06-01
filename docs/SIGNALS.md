# 2026 Context-Engineering Signals

`measure-ai-proficiency` (v0.6.0+) goes beyond file *presence* and detects the
context-engineering **signals** that distinguish production-grade agent setups in
2026: structural primitive quality, verification, deterministic hooks, eval loops,
telemetry, anti-drift maintenance hygiene, dynamic-workflow orchestration, plugin
distribution, harness engineering, and curricula on-ramps.

These signals **rewire Levels 6-8**: reaching those levels now requires the
matching signals *and* file coverage — not file coverage alone.

> **Grounding.** Every signal is grounded only in official documentation and
> primary sources (Claude Code docs, the Dynamic Workflows docs, the harness
> research papers, Anthropic Academy, and the Google 5-Day AI Agents course).
> Detection patterns never reference social-media handles.
>
> **Limitation.** Static scans cannot measure *runtime* efficacy. These signals
> detect documented **proxies** in committed artifacts (keywords + filesystem
> structure), not whether dynamic workflows or eval loops actually run.

## Signal groups

Defined in [`measure_ai_proficiency/signals.py`](../measure_ai_proficiency/signals.py).

| Key | Category | What it detects | Official reference |
|-----|----------|-----------------|--------------------|
| `verification` | harness | Adversarial/clean-context review, TDD, asserts, binary completion criteria | docs.claude.com/.../hooks; arXiv:2603.28052 |
| `hooks` | primitive | Deterministic PreToolUse/PostToolUse/SessionStart/Stop/SubagentStop guardrails | docs.claude.com/.../hooks |
| `primitive_discipline` | primitive | Cheapest-primitive-first decisions, progressive disclosure | docs.claude.com/.../skills; agentskills.io |
| `eval_loops` | harness | Eval cases, regression suites, held-out/golden/benchmark gates | docs.claude.com; arXiv:2605.22166 |
| `telemetry` | harness | Telemetry, scorecards, tracing, drift incidents, audit logs | docs.claude.com; arXiv:2603.28052 |
| `maintenance_hygiene` | maintenance | Sentinel/canary drift checks, audit/detox, steward loops, decay | docs.claude.com/.../memory |
| `dynamic_workflows` | orchestration | Dynamic workflows, orchestration scripts, parallel subagents, resumability | code.claude.com/docs/en/workflows |
| `plugins` | primitive | Plugin/marketplace manifests bundling primitives for teams | docs.claude.com/.../plugins |
| `harness_engineering` | harness | The system-around-the-model framing, feedback loops, worktree isolation | arXiv:2603.28052; arXiv:2605.22166 |
| `curricula` | curricula | Anthropic Academy / Google 5-Day AI Agents references | anthropic.com/learn; Google 5-Day AI Agents |

## Structural quality

Beyond keywords, the scanner inspects the **6 primitives** structurally
(`StructuralQuality`):

- **Skills** — count, YAML frontmatter, executable/data content (non-`.md` files
  in the skill folder), and in-skill verification language.
- **Hooks** — `.claude/hooks/` contents and `hooks` config / lifecycle events in
  `.claude/settings.json`.
- **Subagents** — agent definition files under `.claude/agents`, `.github/agents`, `agents/`.
- **Workflows** — a non-empty `.claude/workflows/` directory.
- **Plugins** — `.claude-plugin/` (or nested) manifests.

These roll up into a 0-10 `structural_score`.

## The L6-L8 rewire (gating)

`LEVEL_GATE_REQUIREMENTS` (in `signals.py`) defines what each upper level needs.
The scanner resolves them in `_compute_signal_gates` and applies them in
`_calc_level_with_thresholds`. The ladder is monotonic, so requirements are
cumulative — you cannot skip a gate.

| Level | Requires (in addition to file coverage) |
|-------|------------------------------------------|
| **L6** | structured skills **+** hooks **+** subagents **+** verification |
| **L7** | L6 **+** eval loops **+** telemetry **+** anti-drift maintenance hygiene |
| **L8** | L7 **+** orchestration (`.claude/workflows`) **+** plugins **+** measured outcomes |

If file coverage would place a repo at L8 but the signal gates are not met, the
achieved level is capped at the highest fully-satisfied level (and the score
drops accordingly via the per-level minimum scores). The reports and the
`get_recommendations` output explain exactly which signals are missing, with an
official-docs link for each.

## Conciseness / context-hygiene (anti-bloat)

Always-loaded "floor" files (`CLAUDE.md`, `AGENTS.md`, copilot-instructions) are a
**permanent context tax** — large monolithic files degrade results and crowd out
working context. The scanner flags an always-on file as **bloated** when it exceeds
`word_threshold_bloat` (default **1500 words**, configurable in `.ai-proficiency.yaml`
under `quality:`), emits a `BLOAT:` warning, and applies a small validation penalty
(up to 3 pts, scaled by overage). On-demand **skill bodies are exempt** — progressive
disclosure means they cost nothing until invoked, so length there is fine. The fix the
tool nudges toward: keep a thin routing layer in the floor file and push detail into
scoped/on-demand files (skills, "See X.md" pointers). Grounded in the Claude Code
memory/best-practices guidance to keep `CLAUDE.md` concise and human-readable.

## Signal bonus

Matched signals plus structural quality contribute a **bounded bonus (0-10)** to
`overall_score`, added alongside the cross-reference bonus and clamped at 100.
Gating affects the *level*; the bonus affects the *score within a level*.

## Where signals surface

- **Terminal / Markdown reports** — a "Context Engineering Signals (2026)" section
  with per-signal status, structural quality, and L6-L8 gate status.
- **JSON / CSV** — a `signals` block (JSON) and `signal_bonus`,
  `structural_score`, `matched_signal_count`, `l6_gate`, `l7_gate`, `l8_gate`
  columns (CSV).
- **MCP tools** — `check_harness_orchestration_quality`,
  `scan_for_maintenance_hygiene`, `get_dynamic_workflow_recommendations`,
  `curricula_alignment`, `cheapest_primitive_decision_tree_report`, and the
  existing `scan_current_repo` / `get_recommendations` (see [MCP.md](MCP.md)).

## Extending the signals

Add a new `SignalGroup` to `SIGNAL_GROUPS` in `signals.py` (keyword patterns +
weight + an **official** reference). To make it gate a level, add its key to
`LEVEL_GATE_REQUIREMENTS` and resolve it in `RepoScanner._compute_signal_gates`.
Add a regression eval under `.evals/cases/` so the signal can't be silently removed.
