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

**Yes, it fits — as a visualization layer, not a control plane.**

### What Projects can do here

- **Board view with columns = factory states.** Triage → Spec → Planning → Ready → Assigned → Review → Needs-changes → Merged → Learning. Label-based automations move cards between columns. Gives you a single-glance view of the whole factory.
- **Custom fields** for implementer, estimated effort, blocked-since date, plan file link.
- **Views** for daily operation: *Needs human* (filter on `blocked-on-human`, `needs-changes`, `human-review`), *Stalled* (filter on `ready-for-implementation` with no `assigned-to-agent` for 48h — catches dispatcher failures), *Learning queue* (filter on `self-improvement` PRs).
- **Cross-repo aggregation** if the factory ever runs in more than one repo. Today it's local, but the model scales.

### What Projects can't do here

- **Drive the workflows.** Projects observes state; labels carry state. If someone drags a card, the label doesn't auto-update (you can configure the reverse — label change moves card — but not the other way cleanly).
- **Replace any part of the factory.** The decisions stay in labels and workflow code. Projects is read-only for the automation.
- **Run conditional logic** richer than "label X means column Y." Anything smarter stays in workflow code.

### Risk

Adding Projects introduces a *potential* second source of truth. Mitigation: strict convention that labels are authoritative, Projects is derived. Don't use the Projects board as a place to make decisions — use it to see what's happening.

### Recommendation on Projects

Small, additive, high-leverage. ~1-day task:

1. Create one Project v2 at the org/user level.
2. Single-select field "Factory state" with options matching columns above.
3. Built-in automation: label added → state set. Label removed → state cleared.
4. Three saved views: *All active*, *Needs human*, *Stalled >48h*.
5. No workflow changes. No label changes. Zero risk to the existing chain.

## Priority order going forward

1. **Add the Projects board.** One day. Immediate leverage on observability of the factory itself (meta-observability — before you even tackle #97).
2. **Decide multi-implementer.** Either simplify to two labels or wire Claude/Codex. Current half-built state costs clarity for no benefit.
3. **Ship #97 (transcripts).** Unlocks the learning loop that's currently running on 20% of its signal.
4. **Write one-page factory state-machine doc.** Label transition table + trigger table. Cuts onboarding and debugging time.
5. **Audit plan-PR → impl-PR → issue-closing chain.** Make sure issues reliably close via Copilot's PR, or add a post-merge step that handles it.

## Bottom line

The flow is on solid ground after today. Main weakness isn't architectural — it's visibility and minor dead code. Projects closes the visibility gap cheaply; #97 closes the signal gap structurally.
