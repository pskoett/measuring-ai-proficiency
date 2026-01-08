"""
Tests for GitHub CLI integration and remote repository scanning.
"""

import json
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call

import pytest

from measure_ai_proficiency.github_scanner import (
    check_gh_cli,
    ensure_gh_cli,
    get_repo_default_branch,
    fetch_file_from_github,
    get_repo_tree,
    get_relevant_files,
    download_repo_files,
    create_minimal_git_repo,
    scan_github_repo,
    list_org_repos,
    scan_github_org,
    check_rate_limit_status,
    retry_with_backoff,
)


class TestCheckGhCli:
    """Tests for GitHub CLI availability checks."""

    @patch('subprocess.run')
    def test_check_gh_cli_success(self, mock_run):
        """Test successful gh CLI check."""
        # Mock successful version and auth checks
        mock_run.side_effect = [
            Mock(returncode=0, stdout="gh version 2.40.0"),
            Mock(returncode=0, stdout="Logged in to github.com")
        ]

        assert check_gh_cli() is True
        assert mock_run.call_count == 2

    @patch('subprocess.run')
    def test_check_gh_cli_not_installed(self, mock_run):
        """Test when gh CLI is not installed."""
        mock_run.side_effect = FileNotFoundError()

        assert check_gh_cli() is False

    @patch('subprocess.run')
    def test_check_gh_cli_not_authenticated(self, mock_run):
        """Test when gh CLI is not authenticated."""
        mock_run.side_effect = [
            Mock(returncode=0, stdout="gh version 2.40.0"),
            Mock(returncode=1, stderr="Not authenticated")
        ]

        assert check_gh_cli() is False

    @patch('subprocess.run')
    def test_check_gh_cli_timeout(self, mock_run):
        """Test timeout during gh CLI check."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["gh"], timeout=5)

        assert check_gh_cli() is False


class TestEnsureGhCli:
    """Tests for ensuring gh CLI is available."""

    @patch('measure_ai_proficiency.github_scanner.check_gh_cli')
    def test_ensure_gh_cli_success(self, mock_check):
        """Test ensure_gh_cli when gh is available."""
        mock_check.return_value = True
        ensure_gh_cli()  # Should not raise

    @patch('measure_ai_proficiency.github_scanner.check_gh_cli')
    @patch('sys.exit')
    def test_ensure_gh_cli_not_available(self, mock_exit, mock_check):
        """Test ensure_gh_cli when gh is not available."""
        mock_check.return_value = False
        ensure_gh_cli()
        mock_exit.assert_called_once_with(1)


class TestGetRepoDefaultBranch:
    """Tests for fetching repository default branch."""

    @patch('subprocess.run')
    def test_get_default_branch_success(self, mock_run):
        """Test successful default branch fetch."""
        mock_run.return_value = Mock(returncode=0, stdout="main\n")

        result = get_repo_default_branch("owner", "repo")
        assert result == "main"

    @patch('subprocess.run')
    def test_get_default_branch_master(self, mock_run):
        """Test fetching master branch."""
        mock_run.return_value = Mock(returncode=0, stdout="master\n")

        result = get_repo_default_branch("owner", "repo")
        assert result == "master"

    @patch('subprocess.run')
    def test_get_default_branch_failure(self, mock_run):
        """Test fallback when branch fetch fails."""
        mock_run.return_value = Mock(returncode=1, stdout="")

        result = get_repo_default_branch("owner", "repo")
        assert result == "main"  # fallback

    @patch('subprocess.run')
    def test_get_default_branch_timeout(self, mock_run):
        """Test fallback on timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["gh"], timeout=10)

        result = get_repo_default_branch("owner", "repo")
        assert result == "main"  # fallback


class TestFetchFileFromGithub:
    """Tests for fetching individual files from GitHub."""

    @patch('subprocess.run')
    def test_fetch_file_success(self, mock_run):
        """Test successful file fetch."""
        mock_run.return_value = Mock(returncode=0, stdout="file content here")

        result = fetch_file_from_github("owner", "repo", "CLAUDE.md")
        assert result == "file content here"

    @patch('subprocess.run')
    def test_fetch_file_not_found(self, mock_run):
        """Test file not found."""
        mock_run.return_value = Mock(returncode=404, stdout="")

        result = fetch_file_from_github("owner", "repo", "nonexistent.md")
        assert result is None

    @patch('subprocess.run')
    def test_fetch_file_timeout(self, mock_run):
        """Test timeout during file fetch."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["gh"], timeout=10)

        result = fetch_file_from_github("owner", "repo", "CLAUDE.md")
        assert result is None


class TestGetRepoTree:
    """Tests for fetching repository file tree."""

    @patch('subprocess.run')
    def test_get_repo_tree_success(self, mock_run):
        """Test successful tree fetch."""
        tree_data = {
            "tree": [
                {"path": "CLAUDE.md", "type": "blob", "size": 1000},
                {"path": "README.md", "type": "blob", "size": 2000},
                {"path": "src", "type": "tree", "size": 0},
                {"path": "large.bin", "type": "blob", "size": 2_000_000},  # too large
            ]
        }
        mock_run.return_value = Mock(returncode=0, stdout=json.dumps(tree_data))

        result = get_repo_tree("owner", "repo", "main")

        # Should filter out directories and large files
        assert len(result) == 2
        assert all(entry["type"] == "blob" for entry in result)
        assert all(entry["size"] < 1_000_000 for entry in result)

    @patch('subprocess.run')
    def test_get_repo_tree_with_retry(self, mock_run):
        """Test tree fetch with retry on rate limit."""
        # First call fails with rate limit, second succeeds
        tree_data = {"tree": [{"path": "CLAUDE.md", "type": "blob", "size": 1000}]}

        error = subprocess.CalledProcessError(
            returncode=403,
            cmd=["gh"],
            stderr="API rate limit exceeded"
        )
        mock_run.side_effect = [
            error,  # First attempt fails
            Mock(returncode=0, stdout=json.dumps(tree_data))  # Second succeeds
        ]

        with patch('time.sleep'):  # Mock sleep to speed up test
            result = get_repo_tree("owner", "repo", "main")

        assert len(result) == 1
        assert result[0]["path"] == "CLAUDE.md"


class TestGetRelevantFiles:
    """Tests for filtering relevant AI proficiency files."""

    def test_get_relevant_files_basic(self):
        """Test filtering basic instruction files."""
        tree = [
            {"path": "CLAUDE.md", "type": "blob"},
            {"path": "README.md", "type": "blob"},
            {"path": ".cursorrules", "type": "blob"},
            {"path": "src/main.py", "type": "blob"},
        ]

        result = get_relevant_files(tree)

        assert "CLAUDE.md" in result
        assert ".cursorrules" in result
        assert "README.md" in result  # README.md is included (Level 1 pattern)
        assert "src/main.py" not in result

    def test_get_relevant_files_skills(self):
        """Test filtering skill files."""
        tree = [
            {"path": ".claude/skills/test-skill/SKILL.md", "type": "blob"},
            {"path": ".github/skills/deploy/SKILL.md", "type": "blob"},
            {"path": "skills/custom/SKILL.md", "type": "blob"},
            {"path": ".claude/skills/README.md", "type": "blob"},  # Also included (matches README.md pattern)
            {"path": "unrelated/file.txt", "type": "blob"},  # Not included
        ]

        result = get_relevant_files(tree)

        assert ".claude/skills/test-skill/SKILL.md" in result
        assert ".github/skills/deploy/SKILL.md" in result
        assert "skills/custom/SKILL.md" in result
        assert ".claude/skills/README.md" in result  # README.md is always included
        assert "unrelated/file.txt" not in result

    def test_get_relevant_files_commands(self):
        """Test filtering command files."""
        tree = [
            {"path": ".claude/commands/test.md", "type": "blob"},
            {"path": ".github/commands/deploy.md", "type": "blob"},
            {"path": "commands/custom.md", "type": "blob"},  # Not in valid location
        ]

        result = get_relevant_files(tree)

        assert ".claude/commands/test.md" in result
        assert ".github/commands/deploy.md" in result
        # commands/custom.md might not be included depending on pattern matching

    def test_get_relevant_files_config(self):
        """Test filtering config files."""
        tree = [
            {"path": ".ai-proficiency.yaml", "type": "blob"},
            {"path": ".ai-proficiency.yml", "type": "blob"},
        ]

        result = get_relevant_files(tree)

        assert ".ai-proficiency.yaml" in result
        assert ".ai-proficiency.yml" in result


class TestDownloadRepoFiles:
    """Tests for downloading repository files."""

    @patch('measure_ai_proficiency.github_scanner.get_repo_tree')
    @patch('measure_ai_proficiency.github_scanner.fetch_file_from_github')
    def test_download_repo_files_success(self, mock_fetch, mock_tree):
        """Test successful file download."""
        tree = [
            {"path": "CLAUDE.md", "type": "blob", "size": 1000},
            {"path": ".cursorrules", "type": "blob", "size": 500},
        ]
        mock_tree.return_value = tree
        mock_fetch.side_effect = ["claude content", "cursor rules"]

        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            result = download_repo_files("owner", "repo", "main", target)

            assert result is True
            assert (target / "CLAUDE.md").exists()
            assert (target / ".cursorrules").exists()
            assert (target / "CLAUDE.md").read_text() == "claude content"

    @patch('measure_ai_proficiency.github_scanner.get_repo_tree')
    def test_download_repo_files_empty_tree(self, mock_tree):
        """Test handling of empty tree."""
        mock_tree.return_value = []

        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            result = download_repo_files("owner", "repo", "main", target)

            # Empty tree is valid (Level 1 repo)
            assert result is True

    @patch('measure_ai_proficiency.github_scanner.get_repo_tree')
    def test_download_repo_files_tree_fetch_fails(self, mock_tree):
        """Test handling of tree fetch failure."""
        mock_tree.side_effect = subprocess.CalledProcessError(1, ["gh"])

        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            result = download_repo_files("owner", "repo", "main", target)

            assert result is False


class TestCreateMinimalGitRepo:
    """Tests for creating minimal git repository structure."""

    def test_create_minimal_git_repo(self):
        """Test git structure creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            create_minimal_git_repo(target, "owner", "repo")

            git_dir = target / ".git"
            assert git_dir.exists()
            assert (git_dir / "config").exists()
            assert (git_dir / "HEAD").exists()

            # Check config content
            config = (git_dir / "config").read_text()
            assert "https://github.com/owner/repo.git" in config

            # Check HEAD content
            head = (git_dir / "HEAD").read_text()
            assert "ref: refs/heads/main" in head


class TestScanGithubRepo:
    """Tests for scanning single GitHub repositories."""

    @patch('measure_ai_proficiency.github_scanner.ensure_gh_cli')
    @patch('measure_ai_proficiency.github_scanner.get_repo_default_branch')
    @patch('measure_ai_proficiency.github_scanner.download_repo_files')
    def test_scan_github_repo_success(self, mock_download, mock_branch, mock_ensure):
        """Test successful repository scan."""
        mock_branch.return_value = "main"
        mock_download.return_value = True

        result = scan_github_repo("owner/repo")

        assert result is not None
        assert result.exists()
        # Check that .git directory was created
        assert (result / ".git").exists()
        assert (result / ".git" / "config").exists()
        assert (result / ".git" / "HEAD").exists()

        # Cleanup
        import shutil
        shutil.rmtree(result)

    @patch('measure_ai_proficiency.github_scanner.ensure_gh_cli')
    def test_scan_github_repo_invalid_format(self, mock_ensure):
        """Test invalid repository format."""
        result = scan_github_repo("invalid-format")
        assert result is None

    @patch('measure_ai_proficiency.github_scanner.ensure_gh_cli')
    @patch('measure_ai_proficiency.github_scanner.get_repo_default_branch')
    @patch('measure_ai_proficiency.github_scanner.download_repo_files')
    def test_scan_github_repo_download_fails(self, mock_download, mock_branch, mock_ensure):
        """Test scan when download fails."""
        mock_branch.return_value = "main"
        mock_download.return_value = False

        result = scan_github_repo("owner/repo")
        assert result is None


class TestListOrgRepos:
    """Tests for listing organization repositories."""

    @patch('measure_ai_proficiency.github_scanner.ensure_gh_cli')
    @patch('subprocess.run')
    def test_list_org_repos_success(self, mock_run, mock_ensure):
        """Test successful org repo listing."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="owner/repo1\nowner/repo2\nowner/repo3\n"
        )

        result = list_org_repos("owner", limit=100)

        assert len(result) == 3
        assert "owner/repo1" in result
        assert "owner/repo2" in result

    @patch('measure_ai_proficiency.github_scanner.ensure_gh_cli')
    @patch('subprocess.run')
    def test_list_org_repos_empty(self, mock_run, mock_ensure):
        """Test org with no repos."""
        mock_run.return_value = Mock(returncode=0, stdout="")

        result = list_org_repos("empty-org")
        assert result == []

    @patch('measure_ai_proficiency.github_scanner.ensure_gh_cli')
    @patch('subprocess.run')
    def test_list_org_repos_failure(self, mock_run, mock_ensure):
        """Test failed org listing."""
        mock_run.return_value = Mock(returncode=1, stderr="Not found")

        result = list_org_repos("nonexistent-org")
        assert result == []


class TestScanGithubOrg:
    """Tests for scanning GitHub organizations."""

    @patch('measure_ai_proficiency.github_scanner.ensure_gh_cli')
    @patch('measure_ai_proficiency.github_scanner.list_org_repos')
    @patch('measure_ai_proficiency.github_scanner.scan_github_repo')
    def test_scan_github_org_success(self, mock_scan, mock_list, mock_ensure):
        """Test successful org scan."""
        mock_list.return_value = ["owner/repo1", "owner/repo2"]
        mock_scan.side_effect = [Path("/tmp/repo1"), Path("/tmp/repo2")]

        result = scan_github_org("owner", limit=10)

        assert len(result) == 2
        assert result[0][0] == "owner/repo1"
        assert result[1][0] == "owner/repo2"

    @patch('measure_ai_proficiency.github_scanner.ensure_gh_cli')
    @patch('measure_ai_proficiency.github_scanner.list_org_repos')
    def test_scan_github_org_no_repos(self, mock_list, mock_ensure):
        """Test org with no repos."""
        mock_list.return_value = []

        result = scan_github_org("empty-org")
        assert result == []


class TestCheckRateLimitStatus:
    """Tests for checking GitHub API rate limit status."""

    @patch('subprocess.run')
    def test_check_rate_limit_success(self, mock_run):
        """Test successful rate limit check."""
        rate_data = {
            "resources": {
                "core": {
                    "limit": 5000,
                    "remaining": 4999,
                    "reset": 1234567890
                }
            }
        }
        mock_run.return_value = Mock(returncode=0, stdout=json.dumps(rate_data))

        result = check_rate_limit_status()

        assert result["limit"] == 5000
        assert result["remaining"] == 4999
        assert result["reset"] == 1234567890

    @patch('subprocess.run')
    def test_check_rate_limit_failure(self, mock_run):
        """Test rate limit check failure."""
        mock_run.return_value = Mock(returncode=1, stdout="")

        result = check_rate_limit_status()

        assert result["limit"] == 0
        assert result["remaining"] == 0
        assert result["reset"] == 0


class TestRetryWithBackoff:
    """Tests for retry decorator."""

    def test_retry_success_first_attempt(self):
        """Test successful call on first attempt."""
        mock_func = Mock(return_value="success")
        decorated = retry_with_backoff(max_retries=3)(mock_func)

        result = decorated()

        assert result == "success"
        assert mock_func.call_count == 1

    @patch('time.sleep')
    def test_retry_success_after_failure(self, mock_sleep):
        """Test successful call after retries."""
        mock_func = Mock(side_effect=[
            subprocess.CalledProcessError(403, ["gh"], stderr="rate limit"),
            "success"
        ])
        decorated = retry_with_backoff(max_retries=3, initial_delay=1.0)(mock_func)

        result = decorated()

        assert result == "success"
        assert mock_func.call_count == 2
        mock_sleep.assert_called()

    @patch('time.sleep')
    def test_retry_max_retries_exceeded(self, mock_sleep):
        """Test max retries exceeded."""
        error = subprocess.CalledProcessError(403, ["gh"], stderr="rate limit")
        mock_func = Mock(side_effect=error)
        decorated = retry_with_backoff(max_retries=2, initial_delay=0.5)(mock_func)

        with pytest.raises(subprocess.CalledProcessError):
            decorated()

        assert mock_func.call_count == 3  # initial + 2 retries

    def test_retry_non_retryable_error(self):
        """Test non-retryable error is not retried."""
        error = ValueError("unexpected error")
        mock_func = Mock(side_effect=error)
        decorated = retry_with_backoff(max_retries=3)(mock_func)

        with pytest.raises(ValueError):
            decorated()

        assert mock_func.call_count == 1  # No retries for unexpected errors
