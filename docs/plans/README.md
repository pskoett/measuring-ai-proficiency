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

Every plan file carries YAML frontmatter at the top of the file that encodes its current lifecycle state:

```yaml
---
plan-id: plan-097
status: shipped
shipped-in: "#97"
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

### Rule for agents

**`status: shipped`, `status: superseded`, and `status: abandoned` plans are historical artifacts. Do not treat them as current design without additional corroboration.** When reasoning about the current state of the system, prefer `status: active` plans and code over any historical plan file.

### Automation

`plan-merged-dispatcher` automatically prepends `status: shipped` and `shipped-in: "#NN"` to every newly merged plan file when the frontmatter is missing. This happens on every plan PR merge and is idempotent.

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
