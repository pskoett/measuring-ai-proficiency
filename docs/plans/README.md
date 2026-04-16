# Plan Files

Plan files live here at `docs/plans/plan-NNN-<slug>.md` where NNN is a three-digit zero-padded sequence (e.g., `001`, `002`, `042`).

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

- `NNN`: Three-digit zero-padded sequence number (start at `001`, increment by one)
- `slug`: Short kebab-case description of the plan topic (e.g., `docs-audit`, `add-mcp-server`)

Examples:
- `plan-001-docs-audit.md`
- `plan-002-github-scanning.md`
- `plan-042-refactor-scanner.md`

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
