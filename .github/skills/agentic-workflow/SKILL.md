# Agentic Workflow Creator

Create natural language GitHub Actions workflows using the agentic workflows pattern from GitHub Next.

## Description

This skill creates markdown-based agentic workflows that can be compiled to GitHub Actions YAML. Instead of writing traditional scripts, you describe repository behaviors in plain language.

## Usage

```
/agentic-workflow <task description>
```

Or invoke with specific parameters:
```
/agentic-workflow --trigger "issue opened" --task "triage and label issues"
```

## Workflow Structure

Agentic workflows use this markdown format:

```markdown
# Workflow Name

Brief description of what this workflow does.

## Triggers

- on: [trigger events]

## Permissions

- issues: write
- pull-requests: write
- contents: read

## Safe-outputs

- Maximum 1 pull request per run
- Only modify files in specific directories

## Tools

- edit: Modify files in the repository
- web-fetch: Fetch external documentation
- web-search: Search for solutions

## Instructions

Natural language instructions for the agent to follow.
Be specific about:
- What to look for
- How to make decisions
- What actions to take
- When to stop or escalate
```

## Best Use Cases

Agentic workflows work best for:

1. **Issue Triage** - Auto-label, assign, and categorize issues
2. **Quality Assurance** - Propose tests for uncovered code paths
3. **Accessibility** - Scan and suggest WCAG fixes
4. **Documentation** - Sync docs with code changes
5. **Dependency Updates** - Review and merge safe updates
6. **Code Review** - Automated first-pass reviews

## Examples

### Issue Labeler

```markdown
# Auto-Label Issues

Automatically categorize and label new issues based on content.

## Triggers

- on: issues.opened

## Permissions

- issues: write

## Safe-outputs

- Maximum 3 labels per issue
- Never close issues automatically

## Tools

- None required (uses GitHub API only)

## Instructions

When a new issue is opened:

1. Read the issue title and body
2. Categorize as: bug, feature, question, or documentation
3. Add appropriate labels:
   - `bug` for error reports and broken functionality
   - `enhancement` for feature requests
   - `question` for help requests
   - `docs` for documentation issues
4. Add priority label if keywords suggest urgency:
   - `priority:high` if contains "critical", "urgent", "blocking"
   - `priority:low` if contains "minor", "nice-to-have"
5. Add component labels based on file paths mentioned
6. Comment acknowledging the issue was triaged
```

### Test Coverage Improver

```markdown
# Suggest Missing Tests

Analyze PRs and suggest tests for uncovered code paths.

## Triggers

- on: pull_request.opened
- on: pull_request.synchronize

## Permissions

- pull-requests: write
- contents: read

## Safe-outputs

- Maximum 1 review comment per file
- Only suggest, never commit tests directly

## Tools

- edit: Read source files

## Instructions

For each changed file in the PR:

1. Identify new functions, methods, or branches
2. Check if corresponding test files exist
3. Analyze existing test coverage
4. For uncovered code paths, suggest specific test cases:
   - Unit tests for pure functions
   - Integration tests for API endpoints
   - Edge cases for error handling
5. Post suggestions as review comments on specific lines
6. Be constructive - explain why each test matters
```

## Output Location

Workflows are created in:
- `.github/workflows/` (as `.md` files for agentic execution)
- Can be compiled to YAML with `gh aw compile`

## Security Principles

1. **Explicit permissions** - Never assume access, always declare
2. **Safe-outputs** - Constrain what the workflow can do
3. **Auditability** - Generated YAML should be inspectable
4. **Minimal tools** - Only enable tools actually needed
5. **Human oversight** - Complex actions should request review

## References

- [GitHub Next: Agentic Workflows](https://githubnext.com/projects/agentic-workflows/)
- Uses MCP-based tools for GitHub-native integration
- Compatible with Claude Code and OpenAI Codex engines
