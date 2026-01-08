"""
Measure AI Proficiency

A tool for measuring AI coding proficiency based on context engineering artifacts.
Scans repositories for files like CLAUDE.md, copilot-instructions.md, .cursorrules,
and other context engineering patterns to assess maturity levels.

Focused on the big four AI coding tools:
- Claude Code
- GitHub Copilot
- Cursor
- OpenAI Codex CLI

Supports:
- Auto-detection of AI tools in use
- Custom configuration via .ai-proficiency.yaml
- Tool-specific recommendations
"""

__version__ = "0.3.0"
__author__ = "Peter Skoett"

from .scanner import (
    RepoScanner,
    RepoScore,
    scan_multiple_repos,
    scan_github_org,
    CrossReference,
    ContentQuality,
    CrossReferenceResult,
)
from .reporter import (
    TerminalReporter,
    JsonReporter,
    MarkdownReporter,
    CsvReporter,
    get_reporter,
)
from .config import LEVELS, LevelConfig
from .repo_config import (
    RepoConfig,
    load_repo_config,
    detect_ai_tools,
    TOOL_DETECTION,
    TOOL_RECOMMENDATIONS,
)

__all__ = [
    "RepoScanner",
    "RepoScore",
    "scan_multiple_repos",
    "scan_github_org",
    "CrossReference",
    "ContentQuality",
    "CrossReferenceResult",
    "TerminalReporter",
    "JsonReporter",
    "MarkdownReporter",
    "CsvReporter",
    "get_reporter",
    "LEVELS",
    "LevelConfig",
    "RepoConfig",
    "load_repo_config",
    "detect_ai_tools",
    "TOOL_DETECTION",
    "TOOL_RECOMMENDATIONS",
]
