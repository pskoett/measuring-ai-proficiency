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

from .config import LEVELS, CORE_AI_FILES, LevelConfig, filter_patterns_for_tools
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
# Note: Max file size is now configurable via RepoConfig.max_file_size (default: 100KB)

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
    effective_thresholds: Dict[int, int] = field(default_factory=dict)  # Level -> % threshold
    default_level: Optional[int] = None  # Level with default thresholds (when custom are used)

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

    # Config getters with defaults (used before config is loaded)
    @property
    def _max_file_size(self) -> int:
        return self.config.max_file_size if self.config else 100_000

    @property
    def _min_substantive_bytes(self) -> int:
        return self.config.min_substantive_bytes if self.config else 100

    @property
    def _word_threshold_partial(self) -> int:
        return self.config.word_threshold_partial if self.config else 50

    @property
    def _word_threshold_full(self) -> int:
        return self.config.word_threshold_full if self.config else 200

    @property
    def _git_timeout(self) -> int:
        return self.config.git_timeout if self.config else 5

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
        score.overall_level, score.effective_thresholds, score.default_level = self._calculate_overall_level(score.level_scores)
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

        # Filter patterns based on configured tools
        configured_tools = self.config.tools if self.config else []
        file_patterns = filter_patterns_for_tools(config.file_patterns, configured_tools)
        dir_patterns = filter_patterns_for_tools(config.directory_patterns, configured_tools)

        # Count total unique patterns for coverage calculation (filtered)
        all_patterns = set(file_patterns + dir_patterns)
        level_score.total_patterns = len(all_patterns)

        matched_patterns: Set[str] = set()

        # Check file patterns
        for pattern in file_patterns:
            matches = self._find_matches(pattern)
            for match_path in matches:
                file_match = self._create_file_match(match_path, pattern, level_num)
                level_score.matched_files.append(file_match)
                matched_patterns.add(pattern)

        # Check directory patterns
        for pattern in dir_patterns:
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
                    if path.stat().st_size <= self._max_file_size:
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
                    if match.stat().st_size <= self._max_file_size:
                        files.append(match)
            except (OSError, PermissionError):
                pass

        return files

    def _read_file_safe(self, path: Path) -> Optional[str]:
        """Safely read file content with size limit and error handling."""

        try:
            if path.stat().st_size > self._max_file_size:
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
                timeout=self._git_timeout,
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
        # Substance score based on word count (configurable thresholds)
        if len(words) > self._word_threshold_full:
            score += 2.0
        elif len(words) > self._word_threshold_partial:
            score += 1.0

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

    # Default thresholds for level advancement (percentage coverage required)
    DEFAULT_THRESHOLDS: Dict[int, int] = {
        3: 15,   # Comprehensive context
        4: 12,   # Skills & automation
        5: 10,   # Multi-agent ready
        6: 8,    # Fleet infrastructure
        7: 6,    # Agent fleet
        8: 5,    # Custom orchestration (frontier)
    }

    def _calculate_overall_level(self, level_scores: Dict[int, LevelScore]) -> tuple:
        """
        Calculate the overall maturity level (1-8) and return effective thresholds.

        Returns:
            tuple: (overall_level, effective_thresholds, default_level)
            - overall_level: Level achieved with effective thresholds
            - effective_thresholds: Dict of thresholds used (custom if configured)
            - default_level: Level that would be achieved with default thresholds (None if no custom)
        """

        # Use custom thresholds from config if available
        has_custom = self.config and self.config.thresholds
        thresholds = self.DEFAULT_THRESHOLDS.copy()
        if has_custom:
            for level_num, custom_threshold in self.config.thresholds.items():
                thresholds[level_num] = custom_threshold

        # Check for core AI files (Level 2 requirement)
        level_2 = level_scores.get(2)
        if not level_2 or level_2.substantive_file_count == 0:
            return 1, thresholds, None  # No AI files = Level 1

        has_core_file = any(
            any(core in f.path for core in CORE_AI_FILES) for f in level_2.matched_files
        )
        if not has_core_file:
            return 1, thresholds, None  # No core AI file = Level 1

        # Calculate level with effective thresholds
        current_level = self._calc_level_with_thresholds(level_scores, thresholds)

        # Calculate default level if custom thresholds are in use
        default_level = None
        if has_custom:
            default_level = self._calc_level_with_thresholds(level_scores, self.DEFAULT_THRESHOLDS)

        return current_level, thresholds, default_level

    def _calc_level_with_thresholds(self, level_scores: Dict[int, LevelScore], thresholds: Dict[int, int]) -> int:
        """Calculate level using given thresholds."""
        current_level = 2
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

    # =========================================================================
    # Recommendation Helper Methods
    # =========================================================================

    def _should_skip(self, config: Optional[RepoConfig], rec_type: str) -> bool:
        """Check if a recommendation type should be skipped."""
        if config and config.skip_recommendations:
            return rec_type in config.skip_recommendations
        return False

    def _in_focus(self, config: Optional[RepoConfig], rec_type: str) -> bool:
        """Check if a recommendation type is in the focus area."""
        if config and config.focus_areas:
            return rec_type in config.focus_areas
        return True

    def _tool_path(self, tools: List[str], rec_type: str) -> str:
        """Get tool-specific path for a recommendation type."""
        return format_multi_tool_options(tools, rec_type)

    # Proper display names for AI tools (handles special capitalization like "GitHub")
    TOOL_DISPLAY_NAMES = {
        "claude-code": "Claude Code",
        "github-copilot": "GitHub Copilot",
        "cursor": "Cursor",
        "openai-codex": "OpenAI Codex",
    }

    def _format_tool_name(self, tool: str) -> str:
        """Format a tool ID into a display name."""
        return self.TOOL_DISPLAY_NAMES.get(tool, tool.replace("-", " ").title())

    def _add_tools_header(
        self, recs: List[str], tools: List[str], suffix: str = "Recommendations tailored accordingly."
    ) -> None:
        """Add detected tools header to recommendations."""
        if tools:
            tool_names = ", ".join(self._format_tool_name(t) for t in tools)
            recs.append(f"🔍 Detected AI tools: {tool_names}. {suffix}")

    def _recommendations_level_1(self, score: RepoScore, tools: List[str]) -> List[str]:
        """Generate recommendations for Level 1: Zero AI."""
        recs: List[str] = []
        basic_file = self._tool_path(tools, "basic_file") or "CLAUDE.md"

        self._add_tools_header(recs, tools)

        recs.append(
            f"🚀 START HERE: Create {basic_file} in your repository root. "
            "Describe your project's purpose, architecture, key abstractions, and coding conventions. "
            "This is the #1 way to improve AI coding assistance."
        )

        if "github-copilot" in tools or not tools:
            recs.append(
                "📝 Add .github/copilot-instructions.md for GitHub Copilot users. "
                "Include project-specific patterns, naming conventions, and common pitfalls."
            )

        if "cursor" in tools or not tools:
            recs.append(
                "🎯 For Cursor users: Create a .cursorrules file with your team's coding standards. "
                "This helps maintain consistency across AI-assisted coding sessions."
            )

        if "openai-codex" in tools:
            recs.append(
                "🤖 For OpenAI Codex: Create AGENTS.md with agent instructions and "
                "set up .codex/ directory for Codex-specific configuration."
            )

        recs.append(
            "💡 Quick win: Ensure your README.md has clear sections on architecture, setup, and testing. "
            "This provides baseline context for all AI tools."
        )

        return recs

    def _recommendations_level_2(
        self, score: RepoScore, tools: List[str], config: Optional[RepoConfig]
    ) -> List[str]:
        """Generate recommendations for Level 2: Basic Instructions."""
        recs: List[str] = []
        level_2 = score.level_scores.get(2)
        level_3 = score.level_scores.get(3)
        if not level_3:
            return recs

        self._add_tools_header(recs, tools)

        # First, check for missing Level 2 files (complete Level 2 before moving to Level 3)
        level_2_files = [f.path for f in level_2.matched_files] if level_2 else []

        # Check for missing AGENTS.md (for claude-code users)
        if "claude-code" in tools or not tools:
            has_claude_md = any("CLAUDE.md" in f for f in level_2_files)
            has_agents_md = any(f == "AGENTS.md" for f in level_2_files)
            if has_claude_md and not has_agents_md:
                recs.append(
                    "📋 Add AGENTS.md: Define agent roles, responsibilities, and behavioral guidelines. "
                    "Complements CLAUDE.md by separating 'what the project is' from 'how agents should behave'. "
                    "Include sections for different agent types (reviewer, implementer, etc.)."
                )

        # Check for missing copilot instructions (for github-copilot users)
        if "github-copilot" in tools:
            has_copilot_instructions = any("copilot-instructions.md" in f for f in level_2_files)
            if not has_copilot_instructions:
                recs.append(
                    "📝 Add .github/copilot-instructions.md: Provide GitHub Copilot with project-specific context. "
                    "Include coding patterns, naming conventions, and common pitfalls to avoid."
                )

        # Check for missing cursorrules (for cursor users)
        if "cursor" in tools:
            has_cursorrules = any(".cursorrules" in f for f in level_2_files)
            if not has_cursorrules:
                recs.append(
                    "🎯 Add .cursorrules: Configure Cursor with your team's coding standards. "
                    "This ensures AI-generated code matches your project's style."
                )

        # Recommend scoped instructions for larger projects
        level_3_dirs = level_3.matched_directories if level_3 else []

        # Copilot scoped instructions
        if "github-copilot" in tools and not self._should_skip(config, "scoped_instructions"):
            has_instructions_dir = any(".github/instructions" in d for d in level_3_dirs)
            if not has_instructions_dir and len(level_3.matched_files) > 10:
                recs.append(
                    "📂 Add scoped instructions for Copilot: Create .github/instructions/ with area-specific files "
                    "like frontend.instructions.md, api.instructions.md, tests.instructions.md. "
                    "Provides targeted context for different parts of your codebase."
                )

        # Cursor scoped rules
        if "cursor" in tools and not self._should_skip(config, "scoped_instructions"):
            has_cursor_rules_dir = any(".cursor/rules" in d for d in level_3_dirs)
            if not has_cursor_rules_dir and len(level_3.matched_files) > 10:
                recs.append(
                    "📂 Add scoped rules for Cursor: Create .cursor/rules/ with area-specific files "
                    "like frontend.md, backend.md, database.md. "
                    "Provides targeted context for different parts of your codebase."
                )

        # Check for missing critical docs
        missing_critical = []
        level_3_files = level_3.matched_files

        checks = [
            ("ARCHITECTURE", "ARCHITECTURE.md"),
            ("API", "API.md"),
            (["CONVENTIONS", "STYLE", "STANDARDS"], "CONVENTIONS.md"),
            ("TESTING", "TESTING.md"),
        ]

        for terms, filename in checks:
            if isinstance(terms, str):
                terms = [terms]
            if not any(any(t in f.path.upper() for t in terms) for f in level_3_files):
                missing_critical.append(filename)

        if missing_critical and not self._should_skip(config, "documentation"):
            recs.append(
                f"📚 PRIORITY: Add comprehensive documentation - you're missing {', '.join(missing_critical)}. "
                "These files provide essential context for AI tools to understand your codebase deeply."
            )

        # Priority recommendations
        priority_recs = []

        if not any("ARCHITECTURE" in f.path.upper() for f in level_3_files) and self._in_focus(config, "architecture"):
            priority_recs.append((
                "🏗️ Create docs/ARCHITECTURE.md: Document your system design, component relationships, "
                "data flow, and key architectural decisions. Include diagrams if possible. "
                "This helps AI understand the big picture when making suggestions.", 1
            ))

        if not any(any(t in f.path.upper() for t in ["CONVENTIONS", "STYLE", "STANDARDS"]) for f in level_3_files) and self._in_focus(config, "conventions"):
            priority_recs.append((
                "📏 Create CONVENTIONS.md: Document your team's coding standards, naming conventions, "
                "file organization, import patterns, error handling, and testing requirements. "
                "This ensures AI-generated code matches your team's style.", 2
            ))

        if not any("PATTERNS" in f.path.upper() for f in level_3_files) and self._in_focus(config, "patterns"):
            priority_recs.append((
                "🎨 Add PATTERNS.md: Document common design patterns used in your codebase. "
                "Include examples of: state management, error handling, API interactions, "
                "data transformations, and component composition. AI will follow these patterns.", 3
            ))

        if not any("API" in f.path.upper() for f in level_3_files) and self._in_focus(config, "api"):
            priority_recs.append((
                "🔌 Document your APIs: Create docs/API.md describing endpoints, request/response formats, "
                "authentication, rate limiting, and error codes. Helps AI generate correct API calls.", 4
            ))

        if not any("TESTING" in f.path.upper() for f in level_3_files) and self._in_focus(config, "testing"):
            priority_recs.append((
                "🧪 Add TESTING.md: Document your testing strategy, how to run tests, "
                "coverage requirements, and common testing patterns. AI can then generate proper tests.", 5
            ))

        priority_recs.sort(key=lambda x: x[1])
        for rec, _ in priority_recs[:5]:
            recs.append(rec)

        if len(recs) < 7 and self._in_focus(config, "contributing"):
            if not any("CONTRIBUTING" in f.path.upper() for f in level_3_files):
                recs.append(
                    "👥 Add CONTRIBUTING.md: Define workflow for PRs, commit conventions, "
                    "code review guidelines, and development setup. Helps AI understand your process."
                )

        return recs

    def _recommendations_level_3(
        self, score: RepoScore, tools: List[str], config: Optional[RepoConfig]
    ) -> List[str]:
        """Generate recommendations for Level 3: Comprehensive Context."""
        recs: List[str] = []
        level_4 = score.level_scores.get(4)
        if not level_4:
            return recs

        self._add_tools_header(recs, tools)

        recs.append(
            "⚡ LEVEL UP: You have comprehensive documentation. Now add automation and workflows "
            "to make AI even more productive with skills, hooks, and custom commands."
        )

        # Skills directory
        skills_dir = self._tool_path(tools, "skills_dir")
        if skills_dir and not self._should_skip(config, "skills"):
            has_skills = any(
                any(d in dir_name for d in [".claude/skills", ".github/skills", ".cursor/skills", ".codex/skills"])
                for dir_name in level_4.matched_directories
            )
            if not has_skills:
                recs.append(
                    f"🛠️ Create {skills_dir}: Add custom skills for common tasks. Each skill should have "
                    "a SKILL.md describing its purpose, inputs, outputs, and usage. Examples: "
                    "create-component, run-tests, deploy-staging, generate-api-client. "
                    "Follows the Agent Skills standard (agentskills.io)."
                )

        # Claude-specific: hooks and commands
        if "claude-code" in tools:
            if not self._should_skip(config, "hooks"):
                if not any(".claude/hooks" in d for d in level_4.matched_directories):
                    recs.append(
                        "🪝 Set up .claude/hooks/: Add PostToolUse hooks for automatic actions like "
                        "formatting code, running linters, updating tests, or validating against conventions. "
                        "This ensures AI-generated code is always production-ready."
                    )

            if not self._should_skip(config, "commands"):
                if not any(".claude/commands" in d for d in level_4.matched_directories):
                    recs.append(
                        "⌨️ Add .claude/commands/: Create custom slash commands for frequent tasks. "
                        "Examples: /new-feature, /add-test, /refactor-component, /update-docs. "
                        "Makes complex workflows one-command simple."
                    )

        # Copilot instructions directory
        if "github-copilot" in tools and not self._should_skip(config, "instructions"):
            if not any(".github/instructions" in d for d in level_4.matched_directories):
                recs.append(
                    "📋 Add .github/instructions/: Create scoped instruction files for different "
                    "parts of your codebase. Examples: frontend.instructions.md, api.instructions.md."
                )

        # Cursor-specific
        if "cursor" in tools and not self._should_skip(config, "cursor"):
            if not any(".cursor/rules" in d for d in level_4.matched_directories):
                recs.append(
                    "🎯 Add .cursor/rules/: Create scoped rule files (.md or .mdc) for different "
                    "parts of your codebase. Also consider .cursor/skills/ for reusable skills."
                )

        # Memory (universal) - check files and .memory/ directory
        if not self._should_skip(config, "memory"):
            has_memory_file = any(
                any(t in f.path.upper() for t in ["MEMORY", "LEARNINGS", "DECISIONS"])
                for f in level_4.matched_files
            )
            has_memory_dir = any(".memory" in d.lower() for d in level_4.matched_directories)
            if not has_memory_file and not has_memory_dir:
                recs.append(
                    "💾 Add MEMORY.md, LEARNINGS.md, or DECISIONS.md: Document lessons learned, "
                    "past decisions, failed approaches, and architectural evolution. Helps AI avoid "
                    "repeating mistakes. Alternatively, use a .memory/ directory for structured memory files."
                )

        # MCP basics (universal - shared tool configurations)
        if not self._should_skip(config, "mcp"):
            has_mcp = (
                any(".mcp" in f.path.lower() for f in level_4.matched_files)
                or any(".mcp" in d.lower() for d in level_4.matched_directories)
            )
            if not has_mcp:
                recs.append(
                    "🔗 Add .mcp.json: Configure shared MCP (Model Context Protocol) servers at the root "
                    "(Boris Cherny pattern). This allows team-wide tool integrations like databases, APIs, "
                    "or Slack. Start simple with filesystem or search servers, then add custom ones."
                )

        # Boris Cherny's verification loops
        if not self._should_skip(config, "verification"):
            recs.append(
                "✅ VERIFICATION (Boris Cherny's key insight): Give AI a way to verify its work - "
                "tests, linters, type checkers, or browser testing. This 2-3x the quality of results. "
                "Consider adding a verify script or PostToolUse hook for automatic validation."
            )

        # ClawdBot pattern: Agent personality
        if not self._should_skip(config, "soul"):
            if not any(any(t in f.path.upper() for t in ["SOUL", "IDENTITY", "PERSONALITY"]) for f in level_4.matched_files):
                recs.append(
                    "🎭 Consider SOUL.md or IDENTITY.md (ClawdBot pattern): Define your agent's "
                    "behavioral constitution - personality, tone, values, and guidelines for how "
                    "it should interact with users and handle edge cases."
                )

        return recs

    def _recommendations_level_4(
        self, score: RepoScore, tools: List[str], config: Optional[RepoConfig]
    ) -> List[str]:
        """Generate recommendations for Level 4: Skills & Automation."""
        recs: List[str] = []
        level_4 = score.level_scores.get(4)
        level_5 = score.level_scores.get(5)
        if not level_5:
            return recs

        # Get matched files/dirs for existence checks
        matched_dirs_4 = level_4.matched_directories if level_4 else []
        matched_files_4 = [f.path for f in level_4.matched_files] if level_4 else []

        self._add_tools_header(recs, tools)

        recs.append(
            "🚀 ADVANCING: You have skills and automation. Now configure multiple specialized agents "
            "and MCP integrations for more sophisticated AI collaboration."
        )

        has_agents = any(
            any(d in dir_name for d in [".github/agents", ".claude/agents", "agents"])
            for dir_name in level_5.matched_directories
        )

        if not has_agents and not self._should_skip(config, "agents"):
            if "github-copilot" in tools:
                recs.append(
                    "🤖 Add .github/agents/: Create specialized GitHub agents for code review "
                    "(reviewer.agent.md), testing (tester.agent.md), security analysis (security.agent.md). "
                    "Each with specific expertise and evaluation criteria."
                )
            elif "claude-code" in tools:
                recs.append(
                    "🤖 Add .claude/agents/: Create specialized agents for different tasks. "
                    "Define agent personas with specific expertise and context requirements."
                )
            else:
                recs.append(
                    "🤖 Add agents/: Create specialized agent configurations for your AI tools. "
                    "Each agent should have specific expertise and evaluation criteria."
                )

        # Check for advanced MCP setup (basics covered in Level 3)
        has_mcp_servers_dir = any(".mcp/servers" in d for d in level_5.matched_directories)
        if not has_mcp_servers_dir and not self._should_skip(config, "mcp"):
            recs.append(
                "🔗 Advanced MCP setup: Create .mcp/servers/ for custom server configurations. "
                "Build domain-specific servers (database explorer, CI/CD status, internal docs). "
                "Consider .mcp/prompts/ for reusable prompt templates across agents."
            )

        if not self._should_skip(config, "handoffs"):
            recs.append(
                "🤝 Create agents/HANDOFFS.md: Document when and how specialized agents should "
                "hand off work to each other. Define triggers, context passing, and success criteria."
            )

        # New: Workflow automation recommendations
        has_makefile = any("Makefile" in f or "justfile" in f for f in matched_files_4)
        if not has_makefile and not self._should_skip(config, "automation"):
            recs.append(
                "⚡ Add Makefile or justfile: Define common development tasks (build, test, lint, deploy) "
                "so agents can execute them. Include AI-specific targets like 'make ai-review' or 'make context-update'."
            )

        # New: Scripts documentation
        has_scripts = "scripts" in matched_dirs_4 or any("scripts/" in f for f in matched_files_4)
        if has_scripts and not self._should_skip(config, "scripts"):
            has_scripts_readme = any("scripts/README" in f or "scripts/SCRIPTS" in f for f in matched_files_4)
            if not has_scripts_readme:
                recs.append(
                    "📜 Add scripts/README.md: Document your automation scripts so agents understand "
                    "what each script does, its parameters, and when to use it."
                )

        # New: Context file for complex projects
        has_context = any("context.yaml" in f or "context.json" in f for f in matched_files_4)
        if not has_context and not self._should_skip(config, "context"):
            recs.append(
                "📦 Add context.yaml or context.json: Define structured project context that agents can parse. "
                "Include key directories, important files, build commands, and testing patterns."
            )

        return recs

    def _recommendations_level_5(
        self, score: RepoScore, tools: List[str], config: Optional[RepoConfig]
    ) -> List[str]:
        """Generate recommendations for Level 5: Multi-Agent Ready."""
        recs: List[str] = []
        level_6 = score.level_scores.get(6)
        if not level_6:
            return recs

        self._add_tools_header(recs, tools)

        recs.append(
            "🎯 FLEET READY: You have multi-agent setup. Now add fleet infrastructure "
            "for managing parallel agent instances with shared memory and workflows."
        )

        if not any(".beads" in d or "beads" in d for d in level_6.matched_directories) and not self._should_skip(config, "beads"):
            recs.append(
                "🧠 Set up Beads: Create .beads/ for persistent memory across agent sessions. "
                "Beads provides external memory that survives session timeouts and enables "
                "long-horizon work across multiple agent instances."
            )

        if not any("workflows" in d or "pipelines" in d for d in level_6.matched_directories) and not self._should_skip(config, "workflows"):
            recs.append(
                "🔄 Add workflows/: Create YAML workflow definitions for multi-step processes. "
                "Examples: workflows/code_review.yaml, workflows/feature_development.yaml. "
                "These coordinate agent activities across complex tasks."
            )

        if not any("SHARED_CONTEXT" in f.path.upper() for f in level_6.matched_files) and not self._should_skip(config, "shared_context"):
            recs.append(
                "📊 Create SHARED_CONTEXT.md: Document context that all agents should have access to - "
                "critical system constraints, business rules, compliance requirements, and team values."
            )

        if not self._should_skip(config, "monorepo"):
            if "claude-code" in tools:
                recs.append(
                    "📦 For monorepos: Add packages/*/CLAUDE.md for package-specific context. "
                    "This helps agents understand boundaries and relationships between packages."
                )
            elif "github-copilot" in tools:
                recs.append(
                    "📦 For monorepos: Add packages/*/.github/copilot-instructions.md for package-specific context. "
                    "This helps Copilot understand boundaries and relationships between packages."
                )
            else:
                recs.append(
                    "📦 For monorepos: Add package-specific context files for each package. "
                    "This helps agents understand boundaries and relationships between packages."
                )

        # Basic observability
        if not self._should_skip(config, "observability"):
            recs.append(
                "📊 Add basic agent observability: Log agent actions, decisions, and outcomes. "
                "Track metrics like task completion rate, error frequency, and common failure modes. "
                "This helps identify where agents struggle and need better context."
            )

        return recs

    def _recommendations_level_6(
        self, score: RepoScore, tools: List[str], config: Optional[RepoConfig]
    ) -> List[str]:
        """Generate recommendations for Level 6: Fleet Infrastructure."""
        recs: List[str] = []
        level_7 = score.level_scores.get(7)
        if not level_7:
            return recs

        self._add_tools_header(recs, tools)

        recs.append(
            "⚡ FLEET INFRASTRUCTURE: You have the basics. Now scale to a full agent fleet "
            "with governance, scheduling, and multi-agent pipelines."
        )

        if not any("GOVERNANCE" in f.path.upper() for f in level_7.matched_files) and not self._should_skip(config, "governance"):
            recs.append(
                "📋 Create GOVERNANCE.md: Document agent permissions, boundaries, and policies. "
                "Define what agents can and cannot do, approval requirements, and escalation paths."
            )

        if not any("SCHEDULING" in f.path.upper() or "PRIORITY" in f.path.upper() for f in level_7.matched_files) and not self._should_skip(config, "scheduling"):
            recs.append(
                "📅 Add agents/SCHEDULING.md: Define how to prioritize and schedule agent work. "
                "Include queue management, priority rules, and resource allocation strategies."
            )

        if not any("convoys" in d or "molecules" in d or "epics" in d for d in level_7.matched_directories) and not self._should_skip(config, "convoys"):
            recs.append(
                "🚛 Set up convoys/ or molecules/: Use Gas Town-style work decomposition. "
                "Break large tasks into molecules (atomic units) and convoys (coordinated groups)."
            )

        if not any("swarm" in d or "wisps" in d or "polecats" in d for d in level_7.matched_directories) and not self._should_skip(config, "swarm"):
            recs.append(
                "🐝 Consider swarm/, wisps/, or polecats/ (Gas Town patterns): "
                "swarm/ for distributed agent coordination, wisps/ for lightweight ephemeral agents, "
                "polecats/ for aggressive cleanup and maintenance agents."
            )

        if not self._should_skip(config, "metrics"):
            recs.append(
                "📊 Add agents/METRICS.md: Track agent performance, success rates, and productivity. "
                "Use metrics to optimize your fleet configuration and identify bottlenecks."
            )

        # Fleet observability and health checks
        if not self._should_skip(config, "observability"):
            recs.append(
                "🏥 Add fleet health checks: Define agents/HEALTH.md documenting how to verify agent fleet health. "
                "Include: heartbeat patterns, stuck-task detection, memory leak indicators, and auto-recovery triggers."
            )

        if not self._should_skip(config, "recovery"):
            recs.append(
                "🔄 Document recovery patterns: Create agents/RECOVERY.md with strategies for common failures. "
                "Include: context corruption, stuck loops, cascading failures, and graceful degradation procedures."
            )

        return recs

    def _recommendations_level_7(
        self, score: RepoScore, tools: List[str], config: Optional[RepoConfig]
    ) -> List[str]:
        """Generate recommendations for Level 7: Agent Fleet."""
        recs: List[str] = []
        level_7 = score.level_scores.get(7)
        level_8 = score.level_scores.get(8)

        # Get existing files/directories to avoid redundant recommendations
        matched_dirs_7 = level_7.matched_directories if level_7 else []
        matched_dirs_8 = level_8.matched_directories if level_8 else []
        matched_files_8 = [f.path.upper() for f in level_8.matched_files] if level_8 else []
        all_dirs = matched_dirs_7 + matched_dirs_8

        self._add_tools_header(recs, tools)

        recs.append(
            "🎖️ AGENT FLEET: You're managing a full fleet. Now consider custom orchestration "
            "for advanced coordination and meta-automation."
        )

        # Only recommend if orchestration/ doesn't exist
        has_orchestration = any("orchestration" in d for d in all_dirs)
        if not has_orchestration and not self._should_skip(config, "orchestration"):
            recs.append(
                "🏗️ Build orchestration/: Create custom orchestration logic for complex workflows. "
                "Define how agents coordinate, share state, and handle failures at scale."
            )

        # Gas Town alternative: explain what it solves, provide non-Google alternatives
        has_gastown = any("gastown" in d for d in all_dirs)
        if not has_gastown and not self._should_skip(config, "gastown"):
            recs.append(
                "🔧 Multi-agent orchestration: Consider orchestrator patterns for managing agent fleets. "
                "Options: Gas Town (.gastown/) for Kubernetes-like management, or simpler approaches "
                "like a central ORCHESTRATOR.md defining agent roles and handoff protocols."
            )

        # Meta-automation with existence check
        has_meta = any("meta" in d or "generator" in d for d in all_dirs)
        if not has_meta and not self._should_skip(config, "meta"):
            recs.append(
                "⚙️ Add meta/ or generators/: Create meta-automation that generates automation. "
                "Templates and generators that create new agent configs, workflows, and skills."
            )

        # Agent SDK/framework guidance
        has_sdk = any("agent_sdk" in d or "agent_framework" in d for d in all_dirs)
        if not has_sdk and not self._should_skip(config, "sdk"):
            recs.append(
                "🛠️ Build agent_sdk/ or agent_framework/: Create reusable components for agent development. "
                "Shared utilities, base classes, and patterns that all agents can use."
            )

        # Experimental with existence check
        has_experimental = any("experimental" in d or "frontier" in d for d in all_dirs)
        if not has_experimental and not self._should_skip(config, "experimental"):
            recs.append(
                "🧪 Explore experimental/: Document frontier techniques you're exploring. "
                "New patterns, frameworks, and approaches for AI-assisted development."
            )

        # Protocols with existence check - provide clearer explanation
        has_protocols = any("protocol" in d or "watchdog" in d for d in all_dirs)
        has_protocol_files = any("PROTOCOL" in f or "FEDERATION" in f or "ESCALATION" in f for f in matched_files_8)
        if not has_protocols and not has_protocol_files and not self._should_skip(config, "protocols"):
            recs.append(
                "📬 Define agent communication protocols: Create protocols/ directory with "
                "inter-agent messaging patterns, failure escalation procedures, and health monitoring. "
                "Examples: PROTOCOL.md (message formats), ESCALATION.md (error handling), watchdog/ (monitoring)."
            )

        return recs

    def _recommendations_level_8(
        self, score: RepoScore, tools: List[str], config: Optional[RepoConfig]
    ) -> List[str]:
        """Generate recommendations for Level 8: Custom Orchestration."""
        recs: List[str] = []
        level_8 = score.level_scores.get(8)

        # Get existing files/directories
        matched_dirs = level_8.matched_directories if level_8 else []
        matched_files = [f.path.upper() for f in level_8.matched_files] if level_8 else []

        self._add_tools_header(recs, tools, suffix="You're at the frontier!")

        recs.append(
            "🌟 FRONTIER: You're at Level 8 - building custom orchestration! "
            "You're among the most advanced AI-assisted development setups in existence."
        )

        # Conditional recommendations based on what's missing
        has_tools_custom = any("tools/custom" in d or ".tools" in d for d in matched_dirs)
        if not has_tools_custom and not self._should_skip(config, "tools"):
            recs.append(
                "🔧 Build tools/custom/: Create custom tool definitions and integrations. "
                "Define reusable tool configurations that agents can discover and use."
            )

        has_agent_templates = any("agent_template" in d for d in matched_dirs)
        if not has_agent_templates and not self._should_skip(config, "templates"):
            recs.append(
                "📋 Add agent_templates/: Create reusable agent configuration templates. "
                "Document patterns for common agent types (reviewer, implementer, tester, etc.)."
            )

        # Always show celebratory/guidance recommendations
        recs.append(
            "🎓 Share your learnings: Write blog posts, create templates, or contribute patterns "
            "back to the community. Your setup can help others level up their AI proficiency."
        )

        has_metrics = any("METRICS" in f or "PERFORMANCE" in f for f in matched_files)
        if not has_metrics:
            recs.append(
                "📈 Track metrics: Monitor AI-assisted productivity gains, code quality improvements, "
                "and developer satisfaction. Quantify your success to justify investment."
            )

        recs.append(
            "🔬 Push boundaries: You're positioned to shape the future of AI-assisted development. "
            "Experiment with new patterns and share what works."
        )
        recs.append(
            "🤝 Mentor others: Help other teams in your organization adopt similar practices. "
            "Create internal documentation and training on context engineering."
        )

        # Community contribution
        recs.append(
            "🌐 Contribute to open source: Share your agent patterns, skills, or orchestration logic. "
            "Publish to GitHub, write about your learnings, or contribute to AI coding tool documentation."
        )

        return recs

    def _generate_recommendations(self, score: RepoScore) -> List[str]:
        """Generate actionable recommendations based on the score and detected tools."""

        tools = score.detected_tools if score.detected_tools else ["claude-code"]
        config = score.config

        # Dispatch to level-specific recommendation handlers
        handlers = {
            1: lambda: self._recommendations_level_1(score, tools),
            2: lambda: self._recommendations_level_2(score, tools, config),
            3: lambda: self._recommendations_level_3(score, tools, config),
            4: lambda: self._recommendations_level_4(score, tools, config),
            5: lambda: self._recommendations_level_5(score, tools, config),
            6: lambda: self._recommendations_level_6(score, tools, config),
            7: lambda: self._recommendations_level_7(score, tools, config),
            8: lambda: self._recommendations_level_8(score, tools, config),
        }

        handler = handlers.get(score.overall_level)
        if handler:
            return handler()
        return []


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
