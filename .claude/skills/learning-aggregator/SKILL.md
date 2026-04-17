---
name: learning-aggregator
description: "[Beta] Cross-session analysis of accumulated .learnings/ files. Reads all entries, groups by pattern_key, computes recurrence across sessions, and outputs ranked promotion candidates. This is the outer loop's inspect step — it turns raw learning data into actionable gap reports. Use on a regular cadence (weekly, before major tasks, or at session start for critical projects). Can be invoked manually or scheduled."
---

# Learning Aggregator

Reads accumulated `.learnings/` files across all sessions, finds patterns, and produces a ranked list of promotion candidates. This is the outer loop's **inspect** step.

Without this skill, `.learnings/` is a write-only log. Patterns accumulate but nobody synthesizes them. The same gap resurfaces two weeks later because no one looked.

## When to Use

- **Weekly cadence** — scheduled or manual, review accumulated learnings
- **Before major tasks** — check if the task area has known patterns
- **After a burst of sessions** — consolidate findings from a sprint or incident
- **When self-improvement flags `promotion_ready`** — verify the flag with full context

## What It Produces

A **gap report** — a ranked list of patterns that have crossed (or are approaching) the promotion threshold, with evidence and recommended actions.

## Step 1: Read All Learning Files

Read these files in `.learnings/`:

| File | Contains |
|------|----------|
| `LEARNINGS.md` | Corrections, knowledge gaps, best practices, recurring patterns |
| `ERRORS.md` | Command failures, API errors, exceptions |
| `FEATURE_REQUESTS.md` | Missing capabilities |

Parse each entry's metadata:
- `Pattern-Key` — the stable deduplication key
- `Recurrence-Count` — how many times this pattern has been seen
- `First-Seen` / `Last-Seen` — date range
- `Priority` — low / medium / high / critical
- `Status` — pending / promotion_ready / promoted / dismissed
- `Area` — frontend / backend / infra / tests / docs / config
- `Related Files` — which parts of the codebase are affected
- `Source` — conversation / error / user_feedback / simplify-and-harden
- `Tags` — free-form labels

## Step 2: Group and Aggregate

Group entries by `Pattern-Key`. For each group:

1. **Sum recurrences** across all entries with the same key
2. **Count distinct tasks** — how many different sessions/tasks encountered this
3. **Compute time window** — days between First-Seen and Last-Seen
4. **Collect all related files** — union of all entries' file references
5. **Take highest priority** across entries in the group
6. **Collect evidence** — the Summary and Details from each entry

For entries without a `Pattern-Key`, use conservative grouping only:
- **Exact match**: Same `Area` AND at least 2 identical `Tags`
- **File overlap**: Same `Related Files` path (exact path match, not substring)
- **Do NOT fuzzy-match** on Summary text — false groupings are worse than ungrouped entries

Flag ungrouped entries separately with a recommendation to assign a `Pattern-Key`. Ungrouped entries are common and expected — they may be one-off issues or genuinely novel problems.

## Step 3: Rank and Classify

### Promotion Threshold
An entry is **promotion-ready** when:
- `Recurrence-Count >= 3` across the group
- Seen in `>= 2 distinct tasks`
- Within a `30-day window`

### Approaching Threshold
An entry is **approaching** when:
- `Recurrence-Count >= 2` or
- `Priority: high/critical` with any recurrence

### Classification
For each promotion candidate, classify the gap type:

| Gap Type | Signal | Fix Target |
|----------|--------|------------|
| **Knowledge gap** | Agent didn't know X | Update project instruction files (CLAUDE.md, AGENTS.md, .github/copilot-instructions.md) |
| **Tool gap** | Agent improvised around missing capability | Add or update MCP tool / script |
| **Skill gap** | Same behavior pattern keeps failing | Create or update a skill (use `/skill-creator`, validate with `quick_validate.py`, register `skill-check` eval) |
| **Ambiguity** | Conflicting interpretations of spec/prompt | Tighten instructions or add examples |
| **Reasoning failure** | Agent had the knowledge but reasoned wrong | Add explicit decision rules or constraints |

## Step 4: Produce Gap Report

Output a structured report:

```markdown
## Learning Aggregator: Gap Report

**Scan date:** YYYY-MM-DD
**Period:** [since date] to [now]
**Entries scanned:** N
**Patterns found:** N
**Promotion-ready:** N
**Approaching threshold:** N

### Promotion-Ready Patterns

#### 1. [Pattern-Key] — [Summary]

- **Recurrence:** N times across M tasks
- **Window:** First-Seen → Last-Seen
- **Priority:** high
- **Gap type:** knowledge gap
- **Area:** backend
- **Related files:** path/to/file.ext
- **Evidence:**
  - [LRN-YYYYMMDD-001] Summary of first occurrence
  - [LRN-YYYYMMDD-002] Summary of second occurrence
  - [ERR-YYYYMMDD-001] Summary of related error
- **Recommended action:** Add rule to project instruction files (CLAUDE.md, AGENTS.md, .github/copilot-instructions.md): "[concise prevention rule]"
- **Eval candidate:** Yes — [description of what to test]

#### 2. ...

### Approaching Threshold

#### 1. [Pattern-Key] — [Summary]
- **Recurrence:** 2 times across 1 task
- **Needs:** 1 more recurrence or 1 more distinct task
- ...

### Ungrouped Entries (no Pattern-Key)

- [LRN-YYYYMMDD-005] "Summary" — needs pattern_key assignment
- ...

### Dismissed / Stale

- Entries with Last-Seen > 90 days ago and Status: pending → recommend dismissal
```

## Step 5: Handoff

The gap report feeds into:

1. **harness-updater agent** — takes promotion-ready patterns and applies them to project instruction files (CLAUDE.md, AGENTS.md, .github/copilot-instructions.md)
2. **eval-creator skill** — takes eval candidates and creates permanent test cases
3. **Human review** — for patterns classified as "reasoning failure" or "ambiguity" (these need human judgment)

## Filtering

- `--since YYYY-MM-DD` — only scan entries after this date
- `--min-recurrence N` — raise the promotion threshold
- `--area AREA` — filter to a specific area (frontend, backend, etc.)
- `--deep` — also analyze session traces (see Session Trace Analysis below)

## Session Trace Analysis

The outer loop reads from two complementary sources:

| Source | What it is | Cadence | Cost |
|--------|-----------|---------|------|
| `.learnings/` | Explicit entries written by self-improvement during sessions. Agent's own reflections: corrections, knowledge gaps, recurring patterns it noticed. | Every session (hot path) | Near-zero |
| Session transcripts | Full session transcripts from GitHub Actions `agent` artifacts: prompts, tool calls, outputs, token usage. Available for all gh-aw factory workflows. | Weekly or on-demand (cold path) | Moderate — download per run |

The default mode reads `.learnings/` and produces a gap report from what the agent explicitly logged. The `--deep` mode also analyzes session transcripts and merges findings from both sources.

### Why both sources matter

`.learnings/` captures what the agent **noticed and chose to log** — a curated subset. Session transcripts capture **everything that happened**, including patterns the agent worked around, retried, or never recognized as failures.

Examples of patterns visible in transcripts but absent from `.learnings/`:

- **Retry loops**: The same tool call repeated 3+ times with small variations. The agent eventually got it right but never logged the initial failures.
- **Noop patterns**: Workflows that called noop on runs that should have produced output — a signal of misconfigured triggers or overly strict noop conditions.
- **Worked-around test failures**: A test failed, the agent changed approach, the new approach passed, the original failure was forgotten.
- **Context handoff causes**: Which drift signals actually triggered handoffs, not just that handoffs happened.
- **Token/time anomalies**: Sessions with disproportionate cost vs output — a signal of inefficiency the agent is unaware of.
- **Spec drift**: Agent spending effort on out-of-scope work, visible in tool call sequences before a pivot.

These patterns are high-value for the outer loop because the agent can't self-report them. Session transcripts are the only source.

### When to trigger --deep mode

Trace analysis is **not** per-session. It's cadenced:

- **Weekly scheduled** (recommended minimum): after a sprint or burst of sessions
- **Post-incident**: when something went wrong and you want to understand why
- **Pre-promotion**: before committing a pattern to project instruction files, verify it actually recurs in real sessions
- **Manual invocation**: `/learning-aggregator --deep --since 7d`

Running trace analysis per-session would burn tokens without producing new signal — cross-session patterns only emerge over multiple sessions.

## GitHub Actions Transcript Analysis

Every factory workflow compiled with gh-aw uploads an `agent` artifact after the agent step completes. This artifact contains the full session transcript and is the primary source for `--deep` mode analysis.

### Artifact contents

| File | What it contains |
|------|-----------------|
| `agent-stdio.log` | Full conversation: the prompt, all tool calls, tool outputs, and agent reasoning in chronological order |
| `sandbox/agent/logs/` | Structured agent logs with timestamps and tool metadata |
| `safeoutputs.jsonl` | Structured record of every safe-output action the agent took (issue created, comment posted, etc.) |
| `agent_output.json` | The final structured output payload |
| `agent_usage.json` | Token usage: prompt tokens, completion tokens, total |

### Discovering artifacts

Use the GitHub CLI to list recent runs and download artifacts:

```bash
# List recent runs for a specific factory workflow
gh run list --workflow spec-refiner.lock.yml --limit 10 \
  --json databaseId,displayTitle,conclusion,createdAt,event,headBranch,headSha

# Download the agent artifact for a specific run
mkdir -p /tmp/transcripts/<run-id>
gh run download <run-id> --name agent --dir /tmp/transcripts/<run-id>

# Or via the API
gh api repos/{owner}/{repo}/actions/runs/{run-id}/artifacts
```

Artifact retention is 90 days by default (the gh-aw default). After 90 days, the artifact is deleted automatically.

### What to extract from a transcript

For each `agent-stdio.log` file, parse the conversation and look for:

1. **Tool call repetition** — same tool + similar args called 3+ times in sequence → likely a retry loop. Pattern-key: `retry-loop.<tool>`
2. **Noop on actionable input** — agent called noop but the triggering event clearly warranted action → Pattern-key: `noop-misfire.<workflow>`
3. **Error patterns in tool output** — responses containing `error`, `failed`, `Traceback`, `not found` before the agent recovered → Pattern-key: `error.<category>`
4. **Approach changes mid-task** — agent abandoning a path and restarting (visible as repeated similar tool calls with different parameters after an error) → Pattern-key: `approach-switch.<domain>`
5. **Token anomalies** — `agent_usage.json` showing token count more than 2x the median for similar workflows → Pattern-key: `cost.<workflow>`
6. **Spec drift signals** — tool calls accessing files or making changes clearly outside the stated scope → Pattern-key: `drift.<workflow>`

Each finding is mapped to the same taxonomy as self-improvement:
- `harden.*` — security, validation, permissions
- `simplify.*` — complexity, dead code, over-abstraction
- `process.*` — workflow ordering, handoff logic
- `spec.*` — scope adherence, plan compliance

### Privacy handling

Transcripts may contain content from issue bodies, commit messages, and PR descriptions. These can include PII (names, email addresses, code snippets from private contexts). When analyzing:

- Extract only the **structural patterns** (tool call sequences, error categories, retry counts)
- Do not copy raw transcript content into issues or `.learnings/` entries
- Do not include issue body excerpts unless they are already public on GitHub
- Summarize patterns in abstract terms: "agent retried file-read 5 times before succeeding" not the actual file content

### How the two sources merge in the gap report

When `--deep` runs, each pattern in the gap report gets a `sources` field:

```yaml
promotion_ready:
  - pattern_key: "retry-loop.file-read"
    recurrence_count: 5
    sources:
      - .learnings/LEARNINGS.md (2 entries)
      - transcript:spec-refiner/run-12345678 (3 occurrences)
    confidence: high  # appears in both sources
    evidence:
      - "LRN-20260401-001: File read retry on large repos"
      - "transcript:12345678: Same grep tool called 4 times with varying patterns"
      - "transcript:12345679: File not found on first attempt, succeeded on second"
```

A pattern in both sources is higher confidence than one from either alone.

### Reading traces with Entire (optional)

If [Entire](https://entire.io) is installed and enabled on this repo, the `--deep` flag also uses the Entire CLI for local Claude Code session transcripts:

```bash
# Check availability
entire --version

# List recent checkpoints as JSON
entire rewind --list

# Read a checkpoint's full transcript
entire explain --checkpoint <id> --full --no-pager
```

If `entire` is not installed, `--deep` uses only GitHub Actions artifact transcripts as described above. Entire and Actions artifact analysis are complementary:

| Source | Covers | Best for |
|--------|--------|----------|
| GitHub Actions artifacts | All gh-aw factory workflow runs | Automated factory patterns |
| Entire checkpoints | Local Claude Code sessions | Human-driven interactive patterns |

## Persistence

Reads `.learnings/` from the working directory. This is the only persistence mode — the skill does not integrate with external memory backends in interactive sessions. For CI-side durable storage across workflow runs, see `learning-aggregator-ci`, which can optionally back its state with gh-aw's `repo-memory` (git-branch persistence). The resulting branch is a normal git branch and can be fetched locally if desired, but the interactive skill itself only reads local files.

### Tracker-id in gap reports

Each promotion candidate in the gap report includes a `tracker` field set to the pattern-key. This tracker propagates through the full chain: harness-updater embeds it as a comment in project instruction files, eval-creator references it in eval cases. To audit the full lifecycle of a pattern, search for `tracker:[pattern-key]` across the repo and GitHub.

## What This Skill Does NOT Do

- Does not modify `.learnings/` files (read-only analysis)
- Does not apply promotions (that's harness-updater)
- Does not create evals (that's eval-creator)
- Does not fix code or run tests
- Does not replace human judgment for ambiguous patterns
- Does not run `--deep` trace analysis per-session — only on cadence or explicit invocation
- Does not require Entire — falls back to `.learnings/`-only mode when trace source is unavailable
