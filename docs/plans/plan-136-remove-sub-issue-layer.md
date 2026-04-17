# Plan 136: Remove sub-issue layer, put plan checklist on the original issue

**Source issue**: #136
**Status**: Ready for implementation

## Problem Statement

The factory chain currently routes every `needs-spec` issue through a sub-issue layer: `spec-refiner` produces a plan PR, `/plan` reads the approved plan and creates N sub-issues, and `implementer-dispatcher` picks those sub-issues up and assigns Copilot. Two original justifications for that layer no longer apply:

1. **Parallelism** — after #135's discussion, `/plan` was on track to produce one consolidated sub-issue per plan anyway, because sibling PRs that touch the same file set always lose a merge-conflict race (see #62). The N→1 collapse left the sub-issue layer with no parallel fan-out to justify.
2. **Per-task implementer routing** — after #102 and #120, `impl:copilot` is the only wired label. The "different implementers per sub-issue" flow never materialized.

What remains is pure overhead: an extra GitHub issue per plan (parent + child, one-to-one), the entire `/plan` workflow, `implementer-dispatcher`'s parent-issue discovery logic (#115), reviewer's sibling-PR awareness (#62 / plan-003), label churn, and confusing UX for humans who have to track two issues for one unit of work.

Collapse the chain: the **original issue** becomes the unit of work end-to-end. When the plan PR merges, a small automation writes the plan's checklist into the original issue body and applies `ready-for-implementation`. `implementer-dispatcher` fires on the original issue's label and assigns Copilot directly. `/plan` goes away. Three failure modes disappear at once.

## Interview Synthesis

**Technical constraints**
- The automation that mutates the original issue body on plan-PR merge must be idempotent. Re-running on the same plan PR must not duplicate checklist content.
- Use a plain GitHub Actions or small gh-aw workflow triggered on `pull_request.closed` with `merged == true` and a path filter on `docs/plans/plan-*.md`. Prefer a non-agentic workflow for the body-mutation step because the transformation is deterministic.
- Preserve the existing `needs-plan` → `ready-for-implementation` label transition semantics so `implementer-dispatcher` needs no behavioral change beyond removing the parent-issue lookup.
- Leave `spec-refiner` responsible for producing the plan PR and linking it to the original issue. Only the post-merge step is new.

**Scope boundaries**
- Delete `/plan` (the `.github/workflows/plan.md` + `.lock.yml` pair).
- Delete the sub-issue creation path and its labels (`task`, `ai-generated`, `ready-for-implementation` on sub-issues) from any skill or doc that still describes them.
- Remove parent-issue discovery logic from `implementer-dispatcher` and simplify the triggering `if:` block.
- Remove sibling-PR awareness from `reviewer.md`/`reviewer.lock.yml` (the plan-003 / #62 compensating logic).
- Update operator docs: `docs/AGENT_FACTORY.md`, `docs/chain.md`, `AGENTS.md`, `.claude/skills/use-agent-factory/SKILL.md`, `.github/copilot-instructions.md`.
- Do **not** change how `spec-refiner` produces plan PRs or numbers them.
- Do **not** re-introduce multi-implementer routing. If we ever need it, it can be a label on the single issue.

**Risk tolerance**
- Prefer deletion over compatibility shims. Removing dead code is the whole point.
- Accept a short window during rollout where an already-approved plan PR still refers to sub-issues that will no longer be created; document the manual fallback (`gh issue edit <n> --add-label ready-for-implementation`) for that window.
- Keep the change reversible by one revert commit per surface (workflow deletions, dispatcher edit, reviewer edit, docs).

**Success signal**
- Opening a `needs-spec` issue produces exactly one plan PR and **no** intermediate task issue.
- Merging the plan PR mutates the original issue body (plan checklist inserted) and applies `ready-for-implementation`. Running the merge event twice does not duplicate the checklist.
- `implementer-dispatcher` triggers off the original issue's label and assigns Copilot with correct context and no parent-issue lookup.
- `grep -r "sub-issue\|parent issue\|/plan creates" docs/ .claude/ .github/` returns only historical/archive references.
- Reviewer workflow has no remaining sibling-PR code path.

## Success Criteria

- `/plan` is removed: `.github/workflows/plan.md` and `.github/workflows/plan.lock.yml` are deleted. No workflow or skill still invokes `/plan` as a slash command.
- A new post-merge automation (hereafter "plan-merged-dispatcher") writes the plan's implementation checklist into the source issue body, transitions labels `needs-plan` → `ready-for-implementation`, and is idempotent.
- `implementer-dispatcher`'s parent-issue lookup is removed. Its trigger is now the source issue's `ready-for-implementation` label.
- `reviewer.md`'s sibling-PR awareness logic is removed. The reviewer only reasons about the single PR in front of it.
- Docs updated and consistent: `docs/AGENT_FACTORY.md`, `docs/chain.md`, `AGENTS.md`, `.claude/skills/use-agent-factory/SKILL.md`, `.github/copilot-instructions.md`, `CLAUDE.md` factory-chain line.
- Lock-file-sync guard (#95 / #131) stays green across all touched workflows. Every `.md` edit has a paired recompiled `.lock.yml` commit.
- Full happy path exercised end-to-end on a throwaway `needs-spec` issue before merge: issue opened → plan PR produced → plan PR merged → issue body updated → Copilot assigned → PR opened and merged → issue closed.

## Risk Assessment

**Blast radius**: High. This touches every active issue that is currently mid-flight through the factory.

**Rollback**: One revert per deleted workflow and per edited workflow. Docs revert independently. No data migrations.

**Risk**: An issue that already has a plan PR open when this lands will expect the old `/plan` → sub-issue flow. Mitigation: merge only when no plan PRs are open, or manually apply `ready-for-implementation` to the source issue for any in-flight cases. Document this explicitly in the rollout note. A secondary risk is that the post-merge body mutation races with concurrent label automation; mitigate by making the mutation idempotent and guarding with a `merged == true && head ref matches plan branch pattern` check.

## Affected Files/Areas

- `.github/workflows/plan.md`, `.github/workflows/plan.lock.yml` — delete.
- `.github/workflows/plan-merged-dispatcher.yml` (or similarly named) — new, non-agentic, runs on `pull_request.closed` with `merged == true` and path filter `docs/plans/plan-*.md`.
- `.github/workflows/implementer-dispatcher.md` and `.lock.yml` — strip parent-issue lookup; trigger off source-issue label.
- `.github/workflows/reviewer.md` and `.lock.yml` — remove sibling-PR awareness.
- `.github/workflows/spec-refiner.md` and `.lock.yml` — only touch if it currently adds `needs-plan` or references `/plan`; otherwise leave alone.
- `docs/AGENT_FACTORY.md`, `docs/chain.md`, `AGENTS.md` — update chain diagram and step list.
- `.claude/skills/use-agent-factory/SKILL.md` — rewrite the "how sub-issues flow" section.
- `.github/copilot-instructions.md`, `CLAUDE.md` — update the factory-chain sentence and workflow count.
- Any label definitions (`.github/labels.yml` or equivalent, if present) that exist only to serve the sub-issue flow.

## Open Questions

- [ ] Should `plan-merged-dispatcher` live as a plain GitHub Actions `.yml` (recommended — deterministic string manipulation) or as a gh-aw agentic workflow (overkill, but consistent with the rest of the factory)? - Can proceed with plain Actions as the default; escalate only if the checklist extraction turns out to need LLM reasoning.
- [ ] What is the canonical marker used to locate the plan's Implementation Checklist inside the plan file so the post-merge step can extract it deterministically? - `## Implementation Checklist` is present in every current plan file; use that as the anchor.
- [ ] Should the original issue body be fully replaced or appended to? - Append with a clearly delimited `<!-- plan-checklist: plan-NNN -->` block so human-authored issue context is preserved and re-runs can replace the block idempotently.

## Implementation Checklist

- [ ] Inventory every reference to the sub-issue flow so nothing is missed: grep `sub-issue`, `parent issue`, `/plan `, `ready-for-implementation` (applied to tasks vs. parents), `assigned-to-agent` across `.github/`, `docs/`, `.claude/`, `AGENTS.md`, `CLAUDE.md`.
- [ ] Design the post-merge body-mutation step: exact event trigger, path filter on `docs/plans/plan-*.md`, idempotency marker format, and the mapping from plan file → source issue number (the filename prefix is the issue number).
- [ ] Add `.github/workflows/plan-merged-dispatcher.yml`: on `pull_request.closed` with `merged == true` and path filter, read the merged plan file, extract its `## Implementation Checklist` section, and edit the source issue body to contain a single `<!-- plan-checklist: plan-NNN -->` block. Transition labels `needs-plan` → `ready-for-implementation` on the source issue in the same step.
- [ ] Prove idempotency: running the workflow twice on the same merged PR results in identical issue body and label state.
- [ ] Remove `.github/workflows/plan.md` and `.github/workflows/plan.lock.yml`. Run `gh aw compile` to confirm no other workflow imports or depends on them.
- [ ] Strip parent-issue discovery from `.github/workflows/implementer-dispatcher.md`. Trigger should be the source issue's `ready-for-implementation` label. Recompile the lock file.
- [ ] Remove sibling-PR awareness from `.github/workflows/reviewer.md`. Recompile the lock file.
- [ ] Update `docs/AGENT_FACTORY.md`, `docs/chain.md`, `AGENTS.md` with the new chain: issue → spec-refiner → plan PR → **plan-merged-dispatcher** → ready-for-implementation on issue → implementer-dispatcher → Copilot → PR → reviewer → merge.
- [ ] Update `.claude/skills/use-agent-factory/SKILL.md` to remove all sub-issue language and describe the new lifecycle. Include the manual fallback for any in-flight issue that predates this change.
- [ ] Update `.github/copilot-instructions.md` and `CLAUDE.md` factory-chain description. Adjust the `14-workflow` count if the net workflow count changes (plan deleted, plan-merged-dispatcher added = still roughly 14; confirm after changes).
- [ ] Walk through a throwaway `needs-spec` issue end-to-end on a staging branch and confirm every success-criterion check passes. Specifically verify the lock-file-sync guard stays green after the workflow edits.
- [ ] Add a short "migration note" paragraph to `docs/AGENT_FACTORY.md` describing the in-flight-issue fallback (`gh issue edit <n> --add-label ready-for-implementation`) so operators have guidance for the rollout window.

## Rejected Alternatives

**Keep the sub-issue layer but fix its failure modes individually**: Rejected. That is what #62, #115, #135, and the earlier stopgaps have been doing. The cost keeps compounding because the layer has no earned purpose anymore.

**Collapse to a single sub-issue permanently (the #135 approach)**: Rejected as the final state. It still pays the cost of an extra issue and the entire dispatcher-parent-lookup layer for no remaining benefit. #135 was useful as a tactical fix but is redundant with this refactor.

**Move the plan checklist into a PR description instead of the issue body**: Rejected. The issue is the durable identifier humans use to ask "what is the state of this work". Putting the checklist on the PR ties it to a transient artifact.

**Implement the post-merge mutation as another gh-aw agentic workflow**: Rejected. The transformation is deterministic string manipulation on a file with a known structure. An LLM in the loop adds cost, latency, and a new class of drift for no benefit.

**Keep `/plan` but stub it to exit immediately when invoked**: Rejected. That leaves a half-live workflow in the chain, which is exactly the "confusing dead code" pattern we are trying to remove.

## Recommended implementer

**Choice**: copilot
**Rationale**: Auto-assignable via `implementer-dispatcher`. The change spans multiple workflow files and docs but each edit is mechanical; no novel design decisions remain after this plan. Escalate to Claude Opus if the post-merge body-mutation step needs more careful reasoning than a plain Actions step can handle, but the expected path is Copilot.
