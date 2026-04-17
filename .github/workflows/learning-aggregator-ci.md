---
on:
  schedule: weekly on monday
  workflow_dispatch:
timeout-minutes: 15
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
  bash:
    - "gh"
    - "gh run"
    - "gh api"
    - "jq"
    - "cat"
    - "grep"
    - "head"
    - "tail"
    - "wc"
    - "ls"
    - "find"
    - "sort"
    - "uniq"
    - "mkdir"
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

You are the outer loop's **inspect** step. You read accumulated learnings across all time and recent session transcripts, find patterns, and produce a ranked gap report.

## Your skill

Read `.claude/skills/learning-aggregator/SKILL.md` in full and follow its process. That file defines the grouping logic, recurrence computation, gap classification, and promotion threshold.

This is a CI run, not an interactive session. Apply rule 2 from the "Adapting skills for single-shot gh-aw runs" section of `AGENTS.md`: run the aggregation as a batch without interactive prompts.

## Phase 1: Read learnings files

1. Read all files in `.learnings/`: `LEARNINGS.md`, `ERRORS.md`, `FEATURE_REQUESTS.md`.
2. Parse each entry's metadata: `Pattern-Key`, `Priority`, `Status`, `Area`, `Recurrence-Count`.
3. Group entries by `Pattern-Key` (exact match only).
4. For each group: count recurrences, count distinct tasks, compute time window, collect evidence.
5. Flag entries without `Pattern-Key` as ungrouped.

If `.learnings/` does not exist or all files are empty and no transcript artifacts are available (Phase 2 below), call noop.

## Phase 2: Analyze session transcript artifacts

Every factory workflow run uploads an `agent` artifact containing the session transcript. Download and analyze recent transcripts to find patterns not yet logged in `.learnings/`.

### Step 1: Discover recent factory workflow runs

List the last 20 runs for each agent-backed factory workflow:

```bash
for workflow in spec-refiner reviewer implementer-dispatcher self-improvement-meta \
    ci-cleaner contribution-checker simplify-and-harden-ci eval-creator-ci \
    ai-proficiency-pr-review ai-proficiency-weekly-report issue-triage pr-fix \
    conflict-resolver; do
  gh run list --workflow "${workflow}.lock.yml" --limit 20 \
    --json databaseId,displayTitle,conclusion,createdAt,event,headBranch \
    2>/dev/null || true
done
```

Focus on runs from the last 7 days. Skip runs with conclusion `skipped` or `cancelled`.

### Step 2: Download transcript artifacts

For each run ID collected above, attempt to download the `agent` artifact:

```bash
mkdir -p /tmp/transcripts/<run-id>
gh run download <run-id> --name agent --dir /tmp/transcripts/<run-id> 2>/dev/null || true
```

Skip silently if the artifact does not exist or has expired. Do not fail if no transcripts are available.

### Step 3: Parse transcripts for patterns

For each downloaded transcript, read `agent-stdio.log`. Apply the transcript analysis method from the "GitHub Actions Transcript Analysis" section of `.claude/skills/learning-aggregator/SKILL.md`:

- Look for retry loops (same tool call repeated 3+ times)
- Look for approach changes mid-task
- Look for error messages in tool outputs
- Look for noop calls on runs that should have produced output
- Compare workflow name and run event to understand context

Map each finding to a `Pattern-Key` using the taxonomy from the skill. Merge with findings from Phase 1.

### Step 4: Deduplicate against existing learnings

Before adding any transcript-derived pattern to the output, check whether a matching `Pattern-Key` already exists in `.learnings/LEARNINGS.md` with `Status: promoted_to_skill` OR `Status: pending`. If a pending entry already covers the same pattern, increment its recurrence count in the issue body rather than creating a new row.

## Phase 3: Classify and rank

6. Classify each group's gap type: knowledge gap, tool gap, skill gap, ambiguity, reasoning failure.
7. Rank groups: promotion-ready first (3+ recurrences across 2+ tasks), then approaching threshold, then by priority.
8. For transcript-derived patterns, label the source as `transcript` in the evidence field.
9. Do not modify repository files.

## Output

Create one issue with this structure:

```markdown
## Weekly Learning Aggregation

**Scan date**: YYYY-MM-DD
**Learnings entries scanned**: N
**Transcript artifacts analyzed**: M
**Pattern groups**: K
**Promotion candidates**: P

### Promotion-Ready (3+ recurrences)

| Pattern-Key | Recurrences | Gap type | Source | Prevention rule |
|------------|-------------|----------|--------|-----------------|
| ... | ... | ... | learnings/transcript | ... |

### Approaching Threshold

| Pattern-Key | Recurrences | Gap type | Source | Notes |
|------------|-------------|----------|--------|-------|
| ... | ... | ... | ... | ... |

### Transcript-Only Findings (not yet in .learnings/)

[Patterns found only in transcripts that have not been logged manually. These
are candidates for adding to .learnings/LEARNINGS.md in the next
self-improvement-meta PR.]

### Ungrouped Entries

[List entries without Pattern-Key that need manual categorization]
```

## Noop

Call `noop` if:
- `.learnings/` directory does not exist or is empty AND no transcript artifacts are found
- All entries are already promoted (status: `promoted_to_skill`) AND no new transcript patterns found
- No new entries or transcripts since last aggregation run

## Self-improvement feedback path

Transcript-derived patterns that cross the promotion threshold should be noted in the issue body with the prefix `**TRANSCRIPT CANDIDATE**`. These are routed to the next `self-improvement-meta` run, which adds them to `.learnings/LEARNINGS.md` via the standard PR path.

Do not write directly to `.learnings/LEARNINGS.md` from this workflow.

## Style

Follow the writing rules in `AGENTS.md`. Tables over prose. Evidence over opinion.

## Session capture

This workflow's full session is automatically captured in the `agent` artifact for this run. The artifact includes the prompt, all tool calls, tool outputs, and token usage. Because this workflow is the consumer of transcript artifacts, it does not recurse on its own transcript.
