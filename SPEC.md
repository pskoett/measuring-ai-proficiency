# plan-interview Skill Specification

## Overview

`plan-interview` is a Claude Code skill that ensures alignment between user and Claude during feature/spec planning through a structured interview process. It hooks into planning mode as a pre-hook, gathering requirements before codebase exploration begins.

## Invocation

**Explicit invocation only** via `/plan-interview`

The skill does not auto-activate. Users must explicitly invoke it when they want the enhanced planning process.

**Research task detection:** If the task is purely research/exploration (not implementation), the skill skips entirely and defers to normal Claude behavior.

## Interview Process

### Timing

Upfront interview **before** any codebase exploration. Claude gathers requirements first, then explores.

### Question Generation

- **Fully generative** - Claude generates questions dynamically based on the task
- **Thematic batches** - Group related questions together (2-3 questions per batch)
- No fixed template; questions adapt to what's being built

### Required Question Domains

Every interview must cover these four domains:

1. **Technical constraints** - Performance requirements, compatibility, existing patterns to follow
2. **Scope boundaries** - What's explicitly out of scope, MVP vs full vision
3. **Risk tolerance** - Acceptable tradeoffs (speed vs quality, tech debt tolerance)
4. **Success criteria** - How will we know when the feature is done and working?

Additionally, include **codebase/architecture understanding** questions when the codebase is unfamiliar or poorly structured.

### Completion Criteria

Interview continues until Claude achieves **actionable specificity** - the ability to describe concrete implementation steps.

### Handling Edge Cases

| Scenario | Behavior |
|----------|----------|
| Contradictory requirements | Make a recommendation with rationale, ask for confirmation |
| User pivots requirements | Restart fresh with new direction |
| Interrupted interview | Ask user whether to continue or restart |

### Anti-Patterns to Avoid

- **Repetitive questions** - Don't ask variations of the same question
- **Silent assumptions** - Don't make major assumptions without asking
- **Over-engineering** - Don't add unnecessary complexity to simple tasks

## Fast Mode (Draft + Refine)

When user wants quick planning:

1. Perform **task-focused search** (find files directly related to the task)
2. Generate **draft plan** based on findings
3. Interview to **refine** the draft

## Output Artifacts

### Location

```
docs/plans/
```

Git-friendly location for PR reviews. No automatic git actions (user handles commits).

### File Naming

Sequential numbering with descriptive suffix:

```
plan-001-user-authentication.md
plan-002-metrics-dashboard.md
```

### Generation Order

Sequential: **Plan file** → (derives) **Checklist** → (derives) **Decision tree**

### Required Plan Elements

Every plan must include, regardless of structure:

| Element | Description |
|---------|-------------|
| **Success criteria** | Clear definition of done |
| **Risk assessment** | What could go wrong and mitigations |
| **Affected files/areas** | Which parts of codebase will be touched |
| **Open questions** | Remaining uncertainties (user decides which block implementation) |

### Optional Elements

| Element | Include When |
|---------|--------------|
| **Rejected alternatives** | Major architectural decisions were made |
| **Visual artifacts** | Helpful for understanding (ASCII or Mermaid diagrams) |
| **Decision tree** | Multiple valid approaches with real tradeoffs exist |

### Plan Schema

**Freeform with constraints** - Claude decides structure but must include required elements.

- No length or complexity limits
- **No time estimates** - Just describe what needs doing

### Checklist

**Embedded in plan document** as a section (not separate file).

### Decision Tree

Only generated when there are **multiple valid approaches with real tradeoffs**. Not included for straightforward implementations.

## Post-Plan Behavior

### Approval

After plan is written, user reviews. On approval:

- **Auto-start implementation** immediately
- No explicit "proceed" confirmation needed

### Implementation Checkpoints

**At natural breakpoints** - when Claude is about to make a significant decision, compare progress to plan.

### Abbreviated Mode

If task turns out simpler than expected during exploration, produce a **shorter plan document** rather than full version.

## Integration

### Claude Code Coupling

**Claude Code only** - assumes Claude Code tools and workflows. Not portable to other interfaces.

### Planning Mode Hook

**Pre-hook to EnterPlanMode** - skill runs before standard planning, then hands off.

### State Management

**Stateless** - each planning session starts fresh. Does not track patterns from previous sessions or reference existing plans in `docs/plans/`.

## Example Flow

```
User: /plan-interview Add user authentication to the app

Claude: I'll help you plan the user authentication feature. Let me gather some
        requirements first.

        [AskUserQuestion: Thematic batch about scope/boundaries]
        - What authentication methods should be supported?
        - Is this for new users only or migrating existing sessions?
        - What's explicitly out of scope for this implementation?

User: [Answers]

Claude: [AskUserQuestion: Thematic batch about technical constraints]
        - Are there existing auth patterns in the codebase to follow?
        - What session storage mechanism should we use?
        - Any specific security requirements (MFA, password policies)?

User: [Answers]

Claude: [AskUserQuestion: Thematic batch about risk/tradeoffs]
        ...continues until actionable specificity reached...

Claude: [Explores codebase based on gathered requirements]

Claude: [Writes plan to docs/plans/plan-001-user-authentication.md]

        Here's the plan I've created. Review it and let me know if it looks good.

User: Looks good, let's do it.

Claude: [Auto-starts implementation, uses TodoWrite to track progress]
        [At natural breakpoints, compares progress to plan]
```

## Configuration

No configuration required. The skill is designed to be drop-in usable across any Claude Code project.
