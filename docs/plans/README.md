# Plan Files

Plan files live here at `docs/plans/plan-NNN-<slug>.md` where NNN is the **source issue number**, zero-padded to three digits (e.g., `007`, `042`, `123`).

The `spec-refiner` workflow creates these files when an issue is labeled `needs-spec`. Each plan file contains:

- Structured requirements from the plan-interview skill
- Success criteria
- Implementation checklist
- Risk assessment with blast radius
- Recommended implementer (Claude Opus 4.6, Claude Sonnet 4.6, Copilot, or Codex)

Downstream agents use plan files as the source of truth for implementation and review.

## Lifecycle Metadata

Every plan file carries YAML frontmatter at the top of the file that encodes its current lifecycle state and implementation surface:

```yaml
---
plan-id: plan-097
status: shipped
shipped-in: "#97"
target-files:
  - AGENTS.md
  - docs/AGENT_FACTORY.md
---
```

### Supported `status` values

| Value | Meaning |
|-------|---------|
| `active` | Current design or open planning artifact. Treat as authoritative. |
| `shipped` | The plan was implemented and merged. Historical artifact. |
| `superseded` | The plan was replaced by a newer plan or design. Historical artifact. |
| `abandoned` | The plan was intentionally not completed. Historical artifact. |

### Companion fields

- `shipped-in`: The source issue number that this plan shipped under (e.g., `"#97"`). Present when `status: shipped`.
- `superseded-by`: The plan ID that replaced this one (e.g., `plan-136`). Present when `status: superseded`.
- `target-files`: List of concrete file paths the implementation is expected to change. **Required for all new plan-worthy issues.** Used by `spec-refiner` to detect overlapping work before dispatch and by `serialization-resolver` to re-evaluate blocked issues. Must list normalized paths relative to the repository root (e.g., `AGENTS.md`, `.github/workflows/spec-refiner.md`). Glob patterns are not supported; list concrete paths only. Exclude generated files and low-conflict areas such as `docs/plans/*`, `.evals/`, `.learnings/`, and test files.

### Rule for agents

**`status: shipped`, `status: superseded`, and `status: abandoned` plans are historical artifacts. Do not treat them as current design without additional corroboration.** When reasoning about the current state of the system, prefer `status: active` plans and code over any historical plan file.

### Automation

`plan-merged-dispatcher` automatically prepends `status: shipped` and `shipped-in: "#NN"` to every newly merged plan file when the frontmatter is missing. This happens on every plan PR merge and is idempotent.

`spec-refiner` reads `target-files` from newly created plan files to run a pre-dispatch overlap check. If `target-files` is missing, the check is skipped and a warning is noted in the dispatch comment.

### target-files contract

- **Who writes it**: `spec-refiner` populates `target-files` in every new plan file it generates, based on the implementation surface identified during the plan-interview skill run.
- **What to include**: Concrete paths that the implementer will edit as part of this plan. Shared harness files (e.g., `AGENTS.md`, `CLAUDE.md`, workflow prompts, factory docs) must be listed if the plan touches them.
- **What to exclude**: `docs/plans/*`, `.evals/`, `.learnings/`, test files, and build artifacts. These paths rarely produce structural conflicts and are excluded from the overlap check to avoid false blocks.
- **Accuracy matters**: `target-files` drift (declaring files that won't be changed, or omitting files that will) degrades the overlap check. Keep the list honest and minimal.

## Naming Convention

```
plan-NNN-<slug>.md
```

- `NNN`: Source issue number, zero-padded to three digits (e.g., issue #7 → `007`, issue #42 → `042`, issue #1042 → `1042`)
- `slug`: Short kebab-case description of the plan topic (e.g., `docs-audit`, `add-mcp-server`)

Examples:
- `plan-007-docs-audit.md` (from issue #7)
- `plan-042-refactor-scanner.md` (from issue #42)
- `plan-123-add-mcp-server.md` (from issue #123)

> **Historical files**: Earlier plan files used a sequential counter (`001`, `002`, …) instead of the issue number. Those files remain valid and should **not** be renamed.




## Plan File Format

Each plan file follows this structure:

```markdown
---
plan-id: plan-NNN
status: active
target-files:
  - path/to/file-one.md
  - path/to/file-two.yml
---
# Plan NNN: <Short Title>

**Source issue**: #<issue-number>
**Status**: Draft | Ready for implementation | In progress | Done

## Problem Statement
...

## Success Criteria
...

## Risk Assessment
**Blast radius**: Low | Medium | High
**Rollback**: ...
**Risk**: ...

## Affected Files/Areas
...

## Implementation Checklist
- [ ] Step one
- [ ] Step two

## Recommended implementer
**Choice**: claude-opus-4.6 | claude-sonnet-4.6 | copilot | codex
**Rationale**: ...
```

The `target-files` frontmatter field is required for all new plan-worthy issues. It enables `spec-refiner` to detect overlapping work before dispatch and allows `serialization-resolver` to re-evaluate blocked issues automatically when in-flight PRs merge. See the **Lifecycle Metadata** section above for the full contract.
