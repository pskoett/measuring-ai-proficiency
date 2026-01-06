"""
Tests for reporter module.

Tests output formatting for terminal, JSON, markdown, and CSV reporters.
"""

import io
import json
import tempfile
from pathlib import Path

import pytest

from measure_ai_proficiency import RepoScanner
from measure_ai_proficiency.reporter import (
    get_reporter,
    TerminalReporter,
    JsonReporter,
    MarkdownReporter,
    CsvReporter,
    _format_tool_name,
)


class TestFormatToolName:
    """Tests for tool name formatting."""

    def test_github_copilot_capitalization(self):
        """GitHub Copilot should have capital H."""
        assert _format_tool_name("github-copilot") == "GitHub Copilot"

    def test_claude_code(self):
        """Claude Code should format correctly."""
        assert _format_tool_name("claude-code") == "Claude Code"

    def test_cursor(self):
        """Cursor should format correctly."""
        assert _format_tool_name("cursor") == "Cursor"

    def test_openai_codex(self):
        """OpenAI Codex should format correctly."""
        assert _format_tool_name("openai-codex") == "OpenAI Codex"

    def test_unknown_tool_fallback(self):
        """Unknown tools should use title() fallback."""
        assert _format_tool_name("some-new-tool") == "Some New Tool"


class TestGetReporter:
    """Tests for get_reporter factory function."""

    def test_terminal_reporter(self):
        """Should return TerminalReporter for 'terminal' format."""
        reporter = get_reporter("terminal")
        assert isinstance(reporter, TerminalReporter)

    def test_json_reporter(self):
        """Should return JsonReporter for 'json' format."""
        reporter = get_reporter("json")
        assert isinstance(reporter, JsonReporter)

    def test_markdown_reporter(self):
        """Should return MarkdownReporter for 'markdown' format."""
        reporter = get_reporter("markdown")
        assert isinstance(reporter, MarkdownReporter)

    def test_csv_reporter(self):
        """Should return CsvReporter for 'csv' format."""
        reporter = get_reporter("csv")
        assert isinstance(reporter, CsvReporter)

    def test_unknown_format_returns_terminal(self):
        """Unknown format should default to TerminalReporter."""
        reporter = get_reporter("unknown")
        assert isinstance(reporter, TerminalReporter)

    def test_verbose_flag_passed(self):
        """Verbose flag should be passed to reporter."""
        reporter = get_reporter("terminal", verbose=True)
        assert reporter.verbose is True


class TestTerminalReporter:
    """Tests for TerminalReporter output."""

    def test_report_single_outputs_to_stream(self):
        """report_single should write to the provided stream."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "README.md").write_text("# Test\n" + "x" * 200)

            scanner = RepoScanner(tmpdir)
            score = scanner.scan()

            reporter = TerminalReporter()
            output = io.StringIO()
            reporter.report_single(score, output)

            result = output.getvalue()
            assert "AI Proficiency Report" in result
            assert "Overall Level" in result

    def test_report_multiple_outputs_summary(self):
        """report_multiple should include summary for multiple repos."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "README.md").write_text("# Test\n" + "x" * 200)

            scanner = RepoScanner(tmpdir)
            scores = [scanner.scan(), scanner.scan()]

            reporter = TerminalReporter()
            output = io.StringIO()
            reporter.report_multiple(scores, output)

            result = output.getvalue()
            assert "Summary" in result or "repos" in result.lower()


class TestJsonReporter:
    """Tests for JsonReporter output."""

    def test_outputs_valid_json(self):
        """Output should be valid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "README.md").write_text("# Test\n" + "x" * 200)

            scanner = RepoScanner(tmpdir)
            score = scanner.scan()

            reporter = JsonReporter()
            output = io.StringIO()
            reporter.report_single(score, output)

            result = output.getvalue()
            data = json.loads(result)  # Should not raise

            assert "overall_level" in data
            assert "overall_score" in data
            assert "repo_name" in data

    def test_includes_level_scores(self):
        """JSON output should include level_scores."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "README.md").write_text("# Test\n" + "x" * 200)

            scanner = RepoScanner(tmpdir)
            score = scanner.scan()

            reporter = JsonReporter()
            output = io.StringIO()
            reporter.report_single(score, output)

            data = json.loads(output.getvalue())
            assert "level_scores" in data

    def test_multiple_repos_outputs_object_with_repos(self):
        """Multiple repos should output a JSON object with repos array."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "README.md").write_text("# Test\n" + "x" * 200)

            scanner = RepoScanner(tmpdir)
            scores = [scanner.scan(), scanner.scan()]

            reporter = JsonReporter()
            output = io.StringIO()
            reporter.report_multiple(scores, output)

            data = json.loads(output.getvalue())
            assert isinstance(data, dict)
            assert "repos" in data
            assert len(data["repos"]) == 2


class TestMarkdownReporter:
    """Tests for MarkdownReporter output."""

    def test_outputs_markdown_headers(self):
        """Output should contain markdown headers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "README.md").write_text("# Test\n" + "x" * 200)

            scanner = RepoScanner(tmpdir)
            score = scanner.scan()

            reporter = MarkdownReporter()
            output = io.StringIO()
            reporter.report_single(score, output)

            result = output.getvalue()
            assert "# AI Proficiency Report" in result or "## " in result

    def test_includes_level_breakdown(self):
        """Markdown should include level breakdown."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "README.md").write_text("# Test\n" + "x" * 200)

            scanner = RepoScanner(tmpdir)
            score = scanner.scan()

            reporter = MarkdownReporter()
            output = io.StringIO()
            reporter.report_single(score, output)

            result = output.getvalue()
            assert "Level" in result


class TestCsvReporter:
    """Tests for CsvReporter output."""

    def test_outputs_csv_header(self):
        """Output should start with CSV header."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "README.md").write_text("# Test\n" + "x" * 200)

            scanner = RepoScanner(tmpdir)
            score = scanner.scan()

            reporter = CsvReporter()
            output = io.StringIO()
            # CsvReporter only has report_multiple, use single-item list
            reporter.report_multiple([score], output)

            result = output.getvalue()
            lines = result.strip().split("\n")
            assert len(lines) >= 2  # Header + data
            assert "repo_name" in lines[0].lower() or "Repository" in lines[0]

    def test_multiple_repos_adds_rows(self):
        """Multiple repos should add data rows."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "README.md").write_text("# Test\n" + "x" * 200)

            scanner = RepoScanner(tmpdir)
            scores = [scanner.scan(), scanner.scan()]

            reporter = CsvReporter()
            output = io.StringIO()
            reporter.report_multiple(scores, output)

            result = output.getvalue()
            lines = result.strip().split("\n")
            assert len(lines) >= 3  # Header + 2 data rows
