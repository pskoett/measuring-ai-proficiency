"""
Repository-specific configuration for AI proficiency measurement.

Supports:
1. Auto-detection of AI tools in use
2. Custom config via .ai-proficiency.yaml
"""

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

# Try to import yaml, but make it optional
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


@dataclass
class RepoConfig:
    """Repository-specific configuration for proficiency scanning."""

    # AI tools in use (auto-detected or configured)
    tools: List[str] = field(default_factory=list)

    # Custom file locations (override defaults)
    custom_patterns: Dict[str, str] = field(default_factory=dict)

    # Custom thresholds for level advancement
    thresholds: Dict[int, int] = field(default_factory=dict)

    # Recommendations to skip
    skip_recommendations: List[str] = field(default_factory=list)

    # Focus areas (only show recommendations for these)
    focus_areas: List[str] = field(default_factory=list)

    # Patterns to skip during validation (documentation examples, etc.)
    skip_validation_patterns: List[str] = field(default_factory=list)

    # Quality scoring thresholds (configurable)
    max_file_size: int = 100_000  # Max file size for cross-ref scanning (bytes)
    min_substantive_bytes: int = 100  # Minimum bytes for a file to be "substantive"
    word_threshold_partial: int = 50  # Words for partial quality points
    word_threshold_full: int = 200  # Words for full quality points
    git_timeout: int = 5  # Git command timeout in seconds

    # Whether config was loaded from file
    from_file: bool = False

    @property
    def has_claude(self) -> bool:
        return "claude-code" in self.tools

    @property
    def has_copilot(self) -> bool:
        return "github-copilot" in self.tools

    @property
    def has_cursor(self) -> bool:
        return "cursor" in self.tools

    @property
    def has_codex(self) -> bool:
        return "openai-codex" in self.tools

    @property
    def primary_tool(self) -> Optional[str]:
        """Return the primary AI tool (first in list)."""
        return self.tools[0] if self.tools else None


# Tool detection patterns
TOOL_DETECTION = {
    "claude-code": {
        "files": ["CLAUDE.md", ".claude/settings.json", ".claude/settings.local.json"],
        "dirs": [".claude", ".claude/skills", ".claude/commands", ".claude/hooks"],
    },
    "github-copilot": {
        "files": [".github/copilot-instructions.md", ".github/AGENTS.md"],
        "dirs": [".github/skills", ".github/agents", ".copilot"],
    },
    "cursor": {
        "files": [".cursorrules"],
        "dirs": [".cursor", ".cursor/rules"],
    },
    "openai-codex": {
        "files": ["AGENTS.md"],  # Note: AGENTS.md is shared with Claude
        "dirs": [".codex", ".codex/skills"],
    },
}

# Tool-specific recommendations
TOOL_RECOMMENDATIONS = {
    "claude-code": {
        "basic_file": "CLAUDE.md",
        "skills_dir": ".claude/skills/",
        "commands_dir": ".claude/commands/",
        "hooks_dir": ".claude/hooks/",
        "agents_dir": ".claude/agents/",
        "settings": ".claude/settings.json",
    },
    "github-copilot": {
        "basic_file": ".github/copilot-instructions.md",
        "skills_dir": ".github/skills/",
        "agents_dir": ".github/agents/",
        "instructions_dir": ".github/instructions/",
    },
    "cursor": {
        "basic_file": ".cursorrules",
        "rules_dir": ".cursor/rules/",
    },
    "openai-codex": {
        "basic_file": "AGENTS.md",
        "skills_dir": ".codex/skills/",
        "config_dir": ".codex/",
    },
}


def detect_ai_tools(repo_path: Path) -> List[str]:
    """Auto-detect which AI tools are in use based on existing files."""

    detected: List[str] = []

    for tool, patterns in TOOL_DETECTION.items():
        tool_found = False

        # Check files
        for file_pattern in patterns.get("files", []):
            if (repo_path / file_pattern).exists():
                tool_found = True
                break

        # Check directories if no file found
        if not tool_found:
            for dir_pattern in patterns.get("dirs", []):
                if (repo_path / dir_pattern).is_dir():
                    tool_found = True
                    break

        if tool_found:
            detected.append(tool)

    return detected


def load_repo_config(repo_path: Path) -> RepoConfig:
    """
    Load repository configuration.

    Priority:
    1. .ai-proficiency.yaml (if exists)
    2. Auto-detection (always runs as fallback/supplement)
    """

    config = RepoConfig()

    # Try to load from config file
    config_file = repo_path / ".ai-proficiency.yaml"
    if config_file.exists() and YAML_AVAILABLE:
        try:
            with open(config_file) as f:
                data = yaml.safe_load(f) or {}

            config.from_file = True

            # Load tools (can be list or single string)
            if "tools" in data:
                tools = data["tools"]
                if isinstance(tools, str):
                    config.tools = [tools]
                elif isinstance(tools, list):
                    config.tools = tools

            # Load custom patterns
            if "documentation" in data:
                config.custom_patterns = data["documentation"]

            # Load thresholds
            if "thresholds" in data:
                for level, threshold in data["thresholds"].items():
                    # Handle both "level_3" and "3" formats
                    level_num = int(str(level).replace("level_", ""))
                    config.thresholds[level_num] = int(threshold)

            # Load skip recommendations
            if "skip_recommendations" in data:
                config.skip_recommendations = data["skip_recommendations"]

            # Load focus areas
            if "focus_areas" in data:
                config.focus_areas = data["focus_areas"]

            # Load validation patterns to skip (documentation examples)
            if "skip_validation_patterns" in data:
                config.skip_validation_patterns = data["skip_validation_patterns"]

            # Load quality scoring options
            if "quality" in data:
                quality = data["quality"]
                if "max_file_size" in quality:
                    config.max_file_size = int(quality["max_file_size"])
                if "min_substantive_bytes" in quality:
                    config.min_substantive_bytes = int(quality["min_substantive_bytes"])
                if "word_threshold_partial" in quality:
                    config.word_threshold_partial = int(quality["word_threshold_partial"])
                if "word_threshold_full" in quality:
                    config.word_threshold_full = int(quality["word_threshold_full"])
                if "git_timeout" in quality:
                    config.git_timeout = int(quality["git_timeout"])

        except yaml.YAMLError as e:
            print(f"Warning: Failed to parse {config_file}: {e}", file=sys.stderr)
        except Exception as e:
            print(f"Warning: Failed to load config {config_file}: {e}", file=sys.stderr)

    # Auto-detect tools (supplement configured tools)
    detected_tools = detect_ai_tools(repo_path)

    # Merge detected tools with configured (configured takes priority)
    if config.tools:
        # Add any detected tools not already in config
        for tool in detected_tools:
            if tool not in config.tools:
                config.tools.append(tool)
    else:
        config.tools = detected_tools

    return config


def get_tool_specific_recommendation(
    tool: str,
    rec_type: str,
    fallback: str = ""
) -> str:
    """Get a tool-specific path/recommendation."""

    tool_recs = TOOL_RECOMMENDATIONS.get(tool, {})
    return tool_recs.get(rec_type, fallback)


# Proper display names for AI tools (handles special capitalization like "GitHub")
TOOL_DISPLAY_NAMES = {
    "claude-code": "Claude Code",
    "github-copilot": "GitHub Copilot",
    "cursor": "Cursor",
    "openai-codex": "OpenAI Codex",
}


def format_multi_tool_options(tools: List[str], rec_type: str) -> str:
    """Format recommendations showing options for multiple tools."""

    options = []
    for tool in tools:
        path = get_tool_specific_recommendation(tool, rec_type)
        if path:
            tool_name = TOOL_DISPLAY_NAMES.get(tool, tool.replace("-", " ").title())
            options.append(f"{path} ({tool_name})")

    if not options:
        return ""

    if len(options) == 1:
        return options[0].split(" (")[0]  # Just the path

    return " or ".join(options[:2])  # Show up to 2 options
