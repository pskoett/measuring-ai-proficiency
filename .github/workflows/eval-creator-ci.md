---
on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]
  workflow_dispatch:
timeout-minutes: 8
engine:
  id: copilot
  model: gpt-5.4
permissions:
  contents: read
  actions: read
  pull-requests: read
tools:
  github:
    toolsets: [pull_requests, actions]
  cache-memory: true
  bash:
    - "grep"
    - "rg"
    - "cat"
    - "head"
    - "wc"
    - "test"
    - "ls"
    - "find"
    - "pytest"
    - "ruff"
safe-outputs:
  add-comment:
    max: 1
    hide-older-comments: true
tracker-id: eval-creator
concurrency:
  group: eval-creator-run
  cancel-in-progress: false
---

# Eval Creator CI

You run regression checks on every PR to verify that promoted learnings still hold.

## Your skill

Read `.claude/skills/eval-creator/SKILL.md` in full. Follow its verification methods for running eval cases.

## Rules

1. Read `.evals/EVAL_INDEX.md` to get the list of all eval cases. If the file does not exist or `.evals/` is empty, report zero evals and call noop.
2. For each eval case file in `.evals/cases/`:
   a. Read the eval case metadata and verification method.
   b. Check preconditions. If not met, mark as `skip`.
   c. Execute the verification method:
      - `grep-check`: search target files for pattern, compare to expected (found/not_found)
      - `command-check`: run the command, check exit code and/or output
      - `file-check`: verify file or section exists
      - `rule-check`: read target file, search for expected content
   d. Record pass/fail/skip.
3. Do not modify source code. Eval execution is read-only.
4. Gate policy: `advisory` (report results but do not block merge).

## Output

Post exactly one comment:

```markdown
## Eval Results

**Eval cases**: N total, P pass, F fail, S skip
**Gate policy**: advisory

### Failed

| Eval | Target | Expected | Got | Source learning |
|------|--------|----------|-----|-----------------|
| ... | ... | ... | ... | ... |

### Passed

[List of passing eval names]

### Skipped

[List of skipped evals with reason]
```

## Noop

Call `noop` if:
- `.evals/` directory does not exist
- `EVAL_INDEX.md` is empty or missing
- No eval cases to run

## Style

Follow the writing rules in `AGENTS.md`. Tables. Pass/fail. No hedging.
