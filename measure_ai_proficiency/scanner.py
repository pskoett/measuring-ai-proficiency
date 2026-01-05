"""
Repository scanner for AI proficiency measurement.

Scans repositories for context engineering artifacts and calculates maturity scores.
Uses levels 1-8 aligned with Steve Yegge's 8-stage AI coding proficiency model.
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
    overall_level: int = 1  # Default to Level 1 (baseline)
    overall_score: float = 0.0
    recommendations: List[str] = field(default_factory=list)

    @property
    def has_any_ai_files(self) -> bool:
        """Check if repo has any AI-specific files (Level 2+)."""

        # Check if any Level 2+ files exist
        for level_num, ls in self.level_scores.items():
            if level_num >= 2 and ls.file_count > 0:
                return True
        return False


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

        # Progressive threshold checks for levels 3-8
        thresholds = {
            3: 15,   # Comprehensive context
            4: 12,   # Skills & automation
            5: 10,   # Multi-agent ready
            6: 8,    # Fleet infrastructure
            7: 6,    # Agent fleet
            8: 5,    # Custom orchestration (frontier)
        }

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
        """Generate actionable recommendations based on the score."""

        recommendations: List[str] = []
        level_3 = score.level_scores.get(3)
        level_4 = score.level_scores.get(4)
        level_5 = score.level_scores.get(5)
        level_6 = score.level_scores.get(6)
        level_7 = score.level_scores.get(7)

        if score.overall_level == 1:
            # Level 1: Zero AI - need to start with basic AI files
            recommendations.append(
                "🚀 START HERE: Create a CLAUDE.md file in your repository root. "
                "Describe your project's purpose, architecture, key abstractions, and coding conventions. "
                "This is the #1 way to improve AI coding assistance."
            )
            recommendations.append(
                "📝 Add a .github/copilot-instructions.md for GitHub Copilot users. "
                "Include project-specific patterns, naming conventions, and common pitfalls."
            )
            recommendations.append(
                "🎯 For Cursor users: Create a .cursorrules file with your team's coding standards. "
                "This helps maintain consistency across AI-assisted coding sessions."
            )
            recommendations.append(
                "💡 Quick win: Ensure your README.md has clear sections on architecture, setup, and testing. "
                "This provides baseline context for all AI tools."
            )
            return recommendations

        if score.overall_level == 2:
            # Level 2: Basic Instructions - need comprehensive context
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

            if missing_critical:
                recommendations.append(
                    f"📚 PRIORITY: Add comprehensive documentation - you're missing {', '.join(missing_critical)}. "
                    f"These files provide essential context for AI tools to understand your codebase deeply."
                )

            priority_recs = []

            if not any("ARCHITECTURE" in f.path.upper() for f in level_3.matched_files):
                priority_recs.append((
                    "🏗️ Create docs/ARCHITECTURE.md: Document your system design, component relationships, "
                    "data flow, and key architectural decisions. Include diagrams if possible. "
                    "This helps AI understand the big picture when making suggestions.", 1
                ))

            if not any(any(term in f.path.upper() for term in ["CONVENTIONS", "STYLE", "STANDARDS"])
                      for f in level_3.matched_files):
                priority_recs.append((
                    "📏 Create CONVENTIONS.md: Document your team's coding standards, naming conventions, "
                    "file organization, import patterns, error handling, and testing requirements. "
                    "This ensures AI-generated code matches your team's style.", 2
                ))

            if not any("PATTERNS" in f.path.upper() for f in level_3.matched_files):
                priority_recs.append((
                    "🎨 Add PATTERNS.md: Document common design patterns used in your codebase. "
                    "Include examples of: state management, error handling, API interactions, "
                    "data transformations, and component composition. AI will follow these patterns.", 3
                ))

            if not any("API" in f.path.upper() for f in level_3.matched_files):
                priority_recs.append((
                    "🔌 Document your APIs: Create docs/API.md describing endpoints, request/response formats, "
                    "authentication, rate limiting, and error codes. Helps AI generate correct API calls.", 4
                ))

            if not any("TESTING" in f.path.upper() for f in level_3.matched_files):
                priority_recs.append((
                    "🧪 Add TESTING.md: Document your testing strategy, how to run tests, "
                    "coverage requirements, and common testing patterns. AI can then generate proper tests.", 5
                ))

            priority_recs.sort(key=lambda x: x[1])
            for rec, _ in priority_recs[:5]:
                recommendations.append(rec)

            if len(recommendations) < 7:
                if not any("CONTRIBUTING" in f.path.upper() for f in level_3.matched_files):
                    recommendations.append(
                        "👥 Add CONTRIBUTING.md: Define workflow for PRs, commit conventions, "
                        "code review guidelines, and development setup. Helps AI understand your process."
                    )

        if score.overall_level == 3:
            # Level 3: Comprehensive Context - need skills & automation
            recommendations.append(
                "⚡ LEVEL UP: You have comprehensive documentation. Now add automation and workflows "
                "to make AI even more productive with skills, hooks, and custom commands."
            )

            if not any(".claude/skills" in d for d in level_4.matched_directories):
                recommendations.append(
                    "🛠️ Create .claude/skills/: Add custom skills for common tasks. Each skill should have "
                    "a SKILL.md describing its purpose, inputs, outputs, and usage. Examples: "
                    "create-component, run-tests, deploy-staging, generate-api-client."
                )

            if not any(".claude/hooks" in d for d in level_4.matched_directories):
                recommendations.append(
                    "🪝 Set up .claude/hooks/: Add PostToolUse hooks for automatic actions like "
                    "formatting code, running linters, updating tests, or validating against conventions. "
                    "This ensures AI-generated code is always production-ready."
                )

            if not any(".claude/commands" in d for d in level_4.matched_directories):
                recommendations.append(
                    "⌨️ Add .claude/commands/: Create custom slash commands for frequent tasks. "
                    "Examples: /new-feature, /add-test, /refactor-component, /update-docs. "
                    "Makes complex workflows one-command simple."
                )

            if not any(any(term in f.path.upper() for term in ["MEMORY", "LEARNINGS", "DECISIONS"])
                      for f in level_4.matched_files):
                recommendations.append(
                    "💾 Add MEMORY.md or LEARNINGS.md: Document lessons learned, past decisions, "
                    "failed approaches, and architectural evolution. Helps AI avoid repeating mistakes "
                    "and understand historical context."
                )

        if score.overall_level == 4:
            # Level 4: Skills & Automation - need multi-agent setup
            recommendations.append(
                "🚀 ADVANCING: You have skills and automation. Now configure multiple specialized agents "
                "and MCP integrations for more sophisticated AI collaboration."
            )

            if not any(".github/agents" in d or ".claude/agents" in d for d in level_5.matched_directories):
                recommendations.append(
                    "🤖 Add .github/agents/: Create specialized agents for code review (reviewer.agent.md), "
                    "testing (tester.agent.md), security analysis (security.agent.md), and documentation "
                    "(documenter.agent.md). Each with specific expertise and evaluation criteria."
                )

            if not any(".mcp" in d for d in level_5.matched_directories):
                recommendations.append(
                    "🔗 Set up MCP servers: Create .mcp/servers/ for integrations with external tools, "
                    "databases, APIs, and services that agents need. This enables richer agent capabilities."
                )

            recommendations.append(
                "🤝 Create agents/HANDOFFS.md: Document when and how specialized agents should "
                "hand off work to each other. Define triggers, context passing, and success criteria."
            )

        if score.overall_level == 5:
            # Level 5: Multi-Agent Ready - need fleet infrastructure
            recommendations.append(
                "🎯 FLEET READY: You have multi-agent setup. Now add fleet infrastructure "
                "for managing parallel agent instances with shared memory and workflows."
            )

            if not any(".beads" in d or "beads" in d for d in level_6.matched_directories):
                recommendations.append(
                    "🧠 Set up Beads: Create .beads/ for persistent memory across agent sessions. "
                    "Beads provides external memory that survives session timeouts and enables "
                    "long-horizon work across multiple agent instances."
                )

            if not any("workflows" in d or "pipelines" in d for d in level_6.matched_directories):
                recommendations.append(
                    "🔄 Add workflows/: Create YAML workflow definitions for multi-step processes. "
                    "Examples: workflows/code_review.yaml, workflows/feature_development.yaml. "
                    "These coordinate agent activities across complex tasks."
                )

            if not any("SHARED_CONTEXT" in f.path.upper() for f in level_6.matched_files):
                recommendations.append(
                    "📊 Create SHARED_CONTEXT.md: Document context that all agents should have access to - "
                    "critical system constraints, business rules, compliance requirements, and team values."
                )

            recommendations.append(
                "📦 For monorepos: Add packages/*/CLAUDE.md for package-specific context. "
                "This helps agents understand boundaries and relationships between packages."
            )

        if score.overall_level == 6:
            # Level 6: Fleet Infrastructure - need agent fleet governance
            recommendations.append(
                "⚡ FLEET INFRASTRUCTURE: You have the basics. Now scale to a full agent fleet "
                "with governance, scheduling, and multi-agent pipelines."
            )

            if not any("GOVERNANCE" in f.path.upper() for f in level_7.matched_files):
                recommendations.append(
                    "📋 Create GOVERNANCE.md: Document agent permissions, boundaries, and policies. "
                    "Define what agents can and cannot do, approval requirements, and escalation paths."
                )

            if not any("SCHEDULING" in f.path.upper() or "PRIORITY" in f.path.upper() for f in level_7.matched_files):
                recommendations.append(
                    "📅 Add agents/SCHEDULING.md: Define how to prioritize and schedule agent work. "
                    "Include queue management, priority rules, and resource allocation strategies."
                )

            if not any("convoys" in d or "molecules" in d or "epics" in d for d in level_7.matched_directories):
                recommendations.append(
                    "🚛 Set up convoys/ or molecules/: Use Gas Town-style work decomposition. "
                    "Break large tasks into molecules (atomic units) and convoys (coordinated groups)."
                )

            recommendations.append(
                "📊 Add agents/METRICS.md: Track agent performance, success rates, and productivity. "
                "Use metrics to optimize your fleet configuration and identify bottlenecks."
            )

        if score.overall_level == 7:
            # Level 7: Agent Fleet - need custom orchestration
            recommendations.append(
                "🎖️ AGENT FLEET: You're managing a full fleet. Now consider custom orchestration "
                "for advanced coordination and meta-automation."
            )

            recommendations.append(
                "🏗️ Build orchestration/: Create custom orchestration logic for complex workflows. "
                "Define how agents coordinate, share state, and handle failures at scale."
            )

            recommendations.append(
                "🔧 Consider Gas Town: Set up .gastown/ configuration for Steve Yegge's "
                "multi-agent orchestrator. It provides Kubernetes-like agent management."
            )

            recommendations.append(
                "⚙️ Add meta/: Create meta-automation that generates automation. "
                "Templates and generators that create new agent configs, workflows, and skills."
            )

            recommendations.append(
                "🧪 Explore experimental/: Document frontier techniques you're exploring. "
                "New patterns, frameworks, and approaches for AI-assisted development."
            )

        if score.overall_level == 8:
            # Level 8: Custom Orchestration - frontier level
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
