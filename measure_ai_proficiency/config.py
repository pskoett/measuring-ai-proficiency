"""
Configuration for AI proficiency measurement.

Defines the file patterns to look for at each maturity level (1-8).
Aligned with Steve Yegge's 8-stage AI coding proficiency model.
Focused on the big four: Claude Code, GitHub Copilot, Cursor, and OpenAI Codex.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class LevelConfig:
    """Configuration for a single maturity level."""
    name: str
    description: str
    file_patterns: List[str]
    directory_patterns: List[str] = field(default_factory=list)
    weight: float = 1.0


# Level 1: Zero or Near-Zero AI (Yegge Stage 1)
# Baseline level - no AI-specific context files, maybe just README
LEVEL_1_PATTERNS = LevelConfig(
    name="Level 1: Zero AI",
    description="No AI-specific context files, baseline level",
    file_patterns=[
        # Only generic files that don't indicate AI usage
        "README.md",
    ],
    weight=0.5
)

# Level 2: Basic agent use with minimal context (Yegge Stage 2)
LEVEL_2_PATTERNS = LevelConfig(
    name="Level 2: Basic Instructions",
    description="Basic context files exist with minimal project information",
    file_patterns=[
        # Claude Code
        "CLAUDE.md",
        "AGENTS.md",
        # GitHub Copilot
        ".github/copilot-instructions.md",
        # Cursor
        ".cursorrules",
        # OpenAI Codex
        "CODEX.md",
    ],
    weight=1.0
)

# Level 3: Trusted agent with comprehensive context (Yegge Stage 3)
LEVEL_3_PATTERNS = LevelConfig(
    name="Level 3: Comprehensive Context",
    description="Detailed instruction files covering architecture, conventions, and patterns",
    file_patterns=[
        # Agent instruction files (detailed versions)
        # Copilot scoped instructions
        ".github/instructions/*.instructions.md",
        ".github/*.md",
        # Cursor rules directory
        ".cursor/rules/*.md",
        ".cursor/rules/*.mdc",
        ".cursor/*.md",
        # VSCode AI instructions
        ".vscode/*.md",
        # Codex CLI
        ".codex/*.md",

        # Architecture and specification files
        "ARCHITECTURE.md",
        "docs/ARCHITECTURE.md",
        "*/docs/ARCHITECTURE.md",
        "docs/architecture/*.md",
        "spec.md",
        "specs/*.md",
        "docs/adr/*.md",
        "docs/architecture/decisions/*.md",
        "DESIGN.md",
        "docs/design/*.md",
        "docs/rfcs/*.md",
        "TECHNICAL_OVERVIEW.md",
        "API.md",
        "docs/API.md",
        "*/docs/API.md",
        "docs/api/*.md",
        "DATA_MODEL.md",
        "docs/data/*.md",
        "SECURITY.md",
        "docs/SECURITY.md",
        "GLOSSARY.md",
        "DOMAIN.md",

        # Conventions and standards
        "CONVENTIONS.md",
        "STYLE.md",
        "CONTRIBUTING.md",
        "PATTERNS.md",
        "ANTI_PATTERNS.md",
        "CODE_REVIEW.md",
        "PR_REVIEW.md",
        "PULL_REQUEST_TEMPLATE.md",
        ".github/PULL_REQUEST_TEMPLATE.md",
        ".github/pull_request_template.md",
        "docs/PR_REVIEW.md",
        "docs/CODE_REVIEW.md",
        "NAMING.md",

        # Development context
        "DEVELOPMENT.md",
        "docs/DEVELOPMENT.md",
        "SETUP.md",
        "docs/SETUP.md",
        "docs/LOCAL_SETUP.md",
        "*/docs/LOCAL_SETUP.md",
        "TESTING.md",
        "docs/TESTING.md",
        "*/docs/TESTING.md",
        "DEBUGGING.md",
        "PERFORMANCE.md",
        "DEPLOYMENT.md",
        "docs/DEPLOYMENT.md",
        "*/docs/DEPLOYMENT.md",
        "INFRASTRUCTURE.md",
        "DEPENDENCIES.md",
        "MIGRATION.md",
        "CHANGELOG.md",
        "docs/runbooks/*.md",
        "docs/guides/*.md",
        # Catch additional docs files
        "docs/*.md",
        "*/docs/*.md",
        # Catch .md files in common project subdirectories
        "backend/*.md",
        "frontend/*.md",
        "server/*.md",
        "client/*.md",
        "api/*.md",
        "src/*.md",
        "lib/*.md",
        "packages/*/*.md",
        "services/*/*.md",
        # Catch deeply nested .md files (templates, nested folders, etc.)
        "*/*/*.md",
        "*/*/*/*.md",
    ],
    directory_patterns=[
        "docs/architecture",
        "docs/adr",
        "docs/design",
        "docs/rfcs",
        "docs/api",
        "docs/runbooks",
        "docs/guides",
        "examples",
        ".cursor/rules",
    ],
    weight=1.5
)

# Level 4: Skills & Automation (Yegge Stage 4)
LEVEL_4_PATTERNS = LevelConfig(
    name="Level 4: Skills & Automation",
    description="Skill files, memory systems, hooks, and workflow definitions",
    file_patterns=[
        # Skill files - Claude Code, GitHub Copilot, Cursor, and OpenAI Codex
        "SKILL.md",
        "skills/*.md",
        "skills/*/SKILL.md",
        ".claude/skills/*/SKILL.md",
        ".claude/skills/*/*/*.md",
        ".github/skills/*/SKILL.md",
        ".github/skills/*/*.md",
        ".copilot/skills/*/SKILL.md",
        ".copilot/skills/*/*.md",
        ".cursor/skills/*/SKILL.md",
        ".cursor/skills/*/*.md",
        ".codex/skills/*/SKILL.md",
        ".codex/skills/*/*.md",
        "CAPABILITIES.md",

        # Workflow and automation
        "WORKFLOWS.md",
        "COMMANDS.md",
        ".claude/commands/*.md",
        "Makefile",
        "justfile",
        "scripts/*.sh",
        "scripts/*.py",
        "scripts/*.md",
        "scripts/README.md",

        # Memory and learning
        "MEMORY.md",
        "LEARNINGS.md",
        "DECISIONS.md",
        ".memory/*.md",
        ".memory/*.json",
        "RETROSPECTIVES.md",
        "KNOWN_ISSUES.md",
        "TROUBLESHOOTING.md",
        "FAQ.md",
        "GOTCHAS.md",
        "HISTORY.md",
        "context.yaml",
        "context.json",

        # Context files for agents
        ".context/*.md",
        ".ai/*.md",
        "PROMPTS.md",
        ".prompts/*.md",
        "personas/*.md",

        # Agent personality and behavioral constitution (ClawdBot pattern)
        "SOUL.md",
        ".soul/*.md",
        "IDENTITY.md",
        "PERSONALITY.md",

        # Session transcripts and logging
        ".transcripts/*.jsonl",
        "transcripts/*.jsonl",
        ".sessions/*.jsonl",
        "sessions/*.jsonl",

        # Hooks and automation
        ".claude/hooks/*.sh",
        ".claude/hooks/*.py",
        ".claude/settings.json",
        ".claude/settings.local.json",
        ".husky/*",

        # AI context templates
        "templates/*.md",
        "*/templates/*.md",
        "*/templates/*/*.md",
    ],
    directory_patterns=[
        "skills",
        ".claude/commands",
        ".claude/hooks",
        ".claude/skills",
        ".github/skills",
        ".copilot/skills",
        ".cursor/skills",
        ".codex/skills",
        ".memory",
        ".context",
        ".ai",
        ".prompts",
        "personas",
        ".codex",
        ".soul",
        ".transcripts",
        "transcripts",
        ".sessions",
        "sessions",
    ],
    weight=2.0
)

# Level 5: Multi-Agent Ready (Yegge Stage 5)
LEVEL_5_PATTERNS = LevelConfig(
    name="Level 5: Multi-Agent Ready",
    description="Multiple specialized agents, MCP configs, and basic orchestration",
    file_patterns=[
        # Agent configuration
        ".github/agents/*.agent.md",
        ".github/agents/*.md",
        ".claude/agents/*.md",
        "agents/*.md",
        # Agent reference files
        ".github/agents/references.md",
        ".claude/agents/references.md",
        "agents/references.md",

        # MCP configuration (Boris Cherny pattern: .mcp.json shared via git)
        "mcp.json",
        ".mcp.json",
        ".mcp/*.json",
        "mcp-config.json",
        "mcp-server/*.md",

        # Multi-agent configuration (specific agent files)
        ".github/agents/reviewer.agent.md",
        ".github/agents/pr-reviewer.agent.md",
        ".github/agents/code-reviewer.agent.md",
        ".github/agents/tester.agent.md",
        ".github/agents/documenter.agent.md",
        ".github/agents/security.agent.md",
        ".github/agents/architect.agent.md",
        ".github/agents/refactorer.agent.md",
        ".github/agents/debugger.agent.md",
        ".github/agents/planner.agent.md",

        # Agent handoffs and orchestration basics
        "agents/HANDOFFS.md",
        "agents/ORCHESTRATION.md",
        "agents/REFERENCES.md",
        "roles/*.md",

        # Tool configs
        ".mcp/servers/*.json",
        "tools/TOOLS.md",
        "tools/*.json",
    ],
    directory_patterns=[
        ".claude/agents",
        ".github/agents",
        "agents",
        "roles",
        ".mcp",
        ".mcp/servers",
        "tools",
    ],
    weight=2.5
)

# Level 6: Fleet Infrastructure (Yegge Stage 6)
LEVEL_6_PATTERNS = LevelConfig(
    name="Level 6: Fleet Infrastructure",
    description="Advanced memory systems, shared context, and workflow pipelines",
    file_patterns=[
        # Beads memory system
        ".beads/*.md",
        ".beads/*.json",
        ".beads/*.yaml",
        "beads/*.md",
        "beads/*.json",

        # Agent state persistence
        ".agent_state/*.json",
        ".agent_state/*.yaml",
        ".agent_state/README.md",
        "agent_state/*.json",

        # Shared context (monorepo)
        "SHARED_CONTEXT.md",
        "packages/*/CLAUDE.md",
        "packages/*/AGENTS.md",
        "services/*/CLAUDE.md",
        "services/*/AGENTS.md",
        "apps/*/CLAUDE.md",
        "apps/*/AGENTS.md",

        # Advanced workflow pipelines
        "workflows/*.yaml",
        "workflows/*.yml",
        "workflows/README.md",
        "pipelines/*.yaml",
        "pipelines/*.yml",
        "pipelines/README.md",

        # Memory systems (global)
        "memory/global/*.md",
        "memory/global/*.json",
        "memory/shared/*.md",
        "memory/project/*.md",
        ".memory/global/*.md",

        # Fleet configuration
        "FLEET.md",
        "agents/FLEET.md",
        ".fleet/*.yaml",
        ".fleet/*.json",
        ".fleet/README.md",

        # Gas Town patterns - service discovery and routing
        "routes.jsonl",
        ".routes/*.jsonl",
        "discovery/*.md",
        "discovery/*.yaml",

        # Formula templates (Gas Town molecules)
        "formulas/*.toml",
        "formulas/*.yaml",
        "formulas/README.md",
        ".formulas/*.toml",
    ],
    directory_patterns=[
        ".beads",
        "beads",
        ".agent_state",
        "agent_state",
        "workflows",
        "pipelines",
        "formulas",
        ".formulas",
        "discovery",
        "memory/global",
        "memory/shared",
        "memory/project",
        ".fleet",
    ],
    weight=3.0
)

# Level 7: Agent Fleet (Yegge Stage 7)
LEVEL_7_PATTERNS = LevelConfig(
    name="Level 7: Agent Fleet",
    description="Large agent fleet with governance, scheduling, and multi-agent pipelines",
    file_patterns=[
        # Governance
        "GOVERNANCE.md",
        "agents/GOVERNANCE.md",
        "AGENT_PERMISSIONS.md",
        "agents/PERMISSIONS.md",
        "AGENT_POLICIES.md",
        "agents/POLICIES.md",

        # Fleet-scale agent definitions
        "agents/specialists/*.md",
        "agents/roles/*.md",
        ".github/agents/specialists/*.md",
        ".claude/agents/specialists/*.md",

        # Agent scheduling
        "agents/SCHEDULING.md",
        "agents/PRIORITY.md",
        "AGENT_QUEUE.md",
        ".queue/*.yaml",
        ".queue/*.json",
        "queue/*.yaml",

        # Multi-agent pipeline definitions
        "workflows/code_review.yaml",
        "workflows/feature_development.yaml",
        "workflows/incident_response.yaml",
        "workflows/release_pipeline.yaml",
        "workflows/security_audit.yaml",
        "workflows/deployment.yaml",
        "pipelines/multi_agent/*.yaml",
        "pipelines/multi_agent/*.yml",

        # Convoy/molecule patterns (Gas Town style)
        "convoys/*.yaml",
        "convoys/*.md",
        "convoys/README.md",
        "molecules/*.yaml",
        "molecules/*.md",
        "molecules/README.md",
        "epics/*.yaml",
        "epics/*.md",
        "epics/README.md",

        # Gas Town advanced patterns
        "swarm/*.yaml",
        "swarm/*.md",
        "swarm/README.md",
        "wisps/*.yaml",
        "wisps/*.md",
        "polecats/*.yaml",
        "polecats/*.md",
        ".rigs/*.yaml",
        ".rigs/*.md",
        "rigs/*.yaml",

        # Agent metrics
        "agents/METRICS.md",
        "AGENT_PERFORMANCE.md",
        ".metrics/agents/*.json",
        ".metrics/agents/*.yaml",
        "metrics/agents/*.md",
    ],
    directory_patterns=[
        "agents/specialists",
        "agents/roles",
        ".queue",
        "queue",
        "convoys",
        "molecules",
        "epics",
        "swarm",
        "wisps",
        "polecats",
        ".rigs",
        "rigs",
        ".metrics/agents",
        "metrics/agents",
        "pipelines/multi_agent",
    ],
    weight=4.0
)

# Level 8: Custom Orchestration (Yegge Stage 8)
LEVEL_8_PATTERNS = LevelConfig(
    name="Level 8: Custom Orchestration",
    description="Custom orchestration, meta-automation, and frontier tooling",
    file_patterns=[
        # Custom orchestration
        "orchestration.yaml",
        "orchestration/*.yaml",
        "orchestration/*.py",
        "orchestration/README.md",
        "ORCHESTRATOR.md",
        "orchestration/ARCHITECTURE.md",

        # Gas Town / custom orchestrators
        ".gastown/*.yaml",
        ".gastown/*.json",
        ".gastown/README.md",
        "gastown.config.yaml",
        "gastown.config.json",

        # Meta-automation (automation generating automation)
        "meta/*.yaml",
        "meta/*.py",
        "meta/README.md",
        "generators/*.py",
        "generators/*.yaml",
        "generators/README.md",
        "AUTO_GENERATE.md",

        # Agent composition
        "agents/COMPOSITION.md",
        "agents/DECOMPOSITION.md",
        "agents/TEMPLATES.md",
        "agent_templates/*.yaml",
        "agent_templates/*.md",
        "agent_templates/README.md",

        # Frontier tooling
        ".frontier/*.yaml",
        ".frontier/*.json",
        ".frontier/README.md",
        "experimental/*.md",
        "EXPERIMENTAL.md",

        # Custom tool definitions
        "tools/custom/*.py",
        "tools/custom/*.yaml",
        "tools/custom/README.md",
        "tools/REGISTRY.md",
        ".tools/*.yaml",
        ".tools/*.json",

        # Agent SDK / framework
        "agent_sdk/*.py",
        "agent_sdk/README.md",
        "agent_framework/*.py",
        "agent_framework/README.md",
        "AGENT_SDK.md",
        "FRAMEWORK.md",

        # Custom protocols
        "protocols/*.md",
        "protocols/*.yaml",
        "PROTOCOL.md",

        # Agent communication (ClawdBot/Gas Town patterns)
        "mail-protocol.md",
        "MAIL_PROTOCOL.md",
        "federation.md",
        "FEDERATION.md",
        "escalation.md",
        "ESCALATION.md",
        "watchdog/*.yaml",
        "watchdog/*.md",

        # Infrastructure as code for agents
        "infra/agents/*.tf",
        "infra/agents/*.yaml",
        "k8s/agents/*.yaml",
    ],
    directory_patterns=[
        "orchestration",
        ".gastown",
        "meta",
        "generators",
        "agent_templates",
        ".frontier",
        "experimental",
        "tools/custom",
        ".tools",
        "agent_sdk",
        "agent_framework",
        "protocols",
        "watchdog",
        "infra/agents",
        "k8s/agents",
    ],
    weight=5.0
)

# All levels for iteration (1-8)
LEVELS: Dict[int, LevelConfig] = {
    1: LEVEL_1_PATTERNS,
    2: LEVEL_2_PATTERNS,
    3: LEVEL_3_PATTERNS,
    4: LEVEL_4_PATTERNS,
    5: LEVEL_5_PATTERNS,
    6: LEVEL_6_PATTERNS,
    7: LEVEL_7_PATTERNS,
    8: LEVEL_8_PATTERNS,
}

# Core files that indicate basic AI tool adoption (any of these suggest Level 2+)
# Only includes actual files from Level 2 patterns
CORE_AI_FILES: Set[str] = {
    "CLAUDE.md",
    "AGENTS.md",
    ".github/copilot-instructions.md",
    ".cursorrules",
    "CODEX.md",
}

# Tool-specific pattern mapping
# Maps patterns to the tools they belong to. Patterns not listed are considered generic (all tools).
# Used to filter patterns when user specifies tools in .ai-proficiency.yaml
# Note: AGENTS.md is intentionally NOT listed here - it's a generic agent instruction file
# that works with all AI tools (Claude, Copilot, Cursor, Codex, etc.)
TOOL_SPECIFIC_PATTERNS: Dict[str, List[str]] = {
    # Claude Code specific
    "claude-code": [
        "CLAUDE.md",
        ".claude/",
    ],
    # GitHub Copilot specific
    "github-copilot": [
        ".github/copilot-instructions.md",
        ".github/instructions/",
        ".github/agents/",
        ".github/skills/",
        ".copilot/",
    ],
    # Cursor specific
    "cursor": [
        ".cursorrules",
        ".cursor/",
    ],
    # OpenAI Codex specific
    "openai-codex": [
        "CODEX.md",
        ".codex/",
    ],
}


def get_tool_for_pattern(pattern: str) -> Optional[str]:
    """
    Determine which tool a pattern belongs to.
    Returns None if the pattern is generic (applies to all tools).
    """
    for tool, patterns in TOOL_SPECIFIC_PATTERNS.items():
        for tool_pattern in patterns:
            if tool_pattern.endswith("/"):
                # Directory prefix match
                if pattern.startswith(tool_pattern) or pattern.startswith(tool_pattern.rstrip("/")):
                    return tool
            else:
                # Exact match
                if pattern == tool_pattern:
                    return tool
    return None  # Generic pattern, applies to all tools


def filter_patterns_for_tools(patterns: List[str], tools: List[str]) -> List[str]:
    """
    Filter patterns to only include those relevant to the specified tools.
    Generic patterns (not tool-specific) are always included.
    """
    if not tools:
        return patterns  # No filtering if no tools specified

    filtered = []
    for pattern in patterns:
        tool = get_tool_for_pattern(pattern)
        if tool is None or tool in tools:
            filtered.append(pattern)
    return filtered

