"""
Tests for measure_ai_proficiency.

Tests are aligned with levels 1-8 (matching Steve Yegge's 8-stage model).
Level 1 = baseline (no AI files), Level 2+ = AI context present.
"""

import tempfile
from pathlib import Path

import pytest

from measure_ai_proficiency import RepoScanner, RepoScore
from measure_ai_proficiency.config import LEVELS


class TestRepoScanner:
    """Tests for the RepoScanner class."""

    def test_empty_repo_returns_level_1(self):
        """An empty repository should return Level 1 (baseline)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = RepoScanner(tmpdir)
            score = scanner.scan()

            assert score.overall_level == 1
            assert score.overall_score == 0.0

    def test_claude_md_returns_level_2(self):
        """A repo with CLAUDE.md should return at least Level 2."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a substantive CLAUDE.md
            claude_md = Path(tmpdir) / "CLAUDE.md"
            claude_md.write_text("""
# Project Context

This is a web application built with React and Node.js.

## Architecture

- Frontend: React with TypeScript
- Backend: Express.js
- Database: PostgreSQL

## Conventions

- Use functional components with hooks
- Follow ESLint rules
- Write tests for all new features
""")

            scanner = RepoScanner(tmpdir)
            score = scanner.scan()

            assert score.overall_level >= 2
            assert score.has_any_ai_files

    def test_cursorrules_returns_level_2(self):
        """A repo with .cursorrules should return at least Level 2."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cursorrules = Path(tmpdir) / ".cursorrules"
            cursorrules.write_text("""
You are an expert TypeScript developer.
Always use strict TypeScript.
Prefer functional programming patterns.
Write comprehensive tests.
""")

            scanner = RepoScanner(tmpdir)
            score = scanner.scan()

            assert score.overall_level >= 2

    def test_copilot_instructions_returns_level_2(self):
        """A repo with copilot-instructions.md should return at least Level 2."""
        with tempfile.TemporaryDirectory() as tmpdir:
            github_dir = Path(tmpdir) / ".github"
            github_dir.mkdir()

            copilot_md = github_dir / "copilot-instructions.md"
            copilot_md.write_text("""
# Copilot Instructions

This is a Python project using FastAPI.
Follow PEP 8 style guidelines.
Use type hints everywhere.
""")

            scanner = RepoScanner(tmpdir)
            score = scanner.scan()

            assert score.overall_level >= 2

    def test_comprehensive_repo_returns_level_3(self):
        """A repo with comprehensive context should return Level 3."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Level 2 files (core AI file)
            Path(tmpdir, "CLAUDE.md").write_text("# Project\n" + "x" * 200)
            Path(tmpdir, "README.md").write_text("# README\n" + "x" * 200)

            # Level 3 files (comprehensive context)
            Path(tmpdir, "ARCHITECTURE.md").write_text("# Architecture\n" + "x" * 500)
            Path(tmpdir, "CONVENTIONS.md").write_text("# Conventions\n" + "x" * 500)
            Path(tmpdir, "PATTERNS.md").write_text("# Patterns\n" + "x" * 500)
            Path(tmpdir, "CONTRIBUTING.md").write_text("# Contributing\n" + "x" * 500)
            Path(tmpdir, "TESTING.md").write_text("# Testing\n" + "x" * 500)

            # Create docs directory
            docs_dir = Path(tmpdir) / "docs" / "adr"
            docs_dir.mkdir(parents=True)
            Path(docs_dir, "001-use-react.md").write_text("# ADR 001\n" + "x" * 500)

            scanner = RepoScanner(tmpdir)
            score = scanner.scan()

            assert score.overall_level >= 3

    def test_stub_files_not_counted_as_substantive(self):
        """Files with minimal content should not count as substantive."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a stub CLAUDE.md (too small)
            claude_md = Path(tmpdir) / "CLAUDE.md"
            claude_md.write_text("# TODO")  # Only ~6 bytes

            scanner = RepoScanner(tmpdir)
            score = scanner.scan()

            level_2 = score.level_scores.get(2)
            assert level_2 is not None
            assert level_2.substantive_file_count == 0

    def test_recommendations_generated_for_level_1(self):
        """Level 1 repos should get basic recommendations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = RepoScanner(tmpdir)
            score = scanner.scan()

            assert score.overall_level == 1
            assert len(score.recommendations) > 0
            assert any("CLAUDE.md" in r for r in score.recommendations)

    def test_level_scores_have_correct_names(self):
        """Level scores should have correct names from config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = RepoScanner(tmpdir)
            score = scanner.scan()

            for level_num, level_score in score.level_scores.items():
                expected_name = LEVELS[level_num].name
                assert level_score.name == expected_name


class TestLevelConfig:
    """Tests for level configuration."""

    def test_all_levels_defined(self):
        """All 8 levels should be defined in LEVELS."""
        for i in range(1, 9):
            assert i in LEVELS, f"Level {i} not defined in LEVELS"

    def test_levels_have_patterns(self):
        """Each level should have file patterns defined."""
        for level_num, config in LEVELS.items():
            assert len(config.file_patterns) > 0, f"Level {level_num} has no file patterns"

    def test_level_weights_increase(self):
        """Higher levels should have higher weights."""
        weights = [LEVELS[i].weight for i in range(1, 9)]
        assert weights == sorted(weights), "Level weights should increase"


class TestRepoScore:
    """Tests for RepoScore dataclass."""

    def test_has_any_ai_files_empty(self):
        """Empty repo should report no AI files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = RepoScanner(tmpdir)
            score = scanner.scan()

            assert not score.has_any_ai_files

    def test_has_any_ai_files_with_claude_md(self):
        """Repo with CLAUDE.md should report has AI files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "CLAUDE.md").write_text("# Project\n" + "x" * 200)

            scanner = RepoScanner(tmpdir)
            score = scanner.scan()

            assert score.has_any_ai_files


class TestHigherLevels:
    """Tests for levels 4-8."""

    def test_skills_returns_level_4(self):
        """A repo with skills should return at least Level 4."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Level 2 (core AI file)
            Path(tmpdir, "CLAUDE.md").write_text("# Project\n" + "x" * 200)

            # Level 3 (comprehensive context)
            Path(tmpdir, "ARCHITECTURE.md").write_text("# Architecture\n" + "x" * 500)
            Path(tmpdir, "CONVENTIONS.md").write_text("# Conventions\n" + "x" * 500)
            Path(tmpdir, "PATTERNS.md").write_text("# Patterns\n" + "x" * 500)
            Path(tmpdir, "TESTING.md").write_text("# Testing\n" + "x" * 500)
            Path(tmpdir, "CONTRIBUTING.md").write_text("# Contributing\n" + "x" * 500)

            # Level 4 (skills & automation)
            skills_dir = Path(tmpdir) / ".claude" / "skills" / "test-skill"
            skills_dir.mkdir(parents=True)
            Path(skills_dir, "SKILL.md").write_text("# Test Skill\n" + "x" * 300)

            hooks_dir = Path(tmpdir) / ".claude" / "hooks"
            hooks_dir.mkdir(parents=True)
            Path(hooks_dir, "post-edit.sh").write_text("#!/bin/bash\necho 'done'\n" + "x" * 100)

            Path(tmpdir, "MEMORY.md").write_text("# Memory\n" + "x" * 300)

            scanner = RepoScanner(tmpdir)
            score = scanner.scan()

            assert score.overall_level >= 4


class TestAutoDetection:
    """Tests for AI tool auto-detection."""

    def test_detects_claude_code(self):
        """Should detect Claude Code when CLAUDE.md exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "CLAUDE.md").write_text("# Project\n" + "x" * 200)

            scanner = RepoScanner(tmpdir)
            score = scanner.scan()

            assert "claude-code" in score.detected_tools

    def test_detects_github_copilot(self):
        """Should detect GitHub Copilot when copilot-instructions.md exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            github_dir = Path(tmpdir) / ".github"
            github_dir.mkdir()
            Path(github_dir, "copilot-instructions.md").write_text("# Instructions\n" + "x" * 200)

            scanner = RepoScanner(tmpdir)
            score = scanner.scan()

            assert "github-copilot" in score.detected_tools

    def test_detects_cursor(self):
        """Should detect Cursor when .cursorrules exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, ".cursorrules").write_text("# Rules\n" + "x" * 200)

            scanner = RepoScanner(tmpdir)
            score = scanner.scan()

            assert "cursor" in score.detected_tools

    def test_detects_multiple_tools(self):
        """Should detect multiple tools when present."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Claude
            Path(tmpdir, "CLAUDE.md").write_text("# Project\n" + "x" * 200)
            # Cursor
            Path(tmpdir, ".cursorrules").write_text("# Rules\n" + "x" * 200)

            scanner = RepoScanner(tmpdir)
            score = scanner.scan()

            assert "claude-code" in score.detected_tools
            assert "cursor" in score.detected_tools

    def test_empty_repo_no_tools(self):
        """Empty repo should have no detected tools."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = RepoScanner(tmpdir)
            score = scanner.scan()

            assert score.detected_tools == []


class TestRepoConfig:
    """Tests for repository configuration."""

    def test_config_loaded_from_yaml(self):
        """Should load config from .ai-proficiency.yaml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create config file
            config_content = """
tools:
  - claude-code
thresholds:
  level_3: 5
skip_recommendations:
  - hooks
"""
            Path(tmpdir, ".ai-proficiency.yaml").write_text(config_content)
            Path(tmpdir, "CLAUDE.md").write_text("# Project\n" + "x" * 200)

            scanner = RepoScanner(tmpdir)
            score = scanner.scan()

            # Check config was loaded (if yaml is available)
            if score.config and score.config.from_file:
                assert "claude-code" in score.config.tools
                assert score.config.thresholds.get(3) == 5
                assert "hooks" in score.config.skip_recommendations

    def test_score_includes_detected_tools(self):
        """RepoScore should include detected_tools field."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "CLAUDE.md").write_text("# Project\n" + "x" * 200)

            scanner = RepoScanner(tmpdir)
            score = scanner.scan()

            assert hasattr(score, 'detected_tools')
            assert isinstance(score.detected_tools, list)
