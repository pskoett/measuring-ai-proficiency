---
on:
  schedule: weekly on monday
  workflow_dispatch:
timeout-minutes: 10
engine:
  id: copilot
  model: gpt-5.4
permissions:
  contents: read
  actions: read
  issues: read
  pull-requests: read
tools:
  github:
    toolsets: [pull_requests, actions, issues]
  cache-memory: true
safe-outputs:
  create-issue:
    max: 1
    title-prefix: "[learnings] "
    labels: [self-improvement, automation]
    close-older-issues: true
tracker-id: learning-aggregator
concurrency:
  group: learning-aggregator
  cancel-in-progress: false
---

# Learning Aggregator CI

You are the outer loop's **inspect** step. You read accumulated learnings across all time, find patterns, and produce a ranked gap report.

## Your skill

Read `.claude/skills/learning-aggregator/SKILL.md` in full and follow its process. That file defines the grouping logic, recurrence computation, gap classification, and promotion threshold.

This is a CI run, not an interactive session. Apply rule 2 from the "Adapting skills for single-shot gh-aw runs" section of `AGENTS.md`: run the aggregation as a batch without interactive prompts.

## Rules

1. Read all files in `.learnings/`: `LEARNINGS.md`, `ERRORS.md`, `FEATURE_REQUESTS.md`. If empty, call noop.
2. Parse each entry's metadata: `Pattern-Key`, `Priority`, `Status`, `Area`, `Recurrence-Count`.
3. Group entries by `Pattern-Key` (exact match only).
4. For each group: count recurrences, count distinct tasks, compute time window, collect evidence.
5. Flag entries without `Pattern-Key` as ungrouped.
6. Classify each group's gap type: knowledge gap, tool gap, skill gap, ambiguity, reasoning failure.
7. Rank groups: promotion-ready first (3+ recurrences across 2+ tasks), then approaching threshold, then by priority.
8. Do not modify repository files.

## Output

Create one issue with this structure:

```markdown
## Weekly Learning Aggregation

**Scan date**: YYYY-MM-DD
**Entries scanned**: N
**Pattern groups**: M
**Promotion candidates**: K

### Promotion-Ready (3+ recurrences)

| Pattern-Key | Recurrences | Gap type | Prevention rule |
|------------|-------------|----------|-----------------|
| ... | ... | ... | ... |

### Approaching Threshold

| Pattern-Key | Recurrences | Gap type | Notes |
|------------|-------------|----------|-------|
| ... | ... | ... | ... |

### Ungrouped Entries

[List entries without Pattern-Key that need manual categorization]
```

## Noop

Call `noop` if:
- `.learnings/` directory does not exist or is empty
- All entries are already promoted (status: `promoted_to_skill`)
- No new entries since last aggregation run

## Style

Follow the writing rules in `AGENTS.md`. Tables over prose. Evidence over opinion.
