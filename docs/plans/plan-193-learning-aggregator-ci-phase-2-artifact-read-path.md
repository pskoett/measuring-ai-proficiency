---
plan-id: plan-193
status: shipped
shipped-in: "#193"
---
# Plan 193: Fix learning-aggregator-ci Phase 2 artifact transcript reads

**Source issue**: #193
**Status**: Ready for implementation

## Problem Statement

`learning-aggregator-ci` is supposed to turn recent `agent` artifacts into weekly transcript-derived findings. The current Phase 2 path did not produce usable transcript analysis on the first manual dispatch. The issue report narrowed the failure to artifact consumption: metadata was visible, but the workflow could not prove that it had opened and parsed the artifact payload.

The most likely causes are narrow and mechanical, but the exact one still needs confirmation in code. Either `gh run download` leaves a ZIP that the workflow cannot extract with its current bash allowlist, or the command already extracts and the real bug is an incorrect path assumption plus weak debug visibility. The plan should let implementation prove which branch is real, fix the working path, and make future failures observable instead of silent.

## Interview Synthesis

The issue body provides enough detail to simulate the planning interview:

### Technical constraints

- Stay inside the current gh-aw workflow model. Use the existing `gh`-based transcript download path.
- Preserve the weekly transcript-analysis design rather than redesigning the outer loop.
- Keep the implementation compatible with current `agent` artifact contents and `gh run download` behavior.
- Recompile workflow markdown after edits so runtime and source stay in sync.

### Scope boundaries

- Fix Phase 2 artifact consumption end to end for `learning-aggregator-ci`.
- Update directly affected documentation for the now-working transcript path.
- Do not redesign the broader learning taxonomy, ranking model, or issue format beyond what is needed to distinguish "read but empty" from "could not read."
- Do not expand this issue into unrelated outer-loop rebuild work tracked by companion issues.

### Risk tolerance

- Prefer the smallest deterministic fix over a broad refactor.
- Accept a short-lived diagnostic step in the prompt if it makes the path observable and easy to maintain.
- Avoid speculative allowlist growth if the root cause is only a bad path assumption.

### Success signal

- A manual `learning-aggregator-ci` dispatch reports a nonzero `Transcript artifacts analyzed` count.
- If transcript-only patterns are present, they appear in `Transcript-Only Findings`.
- If no patterns are extracted after successful reads, the output explicitly reports `artifacts read: N, patterns extracted: 0`.
- `docs/AGENT_FACTORY.md` explains the working Phase 2 path in a way that matches the implementation.

## Decision Frame

Resolve the implementation through one early branch:

1. Reproduce the artifact download path against a recent run.
2. If `gh run download --name agent --dir <path>` leaves a ZIP, add the minimum extraction tool support and wire an explicit extraction step.
3. If it already extracts, keep the allowlist narrow and fix the prompt's canonical pathing, directory inspection, and success reporting.

The rest of the change should follow from that result.

## Success Criteria

- `learning-aggregator-ci` can successfully download and open at least one recent `agent` artifact during a manual dispatch in this repository.
- The workflow output issue reports a nonzero `Transcript artifacts analyzed` count when artifacts are actually parsed.
- The workflow output distinguishes `artifacts read: N, patterns extracted: 0` from a failure to read artifacts at all.
- The Phase 2 prompt includes a concrete success-path example that shows one run, one parsed transcript, and one extracted pattern candidate.
- `.github/workflows/learning-aggregator-ci.lock.yml` is regenerated from the updated markdown workflow source.
- `docs/AGENT_FACTORY.md` reflects the implemented Phase 2 transcript-analysis path. Update `docs/chain.md` too if its current wording would become inaccurate.

## Risk Assessment

**Blast radius**: Medium. The change is centered on one workflow, but it affects a core observability path in the outer loop and can quietly regress if the prompt and artifact contract drift apart.

**Rollback**: Simple. Reverting the workflow and docs changes restores current behavior, though it also restores the silent failure mode.

**Key risks and mitigations**

- **Wrong root cause**: the issue hypothesis may blame ZIP extraction when the real bug is path handling. **Mitigation**: make the first implementation step a concrete repro of `gh run download` behavior before editing the allowlist.
- **Prompt-only fix with poor observability**: the workflow might still fail opaquely on missing or moved files. **Mitigation**: add explicit directory inspection and output wording that distinguishes read failures from zero extracted patterns.
- **Workflow source and runtime drift**: markdown edits without recompiling leave the live workflow stale. **Mitigation**: treat lockfile recompilation as part of the same checklist.
- **Documentation drift**: operators may keep following the old transcript story. **Mitigation**: update the specific observability docs that describe weekly transcript analysis.

## Affected Files/Areas

- `.github/workflows/learning-aggregator-ci.md`
- `.github/workflows/learning-aggregator-ci.lock.yml`
- `.claude/skills/learning-aggregator/SKILL.md` if the canonical transcript path or success reporting belongs in the shared skill contract rather than only the workflow prompt
- `docs/AGENT_FACTORY.md`
- `docs/chain.md` if its transcript-analysis wording needs to match the implemented path

## Open Questions

- [ ] Does `gh run download --name agent --dir <path>` already extract the artifact payload in the gh-aw runtime used by this repo, or does it leave a ZIP that must be unpacked? Can proceed.
- [ ] Should the canonical transcript-read path and success-output wording live only in `.github/workflows/learning-aggregator-ci.md`, or should the same expectations be moved into `.claude/skills/learning-aggregator/SKILL.md` so other consumers stay aligned? Can proceed.
- [ ] Does `docs/chain.md` need a wording correction after the implementation, or is `docs/AGENT_FACTORY.md` the only operator-facing doc that currently overstates the working path? Can proceed.

## Implementation Checklist

- [ ] Reproduce the current Phase 2 behavior against a recent `agent` artifact and record whether `gh run download` extracts or leaves a ZIP.
- [ ] Update `.github/workflows/learning-aggregator-ci.md` so Phase 2 follows the proven artifact path instead of the assumed one.
- [ ] If the runtime leaves a ZIP, add the minimum extraction tool support to the workflow allowlist and wire the extraction step explicitly.
- [ ] If the runtime extracts directly, add a canonical file path pattern and an explicit `ls` or equivalent debug step so missing-path failures are visible.
- [ ] Tighten the output contract so successful empty parses are reported as `artifacts read: N, patterns extracted: 0`.
- [ ] Add a concrete success-path example to the Phase 2 prompt that shows one run, one transcript, and one extracted pattern.
- [ ] Recompile `.github/workflows/learning-aggregator-ci.lock.yml`.
- [ ] Update `docs/AGENT_FACTORY.md` to describe the real transcript-analysis path.
- [ ] Update `docs/chain.md` only if its current transcript wording becomes stale after the workflow change.
- [ ] Manually dispatch `learning-aggregator-ci` against the current repository state and confirm the output distinguishes read success from empty extraction.

## Decision Tree

```text
artifact download repro
|
+-- leaves zip bundle
|   |
|   +-- add extraction support
|   +-- extract agent payload
|   +-- parse transcript from extracted files
|
+-- extracts files directly
    |
    +-- fix prompt path assumptions
    +-- add directory visibility
    +-- parse transcript from extracted files
```

## Rejected Alternatives

**Broader outer-loop redesign in this issue**: Rejected. The issue asks for a concrete Phase 2 recovery, not a redesign of transcript promotion, ranking, or companion workflows.

**Blindly add `unzip` without a repro step**: Rejected. It may fix nothing if `gh run download` already extracts in this environment, and it would leave the real bug hidden.

## Recommended implementer

**Choice**: copilot
**Rationale**: Auto-assignable via `implementer-dispatcher`. For manual hand-off to Claude or Codex, a human can swap the label on the source issue before merging the plan PR.
