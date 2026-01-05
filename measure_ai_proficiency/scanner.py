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
        level_2 = score.level_scores.get(2)
        level_3 = score.level_scores.get(3)

        if score.overall_level == 0:
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

        if score.overall_level == 1:
            # Priority recommendations for reaching Level 2
            missing_critical = []
            
            if not any("ARCHITECTURE" in f.path.upper() for f in level_2.matched_files):
                missing_critical.append("ARCHITECTURE.md")
            if not any("API" in f.path.upper() for f in level_2.matched_files):
                missing_critical.append("API.md")
            if not any(any(term in f.path.upper() for term in ["CONVENTIONS", "STYLE", "STANDARDS"]) 
                      for f in level_2.matched_files):
                missing_critical.append("CONVENTIONS.md")
            if not any("TESTING" in f.path.upper() for f in level_2.matched_files):
                missing_critical.append("TESTING.md")
            
            if missing_critical:
                recommendations.append(
                    f"📚 PRIORITY: Add comprehensive documentation - you're missing {', '.join(missing_critical)}. "
                    f"These files provide essential context for AI tools to understand your codebase deeply."
                )
            
            # Add top 3-5 most impactful recommendations
            priority_recs = []
            
            if not any("ARCHITECTURE" in f.path.upper() for f in level_2.matched_files):
                priority_recs.append((
                    "🏗️ Create docs/ARCHITECTURE.md: Document your system design, component relationships, "
                    "data flow, and key architectural decisions. Include diagrams if possible. "
                    "This helps AI understand the big picture when making suggestions.", 1
                ))
            
            if not any(any(term in f.path.upper() for term in ["CONVENTIONS", "STYLE", "STANDARDS"]) 
                      for f in level_2.matched_files):
                priority_recs.append((
                    "📏 Create CONVENTIONS.md: Document your team's coding standards, naming conventions, "
                    "file organization, import patterns, error handling, and testing requirements. "
                    "This ensures AI-generated code matches your team's style.", 2
                ))
            
            if not any("PATTERNS" in f.path.upper() for f in level_2.matched_files):
                priority_recs.append((
                    "🎨 Add PATTERNS.md: Document common design patterns used in your codebase. "
                    "Include examples of: state management, error handling, API interactions, "
                    "data transformations, and component composition. AI will follow these patterns.", 3
                ))
            
            if not any("API" in f.path.upper() for f in level_2.matched_files):
                priority_recs.append((
                    "🔌 Document your APIs: Create docs/API.md describing endpoints, request/response formats, "
                    "authentication, rate limiting, and error codes. Helps AI generate correct API calls.", 4
                ))
            
            if not any("TESTING" in f.path.upper() for f in level_2.matched_files):
                priority_recs.append((
                    "🧪 Add TESTING.md: Document your testing strategy, how to run tests, "
                    "coverage requirements, and common testing patterns. AI can then generate proper tests.", 5
                ))
            
            # Sort by priority and add top recommendations
            priority_recs.sort(key=lambda x: x[1])
            for rec, _ in priority_recs[:5]:  # Limit to top 5
                recommendations.append(rec)
            
            # Additional helpful docs (lower priority)
            if len(recommendations) < 7:  # Don't overwhelm with too many
                if not any("CONTRIBUTING" in f.path.upper() for f in level_2.matched_files):
                    recommendations.append(
                        "👥 Add CONTRIBUTING.md: Define workflow for PRs, commit conventions, "
                        "code review guidelines, and development setup. Helps AI understand your process."
                    )
            
            if len(recommendations) < 8:
                recommendations.append(
                    "📂 Organization tip: Consider grouping docs in a /docs folder with subdirectories "
                    "for architecture, api, guides, and runbooks. Makes context easier to find."
                )

        if score.overall_level == 2:
            # Recommendations for reaching Level 3
            recommendations.append(
                "⚡ LEVEL UP: You have comprehensive documentation. Now add automation and workflows "
                "to make AI even more productive with skills, hooks, and custom commands."
            )
            
            if not any(".claude/skills" in d for d in level_3.matched_directories):
                recommendations.append(
                    "🛠️ Create .claude/skills/: Add custom skills for common tasks. Each skill should have "
                    "a SKILL.md describing its purpose, inputs, outputs, and usage. Examples: "
                    "create-component, run-tests, deploy-staging, generate-api-client."
                )
            
            if not any(".claude/agents" in d for d in level_3.matched_directories):
                recommendations.append(
                    "🤖 Add .claude/agents/: Create specialized agent personas (e.g., test-expert.md, "
                    "security-reviewer.md, api-designer.md) with specific expertise and responsibilities. "
                    "Each agent gets different context and instructions."
                )
            
            if not any(".claude/hooks" in d for d in level_3.matched_directories):
                recommendations.append(
                    "🪝 Set up .claude/hooks/: Add PostToolUse hooks for automatic actions like "
                    "formatting code, running linters, updating tests, or validating against conventions. "
                    "This ensures AI-generated code is always production-ready."
                )
            
            if not any(".claude/commands" in d for d in level_3.matched_directories):
                recommendations.append(
                    "⌨️ Add .claude/commands/: Create custom slash commands for frequent tasks. "
                    "Examples: /new-feature, /add-test, /refactor-component, /update-docs. "
                    "Makes complex workflows one-command simple."
                )
            
            if not any(any(term in f.path.upper() for term in ["MEMORY", "LEARNINGS", "DECISIONS"]) 
                      for f in level_3.matched_files):
                recommendations.append(
                    "💾 Add MEMORY.md or LEARNINGS.md: Document lessons learned, past decisions, "
                    "failed approaches, and architectural evolution. Helps AI avoid repeating mistakes "
                    "and understand historical context."
                )
            
            if not any("WORKFLOW" in f.path.upper() for f in level_3.matched_files):
                recommendations.append(
                    "🔄 Create WORKFLOWS.md: Document your team's common development workflows "
                    "step-by-step (e.g., feature development, bug fixes, deployments). "
                    "AI can guide through these processes."
                )
            
            # Check for scripts
            has_scripts = any("scripts/" in f.path for f in level_3.matched_files)
            if not has_scripts:
                recommendations.append(
                    "📜 Add scripts/ directory: Include setup, testing, deployment, and maintenance scripts. "
                    "Document each script in a scripts/README.md so AI knows when and how to use them."
                )

        if score.overall_level == 3:
            # Recommendations for reaching Level 4
            recommendations.append(
                "🚀 ADVANCED: You have mature context engineering. Consider multi-agent orchestration "
                "for complex workflows requiring specialized expertise and collaboration."
            )
            
            recommendations.append(
                "🤝 Create agents/HANDOFFS.md: Document when and how specialized agents should "
                "hand off work to each other. Define triggers, context passing, and success criteria."
            )
            
            recommendations.append(
                "🎭 Add .github/agents/: Create specialized agents for code review (reviewer.agent.md), "
                "testing (tester.agent.md), security analysis (security.agent.md), and documentation "
                "(documenter.agent.md). Each with specific expertise and evaluation criteria."
            )
            
            recommendations.append(
                "🧩 Set up agents/ORCHESTRATION.md: Define workflows that require multiple agents "
                "working together (e.g., feature-development.yaml, incident-response.yaml, "
                "refactoring-workflow.yaml)."
            )
            
            recommendations.append(
                "📊 Add SHARED_CONTEXT.md: Document context that all agents should have access to - "
                "critical system constraints, business rules, compliance requirements, and team values."
            )
            
            recommendations.append(
                "🔗 Consider MCP (Model Context Protocol) servers: Set up .mcp/servers/ for "
                "integrations with external tools, databases, APIs, and services that agents need."
            )
            
            recommendations.append(
                "💡 Explore orchestration tools: Look into Gas Town, LangChain, or custom workflows "
                "for managing multi-agent collaboration and complex development pipelines."
            )

        if score.overall_level == 4:
            recommendations.append(
                "🌟 EXCEPTIONAL: You're at the frontier of AI-assisted development! "
                "Your context engineering is world-class."
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
                "🔬 Experiment with cutting edge: Try proposed APIs, new agent frameworks, "
                "and emerging patterns. You're positioned to shape the future of AI-assisted development."
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
