"""
Report generation for AI proficiency measurement.

Outputs results in various formats: terminal, JSON, markdown, CSV.
Uses levels 1-8 aligned with Steve Yegge's 8-stage model.
"""

import json
import sys
from datetime import datetime
from typing import List, TextIO, Union

from .scanner import RepoScore, RepoScanner


# Terminal colors
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[35m"
    PURPLE = "\033[35;1m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"


# Proper display names for AI tools (handles special capitalization like "GitHub")
TOOL_DISPLAY_NAMES = {
    "claude-code": "Claude Code",
    "github-copilot": "GitHub Copilot",
    "cursor": "Cursor",
    "openai-codex": "OpenAI Codex",
}


def _format_tool_name(tool: str) -> str:
    """Format a tool ID into a display name."""
    return TOOL_DISPLAY_NAMES.get(tool, tool.replace("-", " ").title())


def _supports_color() -> bool:
    """Check if terminal supports color."""

    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def _color(text: str, color: str) -> str:
    """Apply color if supported."""

    if _supports_color():
        return f"{color}{text}{Colors.ENDC}"
    return text


def _level_color(level: int) -> str:
    """Get color for a level (1-8)."""

    colors = {
        1: Colors.RED,       # Zero AI
        2: Colors.YELLOW,    # Basic
        3: Colors.CYAN,      # Comprehensive
        4: Colors.GREEN,     # Advanced
        5: Colors.BLUE,      # Multi-Agent
        6: Colors.MAGENTA,   # Fleet Ready
        7: Colors.PURPLE,    # Agent Fleet
        8: Colors.BOLD,      # Frontier
    }
    return colors.get(level, Colors.ENDC)


def _level_status(level: int) -> str:
    """Get status label for a level (1-8)."""

    statuses = {
        1: "Zero AI",
        2: "Basic",
        3: "Comprehensive",
        4: "Advanced",
        5: "Multi-Agent",
        6: "Fleet Ready",
        7: "Agent Fleet",
        8: "Frontier",
    }
    return statuses.get(level, "Unknown")


def _progress_bar(percent: float, width: int = 20) -> str:
    """Create a simple progress bar."""

    filled = int(width * percent / 100)
    empty = width - filled
    return f"[{'█' * filled}{'░' * empty}]"


def _progress_bar_with_threshold(coverage: float, threshold: float, width: int = 20) -> str:
    """Create a progress bar with threshold marker.

    The bar shows:
    - Filled blocks up to current coverage
    - A '|' marker at the threshold position
    - Empty blocks for remaining space
    """
    # Calculate positions (scale to bar width)
    threshold_pos = int(threshold / 100 * width)
    coverage_pos = int(min(coverage, 100) / 100 * width)

    bar_chars = []
    for i in range(width):
        if i == threshold_pos and coverage_pos <= threshold_pos:
            # Show threshold marker when not yet reached
            bar_chars.append("|")
        elif i < coverage_pos:
            bar_chars.append("█")
        elif i == threshold_pos:
            # Threshold marker (already passed)
            bar_chars.append("|")
        else:
            bar_chars.append("░")

    return f"[{''.join(bar_chars)}]"


class TerminalReporter:
    """Report results to terminal with colors and formatting."""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose

    def _print_level_breakdown(
        self,
        score: RepoScore,
        achieved_level: int,
        thresholds: dict,
        output: TextIO,
        show_files: bool = True,
    ) -> None:
        """Print level breakdown with thresholds."""
        for level_num in sorted(score.level_scores.keys()):
            level_score = score.level_scores[level_num]
            achieved = "✓" if level_num <= achieved_level else "○"
            achieved_color = Colors.GREEN if achieved == "✓" else Colors.DIM

            coverage = level_score.coverage_percent
            threshold = thresholds.get(level_num)

            # Use threshold-aware progress bar for levels 3+
            if threshold is not None:
                bar = _progress_bar_with_threshold(coverage, threshold)
                # Show coverage/threshold and status
                if coverage >= threshold:
                    status_str = _color("✓", Colors.GREEN)
                    pct_display = f"{coverage:.1f}%/{threshold}%"
                else:
                    gap = threshold - coverage
                    status_str = _color(f"needs +{gap:.1f}%", Colors.YELLOW)
                    pct_display = f"{coverage:.1f}%/{threshold}%"
            else:
                bar = _progress_bar(coverage)
                status_str = ""
                pct_display = f"{coverage:.1f}%"

            print(f"    {_color(achieved, achieved_color)} {level_score.name}", file=output)
            print(
                f"      {bar} {pct_display} {status_str} ({level_score.substantive_file_count} files)",
                file=output,
            )

            if show_files and self.verbose and level_score.matched_files:
                for f in level_score.matched_files[:5]:
                    status = "●" if f.is_substantive else "○"
                    print(f"        {_color(status, Colors.DIM)} {f.path}", file=output)
                if len(level_score.matched_files) > 5:
                    print(
                        f"        {_color(f'... and {len(level_score.matched_files) - 5} more', Colors.DIM)}",
                        file=output,
                    )
            print(file=output)

    def report_single(self, score: RepoScore, output: TextIO = sys.stdout) -> None:
        """Report a single repository score."""

        print(file=output)
        print(_color(f"{'='*60}", Colors.DIM), file=output)
        print(_color(f" AI Proficiency Report: {score.repo_name}", Colors.BOLD), file=output)
        print(_color(f"{'='*60}", Colors.DIM), file=output)
        print(file=output)

        # Overall level - show both custom and default if custom thresholds are used
        has_custom_thresholds = score.default_level is not None

        if has_custom_thresholds:
            # Show custom level
            custom_level_text = score.level_scores[score.overall_level].name
            print(
                f"  Overall Level (Custom): {_color(custom_level_text, _level_color(score.overall_level))}",
                file=output,
            )
            # Show default level
            default_level_text = score.level_scores[score.default_level].name
            print(
                f"  Overall Level (Default): {_color(default_level_text, _level_color(score.default_level))}",
                file=output,
            )
        else:
            # Show single level
            level_text = score.level_scores[score.overall_level].name
            print(
                f"  Overall Level: {_color(level_text, _level_color(score.overall_level))}",
                file=output,
            )

        # Show score (same for both custom and default - objective measurement)
        print(
            f"  Overall Score: {_color(f'{score.overall_score:.1f}/100', Colors.BOLD)}",
            file=output,
        )

        # Show detected tools
        if score.detected_tools:
            tool_names = ", ".join(_format_tool_name(t) for t in score.detected_tools)
            print(f"  AI Tools: {_color(tool_names, Colors.CYAN)}", file=output)

            # Show if config was loaded
            if score.config and score.config.from_file:
                print(f"  Config: {_color('.ai-proficiency.yaml loaded', Colors.DIM)}", file=output)

        # Show custom thresholds indicator
        if score.default_level is not None and score.config and score.config.thresholds:
            threshold_vals = ", ".join(
                f"L{k}:{v}%" for k, v in sorted(score.config.thresholds.items())
            )
            print(f"  Thresholds: {_color(f'Custom ({threshold_vals})', Colors.MAGENTA)}", file=output)

        print(file=output)

        # Level breakdown with custom thresholds (if defined)
        default_thresholds = RepoScanner.DEFAULT_THRESHOLDS
        if has_custom_thresholds:
            print(_color("  Level Breakdown (Custom Thresholds):", Colors.BOLD), file=output)
        else:
            print(_color("  Level Breakdown:", Colors.BOLD), file=output)
        print(file=output)

        self._print_level_breakdown(
            score, score.overall_level, score.effective_thresholds, output
        )

        # Show default threshold breakdown when custom thresholds are in use
        if has_custom_thresholds:
            print(_color("  Level Breakdown (Default Thresholds):", Colors.BOLD), file=output)
            print(file=output)
            self._print_level_breakdown(
                score, score.default_level, default_thresholds, output, show_files=False
            )

        # Cross-references section
        xref = score.cross_references
        if xref and (xref.total_count > 0 or xref.quality_scores):
            print(_color("  Cross-References & Quality:", Colors.BOLD), file=output)
            print(file=output)

            if xref.total_count > 0:
                print(f"    References: {xref.total_count} found in {xref.source_files_scanned} files", file=output)
                print(f"    Unique targets: {len(xref.unique_targets)}", file=output)
                resolved_pct = f"{xref.resolution_rate:.0f}%"
                resolved_color = Colors.GREEN if xref.resolution_rate >= 75 else Colors.YELLOW
                print(f"    Resolved: {xref.resolved_count}/{xref.total_count} ({_color(resolved_pct, resolved_color)})", file=output)

            if xref.quality_scores:
                print(file=output)
                print(f"    Content Quality:", file=output)
                for file_path, quality in xref.quality_scores.items():
                    q_color = Colors.GREEN if quality.quality_score >= 6 else (Colors.YELLOW if quality.quality_score >= 3 else Colors.RED)
                    # Show indicators as compact symbols
                    indicators = []
                    if quality.has_sections:
                        indicators.append("§")  # sections
                    if quality.has_specific_paths:
                        indicators.append("⌘")  # paths
                    if quality.has_tool_commands:
                        indicators.append("$")  # commands
                    if quality.has_constraints:
                        indicators.append("!")  # constraints
                    if quality.commit_count >= 3:
                        indicators.append(f"↻{quality.commit_count}")  # commits
                    indicator_str = " ".join(indicators) if indicators else "minimal"
                    print(f"      {file_path}: {_color(f'{quality.quality_score:.1f}/10', q_color)} ({quality.word_count} words) [{indicator_str}]", file=output)

                # Add quality scoring legend
                print(file=output)
                print(f"    {_color('Quality indicators:', Colors.DIM)}", file=output)
                print(f"      {_color('§', Colors.DIM)}=sections  {_color('⌘', Colors.DIM)}=paths  {_color('$', Colors.DIM)}=commands  {_color('!', Colors.DIM)}=constraints  {_color('↻N', Colors.DIM)}=commits", file=output)

            if xref.bonus_points > 0:
                print(file=output)
                print(f"    {_color(f'Bonus: +{xref.bonus_points:.1f} points', Colors.GREEN)}", file=output)

            # Show detailed references in verbose mode
            if self.verbose and xref.references:
                print(file=output)
                print(f"    {_color('References:', Colors.DIM)}", file=output)
                for ref in xref.references[:10]:
                    status = "✓" if ref.is_resolved else "✗"
                    status_color = Colors.GREEN if ref.is_resolved else Colors.RED
                    print(f"      {_color(status, status_color)} {ref.source_file}:{ref.line_number} -> {ref.target}", file=output)
                if len(xref.references) > 10:
                    print(f"      {_color(f'... and {len(xref.references) - 10} more', Colors.DIM)}", file=output)

            print(file=output)

        # Validation warnings section (Improvements 2-5)
        if score.validation and score.validation.warnings:
            print(_color("  Validation Warnings:", Colors.BOLD), file=output)
            print(file=output)

            for warning in score.validation.warnings[:10]:
                # Color code by warning type
                if warning.startswith("STALE:"):
                    print(f"    {_color('⏰', Colors.YELLOW)} {warning}", file=output)
                elif warning.startswith("TEMPLATE:"):
                    print(f"    {_color('📋', Colors.YELLOW)} {warning}", file=output)
                elif warning.startswith("MISSING REF:"):
                    print(f"    {_color('⚠️', Colors.RED)} {warning}", file=output)
                elif warning.startswith("INVALID SKILL:"):
                    print(f"    {_color('❌', Colors.RED)} {warning}", file=output)
                else:
                    print(f"    → {warning}", file=output)

            if len(score.validation.warnings) > 10:
                print(f"    {_color(f'... and {len(score.validation.warnings) - 10} more warnings', Colors.DIM)}", file=output)

            if score.validation.validation_penalty > 0:
                print(file=output)
                print(f"    {_color(f'Penalty: -{score.validation.validation_penalty:.1f} points', Colors.RED)}", file=output)

            print(file=output)

        # Behavioral analysis section (Level 6-8 concrete indicators)
        if score.validation and score.validation.behavioral:
            behavioral = score.validation.behavioral
            has_any = (
                (behavioral.ci_integration and behavioral.ci_integration.has_ci_agents) or
                (behavioral.handoffs and behavioral.handoffs.valid) or
                (behavioral.outcomes and behavioral.outcomes.has_measured_outcomes)
            )

            if has_any or self.verbose:
                print(_color("  Behavioral Indicators (Levels 6-8):", Colors.BOLD), file=output)
                print(file=output)

                # Level 6: CI/CD Integration
                if behavioral.ci_integration:
                    ci = behavioral.ci_integration
                    status = "✓" if ci.has_ci_agents else "○"
                    status_color = Colors.GREEN if ci.has_ci_agents else Colors.DIM
                    print(f"    {_color(status, status_color)} CI/CD Agent Integration (L6)", file=output)
                    if ci.has_ci_agents and ci.agent_patterns_found:
                        patterns = ", ".join(ci.agent_patterns_found[:3])
                        print(f"      {_color(f'Found: {patterns}', Colors.DIM)}", file=output)

                # Level 7: Agent Handoffs
                if behavioral.handoffs:
                    ho = behavioral.handoffs
                    status = "✓" if ho.valid else "○"
                    status_color = Colors.GREEN if ho.valid else Colors.DIM
                    print(f"    {_color(status, status_color)} Agent Handoffs (L7): {ho.agent_count} agents", file=output)
                    if ho.valid and ho.cross_references:
                        refs = ", ".join(ho.cross_references[:2])
                        print(f"      {_color(f'Handoffs: {refs}', Colors.DIM)}", file=output)

                # Level 8: Measured Outcomes
                if behavioral.outcomes:
                    out = behavioral.outcomes
                    status = "✓" if out.has_measured_outcomes else "○"
                    status_color = Colors.GREEN if out.has_measured_outcomes else Colors.DIM
                    indicators = [k for k, v in out.indicators.items() if v]
                    print(f"    {_color(status, status_color)} Measured Outcomes (L8)", file=output)
                    if indicators:
                        ind_str = ", ".join(indicators[:3])
                        print(f"      {_color(f'Indicators: {ind_str}', Colors.DIM)}", file=output)

                print(file=output)

        # Recommendations
        if score.recommendations:
            print(_color("  Recommendations:", Colors.BOLD), file=output)
            print(file=output)
            for rec in score.recommendations:
                print(f"    → {rec}", file=output)
            print(file=output)

        # Add guidance if many files detected but low level
        total_files = sum(ls.file_count for ls in score.level_scores.values())
        if total_files > 30 and score.overall_level <= 2:
            print(_color("  Note:", Colors.BOLD), file=output)
            print(f"    You have {total_files} documentation files detected but a low level score.", file=output)
            print(f"    This likely means your team uses different file names/structures.", file=output)
            print(f"    Consider customizing patterns in config.py for your organization.", file=output)
            print(f"    Run with -v to see all detected files.", file=output)
            print(file=output)

        print(_color(f"{'='*60}", Colors.DIM), file=output)
        print(file=output)

    def report_multiple(self, scores: List[RepoScore], output: TextIO = sys.stdout) -> None:
        """Report multiple repository scores as a summary table."""

        if not scores:
            print("No repositories scanned.", file=output)
            return

        print(file=output)
        print(_color(f"{'='*80}", Colors.DIM), file=output)
        print(_color(" AI Proficiency Summary", Colors.BOLD), file=output)
        print(_color(f"{'='*80}", Colors.DIM), file=output)
        print(file=output)

        # Sort by level descending, then score descending
        sorted_scores = sorted(
            scores,
            key=lambda s: (s.overall_level, s.overall_score),
            reverse=True,
        )

        # Header with bonus column
        print(f"  {'Repository':<28} {'Level':<10} {'Score':<8} {'Bonus':<8} {'Quality':<8} {'Status'}", file=output)
        print(f"  {'-'*28} {'-'*10} {'-'*8} {'-'*8} {'-'*8} {'-'*12}", file=output)

        # Distribution counters (levels 1-8)
        level_counts = {i: 0 for i in range(1, 9)}

        # Aggregate cross-ref stats
        total_refs = 0
        total_quality = 0.0
        repos_with_quality = 0

        for score in sorted_scores:
            name = score.repo_name[:26] + ".." if len(score.repo_name) > 28 else score.repo_name
            level = f"Level {score.overall_level}"
            score_str = f"{score.overall_score:.1f}"

            # Cross-reference bonus and quality
            bonus_str = "-"
            quality_str = "-"
            if score.cross_references:
                xref = score.cross_references
                if xref.bonus_points > 0:
                    bonus_str = f"+{xref.bonus_points:.1f}"
                total_refs += xref.total_count
                if xref.quality_scores:
                    avg_quality = sum(q.quality_score for q in xref.quality_scores.values()) / len(xref.quality_scores)
                    quality_str = f"{avg_quality:.1f}/10"
                    total_quality += avg_quality
                    repos_with_quality += 1

            status_text = _level_status(score.overall_level)
            status = _color(status_text, _level_color(score.overall_level))

            print(f"  {name:<28} {level:<10} {score_str:<8} {bonus_str:<8} {quality_str:<8} {status}", file=output)
            level_counts[score.overall_level] += 1

        print(file=output)
        print(_color("  Distribution:", Colors.BOLD), file=output)
        total = len(scores)
        for level_num in range(1, 9):
            count = level_counts[level_num]
            pct = count / total * 100 if total > 0 else 0
            bar_width = int(pct / 5)
            bar = "█" * bar_width + "░" * (20 - bar_width)
            print(f"    Level {level_num}: [{bar}] {count} repos ({pct:.1f}%)", file=output)

        # Aggregate cross-reference stats
        if total_refs > 0 or repos_with_quality > 0:
            print(file=output)
            print(_color("  Cross-References:", Colors.BOLD), file=output)
            print(f"    Total references: {total_refs} across {total} repos", file=output)
            if repos_with_quality > 0:
                avg_org_quality = total_quality / repos_with_quality
                print(f"    Average quality: {avg_org_quality:.1f}/10 ({repos_with_quality} repos with AI instruction files)", file=output)

        print(file=output)
        print(_color(f"{'='*80}", Colors.DIM), file=output)
        print(file=output)


class JsonReporter:
    """Report results as JSON."""

    def __init__(self, indent: int = 2):
        self.indent = indent

    def _score_to_dict(self, score: RepoScore) -> dict:
        """Convert a RepoScore to a JSON-serializable dict."""

        result = {
            "repo_path": score.repo_path,
            "repo_name": score.repo_name,
            "scan_time": score.scan_time.isoformat(),
            "overall_level": score.overall_level,
            "overall_score": round(score.overall_score, 2),
            "detected_tools": score.detected_tools,
            "config_loaded": score.config.from_file if score.config else False,
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

        # Add custom thresholds if config loaded
        if score.config and score.config.thresholds:
            result["custom_thresholds"] = score.config.thresholds

        # Add cross-references if present
        if score.cross_references:
            xref = score.cross_references
            result["cross_references"] = {
                "total_count": xref.total_count,
                "source_files_scanned": xref.source_files_scanned,
                "unique_targets": list(xref.unique_targets),
                "resolved_count": xref.resolved_count,
                "resolution_rate": round(xref.resolution_rate, 2),
                "bonus_points": round(xref.bonus_points, 2),
                "quality_scoring_legend": {
                    "max_score": 10,
                    "indicators": {
                        "sections": {"max_points": 2, "description": "Markdown headers (##) for organization"},
                        "paths": {"max_points": 2, "description": "Concrete file/directory paths (/src/, ~/)"},
                        "commands": {"max_points": 2, "description": "CLI commands in backticks"},
                        "constraints": {"max_points": 2, "description": "Directive language (never, avoid, don't, do not, must not, always, required)"},
                        "substance": {"max_points": 2, "description": "Word count (200+ words = 2 pts, 50-200 = 1 pt)"},
                        "commits": {"max_points": 2, "description": "Git commit history (5+ commits = 2 pts, 3-4 = 1 pt)"},
                    },
                },
                "references": [
                    {
                        "source_file": ref.source_file,
                        "target": ref.target,
                        "reference_type": ref.reference_type,
                        "line_number": ref.line_number,
                        "is_resolved": ref.is_resolved,
                    }
                    for ref in xref.references
                ],
                "quality_scores": {
                    path: {
                        "has_sections": q.has_sections,
                        "has_specific_paths": q.has_specific_paths,
                        "has_tool_commands": q.has_tool_commands,
                        "has_constraints": q.has_constraints,
                        "has_cross_refs": q.has_cross_refs,
                        "word_count": q.word_count,
                        "section_count": q.section_count,
                        "commit_count": q.commit_count,
                        "quality_score": round(q.quality_score, 2),
                    }
                    for path, q in xref.quality_scores.items()
                },
            }

        # Add validation results if present (Improvements 2-5)
        if score.validation:
            v = score.validation
            result["validation"] = {
                "validation_penalty": round(v.validation_penalty, 2),
                "warnings": v.warnings[:20],  # Limit to 20 warnings
                "freshness": {
                    path: {
                        "last_modified": f.last_modified.isoformat() if f.last_modified else None,
                        "days_since_update": f.days_since_update,
                        "days_behind_code": f.days_behind_code,
                        "is_stale": f.is_stale,
                        "staleness_level": f.staleness_level,
                    }
                    for path, f in v.freshness_scores.items()
                },
                "alignment": {
                    path: {
                        "total_references": a.total_references,
                        "existing_count": a.existing_count,
                        "missing_paths": a.missing_paths[:10],  # Limit
                        "alignment_ratio": round(a.alignment_ratio, 2),
                    }
                    for path, a in v.alignment_scores.items()
                },
                "templates": {
                    path: {
                        "is_template": t.is_template,
                        "markers_found": t.markers_found,
                        "template_score": round(t.template_score, 2),
                    }
                    for path, t in v.template_analyses.items()
                },
                "stale_references": [
                    {
                        "path": ref.path,
                        "status": ref.status,
                        "source_file": ref.source_file,
                    }
                    for ref in v.stale_references[:20]  # Limit
                ],
                "skill_validations": {
                    path: {
                        "valid_file_refs": s.valid_file_refs,
                        "invalid_file_refs": s.invalid_file_refs,
                        "is_valid": s.is_valid,
                    }
                    for path, s in v.skill_validations.items()
                },
            }

            # Add behavioral analysis if present
            if v.behavioral:
                b = v.behavioral
                result["validation"]["behavioral"] = {
                    "level_6_ready": b.level_6_ready,
                    "level_7_ready": b.level_7_ready,
                    "level_8_ready": b.level_8_ready,
                }
                if b.ci_integration:
                    result["validation"]["behavioral"]["ci_integration"] = {
                        "has_ci_agents": b.ci_integration.has_ci_agents,
                        "workflow_files": b.ci_integration.workflow_files,
                        "agent_patterns_found": b.ci_integration.agent_patterns_found,
                    }
                if b.handoffs:
                    result["validation"]["behavioral"]["handoffs"] = {
                        "valid": b.handoffs.valid,
                        "agent_count": b.handoffs.agent_count,
                        "has_handoff_docs": b.handoffs.has_handoff_docs,
                        "cross_references": b.handoffs.cross_references,
                        "reason": b.handoffs.reason,
                    }
                if b.outcomes:
                    result["validation"]["behavioral"]["outcomes"] = {
                        "has_measured_outcomes": b.outcomes.has_measured_outcomes,
                        "indicators": b.outcomes.indicators,
                    }

        return result

    def report_single(self, score: RepoScore, output: TextIO = sys.stdout) -> None:
        """Report a single repository score as JSON."""

        json.dump(self._score_to_dict(score), output, indent=self.indent)
        print(file=output)

    def report_multiple(self, scores: List[RepoScore], output: TextIO = sys.stdout) -> None:
        """Report multiple repository scores as JSON."""

        # Calculate aggregate cross-reference stats
        total_refs = 0
        total_resolved = 0
        total_quality = 0.0
        repos_with_quality = 0
        total_bonus = 0.0

        for score in scores:
            if score.cross_references:
                xref = score.cross_references
                total_refs += xref.total_count
                total_resolved += xref.resolved_count
                total_bonus += xref.bonus_points
                if xref.quality_scores:
                    avg_q = sum(q.quality_score for q in xref.quality_scores.values()) / len(xref.quality_scores)
                    total_quality += avg_q
                    repos_with_quality += 1

        result = {
            "scan_time": datetime.now().isoformat(),
            "total_repos": len(scores),
            "distribution": {
                f"level_{i}": sum(1 for s in scores if s.overall_level == i)
                for i in range(1, 9)
            },
            "average_score": round(
                sum(s.overall_score for s in scores) / len(scores) if scores else 0,
                2,
            ),
            "cross_references_summary": {
                "total_references": total_refs,
                "total_resolved": total_resolved,
                "repos_with_ai_instructions": repos_with_quality,
                "average_quality": round(total_quality / repos_with_quality, 2) if repos_with_quality > 0 else 0,
                "total_bonus_points": round(total_bonus, 2),
            },
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

        level_name = score.level_scores[score.overall_level].name
        print(f"- **Overall Level:** {level_name}", file=output)
        print(f"- **Overall Score:** {score.overall_score:.1f}/100", file=output)

        # Show detected tools
        if score.detected_tools:
            tool_names = ", ".join(_format_tool_name(t) for t in score.detected_tools)
            print(f"- **AI Tools Detected:** {tool_names}", file=output)
            if score.config and score.config.from_file:
                print(f"- **Config:** `.ai-proficiency.yaml` loaded", file=output)

        print(file=output)

        print("## Level Breakdown", file=output)
        print(file=output)
        print("| Level | Coverage | Files | Status |", file=output)
        print("|-------|----------|-------|--------|", file=output)

        for level_num in sorted(score.level_scores.keys()):
            ls = score.level_scores[level_num]
            achieved = "✓" if level_num <= score.overall_level else "○"
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

        # Cross-references section
        xref = score.cross_references
        if xref and (xref.total_count > 0 or xref.quality_scores):
            print("## Cross-References & Quality", file=output)
            print(file=output)

            if xref.total_count > 0:
                print(f"- **References Found:** {xref.total_count}", file=output)
                print(f"- **Files Scanned:** {xref.source_files_scanned}", file=output)
                print(f"- **Unique Targets:** {len(xref.unique_targets)}", file=output)
                print(f"- **Resolution Rate:** {xref.resolution_rate:.0f}%", file=output)

            if xref.bonus_points > 0:
                print(f"- **Bonus Points:** +{xref.bonus_points:.1f}", file=output)
            print(file=output)

            if xref.quality_scores:
                print("### Content Quality", file=output)
                print(file=output)
                print("| File | Score | Words | Commits | Sections | Paths | Commands | Constraints |", file=output)
                print("|------|-------|-------|---------|----------|-------|----------|-------------|", file=output)
                for path, q in xref.quality_scores.items():
                    print(
                        f"| `{path}` | {q.quality_score:.1f}/10 | {q.word_count} | {q.commit_count} | "
                        f"{'✓' if q.has_sections else '○'} | {'✓' if q.has_specific_paths else '○'} | "
                        f"{'✓' if q.has_tool_commands else '○'} | {'✓' if q.has_constraints else '○'} |",
                        file=output,
                    )
                print(file=output)

                # Add quality scoring explanation
                print("**Quality Scoring (0-10 points):**", file=output)
                print("- **Sections** (0-2 pts): Markdown headers (`##`) for organization", file=output)
                print("- **Paths** (0-2 pts): Concrete file/directory paths (`/src/`, `~/config/`)", file=output)
                print("- **Commands** (0-2 pts): CLI commands in backticks (`` `npm test` ``)", file=output)
                print("- **Constraints** (0-2 pts): Directive language (\"never\", \"avoid\", \"don't\", \"do not\", \"must not\", \"always\", \"required\")", file=output)
                print("- **Substance** (0-2 pts): Word count (200+ words = 2 pts)", file=output)
                print("- **Commits** (0-2 pts): Git history (5+ commits = 2 pts, 3-4 = 1 pt)", file=output)
                print(file=output)

            if xref.references:
                print("### Reference Details", file=output)
                print(file=output)
                print("| Source | Target | Type | Status |", file=output)
                print("|--------|--------|------|--------|", file=output)
                for ref in xref.references[:20]:
                    status = "Resolved" if ref.is_resolved else "Missing"
                    print(f"| `{ref.source_file}:{ref.line_number}` | `{ref.target}` | {ref.reference_type} | {status} |", file=output)
                if len(xref.references) > 20:
                    print(f"\n*...and {len(xref.references) - 20} more references*", file=output)
                print(file=output)

        # Validation warnings section (Improvements 2-5)
        if score.validation and (score.validation.warnings or score.validation.behavioral):
            print("## Validation & Freshness", file=output)
            print(file=output)

            if score.validation.warnings:
                print("### Warnings", file=output)
                print(file=output)
                for warning in score.validation.warnings[:15]:
                    if warning.startswith("STALE:"):
                        print(f"- :hourglass: {warning}", file=output)
                    elif warning.startswith("TEMPLATE:"):
                        print(f"- :clipboard: {warning}", file=output)
                    elif warning.startswith("MISSING REF:"):
                        print(f"- :warning: {warning}", file=output)
                    elif warning.startswith("INVALID SKILL:"):
                        print(f"- :x: {warning}", file=output)
                    else:
                        print(f"- {warning}", file=output)

                if len(score.validation.warnings) > 15:
                    print(f"\n*...and {len(score.validation.warnings) - 15} more warnings*", file=output)
                print(file=output)

                if score.validation.validation_penalty > 0:
                    print(f"**Penalty:** -{score.validation.validation_penalty:.1f} points", file=output)
                    print(file=output)

            # Freshness summary
            if score.validation.freshness_scores:
                print("### Freshness Status", file=output)
                print(file=output)
                print("| File | Days Behind Code | Status |", file=output)
                print("|------|-----------------|--------|", file=output)
                for path, f in score.validation.freshness_scores.items():
                    status_emoji = ":white_check_mark:" if f.staleness_level == "fresh" else (":hourglass:" if f.staleness_level == "aging" else ":warning:")
                    print(f"| `{path}` | {f.days_behind_code} | {status_emoji} {f.staleness_level} |", file=output)
                print(file=output)

            # Behavioral indicators (Level 6-8)
            if score.validation.behavioral:
                b = score.validation.behavioral
                print("### Behavioral Indicators (Levels 6-8)", file=output)
                print(file=output)
                print("| Indicator | Status | Details |", file=output)
                print("|-----------|--------|---------|", file=output)

                # L6: CI/CD
                if b.ci_integration:
                    ci = b.ci_integration
                    status = ":white_check_mark:" if ci.has_ci_agents else ":o:"
                    details = ", ".join(ci.agent_patterns_found[:2]) if ci.agent_patterns_found else "Not detected"
                    print(f"| CI/CD Agent Integration (L6) | {status} | {details} |", file=output)

                # L7: Handoffs
                if b.handoffs:
                    ho = b.handoffs
                    status = ":white_check_mark:" if ho.valid else ":o:"
                    details = f"{ho.agent_count} agents" + (", " + ho.cross_references[0] if ho.cross_references else "")
                    print(f"| Agent Handoffs (L7) | {status} | {details} |", file=output)

                # L8: Outcomes
                if b.outcomes:
                    out = b.outcomes
                    status = ":white_check_mark:" if out.has_measured_outcomes else ":o:"
                    indicators = [k for k, v in out.indicators.items() if v]
                    details = ", ".join(indicators[:2]) if indicators else "Not detected"
                    print(f"| Measured Outcomes (L8) | {status} | {details} |", file=output)

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
        for level_num in range(1, 9):
            count = sum(1 for s in scores if s.overall_level == level_num)
            pct = count / total * 100 if total > 0 else 0
            print(f"| Level {level_num} | {count} | {pct:.1f}% |", file=output)

        print(file=output)

        print("## Repositories", file=output)
        print(file=output)
        print("| Repository | Level | Score | Bonus | Quality | Status |", file=output)
        print("|------------|-------|-------|-------|---------|--------|", file=output)

        sorted_scores = sorted(
            scores,
            key=lambda s: (s.overall_level, s.overall_score),
            reverse=True,
        )

        # Aggregate cross-ref stats
        total_refs = 0
        total_quality = 0.0
        repos_with_quality = 0

        for score in sorted_scores:
            status = _level_status(score.overall_level)

            # Cross-reference bonus and quality
            bonus_str = "-"
            quality_str = "-"
            if score.cross_references:
                xref = score.cross_references
                if xref.bonus_points > 0:
                    bonus_str = f"+{xref.bonus_points:.1f}"
                total_refs += xref.total_count
                if xref.quality_scores:
                    avg_quality = sum(q.quality_score for q in xref.quality_scores.values()) / len(xref.quality_scores)
                    quality_str = f"{avg_quality:.1f}/10"
                    total_quality += avg_quality
                    repos_with_quality += 1

            print(
                f"| {score.repo_name} | Level {score.overall_level} | "
                f"{score.overall_score:.1f} | {bonus_str} | {quality_str} | {status} |",
                file=output,
            )

        print(file=output)

        # Cross-reference aggregate stats
        if total_refs > 0 or repos_with_quality > 0:
            print("## Cross-References Summary", file=output)
            print(file=output)
            print(f"- **Total References:** {total_refs} across {total} repos", file=output)
            if repos_with_quality > 0:
                avg_org_quality = total_quality / repos_with_quality
                print(f"- **Average Quality:** {avg_org_quality:.1f}/10 ({repos_with_quality} repos with AI instruction files)", file=output)
            print(file=output)


class CsvReporter:
    """Report results as CSV."""

    def report_single(self, score: RepoScore, output: TextIO = sys.stdout) -> None:
        """Report a single repository score as CSV."""
        self.report_multiple([score], output)

    def report_multiple(self, scores: List[RepoScore], output: TextIO = sys.stdout) -> None:
        """Report multiple repository scores as CSV."""

        # Header with levels 1-8, cross-reference columns, and validation columns
        header = "repo_name,repo_path,overall_level,overall_score,bonus_points,avg_quality,ref_count,resolved_count,validation_penalty,has_stale_files,has_templates,warning_count,ci_agents,handoffs_valid,outcomes_valid"
        for i in range(1, 9):
            header += f",level_{i}_coverage"
        print(header, file=output)

        for score in scores:
            coverages = [
                score.level_scores.get(i, type("obj", (object,), {"coverage_percent": 0})).coverage_percent
                for i in range(1, 9)
            ]

            # Cross-reference data
            bonus = 0.0
            avg_quality = 0.0
            ref_count = 0
            resolved_count = 0
            if score.cross_references:
                xref = score.cross_references
                bonus = xref.bonus_points
                ref_count = xref.total_count
                resolved_count = xref.resolved_count
                if xref.quality_scores:
                    avg_quality = sum(q.quality_score for q in xref.quality_scores.values()) / len(xref.quality_scores)

            # Validation data
            validation_penalty = 0.0
            has_stale = False
            has_templates = False
            warning_count = 0
            ci_agents = False
            handoffs_valid = False
            outcomes_valid = False

            if score.validation:
                v = score.validation
                validation_penalty = v.validation_penalty
                has_stale = v.has_stale_files
                has_templates = v.has_template_content
                warning_count = len(v.warnings)
                if v.behavioral:
                    ci_agents = v.behavioral.level_6_ready
                    handoffs_valid = v.behavioral.level_7_ready
                    outcomes_valid = v.behavioral.level_8_ready

            line = (
                f'"{score.repo_name}","{score.repo_path}",{score.overall_level},'
                f'{score.overall_score:.2f},{bonus:.2f},{avg_quality:.2f},'
                f'{ref_count},{resolved_count},{validation_penalty:.2f},'
                f'{has_stale},{has_templates},{warning_count},'
                f'{ci_agents},{handoffs_valid},{outcomes_valid}'
            )
            for cov in coverages:
                line += f",{cov:.2f}"
            print(line, file=output)


def get_reporter(
    format: str, verbose: bool = True
) -> Union["TerminalReporter", "JsonReporter", "MarkdownReporter", "CsvReporter"]:
    """Get a reporter for the specified format."""

    reporters = {
        "terminal": TerminalReporter(verbose=verbose),
        "json": JsonReporter(),
        "markdown": MarkdownReporter(),
        "csv": CsvReporter(),
    }
    return reporters.get(format, TerminalReporter(verbose=verbose))
