"""
2026 context-engineering signal detection.

This module defines *content/structural* signals that go beyond file presence:
verification discipline, eval loops, deterministic hooks, telemetry/observability,
anti-drift maintenance hygiene, dynamic-workflow orchestration, harness engineering,
primitive decision discipline, plugin distribution, and curricula on-ramps.

These signals are how the scanner rewires Levels 6-8: reaching those levels requires
the matching signals (and file coverage), not file presence alone.

GROUNDING — every signal is grounded ONLY in official documentation and primary
sources. No social-media handles or attributions are encoded here.

  - Claude Code docs ............. https://docs.claude.com/en/docs/claude-code
  - Dynamic Workflows ........... https://code.claude.com/docs/en/workflows
  - Hooks ....................... https://docs.claude.com/en/docs/claude-code/hooks
  - Skills ...................... https://docs.claude.com/en/docs/claude-code/skills
  - Sub-agents .................. https://docs.claude.com/en/docs/claude-code/sub-agents
  - Plugins ..................... https://docs.claude.com/en/docs/claude-code/plugins
  - MCP ......................... https://modelcontextprotocol.io
  - Agent Skills standard ....... https://agentskills.io
  - Harness research ............ arXiv:2603.28052 (Meta-Harness),
                                  arXiv:2605.22166 (Life-Harness)
  - Anthropic Academy (free courses) and the Google "5-Day AI Agents" course
    (Day 3 explicitly covers Context Engineering) ground the curricula signal.

IMPORTANT (per the proficiency-signals research): static repository scans cannot
measure *runtime* efficacy. These signals detect documented *proxies* in committed
artifacts — they do not assert that dynamic workflows or eval loops actually run.
"""

from dataclasses import dataclass, field
from typing import Dict, List


# Signal categories used to group hits in reports.
CATEGORY_HARNESS = "harness"
CATEGORY_ORCHESTRATION = "orchestration"
CATEGORY_MAINTENANCE = "maintenance"
CATEGORY_PRIMITIVE = "primitive"
CATEGORY_CURRICULA = "curricula"


@dataclass(frozen=True)
class SignalGroup:
    """A content signal detectable via keyword/regex over instruction files.

    Patterns are matched case-insensitively as regular expressions against the
    concatenated text of a repository's AI instruction files.
    """

    key: str                      # stable slug, e.g. "verification"
    title: str                    # display title
    category: str                 # one of the CATEGORY_* constants
    description: str              # what this signal indicates
    keyword_patterns: List[str]   # regex strings (matched case-insensitively)
    weight: float                 # contribution to the bounded signal bonus
    official_reference: str       # OFFICIAL doc/source only — never a handle


# =============================================================================
# Signal registry
# =============================================================================
# Ordered roughly by the level gate they feed (L6 -> L7 -> L8), then proxies.

SIGNAL_GROUPS: List[SignalGroup] = [
    # ---- L6 gate contributors -------------------------------------------------
    SignalGroup(
        key="verification",
        title="Verification Discipline",
        category=CATEGORY_HARNESS,
        description=(
            "Explicit verification: adversarial/clean-context review, binary "
            "completion criteria, TDD, asserts, self-review before done."
        ),
        keyword_patterns=[
            r"\bverif(?:y|ication|ied)\b",
            r"\badversarial\b",
            r"\brefut(?:e|ation)\b",
            r"\bclean[- ]context\b",
            r"\bbinary completion\b",
            r"\bcompletion criteria\b",
            r"\bfailing test first\b",
            r"\bred[- ]green(?:[- ]refactor)?\b",
            r"\btest[- ]driven\b|\bTDD\b",
            r"\bassert(?:ion)?s?\b",
            r"\bdouble[- ]check\b",
            r"\bself[- ]review\b",
            r"\bverified read\b",
        ],
        weight=1.4,
        official_reference="https://docs.claude.com/en/docs/claude-code/hooks; arXiv:2603.28052",
    ),
    SignalGroup(
        key="hooks",
        title="Deterministic Hooks",
        category=CATEGORY_PRIMITIVE,
        description=(
            "Deterministic (non-LLM) lifecycle guardrails: PreToolUse/PostToolUse/"
            "SessionStart/Stop/SubagentStop matchers enforcing policy or formatting."
        ),
        keyword_patterns=[
            r"\bPreToolUse\b",
            r"\bPostToolUse\b",
            r"\bSessionStart\b",
            r"\bSubagentStop\b",
            r"\bUserPromptSubmit\b",
            r"\bdeterministic guardrail\b",
            r"\bON-EDIT\b|\bon[- ]edit hook\b",
            r"\bhooks?\b(?=.{0,40}(?:tool|edit|commit|lint|format|block))",
        ],
        weight=1.4,
        official_reference="https://docs.claude.com/en/docs/claude-code/hooks",
    ),
    SignalGroup(
        key="primitive_discipline",
        title="Primitive Decision Discipline",
        category=CATEGORY_PRIMITIVE,
        description=(
            "Cheapest-primitive-first decision logic and progressive disclosure: "
            "choosing skill vs subagent vs MCP vs hook deliberately."
        ),
        keyword_patterns=[
            r"\bprogressive disclosure\b",
            r"\bcheapest primitive\b",
            r"\bskill vs (?:subagent|mcp|hook)\b",
            r"\bwhen to use a (?:skill|subagent|hook|plugin)\b",
            r"\bleast[- ]privilege\b",
            r"\bearn(?:ed)? complexity\b",
            r"\bdecision tree\b",
            r"\bMCP for reach\b|\bskills for knowledge\b",
        ],
        weight=1.0,
        official_reference="https://docs.claude.com/en/docs/claude-code/skills; https://agentskills.io",
    ),
    # ---- L7 gate contributors -------------------------------------------------
    SignalGroup(
        key="eval_loops",
        title="Eval / Regression Loops",
        category=CATEGORY_HARNESS,
        description=(
            "Systematic evaluation infrastructure: eval cases, regression suites, "
            "held-out validation, golden tests, benchmark gates."
        ),
        keyword_patterns=[
            r"\beval(?:uation)? (?:case|loop|suite|harness|gate)s?\b",
            r"\bregression (?:test|suite|check|guard)s?\b",
            r"\bheld[- ]out\b",
            r"\bgolden (?:test|file|output)s?\b",
            r"\bbenchmark(?:s|ed|ing)?\b",
            r"\beval[- ]?id\b|\.evals\b",
        ],
        weight=1.3,
        official_reference="https://docs.claude.com/en/docs/claude-code; arXiv:2605.22166",
    ),
    SignalGroup(
        key="telemetry",
        title="Telemetry & Observability",
        category=CATEGORY_HARNESS,
        description=(
            "Measurement of the harness: telemetry, scorecards, metrics, tracing, "
            "drift incidents, audit logs, correlation IDs."
        ),
        keyword_patterns=[
            r"\btelemetry\b",
            r"\bobservability\b",
            r"\bscorecard\b",
            r"\bcorrelation id\b",
            r"\btracing\b|\btraces\b",
            r"\baudit log\b",
            r"\bdrift incident\b",
            r"\bsuccess[_ -]rate\b|\bcompletion[_ -]rate\b",
        ],
        weight=1.1,
        official_reference="https://docs.claude.com/en/docs/claude-code; arXiv:2603.28052",
    ),
    SignalGroup(
        key="maintenance_hygiene",
        title="Anti-Drift Maintenance Hygiene",
        category=CATEGORY_MAINTENANCE,
        description=(
            "Living-context practices: sentinel/canary drift checks, periodic "
            "audits/detox, steward self-healing loops, decay schedules."
        ),
        keyword_patterns=[
            r"\bsentinel\b",
            r"\bcanary\b",
            r"\bdrift detect(?:ion|ed)?\b",
            r"\bstaleness\b|\bstale context\b",
            r"\baudit (?:CLAUDE|AGENTS|the context|instruction)\b",
            r"\bdetox\b",
            r"\bsteward\b",
            r"\bdecay schedule\b|\bdecay\b",
            r"\bliving context\b",
            r"\bself[- ]healing\b",
            r"\bperiodic audit\b",
        ],
        weight=1.2,
        official_reference="https://docs.claude.com/en/docs/claude-code/memory",
    ),
    # ---- L8 gate contributors -------------------------------------------------
    SignalGroup(
        key="dynamic_workflows",
        title="Dynamic Workflows / Orchestration",
        category=CATEGORY_ORCHESTRATION,
        description=(
            "External orchestration: dynamic workflows, JS orchestration scripts, "
            "parallel subagents at scale, resumable background execution."
        ),
        keyword_patterns=[
            r"\bdynamic workflows?\b",
            r"\borchestration script\b",
            r"\bparallel subagents?\b",
            r"\bwho holds the plan\b",
            r"\bresumable\b",
            r"\bbackground execution\b",
            r"\bfan[- ]out\b.{0,30}\bverif",
            r"\bultracode\b",
            r"\.claude/workflows\b",
        ],
        weight=1.3,
        official_reference="https://code.claude.com/docs/en/workflows",
    ),
    SignalGroup(
        key="plugins",
        title="Plugin Distribution",
        category=CATEGORY_PRIMITIVE,
        description=(
            "Team-scale distribution: plugin manifests / marketplaces bundling "
            "skills, hooks, subagents, commands, and workflows."
        ),
        keyword_patterns=[
            r"\.claude-plugin\b",
            r"\bplugin manifest\b",
            r"\bmarketplace\.json\b",
            r"\bplugin marketplace\b",
            r"\binstallable (?:plugin|package)\b",
        ],
        weight=1.0,
        official_reference="https://docs.claude.com/en/docs/claude-code/plugins",
    ),
    # ---- Proxies & on-ramps ---------------------------------------------------
    SignalGroup(
        key="harness_engineering",
        title="Harness Engineering Mindset",
        category=CATEGORY_HARNESS,
        description=(
            "Explicit framing of the system around the model as the engineered "
            "surface (prompt -> context -> harness progression)."
        ),
        keyword_patterns=[
            r"\bharness engineering\b",
            r"\bcontext engineering\b",
            r"\bthe (?:system|machine|layer) around the model\b",
            r"\bprompt engineering, context engineering\b",
            r"\bfeedback loop\b",
            r"\bone (?:agent|worktree) per (?:worktree|agent)\b",
        ],
        weight=0.9,
        official_reference="arXiv:2603.28052; arXiv:2605.22166",
    ),
    SignalGroup(
        key="curricula",
        title="Curricula On-Ramps",
        category=CATEGORY_CURRICULA,
        description=(
            "References to official learning on-ramps that teach context "
            "engineering and production agent patterns."
        ),
        keyword_patterns=[
            r"\bAnthropic Academy\b",
            r"\bClaude Code 101\b",
            r"\bAgent Skills course\b|\bIntroduction to Agent Skills\b",
            r"\bModel Context Protocol course\b|\bIntro(?:duction)? to (?:the )?Model Context Protocol\b",
            r"\b5[- ]?day AI Agents\b|\bGoogle .{0,20}AI Agents\b",
            r"\bcontext engineering course\b",
        ],
        weight=0.7,
        official_reference="https://www.anthropic.com/learn (Anthropic Academy); Google 5-Day AI Agents course",
    ),
]


# Fast lookup by key.
SIGNAL_GROUPS_BY_KEY: Dict[str, SignalGroup] = {g.key: g for g in SIGNAL_GROUPS}


# =============================================================================
# Level gate definitions (used by the scanner to rewire L6-L8)
# =============================================================================
# Each upper level requires a set of named requirements. A requirement maps to
# either a signal key (content) or a structural-quality flag (filesystem). The
# scanner resolves these against HarnessSignals + StructuralQuality.
#
# Requirement vocabulary (resolved in scanner._compute_signal_gates):
#   structured_skills, hooks, subagents, verification           (L6)
#   eval_loops, telemetry, maintenance_hygiene                  (L7, cumulative)
#   orchestration, plugins, measured_outcomes                   (L8, cumulative)

LEVEL_GATE_REQUIREMENTS: Dict[int, List[str]] = {
    6: ["structured_skills", "hooks", "subagents", "verification"],
    7: ["eval_loops", "telemetry", "maintenance_hygiene"],
    8: ["orchestration", "plugins", "measured_outcomes"],
}

# Human-readable label for each gate requirement, used in reports/recommendations.
GATE_REQUIREMENT_LABELS: Dict[str, str] = {
    "structured_skills": "structured skills (YAML frontmatter or executable content)",
    "hooks": "deterministic hooks (PreToolUse/PostToolUse/etc.)",
    "subagents": "subagents (2+ agent definitions)",
    "verification": "verification discipline (verify/adversarial/TDD/asserts)",
    "eval_loops": "eval/regression loops (.evals or eval-suite references)",
    "telemetry": "telemetry/observability (metrics, scorecards, tracing)",
    "maintenance_hygiene": "anti-drift maintenance (sentinel/audit/steward/decay)",
    "orchestration": "orchestration (.claude/workflows or dynamic-workflow patterns)",
    "plugins": "plugin distribution (.claude-plugin manifest)",
    "measured_outcomes": "measured outcomes (metrics/logs/success tracking)",
}

# Official reference for each gate requirement (for actionable recommendations).
GATE_REQUIREMENT_REFERENCES: Dict[str, str] = {
    "structured_skills": "https://docs.claude.com/en/docs/claude-code/skills",
    "hooks": "https://docs.claude.com/en/docs/claude-code/hooks",
    "subagents": "https://docs.claude.com/en/docs/claude-code/sub-agents",
    "verification": "https://docs.claude.com/en/docs/claude-code/hooks",
    "eval_loops": "https://docs.claude.com/en/docs/claude-code",
    "telemetry": "https://docs.claude.com/en/docs/claude-code",
    "maintenance_hygiene": "https://docs.claude.com/en/docs/claude-code/memory",
    "orchestration": "https://code.claude.com/docs/en/workflows",
    "plugins": "https://docs.claude.com/en/docs/claude-code/plugins",
    "measured_outcomes": "https://docs.claude.com/en/docs/claude-code",
}
