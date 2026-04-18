---
plan-id: plan-001
status: shipped
shipped-in: "#32"
---
# Plan 001: Audit and update all docs/ files

**Source issue**: #32
**Status**: Ready for implementation

## Problem Statement

The codebase has evolved significantly. The agent factory grew to 11 workflows (adding `implementer-dispatcher`), 8 skills were added or updated, the MCP server was added (`mcp_server.py`), and the GitHub scanner (`github_scanner.py`) was added. Several docs files predate these additions and contain stale descriptions, missing components, or cross-references to outdated content.

## Success Criteria

- Every file in `docs/` accurately reflects the current state of the code and factory chain.
- No doc references a file, feature, or workflow that does not exist.
- `implementer-dispatcher` is described where the factory chain is discussed.
- `mcp_server.py` and `github_scanner.py` appear in architecture and API docs.
- All 8 skills appear in `AGENT_FACTORY.md` and `chain.md` skill tables.
- Cross-references between docs resolve to real files.
- Writing style: no em-dashes, short declarative sentences, lead with the answer.

## Risk Assessment

**Blast radius**: Low. Docs only. No code changes.
**Rollback**: Trivial. Revert the commit.
**Risk**: Introducing new inaccuracies while fixing old ones. Mitigation: read each source file in `measure_ai_proficiency/` before editing the corresponding doc section.

## Affected Files/Areas

All files in `docs/`:
- `docs/ARCHITECTURE.md` - Missing `mcp_server.py` and `github_scanner.py` components
- `docs/chain.md` - Missing `implementer-dispatcher` in the flow diagram; shows human-assigns step instead of automated dispatch
- `docs/AGENT_FACTORY.md` - Appears mostly current; verify skills table has all 8 skills
- `docs/API.md` - Verify `--github-repo` and `--github-org` flags are documented
- `docs/CHANGELOG.md` - Verify recent additions (MCP server, GitHub scanner, factory chain, skills) are recorded
- `docs/CONTRIBUTING.md` - Verify skills sync instructions cover all three skill locations
- `docs/CONVENTIONS.md` - Verify writing style rules match current AGENTS.md conventions
- `docs/CUSTOMIZATION.md` - Verify config options match `repo_config.py`
- `docs/FEATURE_BACKLOG.md` - Verify completed features are marked done and not listed as upcoming
- `docs/GITHUB_ACTION.md` - Verify action setup instructions are accurate
- `docs/MCP.md` - Verify all 7 MCP tools are documented with correct signatures
- `docs/PATTERNS.md` - Verify detection patterns match `config.py` and `scanner.py`
- `docs/SECURITY.md` - Verify security considerations are current
- `docs/SPEC.md` - Verify project specification reflects current scope
- `docs/TESTING.md` - Verify test instructions match current test suite
- `docs/AGENT_REFERENCES.md` - Verify best practices for agent references are current
- `docs/plans/README.md` - Appears current; confirm no changes needed

## Open Questions

- [ ] Does `docs/FEATURE_BACKLOG.md` need the MCP server and GitHub scanner marked as completed? Likely yes. Can proceed.
- [ ] Should `docs/CHANGELOG.md` use semantic versioning or date-based entries? Inspect existing format and match it. Can proceed.

## Implementation Checklist

- [ ] Read `measure_ai_proficiency/mcp_server.py` and update `docs/ARCHITECTURE.md` to include the MCP server component (layer, entry point, available tools)
- [ ] Read `measure_ai_proficiency/github_scanner.py` and update `docs/ARCHITECTURE.md` to include the GitHub scanner component
- [ ] Update `docs/ARCHITECTURE.md` data flow diagram to show GitHub CLI scanning path alongside local scanning path
- [ ] Update `docs/chain.md` flow diagram to replace the "human assigns to chosen agent" step with `implementer-dispatcher` node
- [ ] Update `docs/chain.md` skills table to include all 8 skills: `plan-interview`, `self-improvement`, `dx-data-navigator`, `intent-framed-agent`, `context-surfing`, `measure-ai-proficiency`, `customize-measurement`, `agentic-workflow`
- [ ] Verify `docs/AGENT_FACTORY.md` skills table lists all 8 skills and add any missing entries
- [ ] Verify `docs/API.md` documents `--github-repo` and `--github-org` flags; add if missing
- [ ] Verify `docs/MCP.md` documents all 7 MCP tools (`scan_current_repo`, `get_recommendations`, `check_cross_references`, `get_level_requirements`, `scan_github_repo`, `scan_github_org`, `validate_file_quality`) with correct signatures
- [ ] Verify `docs/PATTERNS.md` matches current `CROSS_REF_PATTERNS` and `QUALITY_PATTERNS` in `scanner.py` and `LEVELS` in `config.py`
- [ ] Verify `docs/CUSTOMIZATION.md` config options match the fields in `repo_config.py`; update any that have changed
- [ ] Verify `docs/CONTRIBUTING.md` skills sync instructions cover `.claude/skills/`, `.github/skills/`, and `skill-template/`; update if needed
- [ ] Verify `docs/CONVENTIONS.md` writing style rules include the no-em-dash and short-sentence rules from `AGENTS.md`
- [ ] Update `docs/CHANGELOG.md` to record MCP server, GitHub scanner, and agent factory chain additions if not already recorded
- [ ] Verify `docs/FEATURE_BACKLOG.md` marks MCP server and GitHub scanner as completed
- [ ] Verify `docs/GITHUB_ACTION.md` setup instructions are accurate for the current codebase
- [ ] Verify `docs/SPEC.md` reflects current scope including MCP server and GitHub CLI scanning
- [ ] Verify `docs/SECURITY.md` covers MCP server security considerations
- [ ] Verify `docs/TESTING.md` reflects current test coverage and test commands
- [ ] Verify `docs/AGENT_REFERENCES.md` best practices are current
- [ ] Run a cross-reference check: scan all markdown links in `docs/` and confirm each target file exists
- [ ] Confirm no doc still describes the old 10-workflow count (the correct count is 11)

## Rejected Alternatives

**Automated script to check cross-references**: A script could find broken links, but it cannot verify semantic accuracy (e.g., whether a doc correctly describes what a function does). Manual per-file audit is required.

## Recommended implementer

**Choice**: claude-sonnet-4.6
**Rationale**: 17 files to audit and update with clear scope and existing patterns. The work requires reading source files to verify accuracy, then updating doc content. No architectural decisions. Sonnet is the right default for systematic single-pass documentation work.
