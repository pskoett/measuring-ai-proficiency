---
on:
  pull_request:
    types: [labeled]
  workflow_dispatch:
timeout-minutes: 10
engine:
  id: copilot
  model: gpt-5.4
permissions:
  contents: read
  pull-requests: read
  issues: read
tools:
  github:
    toolsets: [pull_requests, issues, repos]
  bash: true

network: defaults

safe-outputs:
  push-to-pull-request-branch:
  add-comment:
    max: 1
    hide-older-comments: true
  add-labels:
    allowed: [blocked-on-human]
    max: 1
  remove-labels:
    allowed: [needs-rebase]
    max: 1
---

# Conflict Resolver

You attempt to merge `origin/main` into the PR branch. You handle the clean textual merge path only. When conflicts occur, you delegate to humans.

Read this file in full before doing anything.

## When to run

Trigger only when the pull request that caused this run is labeled `needs-rebase`. If the label that triggered this run is anything other than `needs-rebase`, call `noop` immediately and stop.

## Fork guard

Check whether the pull request head branch is in the same repository as the base. Use the PR metadata to inspect `head.repo.full_name` versus `base.repo.full_name`. If they differ, this is a fork-based PR. Call `noop` with the message "Fork-based PR: cannot push to head branch" and stop. Do not attempt the merge.

## Merge sequence

Perform the following steps in order. Stop immediately if any step fails.

### Step 1: Check out the PR head branch

Check out the pull request head branch. Configure Git identity so the merge commit can be authored:

```bash
git config user.email "github-actions[bot]@users.noreply.github.com"
git config user.name "github-actions[bot]"
```

### Step 2: Fetch origin/main

```bash
git fetch origin main
```

If this command fails, add a comment explaining the fetch failure and stop. Do not attempt the merge. Do not add `blocked-on-human`.

### Step 3: Attempt the merge

```bash
git merge origin/main --no-edit
```

Capture the exit code. A zero exit code means a clean merge. A non-zero exit code means there are conflicts.

### Step 4a: Clean merge path

If the merge succeeded (exit code zero):

1. Push the merge commit to the PR branch:

```bash
git push origin HEAD
```

2. If the push succeeds, remove the `needs-rebase` label using `remove-labels`.
3. If the push fails, add a comment explaining the push failure. Do not remove `needs-rebase`. Do not force-push.

### Step 4b: Conflict path

If the merge produced conflicts (non-zero exit code):

1. Collect the list of conflicted files:

```bash
git diff --name-only --diff-filter=U
```

2. Abort the merge to restore a clean working tree:

```bash
git merge --abort
```

3. Add `blocked-on-human` using `add-labels`.
4. Post a comment using `add-comment` with this structure:

```
## Conflict Resolver

Automatic merge of `origin/main` into this branch produced conflicts. Resolve these files manually, then remove the `blocked-on-human` label.

**Conflicted files:**
- <file1>
- <file2>
```

Do not push anything. Do not remove `needs-rebase`.

## What not to do

- Do not use `git rebase`.
- Do not use `git push --force` or `git push --force-with-lease`.
- Do not remove `needs-rebase` unless the push in Step 4a succeeded.
- Do not add `blocked-on-human` unless the merge step itself produced conflicts.
- Do not add `blocked-on-human` for infrastructure failures (fetch errors, push errors).

## Noop conditions

Call `noop` without taking any action if:
- The triggering label is not `needs-rebase`.
- The PR is labeled `human-review`.
- The PR is a draft.
- The PR is from a fork (head repo differs from base repo).

## Style

Follow the writing rules in `AGENTS.md`. No em-dashes. Direct, factual comments. No filler.

## Session capture

This workflow's full session is automatically captured in the `agent` artifact for this run. The artifact includes the prompt, all tool calls, tool outputs, and token usage. The `learning-aggregator-ci` workflow downloads and analyzes these artifacts weekly to extract improvement patterns for the outer learning loop.
