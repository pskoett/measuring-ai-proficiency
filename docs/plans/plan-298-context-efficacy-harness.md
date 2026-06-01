# Plan 298 — Context Efficacy Proving Harness (v0.7.0)

Source issue: #298. Ship vehicle: feature branch → PR → main → v0.7.0 release.

## Goal

Break the static-scan ceiling: stop scoring what artifacts *exist* and start proving
what they *do*, with reproducible evidence, reported as a separate **Efficacy Score**
(0–100) alongside the Proficiency Score. Turn the tool from a context *linter* into a
context *proving harness*.

## Decisions locked (via /plan-interview)

| Decision | Choice |
|----------|--------|
| Execution model | `--prove` = resolve/validate only (no arbitrary exec). `--prove-exec` = run repo code in a hardened sandbox. Exec **hard-blocked on remote/GitHub-scanned repos**. Whole pass opt-in; default scan unchanged. |
| Scoring | Report-only **Efficacy Score (0–100)** + per-artifact pass/fail. Does NOT change level or proficiency score. |
| MVP provers | (1) Commands, (2) Hooks, (3) Token-efficiency / context budget (deterministic, no exec). |
| Surfaces | CLI (`--prove`/`--prove-exec`), MCP `prove_efficacy` tool, CI gh-aw workflow (PR comment). |
| Security | Threat model + executor hardening + required `harden-auditor` pass before merge. |
| Deferred | Skills smoke prover; LLM behavior-change probe; efficacy gating L6+. |

## Success Criteria

Done when, on this repo and fixtures:
1. `measure-ai-proficiency --prove` runs WITHOUT executing any repo-defined code, and reports:
   - per documented command: resolves? (✓/✗) with the exact check command;
   - per hook: wired? (✓/✗) with where it's declared;
   - a **Context Budget**: always-on token estimate, % of a reference window, efficiency ratio;
   - an aggregate **Efficacy Score (0–100)**.
2. `measure-ai-proficiency --prove-exec` additionally executes commands/hooks in the sandbox and reports run outcomes; it **refuses to exec** for `--github-repo`/`--github-org` (prints why) and when `--prove-exec` is absent.
3. Efficacy is rendered in all four reporters and serialized in JSON (`_score_to_dict`) and CSV; the level and proficiency score are byte-for-byte unchanged when `--prove` is off.
4. MCP `prove_efficacy` tool returns the same structured result (resolve-only by default; exec arg honored but blocked for remote).
5. CI gh-aw workflow runs the (resolve-only) pass on PRs and comments the efficacy result.
6. Threat model documented; `harden-auditor` green on the executor; `pytest` green (new tests for each prover + the remote-exec block + the off-by-default invariant); ≥2 new eval cases.

## Architecture

New isolated module `measure_ai_proficiency/efficacy.py` (mirrors `signals.py`):

```
efficacy.py
  @dataclass ArtifactCheck   { name, kind, status: pass|fail|skip, evidence, reproduce_cmd, detail }
  @dataclass ProberResult    { prober, checks: List[ArtifactCheck], score, summary }
  @dataclass ContextBudget   { always_on_tokens, files: Dict[path,tokens], window_tokens, pct_of_window, efficiency_ratio, method }
  @dataclass EfficacyResult  { provers: Dict[str,ProberResult], context_budget, score, executed: bool, warnings }
  class EfficacyAnalyzer(repo_path, score: RepoScore, execute: bool, is_remote: bool, config)
      run() -> EfficacyResult        # runs the 3 provers; never execs if is_remote or not execute
  # provers
  _prove_commands(...)   # extract documented commands -> shutil.which / `<cmd> --help` (exec gated)
  _prove_hooks(...)      # parse settings.json + .claude/hooks; exec synthetic event (exec gated)
  _measure_context_budget(...)  # deterministic token estimate of always-on context
  # sandbox
  _run_sandboxed(cmd, stdin, cwd, timeout, env_allowlist) -> (rc, out, err, timed_out)
```

- **Tokenizer:** use `tiktoken` if importable, else a heuristic (`ceil(chars/4)`); record `method` in the output. No hard new dependency.
- **Always-on set for the budget:** present `INSTRUCTION_FILES` (CLAUDE.md, AGENTS.md, copilot-instructions, .cursorrules, CODEX.md) + the cumulative skill **frontmatter metadata** (Layer-2, the part that's effectively always-routable). Reference window default `context_window_tokens = 200_000` (configurable).
- **Score:** weighted blend of command-resolution rate, hook-wiring(/exec) rate, and a budget-efficiency factor; capped 0–100; report-only.

## Integration points (precise)

- `scanner.py`: add `efficacy: Optional["EfficacyResult"] = None` to `RepoScore`. Do **not** call efficacy from `scan()`. Add a thin `RepoScanner.prove(score, execute, is_remote)` that delegates to `EfficacyAnalyzer`. (`__init__.py` exports the new public types.)
- `__main__.py` (argparse, ~L160): add `--prove`, `--prove-exec` (implies prove), `--context-window N`. After scoring each repo, if prove requested → run analyzer with `execute=args.prove_exec` and `is_remote=(github mode)`; attach `score.efficacy`. Exec is forced off for `--github-repo`/`--github-org`/`--org` with a printed notice.
- `reporter.py`: render efficacy in `TerminalReporter`/`MarkdownReporter` (a "Context Efficacy (--prove)" section: per-artifact ✓/✗ + reproduce cmd, Context Budget, Efficacy Score), in `JsonReporter._score_to_dict` (an `efficacy` block — also consumed by MCP), and a couple of CSV columns (`efficacy_score`, `always_on_tokens`).
- `mcp_server.py`: new `prove_efficacy` tool (list_tools + call_tool + handler). Resolve-only by default; optional `execute` arg honored only for the local cwd repo (never remote).
- `repo_config.py`: add `context_window_tokens` (default 200000) + `command_allowlist` (safe default set) + `prove` skip hooks, parsed from `.ai-proficiency.yaml`.
- `.github/workflows/efficacy.md` (+ compiled `.lock.yml` via `gh aw compile`): PR-triggered, runs `--prove` (resolve-only), comments the efficacy summary. (CI exec deferred.)
- Docs: `docs/EFFICACY.md` (the harness + threat model), plus pointers from `README.md`, `docs/SIGNALS.md`, `CLAUDE.md`. Bump `__init__.py` + `pyproject.toml` → 0.7.0.

## Threat Model (executor)

`--prove-exec` runs repo-defined commands/hooks → treat repo input as untrusted.

| Risk | Mitigation |
|------|------------|
| Arbitrary code exec on scan | Exec is opt-in (`--prove-exec`), **never** on remote/GitHub repos, never in default scan; prints what it will run. |
| Destructive commands | Command **allowlist** (basenames); prefer `--help`/dry-run; deny shell metacharacters; no `shell=True`. |
| Env/secret exfiltration | Scrubbed env (minimal PATH + explicit allowlist), no inherited tokens. |
| Runaway / hang | Per-call timeout + output size cap + total-time budget. |
| Network calls | Best-effort: scrub proxy vars; document that true network isolation needs a container (known limitation, called out in `log()`/docs). |
| Path escape | Run with `cwd` set; resolve+contain any written paths (reuse the 0.6.0 traversal guard pattern). |

A `harden-auditor` pass over `efficacy.py` must be green before merge.

## Affected Files/Areas

New: `efficacy.py`, `docs/EFFICACY.md`, `docs/plans/plan-298-...md`, `.github/workflows/efficacy.{md,lock.yml}`, `.evals/cases/EVAL-014+.md`, tests `tests/test_efficacy.py` (+ MCP/reporter test additions).
Modified: `scanner.py` (RepoScore field + prove()), `__main__.py` (flags), `reporter.py` (4 renderers + JSON/CSV), `mcp_server.py` (tool), `repo_config.py` (config), `__init__.py`/`pyproject.toml` (0.7.0), `README.md`/`docs/SIGNALS.md`/`docs/MCP.md`/`CLAUDE.md`/`.evals/EVAL_INDEX.md`.

## Risk Assessment

- **Security (high):** mitigated by the threat model above + opt-in + remote-block + harden pass.
- **False positives in command extraction (med):** conservative extractor (only fenced/backticked tokens that look like real CLIs; skip prose); mark uncertain as `skip`, not `fail`.
- **Tokenizer accuracy (low):** heuristic is approximate; label the method and treat the budget as an estimate, not a verdict.
- **Backward-compat (low):** efficacy is additive + opt-in; assert level/score unchanged when off.
- **OneDrive git friction (op):** push via the established fast-/tmp-clone path.

## Rejected Alternatives

- *Execute by default* — too risky for a tool people run on arbitrary repos.
- *Make efficacy modify/gate the score now* — deferred; ship the measurement first (earn complexity), gate in a later version once the signal is trusted.
- *Container-based sandbox in MVP* — heavy/portability cost; revisit if exec scope grows.

## Open Questions

- [ ] Tokenizer: ship pure-heuristic only, or optional `tiktoken`? — Can proceed (default heuristic; tiktoken if present).
- [ ] CI: resolve-only in 0.7.0, exec-in-CI later? — Can proceed (resolve-only).
- [ ] Always-on budget: include skill frontmatter metadata or instruction files only? — Can proceed (instruction files + skill frontmatter; configurable).
- [ ] Command allowlist default contents — Can proceed (start strict: build/test/lint tooling basenames; user-extendable via config).

## Implementation Checklist

- [ ] `efficacy.py`: dataclasses + `EfficacyAnalyzer` + sandbox runner (hardened).
- [ ] Commands prover (resolve + gated exec).
- [ ] Hooks prover (wiring + gated synthetic-event exec).
- [ ] Context-budget prover (deterministic token estimate + efficiency ratio).
- [ ] Wire `RepoScore.efficacy` + `RepoScanner.prove()`; keep `scan()` unchanged.
- [ ] `__main__.py` flags (`--prove`, `--prove-exec`, `--context-window`) + remote-exec block.
- [ ] Reporters (terminal/markdown/json/csv) + `_score_to_dict` efficacy block.
- [ ] MCP `prove_efficacy` tool (+ test).
- [ ] `repo_config.py` options + parsing.
- [ ] CI gh-aw `efficacy.md` (+ compile) PR comment.
- [ ] Tests: per-prover, remote-exec-blocked, off-by-default invariant, MCP, reporter.
- [ ] Eval cases EVAL-014+ (efficacy module + remote-block guard).
- [ ] Threat model doc `docs/EFFICACY.md` + harden-auditor pass.
- [ ] Docs (README/SIGNALS/MCP/CLAUDE) + bump to 0.7.0.
- [ ] Verify: `pytest` green; dogfood `--prove` on this repo; then branch → PR → release.
