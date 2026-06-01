# Writing Effective Agents Files (CLAUDE.md / AGENTS.md)

Short, behavioral, and honest beats long and aspirational. This is the guidance the
scanner's conciseness checks (`docs/SIGNALS.md`) nudge toward.

## Why conciseness matters

Always-loaded files (`CLAUDE.md`, `AGENTS.md`, copilot-instructions) are a **permanent
context tax** — every line costs tokens on every turn (even lines the model skips),
multiplies across multi-agent runs, and pushes compaction earlier. Past a point, **a
bloated file makes the model ignore your actual instructions**. Anthropic's Claude Code
memory/best-practices guidance is explicit: keep `CLAUDE.md` focused and human-readable
(aim for well under ~200 lines).

## The one audit rule

> **Every always-loaded line must change behavior, or cut it.**

For each line, ask: *"What would go wrong if this line wasn't here?"* If the answer is
"nothing," delete it. Real teams slim files hard this way (e.g. 180 lines → ~24) and get
better results.

## Avoid aspirational content

Describe how the team **actually works**, not an ideal version of itself. Aspirational
rules ("always write perfect tests", "follow clean architecture") that aren't enforced
add noise and erode trust in the file. Document the real conventions, the real gotchas,
and the things that have actually bitten you.

## Thin core + progressive disclosure

Keep the always-on file a **thin routing layer**; push detail into on-demand surfaces:

- **Skills** (`SKILL.md`) — loaded only when relevant (zero token cost until used).
- **Scoped files** — `src/auth/CLAUDE.md`, path-scoped rules (nearest scope wins).
- **Pointers** — "See `docs/TESTING.md` for the test workflow" instead of inlining it.

## Behavioral baseline (Karpathy's LLM-coding pitfalls)

A widely-used, battle-tested concise `CLAUDE.md` distills four behaviors that counter
common LLM failure modes. They're worth encoding (concisely) in your agents files:

1. **Think before coding** — don't assume silently; surface confusion, tradeoffs, and
   alternatives; ask when unclear.
2. **Simplicity first** — minimum code that solves the problem; no speculative
   abstractions; "if 200 lines could be 50, rewrite it."
3. **Surgical changes** — touch only what the task requires; don't refactor or reformat
   adjacent code; only remove dead code your own change created.
4. **Goal-driven execution** — turn tasks into verifiable success criteria (tests first),
   then loop until they pass.

These map directly to signals the scanner rewards: constraints/"NEVER do" rules,
verification discipline, and surgical/minimal-change conventions.

## References (official + exemplar)

- Claude Code memory & best practices — concise, human-readable `CLAUDE.md`:
  https://docs.claude.com/en/docs/claude-code/memory
- Agent Skills (progressive disclosure): https://docs.claude.com/en/docs/claude-code/skills
- Exemplar of a concise, behavioral `CLAUDE.md` (Karpathy-inspired):
  https://github.com/multica-ai/andrej-karpathy-skills
