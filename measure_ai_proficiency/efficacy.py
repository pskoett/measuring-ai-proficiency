"""
Context efficacy proving harness (v0.7.0).

Proves what a repository's AI artifacts actually DO, not just that they exist, and
reports a separate, **report-only** Efficacy Score (0-100) plus per-artifact green/red
evidence with a reproducing command. It never changes the Proficiency Score or level.

SECURITY (see docs/EFFICACY.md for the full threat model):
- The default pass (`execute=False`, i.e. CLI `--prove`) RESOLVES/VALIDATES only — it
  runs no repo-defined code. It checks that documented commands resolve, that hooks are
  wired, and estimates the always-on token budget.
- Executing repo-defined commands/hooks requires explicit opt-in (`execute=True`, i.e.
  CLI `--prove-exec`) and is HARD-BLOCKED for remote / GitHub-scanned repos.
- Repo content is treated as untrusted input: execution uses an argv list (never via a
  shell), a command allowlist, a scrubbed env, a timeout, and an output cap.
- Hooks are NEVER executed (only validated for wiring + contained script existence);
  only the commands prober runs, and only a fixed `<cmd> --help` probe (never the
  documented arguments).
"""

import os
import re
import json
import math
import shutil
import tempfile
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# =============================================================================
# Hardening constants
# =============================================================================

# Env vars passed through to sandboxed processes (everything else is dropped).
# NOTE: HOME is intentionally EXCLUDED — it is replaced with a throwaway temp dir per
# call so user credential files (~/.npmrc, ~/.pypirc, ~/.m2/settings.xml, ...) can never
# be read by a probed tool.
_SAFE_ENV_KEYS = ("PATH", "LANG", "LC_ALL", "LC_CTYPE", "TMPDIR", "SYSTEMROOT")

# Default allowlist of command basenames eligible for the `<cmd> --help` probe under
# --prove-exec. Resolution checks (`which`) are always safe and not gated by this.
#
# DELIBERATELY EXCLUDES general-purpose shells / code-eval runtimes (bash, sh, python,
# node, deno, ruby, perl, ...): those accept arbitrary code via `-c`/`-e`, so allowing
# them — even just for `--help` — would weaken the allowlist as a defense. Only build /
# test / lint *nouns* that don't take an arbitrary code string are included. (Hooks are
# never executed at all; see _prove_hooks.)
DEFAULT_COMMAND_ALLOWLIST: frozenset = frozenset({
    "make", "just", "npm", "pnpm", "yarn", "pytest", "go", "cargo", "ruff",
    "black", "mypy", "flake8", "eslint", "prettier", "tox", "uv", "pip", "pip3",
    "jest", "vitest", "tsc", "poetry", "gradle", "mvn", "dotnet", "rake",
    "bundle", "rubocop", "golangci-lint", "pre-commit", "hatch", "nox",
})

_EXEC_TIMEOUT_SECONDS = 15      # per command/hook
_OUTPUT_CAP_BYTES = 8_000       # captured stdout/stderr cap
_DEFAULT_CONTEXT_WINDOW = 200_000

# Hook lifecycle event names (Claude Code).
_HOOK_EVENTS = (
    "PreToolUse", "PostToolUse", "SessionStart", "Stop",
    "SubagentStop", "UserPromptSubmit", "PreCompact", "Notification",
)

# Words that look command-like in backticks but are prose/builtins we skip to reduce
# false positives in the commands prober.
_COMMAND_STOPWORDS = frozenset({
    "the", "a", "an", "and", "or", "if", "for", "in", "to", "of", "is", "are",
    "this", "that", "true", "false", "null", "none", "todo", "note", "eg", "ie",
})

# Inline-code / fenced command extraction.
_INLINE_CODE = re.compile(r"`([^`\n]{2,200})`")
_FENCED_BLOCK = re.compile(r"```(?:bash|sh|shell|console|zsh)?\n(.*?)```", re.DOTALL)
_CMD_FIRST_TOKEN = re.compile(r"^[a-z][a-z0-9_.-]{1,40}$")


# =============================================================================
# Result data structures
# =============================================================================

@dataclass
class ArtifactCheck:
    """One proven (or skipped) artifact."""

    name: str
    kind: str                      # "command" | "hook"
    status: str                    # "pass" | "fail" | "skip"
    evidence: str = ""
    reproduce_cmd: str = ""
    detail: str = ""


@dataclass
class ProberResult:
    """Output of a single prober."""

    prober: str                    # "commands" | "hooks"
    checks: List[ArtifactCheck] = field(default_factory=list)
    summary: str = ""

    @property
    def passed(self) -> int:
        return sum(1 for c in self.checks if c.status == "pass")

    @property
    def total_scored(self) -> int:
        """Checks that count toward the rate (pass + fail; skips excluded)."""
        return sum(1 for c in self.checks if c.status in ("pass", "fail"))

    @property
    def rate(self) -> Optional[float]:
        """Pass rate over scored checks, or None if nothing to prove."""
        if self.total_scored == 0:
            return None
        return self.passed / self.total_scored


@dataclass
class ContextBudget:
    """Always-on context token footprint (deterministic; no execution)."""

    always_on_tokens: int = 0
    files: Dict[str, int] = field(default_factory=dict)   # path -> tokens
    skill_metadata_tokens: int = 0
    window_tokens: int = _DEFAULT_CONTEXT_WINDOW
    method: str = "heuristic"      # "tiktoken" | "heuristic"

    @property
    def pct_of_window(self) -> float:
        if self.window_tokens <= 0:
            return 0.0
        return self.always_on_tokens / self.window_tokens * 100

    @property
    def efficiency_factor(self) -> float:
        """0-1 efficiency: full credit under ~1.5% of the window, decaying to 0 by ~6%."""
        pct = self.pct_of_window
        if pct <= 1.5:
            return 1.0
        if pct >= 6.0:
            return 0.0
        return round(1.0 - (pct - 1.5) / 4.5, 3)


@dataclass
class EfficacyResult:
    """Combined efficacy evidence + report-only score."""

    provers: Dict[str, ProberResult] = field(default_factory=dict)
    context_budget: Optional[ContextBudget] = None
    executed: bool = False         # whether any repo code was actually run
    warnings: List[str] = field(default_factory=list)

    @property
    def score(self) -> float:
        """Report-only Efficacy Score (0-100): mean of available sub-scores.

        Provers with nothing to prove are excluded (absence is the Proficiency
        score's concern, not efficacy's).
        """
        parts: List[float] = []
        for p in self.provers.values():
            if p.rate is not None:
                parts.append(p.rate)
        if self.context_budget and self.context_budget.always_on_tokens > 0:
            parts.append(self.context_budget.efficiency_factor)
        if not parts:
            return 0.0
        return round(sum(parts) / len(parts) * 100, 1)

    @property
    def has_evidence(self) -> bool:
        return any(p.checks for p in self.provers.values()) or bool(
            self.context_budget and self.context_budget.always_on_tokens > 0
        )


# =============================================================================
# Token estimation
# =============================================================================

def estimate_tokens(text: str) -> Tuple[int, str]:
    """Estimate tokens. Uses tiktoken if importable, else a chars/4 heuristic."""
    if not text:
        return 0, "heuristic"
    try:
        import tiktoken  # optional dependency
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text)), "tiktoken"
    except Exception:
        return math.ceil(len(text) / 4), "heuristic"


# =============================================================================
# Analyzer
# =============================================================================

class EfficacyAnalyzer:
    """Runs the efficacy provers against a repository.

    `score` is the RepoScore from a prior scan (duck-typed to avoid importing the
    scanner module here). It is read-only.
    """

    def __init__(
        self,
        repo_path,
        score=None,
        execute: bool = False,
        is_remote: bool = False,
        config=None,
        context_window: Optional[int] = None,
    ):
        self.repo_path = Path(repo_path)
        self.score = score
        # Execution is opt-in AND never permitted on remote/GitHub-scanned repos.
        self.is_remote = is_remote
        self.execute = bool(execute) and not is_remote
        self.config = config
        self.context_window = (
            context_window
            or getattr(config, "context_window_tokens", None)
            or _DEFAULT_CONTEXT_WINDOW
        )
        # The allowlist is a SECURITY control, so it must never be WIDENED by untrusted
        # repo content. A repo-supplied list (from .ai-proficiency.yaml) can only NARROW
        # the built-in default via intersection — never add commands.
        repo_allow = getattr(config, "command_allowlist", None)
        if repo_allow:
            self.allowlist = frozenset(repo_allow) & DEFAULT_COMMAND_ALLOWLIST
        else:
            self.allowlist = DEFAULT_COMMAND_ALLOWLIST

    # ----- public -----

    def run(self) -> EfficacyResult:
        result = EfficacyResult(executed=self.execute)
        if self.is_remote:
            result.warnings.append(
                "Execution is disabled for remote/GitHub-scanned repos; resolve-only results shown."
            )
        elif not self.execute:
            result.warnings.append(
                "Resolve-only pass (no repo code executed). Use --prove-exec to probe "
                "documented commands with `--help`. (Hooks are always validate-only.)"
            )
        else:
            result.warnings.append(
                "Executing allowlisted documented commands with `--help` only. "
                "Hooks are validate-only (never executed)."
            )
        result.provers["commands"] = self._prove_commands()
        result.provers["hooks"] = self._prove_hooks()
        # Context budget is a measurement (no pass/fail checks), so it is reported as a
        # separate `context_budget` field rather than a ProberResult in `provers`. It
        # still contributes its efficiency_factor to the overall Efficacy Score.
        result.context_budget = self._measure_context_budget()
        return result

    # ----- helpers -----

    def _within_repo(self, path: Path) -> bool:
        """True if path resolves to a location strictly inside the repo (symlink-safe)."""
        try:
            repo_root = self.repo_path.resolve()
            resolved = path.resolve()
            return resolved == repo_root or repo_root in resolved.parents
        except (OSError, ValueError, RuntimeError):
            return False

    def _read(self, rel: str) -> Optional[str]:
        path = self.repo_path / rel
        try:
            # Containment guards against a symlink in the repo pointing outside it.
            if path.is_file() and self._within_repo(path) and path.stat().st_size <= 1_000_000:
                return path.read_text(encoding="utf-8", errors="ignore")
        except (OSError, PermissionError):
            return None
        return None

    def _instruction_files(self) -> List[str]:
        # Lazy import avoids a module-load cycle with scanner.
        from .scanner import INSTRUCTION_FILES
        present = []
        for name in INSTRUCTION_FILES:
            if (self.repo_path / name).is_file():
                present.append(name)
        return present

    def _run_sandboxed(self, argv: List[str], stdin: Optional[str] = None) -> dict:
        """Run argv in a hardened subprocess. Returns a result dict.

        Runs from an argv list only (never via a shell). Allowlisted basename only.
        Scrubbed env. Timeout + output cap.
        """
        base = os.path.basename(argv[0]) if argv else ""
        if base not in self.allowlist:
            return {"blocked": True, "rc": None, "out": "", "err": f"{base} not in allowlist", "timed_out": False}

        # Always run the PATH-resolved binary for the allowlisted basename — never an
        # arbitrary (possibly absolute) caller-supplied path. Closes the basename-checked-
        # but-argv0-executed inconsistency.
        resolved = shutil.which(base)
        if not resolved:
            return {"blocked": False, "rc": None, "out": "", "err": f"{base} not found", "timed_out": False}

        env = {k: os.environ[k] for k in _SAFE_ENV_KEYS if k in os.environ}
        # Best-effort hostility reduction (true network isolation needs a container).
        env["GIT_TERMINAL_PROMPT"] = "0"
        env["PIP_NO_INPUT"] = "1"
        env["CI"] = "1"
        # Throwaway HOME so user credential files are never read/leaked by the probe.
        home = tempfile.mkdtemp(prefix="maip-prove-home-")
        env["HOME"] = home
        env["NPM_CONFIG_USERCONFIG"] = os.path.join(home, ".npmrc")
        env["PIP_CONFIG_FILE"] = os.path.join(home, "pip.conf")
        env["GRADLE_USER_HOME"] = os.path.join(home, ".gradle")
        run_argv = [resolved] + list(argv[1:])
        try:
            proc = subprocess.run(
                run_argv,
                cwd=str(self.repo_path),
                env=env,
                input=stdin,
                capture_output=True,
                text=True,
                timeout=_EXEC_TIMEOUT_SECONDS,
                check=False,
            )
            return {
                "blocked": False,
                "rc": proc.returncode,
                "out": (proc.stdout or "")[:_OUTPUT_CAP_BYTES],
                "err": (proc.stderr or "")[:_OUTPUT_CAP_BYTES],
                "timed_out": False,
            }
        except subprocess.TimeoutExpired:
            return {"blocked": False, "rc": None, "out": "", "err": "timeout", "timed_out": True}
        except (OSError, ValueError) as e:
            return {"blocked": False, "rc": None, "out": "", "err": str(e), "timed_out": False}
        finally:
            shutil.rmtree(home, ignore_errors=True)

    # ----- provers -----

    def _extract_commands(self) -> List[str]:
        """Conservatively extract documented CLI command basenames from instruction files."""
        candidates: List[str] = []
        seen = set()
        for rel in self._instruction_files():
            content = self._read(rel)
            if not content:
                continue
            spans: List[str] = list(_INLINE_CODE.findall(content))
            for block in _FENCED_BLOCK.findall(content):
                for line in block.splitlines():
                    line = line.strip()
                    if line and not line.startswith("#"):
                        spans.append(line)
            for span in spans:
                span = span.strip().lstrip("$ ").strip()
                if not span:
                    continue
                first = span.split()[0] if span.split() else ""
                first = first.strip("`'\"")
                # Must look like a CLI basename (no slashes/metachars) — this is the
                # real filter; bare prose words are rejected by the regex + stopwords +
                # the has-args/allowlist check below.
                if not _CMD_FIRST_TOKEN.match(first):
                    continue
                if first in _COMMAND_STOPWORDS:
                    continue
                # Only count a token as a command if it takes args (looks like usage)
                # or is in the allowlist of known tools.
                has_args = len(span.split()) > 1
                if not has_args and first not in self.allowlist:
                    continue
                if first not in seen:
                    seen.add(first)
                    candidates.append(first)
        return candidates

    def _prove_commands(self) -> ProberResult:
        result = ProberResult(prober="commands")
        commands = self._extract_commands()
        for cmd in commands:
            resolved = shutil.which(cmd) is not None
            if not resolved:
                result.checks.append(ArtifactCheck(
                    name=cmd, kind="command", status="fail",
                    evidence="not found on PATH",
                    reproduce_cmd=f"command -v {cmd}",
                    detail="documented command does not resolve",
                ))
                continue
            if not self.execute:
                result.checks.append(ArtifactCheck(
                    name=cmd, kind="command", status="pass",
                    evidence=f"resolves to {shutil.which(cmd)}",
                    reproduce_cmd=f"command -v {cmd}",
                ))
                continue
            # Execute a benign probe (--help) under the sandbox.
            res = self._run_sandboxed([cmd, "--help"])
            if res["blocked"]:
                result.checks.append(ArtifactCheck(
                    name=cmd, kind="command", status="skip",
                    evidence="resolves; exec skipped (not in allowlist)",
                    reproduce_cmd=f"command -v {cmd}",
                ))
            elif res["timed_out"]:
                result.checks.append(ArtifactCheck(
                    name=cmd, kind="command", status="fail",
                    evidence="`--help` timed out", reproduce_cmd=f"{cmd} --help",
                ))
            else:
                # Help text commonly exits 0/1/2; treat "ran without crashing" as pass.
                ok = res["rc"] is not None
                result.checks.append(ArtifactCheck(
                    name=cmd, kind="command", status="pass" if ok else "fail",
                    evidence=f"`--help` exit={res['rc']}", reproduce_cmd=f"{cmd} --help",
                ))
        if commands:
            result.summary = f"{result.passed}/{result.total_scored} documented commands work"
        else:
            result.summary = "no documented CLI commands found"
        return result

    def _hook_commands(self) -> List[Tuple[str, str]]:
        """Return (event, command) pairs from the COMMITTED settings.json only.

        settings.local.json is intentionally skipped: it is gitignored/local and may
        contain user-specific hook commands with credentials/paths we should not capture
        into the (potentially PR-posted) efficacy report. Efficacy proves committed context.
        """
        pairs: List[Tuple[str, str]] = []
        for rel in (".claude/settings.json",):
            content = self._read(rel)
            if not content:
                continue
            try:
                data = json.loads(content)
            except (json.JSONDecodeError, ValueError):
                continue
            hooks = data.get("hooks") if isinstance(data, dict) else None
            if not isinstance(hooks, dict):
                continue
            for event, entries in hooks.items():
                if not isinstance(entries, list):
                    continue
                for entry in entries:
                    inner = entry.get("hooks", []) if isinstance(entry, dict) else []
                    for h in inner if isinstance(inner, list) else []:
                        if isinstance(h, dict) and h.get("command"):
                            pairs.append((event, str(h["command"])))
        return pairs

    def _prove_hooks(self) -> ProberResult:
        result = ProberResult(prober="hooks")
        pairs = self._hook_commands()

        # Also note hook scripts present on disk (wired implicitly by convention).
        hooks_dir = self.repo_path / ".claude" / "hooks"
        script_files: List[Path] = []
        if hooks_dir.is_dir():
            try:
                script_files = [f for f in hooks_dir.iterdir() if f.is_file()]
            except (OSError, PermissionError):
                pass

        # SECURITY: hooks are NEVER executed (their command strings are arbitrary
        # untrusted shell). We only validate that they are wired and that any
        # referenced repo-local script actually exists. This holds even under
        # --prove-exec — running hook command strings safely needs a container,
        # which is out of scope (see docs/EFFICACY.md).
        for event, command in pairs:
            argv = command.split()
            first = os.path.basename(argv[0]) if argv else ""
            # Sanitize untrusted values from repo settings.json before embedding them in
            # report strings (they could carry shell metacharacters/newlines): the event
            # name against the known-events allowlist, and the command basename against
            # the CLI-token charset.
            safe_event = event if event in _HOOK_EVENTS else repr(event)
            safe_first = first if _CMD_FIRST_TOKEN.match(first) else "<cmd>"
            referenced = self._resolve_referenced_script(argv)
            if referenced is not None and not referenced.exists():
                result.checks.append(ArtifactCheck(
                    name=f"{safe_event}:{safe_first}", kind="hook", status="fail",
                    evidence=f"hook script missing: {referenced}",
                    reproduce_cmd=f"test -f {referenced}",
                    detail="hook wired but its script is absent",
                ))
                continue
            result.checks.append(ArtifactCheck(
                name=f"{safe_event}:{safe_first}", kind="hook", status="pass",
                evidence="wired in settings (validate-only; hooks are not executed)",
                reproduce_cmd=f"jq '.hooks[\"{safe_event}\"]' .claude/settings.json",
            ))

        for f in script_files:
            if f.suffix.lower() == ".md":
                continue
            rel = str(f.relative_to(self.repo_path))
            # Informational only ("skip" so it doesn't inflate the pass rate): a script's
            # mere presence doesn't prove it's wired or works.
            result.checks.append(ArtifactCheck(
                name=rel, kind="hook", status="skip",
                evidence="hook script present (not independently graded)",
                reproduce_cmd=f"test -f {rel}",
            ))

        if result.checks:
            result.summary = f"{result.passed}/{result.total_scored} hooks wired/valid (validate-only)"
        else:
            result.summary = "no hooks configured"
        return result

    def _resolve_referenced_script(self, argv: List[str]) -> Optional[Path]:
        """If a hook command points at a repo-local script file, return its path."""
        for tok in argv:
            if "/" in tok and (tok.endswith(".sh") or tok.endswith(".py") or ".claude/hooks" in tok):
                # Strip only a leading "./" prefix (NOT lstrip('./'), which would also
                # eat the leading dot of ".claude/...").
                rel = tok[2:] if tok.startswith("./") else tok
                candidate = (self.repo_path / rel).resolve()
                # Contain strictly INSIDE the repo dir (a path equal to the repo root is
                # never a valid script file, so it is not accepted).
                try:
                    repo_root = self.repo_path.resolve()
                    if repo_root in candidate.parents:
                        return candidate
                except (OSError, ValueError):
                    return None
        return None

    def _measure_context_budget(self) -> ContextBudget:
        budget = ContextBudget(window_tokens=int(self.context_window))
        method = "heuristic"
        total = 0
        for rel in self._instruction_files():
            content = self._read(rel)
            if not content:
                continue
            toks, m = estimate_tokens(content)
            method = m
            budget.files[rel] = toks
            total += toks

        # Always-routable skill metadata (Layer-2 frontmatter is effectively always loaded).
        meta_tokens = 0
        for pattern in (".claude/skills/*/SKILL.md", ".github/skills/*/SKILL.md", "skills/*/SKILL.md"):
            try:
                for skill in self.repo_path.glob(pattern):
                    # glob follows symlinks; skip any SKILL.md that resolves outside the
                    # repo so a malicious symlink can't pull in /etc/passwd, ~/.ssh, etc.
                    if not (skill.is_file() and self._within_repo(skill)):
                        continue
                    content = skill.read_text(encoding="utf-8", errors="ignore")
                    fm = _frontmatter(content)
                    if fm:
                        toks, m = estimate_tokens(fm)
                        method = m
                        meta_tokens += toks
            except (OSError, PermissionError):
                pass

        budget.skill_metadata_tokens = meta_tokens
        budget.always_on_tokens = total + meta_tokens
        budget.method = method
        return budget


def _frontmatter(content: str) -> str:
    """Extract the YAML frontmatter block (between leading --- fences), else ''."""
    if not content.lstrip().startswith("---"):
        return ""
    stripped = content.lstrip()
    end = stripped.find("\n---", 3)
    if end == -1:
        return ""
    return stripped[: end + 4]
