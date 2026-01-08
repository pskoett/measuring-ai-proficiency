#!/usr/bin/env python3
"""
CLI entry point for measuring AI proficiency.

Usage:
    # Scan current directory
    python -m measure_ai_proficiency

    # Scan specific repository
    python -m measure_ai_proficiency /path/to/repo

    # Scan multiple repositories
    python -m measure_ai_proficiency /path/to/repo1 /path/to/repo2

    # Scan all repos in a directory (like a cloned GitHub org)
    python -m measure_ai_proficiency --org /path/to/org-repos

    # Scan GitHub repository without cloning
    python -m measure_ai_proficiency --github-repo owner/repo

    # Scan all repos in GitHub organization without cloning
    python -m measure_ai_proficiency --github-org org-name

    # Output formats
    python -m measure_ai_proficiency --format json
    python -m measure_ai_proficiency --format markdown
    python -m measure_ai_proficiency --format csv

    # Save to file
    python -m measure_ai_proficiency --output report.md --format markdown

    # Quiet mode (hide detailed file matches)
    python -m measure_ai_proficiency -q
"""

import argparse
import shutil
import sys
from pathlib import Path

from . import __version__
from .scanner import RepoScanner, scan_multiple_repos, scan_github_org
from .reporter import get_reporter
from .github_scanner import scan_github_repo, scan_github_org as scan_github_org_remote


def main():
    parser = argparse.ArgumentParser(
        prog="measure-ai-proficiency",
        description="Measure AI coding proficiency based on context engineering artifacts.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Scanning Methods:
  LOCAL (default):         Scan local repositories on disk
  GITHUB CLI (optional):   Scan GitHub repos without cloning (requires gh CLI)

Examples:
  # Local scanning (default)
  %(prog)s                           Scan current directory
  %(prog)s /path/to/repo             Scan specific repository
  %(prog)s repo1 repo2 repo3         Scan multiple repositories
  %(prog)s --org /path/to/org        Scan all repos in directory

  # GitHub CLI scanning (optional, no cloning!)
  %(prog)s --github-repo owner/repo  Scan GitHub repo without cloning
  %(prog)s --github-org anthropic    Scan all repos in GitHub org
  %(prog)s --github-org org --limit 50  Limit number of repos

  # Output formats (work with both methods)
  %(prog)s --format json             Output as JSON
  %(prog)s --format markdown -o report.md  Save markdown report
  %(prog)s -q                        Quiet mode (hide file details)

Maturity Levels (aligned with Steve Yegge's 8-stage model):
  Level 1: Zero AI (no context engineering, autocomplete only)
  Level 2: Basic instructions (CLAUDE.md, .cursorrules, etc.)
  Level 3: Comprehensive context (architecture, conventions, patterns)
  Level 4: Skills & automation (hooks, commands, memory files)
  Level 5: Multi-agent ready (specialized agents, MCP configs)
  Level 6: Fleet infrastructure (Beads, shared context, workflows)
  Level 7: Agent fleet (governance, scheduling, pipelines)
  Level 8: Custom orchestration (Gas Town, meta-automation, frontier)

GitHub CLI Requirements:
  Install: https://cli.github.com/
  Authenticate: gh auth login
        """,
    )

    parser.add_argument(
        "paths",
        nargs="*",
        default=["."],
        help="Repository path(s) to scan (default: current directory)",
    )

    parser.add_argument(
        "--org",
        metavar="PATH",
        help="Scan all repositories in a directory (like a cloned GitHub org)",
    )

    parser.add_argument(
        "--github-repo",
        metavar="OWNER/REPO",
        help="Scan a GitHub repository without cloning (requires gh CLI)",
    )

    parser.add_argument(
        "--github-org",
        metavar="ORG",
        help="Scan all repos in a GitHub organization without cloning (requires gh CLI)",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="Maximum number of repos to scan from GitHub org (default: 1000)",
    )

    parser.add_argument(
        "-f",
        "--format",
        choices=["terminal", "json", "markdown", "csv"],
        default="terminal",
        help="Output format (default: terminal)",
    )

    parser.add_argument(
        "-o",
        "--output",
        metavar="FILE",
        help="Output file (default: stdout)",
    )

    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Hide detailed file matches (show summary only)",
    )

    parser.add_argument(
        "--min-level",
        type=int,
        choices=[1, 2, 3, 4, 5, 6, 7, 8],
        help="Only show repos at or above this level (1-8)",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    args = parser.parse_args()

    # Check for conflicting arguments
    modes = sum([
        bool(args.org),
        bool(args.github_repo),
        bool(args.github_org),
        len(args.paths) > 0 and args.paths != ["."]
    ])
    if modes > 1:
        print("Error: Cannot specify multiple scanning modes (local paths, --org, --github-repo, --github-org)", file=sys.stderr)
        sys.exit(1)

    # Verbose is now the default; use --quiet to suppress
    verbose = not args.quiet

    # Track temp directories for cleanup
    temp_dirs = []

    try:
        # Collect repositories to scan
        if args.github_repo:
            # Scan single GitHub repo without cloning
            temp_dir = scan_github_repo(args.github_repo, verbose=verbose)
            if temp_dir is None:
                sys.exit(1)
            temp_dirs.append(temp_dir)
            scanner = RepoScanner(str(temp_dir), verbose=verbose)
            scores = [scanner.scan()]
            # Set repo name for display
            scores[0].repo_path = args.github_repo

        elif args.github_org:
            # Scan GitHub org without cloning
            results = scan_github_org_remote(args.github_org, verbose=verbose, limit=args.limit)
            if not results:
                sys.exit(1)

            scores = []
            for repo_name, temp_dir in results:
                if temp_dir is None:
                    continue
                temp_dirs.append(temp_dir)
                scanner = RepoScanner(str(temp_dir), verbose=verbose)
                score = scanner.scan()
                # Set repo name for display
                score.repo_path = repo_name
                scores.append(score)

        elif args.org:
            # Scan local org directory
            scores = scan_github_org(args.org, verbose=verbose)

        elif len(args.paths) == 1:
            # Single local repo
            repo_path = Path(args.paths[0]).resolve()
            if not repo_path.exists():
                print(f"Error: Path does not exist: {repo_path}", file=sys.stderr)
                sys.exit(1)
            scanner = RepoScanner(str(repo_path), verbose=verbose)
            scores = [scanner.scan()]

        else:
            # Multiple local repos
            scores = scan_multiple_repos(args.paths, verbose=verbose)

        # Filter by minimum level if specified
        if args.min_level is not None:
            scores = [s for s in scores if s.overall_level >= args.min_level]

        # Get reporter
        reporter = get_reporter(args.format, verbose=verbose)

        # Output
        output = sys.stdout
        if args.output:
            try:
                output = open(args.output, "w")
            except (OSError, IOError) as e:
                print(f"Error: Cannot write to file: {args.output} ({e})", file=sys.stderr)
                sys.exit(1)

        try:
            if len(scores) == 1 and not args.org and not args.github_org:
                reporter.report_single(scores[0], output)
            else:
                reporter.report_multiple(scores, output)
        except (OSError, IOError) as e:
            print(f"Error: Failed to write output: {e}", file=sys.stderr)
            sys.exit(1)
        finally:
            if args.output:
                output.close()

        # Exit code based on results
        if not scores:
            sys.exit(1)

        # Return non-zero if all repos are Level 1 (no AI context)
        if all(s.overall_level == 1 for s in scores):
            sys.exit(2)

    finally:
        # Clean up temp directories
        for temp_dir in temp_dirs:
            if temp_dir and temp_dir.exists():
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    print(f"Warning: Failed to clean up temp directory {temp_dir}: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
