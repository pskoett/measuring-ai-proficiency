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
"""

__version__ = "0.1.0"
__author__ = "Peter Skoett"

from .scanner import RepoScanner, RepoScore, scan_multiple_repos, scan_github_org
from .reporter import (
    TerminalReporter,
    JsonReporter,
    MarkdownReporter,
    CsvReporter,
    get_reporter,
)
from .config import LEVELS, LevelConfig

__all__ = [
    "RepoScanner",
    "RepoScore",
    "scan_multiple_repos",
    "scan_github_org",
    "TerminalReporter",
    "JsonReporter",
    "MarkdownReporter",
    "CsvReporter",
    "get_reporter",
    "LEVELS",
    "LevelConfig",
]
