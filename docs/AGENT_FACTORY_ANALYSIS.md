# Agent Factory Analysis

Living document. Revisit after major workflow changes. Sections are dated; the most recent snapshot is authoritative.

---

## Snapshot: 2026-04-17 (evening, post-#159)

A full day of factory work landed. All weak points from the morning snapshot either shipped, got a deliberate decision, or remain open with a clear owner. Below is the current state, not the diff.

### What shipped today

| PR | Change | Closes weak point |
|---|---|---|
| #138 | Removed sub-issue layer; source issue is the unit of work | Class of sibling-PR merge conflicts gone |
| #143, #156 | Plan-merged-dispatcher uses a PAT (`GH_AW_AGENT_TOKEN`), cascade fires | — |
| #144 | Stale factory refs in `AGENTS.md`, `CLAUDE.md`, `use-agent-factory` skill fixed | — |
| #145 | `bots:` frontmatter added to reviewer, contribution-checker, simplify-and-harden, eval-creator | Review workflows now actually run on Copilot PRs |
| #146 | Factory workflow session transcripts captured in artifacts | Morning #5 (observability gap) |
| #147, #158 | Multi-implementer routing collapsed to Copilot-only; partner agents UI-only | Morning #3 (half-built dead code) — took option (a), simplified |
| #157 | Reviewer auto-labels `BEHIND` PRs with `needs-rebase`; conflict-resolver then fires | Morning #6 (conflict-resolver integration) |
| #159 | `protected_path_prefixes` loosened on `/pr-fix` and conflict-resolver; reviewer gained a self-tamper guard | Chicken-and-egg class: factory can now edit its own workflows via /pr-fix |

### What's working (keep)

**Choreography over orchestration.** Unchanged from morning. Each workflow owns one job and hands off via a label swap. Freeze time on any issue or PR and the state is readable off GitHub.

**Three human gates, well placed.** Plan approval, PR merge, learnings approval. The ratio is still right.

**Source issue as unit of work.** The #138 decision has proven itself through six PRs today. No sibling-PR conflicts reappeared. Checklist-on-body with the delimited idempotent block is doing its job.

**Plan file as durable artifact.** Today's plan files (140, 149, 152) survived merges and are sitting in `docs/plans/` as ground truth for future reviews and for the learning loop.

**Lock-file-sync guard (#131).** Caught zero new drift today because #138 reconciled the pre-existing six. Guard is now doing its actual job: preventing new drift, not catching backlog.

**Quality gates now live on Copilot PRs.** Before #145, reviewer/contribution-checker/simplify-and-harden/eval-creator silently skipped every Copilot PR via the team-membership gate. After #145, they all run. The proof is in #157 and #159, both of which went through the full gate chain.

**Transcripts captured.** Every workflow run now drops its full session (prompt, tool calls, tool outputs, token usage) into the `agent` artifact. `learning-aggregator-ci` consumes them weekly. Outer loop is no longer running on 20% signal.

**Full end-to-end chain proven.** #152 → #154 (plan PR, merged) → plan-merged-dispatcher → `ready-for-implementation` → implementer-dispatcher → #159 (impl PR, merged). First clean-room proof of the post-#138 chain firing without human nudges between stages.

### Remaining weak points

1. **Label semantics still undiagrammed.** The state machine lives in ~12 labels across `AGENT_FACTORY.md`, `AGENTS.md`, and skill files. No single-page `label → label` transition diagram + trigger table. Same as morning. One-day job, still open.

2. **Hand-patched lock file risk is latent, not active.** The CI guard (#131) blocks new drift. The risk now is subtler: someone edits a `.lock.yml` in an emergency (e.g. today's rebase conflict resolution) and forgets to regenerate from the `.md`. Only mitigation is discipline + the CI guard catching it on the next PR. Acceptable for now.

3. **~~Multi-implementer routing~~ resolved (collapsed).** Dropped option (b), took option (a). Partner Agents (`impl:claude-*`, `impl:codex`) are documented as UI-manual-only because the REST API silently drops them. If GitHub fixes the API, revert #147/#158 and wire them. Until then, surface area matches behavior.

4. **No operator dashboard.** Unchanged. You still can't answer "which issues are stuck at `ready-for-implementation`?" or "which PRs have been `needs-changes` >24h?" without `gh` queries. Top priority going forward — see recommendations.

5. **~~Observability gap (#97)~~ shipped (#146).** Transcripts now flow to `learning-aggregator-ci`. Real test is the next weekly run — does the outer loop surface patterns it couldn't before? Track.

6. **`ci-cleaner` and `conflict-resolver` still treated as side branches in docs.** #157 promoted `conflict-resolver` to a first-class participant (reviewer labels → conflict-resolver fires), but the chain diagram and the `AGENT_FACTORY.md` narrative haven't caught up. Partial progress since morning; fold them into the main diagram.

7. **`needs-plan` label semantic weakness.** Same as morning. Post-#138, `needs-plan` means "spec done, plan PR open, waiting for human to merge." It's communicative, not operative. Still worth a sentence in the state-machine doc when that gets written.

8. **Plan PR → issue-closing chain not audited.** Plan PR uses `Refs #NN` (good, non-closing). Implementation PR closes the source issue only if the implementer includes `Closes #NN` in the body. #159 closed #152 today via Copilot's `Fixes #152` — so it works when the implementer follows convention. But no guard exists if it forgets. Low-frequency bug; worth a one-liner check in reviewer.

9. **New: chicken-and-egg on self-modification.** #159 landed, but any future PR that edits `.github/workflows/reviewer.md` still hits the self-tamper guard — by design. Escape hatch is manual human review (the `human-review` label). That's correct, but the *documentation* of the escape hatch is non-obvious. Add one paragraph to `AGENT_FACTORY.md`: "how to land a PR that modifies a protected workflow."

10. **New: stale weekly proficiency report issues (#9, #10, #13)** sitting open since January. Housekeeping — either close them or wire the weekly report to auto-close the previous week's issue.

11. **New: #29 "No-Op Runs" just flagged by triage.** First operational signal from the factory about its own behavior. Worth a plan: are workflows no-op'ing correctly (good — means the skip conditions work), or no-op'ing when they shouldn't (bad — silent coverage gap)?

### GitHub Projects: still the highest-leverage next move

Unchanged from morning. Visualization layer, not control plane. ~1-day task. Columns = factory states, fields for implementer / blocked-since / plan link, three saved views (*Active*, *Needs human*, *Stalled >48h*).

Now slightly more urgent: with six PRs landed today, the "is anything stuck?" question is real. Labels + `gh` queries answered it today because the volume was low and you were at the keyboard. Scale that to a week of background activity and the dashboard gap bites.

### Priority order going forward

1. **Fresh smoke test on a new issue.** Six fixes landed today. Confirm the clean-room flow: new issue → triage → spec → plan PR → merge → ready-for-implementation → implementer PR → reviewer + contribution-checker + simplify-and-harden + eval-creator → merge. No human nudges between stages. (User's stated next step.)
2. **GitHub Projects board.** One day. Immediate leverage on the observability of the factory itself. Highest-ROI remaining work.
3. **Write the one-page state-machine doc.** Label transition table + workflow trigger table. Cuts onboarding and debugging. Also forces an honest accounting of every label (flushes out any more dead ones).
4. **Add the self-modification escape-hatch paragraph to `AGENT_FACTORY.md`.** One commit. Prevents future confusion when someone hits the self-tamper guard.
5. **Decide on #29 (no-op runs).** Cheap investigation — read the workflow logs, classify the no-ops as intentional vs unintentional.
6. **Close stale weekly-report issues #9, #10, #13.** Housekeeping.
7. **Audit plan → impl PR issue-closing.** Add a reviewer check for `Closes|Fixes #NN` when a plan-backed PR is under review.
8. **Fold `ci-cleaner` and `conflict-resolver` into the main chain diagram.** Docs-only. Small.

### Bottom line

Morning's verdict was "flow is on solid ground after today; main weakness is visibility and minor dead code." Evening's verdict: **dead code is gone, observability is shipped, the chain is proven end-to-end. The only material remaining gap is operator visibility.** Projects board closes that.

The factory crossed a threshold today. It stopped being a scaffold under active construction and became a system that can run background work while you're doing something else. That's the point where the dashboard becomes indispensable.

---

## Snapshot: 2026-04-17 (morning, post-#138)

*Archived for traceability. Superseded by the evening snapshot above.*

Initial analysis after the #138 refactor removed the sub-issue layer. Identified 8 weak points; priority list recommended Projects board, multi-implementer decision, #97 observability, state-machine doc, plan-PR audit. By evening: #97 shipped, multi-implementer decided (collapsed), plus four more fixes landed. Projects, state-machine doc, and plan-PR audit remain open.
