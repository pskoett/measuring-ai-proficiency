"""
MCP Server for AI Proficiency Measurement

Provides AI assistants with real-time AI context awareness and improvement suggestions.
This creates a meta-improvement loop where the tool that measures AI proficiency
becomes AI-accessible.
"""

import asyncio
import json
import logging
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from . import __version__
from .scanner import RepoScanner, scan_multiple_repos
from .github_scanner import scan_github_repo, scan_github_org
from .reporter import JsonReporter
from .config import LEVELS
from .signals import GATE_REQUIREMENT_LABELS, GATE_REQUIREMENT_REFERENCES

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
app = Server("measure-ai-proficiency")


# =============================================================================
# Helper Functions
# =============================================================================

def get_current_repo() -> Path:
    """Get the current working directory as a repository path."""
    return Path.cwd()


def check_github_cli() -> bool:
    """Check if GitHub CLI (gh) is installed and available."""
    return shutil.which("gh") is not None


def format_score_result(score: Any) -> Dict[str, Any]:
    """Format a RepoScore object into a JSON-serializable dict."""
    reporter = JsonReporter()
    return reporter._score_to_dict(score)


def get_level_requirements(current_level: int) -> Dict[str, Any]:
    """Get requirements for the next maturity level."""
    if current_level >= 8:
        return {
            "message": "You've reached the highest level (Level 8: Custom Orchestration)!",
            "current_level": current_level,
            "next_level": None,
        }

    next_level = current_level + 1
    level_config = LEVELS.get(next_level)

    if not level_config:
        return {
            "error": f"No configuration found for level {next_level}",
        }

    # Get threshold from scanner defaults
    from .scanner import RepoScanner
    threshold = RepoScanner.DEFAULT_THRESHOLDS.get(next_level, 50)

    return {
        "current_level": current_level,
        "next_level": next_level,
        "next_level_name": level_config.name,
        "next_level_description": level_config.description,
        "required_coverage": threshold,
        "file_patterns": level_config.file_patterns,
    }


# =============================================================================
# MCP Tool Handlers
# =============================================================================

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available MCP tools."""
    return [
        Tool(
            name="scan_current_repo",
            description="Analyze AI proficiency of the current repository. Returns maturity level, score, detected tools, recommendations, and quality metrics.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_recommendations",
            description="Get specific improvement suggestions for the current repository based on its AI proficiency analysis.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="check_cross_references",
            description="Validate references between AI context files in the current repository. Identifies broken links and missing files.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_level_requirements",
            description="Show requirements for the next maturity level. Useful for understanding what files and patterns are needed to advance.",
            inputSchema={
                "type": "object",
                "properties": {
                    "current_level": {
                        "type": "integer",
                        "description": "Current maturity level (1-8). If not provided, will scan the current repo to determine it.",
                        "minimum": 1,
                        "maximum": 8,
                    }
                },
                "required": [],
            },
        ),
        Tool(
            name="scan_github_repo",
            description="Analyze AI proficiency of a remote GitHub repository without cloning it. Requires GitHub CLI (gh) to be installed and authenticated.",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo": {
                        "type": "string",
                        "description": "GitHub repository in 'owner/repo' format (e.g., 'anthropics/claude-code')",
                    }
                },
                "required": ["repo"],
            },
        ),
        Tool(
            name="scan_github_org",
            description="Analyze AI proficiency of all repositories in a GitHub organization without cloning them. Requires GitHub CLI (gh) to be installed and authenticated.",
            inputSchema={
                "type": "object",
                "properties": {
                    "org": {
                        "type": "string",
                        "description": "GitHub organization name (e.g., 'anthropics')",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of repositories to scan (default: all)",
                        "minimum": 1,
                    }
                },
                "required": ["org"],
            },
        ),
        Tool(
            name="validate_file_quality",
            description="Check the quality score of a specific AI context file. Analyzes sections, commands, constraints, and git history.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to validate (relative to repo root or absolute)",
                    }
                },
                "required": ["file_path"],
            },
        ),
        Tool(
            name="check_harness_orchestration_quality",
            description="Score 2026 harness/orchestration maturity for the current repo: structural quality of the 6 primitives, dynamic-workflow and harness signals, and the L6-L8 signal gates (what's required to reach each level).",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="scan_for_maintenance_hygiene",
            description="Report anti-drift maintenance hygiene for the current repo: sentinel/canary drift checks, audits/detox, steward loops, decay schedules, plus telemetry signals. Grounded in official docs.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_dynamic_workflow_recommendations",
            description="Recommend how to adopt Dynamic Workflows + verification patterns for the current repo, scoped to what is statically detectable (.claude/workflows, orchestration scripts, clean-context verifiers). Cites official workflow docs.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="curricula_alignment",
            description="Check whether the current repo references official learning on-ramps (Anthropic Academy, Google 5-Day AI Agents course) that teach context engineering and production agent patterns.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="cheapest_primitive_decision_tree_report",
            description="Return the cheapest-primitive-first decision tree (Skill -> MCP -> Subagent -> Hook -> escalate) and report which primitives the current repo actually uses, with decision-discipline signals.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="prove_efficacy",
            description="Prove what the current repo's AI artifacts actually DO (report-only Efficacy Score + per-artifact evidence): documented commands resolve, hooks are wired, and the always-on context token budget. RESOLVE-ONLY (runs no repo code) — executing commands is CLI-only (`measure-ai-proficiency --prove-exec`), never via this tool.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle MCP tool calls."""
    try:
        if name == "scan_current_repo":
            return await scan_current_repo()
        elif name == "get_recommendations":
            return await get_recommendations_handler()
        elif name == "check_cross_references":
            return await check_cross_references()
        elif name == "get_level_requirements":
            current_level = arguments.get("current_level")
            return await get_level_requirements_handler(current_level)
        elif name == "scan_github_repo":
            repo = arguments.get("repo")
            if not repo:
                raise ValueError("repo parameter is required")
            return await scan_github_repo_handler(repo)
        elif name == "scan_github_org":
            org = arguments.get("org")
            limit = arguments.get("limit")
            if not org:
                raise ValueError("org parameter is required")
            return await scan_github_org_handler(org, limit)
        elif name == "validate_file_quality":
            file_path = arguments.get("file_path")
            if not file_path:
                raise ValueError("file_path parameter is required")
            return await validate_file_quality_handler(file_path)
        elif name == "check_harness_orchestration_quality":
            return await check_harness_orchestration_quality_handler()
        elif name == "scan_for_maintenance_hygiene":
            return await scan_for_maintenance_hygiene_handler()
        elif name == "get_dynamic_workflow_recommendations":
            return await get_dynamic_workflow_recommendations_handler()
        elif name == "curricula_alignment":
            return await curricula_alignment_handler()
        elif name == "cheapest_primitive_decision_tree_report":
            return await cheapest_primitive_decision_tree_report_handler()
        elif name == "prove_efficacy":
            return await prove_efficacy_handler()
        else:
            raise ValueError(f"Unknown tool: {name}")
    except Exception as e:
        logger.error(f"Error in {name}: {str(e)}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]


async def scan_current_repo() -> list[TextContent]:
    """Scan the current repository for AI proficiency."""
    repo_path = get_current_repo()
    scanner = RepoScanner(repo_path)

    # Run blocking scan in thread pool to avoid blocking the event loop
    score = await asyncio.to_thread(scanner.scan)

    result = format_score_result(score)

    return [TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]


async def get_recommendations_handler() -> list[TextContent]:
    """Get improvement recommendations for the current repository."""
    repo_path = get_current_repo()
    scanner = RepoScanner(repo_path)

    # Run blocking scan in thread pool to avoid blocking the event loop
    score = await asyncio.to_thread(scanner.scan)

    # Get validation warnings from the validation result
    validation_warnings = []
    if score.validation:
        validation_warnings = score.validation.warnings

    result = {
        "repo_name": score.repo_name,
        "current_level": score.overall_level,
        "overall_score": round(score.overall_score, 1),
        "recommendations": score.recommendations,
        "validation_warnings": validation_warnings,
    }

    return [TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]


async def check_cross_references() -> list[TextContent]:
    """Validate cross-references in AI context files."""
    repo_path = get_current_repo()
    scanner = RepoScanner(repo_path)

    # Run blocking scan in thread pool to avoid blocking the event loop
    score = await asyncio.to_thread(scanner.scan)

    if not score.cross_references:
        return [TextContent(
            type="text",
            text=json.dumps({
                "message": "No cross-references found in AI context files",
                "total_references": 0,
            }, indent=2)
        )]

    result = {
        "total_references": score.cross_references.total_count,
        "resolved_references": score.cross_references.resolved_count,
        "resolution_rate": round(score.cross_references.resolution_rate, 1),
        "bonus_points": round(score.cross_references.bonus_points, 1),
        "broken_references": [
            {
                "source": ref.source_file,
                "target": ref.target,
                "type": ref.reference_type,
                "resolved": ref.is_resolved,
            }
            for ref in score.cross_references.references
            if not ref.is_resolved
        ],
        "quality_scores": {
            file: {
                "score": round(quality.quality_score, 1),
                "word_count": quality.word_count,
                "section_count": quality.section_count,
                "has_sections": quality.has_sections,
                "has_specific_paths": quality.has_specific_paths,
                "has_tool_commands": quality.has_tool_commands,
                "has_constraints": quality.has_constraints,
                "commit_count": quality.commit_count,
            }
            for file, quality in score.cross_references.quality_scores.items()
        },
    }

    return [TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]


async def get_level_requirements_handler(current_level: Optional[int]) -> list[TextContent]:
    """Get requirements for the next maturity level."""
    if current_level is None:
        # Scan current repo to determine level
        repo_path = get_current_repo()
        scanner = RepoScanner(repo_path)

        # Run blocking scan in thread pool to avoid blocking the event loop
        score = await asyncio.to_thread(scanner.scan)
        current_level = score.overall_level

    result = get_level_requirements(current_level)

    return [TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]


async def scan_github_repo_handler(repo: str) -> list[TextContent]:
    """Scan a GitHub repository without cloning it."""
    # Check if GitHub CLI is available
    if not check_github_cli():
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": "GitHub CLI (gh) is not installed or not in PATH",
                "hint": "Install GitHub CLI from https://cli.github.com/ and run 'gh auth login'",
                "repo": repo,
            }, indent=2)
        )]

    def _fetch_scan_cleanup() -> Optional[Dict[str, Any]]:
        # github_scanner.scan_github_repo returns a temp dir Path (or None);
        # wrap it with RepoScanner to produce a RepoScore, then clean up.
        temp_dir = scan_github_repo(repo)
        if temp_dir is None:
            return None
        try:
            score = RepoScanner(str(temp_dir)).scan()
            score.repo_path = repo
            return format_score_result(score)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    try:
        # Run blocking fetch + scan + cleanup in a thread to avoid blocking the loop
        result = await asyncio.to_thread(_fetch_scan_cleanup)
        if result is None:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "Failed to fetch repository (not found, no AI files, or access denied)",
                    "repo": repo,
                }, indent=2)
            )]

        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    except Exception as e:
        logger.error(f"Error scanning GitHub repo {repo}: {str(e)}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": f"Failed to scan GitHub repository: {str(e)}",
                "repo": repo,
            }, indent=2)
        )]


async def scan_github_org_handler(org: str, limit: Optional[int]) -> list[TextContent]:
    """Scan all repositories in a GitHub organization."""
    # Check if GitHub CLI is available
    if not check_github_cli():
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": "GitHub CLI (gh) is not installed or not in PATH",
                "hint": "Install GitHub CLI from https://cli.github.com/ and run 'gh auth login'",
                "org": org,
            }, indent=2)
        )]

    def _fetch_scan_cleanup_org() -> List[Dict[str, Any]]:
        # github_scanner.scan_github_org returns List[(repo_name, temp_dir|None)];
        # wrap each temp dir with RepoScanner, then clean up. NOTE: limit is a
        # keyword arg (the function signature is (org, verbose, limit)).
        repos = scan_github_org(org, limit=limit) if limit else scan_github_org(org)
        out: List[Dict[str, Any]] = []
        for repo_name, temp_dir in repos:
            if temp_dir is None:
                continue
            try:
                score = RepoScanner(str(temp_dir)).scan()
                score.repo_path = repo_name
                out.append(format_score_result(score))
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)
        return out

    try:
        # Run blocking fetch + scan + cleanup in a thread to avoid blocking the loop
        results = await asyncio.to_thread(_fetch_scan_cleanup_org)

        summary = {
            "organization": org,
            "total_repos": len(results),
            "repos_scanned": limit if limit else len(results),
            "average_score": round(sum(r["overall_score"] for r in results) / len(results), 1) if results else 0,
            "level_distribution": {},
            "repositories": results,
        }

        # Calculate level distribution
        for result in results:
            level = result["overall_level"]
            summary["level_distribution"][level] = summary["level_distribution"].get(level, 0) + 1

        return [TextContent(
            type="text",
            text=json.dumps(summary, indent=2)
        )]
    except Exception as e:
        logger.error(f"Error scanning GitHub org {org}: {str(e)}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": f"Failed to scan GitHub organization: {str(e)}",
                "org": org,
            }, indent=2)
        )]


async def validate_file_quality_handler(file_path: str) -> list[TextContent]:
    """Validate the quality of a specific AI context file."""
    repo_path = get_current_repo()

    # Convert to absolute path if relative
    if not os.path.isabs(file_path):
        file_path = os.path.join(repo_path, file_path)

    if not os.path.exists(file_path):
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": f"File not found: {file_path}",
            }, indent=2)
        )]

    # Scan the repo to get quality metrics
    scanner = RepoScanner(repo_path)

    # Run blocking scan in thread pool to avoid blocking the event loop
    score = await asyncio.to_thread(scanner.scan)

    # Find the file in the quality scores
    rel_path = os.path.relpath(file_path, repo_path)

    if score.cross_references and rel_path in score.cross_references.quality_scores:
        quality = score.cross_references.quality_scores[rel_path]

        result = {
            "file": rel_path,
            "score": round(quality.quality_score, 1),
            "max_score": 10,
            "word_count": quality.word_count,
            "metrics": {
                "section_count": quality.section_count,
                "has_sections": quality.has_sections,
                "has_specific_paths": quality.has_specific_paths,
                "has_tool_commands": quality.has_tool_commands,
                "has_constraints": quality.has_constraints,
                "commit_count": quality.commit_count,
            },
            "recommendations": [],
        }

        # Add specific recommendations based on missing metrics
        if quality.section_count < 5:
            result["recommendations"].append("Add more structure with markdown headers (##)")
        if not quality.has_specific_paths:
            result["recommendations"].append("Include concrete file paths to help AI understand your codebase")
        if not quality.has_tool_commands:
            result["recommendations"].append("Add CLI commands in backticks for common workflows")
        if not quality.has_constraints:
            result["recommendations"].append("Add constraints (never, avoid, must, always) for AI guidance")
        if quality.word_count < 200:
            result["recommendations"].append("Expand content - aim for 200+ words for substantive guidance")
        if quality.commit_count < 3:
            result["recommendations"].append("File needs more updates - indicates it may be stale or template-based")

    else:
        result = {
            "error": f"File not analyzed: {rel_path}",
            "message": "This file was not scanned for quality. It may not be a recognized AI context file.",
        }

    return [TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]


# =============================================================================
# 2026 Context-Engineering Signal Tool Handlers
# =============================================================================

async def _scan_current_for_signals():
    """Scan the current repo and return its RepoScore (with signals computed)."""
    repo_path = get_current_repo()
    scanner = RepoScanner(repo_path)
    return await asyncio.to_thread(scanner.scan)


def _missing_gate_detail(signals, level: int) -> List[Dict[str, str]]:
    """Build actionable detail for a level's missing gate requirements."""
    return [
        {
            "requirement": req,
            "how": GATE_REQUIREMENT_LABELS.get(req, req),
            "reference": GATE_REQUIREMENT_REFERENCES.get(req, ""),
        }
        for req in signals.gate_missing.get(level, [])
    ]


async def check_harness_orchestration_quality_handler() -> list[TextContent]:
    """Score harness/orchestration maturity for the current repo."""
    score = await _scan_current_for_signals()
    sig = score.signals
    if not sig:
        return [TextContent(type="text", text=json.dumps(
            {"error": "No signals computed for this repository"}, indent=2))]

    harness_categories = {"harness", "orchestration", "primitive"}
    result: Dict[str, Any] = {
        "repo_name": score.repo_name,
        "overall_level": score.overall_level,
        "overall_score": round(score.overall_score, 1),
        "signal_bonus": round(sig.bonus_points, 2),
        "structural_quality": None,
        "harness_signals": {
            key: {
                "title": h.title,
                "category": h.category,
                "detected": h.matched,
                "evidence": h.evidence,
                "official_reference": h.official_reference,
            }
            for key, h in sig.hits.items()
            if h.category in harness_categories
        },
        "level_gates": {
            f"L{lvl}": {
                "satisfied": sig.gates.get(lvl, False),
                "missing": _missing_gate_detail(sig, lvl),
            }
            for lvl in (6, 7, 8)
        },
        "note": "Static scans detect documented proxies (artifacts/keywords), not runtime efficacy.",
    }
    if sig.structural:
        sq = sig.structural
        result["structural_quality"] = {
            "structural_score": round(sq.structural_score, 2),
            "skills_count": sq.skills_count,
            "skills_structured": sq.skills_structured,
            "skills_with_frontmatter": sq.skills_with_frontmatter,
            "skills_with_executable_content": sq.skills_with_executable_content,
            "skills_with_verification": sq.skills_with_verification,
            "hooks_present": sq.hooks_present,
            "hook_events": sq.hook_events,
            "subagents_count": sq.subagents_count,
            "workflows_present": sq.workflows_present,
            "plugins_present": sq.plugins_present,
        }
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def scan_for_maintenance_hygiene_handler() -> list[TextContent]:
    """Report anti-drift maintenance hygiene for the current repo."""
    score = await _scan_current_for_signals()
    sig = score.signals
    keys = ("maintenance_hygiene", "telemetry", "verification")
    hits = {k: sig.hits[k] for k in keys if k in sig.hits} if sig else {}

    hygiene = hits.get("maintenance_hygiene")
    telemetry = hits.get("telemetry")
    recommendations: List[str] = []
    if not (hygiene and hygiene.matched):
        recommendations.append(
            "Add anti-drift sentinels/canaries and a periodic CLAUDE.md/AGENTS.md audit (detox). "
            "See https://docs.claude.com/en/docs/claude-code/memory"
        )
    if not (telemetry and telemetry.matched):
        recommendations.append(
            "Add telemetry/observability (metrics, scorecards, drift incidents) to measure harness health."
        )

    result = {
        "repo_name": score.repo_name,
        "maintenance_hygiene_detected": bool(hygiene and hygiene.matched),
        "signals": {
            k: {
                "detected": h.matched,
                "evidence": h.evidence,
                "official_reference": h.official_reference,
            }
            for k, h in hits.items()
        },
        "recommendations": recommendations or ["Maintenance hygiene signals already present."],
    }
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def get_dynamic_workflow_recommendations_handler() -> list[TextContent]:
    """Recommend Dynamic Workflows + verification adoption for the current repo."""
    score = await _scan_current_for_signals()
    sig = score.signals
    sq = sig.structural if sig else None
    dw = sig.hits.get("dynamic_workflows") if sig else None
    verif = sig.hits.get("verification") if sig else None

    workflows_present = bool(sq and sq.workflows_present)
    dw_detected = bool(dw and dw.matched)
    verif_detected = bool(verif and verif.matched)

    recommendations: List[str] = []
    if not workflows_present:
        recommendations.append(
            "Add a .claude/workflows/ directory with reusable orchestration scripts "
            "(save a proven workflow as a project slash command). "
            "See https://code.claude.com/docs/en/workflows"
        )
    if not dw_detected:
        recommendations.append(
            "Document dynamic-workflow patterns: plan -> orchestration script -> parallel "
            "subagents -> converge, with resumable background execution for large migrations/audits."
        )
    if not verif_detected:
        recommendations.append(
            "Add clean-context verification workers / adversarial refutation so verifiers do not "
            "assume the work was correct. See https://docs.claude.com/en/docs/claude-code/hooks"
        )

    result = {
        "repo_name": score.repo_name,
        "workflows_present": workflows_present,
        "dynamic_workflow_signal_detected": dw_detected,
        "verification_signal_detected": verif_detected,
        "l8_orchestration_gate": {
            "satisfied": sig.gates.get(8, False) if sig else False,
            "missing": _missing_gate_detail(sig, 8) if sig else [],
        },
        "official_docs": "https://code.claude.com/docs/en/workflows",
        "recommendations": recommendations or [
            "Strong: dynamic-workflow and verification signals already present."
        ],
        "note": "Static scans detect committed artifacts (.claude/workflows, orchestration "
                "scripts), not runtime workflow execution.",
    }
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def curricula_alignment_handler() -> list[TextContent]:
    """Check curricula on-ramp references in the current repo."""
    score = await _scan_current_for_signals()
    sig = score.signals
    cur = sig.hits.get("curricula") if sig else None
    referenced = bool(cur and cur.matched)

    result = {
        "repo_name": score.repo_name,
        "curricula_referenced": referenced,
        "evidence": cur.evidence if cur else [],
        "recommended_courses": [
            {
                "name": "Anthropic Academy — Claude Code, Agent Skills, MCP, workflows",
                "reference": "https://www.anthropic.com/learn",
            },
            {
                "name": "Google 5-Day AI Agents course — Day 3 covers Context Engineering",
                "reference": "Google 5-Day AI Agents course",
            },
        ],
        "recommendation": (
            "Curricula on-ramps referenced — good team baseline."
            if referenced
            else "Reference official on-ramps (Anthropic Academy, Google 5-Day AI Agents) in your "
                 "context docs to ground the team in context engineering + production patterns."
        ),
    }
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def cheapest_primitive_decision_tree_report_handler() -> list[TextContent]:
    """Return the cheapest-primitive-first decision tree + repo primitive usage."""
    score = await _scan_current_for_signals()
    sig = score.signals
    sq = sig.structural if sig else None
    discipline = sig.hits.get("primitive_discipline") if sig else None

    decision_tree = [
        {"step": 1, "primitive": "Skill",
         "question": "Does the agent need knowledge or a repeatable procedure?",
         "reference": "https://docs.claude.com/en/docs/claude-code/skills"},
        {"step": 2, "primitive": "MCP",
         "question": "Does it need to reach an external system (data/actions)?",
         "reference": "https://modelcontextprotocol.io"},
        {"step": 3, "primitive": "Subagent",
         "question": "Does a side task need its own isolated context window?",
         "reference": "https://docs.claude.com/en/docs/claude-code/sub-agents"},
        {"step": 4, "primitive": "Hook",
         "question": "Must a behavior be enforced deterministically every time?",
         "reference": "https://docs.claude.com/en/docs/claude-code/hooks"},
        {"step": 5, "primitive": "Plugin / Workflow",
         "question": "Distribute to a team or orchestrate at scale?",
         "reference": "https://docs.claude.com/en/docs/claude-code/plugins"},
    ]

    primitives_present = {
        "skills": bool(sq and sq.skills_count > 0),
        "hooks": bool(sq and sq.hooks_present),
        "subagents": bool(sq and sq.subagents_count > 0),
        "workflows": bool(sq and sq.workflows_present),
        "plugins": bool(sq and sq.plugins_present),
    }

    result = {
        "repo_name": score.repo_name,
        "rule": "Reach for the cheapest primitive first; escalate only when a failure "
                "mode or scale justifies it.",
        "decision_tree": decision_tree,
        "primitives_present": primitives_present,
        "decision_discipline_signal": {
            "detected": bool(discipline and discipline.matched),
            "evidence": discipline.evidence if discipline else [],
        },
        "progressive_disclosure_reference": "https://docs.claude.com/en/docs/claude-code/skills",
    }
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def prove_efficacy_handler() -> list[TextContent]:
    """Run the report-only, RESOLVE-ONLY efficacy proving pass on the current repo.

    Execution of repo-defined commands is intentionally NOT available via MCP (no
    human-in-the-loop confirmation here); use the CLI `--prove-exec` for that.
    """
    repo_path = get_current_repo()
    scanner = RepoScanner(repo_path)

    def _run():
        score = scanner.scan()
        # is_remote=False is safe: this handler only ever operates on the local working
        # directory (get_current_repo() == Path.cwd()), never a GitHub-fetched temp dir.
        # execute=False also means no repo code runs regardless.
        scanner.prove(score, execute=False, is_remote=False)
        return score

    score = await asyncio.to_thread(_run)
    eff = score.efficacy
    if not eff:
        return [TextContent(type="text", text=json.dumps(
            {"error": "Efficacy was not computed for this repository"}, indent=2))]

    result: Dict[str, Any] = {
        "repo_name": score.repo_name,
        "efficacy_score": eff.score,
        "executed": eff.executed,
        "warnings": eff.warnings,
        "provers": {
            name: {
                "summary": p.summary,
                "checks": [
                    {
                        "name": c.name,
                        "status": c.status,
                        "evidence": c.evidence,
                        "reproduce_cmd": c.reproduce_cmd,
                    }
                    for c in p.checks
                ],
            }
            for name, p in eff.provers.items()
        },
        "note": "Report-only: does not change the Proficiency Score or level. These are "
                "static/sandboxed proxies, not a guarantee of full runtime efficacy.",
    }
    if eff.context_budget:
        b = eff.context_budget
        result["context_budget"] = {
            "always_on_tokens": b.always_on_tokens,
            "pct_of_window": round(b.pct_of_window, 2),
            "window_tokens": b.window_tokens,
            "efficiency_factor": b.efficiency_factor,
            "method": b.method,
        }
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


# =============================================================================
# Main Entry Point
# =============================================================================

def main() -> None:
    """Main entry point for the MCP server."""
    logger.info(f"Starting measure-ai-proficiency MCP server v{__version__}")

    async def run_server():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )

    import asyncio
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
