# Learnings

Corrections, insights, and knowledge gaps captured during development.

**Categories**: correction | insight | knowledge_gap | best_practice\
**Areas**: frontend | backend | infra | tests | docs | config\
**Statuses**: pending | in_progress | resolved | wont_fix | promoted

---

## [LRN-001] Factory workflow allowed-files lists are narrower than the file surfaces their prompts touch

**Status**: pending
**Priority**: high
**Area**: ci
**Pattern-Key**: factory-workflow-allowed-files-too-narrow
**Discovered**: 2026-04-18 via https://github.com/pskoett/measuring-ai-proficiency/issues/204

### What went wrong

`/pr-fix` generated a correct patch for CHANGELOG.md and a test file after the reviewer flagged both as required. Safe-outputs rejected the push because neither path appeared in `push-to-pull-request-branch.allowed-files`. The fix loop was blocked by its own restriction. Same class of failure previously hit `self-improvement-meta` (issue #186).

### Root cause

gh-aw workflow templates default to a narrow `allowed-files` whitelist. When a workflow is added from an upstream template (e.g. `githubnext/agentics`), the default list covers only the upstream author's expected paths. Repo-specific file surfaces (CHANGELOG.md, tests/, docs/, .learnings/, .evals/) are not in the upstream default.

### Prevention rule

After adding or modifying any factory workflow, audit its `safe-outputs.*.allowed-files` against every file path the workflow's prompt can legitimately write. The allowlist must cover the full reviewer-driven edit surface, not just code-change paths.

### Follow-up audit task

Walk every factory workflow's `safe-outputs.*.allowed-files` and verify it matches the paths the workflow's prompt actually touches. Affected workflows to audit:

- `.github/workflows/ci-cleaner.md`
- `.github/workflows/conflict-resolver.md`
- `.github/workflows/contribution-checker.md`
- `.github/workflows/eval-creator-ci.md`
- `.github/workflows/learning-aggregator-ci.md`
- `.github/workflows/reviewer.md`
- `.github/workflows/simplify-and-harden-ci.md`
- `.github/workflows/spec-refiner.md`

### See also

- Issue #186 (same class of bug on `self-improvement-meta`)
- Issue #203 (the auto-filed failure notice closed by issue #204)
- Issue #204 (fix for `pr-fix` allowed-files)
