---
on:
  issues:
    types: [labeled]
  workflow_dispatch:
if: github.event.label.name == 'ready-for-implementation' || github.event_name == 'workflow_dispatch'
timeout-minutes: 5
engine:
  id: copilot
  model: gpt-5.4
permissions:
  contents: read
  issues: read
tools:
  github:
    toolsets: [issues, repos]
safe-outputs:
  assign-to-agent:
    target-repo: ${{ github.repository }}
  assign-to-user:
    target-repo: ${{ github.repository }}
    allowed: ["claude[bot]", "codex[bot]"]
    max: 1
  add-comment:
    max: 1
  add-labels:
    allowed: [assigned-to-agent]
    max: 1
---

# Implementer Dispatcher

You auto-assign issues to the correct cloud coding agent based on the issue's implementer label. This removes the need for humans to assign each issue individually.

The `ready-for-implementation` label is applied directly to the source issue by `plan-merged-dispatcher` after the plan PR merges. There is no sub-issue layer.

## Process

### Step 1: Read the implementer label from this issue

Look for one of these labels on the issue that triggered this run:

- `impl:copilot` — assign to the Copilot cloud agent via `assign-to-agent`.
- `impl:claude-opus`, `impl:claude-sonnet` — assign to the Claude Partner Agent via `assign-to-user` with assignee `claude[bot]`.
- `impl:codex` — assign to the Codex Partner Agent via `assign-to-user` with assignee `codex[bot]`.

If the issue has no implementer label, default to `impl:copilot`. Post a comment noting that no implementer was specified and the default was used.

### Step 2: Assign the issue

Take exactly one assignment action based on the label:

- **`impl:copilot`**: call `assign-to-agent` (Copilot is the default agent). Post a comment: "Assigned to Copilot cloud agent based on label `impl:copilot`." Add the `assigned-to-agent` label.
- **`impl:claude-opus` or `impl:claude-sonnet`**: call `assign-to-user` with assignee `claude[bot]`. Post a comment: "Assigned to Claude Partner Agent based on label `impl:claude-opus`." (substitute the actual label). Add the `assigned-to-agent` label. Note: Claude Partner Agent is a single bot; the `-opus`/`-sonnet` distinction is advisory only until GitHub exposes per-model routing.
- **`impl:codex`**: call `assign-to-user` with assignee `codex[bot]`. Post a comment: "Assigned to Codex Partner Agent based on label `impl:codex`." Add the `assigned-to-agent` label.

If `assign-to-user` fails because the bot handle is not enabled as a Partner Agent on this repo, post a comment naming the failure and call `noop`. Do not retry with a different handle.

## Noop conditions

Call `noop` if:
- The issue is labeled `human-review`
- The issue already has the `assigned-to-agent` label (prevent double-dispatch)

## Style

Follow the writing rules in `AGENTS.md`. One-line comments. No filler.
