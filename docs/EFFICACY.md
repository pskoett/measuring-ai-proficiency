# Context Efficacy Proving Harness (`--prove`)

`measure-ai-proficiency` (v0.7.0+) can **prove** what a repo's AI artifacts actually
*do*, not just that they exist — and reports it as a separate, **report-only**
Efficacy Score (0–100) with per-artifact green/red evidence and a reproducing command.

It never changes the Proficiency Score or maturity level. Efficacy answers a different
question: *"of the context you have, how much demonstrably works?"*

```bash
measure-ai-proficiency --prove          # resolve-only: runs NO repo code
measure-ai-proficiency --prove-exec     # also executes commands/hooks in a sandbox (local only)
measure-ai-proficiency --prove --context-window 1000000   # custom budget window
```

## What it proves (MVP)

| Prover | Resolve-only (`--prove`) | With `--prove-exec` |
|--------|--------------------------|---------------------|
| **Commands** | Documented CLI commands resolve on `PATH` (`command -v`) | Also runs the allowlisted `<cmd> --help` probe in the sandbox (never the documented args) |
| **Hooks** | Hooks are wired in `settings.json` / present in `.claude/hooks`, and referenced scripts exist | Safe repo-local `.claude/hooks/*.(sh|py)` targets are run against synthetic events; guard-like `PreToolUse` hooks must block a synthetic bad case |
| **Context budget** | Always-on token footprint (instruction files + skill frontmatter), % of a reference window, efficiency factor — **deterministic, never executes** | (same) |

Each check reports `pass` / `fail` / `skip` with evidence and a copy-pasteable
reproducing command. **Absence isn't penalized** — a prover with nothing to prove is
excluded from the score (presence is the Proficiency score's job; efficacy is about
whether what *exists* works).

## Security model

`--prove-exec` runs repo-defined code, so repo content is treated as **untrusted input**.

- **Opt-in, twice.** Nothing executes under `--prove` (resolve-only). Execution requires
  the explicit `--prove-exec` flag.
- **Never on remote.** Execution is **hard-blocked** for `--github-repo` / `--github-org`
  scans (and the MCP tool never executes remote). The CLI prints a notice and downgrades
  to resolve-only.
- **Default scan unchanged.** A normal scan (no `--prove`) computes no efficacy and runs
  nothing new.

### Executor hardening (`efficacy._run_sandboxed`)

| Control | Implementation |
|---------|----------------|
| No shell injection | Commands run from an `argv` **list**; never `shell=True`. |
| Command allowlist | Only basenames in `DEFAULT_COMMAND_ALLOWLIST` (build/test/lint *nouns* — no shells/interpreters) execute, and only the fixed `<cmd> --help` probe runs (never documented args). The probe always runs the `PATH`-resolved binary for the basename. A repo's `.ai-proficiency.yaml` can only **narrow** the allowlist (intersection), never widen it. |
| Scrubbed env | Only `PATH`/`LANG`/`TMPDIR`/… pass through. `HOME` is **replaced with a throwaway temp dir** per call so user credential files (`~/.npmrc`, `~/.pypirc`, `~/.m2`, …) are never read. No inherited tokens/secrets. |
| Hook execution scope | Under `--prove-exec`, only safe repo-local `.claude/hooks/*.(sh|py)` script targets are run (via `sh`/`python3`) with synthetic JSON events. Arbitrary hook command strings are never executed directly. |
| Timeout | Per-call `_EXEC_TIMEOUT_SECONDS` (15s); timeouts are reported as `fail`. |
| Output cap | stdout/stderr truncated to `_OUTPUT_CAP_BYTES`. |
| Path containment | Hook-referenced scripts are resolved and confined strictly inside the repo dir. |

### Known limitation

True **network isolation** requires a container/namespace, which is out of scope for the
MVP. We mitigate with the allowlist, scrubbed env, timeouts, and output caps, and call it
out here rather than imply the sandbox is airtight. Run `--prove-exec` only on repos you
trust; CI runs resolve-only.

## Surfaces

- **CLI:** `--prove` / `--prove-exec` / `--context-window` (renders in all four formats; new CSV columns `efficacy_score`, `always_on_tokens`, `efficacy_executed`).
- **MCP:** `prove_efficacy` tool (resolve-only by default; `execute` arg honored for the local repo only) — lets an assistant prove its own setup works.
- **CI:** `.github/workflows/efficacy.yml` runs the resolve-only pass on PRs and posts a sticky comment.

## Scoring

Report-only Efficacy Score (0–100) = mean of the available sub-scores (command
resolution rate, hook wiring/exec rate, context-budget efficiency factor). It is shown
*beside* the Proficiency Score and never alters the level.

## Deferred

Skills smoke-test prover; an LLM **behavior-change probe** (run a model turn with/without
a rule and measure whether output changes — the automated *"what would go wrong if this
line wasn't here?"*); and efficacy **gating** L6+ once the signal is trusted.

See [SIGNALS.md](SIGNALS.md) for the (presence/structure) signal layer and
[AGENTS_FILE_GUIDANCE.md](AGENTS_FILE_GUIDANCE.md) for the conciseness guidance the
context-budget prover quantifies.
