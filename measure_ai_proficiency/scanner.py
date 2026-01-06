"""
Repository scanner for AI proficiency measurement.

Scans repositories for context engineering artifacts and calculates maturity scores.
Uses levels 1-8 aligned with Steve Yegge's 8-stage AI coding proficiency model.
"""

import fnmatch
import os
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

from .config import LEVELS, CORE_AI_FILES, LevelConfig
from .repo_config import (
    RepoConfig,
    load_repo_config,
    detect_ai_tools,
    get_tool_specific_recommendation,
    format_multi_tool_options,
    TOOL_RECOMMENDATIONS,
)

# =============================================================================
# Cross-Reference Detection Constants
# =============================================================================

# AI instruction files to scan for cross-references
INSTRUCTION_FILES: Set[str] = {
    "CLAUDE.md",
    "AGENTS.md",
    ".cursorrules",
    "CODEX.md",
    ".github/copilot-instructions.md",
    ".copilot-instructions.md",
    ".github/AGENTS.md",
}

# Known AI-related files that are valid reference targets
KNOWN_TARGETS: Set[str] = {
    "CLAUDE.md", "AGENTS.md", ".cursorrules", "CODEX.md",
    "ARCHITECTURE.md", "CONVENTIONS.md", "SKILL.md", "TESTING.md",
    "API.md", "SECURITY.md", "CONTRIBUTING.md", "PATTERNS.md",
    "DEVELOPMENT.md", "DEPLOYMENT.md", "MEMORY.md", "LEARNINGS.md",
    "HANDOFFS.md", "GOVERNANCE.md", "SHARED_CONTEXT.md",
}

# Max file size to read for cross-reference scanning (100KB)
MAX_CROSS_REF_FILE_SIZE: int = 100_000

# Regex patterns for detecting cross-references
CROSS_REF_PATTERNS: Dict[str, re.Pattern] = {
    # Markdown links: [text](file.md) or [text](./path/file.md)
    "markdown_link": re.compile(
        r'\[([^\]]+)\]\(([^)]+\.(?:md|yaml|yml|json|rules|mdc))\)',
        re.IGNORECASE
    ),
    # File mentions in quotes/backticks: "AGENTS.md", `CLAUDE.md`, 'CONVENTIONS.md'
    "file_mention": re.compile(
        r'[`"\']([A-Z][A-Za-z0-9_\-]+\.(?:md|yaml|yml|json))[`"\']'
    ),
    # Relative paths: ./docs/ARCHITECTURE.md, ../CLAUDE.md
    "relative_path": re.compile(
        r'(?:^|\s)(\.{1,2}/[\w\-./]+\.(?:md|yaml|yml|json))',
        re.MULTILINE
    ),
    # Directory references: skills/, .claude/commands/, docs/
    "directory_ref": re.compile(
        r'(?:^|\s)(\.?/?(?:skills|\.claude|\.github|\.copilot|docs|agents|workflows|\.mcp)(?:/[\w\-]+)*/?)',
        re.MULTILINE
    ),
}

# Patterns for evaluating content quality
QUALITY_PATTERNS: Dict[str, re.Pattern] = {
    # Markdown sections (headers)
    "sections": re.compile(r'^#{1,3}\s+.+', re.MULTILINE),
    # Concrete file paths
    "paths": re.compile(r'[`~]?(?:/[\w\-./]+|~/[\w\-./]+)[`]?'),
    # CLI commands in backticks
    "commands": re.compile(r'`[a-z][\w\-]*(?:\s+[^`]+)?`'),
    # Constraint language
    "constraints": re.compile(r'\b(?:never|avoid|don\'t|do not|must not|always|required)\b', re.IGNORECASE),
}


@dataclass
class CrossReference:
    """A detected cross-reference between files."""

    source_file: str      # File containing the reference
    target: str           # Referenced file/directory path
    reference_type: str   # "markdown_link", "file_mention", "relative_path", "directory_ref"
    line_number: int      # Line where reference was found
    is_resolved: bool     # Whether target exists in repo


@dataclass
class ContentQuality:
    """Quality metrics for an AI instruction file's content."""

    has_sections: bool         # Has markdown headers (##)
    has_specific_paths: bool   # Contains concrete file paths
    has_tool_commands: bool    # References CLI tools/commands
    has_constraints: bool      # Contains "never", "avoid", "don't", etc.
    has_cross_refs: bool       # References other docs
    word_count: int
    section_count: int
    commit_count: int          # Number of git commits touching this file
    quality_score: float       # 0-10 based on indicators


@dataclass
class CrossReferenceResult:
    """Summary of cross-references and quality found in a repository."""

    references: List["CrossReference"] = field(default_factory=list)
    source_files_scanned: int = 0
    resolved_count: int = 0
    quality_scores: Dict[str, "ContentQuality"] = field(default_factory=dict)
    bonus_points: float = 0.0

    @property
    def total_count(self) -> int:
        return len(self.references)

    @property
    def unique_targets(self) -> Set[str]:
        return set(r.target for r in self.references)

    @property
    def resolution_rate(self) -> float:
        if self.total_count == 0:
            return 0.0
        return self.resolved_count / self.total_count * 100


@dataclass
class FileMatch:
    """A matched file with metadata."""

    path: str
    pattern: str
    level: int
    size_bytes: int = 0
    last_modified: Optional[datetime] = None

    @property
    def is_substantive(self) -> bool:
        """Check if file has substantive content (not just a stub)."""

        return self.size_bytes > 100  # More than ~100 bytes suggests actual content


@dataclass
class LevelScore:
    """Score for a single maturity level."""

    level: int
    name: str
    description: str
    matched_files: List[FileMatch] = field(default_factory=list)
    matched_directories: List[str] = field(default_factory=list)
    total_patterns: int = 0
    coverage_percent: float = 0.0

    @property
    def file_count(self) -> int:
        return len(self.matched_files)

    @property
    def substantive_file_count(self) -> int:
        return sum(1 for f in self.matched_files if f.is_substantive)


@dataclass
class RepoScore:
    """Complete score for a repository."""

    repo_path: str
    repo_name: str
    scan_time: datetime
    level_scores: Dict[int, LevelScore] = field(default_factory=dict)
    overall_level: int = 1  # Default to Level 1 (baseline)
    overall_score: float = 0.0
    recommendations: List[str] = field(default_factory=list)
    detected_tools: List[str] = field(default_factory=list)
    config: Optional[RepoConfig] = None
    cross_references: Optional[CrossReferenceResult] = None

    @property
    def has_any_ai_files(self) -> bool:
        """Check if repo has any AI-specific files (Level 2+)."""

        # Check if any Level 2+ files exist
        for level_num, ls in self.level_scores.items():
            if level_num >= 2 and ls.file_count > 0:
                return True
        return False

    @property
    def primary_tool(self) -> Optional[str]:
        """Get the primary AI tool in use."""
        return self.detected_tools[0] if self.detected_tools else None


class RepoScanner:
    """Scans a repository for context engineering artifacts."""

    def __init__(self, repo_path: str, verbose: bool = False):
        self.repo_path = Path(repo_path).resolve()
        self.verbose = verbose
        self._dir_cache: Dict[str, bool] = {}
        self.config: Optional[RepoConfig] = None

    def scan(self) -> RepoScore:
        """Scan the repository and return a complete score."""

        scan_time = datetime.now()

        # Load repository config (auto-detection + .ai-proficiency.yaml)
        self.config = load_repo_config(self.repo_path)

        # Initialize score
        score = RepoScore(
            repo_path=str(self.repo_path),
            repo_name=self.repo_path.name,
            scan_time=scan_time,
            detected_tools=self.config.tools,
            config=self.config,
        )

        # Scan each level
        for level_num, level_config in LEVELS.items():
            level_score = self._scan_level(level_num, level_config)
            score.level_scores[level_num] = level_score

        # Scan for cross-references and evaluate content quality
        score.cross_references = self._scan_cross_references()

        # Calculate overall level and score (using custom thresholds if configured)
        score.overall_level = self._calculate_overall_level(score.level_scores)
        base_score = self._calculate_overall_score(score.level_scores)

        # Add cross-reference bonus to overall score (capped at 100)
        score.overall_score = min(100, base_score + score.cross_references.bonus_points)

        # Generate recommendations (tool-specific)
        score.recommendations = self._generate_recommendations(score)

        return score

    def _scan_level(self, level_num: int, config: LevelConfig) -> LevelScore:
        """Scan for files matching a specific level's patterns."""

        level_score = LevelScore(
            level=level_num,
            name=config.name,
            description=config.description,
        )

        # Count total unique patterns for coverage calculation
        all_patterns = set(config.file_patterns + config.directory_patterns)
        level_score.total_patterns = len(all_patterns)

        matched_patterns: Set[str] = set()

        # Check file patterns
        for pattern in config.file_patterns:
            matches = self._find_matches(pattern)
            for match_path in matches:
                file_match = self._create_file_match(match_path, pattern, level_num)
                level_score.matched_files.append(file_match)
                matched_patterns.add(pattern)

        # Check directory patterns
        for pattern in config.directory_patterns:
            if self._directory_exists(pattern):
                level_score.matched_directories.append(pattern)
                matched_patterns.add(pattern)

        # Calculate coverage
        if level_score.total_patterns > 0:
            level_score.coverage_percent = (
                len(matched_patterns) / level_score.total_patterns * 100
            )

        return level_score

    def _find_matches(self, pattern: str) -> List[str]:
        """Find all files matching a pattern."""

        matches: List[str] = []

        # Handle glob patterns
        if "*" in pattern:
            parts = pattern.split("/")
            base_dir = self.repo_path

            for i, part in enumerate(parts):
                if "*" in part:
                    remaining_pattern = "/".join(parts[i:])
                    matches.extend(self._glob_search(base_dir, remaining_pattern))
                    break

                base_dir = base_dir / part
                if not base_dir.exists():
                    break
        else:
            # Direct file path
            full_path = self.repo_path / pattern
            if full_path.exists() and full_path.is_file():
                matches.append(pattern)

        return matches

    def _glob_search(self, base_dir: Path, pattern: str) -> List[str]:
        """Recursively search for files matching a glob pattern."""

        matches: List[str] = []

        # Directories to exclude from scanning
        exclude_dirs = {
            'node_modules', 'venv', '.venv', 'env', '.env',
            'dist', 'build', '__pycache__', '.git', '.svn',
            'vendor', 'target', 'out', '.next', '.nuxt',
            'coverage', '.pytest_cache', '.tox', 'eggs',
            '.mypy_cache', '.ruff_cache', 'site-packages'
        }

        if not base_dir.exists():
            return matches

        try:
            for item in base_dir.rglob("*"):
                # Skip if any part of the path is in exclude_dirs
                if any(part in exclude_dirs for part in item.parts):
                    continue

                if item.is_file():
                    relative = item.relative_to(self.repo_path)
                    if fnmatch.fnmatch(str(relative), pattern):
                        matches.append(str(relative))
        except PermissionError:
            pass

        return matches

    def _directory_exists(self, pattern: str) -> bool:
        """Check if a directory pattern exists."""

        if pattern in self._dir_cache:
            return self._dir_cache[pattern]

        full_path = self.repo_path / pattern
        exists = full_path.exists() and full_path.is_dir()
        self._dir_cache[pattern] = exists
        return exists

    def _create_file_match(self, path: str, pattern: str, level: int) -> FileMatch:
        """Create a FileMatch object with metadata."""

        full_path = self.repo_path / path

        try:
            stat = full_path.stat()
            return FileMatch(
                path=path,
                pattern=pattern,
                level=level,
                size_bytes=stat.st_size,
                last_modified=datetime.fromtimestamp(stat.st_mtime),
            )
        except (OSError, PermissionError):
            return FileMatch(path=path, pattern=pattern, level=level)

    # =========================================================================
    # Cross-Reference Detection Methods
    # =========================================================================

    def _scan_cross_references(self) -> CrossReferenceResult:
        """Scan AI instruction files for cross-references and evaluate quality."""

        sources = self._find_instruction_files()
        references: List[CrossReference] = []
        quality_scores: Dict[str, ContentQuality] = {}

        for source in sources:
            content = self._read_file_safe(source)
            if content:
                # Extract cross-references
                refs = self._extract_references(source, content)
                references.extend(refs)

                # Get commit count for this file
                commit_count = self._get_file_commit_count(source)

                # Evaluate content quality
                quality = self._evaluate_quality(content, commit_count)
                # Update has_cross_refs based on actual references found
                quality = ContentQuality(
                    has_sections=quality.has_sections,
                    has_specific_paths=quality.has_specific_paths,
                    has_tool_commands=quality.has_tool_commands,
                    has_constraints=quality.has_constraints,
                    has_cross_refs=len(refs) > 0,
                    word_count=quality.word_count,
                    section_count=quality.section_count,
                    commit_count=commit_count,
                    quality_score=quality.quality_score,
                )
                rel_path = str(source.relative_to(self.repo_path))
                quality_scores[rel_path] = quality

        resolved_count = sum(1 for r in references if r.is_resolved)
        bonus_points = self._calculate_cross_ref_bonus(references, quality_scores)

        return CrossReferenceResult(
            references=references,
            source_files_scanned=len(sources),
            resolved_count=resolved_count,
            quality_scores=quality_scores,
            bonus_points=bonus_points,
        )

    def _find_instruction_files(self) -> List[Path]:
        """Find AI instruction files to scan for cross-references."""

        files: List[Path] = []

        # Check known instruction files
        for name in INSTRUCTION_FILES:
            path = self.repo_path / name
            if path.exists() and path.is_file():
                try:
                    if path.stat().st_size <= MAX_CROSS_REF_FILE_SIZE:
                        files.append(path)
                except (OSError, PermissionError):
                    pass

        # Also check for scoped instruction files
        scoped_patterns = [
            ".github/instructions/*.instructions.md",
            ".cursor/rules/*.md",
            ".claude/skills/*/SKILL.md",
            ".github/skills/*/SKILL.md",
            ".cursor/skills/*/SKILL.md",
            ".copilot/skills/*/SKILL.md",
            ".codex/skills/*/SKILL.md",
        ]
        for pattern in scoped_patterns:
            try:
                for match in self.repo_path.glob(pattern):
                    if match.stat().st_size <= MAX_CROSS_REF_FILE_SIZE:
                        files.append(match)
            except (OSError, PermissionError):
                pass

        return files

    def _read_file_safe(self, path: Path) -> Optional[str]:
        """Safely read file content with size limit and error handling."""

        try:
            if path.stat().st_size > MAX_CROSS_REF_FILE_SIZE:
                return None
            return path.read_text(encoding='utf-8', errors='ignore')
        except (OSError, PermissionError, UnicodeDecodeError):
            return None

    def _get_file_commit_count(self, file_path: Path) -> int:
        """Get number of git commits that touched this file.

        Uses git log with --follow to track renames.
        Returns 0 if not a git repo or git command fails.
        """
        try:
            # Get relative path from repo root
            rel_path = file_path.relative_to(self.repo_path)
            result = subprocess.run(
                ["git", "log", "--oneline", "--follow", "--", str(rel_path)],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=5,  # Prevent hanging on large repos
            )
            if result.returncode == 0 and result.stdout.strip():
                return len(result.stdout.strip().split('\n'))
            return 0
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError, ValueError):
            return 0

    def _extract_references(self, source: Path, content: str) -> List[CrossReference]:
        """Extract cross-references from a single file's content."""

        references: List[CrossReference] = []
        rel_source = str(source.relative_to(self.repo_path))
        seen: Set[tuple] = set()  # Dedupe (target, line_number)

        for line_num, line in enumerate(content.split('\n'), start=1):
            for ref_type, pattern in CROSS_REF_PATTERNS.items():
                for match in pattern.finditer(line):
                    target = self._extract_target(match, ref_type)

                    if not target:
                        continue

                    # Skip external URLs and anchors
                    if target.startswith(('http://', 'https://', 'mailto:', '#')):
                        continue

                    # Normalize target path
                    normalized = target.lstrip('./')

                    # Dedupe
                    key = (normalized, line_num)
                    if key in seen:
                        continue
                    seen.add(key)

                    # Check if target exists
                    is_resolved = self._resolve_target(normalized)

                    references.append(CrossReference(
                        source_file=rel_source,
                        target=normalized,
                        reference_type=ref_type,
                        line_number=line_num,
                        is_resolved=is_resolved,
                    ))

        return references

    def _extract_target(self, match: re.Match, ref_type: str) -> Optional[str]:
        """Extract the target path from a regex match."""

        if ref_type == "markdown_link":
            # Group 2 is the path in [text](path)
            return match.group(2)
        elif ref_type in ("file_mention", "relative_path", "directory_ref"):
            return match.group(1)
        return match.group(0).strip()

    def _resolve_target(self, target: str) -> bool:
        """Check if a target path exists in the repository."""

        # Try direct path
        full_path = self.repo_path / target
        if full_path.exists():
            return True

        # Try common documentation locations
        for prefix in ['docs/', '.github/', '.claude/']:
            if (self.repo_path / prefix / target).exists():
                return True

        return False

    def _evaluate_quality(self, content: str, commit_count: int = 0) -> ContentQuality:
        """Evaluate the quality of an AI instruction file's content."""

        sections = QUALITY_PATTERNS["sections"].findall(content)
        paths = QUALITY_PATTERNS["paths"].findall(content)
        commands = QUALITY_PATTERNS["commands"].findall(content)
        constraints = QUALITY_PATTERNS["constraints"].findall(content)
        words = content.split()

        # Calculate quality score (0-12, normalized to 0-10)
        # Content indicators (up to 10 pts)
        score = 0.0
        score += min(len(sections) / 5, 2.0)       # Up to 2 pts for sections
        score += min(len(paths) / 3, 2.0)          # Up to 2 pts for paths
        score += min(len(commands) / 3, 2.0)       # Up to 2 pts for commands
        score += min(len(constraints) / 2, 2.0)    # Up to 2 pts for constraints
        score += 2.0 if len(words) > 200 else (1.0 if len(words) > 50 else 0.0)  # Substance

        # Commit history bonus (up to 2 pts) - indicates active maintenance
        # 1 commit = 0 pts (just created), 3+ commits = 1 pt, 5+ commits = 2 pts
        if commit_count >= 5:
            score += 2.0
        elif commit_count >= 3:
            score += 1.0

        return ContentQuality(
            has_sections=len(sections) > 0,
            has_specific_paths=len(paths) > 0,
            has_tool_commands=len(commands) > 0,
            has_constraints=len(constraints) > 0,
            has_cross_refs=False,  # Updated later with actual refs
            word_count=len(words),
            section_count=len(sections),
            commit_count=commit_count,
            quality_score=min(score, 10.0),  # Cap at 10
        )

    def _calculate_cross_ref_bonus(
        self,
        refs: List[CrossReference],
        quality: Dict[str, ContentQuality]
    ) -> float:
        """Calculate bonus points based on cross-references and quality."""

        bonus = 0.0

        # Cross-reference bonus (up to 5 pts)
        if refs:
            unique_targets = set(r.target for r in refs)
            resolved_count = sum(1 for r in refs if r.is_resolved)
            resolved_rate = resolved_count / len(refs) if refs else 0

            # Up to 3 pts for unique cross-references (max at 6 unique)
            bonus += min(len(unique_targets) / 2, 3.0)
            # Up to 2 pts for resolution rate
            bonus += resolved_rate * 2.0

        # Quality bonus (up to 5 pts)
        if quality:
            avg_quality = sum(q.quality_score for q in quality.values()) / len(quality)
            # Half of average quality score as bonus
            bonus += avg_quality / 2

        return min(bonus, 10.0)

    def _calculate_overall_level(self, level_scores: Dict[int, LevelScore]) -> int:
        """
        Calculate the overall maturity level (1-8).

        Levels aligned with Steve Yegge's 8-stage model:
        - Level 1: Baseline - no AI-specific files (just README)
        - Level 2: Core AI file exists (CLAUDE.md, .cursorrules, etc.)
        - Level 3: Level 2 + significant Level 3 coverage (>15%)
        - Level 4: Level 3 + significant Level 4 coverage (>12%)
        - Level 5: Level 4 + significant Level 5 coverage (>10%)
        - Level 6: Level 5 + significant Level 6 coverage (>8%)
        - Level 7: Level 6 + significant Level 7 coverage (>6%)
        - Level 8: Level 7 + significant Level 8 coverage (>5%)

        Custom thresholds can be configured via .ai-proficiency.yaml
        """

        # Check for core AI files (Level 2 requirement)
        level_2 = level_scores.get(2)
        if not level_2 or level_2.substantive_file_count == 0:
            return 1  # No AI files = Level 1

        has_core_file = any(
            any(core in f.path for core in CORE_AI_FILES) for f in level_2.matched_files
        )
        if not has_core_file:
            return 1  # No core AI file = Level 1

        current_level = 2

        # Default thresholds (can be overridden by config)
        default_thresholds = {
            3: 15,   # Comprehensive context
            4: 12,   # Skills & automation
            5: 10,   # Multi-agent ready
            6: 8,    # Fleet infrastructure
            7: 6,    # Agent fleet
            8: 5,    # Custom orchestration (frontier)
        }

        # Use custom thresholds from config if available
        thresholds = default_thresholds.copy()
        if self.config and self.config.thresholds:
            for level_num, custom_threshold in self.config.thresholds.items():
                thresholds[level_num] = custom_threshold

        for level_num in range(3, 9):
            level_score = level_scores.get(level_num)
            threshold = thresholds.get(level_num, 5)

            if level_score and level_score.coverage_percent >= threshold:
                current_level = level_num
            else:
                break

        return current_level

    def _calculate_overall_score(self, level_scores: Dict[int, LevelScore]) -> float:
        """Calculate a weighted overall score (0-100)."""

        total_score = 0.0
        max_possible = 0.0

        for level_num, level_score in level_scores.items():
            config = LEVELS[level_num]
            weight = config.weight

            if level_score.total_patterns > 0:
                coverage_score = level_score.coverage_percent / 100
                substantive_ratio = (
                    level_score.substantive_file_count / max(level_score.file_count, 1)
                    if level_score.file_count > 0
                    else 0
                )

                level_contribution = coverage_score * substantive_ratio * weight * 12.5
                total_score += level_contribution

            max_possible += weight * 12.5

        if max_possible > 0:
            return min(100, (total_score / max_possible) * 100)
        return 0.0

    def _generate_recommendations(self, score: RepoScore) -> List[str]:
        """Generate actionable recommendations based on the score and detected tools."""

        recommendations: List[str] = []
        level_3 = score.level_scores.get(3)
        level_4 = score.level_scores.get(4)
        level_5 = score.level_scores.get(5)
        level_6 = score.level_scores.get(6)
        level_7 = score.level_scores.get(7)

        # Get detected tools for tool-specific recommendations
        tools = score.detected_tools if score.detected_tools else ["claude-code"]
        primary_tool = tools[0] if tools else "claude-code"
        config = score.config

        # Helper to check if recommendation should be skipped
        def should_skip(rec_type: str) -> bool:
            if config and config.skip_recommendations:
                return rec_type in config.skip_recommendations
            return False

        # Helper to check if recommendation is in focus area
        def in_focus(rec_type: str) -> bool:
            if config and config.focus_areas:
                return rec_type in config.focus_areas
            return True  # If no focus areas, include all

        # Helper to get tool-specific path
        def tool_path(rec_type: str) -> str:
            return format_multi_tool_options(tools, rec_type)

        if score.overall_level == 1:
            # Level 1: Zero AI - need to start with basic AI files
            basic_file = tool_path("basic_file") or "CLAUDE.md"

            # Show detected tools if any
            if tools:
                tool_names = ", ".join(t.replace("-", " ").title() for t in tools)
                recommendations.append(
                    f"🔍 Detected AI tools: {tool_names}. Recommendations tailored accordingly."
                )

            recommendations.append(
                f"🚀 START HERE: Create {basic_file} in your repository root. "
                "Describe your project's purpose, architecture, key abstractions, and coding conventions. "
                "This is the #1 way to improve AI coding assistance."
            )

            # Tool-specific recommendations based on what's detected or commonly used
            if "github-copilot" in tools or not tools:
                recommendations.append(
                    "📝 Add .github/copilot-instructions.md for GitHub Copilot users. "
                    "Include project-specific patterns, naming conventions, and common pitfalls."
                )

            if "cursor" in tools or not tools:
                recommendations.append(
                    "🎯 For Cursor users: Create a .cursorrules file with your team's coding standards. "
                    "This helps maintain consistency across AI-assisted coding sessions."
                )

            if "openai-codex" in tools:
                recommendations.append(
                    "🤖 For OpenAI Codex: Create AGENTS.md with agent instructions and "
                    "set up .codex/ directory for Codex-specific configuration."
                )

            recommendations.append(
                "💡 Quick win: Ensure your README.md has clear sections on architecture, setup, and testing. "
                "This provides baseline context for all AI tools."
            )
            return recommendations

        if score.overall_level == 2:
            # Level 2: Basic Instructions - need comprehensive context
            # Show detected tools
            if tools:
                tool_names = ", ".join(t.replace("-", " ").title() for t in tools)
                recommendations.append(
                    f"🔍 Detected AI tools: {tool_names}. Recommendations tailored accordingly."
                )

            missing_critical = []

            if not any("ARCHITECTURE" in f.path.upper() for f in level_3.matched_files):
                missing_critical.append("ARCHITECTURE.md")
            if not any("API" in f.path.upper() for f in level_3.matched_files):
                missing_critical.append("API.md")
            if not any(any(term in f.path.upper() for term in ["CONVENTIONS", "STYLE", "STANDARDS"])
                      for f in level_3.matched_files):
                missing_critical.append("CONVENTIONS.md")
            if not any("TESTING" in f.path.upper() for f in level_3.matched_files):
                missing_critical.append("TESTING.md")

            if missing_critical and not should_skip("documentation"):
                recommendations.append(
                    f"📚 PRIORITY: Add comprehensive documentation - you're missing {', '.join(missing_critical)}. "
                    f"These files provide essential context for AI tools to understand your codebase deeply."
                )

            priority_recs = []

            if not any("ARCHITECTURE" in f.path.upper() for f in level_3.matched_files) and in_focus("architecture"):
                priority_recs.append((
                    "🏗️ Create docs/ARCHITECTURE.md: Document your system design, component relationships, "
                    "data flow, and key architectural decisions. Include diagrams if possible. "
                    "This helps AI understand the big picture when making suggestions.", 1
                ))

            if not any(any(term in f.path.upper() for term in ["CONVENTIONS", "STYLE", "STANDARDS"])
                      for f in level_3.matched_files) and in_focus("conventions"):
                priority_recs.append((
                    "📏 Create CONVENTIONS.md: Document your team's coding standards, naming conventions, "
                    "file organization, import patterns, error handling, and testing requirements. "
                    "This ensures AI-generated code matches your team's style.", 2
                ))

            if not any("PATTERNS" in f.path.upper() for f in level_3.matched_files) and in_focus("patterns"):
                priority_recs.append((
                    "🎨 Add PATTERNS.md: Document common design patterns used in your codebase. "
                    "Include examples of: state management, error handling, API interactions, "
                    "data transformations, and component composition. AI will follow these patterns.", 3
                ))

            if not any("API" in f.path.upper() for f in level_3.matched_files) and in_focus("api"):
                priority_recs.append((
                    "🔌 Document your APIs: Create docs/API.md describing endpoints, request/response formats, "
                    "authentication, rate limiting, and error codes. Helps AI generate correct API calls.", 4
                ))

            if not any("TESTING" in f.path.upper() for f in level_3.matched_files) and in_focus("testing"):
                priority_recs.append((
                    "🧪 Add TESTING.md: Document your testing strategy, how to run tests, "
                    "coverage requirements, and common testing patterns. AI can then generate proper tests.", 5
                ))

            priority_recs.sort(key=lambda x: x[1])
            for rec, _ in priority_recs[:5]:
                recommendations.append(rec)

            if len(recommendations) < 7 and in_focus("contributing"):
                if not any("CONTRIBUTING" in f.path.upper() for f in level_3.matched_files):
                    recommendations.append(
                        "👥 Add CONTRIBUTING.md: Define workflow for PRs, commit conventions, "
                        "code review guidelines, and development setup. Helps AI understand your process."
                    )

        if score.overall_level == 3:
            # Level 3: Comprehensive Context - need skills & automation
            # Show detected tools
            if tools:
                tool_names = ", ".join(t.replace("-", " ").title() for t in tools)
                recommendations.append(
                    f"🔍 Detected AI tools: {tool_names}. Recommendations tailored accordingly."
                )

            recommendations.append(
                "⚡ LEVEL UP: You have comprehensive documentation. Now add automation and workflows "
                "to make AI even more productive with skills, hooks, and custom commands."
            )

            # Tool-specific skills directory recommendation
            skills_dir = tool_path("skills_dir")
            if skills_dir and not should_skip("skills"):
                has_skills = any(
                    any(d in dir_name for d in [".claude/skills", ".github/skills", ".cursor/skills", ".codex/skills"])
                    for dir_name in level_4.matched_directories
                )
                if not has_skills:
                    recommendations.append(
                        f"🛠️ Create {skills_dir}: Add custom skills for common tasks. Each skill should have "
                        "a SKILL.md describing its purpose, inputs, outputs, and usage. Examples: "
                        "create-component, run-tests, deploy-staging, generate-api-client. "
                        "Follows the Agent Skills standard (agentskills.io)."
                    )

            # Hooks (Claude-specific)
            if "claude-code" in tools and not should_skip("hooks"):
                if not any(".claude/hooks" in d for d in level_4.matched_directories):
                    recommendations.append(
                        "🪝 Set up .claude/hooks/: Add PostToolUse hooks for automatic actions like "
                        "formatting code, running linters, updating tests, or validating against conventions. "
                        "This ensures AI-generated code is always production-ready."
                    )

            # Commands (Claude-specific)
            if "claude-code" in tools and not should_skip("commands"):
                if not any(".claude/commands" in d for d in level_4.matched_directories):
                    recommendations.append(
                        "⌨️ Add .claude/commands/: Create custom slash commands for frequent tasks. "
                        "Examples: /new-feature, /add-test, /refactor-component, /update-docs. "
                        "Makes complex workflows one-command simple."
                    )

            # Copilot instructions directory
            if "github-copilot" in tools and not should_skip("instructions"):
                if not any(".github/instructions" in d for d in level_4.matched_directories):
                    recommendations.append(
                        "📋 Add .github/instructions/: Create scoped instruction files for different "
                        "parts of your codebase. Examples: frontend.instructions.md, api.instructions.md."
                    )

            # Cursor-specific recommendations
            if "cursor" in tools and not should_skip("cursor"):
                if not any(".cursor/rules" in d for d in level_4.matched_directories):
                    recommendations.append(
                        "🎯 Add .cursor/rules/: Create scoped rule files (.md or .mdc) for different "
                        "parts of your codebase. Also consider .cursor/skills/ for reusable skills."
                    )

            # Memory (universal)
            if not should_skip("memory"):
                if not any(any(term in f.path.upper() for term in ["MEMORY", "LEARNINGS", "DECISIONS"])
                          for f in level_4.matched_files):
                    recommendations.append(
                        "💾 Add MEMORY.md or LEARNINGS.md: Document lessons learned, past decisions, "
                        "failed approaches, and architectural evolution. Helps AI avoid repeating mistakes "
                        "and understand historical context."
                    )

            # Boris Cherny's key insight: verification loops
            if not should_skip("verification"):
                recommendations.append(
                    "✅ VERIFICATION (Boris Cherny's key insight): Give AI a way to verify its work - "
                    "tests, linters, type checkers, or browser testing. This 2-3x the quality of results. "
                    "Consider adding a verify script or PostToolUse hook for automatic validation."
                )

            # ClawdBot pattern: Agent personality/constitution
            if not should_skip("soul"):
                if not any(any(term in f.path.upper() for term in ["SOUL", "IDENTITY", "PERSONALITY"])
                          for f in level_4.matched_files):
                    recommendations.append(
                        "🎭 Consider SOUL.md or IDENTITY.md (ClawdBot pattern): Define your agent's "
                        "behavioral constitution - personality, tone, values, and guidelines for how "
                        "it should interact with users and handle edge cases."
                    )

        if score.overall_level == 4:
            # Level 4: Skills & Automation - need multi-agent setup
            # Show detected tools
            if tools:
                tool_names = ", ".join(t.replace("-", " ").title() for t in tools)
                recommendations.append(
                    f"🔍 Detected AI tools: {tool_names}. Recommendations tailored accordingly."
                )

            recommendations.append(
                "🚀 ADVANCING: You have skills and automation. Now configure multiple specialized agents "
                "and MCP integrations for more sophisticated AI collaboration."
            )

            # Tool-specific agents directory
            agents_dir = tool_path("agents_dir")
            has_agents = any(
                any(d in dir_name for d in [".github/agents", ".claude/agents", "agents"])
                for dir_name in level_5.matched_directories
            )

            if not has_agents and not should_skip("agents"):
                if "github-copilot" in tools:
                    recommendations.append(
                        "🤖 Add .github/agents/: Create specialized GitHub agents for code review "
                        "(reviewer.agent.md), testing (tester.agent.md), security analysis (security.agent.md). "
                        "Each with specific expertise and evaluation criteria."
                    )
                elif "claude-code" in tools:
                    recommendations.append(
                        "🤖 Add .claude/agents/: Create specialized agents for different tasks. "
                        "Define agent personas with specific expertise and context requirements."
                    )
                else:
                    recommendations.append(
                        "🤖 Add agents/: Create specialized agent configurations for your AI tools. "
                        "Each agent should have specific expertise and evaluation criteria."
                    )

            if not any(".mcp" in d for d in level_5.matched_directories) and not should_skip("mcp"):
                recommendations.append(
                    "🔗 Set up MCP servers: Create .mcp.json at the root (Boris Cherny pattern) for "
                    "team-shared tool integrations - Slack, databases, APIs. Also use .mcp/servers/ "
                    "for complex configs. Enables richer agent capabilities."
                )

            if not should_skip("handoffs"):
                recommendations.append(
                    "🤝 Create agents/HANDOFFS.md: Document when and how specialized agents should "
                    "hand off work to each other. Define triggers, context passing, and success criteria."
                )

        if score.overall_level == 5:
            # Level 5: Multi-Agent Ready - need fleet infrastructure
            # Show detected tools
            if tools:
                tool_names = ", ".join(t.replace("-", " ").title() for t in tools)
                recommendations.append(
                    f"🔍 Detected AI tools: {tool_names}. Recommendations tailored accordingly."
                )

            recommendations.append(
                "🎯 FLEET READY: You have multi-agent setup. Now add fleet infrastructure "
                "for managing parallel agent instances with shared memory and workflows."
            )

            if not any(".beads" in d or "beads" in d for d in level_6.matched_directories) and not should_skip("beads"):
                recommendations.append(
                    "🧠 Set up Beads: Create .beads/ for persistent memory across agent sessions. "
                    "Beads provides external memory that survives session timeouts and enables "
                    "long-horizon work across multiple agent instances."
                )

            if not any("workflows" in d or "pipelines" in d for d in level_6.matched_directories) and not should_skip("workflows"):
                recommendations.append(
                    "🔄 Add workflows/: Create YAML workflow definitions for multi-step processes. "
                    "Examples: workflows/code_review.yaml, workflows/feature_development.yaml. "
                    "These coordinate agent activities across complex tasks."
                )

            if not any("SHARED_CONTEXT" in f.path.upper() for f in level_6.matched_files) and not should_skip("shared_context"):
                recommendations.append(
                    "📊 Create SHARED_CONTEXT.md: Document context that all agents should have access to - "
                    "critical system constraints, business rules, compliance requirements, and team values."
                )

            if not should_skip("monorepo"):
                # Tool-specific monorepo context
                if "claude-code" in tools:
                    recommendations.append(
                        "📦 For monorepos: Add packages/*/CLAUDE.md for package-specific context. "
                        "This helps agents understand boundaries and relationships between packages."
                    )
                elif "github-copilot" in tools:
                    recommendations.append(
                        "📦 For monorepos: Add packages/*/.github/copilot-instructions.md for package-specific context. "
                        "This helps Copilot understand boundaries and relationships between packages."
                    )
                else:
                    recommendations.append(
                        "📦 For monorepos: Add package-specific context files for each package. "
                        "This helps agents understand boundaries and relationships between packages."
                    )

        if score.overall_level == 6:
            # Level 6: Fleet Infrastructure - need agent fleet governance
            # Show detected tools
            if tools:
                tool_names = ", ".join(t.replace("-", " ").title() for t in tools)
                recommendations.append(
                    f"🔍 Detected AI tools: {tool_names}. Recommendations tailored accordingly."
                )

            recommendations.append(
                "⚡ FLEET INFRASTRUCTURE: You have the basics. Now scale to a full agent fleet "
                "with governance, scheduling, and multi-agent pipelines."
            )

            if not any("GOVERNANCE" in f.path.upper() for f in level_7.matched_files) and not should_skip("governance"):
                recommendations.append(
                    "📋 Create GOVERNANCE.md: Document agent permissions, boundaries, and policies. "
                    "Define what agents can and cannot do, approval requirements, and escalation paths."
                )

            if not any("SCHEDULING" in f.path.upper() or "PRIORITY" in f.path.upper() for f in level_7.matched_files) and not should_skip("scheduling"):
                recommendations.append(
                    "📅 Add agents/SCHEDULING.md: Define how to prioritize and schedule agent work. "
                    "Include queue management, priority rules, and resource allocation strategies."
                )

            if not any("convoys" in d or "molecules" in d or "epics" in d for d in level_7.matched_directories) and not should_skip("convoys"):
                recommendations.append(
                    "🚛 Set up convoys/ or molecules/: Use Gas Town-style work decomposition. "
                    "Break large tasks into molecules (atomic units) and convoys (coordinated groups)."
                )

            # Gas Town advanced patterns
            if not any("swarm" in d or "wisps" in d or "polecats" in d for d in level_7.matched_directories) and not should_skip("swarm"):
                recommendations.append(
                    "🐝 Consider swarm/, wisps/, or polecats/ (Gas Town patterns): "
                    "swarm/ for distributed agent coordination, wisps/ for lightweight ephemeral agents, "
                    "polecats/ for aggressive cleanup and maintenance agents."
                )

            if not should_skip("metrics"):
                recommendations.append(
                    "📊 Add agents/METRICS.md: Track agent performance, success rates, and productivity. "
                    "Use metrics to optimize your fleet configuration and identify bottlenecks."
                )

        if score.overall_level == 7:
            # Level 7: Agent Fleet - need custom orchestration
            # Show detected tools
            if tools:
                tool_names = ", ".join(t.replace("-", " ").title() for t in tools)
                recommendations.append(
                    f"🔍 Detected AI tools: {tool_names}. Recommendations tailored accordingly."
                )

            recommendations.append(
                "🎖️ AGENT FLEET: You're managing a full fleet. Now consider custom orchestration "
                "for advanced coordination and meta-automation."
            )

            if not should_skip("orchestration"):
                recommendations.append(
                    "🏗️ Build orchestration/: Create custom orchestration logic for complex workflows. "
                    "Define how agents coordinate, share state, and handle failures at scale."
                )

            if not should_skip("gastown"):
                recommendations.append(
                    "🔧 Consider Gas Town: Set up .gastown/ configuration for Steve Yegge's "
                    "multi-agent orchestrator. It provides Kubernetes-like agent management."
                )

            if not should_skip("meta"):
                recommendations.append(
                    "⚙️ Add meta/: Create meta-automation that generates automation. "
                    "Templates and generators that create new agent configs, workflows, and skills."
                )

            if not should_skip("experimental"):
                recommendations.append(
                    "🧪 Explore experimental/: Document frontier techniques you're exploring. "
                    "New patterns, frameworks, and approaches for AI-assisted development."
                )

            # Gas Town/ClawdBot communication patterns
            if not should_skip("protocols"):
                recommendations.append(
                    "📬 Consider agent communication protocols (Gas Town/ClawdBot patterns): "
                    "MAIL_PROTOCOL.md for inter-agent messaging, FEDERATION.md for distributed agents, "
                    "ESCALATION.md for handling failures, watchdog/ for monitoring agents."
                )

        if score.overall_level == 8:
            # Level 8: Custom Orchestration - frontier level
            # Show detected tools
            if tools:
                tool_names = ", ".join(t.replace("-", " ").title() for t in tools)
                recommendations.append(
                    f"🔍 Detected AI tools: {tool_names}. You're at the frontier!"
                )

            recommendations.append(
                "🌟 FRONTIER: You're at Level 8 - building custom orchestration! "
                "You're among the most advanced AI-assisted development setups in existence."
            )
            recommendations.append(
                "🎓 Share your learnings: Write blog posts, create templates, or contribute patterns "
                "back to the community. Your setup can help others level up their AI proficiency."
            )
            recommendations.append(
                "📈 Track metrics: Monitor AI-assisted productivity gains, code quality improvements, "
                "and developer satisfaction. Quantify your success to justify investment."
            )
            recommendations.append(
                "🔬 Push boundaries: You're positioned to shape the future of AI-assisted development. "
                "Experiment with new patterns and share what works."
            )
            recommendations.append(
                "🤝 Mentor others: Help other teams in your organization adopt similar practices. "
                "Create internal documentation and training on context engineering."
            )

        return recommendations


def scan_multiple_repos(repo_paths: List[str], verbose: bool = False) -> List[RepoScore]:
    """Scan multiple repositories and return scores for all."""

    scores: List[RepoScore] = []
    for repo_path in repo_paths:
        if os.path.isdir(repo_path):
            scanner = RepoScanner(repo_path, verbose=verbose)
            scores.append(scanner.scan())
    return scores


def scan_github_org(org_path: str, verbose: bool = False) -> List[RepoScore]:
    """Scan all repositories in a directory (like a cloned org)."""

    scores: List[RepoScore] = []
    org_dir = Path(org_path)

    if not org_dir.exists():
        return scores

    for item in org_dir.iterdir():
        if item.is_dir() and not item.name.startswith("."):
            scanner = RepoScanner(str(item), verbose=verbose)
            scores.append(scanner.scan())

    return scores
