"""
Tests for CLI entry point (__main__.py).

Tests argument parsing, exit codes, and output handling.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


class TestCLIBasic:
    """Tests for basic CLI functionality."""

    def test_help_flag(self):
        """--help should show usage and exit 0."""
        result = subprocess.run(
            [sys.executable, "-m", "measure_ai_proficiency", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "usage:" in result.stdout.lower()
        assert "measure-ai-proficiency" in result.stdout

    def test_version_flag(self):
        """--version should show version and exit 0."""
        result = subprocess.run(
            [sys.executable, "-m", "measure_ai_proficiency", "--version"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "measure-ai-proficiency" in result.stdout


class TestCLIExitCodes:
    """Tests for CLI exit codes."""

    def test_nonexistent_path_exits_1(self):
        """Scanning a nonexistent path should exit with code 1."""
        result = subprocess.run(
            [sys.executable, "-m", "measure_ai_proficiency", "/nonexistent/path/xyz"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "Error" in result.stderr or "not exist" in result.stderr.lower()

    def test_empty_repo_exits_2(self):
        """Scanning an empty repo (Level 1) should exit with code 2."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [sys.executable, "-m", "measure_ai_proficiency", tmpdir],
                capture_output=True,
                text=True,
            )
            # Empty repo = Level 1 = exit 2
            assert result.returncode == 2

    def test_repo_with_ai_files_exits_0(self):
        """Scanning a repo with AI files should exit with code 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a CLAUDE.md file
            claude_md = Path(tmpdir) / "CLAUDE.md"
            claude_md.write_text("# Project\n\nThis is a test project.\n" + "x" * 200)

            result = subprocess.run(
                [sys.executable, "-m", "measure_ai_proficiency", tmpdir],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0


class TestCLIOutputFormats:
    """Tests for different output formats."""

    def test_json_format(self):
        """--format json should output valid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "README.md").write_text("# Test\n" + "x" * 200)

            result = subprocess.run(
                [sys.executable, "-m", "measure_ai_proficiency", "--format", "json", tmpdir],
                capture_output=True,
                text=True,
            )

            import json
            data = json.loads(result.stdout)  # Should not raise
            assert "overall_level" in data

    def test_markdown_format(self):
        """--format markdown should output markdown."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "README.md").write_text("# Test\n" + "x" * 200)

            result = subprocess.run(
                [sys.executable, "-m", "measure_ai_proficiency", "--format", "markdown", tmpdir],
                capture_output=True,
                text=True,
            )

            assert "#" in result.stdout  # Markdown headers

    def test_csv_format(self):
        """--format csv should output CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "README.md").write_text("# Test\n" + "x" * 200)

            result = subprocess.run(
                [sys.executable, "-m", "measure_ai_proficiency", "--format", "csv", tmpdir],
                capture_output=True,
                text=True,
            )

            lines = result.stdout.strip().split("\n")
            assert len(lines) >= 2  # Header + data


class TestCLIMinLevel:
    """Tests for --min-level filtering."""

    def test_min_level_filters_results(self):
        """--min-level should filter out repos below the threshold."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create an empty repo (Level 1)
            Path(tmpdir, "README.md").write_text("# Test\n" + "x" * 200)

            result = subprocess.run(
                [sys.executable, "-m", "measure_ai_proficiency", "--min-level", "3", tmpdir],
                capture_output=True,
                text=True,
            )

            # Level 1 repo filtered out = empty results = exit 1
            assert result.returncode in [1, 2]


class TestCLIOutputFile:
    """Tests for --output file handling."""

    def test_output_to_file(self):
        """--output should write to specified file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "README.md").write_text("# Test\n" + "x" * 200)
            output_file = Path(tmpdir) / "report.json"

            result = subprocess.run(
                [
                    sys.executable, "-m", "measure_ai_proficiency",
                    "--format", "json",
                    "--output", str(output_file),
                    tmpdir,
                ],
                capture_output=True,
                text=True,
            )

            assert output_file.exists()
            content = output_file.read_text()
            import json
            data = json.loads(content)  # Should not raise
            assert "overall_level" in data


class TestCLIOrgMode:
    """Tests for --org directory scanning."""

    def test_org_mode_scans_subdirs(self):
        """--org should scan all subdirectories."""
        with tempfile.TemporaryDirectory() as orgdir:
            # Create two "repos" in the org directory
            repo1 = Path(orgdir) / "repo1"
            repo1.mkdir()
            Path(repo1, "CLAUDE.md").write_text("# Repo 1\n" + "x" * 200)

            repo2 = Path(orgdir) / "repo2"
            repo2.mkdir()
            Path(repo2, "README.md").write_text("# Repo 2\n" + "x" * 200)

            result = subprocess.run(
                [sys.executable, "-m", "measure_ai_proficiency", "--org", orgdir, "--format", "json"],
                capture_output=True,
                text=True,
            )

            import json
            data = json.loads(result.stdout)
            # JSON output is an object with "repos" array
            assert isinstance(data, dict)
            assert "repos" in data
            assert len(data["repos"]) == 2
