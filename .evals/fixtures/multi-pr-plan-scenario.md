# Multi-PR Plan Scenario Fixture

**Source issue**: #62
**Plan**: `docs/plans/plan-003-reviewer-sibling-pr-awareness.md`
**Related evals**: EVAL-002, EVAL-003

## Scenario Description

A plan (plan-003) is split into three sibling PRs. The reviewer processes PR #65 (the active PR)
while PRs #60 and #61 are open siblings that each cover different criteria from the same plan.

| PR | Status | Covers |
|----|--------|--------|
| #60 | open | Step 1: Find the plan file |
| #61 | open | Step 2: Discover sibling PRs |
| #65 | active (under review) | Steps 3-6: Classification and review output |

## Case A: Sibling-covered criterion produces `Deferred: covered by #NN`

**Setup**

The reviewer processes PR #65. The plan file lists six success criteria. Two of them
("Step 1: Find the plan file" and "Step 2: Discover sibling PRs") are NOT in the diff
of PR #65 but ARE referenced in the titles and bodies of sibling PRs #60 and #61.

**Sibling discovery result**: `[#60 (open), #61 (open)]`

**Expected verdict for each criterion**

| Criterion | Expected classification |
|-----------|------------------------|
| Step 1: Find the plan file | `Deferred: covered by #60` |
| Step 2: Discover sibling PRs | `Deferred: covered by #61` |
| Steps 3-6 (in PR #65's diff) | `Met` |

**Expected review label**: `ai-reviewed` (not `needs-changes`, because deferred items alone
do not trigger `needs-changes`).

## Case B: No sibling covers criterion produces `Missed`

**Setup**

The reviewer processes PR #65. The plan file includes a criterion "Add integration test
for multi-PR scenario". No sibling PR (#60 or #61) mentions this criterion in its title,
body, or diff.

**Sibling discovery result**: `[#60 (open), #61 (open)]`

**Expected verdict for the uncovered criterion**

| Criterion | Expected classification |
|-----------|------------------------|
| Add integration test for multi-PR scenario | `Missed` |

**Expected review label**: `needs-changes` (a Missed criterion with no sibling coverage
is a genuine gap and must block merge).

## Assertions

The two cases above map directly to the rule text in `.github/workflows/reviewer.md`:

1. A criterion covered by a sibling PR must be classified as `Deferred: covered by #NN`,
   not `Missed`.
2. `Deferred` items alone must not trigger `needs-changes`.
3. A criterion covered by neither the active PR nor any sibling must be classified as `Missed`.
4. `Missed` items must trigger `needs-changes`.

These assertions are mechanically checked by EVAL-002 and EVAL-003 against the reviewer
workflow source.
