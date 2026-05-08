---
eval-id: EVAL-007
source-learning: LRN-003
target: AGENTS.md
method: grep-check
expect: found
pattern: "GitHub GraphQL connections cap `first` and `last` at 100."
created: 2026-05-08
last-run: 2026-05-08
last-result: skip
---

# EVAL-007: GitHub GraphQL connection page-size rule stays promoted

## Scenario

`sync-factory-state.yml` failed on four consecutive scheduled runs because it queried `items(first: 250)` against GitHub GraphQL, which rejects connection sizes above 100. `LRN-003` promotes the prevention rule into the shared harness files so future workflow edits do not repeat the same mistake.

## Regression path

If the shared workflow guidance drops this rule, future agents can reintroduce oversized GraphQL connection requests in workflow code or prompts. This eval keeps the promoted rule anchored in `AGENTS.md`.

## Check

`AGENTS.md` must contain the literal string `GitHub GraphQL connections cap \`first\` and \`last\` at 100.`.

## Pass condition

`grep -qF 'GitHub GraphQL connections cap \`first\` and \`last\` at 100.' AGENTS.md` exits with code 0.

## Fail condition

The promoted rule has been removed from `AGENTS.md`. The shared harness no longer tells workflow authors to cap GitHub GraphQL page sizes at 100 and paginate larger scans.
