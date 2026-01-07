# Scripts

Utility scripts for measuring AI proficiency across organizations.

## find-org-repos.sh

Find active repositories in a GitHub organization that have context engineering artifacts.

### Purpose

This script helps you answer: **"What percentage of active repositories in our organization have context engineering artifacts?"**

It's useful for:
- Getting a baseline measurement of AI proficiency across your org
- Identifying which repositories to scan with `measure-ai-proficiency`
- Tracking adoption of context engineering practices
- Discovering repositories that would benefit from adding AI instruction files

### Usage

```bash
./scripts/find-org-repos.sh <org-name> [--json]
```

**Arguments:**
- `org-name` - GitHub organization name (required)
- `--json` - Output results in JSON format for programmatic use (optional)

### Requirements

- **GitHub CLI (gh)**: [Install from cli.github.com](https://cli.github.com/)
- **jq**: [Install from stedolan.github.io/jq](https://stedolan.github.io/jq/)

You must be authenticated with `gh`:
```bash
gh auth login
```

### What It Does

1. **Fetches all repositories** in the specified GitHub organization
2. **Filters for active repos** - repositories with commits in the last 90 days
3. **Checks for AI context artifacts** in each active repo:
   - `CLAUDE.md` - Claude Code instructions
   - `AGENTS.md` - Generic AI agent instructions
   - `.cursorrules` - Cursor instructions
   - `.github/copilot-instructions.md` - GitHub Copilot instructions
   - `CODEX.md` - OpenAI Codex instructions
4. **Outputs summary statistics**:
   - Total repositories in org
   - Number of active repositories
   - Number with AI context artifacts
   - Percentage of active repos with artifacts
5. **Lists discovered repositories** with their artifacts

### Examples

**Basic usage:**
```bash
./scripts/find-org-repos.sh anthropics
```

**Output:**
```
=== Results ===

Organization: anthropics
Total repositories: 150
Active repositories: 45 (commits in last 90 days)
Repos with AI context artifacts: 12

✓ 26.7% of active repositories have context engineering artifacts

=== Repositories to Scan ===

claude-code-examples
  URL: https://github.com/anthropics/claude-code-examples
  Artifacts: CLAUDE.md AGENTS.md

documentation-site
  URL: https://github.com/anthropics/documentation-site
  Artifacts: .cursorrules .github/copilot-instructions.md

...

To scan these repositories:

  # Clone and scan individual repo:
  git clone <repo-url>
  cd <repo-name>
  measure-ai-proficiency .

  # Or scan all at once (requires repos to be cloned):
  # git clone https://github.com/anthropics/claude-code-examples
  # git clone https://github.com/anthropics/documentation-site
  measure-ai-proficiency */
```

**JSON output for automation:**
```bash
./scripts/find-org-repos.sh anthropics --json > results.json
```

**JSON structure:**
```json
{
  "org": "anthropics",
  "scan_date": "2026-01-07T12:00:00Z",
  "days_active": 90,
  "total_repos": 150,
  "active_repos": 45,
  "repos_with_artifacts": 12,
  "percentage": 26.7,
  "repositories": [
    {
      "name": "claude-code-examples",
      "url": "https://github.com/anthropics/claude-code-examples",
      "artifacts": ["CLAUDE.md", "AGENTS.md"]
    },
    {
      "name": "documentation-site",
      "url": "https://github.com/anthropics/documentation-site",
      "artifacts": [".cursorrules", ".github/copilot-instructions.md"]
    }
  ]
}
```

### Workflow

1. **Discover repositories with artifacts:**
   ```bash
   ./scripts/find-org-repos.sh your-org-name
   ```

2. **Clone the repositories:**
   ```bash
   # Clone repos listed in the output
   git clone https://github.com/your-org/repo1
   git clone https://github.com/your-org/repo2
   ```

3. **Scan with measure-ai-proficiency:**
   ```bash
   # Scan all cloned repos
   measure-ai-proficiency repo1/ repo2/ repo3/

   # Or scan with --org flag
   measure-ai-proficiency --org .
   ```

4. **Generate report:**
   ```bash
   measure-ai-proficiency --org . --format markdown --output proficiency-report.md
   ```

### Customization

Edit the `INSTRUCTION_FILES` array in the script to check for additional files:

```bash
INSTRUCTION_FILES=(
    "CLAUDE.md"
    "AGENTS.md"
    ".cursorrules"
    ".github/copilot-instructions.md"
    "CODEX.md"
    # Add your custom files here:
    "SYSTEM_DESIGN.md"
    "AI_GUIDELINES.md"
)
```

Change the activity threshold (default is 90 days):

```bash
DAYS_ACTIVE=60  # Check for commits in last 60 days
```

### Performance

The script uses the GitHub API (`gh api`) to check for file existence without cloning repositories, making it very fast:

- **~150 repos**: 2-3 minutes
- **~500 repos**: 5-10 minutes
- **1000+ repos**: 10-20 minutes

### Troubleshooting

**Error: GitHub CLI (gh) is not installed**
```bash
# Install gh
brew install gh           # macOS
sudo apt install gh       # Linux
winget install GitHub.cli # Windows
```

**Error: Not authenticated with GitHub CLI**
```bash
gh auth login
```

**Error: jq is not installed**
```bash
# Install jq
brew install jq           # macOS
sudo apt install jq       # Linux
winget install jqlang.jq  # Windows
```

**Error: rate limit exceeded**

The script respects GitHub API rate limits. If you hit the limit, wait an hour or authenticate with a personal access token that has higher limits.

### Integration with CI/CD

You can integrate this script into your CI/CD pipeline to track adoption over time:

```yaml
# .github/workflows/track-proficiency.yml
name: Track AI Proficiency

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday

jobs:
  track:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Find repos with artifacts
        run: |
          ./scripts/find-org-repos.sh ${{ github.repository_owner }} --json > proficiency-${{ github.run_number }}.json
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: proficiency-results
          path: proficiency-*.json
```

### See Also

- [Main README](../README.md) - Full documentation for measure-ai-proficiency
- [CUSTOMIZATION.md](../CUSTOMIZATION.md) - Customizing the proficiency scanner
- [GITHUB_ACTION.md](../GITHUB_ACTION.md) - GitHub Action integration
