# MCP Server for AI Proficiency Measurement

The `measure-ai-proficiency` MCP server brings AI context awareness directly into your AI assistant, creating a meta-improvement loop where the tool that measures AI proficiency becomes AI-accessible.

## What is MCP?

The [Model Context Protocol (MCP)](https://modelcontextprotocol.io) is an open standard for connecting AI assistants to tools and data sources. MCP servers extend AI assistants with new capabilities that work across all MCP-compatible tools (Claude Code, Cursor, etc.).

## Why an MCP Server?

### Real-time AI Context Awareness

Your AI assistant can now check its own proficiency level while working:
- "What's my current AI proficiency level in this repo?"
- "What files do I need to reach Level 6?"
- "Are there broken cross-references in CLAUDE.md?"

### Proactive Improvement Suggestions

AI can guide developers to better context engineering:
- Auto-detect when working in a new repo with no AI context
- Suggest specific improvements while editing CLAUDE.md
- Validate cross-references as you write them

### Org-wide Visibility

Query across repositories without switching tools:
- "Which repos in my org need AI context improvements?"
- "Show repos at Level 5+"
- "Find repos with broken skill references"

### Meta-improvement Loop

The tool that measures AI proficiency becomes AI-accessible, creating a feedback loop for better AI context.

## Installation

### 1. Install the package

```bash
pip install measure-ai-proficiency
```

Or from source:

```bash
git clone https://github.com/pskoett/measuring-ai-proficiency.git
cd measuring-ai-proficiency
pip install -e .
```

### 2. Configure Claude Code (or other MCP-compatible client)

Add to your `.mcp.json` or global Claude Code settings:

```json
{
  "mcpServers": {
    "measure-ai-proficiency": {
      "command": "measure-ai-proficiency-mcp",
      "args": [],
      "env": {},
      "description": "AI proficiency measurement and improvement suggestions"
    }
  }
}
```

**Location of .mcp.json:**

- **Project-level**: `.mcp.json` in your repository root (recommended)
- **Global**: `~/.claude/mcp.json` or Claude Code settings

### 3. Restart Claude Code

After updating the configuration, restart Claude Code to load the MCP server.

## Available Tools

The MCP server provides 7 tools for AI proficiency analysis:

### 1. `scan_current_repo`

Analyze AI proficiency of the current repository.

**Returns:**
- Overall maturity level (1-8)
- Overall score (0-100)
- Detected AI tools
- Level-by-level breakdown
- Cross-reference analysis
- Content quality scores
- Recommendations for improvement
- Validation warnings

**Example:**
```
User: What's my AI proficiency level?
Claude: [Uses scan_current_repo tool]
Claude: Your repository is at Level 5: Multi-Agent Ready with a score of 60.1/100...
```

### 2. `get_recommendations`

Get specific improvement suggestions based on the current repository's analysis.

**Returns:**
- Current level and score
- Prioritized recommendations
- Validation warnings
- Specific files to create or improve

**Example:**
```
User: How can I improve my AI context?
Claude: [Uses get_recommendations tool]
Claude: To advance to Level 6, you should:
1. Create .beads/ for persistent memory
2. Add workflow pipelines in workflows/
...
```

### 3. `check_cross_references`

Validate references between AI context files. Identifies broken links and missing files.

**Returns:**
- Total references found
- Resolution rate (%)
- Broken references with source and target
- Quality scores for each file
- Bonus points from cross-references

**Example:**
```
User: Are my CLAUDE.md references valid?
Claude: [Uses check_cross_references tool]
Claude: Found 3 broken references:
- CLAUDE.md → old-file.md (missing)
...
```

### 4. `get_level_requirements`

Show requirements for the next maturity level.

**Parameters:**
- `current_level` (optional): If not provided, scans current repo

**Returns:**
- Next level name and description
- Required coverage percentage
- File patterns needed
- Specific recommendations

**Example:**
```
User: What do I need for Level 6?
Claude: [Uses get_level_requirements tool]
Claude: To reach Level 6: Fleet Infrastructure, you need:
- 8% coverage of fleet patterns
- Files like .beads/, workflows/, shared_context/
...
```

### 5. `scan_github_repo`

Analyze a remote GitHub repository without cloning it.

**Parameters:**
- `repo`: GitHub repository in 'owner/repo' format

**Returns:**
- Same as `scan_current_repo` but for remote repo
- Requires GitHub CLI (gh) to be installed and authenticated

**Example:**
```
User: What's the AI proficiency of anthropics/claude-code?
Claude: [Uses scan_github_repo tool with repo="anthropics/claude-code"]
Claude: The anthropics/claude-code repository is at Level 7...
```

### 6. `scan_github_org`

Analyze all repositories in a GitHub organization.

**Parameters:**
- `org`: GitHub organization name
- `limit` (optional): Max number of repos to scan

**Returns:**
- Organization summary
- Total repos scanned
- Average score
- Level distribution
- Per-repository results

**Example:**
```
User: Scan all repos in my organization
Claude: [Uses scan_github_org tool with org="your-org"]
Claude: Scanned 45 repositories in your-org:
- Average score: 42.3
- Level 5+: 12 repos (27%)
...
```

### 7. `validate_file_quality`

Check the quality score of a specific AI context file.

**Parameters:**
- `file_path`: Path to file (relative or absolute)

**Returns:**
- Quality score (0-10)
- Word count
- Metrics breakdown (sections, paths, commands, constraints, commits)
- Specific recommendations for improvement

**Example:**
```
User: How good is my CLAUDE.md?
Claude: [Uses validate_file_quality tool with file_path="CLAUDE.md"]
Claude: Your CLAUDE.md scores 7.5/10:
- Good: 12 sections, 8 commands
- Needs work: Only 2 constraints, 150 words (aim for 200+)
...
```

## Usage Examples

### Check Current Repository

```
User: What's my AI proficiency level?

Claude: Let me scan your repository.
[Uses scan_current_repo]

Your repository is at **Level 5: Multi-Agent Ready** with a score of 60.1/100.

You have:
- ✓ CLAUDE.md (quality: 10/10)
- ✓ 3 agent files
- ✓ .mcp.json
- ○ No fleet infrastructure yet

To reach Level 6, you need to add:
1. .beads/ for persistent memory
2. workflows/ for orchestration
```

### Validate References

```
User: Are my cross-references valid?

Claude: Let me check your AI context files.
[Uses check_cross_references]

I found 126 references across 11 files:
- Resolved: 82/126 (65%)
- Broken references:
  1. CLAUDE.md → src/old-api.ts (deleted)
  2. AGENTS.md → docs/removed.md (missing)

Your quality scores:
- CLAUDE.md: 10/10 ✓
- AGENTS.md: 8.5/10 (needs more constraints)
```

### Organization Scan

```
User: Which repos in my org need AI context?

Claude: Let me scan your organization.
[Uses scan_github_org with org="your-org"]

Scanned 45 repositories in your-org:

**Summary:**
- Average score: 42.3/100
- Level 1 (No AI): 18 repos (40%)
- Level 2-4: 15 repos (33%)
- Level 5+: 12 repos (27%)

**Top performers:**
1. flagship-app: Level 7 (87.2)
2. api-service: Level 6 (72.1)

**Needs attention:**
1. legacy-app: Level 1 (5.0)
2. internal-tool: Level 1 (5.0)
```

### Improvement Workflow

```
User: I want to improve my AI context to Level 6

Claude: Great! Let me analyze your current state.
[Uses scan_current_repo]

You're at Level 5 (55.3/100). To reach Level 6, you need +8% coverage.

[Uses get_level_requirements]

Here's what you need to add:

**High Priority:**
1. Create .beads/ directory for persistent memory
   - Add .beads/memory.md
   - Document key decisions

2. Add workflow definitions
   - Create workflows/build.yaml
   - Create workflows/deploy.yaml

3. Set up shared context
   - Add shared_context/ARCHITECTURE.md

[After creating files...]

Let me validate the improvements.
[Uses scan_current_repo again]

Excellent! You've reached Level 6: Fleet Infrastructure (70.5/100)!
```

## Advanced Features

### Quality-Driven Improvements

```
User: Why is my score lower than expected?

Claude: Let me check your content quality.
[Uses validate_file_quality for each file]

Your file quality scores:
- CLAUDE.md: 4.0/10 ⚠️
  - Only 80 words (need 200+)
  - Missing constraints (never, avoid, etc.)
  - No git history (template file?)

Let me help you improve CLAUDE.md with:
- Concrete examples from your codebase
- Specific commands for your workflows
- Clear constraints for AI behavior
```

### Cross-Project Analysis

```
User: Compare AI proficiency across my projects

Claude: Let me scan your local repositories.
[Uses scan_current_repo for each repo in directory]

**Comparison:**

1. webapp/ - Level 6 (72.1) ✓
   - Strong: Beads, workflows
   - Opportunity: Add more agents

2. api/ - Level 4 (48.3)
   - Strong: Good CLAUDE.md
   - Opportunity: Add skills, hooks

3. scripts/ - Level 2 (18.2)
   - Needs: Basic context files
```

## Best Practices

### 1. Use MCP for Real-time Feedback

Instead of running the CLI tool separately, let AI check proficiency while you work:

```
User: I just added a new SKILL.md. Did that improve my level?

Claude: [Uses scan_current_repo]
Yes! You've advanced from Level 3 to Level 4...
```

### 2. Validate While Editing

Ask AI to validate references as you write them:

```
User: I'm editing CLAUDE.md and referencing ARCHITECTURE.md. Does it exist?

Claude: [Uses check_cross_references]
Yes, ARCHITECTURE.md exists and is referenced correctly.
```

### 3. Progressive Improvement

Let AI guide you step-by-step:

```
User: Help me reach Level 5

Claude: [Uses get_level_requirements and get_recommendations]
Let's do this systematically:

Step 1: Add your first agent file...
[After completion] ✓

Step 2: Create .mcp.json...
[After completion] ✓

[Uses scan_current_repo]
Congratulations! You've reached Level 5!
```

## Troubleshooting

### MCP Server Not Starting

1. **Check installation:**
   ```bash
   which measure-ai-proficiency-mcp
   ```

2. **Test manually:**
   ```bash
   measure-ai-proficiency-mcp
   ```
   Should start the server (use Ctrl+C to stop)

3. **Check logs:**
   - Claude Code: View logs in developer tools
   - Look for "Starting measure-ai-proficiency MCP server" message

### GitHub Tools Not Working

The `scan_github_repo` and `scan_github_org` tools require:

1. **GitHub CLI installed:**
   ```bash
   gh --version
   ```

2. **Authenticated:**
   ```bash
   gh auth status
   ```

   If not authenticated:
   ```bash
   gh auth login
   ```

### Tool Results Not Showing

If AI doesn't seem to use the tools:

1. Restart Claude Code after updating `.mcp.json`
2. Check that the tool name is correct in the configuration
3. Ask explicitly: "Use the scan_current_repo tool"

## Integration with Existing Workflows

### Combined with CLI

You can use both the MCP server (for AI assistance) and CLI tool (for scripts):

```bash
# In CI/CD
measure-ai-proficiency --min-level 2 --format json > report.json

# With AI
"What's my proficiency?" → AI uses MCP server
```

### With Agent Skills

The MCP server complements agent skills:

- **Skills**: Task-oriented workflows (e.g., "improve AI context")
- **MCP Tools**: Real-time queries and validation

Use them together:
```
User: Improve my AI proficiency

Claude: [Uses improve-ai-context skill]
[Skill internally uses MCP tools for validation]
```

## Examples by Use Case

### For Solo Developers

```
User: I'm starting a new project. What AI context should I add?

Claude: [Uses scan_current_repo]
You're at Level 1. Let's set up basic context:

1. Create CLAUDE.md with:
   - Project overview
   - Architecture patterns
   - Common commands

[After creating file...]
[Uses validate_file_quality]

Good start! Your CLAUDE.md scores 6/10. To improve:
- Add more concrete file paths
- Include constraints for AI behavior
```

### For Engineering Leaders

```
User: Assess AI readiness across my organization

Claude: [Uses scan_github_org]

Organization AI Proficiency Report:

**Overall:** 45 repos, avg score 38.2

**By Team:**
- Frontend: 6 repos, avg 52.1 (Level 4-5)
- Backend: 8 repos, avg 28.3 (Level 2-3) ⚠️
- Data: 4 repos, avg 61.2 (Level 5-6) ✓

**Recommendations:**
- Backend team needs AI context setup
- Frontend ready for advanced features
- Data team could pilot fleet infrastructure
```

### For CI/CD Integration

While the CLI is better for CI/CD, you can use MCP for ad-hoc checks:

```
User: Before I merge this PR, what's our AI proficiency?

Claude: [Uses scan_current_repo]

Current state:
- Level: 5 (60.1/100)
- All references valid ✓
- No validation warnings ✓

Your PR adds .github/skills/test.md - this maintains Level 5.
```

## What's Next?

### Planned Features

- **Real-time monitoring**: Watch for file changes and re-scan
- **Diff analysis**: Compare proficiency before/after changes
- **Template generation**: AI-assisted file creation with best practices
- **Team benchmarking**: Compare against similar repos

### Contributing

The MCP server is part of the open-source measure-ai-proficiency project. Contributions welcome!

- Add new tools
- Improve error handling
- Add caching for performance
- Enhance recommendations

## Related Documentation

- [Main README](README.md) - CLI tool documentation
- [Customization Guide](CUSTOMIZATION.md) - Configure for your team
- [GitHub Action](GITHUB_ACTION.md) - CI/CD integration
- [Model Context Protocol](https://modelcontextprotocol.io) - Official MCP docs

## Support

- **Issues**: [GitHub Issues](https://github.com/pskoett/measuring-ai-proficiency/issues)
- **Discussions**: Use GitHub Discussions for questions
- **Contributing**: See [CONTRIBUTING.md](CONTRIBUTING.md)

---

**Pro tip:** The MCP server creates a meta-improvement loop. As you improve your AI context using AI assistance, the AI becomes more effective at helping you improve further. Start with basic context (Level 2-3), then let AI guide you to higher levels!
