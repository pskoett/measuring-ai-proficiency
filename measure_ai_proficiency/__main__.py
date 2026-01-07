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
import sys
from pathlib import Path

from . import __version__
from .scanner import RepoScanner, scan_multiple_repos, scan_github_org
from .reporter import get_reporter


def main():
    parser = argparse.ArgumentParser(
        prog="measure-ai-proficiency",
        description="Measure AI coding proficiency based on context engineering artifacts.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           Scan current directory
  %(prog)s /path/to/repo             Scan specific repository
  %(prog)s repo1 repo2 repo3         Scan multiple repositories
  %(prog)s --org /path/to/org        Scan all repos in directory
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

    # Verbose is now the default; use --quiet to suppress
    verbose = not args.quiet

    # Collect repositories to scan
    if args.org:
        scores = scan_github_org(args.org, verbose=verbose)
    elif len(args.paths) == 1:
        # Single repo
        repo_path = Path(args.paths[0]).resolve()
        if not repo_path.exists():
            print(f"Error: Path does not exist: {repo_path}", file=sys.stderr)
            sys.exit(1)
        scanner = RepoScanner(str(repo_path), verbose=verbose)
        scores = [scanner.scan()]
    else:
        # Multiple repos
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
        if len(scores) == 1 and not args.org:
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


if __name__ == "__main__":
    main()
