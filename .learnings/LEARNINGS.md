# Learnings

Corrections, insights, and knowledge gaps captured during development.

**Categories**: correction | insight | knowledge_gap | best_practice\
**Areas**: frontend | backend | infra | tests | docs | config\
**Statuses**: pending | in_progress | resolved | wont_fix | promoted

---

## [LRN-003] GitHub GraphQL project queries cannot request more than 100 items per page

**Status**: pending
**Priority**: high
**Area**: ci
**Pattern-Key**: github-graphql-first-limit-100
**Discovered**: 2026-05-23 via https://github.com/pskoett/measuring-ai-proficiency/actions/runs/26272480150

### What went wrong

The scheduled `sync-factory-state.yml` reconcile failed on 2026-05-22 because its project query asked GitHub GraphQL for `items(first: 250)`. GitHub rejected the request before any reconciliation work happened, so the board safety-net run exited immediately instead of correcting stale state.

### Root cause

GitHub GraphQL connections cap `first` at 100 records. The workflow comment described the GraphQL-by-project-ID approach as the only reliable full-reconcile shape, but the query itself exceeded the API limit and had no pagination path.

### Prevention rule

Never request more than 100 items from a GitHub GraphQL connection in one call. When a workflow may need more than 100 records, use `first: 100` and paginate with `pageInfo` and `endCursor`.

### See also

- Issue #278
- Issue #282

---

## [LRN-002] `sync-factory-state` misses `pull_request` webhooks on certain producer paths

**Status**: pending
**Priority**: high
**Area**: ci
**Pattern-Key**: sync-factory-state-webhook-missed
**Discovered**: 2026-04-18 via https://github.com/pskoett/measuring-ai-proficiency/issues/240

### What went wrong

On 2026-04-18, at least three distinct `pull_request` events failed to trigger `sync-factory-state.yml` even though the workflow's `on: pull_request: types: [...]` block lists them explicitly:

1. PR #225 close (17:17 UTC) via `gh pr close` (user PAT): no sync run fired; board showed the PR in 👉 Your turn for ~10 minutes.
2. PR #225 `needs-rebase` label addition (17:03 UTC) via `gh api --method POST`: conflict-resolver never ran because the `pull_request.labeled` event was not delivered.
3. PRs #238, #239 opened as Copilot draft PRs (~17:38 UTC): neither triggered a `pull_request.opened` run; board showed both in 📥 Waiting for spec until a manual dispatch.

The scheduled 10-minute reconcile eventually corrected all three, but the lag was long enough to erode operator trust and to completely block the `needs-rebase` → conflict-resolver automation path.

### Root cause

GitHub webhook delivery is not guaranteed for `pull_request` events produced via `gh` CLI, `gh api`, or Copilot-created PRs (which use `GITHUB_TOKEN`). Events created by `GITHUB_TOKEN` do not re-trigger workflows (GitHub anti-loop protection). PRs mutated through the GitHub web UI appear to deliver reliably. The exact failure envelope has not been fully characterized, but the pattern is consistent: API/CLI producer paths miss webhooks more often than web UI paths.

### Prevention rule

Never rely on `pull_request` webhook triggers as the sole delivery path for `sync-factory-state`. The scheduled reconcile cron is the primary correctness mechanism for these paths. Keep the cron at 5 minutes or shorter.

### See also

- Issue #240 (the tracking issue for this fix)
- PR #225 close, PRs #238/#239 open (the three observed instances)

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
