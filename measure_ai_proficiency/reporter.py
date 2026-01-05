"""
Report generation for AI proficiency measurement.

Outputs results in various formats: terminal, JSON, markdown, CSV.
"""

import json
import sys
from datetime import datetime
from typing import List, TextIO

from .scanner import RepoScore


# Terminal colors
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"


def _supports_color() -> bool:
    """Check if terminal supports color."""

    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def _color(text: str, color: str) -> str:
    """Apply color if supported."""

    if _supports_color():
        return f"{color}{text}{Colors.ENDC}"
    return text


def _level_color(level: int) -> str:
    """Get color for a level."""

    colors = {
        0: Colors.RED,
        1: Colors.YELLOW,
        2: Colors.CYAN,
        3: Colors.GREEN,
        4: Colors.BLUE,
    }
    return colors.get(level, Colors.ENDC)


def _progress_bar(percent: float, width: int = 20) -> str:
    """Create a simple progress bar."""

    filled = int(width * percent / 100)
    empty = width - filled
    return f"[{'█' * filled}{'░' * empty}]"


class TerminalReporter:
    """Report results to terminal with colors and formatting."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def report_single(self, score: RepoScore, output: TextIO = sys.stdout) -> None:
        """Report a single repository score."""

        print(file=output)
        print(_color(f"{'='*60}", Colors.DIM), file=output)
        print(_color(f" AI Proficiency Report: {score.repo_name}", Colors.BOLD), file=output)
        print(_color(f"{'='*60}", Colors.DIM), file=output)
        print(file=output)

        # Overall level
        level_text = f"Level {score.overall_level}"
        if score.overall_level == 0:
            level_text = "Level 0: No Context Engineering"
        else:
            level_text = score.level_scores[score.overall_level].name

        print(
            f"  Overall Level: {_color(level_text, _level_color(score.overall_level))}",
            file=output,
        )
        print(
            f"  Overall Score: {_color(f'{score.overall_score:.1f}/100', Colors.BOLD)}",
            file=output,
        )
        print(file=output)

        # Level breakdown
        print(_color("  Level Breakdown:", Colors.BOLD), file=output)
        print(file=output)

        for level_num in sorted(score.level_scores.keys()):
            level_score = score.level_scores[level_num]
            achieved = "✓" if level_num <= score.overall_level and score.overall_level > 0 else "○"
            achieved_color = Colors.GREEN if achieved == "✓" else Colors.DIM

            bar = _progress_bar(level_score.coverage_percent)
            print(f"    {_color(achieved, achieved_color)} {level_score.name}", file=output)
            print(
                f"      {bar} {level_score.coverage_percent:.1f}% "
                f"({level_score.substantive_file_count} files)",
                file=output,
            )

            if self.verbose and level_score.matched_files:
                for f in level_score.matched_files[:5]:
                    status = "●" if f.is_substantive else "○"
                    print(f"        {_color(status, Colors.DIM)} {f.path}", file=output)
                if len(level_score.matched_files) > 5:
                    print(
                        f"        {_color(f'... and {len(level_score.matched_files) - 5} more', Colors.DIM)}",
                        file=output,
                    )
            print(file=output)

        # Recommendations
        if score.recommendations:
            print(_color("  Recommendations:", Colors.BOLD), file=output)
            print(file=output)
            for rec in score.recommendations:
                print(f"    → {rec}", file=output)
            print(file=output)

        print(_color(f"{'='*60}", Colors.DIM), file=output)
        print(file=output)

    def report_multiple(self, scores: List[RepoScore], output: TextIO = sys.stdout) -> None:
        """Report multiple repository scores as a summary table."""

        if not scores:
            print("No repositories scanned.", file=output)
            return

        print(file=output)
        print(_color(f"{'='*70}", Colors.DIM), file=output)
        print(_color(" AI Proficiency Summary", Colors.BOLD), file=output)
        print(_color(f"{'='*70}", Colors.DIM), file=output)
        print(file=output)

        # Sort by level descending, then score descending
        sorted_scores = sorted(
            scores,
            key=lambda s: (s.overall_level, s.overall_score),
            reverse=True,
        )

        # Header
        print(f"  {'Repository':<30} {'Level':<10} {'Score':<10} {'Status'}", file=output)
        print(f"  {'-'*30} {'-'*10} {'-'*10} {'-'*15}", file=output)

        # Distribution counters
        level_counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}

        for score in sorted_scores:
            name = score.repo_name[:28] + ".." if len(score.repo_name) > 30 else score.repo_name
            level = f"Level {score.overall_level}"
            score_str = f"{score.overall_score:.1f}"

            if score.overall_level == 0:
                status = _color("No AI context", Colors.RED)
            elif score.overall_level == 1:
                status = _color("Basic", Colors.YELLOW)
            elif score.overall_level == 2:
                status = _color("Comprehensive", Colors.CYAN)
            elif score.overall_level == 3:
                status = _color("Advanced", Colors.GREEN)
            else:
                status = _color("Frontier", Colors.BLUE)

            print(f"  {name:<30} {level:<10} {score_str:<10} {status}", file=output)
            level_counts[score.overall_level] += 1

        print(file=output)
        print(_color("  Distribution:", Colors.BOLD), file=output)
        total = len(scores)
        for level_num in range(5):
            count = level_counts[level_num]
            pct = count / total * 100 if total > 0 else 0
            bar_width = int(pct / 5)
            bar = "█" * bar_width + "░" * (20 - bar_width)
            print(f"    Level {level_num}: [{bar}] {count} repos ({pct:.1f}%)", file=output)

        print(file=output)
        print(_color(f"{'='*70}", Colors.DIM), file=output)
        print(file=output)


class JsonReporter:
    """Report results as JSON."""

    def __init__(self, indent: int = 2):
        self.indent = indent

    def _score_to_dict(self, score: RepoScore) -> dict:
        """Convert a RepoScore to a JSON-serializable dict."""

        return {
            "repo_path": score.repo_path,
            "repo_name": score.repo_name,
            "scan_time": score.scan_time.isoformat(),
            "overall_level": score.overall_level,
            "overall_score": round(score.overall_score, 2),
            "level_scores": {
                str(level): {
                    "name": ls.name,
                    "description": ls.description,
                    "file_count": ls.file_count,
                    "substantive_file_count": ls.substantive_file_count,
                    "coverage_percent": round(ls.coverage_percent, 2),
                    "matched_files": [
                        {
                            "path": f.path,
                            "size_bytes": f.size_bytes,
                            "is_substantive": f.is_substantive,
                        }
                        for f in ls.matched_files
                    ],
                    "matched_directories": ls.matched_directories,
                }
                for level, ls in score.level_scores.items()
            },
            "recommendations": score.recommendations,
        }

    def report_single(self, score: RepoScore, output: TextIO = sys.stdout) -> None:
        """Report a single repository score as JSON."""

        json.dump(self._score_to_dict(score), output, indent=self.indent)
        print(file=output)

    def report_multiple(self, scores: List[RepoScore], output: TextIO = sys.stdout) -> None:
        """Report multiple repository scores as JSON."""

        result = {
            "scan_time": datetime.now().isoformat(),
            "total_repos": len(scores),
            "distribution": {
                f"level_{i}": sum(1 for s in scores if s.overall_level == i)
                for i in range(5)
            },
            "average_score": round(
                sum(s.overall_score for s in scores) / len(scores) if scores else 0,
                2,
            ),
            "repos": [self._score_to_dict(s) for s in scores],
        }
        json.dump(result, output, indent=self.indent)
        print(file=output)


class MarkdownReporter:
    """Report results as Markdown."""

    def report_single(self, score: RepoScore, output: TextIO = sys.stdout) -> None:
        """Report a single repository score as Markdown."""

        print(f"# AI Proficiency Report: {score.repo_name}", file=output)
        print(file=output)
        print(f"**Scan Date:** {score.scan_time.strftime('%Y-%m-%d %H:%M')}", file=output)
        print(file=output)

        print("## Summary", file=output)
        print(file=output)

        level_name = (
            "Level 0: No Context Engineering"
            if score.overall_level == 0
            else score.level_scores[score.overall_level].name
        )
        print(f"- **Overall Level:** {level_name}", file=output)
        print(f"- **Overall Score:** {score.overall_score:.1f}/100", file=output)
        print(file=output)

        print("## Level Breakdown", file=output)
        print(file=output)
        print("| Level | Coverage | Files | Status |", file=output)
        print("|-------|----------|-------|--------|", file=output)

        for level_num in sorted(score.level_scores.keys()):
            ls = score.level_scores[level_num]
            achieved = "✓" if level_num <= score.overall_level and score.overall_level > 0 else "○"
            print(
                f"| {ls.name} | {ls.coverage_percent:.1f}% | "
                f"{ls.substantive_file_count} | {achieved} |",
                file=output,
            )

        print(file=output)

        print("## Detected Files", file=output)
        print(file=output)

        for level_num in sorted(score.level_scores.keys()):
            ls = score.level_scores[level_num]
            if ls.matched_files:
                print(f"### {ls.name}", file=output)
                print(file=output)
                for f in ls.matched_files:
                    status = "●" if f.is_substantive else "○"
                    print(f"- {status} `{f.path}`", file=output)
                print(file=output)

        if score.recommendations:
            print("## Recommendations", file=output)
            print(file=output)
            for i, rec in enumerate(score.recommendations, 1):
                print(f"{i}. {rec}", file=output)
            print(file=output)

    def report_multiple(self, scores: List[RepoScore], output: TextIO = sys.stdout) -> None:
        """Report multiple repository scores as Markdown."""

        print("# AI Proficiency Summary", file=output)
        print(file=output)
        print(f"**Scan Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}", file=output)
        print(f"**Total Repositories:** {len(scores)}", file=output)
        print(file=output)

        print("## Distribution", file=output)
        print(file=output)
        print("| Level | Count | Percentage |", file=output)
        print("|-------|-------|------------|", file=output)

        total = len(scores)
        for level_num in range(5):
            count = sum(1 for s in scores if s.overall_level == level_num)
            pct = count / total * 100 if total > 0 else 0
            print(f"| Level {level_num} | {count} | {pct:.1f}% |", file=output)

        print(file=output)

        print("## Repositories", file=output)
        print(file=output)
        print("| Repository | Level | Score | Status |", file=output)
        print("|------------|-------|-------|--------|", file=output)

        sorted_scores = sorted(
            scores,
            key=lambda s: (s.overall_level, s.overall_score),
            reverse=True,
        )
        for score in sorted_scores:
            status = ["No AI context", "Basic", "Comprehensive", "Advanced", "Frontier"][
                score.overall_level
            ]
            print(
                f"| {score.repo_name} | Level {score.overall_level} | "
                f"{score.overall_score:.1f} | {status} |",
                file=output,
            )

        print(file=output)


class CsvReporter:
    """Report results as CSV."""

    def report_multiple(self, scores: List[RepoScore], output: TextIO = sys.stdout) -> None:
        """Report multiple repository scores as CSV."""

        print(
            "repo_name,repo_path,overall_level,overall_score,level_1_coverage,level_2_coverage,level_3_coverage,level_4_coverage",
            file=output,
        )

        for score in scores:
            coverages = [
                score.level_scores.get(i, type("obj", (object,), {"coverage_percent": 0})).coverage_percent
                for i in range(1, 5)
            ]
            print(
                f'"{score.repo_name}","{score.repo_path}",{score.overall_level},'
                f"{score.overall_score:.2f},{coverages[0]:.2f},{coverages[1]:.2f},"
                f"{coverages[2]:.2f},{coverages[3]:.2f}",
                file=output,
            )


def get_reporter(format: str, verbose: bool = False):
    """Get a reporter for the specified format."""

    reporters = {
        "terminal": TerminalReporter(verbose=verbose),
        "json": JsonReporter(),
        "markdown": MarkdownReporter(),
        "csv": CsvReporter(),
    }
    return reporters.get(format, TerminalReporter(verbose=verbose))
