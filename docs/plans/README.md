# Plan Files

Plan files live here at `docs/plans/plan-NNN-<slug>.md` where NNN is a three-digit zero-padded sequence.

The `spec-refiner` workflow creates these files when an issue is labeled `needs-spec`. Each plan file contains:

- Structured requirements from the plan-interview skill
- Success criteria
- Implementation checklist
- Risk assessment with blast radius
- Recommended implementer (Claude Opus 4.6, Claude Sonnet 4.6, Copilot, or Codex)

Downstream agents use plan files as the source of truth for implementation and review.
