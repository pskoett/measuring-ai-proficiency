# Plan Files

Plan files live here at `docs/plans/plan-NNN-<slug>.md` where NNN is the **source issue number**, zero-padded to three digits (e.g., `042`, `066`, `123`).

The `spec-refiner` workflow creates these files when an issue is labeled `needs-spec`. Each plan file contains:

- Structured requirements from the plan-interview skill
- Success criteria
- Implementation checklist
- Risk assessment with blast radius
- Recommended implementer (Claude Opus 4.6, Claude Sonnet 4.6, Copilot, or Codex)

Downstream agents use plan files as the source of truth for implementation and review.

## Naming Convention

```
plan-NNN-<slug>.md
```

- `NNN`: Three-digit zero-padded **source issue number** (e.g., issue #42 → `042`, issue #66 → `066`)
- `slug`: Short kebab-case description of the plan topic (e.g., `docs-audit`, `add-mcp-server`)

Examples:
- `plan-042-refactor-scanner.md` (plan for issue #42)
- `plan-066-update-plan-numbering.md` (plan for issue #66)
- `plan-123-add-mcp-server.md` (plan for issue #123)

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
