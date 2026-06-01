"""
Tests for the context efficacy proving harness (--prove).

Security-critical invariants covered:
- resolve-only by default (no repo code executed)
- execution hard-blocked on remote/GitHub-scanned repos
- efficacy is off by default (a normal scan computes none)
- report-only (never changes the level or proficiency score)
"""

import tempfile
from pathlib import Path

from measure_ai_proficiency import RepoScanner


def _make_repo(root: Path, *, missing_hook: bool = True, guard_hook: bool = False) -> None:
    """Fixture: documented commands + wired hooks (one present, one missing) + a skill."""
    (root / "CLAUDE.md").write_text(
        "# Project\n## Commands\n"
        "Run `python3 --version` for the interpreter. Build with `make build`.\n"
        "`definitely-not-a-real-cmd-xyz --frobnicate` is documented but not installed.\n"
        + "x" * 100
    )
    claude = root / ".claude"
    (claude / "hooks").mkdir(parents=True)
    if guard_hook:
        (claude / "hooks" / "guard.sh").write_text(
            '#!/bin/sh\n'
            'payload="$(cat)"\n'
            'echo "$payload" | grep -q \'"rm -rf /"\' && exit 2\n'
            "exit 0\n"
        )
        hook_cmd = "bash .claude/hooks/guard.sh"
    else:
        (claude / "hooks" / "format.sh").write_text("echo formatted\n")
        hook_cmd = "bash .claude/hooks/format.sh"
    hooks_json = (
        '{"hooks":{'
        f'"PreToolUse":[{{"matcher":"Write","hooks":[{{"type":"command","command":"{hook_cmd}"}}]}}]'
    )
    if missing_hook:
        hooks_json += (
            ',"Stop":[{"hooks":[{"type":"command",'
            '"command":"bash .claude/hooks/missing.sh"}]}]'
        )
    hooks_json += "}}\n"
    (claude / "settings.json").write_text(hooks_json)
    skill = claude / "skills" / "foo"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\nname: foo\ndescription: does foo when needed\n---\n# Foo\n"
    )


class TestEfficacyDefaults:
    def test_efficacy_off_by_default(self):
        """A normal scan must NOT compute efficacy."""
        with tempfile.TemporaryDirectory() as tmp:
            _make_repo(Path(tmp))
            score = RepoScanner(tmp).scan()
            assert score.efficacy is None

    def test_prove_does_not_change_level_or_score(self):
        """Proving is report-only: level and proficiency score are unchanged."""
        with tempfile.TemporaryDirectory() as tmp:
            _make_repo(Path(tmp))
            sc = RepoScanner(tmp)
            score = sc.scan()
            level_before, score_before = score.overall_level, score.overall_score
            sc.prove(score, execute=False, is_remote=False)
            assert score.overall_level == level_before
            assert score.overall_score == score_before


class TestEfficacyProvers:
    def test_resolve_only_executes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            _make_repo(Path(tmp))
            sc = RepoScanner(tmp)
            score = sc.scan()
            eff = sc.prove(score, execute=False, is_remote=False)
            assert eff.executed is False
            assert any("Resolve-only" in w for w in eff.warnings)

    def test_command_resolution(self):
        with tempfile.TemporaryDirectory() as tmp:
            _make_repo(Path(tmp))
            sc = RepoScanner(tmp)
            eff = sc.prove(sc.scan(), execute=False, is_remote=False)
            cmds = {c.name: c.status for c in eff.provers["commands"].checks}
            assert cmds.get("python3") == "pass"
            assert cmds.get("definitely-not-a-real-cmd-xyz") == "fail"

    def test_hook_wiring_and_missing_script(self):
        """The present hook script must NOT be flagged missing; the missing one must fail."""
        with tempfile.TemporaryDirectory() as tmp:
            _make_repo(Path(tmp))
            sc = RepoScanner(tmp)
            eff = sc.prove(sc.scan(), execute=False, is_remote=False)
            checks = eff.provers["hooks"].checks
            # The PreToolUse hook references .claude/hooks/format.sh which exists.
            pre = [c for c in checks if c.name.startswith("PreToolUse")]
            assert pre and all(c.status != "fail" for c in pre), "present hook script falsely failed"
            # The Stop hook references a missing script.
            stop = [c for c in checks if c.name.startswith("Stop")]
            assert stop and any(c.status == "fail" for c in stop)

    def test_context_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            _make_repo(Path(tmp))
            sc = RepoScanner(tmp)
            eff = sc.prove(sc.scan(), execute=False, is_remote=False)
            b = eff.context_budget
            assert b is not None
            assert b.always_on_tokens > 0
            assert "CLAUDE.md" in b.files
            assert 0.0 <= b.efficiency_factor <= 1.0
            assert 0.0 <= b.pct_of_window

    def test_efficacy_score_in_range(self):
        with tempfile.TemporaryDirectory() as tmp:
            _make_repo(Path(tmp))
            sc = RepoScanner(tmp)
            eff = sc.prove(sc.scan(), execute=False, is_remote=False)
            assert 0.0 <= eff.score <= 100.0


class TestEfficacySecurity:
    def test_remote_blocks_execution(self):
        """Execution must be hard-blocked when is_remote=True even with execute=True."""
        with tempfile.TemporaryDirectory() as tmp:
            _make_repo(Path(tmp))
            sc = RepoScanner(tmp)
            eff = sc.prove(sc.scan(), execute=True, is_remote=True)
            assert eff.executed is False
            assert any("remote" in w.lower() or "disabled" in w.lower() for w in eff.warnings)

    def test_exec_runs_safe_hook_scripts_but_not_interpreters(self):
        """Under --prove-exec, command allowlist still blocks interpreters, but safe
        repo-local hook scripts are probed with synthetic events."""
        with tempfile.TemporaryDirectory() as tmp:
            _make_repo(Path(tmp), missing_hook=False, guard_hook=True)
            sc = RepoScanner(tmp)
            eff = sc.prove(sc.scan(), execute=True, is_remote=False)
            assert eff.executed is True
            cmds = {c.name: c for c in eff.provers["commands"].checks}
            # python3 resolves but is intentionally NOT allowlisted -> never executed
            assert "exit=" not in cmds["python3"].evidence
            pre = [c for c in eff.provers["hooks"].checks if c.name.startswith("PreToolUse")]
            assert pre and any("synthetic bad-case exit=" in c.evidence for c in pre)

    def test_exec_guard_hook_blocks_synthetic_bad_case(self):
        with tempfile.TemporaryDirectory() as tmp:
            _make_repo(Path(tmp), missing_hook=False, guard_hook=True)
            sc = RepoScanner(tmp)
            eff = sc.prove(sc.scan(), execute=True, is_remote=False)
            pre = [c for c in eff.provers["hooks"].checks if c.name.startswith("PreToolUse")]
            assert pre and all(c.status == "pass" for c in pre)
