---
on:
  pull_request:
    types: [opened, synchronize]
  issue_comment:
    types: [created]

permissions:
  contents: read
  pull-requests: write
  issues: read

network: defaults

tools:
  github:
  bash:
  edit:

safe-outputs:
  create-comment:
---

# AI Proficiency Assessment for Pull Requests

Assess the repository's AI coding proficiency and context engineering maturity when PRs are opened or when someone comments `/assess-proficiency`.

## Trigger Conditions

Only run this assessment when:
1. A new pull request is opened or updated
2. Someone comments `/assess-proficiency` on a PR or issue

If triggered by a comment, check if the comment body contains `/assess-proficiency`. If not, exit without action.

## Assessment Process

### Step 1: Install the Tool

```bash
pip install measure-ai-proficiency
```

### Step 2: Run the Assessment

Run the proficiency scanner on the repository with verbose output:

```bash
measure-ai-proficiency -v --format json --output proficiency-report.json
```

Also generate a markdown report:

```bash
measure-ai-proficiency --format markdown --output proficiency-report.md
```

### Step 3: Analyze the Results

Read the JSON report and extract:
- Overall maturity level (0-4)
- Total files detected at each level
- Top recommendations for improvement

### Step 4: Check for Context Engineering Changes in the PR

Look at the files changed in this PR. Identify any context engineering artifacts being added or modified:
- CLAUDE.md, AGENTS.md, .cursorrules
- ARCHITECTURE.md, CONVENTIONS.md, PATTERNS.md
- .github/copilot-instructions.md
- .claude/skills/, .claude/commands/, .claude/hooks/
- Any .md files in docs/

If context files are being added, this is positive - acknowledge the improvement.

### Step 5: Create the PR Comment

Post a comment on the PR with the following structure:

```markdown
## AI Proficiency Assessment

| Metric | Value |
|--------|-------|
| **Overall Level** | Level X: [Name] |
| **Overall Score** | XX.X/100 |
| **Files Detected** | XX context files |

### Level Breakdown

[Include level-by-level breakdown with file counts]

### This PR's Impact

[Note any context engineering files being added/modified in this PR]

### Top Recommendations

[List the top 3 most impactful recommendations from the report]

---
*Powered by [measure-ai-proficiency](https://github.com/pskoett/measuring-ai-proficiency)*
```

## Important Guidelines

- Be constructive and encouraging, not critical
- Highlight any positive changes in the PR
- Keep recommendations actionable and specific
- If the repo is already at Level 3+, congratulate them and suggest advanced improvements
- If at Level 0, be encouraging about starting the journey
