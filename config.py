"""
Configuration for AI proficiency measurement.

Defines the file patterns to look for at each maturity level.
Focused on the big four: Claude Code, GitHub Copilot, Cursor, and OpenAI Codex.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set


@dataclass
class LevelConfig:
    """Configuration for a single maturity level."""
    name: str
    description: str
    file_patterns: List[str]
    directory_patterns: List[str] = field(default_factory=list)
    weight: float = 1.0


# Level 0: Autocomplete and chat - no specific files to check
# Level 1: Basic agent use with minimal context
LEVEL_1_PATTERNS = LevelConfig(
    name="Level 1: Basic Instructions",
    description="Basic context files exist with minimal project information",
    file_patterns=[
        # Claude Code
        "CLAUDE.md",
        "AGENTS.md",
        # GitHub Copilot
        ".github/copilot-instructions.md",
        # Cursor
        ".cursorrules",
        # General
        "README.md",
    ],
    weight=1.0
)

# Level 2: Trusted agent with comprehensive context
LEVEL_2_PATTERNS = LevelConfig(
    name="Level 2: Comprehensive Context",
    description="Detailed instruction files covering architecture, conventions, and patterns",
    file_patterns=[
        # Agent instruction files (detailed versions)
        # Copilot scoped instructions
        ".github/instructions/*.instructions.md",
        # Cursor rules directory
        ".cursor/rules/*.md",
        ".cursor/rules/*.mdc",
        
        # Architecture and specification files
        "ARCHITECTURE.md",
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
        "docs/api/*.md",
        "DATA_MODEL.md",
        "docs/data/*.md",
        "SECURITY.md",
        "GLOSSARY.md",
        "DOMAIN.md",
        
        # Conventions and standards
        "CONVENTIONS.md",
        "STYLE.md",
        "CONTRIBUTING.md",
        "PATTERNS.md",
        "ANTI_PATTERNS.md",
        "CODE_REVIEW.md",
        "NAMING.md",
        
        # Development context
        "DEVELOPMENT.md",
        "SETUP.md",
        "TESTING.md",
        "DEBUGGING.md",
        "PERFORMANCE.md",
        "DEPLOYMENT.md",
        "INFRASTRUCTURE.md",
        "DEPENDENCIES.md",
        "MIGRATION.md",
        "docs/runbooks/*.md",
        "docs/guides/*.md",
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

# Level 3: Automated workflows and persistent memory
LEVEL_3_PATTERNS = LevelConfig(
    name="Level 3: Skills, Memory & Workflows",
    description="Skill files, memory systems, hooks, and workflow definitions",
    file_patterns=[
        # Skill files
        "SKILL.md",
        "skills/*.md",
        "skills/*/SKILL.md",
        "CAPABILITIES.md",
        
        # Workflow and automation
        "WORKFLOWS.md",
        "COMMANDS.md",
        ".claude/commands/*.md",
        "Makefile",
        "justfile",
        "scripts/*.sh",
        "scripts/*.py",
        
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
        
        # Agent configuration
        ".github/agents/*.agent.md",
        ".context/*.md",
        ".ai/*.md",
        "PROMPTS.md",
        ".prompts/*.md",
        "personas/*.md",
        
        # Hooks and automation
        ".claude/hooks/*.sh",
        ".claude/hooks/*.py",
        ".claude/settings.json",
        ".claude/settings.local.json",
        ".husky/*",
        
        # MCP configuration
        "mcp.json",
        ".mcp/*.json",
        "mcp-config.json",
    ],
    directory_patterns=[
        "skills",
        ".claude/commands",
        ".claude/hooks",
        ".memory",
        ".context",
        ".ai",
        ".prompts",
        "personas",
        ".mcp",
        ".github/agents",
    ],
    weight=2.0
)

# Level 4: Orchestrated multi-agent systems
LEVEL_4_PATTERNS = LevelConfig(
    name="Level 4: Multi-Agent Orchestration",
    description="Multiple specialized agents, shared context, and orchestration infrastructure",
    file_patterns=[
        # Multi-agent configuration (multiple agent files)
        ".github/agents/reviewer.agent.md",
        ".github/agents/tester.agent.md",
        ".github/agents/documenter.agent.md",
        ".github/agents/security.agent.md",
        ".github/agents/architect.agent.md",
        ".github/agents/refactorer.agent.md",
        ".github/agents/debugger.agent.md",
        ".github/agents/planner.agent.md",
        "agents/HANDOFFS.md",
        "agents/ORCHESTRATION.md",
        "roles/*.md",
        
        # Tool and integration configs
        ".mcp/servers/*.json",
        "tools/TOOLS.md",
        "tools/*.json",
        
        # Shared context
        "SHARED_CONTEXT.md",
        "packages/*/CLAUDE.md",
        "packages/*/AGENTS.md",
        
        # Memory systems
        ".beads/*.md",
        ".beads/*.json",
        "memory/global/*.md",
        "memory/project/*.md",
        ".agent_state/*.json",
        
        # Orchestration
        "orchestration.yaml",
        "orchestration/*.yaml",
        "workflows/code_review.yaml",
        "workflows/feature_development.yaml",
        "workflows/incident_response.yaml",
        "GOVERNANCE.md",
    ],
    directory_patterns=[
        "agents",
        "roles",
        ".beads",
        "memory/global",
        "memory/project",
        ".agent_state",
        "orchestration",
        "workflows",
        ".mcp/servers",
        "tools",
    ],
    weight=3.0
)

# All levels for iteration
LEVELS: Dict[int, LevelConfig] = {
    1: LEVEL_1_PATTERNS,
    2: LEVEL_2_PATTERNS,
    3: LEVEL_3_PATTERNS,
    4: LEVEL_4_PATTERNS,
}

# Core files that indicate basic AI tool adoption (any of these suggest Level 1+)
CORE_AI_FILES: Set[str] = {
    "CLAUDE.md",
    "AGENTS.md",
    ".github/copilot-instructions.md",
    ".cursorrules",
    ".cursor/rules",
    ".github/agents",
}

# Quality indicators - files that suggest the context is actively maintained
QUALITY_INDICATORS: List[str] = [
    "CHANGELOG.md",
    ".github/workflows/*.yml",
    ".github/workflows/*.yaml",
]
