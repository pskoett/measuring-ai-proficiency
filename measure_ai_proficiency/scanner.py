"""
Repository scanner for AI proficiency measurement.

Scans repositories for context engineering artifacts and calculates maturity scores.
"""

import fnmatch
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

from .config import LEVELS, CORE_AI_FILES, LevelConfig


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
    overall_level: int = 0
    overall_score: float = 0.0
    recommendations: List[str] = field(default_factory=list)

    @property
    def has_any_ai_files(self) -> bool:
        """Check if repo has any AI-specific files."""

        return any(ls.file_count > 0 for ls in self.level_scores.values())


class RepoScanner:
    """Scans a repository for context engineering artifacts."""

    def __init__(self, repo_path: str, verbose: bool = False):
        self.repo_path = Path(repo_path).resolve()
        self.verbose = verbose
        self._dir_cache: Dict[str, bool] = {}

    def scan(self) -> RepoScore:
        """Scan the repository and return a complete score."""

        scan_time = datetime.now()

        # Initialize score
        score = RepoScore(
            repo_path=str(self.repo_path),
            repo_name=self.repo_path.name,
            scan_time=scan_time,
        )

        # Scan each level
        for level_num, level_config in LEVELS.items():
            level_score = self._scan_level(level_num, level_config)
            score.level_scores[level_num] = level_score

        # Calculate overall level and score
        score.overall_level = self._calculate_overall_level(score.level_scores)
        score.overall_score = self._calculate_overall_score(score.level_scores)

        # Generate recommendations
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

        if not base_dir.exists():
            return matches

        try:
            for item in base_dir.rglob("*"):
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

    def _calculate_overall_level(self, level_scores: Dict[int, LevelScore]) -> int:
        """
        Calculate the overall maturity level.

        A level is achieved if:
        - Level 1: At least one core AI file exists with substantive content
        - Level 2: Level 1 achieved + significant Level 2 coverage (>20%)
        - Level 3: Level 2 achieved + significant Level 3 coverage (>15%)
        - Level 4: Level 3 achieved + significant Level 4 coverage (>10%)
        """

        level_1 = level_scores.get(1)
        if not level_1 or level_1.substantive_file_count == 0:
            return 0

        # Check for core AI files
        has_core_file = any(
            any(core in f.path for core in CORE_AI_FILES) for f in level_1.matched_files
        )
        if not has_core_file:
            return 0

        current_level = 1

        # Check Level 2 (need >20% coverage)
        level_2 = level_scores.get(2)
        if level_2 and level_2.coverage_percent >= 20:
            current_level = 2
        else:
            return current_level

        # Check Level 3 (need >15% coverage)
        level_3 = level_scores.get(3)
        if level_3 and level_3.coverage_percent >= 15:
            current_level = 3
        else:
            return current_level

        # Check Level 4 (need >10% coverage)
        level_4 = level_scores.get(4)
        if level_4 and level_4.coverage_percent >= 10:
            current_level = 4

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

                level_contribution = coverage_score * substantive_ratio * weight * 25
                total_score += level_contribution

            max_possible += weight * 25

        if max_possible > 0:
            return min(100, (total_score / max_possible) * 100)
        return 0.0

    def _generate_recommendations(self, score: RepoScore) -> List[str]:
        """Generate actionable recommendations based on the score."""

        recommendations: List[str] = []

        if score.overall_level == 0:
            recommendations.append(
                "Start with a CLAUDE.md or .cursorrules file describing your project's "
                "architecture, conventions, and key abstractions."
            )
            recommendations.append(
                "Add a .github/copilot-instructions.md for GitHub Copilot users."
            )
            return recommendations

        if score.overall_level == 1:
            level_2 = score.level_scores.get(2)
            if level_2:
                if not any("ARCHITECTURE" in f.path for f in level_2.matched_files):
                    recommendations.append(
                        "Add an ARCHITECTURE.md documenting your system design."
                    )
                if not any(
                    "CONVENTIONS" in f.path or "STYLE" in f.path
                    for f in level_2.matched_files
                ):
                    recommendations.append(
                        "Add a CONVENTIONS.md or STYLE.md documenting coding standards."
                    )
                if not any("PATTERNS" in f.path for f in level_2.matched_files):
                    recommendations.append(
                        "Add a PATTERNS.md documenting common patterns in your codebase."
                    )

        if score.overall_level == 2:
            level_3 = score.level_scores.get(3)
            if level_3:
                if not any(".claude/hooks" in d for d in level_3.matched_directories):
                    recommendations.append(
                        "Add .claude/hooks/ with PostToolUse hooks for auto-formatting."
                    )
                if not any(
                    "MEMORY" in f.path or "LEARNINGS" in f.path
                    for f in level_3.matched_files
                ):
                    recommendations.append(
                        "Add MEMORY.md or LEARNINGS.md for persistent context."
                    )
                if not any(
                    ".claude/commands" in d for d in level_3.matched_directories
                ):
                    recommendations.append(
                        "Add custom slash commands in .claude/commands/."
                    )

        if score.overall_level == 3:
            recommendations.append(
                "Consider adding specialized agents in .github/agents/ for code review, "
                "testing, and documentation tasks."
            )
            recommendations.append(
                "Explore orchestration tools like Gas Town for managing multiple agents."
            )

        if score.overall_level == 4:
            recommendations.append(
                "You're at the frontier! Consider contributing your patterns back to "
                "the community."
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
