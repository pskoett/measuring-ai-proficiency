# Scanner Scoring Specification

This document is the authoritative reference for how `measure_ai_proficiency` calculates scores. All values here are derived directly from `measure_ai_proficiency/scanner.py`.

## Maturity Levels

Eight levels aligned with Steve Yegge's AI coding proficiency model:

| Level | Name | Description |
|-------|------|-------------|
| 1 | Zero AI | No context engineering (no core AI file present) |
| 2 | Basic Instructions | CLAUDE.md, .cursorrules, or equivalent present |
| 3 | Comprehensive Context | Architecture, conventions, and pattern docs |
| 4 | Skills and Automation | Hooks, commands, skills, memory files |
| 5 | Multi-Agent Ready | Specialized agents, MCP configs |
| 6 | Fleet Infrastructure | CI agents, shared context, workflows |
| 7 | Agent Fleet | Governance, scheduling, handoffs |
| 8 | Custom Orchestration | Meta-automation, frontier tooling |

## Level Advancement Thresholds (`DEFAULT_THRESHOLDS`)

A repository advances to a higher level when the coverage percentage for that level meets or exceeds its threshold. Thresholds cascade: all lower levels must also pass before a higher level is awarded.

| Level | Coverage % Required |
|-------|-------------------|
| 3 | 15% |
| 4 | 12% |
| 5 | 10% |
| 6 | 8% |
| 7 | 6% |
| 8 | 5% |

Level 2 is awarded whenever at least one substantive core AI file exists. Level 1 is the default when no core AI file is found.

Custom thresholds can override these defaults via `.ai-proficiency.yaml` (see `docs/CUSTOMIZATION.md`).

## Minimum Score Guarantees (`LEVEL_MINIMUM_SCORES`)

Every achieved level has a guaranteed minimum score. The reported score is never lower than the minimum for the level reached:

| Level | Minimum Score |
|-------|--------------|
| 2 | 15 |
| 3 | 30 |
| 4 | 45 |
| 5 | 55 |
| 6 | 70 |
| 7 | 85 |
| 8 | 95 |

## Cross-Reference and Quality Bonus

A bonus of up to **+10 points** is added to the base score after the validation penalty is applied.

The bonus is split into two independent components (each capped separately, combined total capped at 10):

### Cross-Reference Bonus (up to 5 pts)

| Sub-component | Calculation | Max |
|--------------|-------------|-----|
| Unique targets | `min(unique_target_count / 2, 3.0)` | 3 pts |
| Resolution rate | `resolved_count / total_refs * 2.0` | 2 pts |
| **Total** | | **5 pts** |

A "resolved" reference is one where the target file actually exists on disk.

### Quality Bonus (up to 5 pts)

| Sub-component | Calculation | Max |
|--------------|-------------|-----|
| Average quality | `avg_quality_score / 2` | 5 pts |

`avg_quality_score` is the mean quality score (0-10) across all scanned instruction files. See `docs/PATTERNS.md` for quality scoring details.

### Combined Cap

```
bonus = min(cross_ref_bonus + quality_bonus, 10.0)
overall_score = min(base_score + bonus, 100)
```

## Validation Penalty

Content validation issues reduce the score before the cross-reference bonus is applied. Maximum total penalty is **10 points**.

| Issue Type | Penalty | Cap |
|-----------|---------|-----|
| Stale instruction files | 2 pts per stale file | 6 pts |
| Invalid file references | 1 pt per broken reference | 4 pts |
| Majority template content | 2 pts flat | 2 pts |
| **Total maximum** | | **10 pts** |

```
base_score = max(0, weighted_score - validation_penalty)
```

## Score Calculation Order

1. Determine coverage percentage per level from matched file patterns.
2. Apply `DEFAULT_THRESHOLDS` (or custom thresholds) to select `overall_level`.
3. Calculate weighted `base_score` across all level contributions.
4. Enforce `LEVEL_MINIMUM_SCORES` floor for the achieved level.
5. Subtract `validation_penalty` (capped at 10, score floored at 0).
6. Add cross-reference and quality `bonus_points` (capped at 10).
7. Clamp final `overall_score` to `[0, 100]`.

## Instruction Files Scanned (`INSTRUCTION_FILES`)

These files are opened and scanned for cross-references and quality indicators:

```
CLAUDE.md
AGENTS.md
.cursorrules
CODEX.md
.github/copilot-instructions.md
.copilot-instructions.md
.github/AGENTS.md
```

## Known Reference Targets (`KNOWN_TARGETS`)

References that resolve to one of these filenames count as "resolved" in the cross-reference bonus calculation:

```
CLAUDE.md        AGENTS.md         .cursorrules      CODEX.md
ARCHITECTURE.md  CONVENTIONS.md    SKILL.md          TESTING.md
API.md           SECURITY.md       CONTRIBUTING.md   PATTERNS.md
DEVELOPMENT.md   DEPLOYMENT.md     MEMORY.md         LEARNINGS.md
HANDOFFS.md      GOVERNANCE.md     SHARED_CONTEXT.md
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | No repositories found |
| 2 | All repositories at Level 1 (no AI context) |
