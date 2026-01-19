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

    try:
        # Run blocking GitHub scan in thread pool to avoid blocking the event loop
        score = await asyncio.to_thread(scan_github_repo, repo)
        result = format_score_result(score)

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

    try:
        # Run blocking GitHub scan in thread pool to avoid blocking the event loop
        scores = await asyncio.to_thread(scan_github_org, org, limit)

        # Format all scores
        results = []
        for score in scores:
            results.append(format_score_result(score))

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
