"""
GitHub integration for scanning remote repositories without cloning.

Uses the GitHub CLI (gh) to fetch repository contents and creates temporary
local structures for scanning.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Optional, Dict, Any

from .config import LEVELS


def check_gh_cli() -> bool:
    """Check if GitHub CLI is installed and authenticated."""
    try:
        result = subprocess.run(
            ["gh", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            return False

        # Check if authenticated
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def ensure_gh_cli():
    """Ensure GitHub CLI is installed and authenticated, exit if not."""
    if not check_gh_cli():
        print("Error: GitHub CLI (gh) is not installed or not authenticated.", file=sys.stderr)
        print("\nTo install:", file=sys.stderr)
        print("  - macOS: brew install gh", file=sys.stderr)
        print("  - Linux: https://github.com/cli/cli#installation", file=sys.stderr)
        print("  - Windows: https://github.com/cli/cli#installation", file=sys.stderr)
        print("\nAfter installation, run: gh auth login", file=sys.stderr)
        sys.exit(1)


def get_repo_default_branch(owner: str, repo: str) -> str:
    """Get the default branch name for a repository."""
    try:
        result = subprocess.run(
            ["gh", "api", f"repos/{owner}/{repo}", "-q", ".default_branch"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        return "main"  # fallback
    except subprocess.TimeoutExpired:
        return "main"


def fetch_file_from_github(owner: str, repo: str, file_path: str, branch: str = "main") -> Optional[str]:
    """
    Fetch a single file from GitHub using gh CLI.

    Returns the file content as a string, or None if the file doesn't exist.
    """
    try:
        # Try to get file content via GitHub API
        result = subprocess.run(
            ["gh", "api", f"repos/{owner}/{repo}/contents/{file_path}",
             "-H", "Accept: application/vnd.github.raw",
             "--jq", "."],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            return result.stdout
        return None
    except subprocess.TimeoutExpired:
        return None


def get_repo_tree(owner: str, repo: str, branch: str = "main") -> List[Dict[str, Any]]:
    """
    Get the complete file tree of a repository using GitHub API.

    Returns a list of file entries with path, type, and size information.
    """
    try:
        # Get the tree SHA for the branch
        result = subprocess.run(
            ["gh", "api", f"repos/{owner}/{repo}/git/trees/{branch}?recursive=1"],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            return []

        data = json.loads(result.stdout)
        tree = data.get("tree", [])

        # Filter for files only (not directories) and exclude large files
        files = [
            entry for entry in tree
            if entry.get("type") == "blob" and entry.get("size", 0) < 1_000_000  # Max 1MB
        ]

        return files
    except (subprocess.TimeoutExpired, json.JSONDecodeError):
        return []


def get_relevant_files(tree: List[Dict[str, Any]]) -> List[str]:
    """
    Filter the repository tree for files relevant to AI proficiency scanning.

    This avoids downloading unnecessary files by checking against known patterns.
    """
    relevant_paths = []

    # Collect all patterns from levels
    patterns_to_check = set()
    for level in LEVELS:
        for pattern in level.file_patterns:
            patterns_to_check.add(pattern)

    # Common AI instruction files to always check
    always_check = {
        "CLAUDE.md", "AGENTS.md", ".cursorrules", "CODEX.md",
        ".github/copilot-instructions.md", ".copilot-instructions.md",
        ".ai-proficiency.yaml", ".ai-proficiency.yml"
    }

    # Patterns that need special handling
    skill_patterns = [
        ".claude/skills/", ".github/skills/", ".copilot/skills/",
        ".cursor/skills/", ".codex/skills/", "skills/"
    ]

    command_patterns = [
        ".claude/commands/", ".github/commands/"
    ]

    for entry in tree:
        path = entry.get("path", "")

        # Check always_check files
        if path in always_check:
            relevant_paths.append(path)
            continue

        # Check if in skills directory
        for skill_pattern in skill_patterns:
            if skill_pattern in path and path.endswith("SKILL.md"):
                relevant_paths.append(path)
                break

        # Check if in commands directory
        for cmd_pattern in command_patterns:
            if path.startswith(cmd_pattern) and path.endswith(".md"):
                relevant_paths.append(path)
                break

        # Check direct pattern matches
        for pattern in patterns_to_check:
            # Simple pattern matching (no wildcards for now)
            if pattern == path or path.endswith(pattern):
                relevant_paths.append(path)
                break

    return relevant_paths


def download_repo_files(owner: str, repo: str, branch: str, target_dir: Path) -> bool:
    """
    Download relevant files from a GitHub repository to a temporary directory.

    Returns True if successful, False otherwise.
    """
    try:
        # Get repository tree
        tree = get_repo_tree(owner, repo, branch)
        if not tree:
            print(f"Warning: Could not fetch tree for {owner}/{repo}", file=sys.stderr)
            return False

        # Get relevant files
        relevant_files = get_relevant_files(tree)

        if not relevant_files:
            # No AI proficiency files found - that's okay, just means Level 1
            return True

        # Download each file
        downloaded = 0
        for file_path in relevant_files:
            content = fetch_file_from_github(owner, repo, file_path, branch)
            if content is not None:
                # Create directory structure
                full_path = target_dir / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)

                # Write file
                try:
                    full_path.write_text(content, encoding='utf-8')
                    downloaded += 1
                except Exception as e:
                    print(f"Warning: Could not write {file_path}: {e}", file=sys.stderr)

        print(f"Downloaded {downloaded}/{len(relevant_files)} files from {owner}/{repo}")
        return True

    except Exception as e:
        print(f"Error downloading files from {owner}/{repo}: {e}", file=sys.stderr)
        return False


def create_minimal_git_repo(target_dir: Path, owner: str, repo: str):
    """
    Create a minimal .git directory to avoid git-related errors during scanning.

    This creates a bare minimum git structure so git commands don't fail.
    """
    git_dir = target_dir / ".git"
    git_dir.mkdir(exist_ok=True)

    # Create minimal config
    config_content = f"""[core]
	repositoryformatversion = 0
	filemode = true
	bare = false
[remote "origin"]
	url = https://github.com/{owner}/{repo}.git
	fetch = +refs/heads/*:refs/remotes/origin/*
"""
    (git_dir / "config").write_text(config_content)

    # Create HEAD
    (git_dir / "HEAD").write_text("ref: refs/heads/main\n")


def scan_github_repo(repo_full_name: str, verbose: bool = False) -> Optional[Path]:
    """
    Scan a GitHub repository without cloning it.

    Args:
        repo_full_name: Full repository name in format "owner/repo"
        verbose: Enable verbose output

    Returns:
        Path to temporary directory containing downloaded files, or None on error.
        Caller is responsible for cleanup.
    """
    ensure_gh_cli()

    # Parse owner/repo
    parts = repo_full_name.split("/")
    if len(parts) != 2:
        print(f"Error: Invalid repository format '{repo_full_name}'. Expected 'owner/repo'", file=sys.stderr)
        return None

    owner, repo = parts

    # Get default branch
    branch = get_repo_default_branch(owner, repo)
    if verbose:
        print(f"Scanning {owner}/{repo} (branch: {branch})")

    # Create temporary directory
    temp_dir = Path(tempfile.mkdtemp(prefix=f"ai-prof-{repo}-"))

    try:
        # Download relevant files
        success = download_repo_files(owner, repo, branch, temp_dir)
        if not success:
            shutil.rmtree(temp_dir)
            return None

        # Create minimal git structure
        create_minimal_git_repo(temp_dir, owner, repo)

        return temp_dir

    except Exception as e:
        print(f"Error scanning {repo_full_name}: {e}", file=sys.stderr)
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        return None


def list_org_repos(org: str, limit: int = 1000) -> List[str]:
    """
    List all repositories in a GitHub organization.

    Returns a list of repository full names (owner/repo format).
    """
    ensure_gh_cli()

    try:
        result = subprocess.run(
            ["gh", "repo", "list", org, "--limit", str(limit), "--json", "nameWithOwner", "-q", ".[].nameWithOwner"],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            print(f"Error listing repos for org '{org}': {result.stderr}", file=sys.stderr)
            return []

        repos = [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]
        return repos

    except subprocess.TimeoutExpired:
        print(f"Error: Timeout while listing repos for org '{org}'", file=sys.stderr)
        return []


def scan_github_org(org: str, verbose: bool = False, limit: int = 1000) -> List[tuple[str, Optional[Path]]]:
    """
    Scan all repositories in a GitHub organization without cloning.

    Args:
        org: GitHub organization name
        verbose: Enable verbose output
        limit: Maximum number of repos to scan

    Returns:
        List of tuples (repo_name, temp_dir_path). temp_dir_path is None if scan failed.
        Caller is responsible for cleanup of temp directories.
    """
    ensure_gh_cli()

    # List all repos
    repos = list_org_repos(org, limit)

    if not repos:
        print(f"No repositories found for organization '{org}'", file=sys.stderr)
        return []

    print(f"Found {len(repos)} repositories in '{org}'")

    # Scan each repo
    results = []
    for i, repo_name in enumerate(repos, 1):
        if verbose:
            print(f"\n[{i}/{len(repos)}] Scanning {repo_name}...")
        else:
            print(f"[{i}/{len(repos)}] {repo_name}")

        temp_dir = scan_github_repo(repo_name, verbose)
        results.append((repo_name, temp_dir))

    return results
