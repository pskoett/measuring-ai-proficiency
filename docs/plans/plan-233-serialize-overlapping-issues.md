---
plan-id: plan-233
status: active
target-files:
  - docs/plans/README.md
  - .github/workflows/spec-refiner.md
  - .github/workflows/spec-refiner.lock.yml
  - .github/workflows/serialization-resolver.yml
  - .github/workflows/sync-factory-state.yml
  - docs/AGENT_FACTORY.md
  - docs/CONTRIBUTING.md
---
# Plan 233: Serialize overlapping issues

**Source issue**: #233
**Status**: Ready for implementation

## Problem Statement

The factory currently dispatches multiple issues in parallel with no awareness of overlapping file surfaces. That works for isolated changes, but it breaks down on shared harness files such as `AGENTS.md`, `CLAUDE.md`, workflow prompts, and core factory docs. When two in-flight items touch the same structural surface, the later PR either dies in conflict resolution or accumulates conflicts until a human has to choose between competing designs under merge pressure.

Issue #233 asks for a prevention step earlier in the chain. The goal is to block dispatch before the second issue starts implementation when its declared target surface overlaps with files already touched by an open factory PR.

## Interview Synthesis

The issue body provides enough detail to simulate the planning interview.

### Technical constraints

- Keep the current factory flow intact: `spec-refiner` creates the plan artifact, `plan-merged-dispatcher` activates the source issue, and `implementer-dispatcher` assigns Copilot after the issue is ready.
- Standardize the plan file surface in a machine-readable way. The issue allows either frontmatter `target-files` or a stable markdown section. Use a format that is easy for both workflow code and agents to read.
- Reuse GitHub-native file-surface signals for in-flight work. The issue explicitly points at `gh pr diff --name-only` for open PRs labeled `plan-file` or `impl:copilot`.
- Treat only the shared harness paths as serialization signals. Exclude low-conflict areas such as `docs/plans/*`, `.evals/`, `.learnings/`, and tests to avoid false blocking.

### Scope boundaries

- Cover the plan-file format contract, the overlap check in `spec-refiner`, the blocked-state label, board-state routing, and merge-time re-evaluation of queued issues.
- Keep the first version focused on the shared-harness allowlist called out in the issue. Do not generalize into a whole-repo locking system.
- Do not redesign conflict resolution or try to auto-merge structurally conflicting prose changes.
- Do not expand the feature into unrelated throughput controls beyond serialization for overlapping harness surfaces.

### Risk tolerance

- Prefer deterministic queueing over optimistic parallelism on the shared harness surface.
- Accept a small amount of extra workflow logic if it prevents dead PRs and repeated manual cleanup.
- Avoid brittle heuristics that guess intent from issue text alone. The dispatch check should use an explicit target surface plus concrete open-PR file lists.

### Success signal

- Plan files expose a stable `target-files` surface that automation can read directly.
- `spec-refiner` blocks a plan-worthy issue from reaching implementation when its `target-files` overlap with in-flight PR surfaces on the protected harness allowlist.
- Blocked issues carry a distinct `blocked-on-serialization` signal and a comment that names the blocking PRs and overlapping files.
- A follow-up workflow re-checks queued issues when blocking PRs merge and frees them automatically when the overlap disappears.
- Factory docs and board-state docs explain the new queueing behavior so humans understand why an issue is waiting.

## Decision

Adopt **frontmatter `target-files`** as the machine-readable plan surface, and add a dedicated **`serialization-resolver.yml`** workflow for unblocking queued issues.

This keeps the contract simple:

1. `spec-refiner` writes `target-files` into every new plan file.
2. `spec-refiner` compares the new plan's `target-files` against the current file surfaces of open factory PRs, bounded to the protected harness allowlist.
3. If any overlap exists, the source issue is queued with `blocked-on-serialization` instead of being released for implementation.
4. `serialization-resolver.yml` re-evaluates queued issues when a blocking PR merges or when a relevant issue state changes.

Choosing a dedicated resolver workflow is cleaner than overloading `plan-merged-dispatcher`. The merge that frees a blocked issue may be either a plan PR or an implementation PR, so the re-check should live in a workflow that watches the broader in-flight set, not only merged plan files.

## Success Criteria

- `docs/plans/README.md` documents `target-files` as a stable machine-readable contract for implementation surface declarations.
- `spec-refiner` emits plan files with `target-files` in frontmatter and uses that data during its pre-dispatch overlap check.
- The overlap check considers only the protected shared-harness allowlist from the issue: `AGENTS.md`, `CLAUDE.md`, `docs/AGENT_FACTORY.md`, `docs/FACTORY_STATE_MACHINE.md`, `docs/chain.md`, `.github/workflows/*.md`, `.github/workflows/*.yml`, and `.claude/skills/**/SKILL.md`.
- `spec-refiner.md` documents the overlap check and references a concrete helper shape for collecting `in-flight-target-files(PR_N)` from open PRs.
- A distinct `blocked-on-serialization` label is created or ensured automatically with a color that is visibly different from `blocked-on-human`.
- `sync-factory-state.yml` routes `blocked-on-serialization` into the `👉 Your turn` lane with semantics that distinguish "human clarification needed" from "queued behind overlapping work."
- A new `serialization-resolver.yml` workflow, or an equivalently broad resolver, re-evaluates every `blocked-on-serialization` issue when the blocking PR set changes and re-adds `ready-for-implementation` only when no protected overlap remains.
- `docs/AGENT_FACTORY.md` explains the serialization policy, what comment humans will see, and how a blocked issue becomes free again.
- At least one manual test covers two issues that both target `AGENTS.md`, verifying that the later issue is queued with `blocked-on-serialization` while the first PR is open and is released after the blocking PR merges.

## Risk Assessment

**Blast radius**: High. The change alters factory dispatch semantics, adds a new blocked state, and introduces a new reactivation path for queued issues.

**Rollback**: Moderate. Docs and workflow changes are easy to revert, but a partial rollback could strand issues in the wrong queue state if the new label or resolver remains half-enabled.

**Key risks and mitigations**

- **Risk**: `target-files` drift from real implementation surfaces, producing false negatives or false positives. **Mitigation**: document the contract in `docs/plans/README.md`, keep the protected allowlist narrow, and compare declared targets only against concrete changed files from open PRs.
- **Risk**: a queued issue never gets freed because the resolver watches too narrow an event set. **Mitigation**: use a dedicated resolver workflow with triggers tied to PR merge and issue label/state changes, plus an idempotent full re-check of currently blocked issues.
- **Risk**: the new blocked state confuses board users because it shares a lane with other human-action states. **Mitigation**: update `sync-factory-state.yml` comments and factory docs so the queueing reason is explicit in both labels and issue comments.
- **Risk**: label creation fails on a fresh repo or after accidental deletion. **Mitigation**: ensure the label in workflow code before first use rather than assuming it already exists.
- **Risk**: the overlap check blocks on noisy paths outside the shared harness surface. **Mitigation**: normalize both plan targets and PR diff paths through the issue's explicit allowlist and keep excluded areas out of the matching logic.

## Affected Files/Areas

- `docs/plans/README.md`: document `target-files` as part of the plan-file contract and explain how agents should interpret it.
- `.github/workflows/spec-refiner.md`: add the overlap-check logic and the plan-writing requirement for `target-files`.
- `.github/workflows/spec-refiner.lock.yml`: recompile the workflow after the prompt change.
- `.github/workflows/serialization-resolver.yml`: add the queued-issue re-evaluation workflow.
- `.github/workflows/sync-factory-state.yml`: route `blocked-on-serialization` to the correct board lane and explain the new state.
- `docs/AGENT_FACTORY.md`: document the serialization policy and human-visible behavior.
- `docs/CONTRIBUTING.md`: update the contributor-facing label and workflow summary if it would otherwise become stale.
- Shared harness-path matching logic across the factory workflows and helper shell snippets, as needed.

## Open Questions

- [ ] Should `target-files` allow glob patterns directly in plan frontmatter, or should plans declare only normalized concrete paths and let workflow code own all wildcard expansion? Can proceed.
- [ ] Should `serialization-resolver.yml` wake on every merge and label change, or should it also run on a short schedule as a safety net against missed events? Can proceed.
- [ ] Where should the "ensure label exists" step live so it is deterministic but not duplicated unnecessarily: inside `spec-refiner`, inside `serialization-resolver`, or in both workflows with an idempotent helper? Can proceed.

## Implementation Checklist

- [ ] Extend the plan-file convention in `docs/plans/README.md` to define `target-files` and when it must be populated.
- [ ] Update `.github/workflows/spec-refiner.md` so plan-worthy plans include `target-files` and the workflow performs a pre-dispatch overlap check against open factory PRs.
- [ ] Keep the overlap check bounded to the shared-harness allowlist from issue #233 and explicitly exclude low-conflict areas such as `docs/plans/*`, `.evals/`, `.learnings/`, and tests.
- [ ] Add or ensure a `blocked-on-serialization` label with a distinct color before applying it to queued issues.
- [ ] Add the issue comment template that names blocking PR numbers and the exact overlapping files when serialization blocks dispatch.
- [ ] Update `.github/workflows/sync-factory-state.yml` so `blocked-on-serialization` maps to the `👉 Your turn` lane with clear queue semantics.
- [ ] Add `.github/workflows/serialization-resolver.yml` to re-check all `blocked-on-serialization` issues whenever the in-flight PR set changes and to restore `ready-for-implementation` only when no overlap remains.
- [ ] Update `docs/AGENT_FACTORY.md` and any directly related contributor docs so operators know why an issue may queue behind another open PR.
- [ ] Recompile `.github/workflows/spec-refiner.lock.yml` after the workflow-source change.
- [ ] Run the repo's existing verification command set after the workflow and documentation changes land.
- [ ] Perform the manual two-issue `AGENTS.md` overlap test described in the issue and capture the observed queue and release behavior in the implementation PR summary.

## Rejected Alternatives

**Rely on force-rebase or merge-queue enforcement alone**: Rejected. Those mechanisms help with textual freshness, but they do not prevent two agents from making incompatible structural edits to the same shared harness files.

**Serialize the entire factory globally**: Rejected. The issue is about a narrow shared surface. Global serialization would throw away the throughput gain from independent parallel work.

**Infer target files only from issue text**: Rejected. The overlap check needs a contract stronger than natural-language guesses. A machine-readable plan surface is the safer source of truth.

## Recommended implementer

**Choice**: copilot
**Rationale**: Auto-assignable via `implementer-dispatcher`. The work spans workflow prompts, a new resolver workflow, board-state routing, and factory docs, so the plan should drive a structured implementation handoff even though the factory still routes to Copilot only.
