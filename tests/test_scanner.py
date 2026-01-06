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

    def test_comprehensive_repo_detects_level_3_files(self):
        """A repo with comprehensive context files should detect them at Level 3."""
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

            scanner = RepoScanner(tmpdir)
            score = scanner.scan()

            # Verify level 3 files are detected (coverage > 0)
            level_3 = score.level_scores.get(3)
            assert level_3 is not None
            assert level_3.coverage_percent > 0
            assert len(level_3.matched_files) >= 5  # At least 5 level 3 files

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

    def test_skills_detected_at_level_4(self):
        """A repo with skills should detect level 4 files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Level 2 (core AI file)
            Path(tmpdir, "CLAUDE.md").write_text("# Project\n" + "x" * 200)

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

            # Verify level 4 files are detected
            level_4 = score.level_scores.get(4)
            assert level_4 is not None
            assert level_4.coverage_percent > 0
            assert len(level_4.matched_files) >= 2  # SKILL.md and hook
            assert len(level_4.matched_directories) >= 1  # .claude/hooks or .claude/skills


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


class TestCrossReferences:
    """Tests for cross-reference detection and quality evaluation."""

    def test_detects_markdown_links(self):
        """Should detect markdown links like [text](file.md)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            claude_md = Path(tmpdir) / "CLAUDE.md"
            claude_md.write_text("""
# Project Context

See the [architecture docs](ARCHITECTURE.md) for system design.
Also check [conventions](./CONVENTIONS.md).
""")
            # Create the referenced file so it can be resolved
            Path(tmpdir, "ARCHITECTURE.md").write_text("# Architecture\n" + "x" * 200)

            scanner = RepoScanner(tmpdir)
            score = scanner.scan()

            assert score.cross_references is not None
            assert score.cross_references.total_count >= 2
            # At least one should be resolved (ARCHITECTURE.md exists)
            assert score.cross_references.resolved_count >= 1

    def test_detects_file_mentions(self):
        """Should detect file mentions in quotes like 'AGENTS.md'."""
        with tempfile.TemporaryDirectory() as tmpdir:
            claude_md = Path(tmpdir) / "CLAUDE.md"
            claude_md.write_text("""
# Project Context

This file works alongside `AGENTS.md` and "CONVENTIONS.md".
Read 'TESTING.md' for testing guidelines.
""")

            scanner = RepoScanner(tmpdir)
            score = scanner.scan()

            assert score.cross_references is not None
            assert score.cross_references.total_count >= 3

    def test_detects_directory_refs(self):
        """Should detect directory references like skills/ or .claude/commands/."""
        with tempfile.TemporaryDirectory() as tmpdir:
            claude_md = Path(tmpdir) / "CLAUDE.md"
            claude_md.write_text("""
# Project Context

Custom skills are in .claude/skills/ directory.
See docs/ for documentation.
""")
            # Create the skills directory
            skills_dir = Path(tmpdir) / ".claude" / "skills"
            skills_dir.mkdir(parents=True)

            scanner = RepoScanner(tmpdir)
            score = scanner.scan()

            assert score.cross_references is not None
            # Should have directory references
            dir_refs = [r for r in score.cross_references.references if r.reference_type == "directory_ref"]
            assert len(dir_refs) >= 1

    def test_ignores_external_urls(self):
        """Should not count external URLs as cross-references."""
        with tempfile.TemporaryDirectory() as tmpdir:
            claude_md = Path(tmpdir) / "CLAUDE.md"
            claude_md.write_text("""
# Project Context

See [docs](https://example.com/docs.md) for more info.
Also check http://example.com/file.yaml
""")

            scanner = RepoScanner(tmpdir)
            score = scanner.scan()

            assert score.cross_references is not None
            # Should have no references (external URLs should be ignored)
            assert score.cross_references.total_count == 0

    def test_resolution_tracking(self):
        """Should correctly track whether references resolve to existing files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            claude_md = Path(tmpdir) / "CLAUDE.md"
            claude_md.write_text("""
# Project Context

See [exists](README.md) and [missing](MISSING.md).
""")
            # Create README.md (exists)
            Path(tmpdir, "README.md").write_text("# README\n" + "x" * 200)
            # Don't create MISSING.md

            scanner = RepoScanner(tmpdir)
            score = scanner.scan()

            assert score.cross_references is not None
            # Check we have both resolved and unresolved references
            refs = score.cross_references.references
            resolved = [r for r in refs if r.is_resolved]
            unresolved = [r for r in refs if not r.is_resolved]
            assert len(resolved) >= 1
            assert len(unresolved) >= 1

    def test_quality_score_calculation(self):
        """Should calculate quality scores for instruction files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            claude_md = Path(tmpdir) / "CLAUDE.md"
            claude_md.write_text("""
# Project Context

## Architecture

This project uses React and TypeScript.

## Conventions

- Never use `any` type
- Always use functional components
- Run `npm test` before committing

## Paths

Files are in `/src/components/` and `~/config/`.

## Important

Never modify the database directly.
""")

            scanner = RepoScanner(tmpdir)
            score = scanner.scan()

            assert score.cross_references is not None
            assert "CLAUDE.md" in score.cross_references.quality_scores

            quality = score.cross_references.quality_scores["CLAUDE.md"]
            assert quality.has_sections  # Has ## headers
            assert quality.has_constraints  # Has "never"
            assert quality.has_tool_commands  # Has `npm test`
            assert quality.quality_score > 0

    def test_bonus_points_added(self):
        """Should add bonus points to overall score for cross-references."""
        with tempfile.TemporaryDirectory() as tmpdir:
            claude_md = Path(tmpdir) / "CLAUDE.md"
            claude_md.write_text("""
# Project Context

## Architecture

See [architecture](ARCHITECTURE.md) for details.
Also check [conventions](CONVENTIONS.md) and [testing](TESTING.md).

## Rules

- Never modify production directly
- Always run tests
- Use `npm run lint` before committing
""")
            # Create referenced files
            Path(tmpdir, "ARCHITECTURE.md").write_text("# Architecture\n" + "x" * 300)
            Path(tmpdir, "CONVENTIONS.md").write_text("# Conventions\n" + "x" * 300)
            Path(tmpdir, "TESTING.md").write_text("# Testing\n" + "x" * 300)

            scanner = RepoScanner(tmpdir)
            score = scanner.scan()

            assert score.cross_references is not None
            assert score.cross_references.bonus_points > 0
            # Bonus should be capped at 10
            assert score.cross_references.bonus_points <= 10

    def test_bonus_capped_at_10(self):
        """Bonus points should be capped at 10."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a very comprehensive CLAUDE.md with many cross-refs
            refs = "\n".join([f"See [file{i}](FILE{i}.md)" for i in range(20)])
            claude_md = Path(tmpdir) / "CLAUDE.md"
            claude_md.write_text(f"""
# Comprehensive Project

## Architecture

This is a large project with many references.

{refs}

## Rules

Never do X. Never do Y. Never do Z.
Always run `test`. Always run `lint`. Always run `build`.
Use `/path/to/file` and `~/config/file`.
""")
            # Create some referenced files
            for i in range(10):
                Path(tmpdir, f"FILE{i}.md").write_text(f"# File {i}\n" + "x" * 200)

            scanner = RepoScanner(tmpdir)
            score = scanner.scan()

            assert score.cross_references is not None
            assert score.cross_references.bonus_points <= 10

    def test_empty_repo_no_cross_refs(self):
        """Empty repo should have no cross-references but valid structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = RepoScanner(tmpdir)
            score = scanner.scan()

            assert score.cross_references is not None
            assert score.cross_references.total_count == 0
            assert score.cross_references.source_files_scanned == 0
            assert score.cross_references.bonus_points == 0
