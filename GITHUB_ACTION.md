# GitHub Action Integration

Automatically assess AI proficiency on every PR and track progress over time with GitHub Actions.

## Two Options

| Option | Engine | Best For |
|--------|--------|----------|
| **GitHub Agentic Workflows** | GitHub Copilot | GitHub-native, natural language workflows |
| **Claude Code Action** | Anthropic Claude | Anthropic API users, more detailed analysis |

---

## Option 1: GitHub Agentic Workflows (Recommended)

Uses [GitHub Agentic Workflows](https://githubnext.com/projects/agentic-workflows/) - natural language automation powered by GitHub Copilot.

### Quick Setup

```bash
# Install the gh-aw CLI extension
gh extension install githubnext/gh-aw

# Add the PR review workflow
gh aw add pskoett/measuring-ai-proficiency/.github/workflows/ai-proficiency-pr-review --create-pull-request

# Add the weekly report workflow
gh aw add pskoett/measuring-ai-proficiency/.github/workflows/ai-proficiency-weekly-report --create-pull-request
```

### Manual Setup

1. **Create a Copilot Token**
   - Go to [GitHub Settings > Personal Access Tokens](https://github.com/settings/personal-access-tokens/new)
   - Name: "Agentic Workflows Copilot"
   - Expiration: 90 days (recommended)
   - Resource owner: Your account
   - Repository access: Public repositories (or select specific repos)
   - Permissions: Account permissions > Copilot Requests > Read

2. **Add Token to Repository**
   - Go to your repo > Settings > Secrets and variables > Actions
   - Create secret: `COPILOT_GITHUB_TOKEN`
   - Paste your token

3. **Copy Workflow Files**

   Copy these files to your repository's `.github/workflows/` directory:
   - `ai-proficiency-pr-review.md` - Assesses PRs when opened
   - `ai-proficiency-weekly-report.md` - Weekly tracking reports

4. **Compile Workflows**
   ```bash
   gh aw compile
   ```

### What You Get

**PR Review Workflow:**
- Automatically comments on new PRs with proficiency assessment
- Responds to `/assess-proficiency` comments
- Highlights context engineering changes in the PR
- Provides actionable recommendations

**Weekly Report Workflow:**
- Creates a GitHub issue every Monday with status report
- Tracks progress over time
- Compares to previous week
- Suggests next improvements

---

## Option 2: Claude Code Action

Uses [Anthropic's Claude Code Action](https://github.com/anthropics/claude-code-action) for deeper AI-powered analysis.

### Quick Setup

```bash
# In Claude Code terminal
/install-github-app
```

This guides you through:
1. Installing the Claude GitHub app
2. Adding the ANTHROPIC_API_KEY secret

### Manual Setup

1. **Install Claude GitHub App**
   - Visit [github.com/apps/claude](https://github.com/apps/claude)
   - Install on your repository

2. **Add API Key**
   - Go to your repo > Settings > Secrets and variables > Actions
   - Create secret: `ANTHROPIC_API_KEY`
   - Add your Anthropic API key

3. **Copy Workflow File**

   Copy `.github/workflows/ai-proficiency-claude.yml` to your repository.

### What You Get

- Automatic PR assessment on open
- Responds to `/assess-proficiency` and `@claude` mentions
- Detailed AI analysis of your context engineering
- Artifact uploads for historical tracking

---

## Workflow Triggers

### Automatic Triggers

| Workflow | Trigger | Action |
|----------|---------|--------|
| PR Review | PR opened/updated | Comments with assessment |
| Weekly Report | Monday 9am UTC | Creates tracking issue |

### Manual Triggers

| Command | Where | Action |
|---------|-------|--------|
| `/assess-proficiency` | PR or Issue comment | Runs full assessment |
| `@claude assess proficiency` | PR or Issue comment | Claude-powered assessment |
| Workflow dispatch | Actions tab | Manual run |

---

## Example Output

### PR Comment

```markdown
## AI Proficiency Assessment

| Metric | Value |
|--------|-------|
| **Overall Level** | Level 3: Comprehensive Context |
| **Overall Score** | 45.3/100 |
| **Files Detected** | 47 context files |

### This PR's Impact

This PR adds `ARCHITECTURE.md` - great improvement for Level 3 maturity!

### Top Recommendations

1. Add `.claude/hooks/` for automatic formatting
2. Create `MEMORY.md` to capture learnings
3. Set up custom commands in `.claude/commands/`
```

### Weekly Report Issue

```markdown
## Weekly AI Proficiency Report

**Report Date:** 2025-01-06
**Repository:** my-project

### Current Status

| Metric | This Week | Last Week | Change |
|--------|-----------|-----------|--------|
| **Level** | 3 | 2 | +1 |
| **Score** | 45.3 | 32.1 | +13.2 |
| **Total Files** | 47 | 38 | +9 |

### This Week's Recommendations

1. Add CONVENTIONS.md with coding standards
2. Document API contracts in API.md
3. Create testing guide in TESTING.md
```

---

## Customization

### Adjust Assessment Frequency

Edit the cron schedule in `ai-proficiency-weekly-report.md`:

```yaml
on:
  schedule:
    - cron: "0 9 * * 1"  # Weekly on Monday
    # - cron: "0 9 * * *"  # Daily
    # - cron: "0 9 1 * *"  # Monthly
```

### Add Minimum Level Gate

Add a check step to fail PRs below a threshold:

```yaml
- name: Check minimum level
  run: |
    LEVEL=$(jq '.overall_level' proficiency-report.json)
    if [ "$LEVEL" -lt 2 ]; then
      echo "Repository must be at least Level 2 (Basic Instructions)"
      exit 1
    fi
```

### Custom Labels

Add labels to weekly report issues by modifying the workflow to include label assignment.

---

## Troubleshooting

### Workflow Not Triggering

1. Check that the workflow file is in `.github/workflows/`
2. Verify the token has correct permissions
3. For agentic workflows, ensure `.lock.yml` file was generated

### Token Errors

- Copilot token: Must have "Copilot Requests: Read" permission
- Anthropic key: Verify key is valid and has sufficient credits

### Missing Comments

- Check repository permissions allow Actions to write comments
- Verify the workflow has `pull-requests: write` permission

---

## Security

- Tokens are stored as GitHub Secrets (never in code)
- Workflows run with minimal required permissions
- Agentic workflows use read-only defaults with explicit safe-outputs
- All generated YAML is auditable in `.lock.yml` files

---

## Resources

- [GitHub Agentic Workflows Docs](https://githubnext.github.io/gh-aw/)
- [Claude Code Action Docs](https://github.com/anthropics/claude-code-action)
- [measure-ai-proficiency Tool](https://github.com/pskoett/measuring-ai-proficiency)
