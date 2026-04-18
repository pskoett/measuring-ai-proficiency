# The Agent Factory Chain

How the workflows in this repo chain together into a spec, plan, implement, review, learn loop, and how the skills library plugs in underneath.

## Layered architecture

```
+-------------------------------------------------------------+
|                     GitHub Actions Runtime                   |
|  (triggers, permissions, sandboxing, safe outputs, MCP)      |
+-----------------------------+-------------------------------+
                              |
+-----------------------------+-------------------------------+
|                    gh-aw Adapter Layer                       |
|  (frontmatter, handoff logic, label semantics)              |
|                                                              |
|  spec-refiner.md          reviewer.md                        |
|  implementer-dispatcher.md self-improvement-meta.md          |
|  simplify-and-harden-ci.md learning-aggregator-ci.md         |
|  eval-creator-ci.md        ci-cleaner.md                     |
|  conflict-resolver.md      contribution-checker.md           |
|  ai-proficiency-pr-review.md ai-proficiency-weekly-report.md |
|  issue-triage.md           plan-merged-dispatcher.yml        |
|  pr-fix.md                 trigger-plan.yml                  |
+-----------------------------+-------------------------------+
                              | reads skills from
                              v
+-------------------------------------------------------------+
|                    Agent Skills Library                      |
|  (.claude/skills/ in this repo)                             |
|                                                              |
|  plan-interview/       intent-framed-agent/                  |
|  simplify-and-harden/  learning-aggregator/                  |
|  eval-creator/         measure-ai-proficiency/               |
|  context-surfing/      verify-gate/                          |
|  customize-measurement/ agentic-workflow/                    |
|  pre-flight-check/                                           |
+-------------------------------------------------------------+

+-------------------------------------------------------------+
|                    Observability Layer                       |
|  (session transcripts, artifact storage, learning loop)     |
|                                                              |
|  Each gh-aw run uploads an `agent` artifact:                |
|    agent-stdio.log  (full conversation transcript)          |
|    agent_usage.json (token usage)                           |
|    safeoutputs.jsonl (actions taken)                        |
|    sandbox/agent/logs/ (structured tool logs)               |
|                                                              |
|  Retention: 90 days (GitHub Actions artifact storage)       |
|  .entire/metadata/ — schema docs, not raw data              |
+-----------------------------+-------------------------------+
                              | learning-aggregator-ci reads weekly
                              v
+-------------------------------------------------------------+
|                    Learning Loop                             |
|  .learnings/LEARNINGS.md + transcript-derived patterns      |
|  self-improvement-meta writes durable guardrails to repo    |
+-------------------------------------------------------------+
```

The adapter layer is thin on purpose. It owns GitHub-specific concerns: when to trigger, what permissions to request, which safe outputs to configure, how to move labels around to hand off to the next workflow. It does **not** own the agent's internal process. That lives in the skills.

Why this matters: the same skill runs in Claude Code on your laptop, in Codex CLI in a terminal, and in gh-aw in GitHub Actions. One canonical definition, three runtime surfaces. Update the skill once, every consumer gets the fix.

## The chain at a glance

```
issues.opened [needs-spec]
       |
       v
+----------------------+
|   spec-refiner       |   reads .claude/skills/plan-interview/SKILL.md
|                      |   classifies issue: plan-worthy, direct-route, or blocked
+----------+-----------+
           |
           +--[plan-worthy]------------------------------------------+
           |   writes docs/plans/plan-NNN-<slug>.md with implementer  |
           |   recommendation                                          |
           |   labels needs-plan                                       |
           |   v                                                       |
           |   (human reviews + merges plan PR)                       |
           |   |                                                       |
           |   v                                                       |
           | +----------------------+                                  |
           | | plan-merged-         |   plain GitHub Actions workflow  |
           | | dispatcher           |   writes plan checklist onto     |
           | +----------+-----------+   source issue body              |
           |            |               labels ready-for-implementation|
           |            v               <-----------------------------+
           |
           +--[direct route]---> labels impl:copilot + ready-for-implementation
           |                     posts comment explaining fast-track
           |
           +--[blocked/terminal]-> labels blocked-on-human
                                   posts comment; human takes next action
           |
           v (ready-for-implementation)
+----------------------+
|  implementer-        |   reads impl:* label on source issue
|  dispatcher          |   auto-assigns source issue to chosen agent
+----------+-----------+
           | opens PR
           v
       +---+--------------------+
       |                        |
  Claude Opus 4.6          Copilot cloud agent
  Claude Sonnet 4.6        Codex GPT-5.4
       |                        |
       +------------+-----------+
                    v
+----------------------+
|   reviewer           |   reads .claude/skills/intent-framed-agent/SKILL.md
|                      |   detects implementer, applies calibration
+----------+-----------+
           | labels ai-reviewed | needs-changes | spec-drift | fast-track
           v
       +---+----+
       |        |
  needs-      ai-
  changes   reviewed
       |        |
       v        v
+---------+ +---------+
| /pr-fix | |  human  |
|         | |  merge  |
+---------+ +---------+
     | loops back
     v
(eventually merged)

PR labeled needs-rebase?
            |
            v
+---------------------------+
| conflict-resolver         |   merges origin/main into PR branch
+---------------------------+
  clean merge: push + remove needs-rebase
  conflicts:   add blocked-on-human + comment with file list

                  | (nightly, independent of the main chain)
                  v
       +---------------------------+
       | self-improvement-meta     |   reads workflow logs and .learnings/
       +------------+--------------+
                    | reads logs from all runs in last 24h
                    | opens PR updating AGENTS.md and workflow files
                    v
              permanent
              guardrails

                  | (weekly, independent of the main chain)
                  v
       +---------------------------+
       | learning-aggregator-ci    |   reads .learnings/ + agent artifact transcripts
       +------------+--------------+
                    | downloads agent artifacts from all factory workflow runs (last 7 days)
                    | merges explicit learnings + transcript-derived patterns
                    | creates gap report issue with promotion candidates
                    v
              transcript-derived
              pattern candidates
              (routed to self-improvement-meta for PR creation)
```

## The implementer routing decision

As of April 2026, the implementer step in the chain has four choices, all bundled with the Copilot subscription:

| Implementer | Default use case | Why |
|-------------|------------------|-----|
| **Claude Opus 4.6** | Complex, multi-file, architecturally risky | Strongest reasoning for precise spec adherence |
| **Claude Sonnet 4.6** | Single-component features with clear scope | Claude reasoning at lower cost and latency |
| **Copilot cloud agent** | Trivial changes, dependency bumps, mechanical edits | Fast, cheap, bundled |
| **Codex GPT-5.4** | Opportunistic, A/B data, different reasoning style | Strong on common patterns |

`spec-refiner` classifies each issue and routes it. For plan-worthy issues, it writes a recommendation into the plan file itself. A human reviewing the plan PR sees the recommendation. When the plan PR merges, `plan-merged-dispatcher` labels the source issue `ready-for-implementation`; `implementer-dispatcher` then auto-assigns that issue to the chosen agent based on its `impl:*` label. One plan, one source issue, one PR.

For direct-route issues, `spec-refiner` skips the plan file, applies `impl:copilot` and `ready-for-implementation`, and calls `assign-to-agent` directly in the same run. Copilot is assigned without a plan PR or human merge gate and without depending on `implementer-dispatcher`.

This is a deliberate human-in-the-loop decision point for plan-worthy work. The routing rule is "complexity warrants Opus" and only a human can decide, for a given repo on a given day, whether the cost or latency difference is worth it. The spec-refiner recommends, the human chooses, and `reviewer` calibrates the review based on who actually produced the code.

See `AGENTS.md` for the full routing guidelines.

## Why many specialized workflows instead of one

Specialization. Each workflow does one job well. When one fails, you can isolate the failure. When one improves, you can measure the improvement independently. They compose through GitHub events (labels, comments, files) rather than through direct coupling. This is choreography, not orchestration.

## How state moves through the chain

State lives in GitHub, not in memory. Each agent starts cold. The spec file must be written back to the repo so the planner can read it. The source issue must be labeled `ready-for-implementation` so the dispatcher can find it. The reviewer must read the plan file from disk. Every handoff is mediated by a file, a label, or a PR.

This makes the chain debuggable. You can inspect the state at any point by looking at the repo.

## How to pause the chain

Add the `human-review` label to any issue or PR. All agents in this pack check for that label at run start and call `noop` if they see it. This is the emergency stop.

## How to fast-forward the chain

Skip phases for simple changes by manually labeling. Want to skip spec-refinement? Label the issue `needs-plan` directly. `trigger-plan.yml` will detect the absence of a plan file, skip the `spec-refined` guard, and transition to `ready-for-implementation` automatically. Want to skip the reviewer? Label the PR `human-review` and review it yourself.

The chain is opinionated, not rigid. You control which steps run.

## How the outer loop closes

`self-improvement-meta` runs nightly. It reads the run logs of every agent that ran in the last 24 hours, extracts failure patterns, and opens a PR that updates `AGENTS.md` or the individual workflow files. When the PR merges, the next run of the affected agent reads the updated instructions.

`learning-aggregator-ci` runs weekly (Monday). It reads both `.learnings/` entries AND the `agent` artifact transcripts from recent factory workflow runs. Transcript analysis surfaces patterns that agents never explicitly logged — retry loops, noop misfires, approach changes. Transcript-derived patterns feed into the same `.learnings/LEARNINGS.md` write path via `self-improvement-meta`.

This is the two-loop model shipped as GitHub Actions. Inner loops run per-task. The outer loop runs per-day (telemetry) and per-week (transcripts). Both are visible in the repo, inspectable as markdown, and owned by the team.

## The human's job

Three decisions (for plan-worthy issues):

1. **At spec**: is this plan file correct? If yes, merge. If no, edit and re-run.
2. **At review**: should this PR ship? The reviewer did the first pass. You do the final one.
3. **At learning**: is this prevention rule worth keeping? The meta-agent proposes. You approve.

For direct-route issues, decision 1 is skipped. The agent goes straight to implementation after spec-refiner classifies the issue.

Everything else is automated. That is the point.

See [`FACTORY_STATE_MACHINE.md`](FACTORY_STATE_MACHINE.md) for the one-page operator reference: label-to-lane mapping, workflow trigger table, and the happy-path sequence diagram.
