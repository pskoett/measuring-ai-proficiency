# Plan 207: Remove dead Partner-Agent routing surface

**Source issue**: #207
**Status**: Ready for implementation

## Problem Statement

The factory already knows a hard truth: only `impl:copilot` can be auto-routed today. GitHub's REST assignees path accepts Copilot but silently drops Partner Agents, so `impl:claude-opus`, `impl:claude-sonnet`, and `impl:codex` do not produce real routing behavior.

The repo still exposes those labels as part of the live surface. `spec-refiner` tells humans they can swap to them before merge. `implementer-dispatcher` still documents noop handling for them. `AGENT_FACTORY.md` and `FACTORY_STATE_MACHINE.md` still list them as live control-plane labels. This creates onboarding drag and makes the factory look more capable than it is.

Issue #207 presents two options: keep the labels and add a partial fallback, or delete the dead surface. The issue's own recommendation is Path A. That is the right call. A fallback that still ends in "human clicks the UI" preserves complexity without delivering true routing.

## Interview Synthesis

**Technical constraints**
- Treat the current routing reality as fixed for now: only `impl:copilot` is auto-assignable through workflow-safe primitives.
- Keep the existing plan-worthy and direct-route handoff paths working. This change is about removing misleading surfaces, not redesigning the chain.
- Update workflow source and compiled lock output together when workflow markdown changes.
- Keep operator docs and state-machine docs in sync so the label control plane matches the written guidance.

**Scope boundaries**
- Adopt Path A and remove the three dead Partner-Agent routing labels from the factory's active guidance.
- Update workflow prompts, shared harness docs, and operator docs that still treat those labels as meaningful routing signals.
- Review reviewer guidance only where it depends on the dead routing surface. If the current per-model review calibration is still useful because it keys off the actual PR author, keep it and reframe the surrounding docs instead of deleting it.
- Do not add speculative `assign-to-user` fallback logic or new label taxonomy in this change.

**Risk tolerance**
- Prefer clarity and deletion over future-proof scaffolding that does not work today.
- Accept a moderate documentation and workflow prompt cleanup if it removes a misleading public surface.
- Avoid changes that imply the factory can route Partner Agents "soon" unless there is a concrete runtime path to support it.

**Success signal**
- The plan chooses Path A explicitly.
- Active workflow prompts and operator docs describe `impl:copilot` as the only routing label the factory uses.
- `docs/AGENT_FACTORY.md` and `docs/FACTORY_STATE_MACHINE.md` say the same thing about routing after the change.
- The remaining reviewer guidance, if any, is justified by real PR authorship rather than dead issue-label routing.

## Decision

Adopt **Path A**.

Remove `impl:claude-opus`, `impl:claude-sonnet`, and `impl:codex` from the factory's live routing surface. Collapse the messaging to one rule: the factory auto-routes Copilot only. If a maintainer wants Claude or Codex on a task, that handoff happens outside the factory.

Keep reviewer calibration only if it still reflects actual implementation authors. Removing dead routing labels does not require deleting useful review heuristics for PRs that were manually authored or manually assigned outside the factory.

## Success Criteria

- The implementation records Path A as the chosen direction and removes repo guidance that presents the three Partner-Agent labels as part of the active routing contract.
- `.github/workflows/spec-refiner.md` no longer instructs humans to swap to `impl:claude-*` or `impl:codex`, and its compiled lock file matches.
- `.github/workflows/implementer-dispatcher.md` no longer carries dead routing branches for Partner-Agent labels, and its compiled lock file matches if the source changes.
- `docs/AGENT_FACTORY.md` and `docs/FACTORY_STATE_MACHINE.md` are aligned on a single routing story: the factory auto-routes Copilot only.
- Shared factory guidance such as `AGENTS.md`, `CLAUDE.md`, `docs/chain.md`, and `.claude/skills/use-agent-factory/SKILL.md` no longer tell operators to use the removed labels as manual overrides.
- The three dead labels are removed from repository metadata as part of the issue's completion path, or the implementation documents the exact repo-admin step required if that metadata change cannot live in the PR itself.
- Reviewer guidance is either simplified to a smaller supported set or intentionally preserved with an explicit rationale tied to actual PR authorship.

## Risk Assessment

**Blast radius**: Medium. The change touches workflow prompts, shared harness guidance, and operator documentation that describe how issues move through the factory.

**Rollback**: Moderate. Reverting text and workflow prompt changes is easy, but it would restore a misleading surface that operators already trip over.

**Key risks and mitigations**
- **Risk**: Some references to the dead labels survive in docs or workflow prompts and keep the repo inconsistent. **Mitigation**: do a repo-wide search for the three labels and update every live guidance path that still treats them as active routing signals.
- **Risk**: A workflow markdown change lands without a matching `.lock.yml` recompile. **Mitigation**: recompile every changed workflow source immediately and review the lock diff in the same PR.
- **Risk**: Reviewer guidance is simplified too aggressively and loses useful calibration that is independent of issue labels. **Mitigation**: check whether reviewer behavior keys off the PR author or the issue label, then keep only the author-grounded guidance.
- **Risk**: Repository labels remain in GitHub even after code and docs stop referencing them. **Mitigation**: treat label deletion as an explicit checklist item, not an implied side effect.

## Affected Files/Areas

- `.github/workflows/spec-refiner.md`
- `.github/workflows/spec-refiner.lock.yml`
- `.github/workflows/implementer-dispatcher.md`
- `.github/workflows/implementer-dispatcher.lock.yml`
- `docs/AGENT_FACTORY.md`
- `docs/FACTORY_STATE_MACHINE.md`
- `docs/chain.md`
- `AGENTS.md`
- `CLAUDE.md`
- `.claude/skills/use-agent-factory/SKILL.md`
- Repository label metadata for `impl:claude-opus`, `impl:claude-sonnet`, and `impl:codex`
- `.github/workflows/reviewer.md` and `.github/workflows/reviewer.lock.yml`, only if the current reviewer calibration is judged too tied to the removed routing surface

## Open Questions

None at plan time. The issue already frames the decision space and recommends the same direction this plan adopts.

## Implementation Checklist

- [ ] Search the repo for every live reference to `impl:claude-opus`, `impl:claude-sonnet`, and `impl:codex`, and separate routing guidance from historical explanation.
- [ ] Update `.github/workflows/spec-refiner.md` so the plan-worthy path recommends Copilot only and no longer presents Partner-Agent labels as manual-override routing signals.
- [ ] Recompile `.github/workflows/spec-refiner.lock.yml` after the workflow source change.
- [ ] Update `.github/workflows/implementer-dispatcher.md` so its routing model matches the new single-label contract, then recompile `.github/workflows/implementer-dispatcher.lock.yml` if the source changed.
- [ ] Rewrite `docs/AGENT_FACTORY.md` to remove the multi-label Implementer Routing table and replace it with a single clear statement that the factory auto-routes Copilot only, while preserving any necessary historical explanation of why.
- [ ] Update `docs/FACTORY_STATE_MACHINE.md` so the label table, trigger table, and happy-path narrative no longer describe the removed labels as part of the live control plane.
- [ ] Audit `AGENTS.md`, `CLAUDE.md`, `docs/chain.md`, and `.claude/skills/use-agent-factory/SKILL.md`, then collapse any remaining manual-override guidance to the simpler out-of-factory handoff wording.
- [ ] Decide whether `.github/workflows/reviewer.md` should keep its current per-model calibration. Preserve it if it is still grounded in actual PR authorship. Simplify it only if it is now misleading.
- [ ] Remove the three dead labels from repository metadata and verify the docs no longer reference them as available routing choices.
- [ ] Run the repo's existing verification commands for any changed workflow sources or docs, including workflow recompilation where required.

## Rejected Alternatives

**Path B, wire the dead labels with a fallback comment or future-facing assignment stub**: This preserves a public surface that still does not route automatically. It adds code and docs for a behavior that ends in the same manual UI action as today.

**Replace the three labels with a new generic manual-routing label**: This is simpler than the current state, but it still expands the label taxonomy for a handoff that is outside the factory's real control plane. The issue does not need a replacement label to succeed.

## Recommended implementer

**Choice**: copilot
**Rationale**: Auto-assignable via the existing factory path. The implementation is a bounded workflow-and-docs cleanup with a clear checklist and no unresolved design work left after this plan.
