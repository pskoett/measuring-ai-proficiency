"""
Tests for MCP server functionality.

Note: These are basic structural tests. Full integration testing requires
an MCP client and is best done manually or with the MCP testing framework.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from measure_ai_proficiency.mcp_server import (
    get_current_repo,
    format_score_result,
    get_level_requirements,
    check_github_cli,
    scan_current_repo,
    get_recommendations_handler,
    check_cross_references,
    get_level_requirements_handler,
    validate_file_quality_handler,
    scan_github_repo_handler,
    scan_github_org_handler,
)
from measure_ai_proficiency.scanner import RepoScanner, RepoScore


class TestHelperFunctions:
    """Test helper functions used by MCP handlers."""

    def test_get_current_repo(self):
        """Test getting current repository path."""
        repo_path = get_current_repo()
        assert isinstance(repo_path, Path)
        assert repo_path.exists()

    def test_format_score_result(self, tmp_path):
        """Test formatting RepoScore to JSON-serializable dict."""
        # Create a minimal RepoScore
        scanner = RepoScanner(tmp_path)
        score = scanner.scan()

        result = format_score_result(score)

        assert isinstance(result, dict)
        assert "repo_name" in result
        assert "overall_level" in result
        assert "overall_score" in result
        assert isinstance(result["overall_score"], (int, float))

    def test_get_level_requirements_max_level(self):
        """Test getting requirements when at max level."""
        result = get_level_requirements(8)

        assert result["current_level"] == 8
        assert result["next_level"] is None
        assert "highest level" in result["message"].lower()

    def test_get_level_requirements_mid_level(self):
        """Test getting requirements for mid-level."""
        result = get_level_requirements(3)

        assert result["current_level"] == 3
        assert result["next_level"] == 4
        assert "next_level_name" in result
        assert "next_level_description" in result
        assert "required_coverage" in result
        assert "file_patterns" in result


class TestMCPHandlers:
    """Test MCP tool handlers."""

    @pytest.mark.asyncio
    async def test_scan_current_repo_handler(self, tmp_path, monkeypatch):
        """Test scan_current_repo MCP handler."""
        # Mock get_current_repo to return our test path
        monkeypatch.setattr(
            "measure_ai_proficiency.mcp_server.get_current_repo",
            lambda: tmp_path
        )

        # Create a minimal context file
        (tmp_path / "CLAUDE.md").write_text("# Test Context\n\nSome content here.")

        result = await scan_current_repo()

        assert len(result) == 1
        assert result[0].type == "text"

        # Parse the JSON response
        data = json.loads(result[0].text)
        assert "repo_name" in data
        assert "overall_level" in data
        assert "overall_score" in data

    @pytest.mark.asyncio
    async def test_get_recommendations_handler(self, tmp_path, monkeypatch):
        """Test get_recommendations MCP handler."""
        monkeypatch.setattr(
            "measure_ai_proficiency.mcp_server.get_current_repo",
            lambda: tmp_path
        )

        result = await get_recommendations_handler()

        assert len(result) == 1
        assert result[0].type == "text"

        data = json.loads(result[0].text)
        assert "repo_name" in data
        assert "current_level" in data
        assert "overall_score" in data
        assert "recommendations" in data
        assert isinstance(data["recommendations"], list)

    @pytest.mark.asyncio
    async def test_check_cross_references_no_refs(self, tmp_path, monkeypatch):
        """Test check_cross_references when no references exist."""
        monkeypatch.setattr(
            "measure_ai_proficiency.mcp_server.get_current_repo",
            lambda: tmp_path
        )

        result = await check_cross_references()

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["total_references"] == 0

    @pytest.mark.asyncio
    async def test_check_cross_references_with_refs(self, tmp_path, monkeypatch):
        """Test check_cross_references with references."""
        monkeypatch.setattr(
            "measure_ai_proficiency.mcp_server.get_current_repo",
            lambda: tmp_path
        )

        # Create files with cross-references
        (tmp_path / "CLAUDE.md").write_text("""
# Claude Context

See [AGENTS.md](AGENTS.md) for agent configuration.
Also check `ARCHITECTURE.md` for system design.
""")
        (tmp_path / "AGENTS.md").write_text("# Agents\n\nAgent definitions here.")
        (tmp_path / "ARCHITECTURE.md").write_text("# Architecture\n\nSystem design.")

        result = await check_cross_references()

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "total_references" in data
        assert "resolved_references" in data
        assert "resolution_rate" in data

    @pytest.mark.asyncio
    async def test_get_level_requirements_handler_with_level(self):
        """Test get_level_requirements handler with explicit level."""
        result = await get_level_requirements_handler(current_level=3)

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["current_level"] == 3
        assert data["next_level"] == 4

    @pytest.mark.asyncio
    async def test_get_level_requirements_handler_auto_detect(self, tmp_path, monkeypatch):
        """Test get_level_requirements handler with auto-detection."""
        monkeypatch.setattr(
            "measure_ai_proficiency.mcp_server.get_current_repo",
            lambda: tmp_path
        )

        result = await get_level_requirements_handler(current_level=None)

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "current_level" in data

    @pytest.mark.asyncio
    async def test_validate_file_quality_missing_file(self, tmp_path, monkeypatch):
        """Test validate_file_quality with missing file."""
        monkeypatch.setattr(
            "measure_ai_proficiency.mcp_server.get_current_repo",
            lambda: tmp_path
        )

        result = await validate_file_quality_handler("nonexistent.md")

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "error" in data
        assert "not found" in data["error"].lower()

    @pytest.mark.asyncio
    async def test_validate_file_quality_existing_file(self, tmp_path, monkeypatch):
        """Test validate_file_quality with existing file."""
        monkeypatch.setattr(
            "measure_ai_proficiency.mcp_server.get_current_repo",
            lambda: tmp_path
        )

        # Create a quality file
        (tmp_path / "CLAUDE.md").write_text("""
## Section 1
Content with `/path/to/file` and `command here`.
Never do this, always do that.

## Section 2
More content with constraints: avoid this, must not do that.

## Section 3
Additional sections with `more commands` and ~/paths.
""")

        result = await validate_file_quality_handler("CLAUDE.md")

        assert len(result) == 1
        data = json.loads(result[0].text)

        # Check structure (may not have score if file not in cross-ref analysis)
        assert isinstance(data, dict)


class TestMCPIntegration:
    """Integration-level tests for MCP server."""

    @pytest.mark.asyncio
    async def test_full_workflow(self, tmp_path, monkeypatch):
        """Test a full workflow: scan → get recommendations → validate."""
        monkeypatch.setattr(
            "measure_ai_proficiency.mcp_server.get_current_repo",
            lambda: tmp_path
        )

        # Create some context files
        (tmp_path / "CLAUDE.md").write_text("""
## Project Context
This is a test project with `/src/main.py` and `make test` command.
Never commit secrets, always use .env files.

See [ARCHITECTURE.md](ARCHITECTURE.md) for design.
""")
        (tmp_path / "ARCHITECTURE.md").write_text("""
## Architecture
System design with `/app/` structure.
""")

        # Step 1: Scan
        scan_result = await scan_current_repo()
        scan_data = json.loads(scan_result[0].text)
        assert "overall_level" in scan_data
        current_level = scan_data["overall_level"]

        # Step 2: Get recommendations
        rec_result = await get_recommendations_handler()
        rec_data = json.loads(rec_result[0].text)
        assert rec_data["current_level"] == current_level
        assert "recommendations" in rec_data

        # Step 3: Check cross-references
        ref_result = await check_cross_references()
        ref_data = json.loads(ref_result[0].text)
        assert ref_data["total_references"] > 0

        # Step 4: Validate specific file
        val_result = await validate_file_quality_handler("CLAUDE.md")
        val_data = json.loads(val_result[0].text)
        # Structure may vary based on whether file was analyzed
        assert isinstance(val_data, dict)


class TestErrorHandling:
    """Test error handling in MCP handlers."""

    @pytest.mark.asyncio
    async def test_validate_file_quality_invalid_path(self, tmp_path, monkeypatch):
        """Test error handling for invalid file paths."""
        monkeypatch.setattr(
            "measure_ai_proficiency.mcp_server.get_current_repo",
            lambda: tmp_path
        )

        result = await validate_file_quality_handler("/absolutely/invalid/path.md")

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "error" in data


class TestGitHubHandlers:
    """Test GitHub-related MCP handlers."""

    def test_check_github_cli_with_gh_installed(self, monkeypatch):
        """Test check_github_cli when gh is installed."""
        monkeypatch.setattr(
            "measure_ai_proficiency.mcp_server.shutil.which",
            lambda cmd: "/usr/local/bin/gh" if cmd == "gh" else None
        )
        assert check_github_cli() is True

    def test_check_github_cli_without_gh(self, monkeypatch):
        """Test check_github_cli when gh is not installed."""
        monkeypatch.setattr(
            "measure_ai_proficiency.mcp_server.shutil.which",
            lambda cmd: None
        )
        assert check_github_cli() is False

    @pytest.mark.asyncio
    async def test_scan_github_repo_no_cli(self, monkeypatch):
        """Test scan_github_repo_handler when GitHub CLI is not available."""
        monkeypatch.setattr(
            "measure_ai_proficiency.mcp_server.check_github_cli",
            lambda: False
        )

        result = await scan_github_repo_handler("owner/repo")

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "error" in data
        assert "GitHub CLI" in data["error"]
        assert "hint" in data

    @pytest.mark.asyncio
    async def test_scan_github_org_no_cli(self, monkeypatch):
        """Test scan_github_org_handler when GitHub CLI is not available."""
        monkeypatch.setattr(
            "measure_ai_proficiency.mcp_server.check_github_cli",
            lambda: False
        )

        result = await scan_github_org_handler("org-name", limit=None)

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "error" in data
        assert "GitHub CLI" in data["error"]
        assert "hint" in data

    @pytest.mark.asyncio
    async def test_scan_github_repo_success(self, tmp_path, monkeypatch):
        """Test scan_github_repo_handler with successful scan."""
        # Mock GitHub CLI check
        monkeypatch.setattr(
            "measure_ai_proficiency.mcp_server.check_github_cli",
            lambda: True
        )

        # Create a mock RepoScore
        scanner = RepoScanner(tmp_path)
        mock_score = scanner.scan()

        # Mock the scan_github_repo function
        monkeypatch.setattr(
            "measure_ai_proficiency.mcp_server.scan_github_repo",
            lambda repo: mock_score
        )

        result = await scan_github_repo_handler("owner/repo")

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "repo_name" in data
        assert "overall_level" in data
        assert "overall_score" in data

    @pytest.mark.asyncio
    async def test_scan_github_repo_error(self, monkeypatch):
        """Test scan_github_repo_handler error handling."""
        monkeypatch.setattr(
            "measure_ai_proficiency.mcp_server.check_github_cli",
            lambda: True
        )

        # Mock the scan_github_repo function to raise an error
        def mock_scan_error(repo):
            raise RuntimeError("API rate limit exceeded")

        monkeypatch.setattr(
            "measure_ai_proficiency.mcp_server.scan_github_repo",
            mock_scan_error
        )

        result = await scan_github_repo_handler("owner/repo")

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "error" in data
        assert "rate limit" in data["error"].lower()

    @pytest.mark.asyncio
    async def test_scan_github_org_success(self, tmp_path, monkeypatch):
        """Test scan_github_org_handler with successful scan."""
        # Mock GitHub CLI check
        monkeypatch.setattr(
            "measure_ai_proficiency.mcp_server.check_github_cli",
            lambda: True
        )

        # Create mock RepoScores
        scanner = RepoScanner(tmp_path)
        mock_score = scanner.scan()

        # Mock the scan_github_org function to return a list of scores
        monkeypatch.setattr(
            "measure_ai_proficiency.mcp_server.scan_github_org",
            lambda org, limit=None: [mock_score, mock_score]
        )

        result = await scan_github_org_handler("org-name", limit=10)

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "organization" in data
        assert data["organization"] == "org-name"
        assert "total_repos" in data
        assert data["total_repos"] == 2
        assert "average_score" in data
        assert "level_distribution" in data
        assert "repositories" in data
        assert len(data["repositories"]) == 2

    @pytest.mark.asyncio
    async def test_scan_github_org_error(self, monkeypatch):
        """Test scan_github_org_handler error handling."""
        monkeypatch.setattr(
            "measure_ai_proficiency.mcp_server.check_github_cli",
            lambda: True
        )

        # Mock the scan_github_org function to raise an error
        def mock_scan_error(org, limit=None):
            raise RuntimeError("Organization not found")

        monkeypatch.setattr(
            "measure_ai_proficiency.mcp_server.scan_github_org",
            mock_scan_error
        )

        result = await scan_github_org_handler("nonexistent-org", limit=None)

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "error" in data
        assert "org" in data
