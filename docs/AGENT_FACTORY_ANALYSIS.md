# Agent Factory Analysis (2026-04-17)

Snapshot analysis of the factory after the #138 refactor that removed the sub-issue layer. Intended as a living document — revisit after major workflow changes.

## What's working (keep)

**Choreography over orchestration.** Each workflow owns one job and hands off via a label swap. You can freeze time at any issue or PR and read the current state off GitHub. This is genuinely good design — debuggable, inspectable, no hidden coordinator.

**Three human gates, well placed.** Plan approval, PR merge, learnings approval. All are judgment calls that actually need a human. Everything between them is automated. The ratio is right.

**Source issue as unit of work (post-#138).** Matches human mental model ("one issue, one PR"), removes the parent-lookup class of bugs, removes the sibling-PR conflict class of bugs. The checklist-on-body pattern with the delimited idempotent block is clean.

**Plan file as durable artifact.** Survives in the repo as documentation even after implementation ships. Reviewer has ground truth. Learning loop can refer back.

**Lock-file-sync guard (#131).** Shifted a whole class of silent breakage (`/plan`, `/pr-fix`, etc. failing at runtime because of stale hashes) into loud PR-time failures.

## Genuine weak points

1. **Label semantics are load-bearing and undiagrammed.** The factory state machine lives in 12+ labels scattered across `AGENT_FACTORY.md`, `AGENTS.md`, and `SKILL.md`. There's no single-page diagram of `label → label` transitions and which workflow triggers each. A new operator (or you, two months from now) can't see the state machine in one place.

2. **Hand-patched lock files are a latent footgun.** Today's reconciliation work (6 workflows) proved that the gh-aw `.md` frontmatter isn't expressive enough for every real need — activation-time guards, concurrency tuning, etc. — so people patch the lock directly, the hash diverges, and it sits for days. The CI guard catches *new* drift but we accumulated 6 stale ones before it fired. The real fix is upstream in gh-aw or a docs note that says "never hand-patch the lock, always express it in the .md."

3. **Multi-implementer routing is half-built dead code.** `impl:copilot` is the only auto-route. `impl:claude-opus`, `impl:claude-sonnet`, `impl:codex` are documented, prose-supported, and do nothing. Spec-refiner's "Recommended implementer" section always says "copilot." Either (a) collapse to two labels (`impl:copilot` + `impl:manual`) and drop the dead prose, or (b) wire up the others. Right now the surface area is wider than the behavior.

4. **No operator dashboard.** You can't answer "which issues are stuck at `ready-for-implementation`?" or "which PRs have been `needs-changes` for >24h?" without writing `gh` queries. For a 1-person repo it's fine; for anything bigger it bites.

5. **Observability gap (#97).** `self-improvement-meta` and `learning-aggregator-ci` see workflow telemetry but not agent reasoning. 80% of the signal that would make the outer loop actually smart is being thrown away. Known, tracked.

6. **`ci-cleaner` and `conflict-resolver` are side branches** not integrated into the main chain diagram. They handle failure modes (CI broken on main, PR needs rebase) but the docs treat them as afterthoughts. They're not — they're two of the most-frequently-fired workflows.

7. **Spec-refiner's `needs-plan` label is semantically weak now.** Pre-#138, `needs-plan` triggered `/plan`. Now it just sits waiting for the human to merge the plan PR, then `plan-merged-dispatcher` strips it. The label still communicates "spec done, plan in flight" which is useful, but make sure that's deliberate, not vestigial.

8. **Plan PR → source issue link is brittle.** Plan PR uses `Refs #NN` (non-closing, good). Implementation PR closes the source issue only if Copilot includes `Closes #NN`. Worth an audit.

## GitHub Projects analysis

**Status: built (2026-04-17).** The board is live at [AI Agent Factory](https://github.com/users/pskoett/projects/3) and mirrored from labels by [`sync-factory-state.yml`](../.github/workflows/sync-factory-state.yml). Setup and operating details live in `AGENT_FACTORY.md#github-projects-board`; this section is the "why" and what actually shipped vs. the original proposal.

### What shipped

- **4 lanes, not 9.** The original 9-column proposal (Triage / Spec / Planning / Ready / Assigned / Review / Needs-changes / Merged / Learning) collapsed to **📥 Waiting for spec / 🤖 Factory building / 👉 Your turn / ✅ Done**. The finer-grained states already live in labels; on the board they added noise without adding answers. Four lanes map directly to the only question the board needs to answer: *is it on me, or on the factory?*
- **Zero custom fields.** The original proposal called for an Implementer / Plan PR / Blocked-since set; all four were created, then deleted. Labels already carry that data, and duplicating it on the board created a second source of truth for no operational gain.
- **One-way sync via a plain GitHub Actions workflow**, not the built-in label automation. The built-in automation couldn't express the priority ordering (closed > human-blocking > PR-open > agent-blocking > default), and it couldn't flip the `your-turn` label as a side effect. The workflow runs on every label/state change plus a 10-minute reconcile cron to catch events missed during outages.
- **Separate activity tracker.** `agent-activity-tracker.yml` adds `agent-working` and `model:<name>` labels while a factory workflow is mid-run, so the board can show "something is chewing on this" without polluting the Status field. Not in the original proposal; added after the first day of use because "Factory building" didn't distinguish waiting from running.

### What Projects still can't do

- **Drive the workflows.** Labels remain authoritative. Dragging a card does not change labels; the 10-minute reconcile snaps it back.
- **Replace any part of the factory.** All decisions stay in labels and workflow code.
- **Richer conditional logic** than the priority table in the sync workflow. Anything smarter stays in code.

### Residual risk

- **Second source of truth is still a potential risk.** Mitigated by the one-way sync and by making the board deliberately minimal (4 lanes, no custom fields). Do not add custom fields casually; they will drift.
- **Tracker misses short issue-triggered runs.** GitHub doesn't expose the issue number on `workflow_runs` for `issues` events, and the tracker polls every 5 minutes. Acceptable for visualization; would matter if used for SLAs.
- **Project IDs are hard-coded** in `sync-factory-state.yml`. Replicating the board in another repo requires updating `PROJECT_ID`, `FIELD_ID`, and four option IDs. Documented in the setup steps.

## Priority order going forward

1. ~~**Add the Projects board.**~~ Done 2026-04-17 — see GitHub Projects analysis above.
2. **Decide multi-implementer.** Either simplify to two labels or wire Claude/Codex. Current half-built state costs clarity for no benefit.
3. **Ship #97 (transcripts).** Unlocks the learning loop that's currently running on 20% of its signal.
4. **Write one-page factory state-machine doc.** Label transition table + trigger table. Cuts onboarding and debugging time. (`FACTORY_STATE_MACHINE.md` exists — audit whether it matches the shipped board lanes.)
5. **Audit plan-PR → impl-PR → issue-closing chain.** Make sure issues reliably close via Copilot's PR, or add a post-merge step that handles it.

## Bottom line

The flow is on solid ground after today. Main weakness isn't architectural — it's visibility and minor dead code. Projects closes the visibility gap cheaply; #97 closes the signal gap structurally.
