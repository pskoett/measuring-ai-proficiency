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
|   spec-refiner.md    reviewer.md    self-improvement-meta.md
+-----------------------------+-------------------------------+
                              | reads skills from
                              v
+-------------------------------------------------------------+
|                    Agent Skills Library                      |
|  (.claude/skills/ in this repo)                             |
|                                                              |
|   plan-interview/    dx-data-navigator/   self-improvement/  |
|   intent-framed-agent/              context-surfing/        |
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
|                      |   recommends implementer in plan file
+----------+-----------+
           | writes docs/plans/plan-NNN.md with implementer recommendation
           | labels needs-plan
           v
+----------------------+
|   /plan              |   from githubnext/agentics
+----------+-----------+
           | creates sub-issues labeled ready-for-implementation
           v
+----------------------+
|  human assigns       |   via github.com web UI Agents tab
|  to chosen agent     |   picks model per spec-refiner recommendation
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
|   reviewer       |   reads .claude/skills/dx-data-navigator/SKILL.md
|                      |         .claude/skills/intent-framed-agent/SKILL.md
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

                  | (nightly, independent of the main chain)
                  v
       +---------------------------+
       | self-improvement-meta     |   reads .claude/skills/self-improvement/SKILL.md
       +------------+--------------+
                    | reads logs from all runs in last 24h
                    | opens PR updating AGENTS.md and workflow files
                    v
              permanent
              guardrails
```

## The implementer routing decision

As of April 2026, the implementer step in the chain has four choices, all bundled with the Copilot subscription:

| Implementer | Default use case | Why |
|-------------|------------------|-----|
| **Claude Opus 4.6** | Complex, multi-file, architecturally risky | Strongest reasoning for precise spec adherence |
| **Claude Sonnet 4.6** | Single-component features with clear scope | Claude reasoning at lower cost and latency |
| **Copilot cloud agent** | Trivial changes, dependency bumps, mechanical edits | Fast, cheap, bundled |
| **Codex GPT-5.4** | Opportunistic, A/B data, different reasoning style | Strong on common patterns |

`spec-refiner` assesses the plan and writes a recommendation into the plan file itself. A human reviewing the plan PR sees the recommendation and decides whether to follow it when they assign sub-issues via the github.com web UI Agents tab.

This is a deliberate human-in-the-loop decision point. The routing rule is "complexity warrants Opus" and only a human can decide, for a given repo on a given day, whether the cost or latency difference is worth it. The spec-refiner recommends, the human chooses, and `reviewer` calibrates the review based on who actually produced the code.

See `AGENTS.md` for the full routing guidelines.

## Why five agents instead of one

Specialization. Each agent does one job well. When one fails, you can isolate the failure. When one improves, you can measure the improvement independently. They compose through GitHub events (labels, comments, files) rather than through direct coupling. This is choreography, not orchestration.

## How state moves through the chain

State lives in GitHub, not in memory. Each agent starts cold. The spec file must be written back to the repo so the planner can read it. The plan sub-issues must be labeled so the implementer can find them. The reviewer must read the plan file from disk. Every handoff is mediated by a file, a label, or a PR.

This makes the chain debuggable. You can inspect the state at any point by looking at the repo.

## How to pause the chain

Add the `human-review` label to any issue or PR. All agents in this pack check for that label at run start and call `noop` if they see it. This is the emergency stop.

## How to fast-forward the chain

Skip phases for simple changes by manually labeling. Want to skip spec-refinement? Label the issue `needs-plan` directly. Want to skip the reviewer? Label the PR `human-review` and review it yourself.

The chain is opinionated, not rigid. You control which steps run.

## How the outer loop closes

`self-improvement-meta` runs nightly. It reads the run logs of every agent that ran in the last 24 hours, extracts failure patterns, and opens a PR that updates `AGENTS.md` or the individual workflow files. When the PR merges, the next run of the affected agent reads the updated instructions.

This is the two-loop model shipped as GitHub Actions. Inner loops run per-task. The outer loop runs per-day. Both are visible in the repo, inspectable as markdown, and owned by the team.

## The human's job

Three decisions:

1. **At spec**: is this plan file correct? If yes, merge. If no, edit and re-run.
2. **At review**: should this PR ship? The reviewer did the first pass. You do the final one.
3. **At learning**: is this prevention rule worth keeping? The meta-agent proposes. You approve.

Everything else is automated. That is the point.
