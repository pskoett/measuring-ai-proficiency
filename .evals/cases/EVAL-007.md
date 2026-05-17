---
eval-id: EVAL-007
source-learning: LRN-003
target: AGENTS.md
method: grep-check
expect: found
pattern: "GitHub GraphQL connections cap `first` at 100 records."
created: 2026-05-17
last-run: 2026-05-17
last-result: skip
---

# EVAL-007: GraphQL page-limit guardrail stays in the harness

## Scenario

On 2026-05-16, `sync-factory-state.yml` failed its scheduled full reconcile because the Projects v2 query requested `items(first: 250)`. GitHub rejects any GraphQL connection that asks for more than 100 items in one call, so the reconcile path died before it could refresh the board.

## Regression path

LRN-003 promotes a durable harness rule: any workflow or script that reconciles GitHub Projects v2 data must respect the GraphQL `first` limit and paginate. This eval checks that the rule remains present in `AGENTS.md`.

## Check

`AGENTS.md` must contain the literal string `GitHub GraphQL connections cap \`first\` at 100 records.`.

## Pass condition

`grep -qF 'GitHub GraphQL connections cap \`first\` at 100 records.' AGENTS.md` exits with code 0.

## Fail condition

The harness guardrail has been removed. Future workflow edits can again request oversized GraphQL pages and reintroduce deterministic reconcile failures on Projects v2 board syncs.
