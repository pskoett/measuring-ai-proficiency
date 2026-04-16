# Plan 097: Capture cloud-agent session transcripts for the learning loop

**Source issue**: #97
**Status**: Ready for implementation

## Problem Statement

The factory currently observes workflow-level outcomes, but it does not retain the session-level traces that explain how an agent got there. When a run misclassifies a PR, loops through repeated fixes, or makes an inconsistent workflow decision, the team can inspect labels, comments, and `gh aw audit` output, but not the full sequence of prompts, tool calls, and intermediate outputs that led to the result.

The requested MVP should capture those sessions after each factory workflow run, store the raw data in GitHub Actions artifacts, and make the transcripts available to the learning loop. The first cut should follow the issue's preferred Option C, not depend on an upstream gh-aw transcript API, and avoid committing raw transcript dumps into git history.

## Interview Synthesis

The issue body provides enough detail to simulate the planning interview:

- **Technical constraints**: Use GitHub-native artifact upload and download for the MVP. Keep the implementation inside the current gh-aw workflow model. Document privacy, retention, and access controls because transcripts can contain issue-body or commit-message PII.
- **Scope boundaries**: No real-time transcript streaming. No browsing UI. No retrofit for past runs. Prefer an artifact-backed path over a dedicated transcript branch.
- **Risk tolerance**: Choose the conservative path first. Reuse GitHub primitives and keep raw transcript storage out of the repository history. Accept an implementation that standardizes around the current gh-aw output shape even if an upstream native API arrives later.
- **Success signal**: Factory workflows publish transcript artifacts, the learning loop can consume them, and the factory docs explain where transcripts live and how to reason about retention.

## Success Criteria

- Every factory workflow that runs an agent uploads a session-transcript artifact after the agent step completes, or exits through an explicit guarded noop path when no transcript payload exists.
- The artifact naming scheme is deterministic and traceable to workflow name, run ID, and the source issue or PR when available.
- `learning-aggregator-ci` can download recent transcript artifacts and extract reusable patterns from them instead of relying only on manually written `.learnings/` entries.
- The workflow or skill path that turns transcript-derived patterns into durable learnings is updated so `.learnings/LEARNINGS.md` can receive those patterns through the repo's existing review flow, rather than leaving them trapped in a weekly report.
- `docs/AGENT_FACTORY.md` gains an `Observability` section that explains where transcripts are stored, who can read them, how long they live, and how they feed the outer loop.
- `docs/chain.md` documents `.entire/` as part of the observability and learning architecture, and explains the relationship between `.entire/metadata/`, temporary transcript handling, and GitHub Actions artifacts.
- All workflow markdown changes are recompiled so the matching `.lock.yml` files stay in sync.

## Risk Assessment

**Blast radius**: High. This changes cross-cutting behavior across many workflows, introduces a new observability data path, and affects how the outer learning loop reasons about failures.

**Rollback**: Moderate. Reverting the workflow and docs changes is straightforward, but it leaves any interim artifact conventions and transcript-analysis assumptions stale until the learning-loop consumers are reverted too.

**Primary risks and mitigations**

- The gh-aw runtime may not expose a stable transcript payload in the same place for every workflow. Mitigation: inspect the actual post-agent filesystem layout first, define one supported selector or manifest shape, and roll that out consistently.
- Adding upload steps to every workflow can create noisy failures on noop, cancelled, or partial runs. Mitigation: gate artifact upload on the presence of expected transcript files and keep the no-payload path explicit.
- Raw transcripts can include sensitive human-authored content. Mitigation: document access and retention up front, use GitHub artifact retention instead of git history for raw dumps, and avoid broadening access beyond existing repo readers.
- The weekly learning flow currently creates issues, not reviewed file changes. Mitigation: design the transcript-to-learning handoff deliberately, either by extending `learning-aggregator-ci` to produce reviewable repo changes or by routing transcript findings into the existing self-improvement PR path without losing the weekly aggregation step.
- Parsing transcript data can become brittle if the payload shape changes upstream. Mitigation: keep the MVP parser narrow, fail with explicit diagnostics, and treat a future gh-aw native transcript API as a migration target rather than a dependency today.

## Affected Files/Areas

- `.github/workflows/spec-refiner.md`
- `.github/workflows/reviewer.md`
- `.github/workflows/implementer-dispatcher.md`
- `.github/workflows/self-improvement-meta.md`
- `.github/workflows/ci-cleaner.md`
- `.github/workflows/contribution-checker.md`
- `.github/workflows/issue-triage.md`
- `.github/workflows/plan.md`
- `.github/workflows/pr-fix.md`
- `.github/workflows/simplify-and-harden-ci.md`
- `.github/workflows/learning-aggregator-ci.md`
- `.github/workflows/eval-creator-ci.md`
- `.github/workflows/ai-proficiency-pr-review.md`
- `.github/workflows/ai-proficiency-weekly-report.md`
- Matching `.github/workflows/*.lock.yml` files after `gh aw compile`
- `.claude/skills/learning-aggregator/SKILL.md`, plus synced skill copies if transcript ingestion becomes part of the skill contract rather than only the workflow shell
- `docs/AGENT_FACTORY.md`
- `docs/chain.md`
- `.entire/` conventions, if the MVP adds tracked documentation or schema notes for metadata layout

## Open Questions

- [ ] Should the first cut attach transcript artifacts to all fourteen workflow definitions, or only to the workflows that can be shown to emit agent-session files today? Default to every workflow that actually runs an agent step, and leave pure pass-through workflows out only if inspection proves they have no transcript payload. Can proceed.
- [ ] Should `.entire/metadata/` store raw transcripts in git, or should it document metadata layout while raw sessions live only in Actions artifacts? Default to artifact-only storage for raw transcripts so git history does not become a transcript archive. Can proceed.
- [ ] Should transcript-derived learnings land through `learning-aggregator-ci` directly, or should that workflow hand structured findings to `self-improvement-meta` for PR creation? Default to the path that preserves a reviewed write path into `.learnings/LEARNINGS.md` with the least workflow churn. Can proceed.

## Implementation Checklist

- [ ] Inspect one recent gh-aw workflow run locally in this repo and identify the actual transcript or session-output files that exist after the agent step, including how they differ across success, noop, and failure cases.
- [ ] Define the MVP transcript artifact contract: file selector, artifact name, retention behavior, and minimum metadata needed to map a transcript back to workflow, run, and issue or PR context.
- [ ] Update each agent-backed workflow markdown file to upload the transcript artifact after the agent step, with guards for missing payloads so the workflow does not fail solely because no transcript files were produced.
- [ ] Recompile the edited workflow markdown files so the corresponding `.lock.yml` artifacts remain current.
- [ ] Extend `learning-aggregator-ci` so it can discover and download recent transcript artifacts during its weekly run.
- [ ] Decide whether transcript ingestion logic belongs in `.github/workflows/learning-aggregator-ci.md`, `.claude/skills/learning-aggregator/SKILL.md`, or both, then make the smallest coherent change and sync any skill edits to every required copy.
- [ ] Implement transcript parsing that extracts repeatable failure or behavior patterns without copying raw transcript bodies into issues or learnings.
- [ ] Update the learning-loop write path so transcript-derived patterns can become reviewed additions to `.learnings/LEARNINGS.md` instead of staying trapped in transient reports.
- [ ] Keep `self-improvement-meta` consistent with the new transcript source, either by consuming the same artifact convention or by documenting why it still relies on logs in the MVP.
- [ ] Add `docs/AGENT_FACTORY.md#observability` with storage location, retention, access model, and operator guidance for inspecting transcript artifacts.
- [ ] Update `docs/chain.md` so the outer-loop diagram and narrative include transcript capture and the role of `.entire/` in the learning architecture.
- [ ] Search the repo for transcript, artifact, and learning-loop guidance that would become stale after this change, and update only the directly affected references.

## Rejected Alternatives

**Option A, gh-aw native transcript API in the MVP**: Rejected for now. It is the cleanest long-term path, but the issue explicitly prefers an artifact-backed first cut that does not wait on upstream support.

**Option B, commit raw transcript dumps to a dedicated branch or `.entire/` tree**: Rejected for the MVP. It creates privacy, review-noise, and repository-growth problems that GitHub Actions artifacts already avoid.

**Keep transcript analysis out of durable learnings**: Rejected. The point of the feature is to strengthen the outer loop, not just produce another transient report.

## Recommended implementer

**Choice**: claude-opus-4.6
**Rationale**: This is a high-blast-radius workflow refactor across nearly every factory workflow, the learning-loop contract, and multiple docs surfaces. The checklist is long, the write path for transcript-derived learnings is non-trivial, and spec drift would be costly.
