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
from measure_ai_proficiency.scanner import LevelScore
from measure_ai_proficiency.signals import SIGNAL_GROUPS, LEVEL_GATE_REQUIREMENTS


def _make_rich_signal_repo(root: Path) -> None:
    """Create a repo fixture exercising the 2026 signal + structural detectors."""
    (root / "CLAUDE.md").write_text(
        "# Project\n## Architecture\n"
        "We practice verification with adversarial review and clean-context verifiers.\n"
        "Run telemetry and observability scorecards. Audit CLAUDE.md for drift (sentinel canary).\n"
        "Dynamic workflows orchestrate parallel subagents. Progressive disclosure for skills.\n"
        "See the Anthropic Academy and the Google 5-day AI Agents course.\n"
        "Choose the cheapest primitive first; skill vs subagent decisions matter.\n"
        "This is harness engineering: the machine around the model, with a feedback loop.\n"
        + "x" * 200
    )
    skill_dir = root / ".claude" / "skills" / "foo"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: foo\ndescription: when to do foo\n---\n# Foo\nVerify and assert outputs.\n"
    )
    (skill_dir / "run.py").write_text("print('hi')\n")  # executable content
    agents_dir = root / ".claude" / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "reviewer.md").write_text("# reviewer\n")
    (agents_dir / "planner.md").write_text("# planner\n")
    hooks_dir = root / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True)
    (hooks_dir / "format.sh").write_text("echo hi\n")
    (root / ".claude" / "settings.json").write_text('{"hooks": {"PreToolUse": []}}\n')
    wf_dir = root / ".claude" / "workflows"
    wf_dir.mkdir(parents=True)
    (wf_dir / "migrate.md").write_text("# migration workflow\n")
    plugin_dir = root / ".claude-plugin"
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "plugin.json").write_text('{"name": "x"}\n')
    evals_dir = root / ".evals" / "cases"
    evals_dir.mkdir(parents=True)
    (evals_dir / "EVAL-001.md").write_text("---\neval-id: EVAL-001\n---\n# case\n")


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


class TestSignals:
    """Tests for 2026 context-engineering signal detection."""

    def test_signals_present_on_scan(self):
        """Every scan should attach a HarnessSignals object with gate keys 6-8."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "CLAUDE.md").write_text("# Project\n" + "x" * 200)
            score = RepoScanner(tmpdir).scan()
            assert score.signals is not None
            assert set(score.signals.gates.keys()) == {6, 7, 8}
            assert 0.0 <= score.signals.bonus_points <= 10.0

    def test_rich_repo_matches_all_signal_groups(self):
        """A rich fixture should match every registered signal group."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _make_rich_signal_repo(Path(tmpdir))
            score = RepoScanner(tmpdir).scan()
            matched = set(score.signals.matched_keys)
            expected = {g.key for g in SIGNAL_GROUPS}
            assert expected.issubset(matched), f"missing: {expected - matched}"

    def test_structural_quality_detection(self):
        """Structural detection should find frontmatter, executable content, hooks, etc."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _make_rich_signal_repo(Path(tmpdir))
            sq = RepoScanner(tmpdir).scan().signals.structural
            assert sq.skills_count >= 1
            assert sq.skills_with_frontmatter >= 1
            assert sq.skills_with_executable_content >= 1
            assert sq.skills_with_verification >= 1
            assert sq.hooks_present is True
            assert "PreToolUse" in sq.hook_events
            assert sq.subagents_count >= 2
            assert sq.workflows_present is True
            assert sq.plugins_present is True
            assert sq.skills_structured is True
            assert 0.0 <= sq.structural_score <= 10.0

    def test_verification_signal_keyword(self):
        """Verification keywords in CLAUDE.md should set the verification signal."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "CLAUDE.md").write_text(
                "# Project\nAlways verify with adversarial refutation and asserts.\n" + "x" * 200
            )
            score = RepoScanner(tmpdir).scan()
            assert score.signals.hits["verification"].matched is True

    def test_no_false_positive_signals_on_bare_repo(self):
        """A bare CLAUDE.md should not trip orchestration/plugin/maintenance signals."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "CLAUDE.md").write_text("# Project\nA simple project.\n" + "x" * 100)
            score = RepoScanner(tmpdir).scan()
            assert score.signals.hits["dynamic_workflows"].matched is False
            assert score.signals.hits["plugins"].matched is False
            assert score.signals.hits["maintenance_hygiene"].matched is False

    def test_signal_bonus_adds_to_score(self):
        """Signal bonus should be reflected in overall_score (vs a bare repo)."""
        with tempfile.TemporaryDirectory() as bare, tempfile.TemporaryDirectory() as rich:
            Path(bare, "CLAUDE.md").write_text("# Project\n" + "x" * 200)
            bare_score = RepoScanner(bare).scan()
            _make_rich_signal_repo(Path(rich))
            rich_score = RepoScanner(rich).scan()
            assert rich_score.signals.bonus_points > bare_score.signals.bonus_points


class TestLevelGating:
    """Tests for the L6-L8 signal-gate rewire."""

    def _full_coverage_levels(self):
        """Synthetic level scores with high coverage for levels 3-8."""
        scores = {}
        for level in range(1, 9):
            scores[level] = LevelScore(
                level=level,
                name=f"Level {level}",
                description="",
                total_patterns=10,
                coverage_percent=50.0,
            )
        return scores

    def test_gate_caps_level_when_signal_missing(self):
        """A failing L6 gate must cap the achieved level at 5 despite full coverage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = RepoScanner(tmpdir)
            level_scores = self._full_coverage_levels()
            gates = {6: False, 7: False, 8: False}
            capped = scanner._calc_level_with_thresholds(
                level_scores, scanner.DEFAULT_THRESHOLDS, gates
            )
            assert capped == 5

    def test_no_gates_reaches_level_8(self):
        """Without gates (backward compatible), full coverage reaches level 8."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = RepoScanner(tmpdir)
            level_scores = self._full_coverage_levels()
            assert scanner._calc_level_with_thresholds(
                level_scores, scanner.DEFAULT_THRESHOLDS, None
            ) == 8

    def test_l6_gate_passes_l7_blocks(self):
        """If L6 gate passes but L7 fails, level caps at 6."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = RepoScanner(tmpdir)
            level_scores = self._full_coverage_levels()
            gates = {6: True, 7: False, 8: False}
            assert scanner._calc_level_with_thresholds(
                level_scores, scanner.DEFAULT_THRESHOLDS, gates
            ) == 6

    def test_compute_gates_reports_missing_requirements(self):
        """A bare repo should report all L6 requirements as missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "CLAUDE.md").write_text("# Project\n" + "x" * 200)
            score = RepoScanner(tmpdir).scan()
            missing_6 = set(score.signals.gate_missing[6])
            assert set(LEVEL_GATE_REQUIREMENTS[6]).issubset(missing_6)
            assert score.signals.gates[6] is False

    def test_rich_repo_satisfies_l6_and_l7_gates(self):
        """The rich fixture should satisfy the L6 and L7 signal gates."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _make_rich_signal_repo(Path(tmpdir))
            score = RepoScanner(tmpdir).scan()
            assert score.signals.gates[6] is True
            assert score.signals.gates[7] is True
            # L8 needs measured outcomes (metrics/logs), absent in the fixture
            assert score.signals.gates[8] is False
            assert "measured_outcomes" in score.signals.gate_missing[8]


class TestConciseness:
    """Tests for conciseness / context-hygiene (anti-bloat) detection."""

    def test_bloated_always_on_file_flagged(self):
        """A very large CLAUDE.md should be flagged as bloated with a penalty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "CLAUDE.md").write_text("# Project\n" + ("word " * 3500))
            score = RepoScanner(tmpdir).scan()
            c = score.validation.conciseness["CLAUDE.md"]
            assert c.is_always_on is True
            assert c.is_bloated is True
            assert score.validation.has_bloat is True
            assert any(w.startswith("BLOAT:") for w in score.validation.warnings)
            assert score.validation.validation_penalty > 0

    def test_concise_always_on_file_not_flagged(self):
        """A concise CLAUDE.md should not be flagged as bloated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "CLAUDE.md").write_text("# Project\n" + ("word " * 120))
            score = RepoScanner(tmpdir).scan()
            c = score.validation.conciseness["CLAUDE.md"]
            assert c.is_always_on is True
            assert c.is_bloated is False
            assert score.validation.has_bloat is False

    def test_large_skill_exempt_from_bloat(self):
        """On-demand skill bodies are exempt from the bloat threshold (progressive disclosure)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "CLAUDE.md").write_text("# Project\n" + "x" * 200)
            skill = Path(tmpdir, ".claude", "skills", "foo")
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: foo\ndescription: d\n---\n" + ("word " * 4000)
            )
            score = RepoScanner(tmpdir).scan()
            rel = ".claude/skills/foo/SKILL.md"
            assert rel in score.validation.conciseness
            assert score.validation.conciseness[rel].is_always_on is False
            assert score.validation.conciseness[rel].is_bloated is False

    def test_bloat_threshold_configurable(self):
        """The bloat threshold default is 1500 words."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "CLAUDE.md").write_text("# Project\n" + ("word " * 300))
            score = RepoScanner(tmpdir).scan()
            assert score.validation.conciseness["CLAUDE.md"].threshold == 1500

    def test_bloat_emits_actionable_recommendation(self):
        """A bloated file should produce an anti-bloat recommendation with the audit rule."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "CLAUDE.md").write_text("# Project\n" + ("word " * 3500))
            score = RepoScanner(tmpdir).scan()
            joined = " ".join(score.recommendations)
            assert "always-loaded line must change behavior" in joined
            assert "AGENTS_FILE_GUIDANCE.md" in joined
