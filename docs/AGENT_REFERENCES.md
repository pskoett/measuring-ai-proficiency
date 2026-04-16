# Agent Reference Patterns

## Why Agent References Matter

Agents and AI tools work best when they know **where to find context**. Simply having documentation isn't enough - agents need to be told which documents to consult for specific tasks.

## Critical: PR_REVIEW.md

**PR_REVIEW.md is one of the most important context files** because:
- It defines your team's code review standards
- Sets expectations for what makes a good PR
- Provides criteria for reviewing code quality
- Helps AI provide consistent, valuable feedback

### What PR_REVIEW.md Should Include:

```markdown
# PR Review Guidelines

## Review Checklist
- [ ] Code follows CONVENTIONS.md standards
- [ ] Tests added/updated (see TESTING.md)
- [ ] Documentation updated
- [ ] No security vulnerabilities
- [ ] Performance considerations addressed
- [ ] Follows patterns in PATTERNS.md

## Code Quality Criteria
- Readability: Can team members understand it?
- Maintainability: Easy to modify later?
- Performance: Meets requirements?
- Security: No vulnerabilities?
- Testing: Adequate coverage?

## Review Process
1. Read the PR description
2. Review changed files
3. Check for breaking changes
4. Verify tests pass
5. Provide constructive feedback

## Common Issues to Check
- Hard-coded values (use config)
- Missing error handling
- Inconsistent naming (see CONVENTIONS.md)
- Security concerns (SQL injection, XSS, etc.)
- Performance issues (N+1 queries, etc.)

## Reference Documents
- ARCHITECTURE.md - System design decisions
- CONVENTIONS.md - Coding standards
- PATTERNS.md - Preferred patterns
- SECURITY.md - Security requirements
- TESTING.md - Testing standards
```

## Agent Reference Files

### For All Providers

Create reference files that agents can consult:

**`.github/agents/references.md`** (GitHub Copilot):
```markdown
# Agent Reference Documents

When reviewing code or making suggestions, consult these documents:

## Core References
- **ARCHITECTURE.md** - System design and component structure
- **CONVENTIONS.md** - Coding standards and style guide
- **PATTERNS.md** - Preferred design patterns
- **PR_REVIEW.md** - Code review criteria and process

## Specialized References
- **API.md** - API design and usage patterns
- **TESTING.md** - Testing strategy and requirements
- **SECURITY.md** - Security guidelines
- **DEPLOYMENT.md** - Deployment process
```

**`.claude/agents/references.md`** (Claude Code):
```markdown
# Agent Context Documents

## Primary Context
1. CLAUDE.md - Main project instructions
2. ARCHITECTURE.md - System architecture
3. CONVENTIONS.md - Coding standards
4. PR_REVIEW.md - Review criteria

## Task-Specific Context
- Code changes → CONVENTIONS.md, PATTERNS.md
- Architecture decisions → ARCHITECTURE.md, DESIGN.md
- API changes → API.md, ARCHITECTURE.md
- Testing → TESTING.md, CONVENTIONS.md
- Reviews → PR_REVIEW.md, CONVENTIONS.md, PATTERNS.md
```

**`.cursor/agents/references.md`** (Cursor):
```markdown
# Cursor Agent References

## Always Check These Files
- .cursorrules - Cursor-specific rules
- CONVENTIONS.md - Team standards
- PATTERNS.md - Code patterns

## For Code Reviews
- PR_REVIEW.md - Review criteria
- CONVENTIONS.md - Style guide
- SECURITY.md - Security checklist

## For New Features
- ARCHITECTURE.md - Where to add code
- PATTERNS.md - How to structure code
- TESTING.md - How to test
```

## Embedding References in Agent Files

### GitHub Copilot Agent Example

**`.github/agents/pr-reviewer.agent.md`**:
```markdown
# PR Review Agent

## Role
You are a senior code reviewer ensuring high quality PRs.

## Required Context
Before reviewing any PR, read:
1. `PR_REVIEW.md` - Review criteria and checklist
2. `CONVENTIONS.md` - Coding standards to enforce
3. `PATTERNS.md` - Preferred patterns to verify
4. `SECURITY.md` - Security considerations
5. `ARCHITECTURE.md` - Architectural constraints

## Review Process
1. Check PR description quality
2. Verify adherence to CONVENTIONS.md
3. Validate patterns match PATTERNS.md
4. Apply checklist from PR_REVIEW.md
5. Check security against SECURITY.md

## Provide Feedback On
- Code quality issues
- Convention violations
- Pattern mismatches
- Security concerns
- Missing tests (see TESTING.md)
```

### Claude Agent Example

**`.claude/agents/code-reviewer.md`**:
```markdown
# Code Review Agent

## Context Documents
Read these before every review:
- `CLAUDE.md` - Project overview
- `PR_REVIEW.md` ⭐ CRITICAL - Review standards
- `CONVENTIONS.md` - Coding standards
- `PATTERNS.md` - Design patterns
- `ARCHITECTURE.md` - System design

## Review Criteria
Apply standards from PR_REVIEW.md:
- [ ] Follows conventions
- [ ] Uses established patterns
- [ ] Maintains architecture
- [ ] Includes tests
- [ ] Has documentation

## Reference Checks
- Naming → CONVENTIONS.md
- Structure → PATTERNS.md
- Design → ARCHITECTURE.md
- Security → SECURITY.md
```

### Cursor Agent Example

**`.cursor/agents/reviewer.md`**:
```markdown
# Cursor Review Agent

## Documents to Consult
1. `.cursorrules` - Cursor rules
2. `PR_REVIEW.md` - Review standards ⭐
3. `CONVENTIONS.md` - Style guide
4. `PATTERNS.md` - Code patterns

## Review Workflow
1. Load PR_REVIEW.md checklist
2. Check code against CONVENTIONS.md
3. Verify patterns from PATTERNS.md
4. Provide actionable feedback
```

## Best Practices

### 1. Explicit References
**Don't**: Assume agents know which docs exist
**Do**: Explicitly list documents in agent files

### 2. Prioritize Documents
**Don't**: List 50 documents with equal weight
**Do**: Mark critical docs (⭐) and explain when to use each

### 3. Update References
**Don't**: Create references once and forget
**Do**: Update when adding new documentation

### 4. Cross-Provider Consistency
**Don't**: Different standards for different tools
**Do**: Same core references across GitHub Copilot, Claude, Cursor

### 5. Task-Specific Context
**Don't**: Every agent reads every document
**Do**: PR agents → PR_REVIEW.md, Test agents → TESTING.md

## Common Agent Reference Patterns

### Code Review Agent
Required docs:
- `PR_REVIEW.md` ⭐ (critical)
- `CONVENTIONS.md`
- `PATTERNS.md`
- `SECURITY.md`
- `ARCHITECTURE.md`

### Testing Agent
Required docs:
- `TESTING.md` ⭐
- `CONVENTIONS.md`
- `ARCHITECTURE.md`

### API Design Agent
Required docs:
- `API.md` ⭐
- `ARCHITECTURE.md`
- `CONVENTIONS.md`
- `SECURITY.md`

### Security Review Agent
Required docs:
- `SECURITY.md` ⭐
- `PR_REVIEW.md`
- `ARCHITECTURE.md`
- `CONVENTIONS.md`

### Architecture Agent
Required docs:
- `ARCHITECTURE.md` ⭐
- `DESIGN.md`
- `PATTERNS.md`
- `API.md`

## Validation Checklist

✅ Do your agent files explicitly reference documentation?
✅ Is PR_REVIEW.md marked as critical?
✅ Do you have a centralized references.md file?
✅ Are references consistent across AI tool providers?
✅ Do specialized agents know their specific documents?
✅ Are references updated when new docs are added?

## Examples from Real Projects

### Minimal Setup (Level 3)
```
project/
├── CLAUDE.md
├── PR_REVIEW.md ⭐
├── CONVENTIONS.md
└── .claude/
    └── agents/
        ├── references.md (lists all docs)
        └── reviewer.md (references PR_REVIEW.md)
```

### Comprehensive Setup (Level 4)
```
project/
├── ARCHITECTURE.md
├── CONVENTIONS.md
├── PR_REVIEW.md ⭐
├── PATTERNS.md
├── TESTING.md
├── SECURITY.md
├── .github/
│   ├── agents/
│   │   ├── references.md
│   │   ├── pr-reviewer.agent.md
│   │   ├── security-reviewer.agent.md
│   │   └── test-reviewer.agent.md
│   └── skills/
│       └── custom-task/
│           └── SKILL.md
└── .claude/
    ├── agents/
    │   ├── references.md
    │   ├── code-reviewer.md
    │   ├── architect.md
    │   └── tester.md
    └── skills/
        └── custom-task/
            └── SKILL.md
```

## Agent Skills

Claude Code, GitHub Copilot, Cursor, OpenAI Codex, and generic tooling all support the [Agent Skills](https://agentskills.io/) open standard. Skills are stored in:

- **Claude Code**: `.claude/skills/*/SKILL.md`
- **GitHub Copilot**: `.github/skills/*/SKILL.md`
- **Cursor**: `.cursor/skills/*/SKILL.md`
- **OpenAI Codex**: `.codex/skills/*/SKILL.md`
- **Generic**: `skills/*/SKILL.md`

Skills are task-specific instructions that AI tools load when relevant, based on the skill's description. Unlike agent files that define roles, skills define procedures for specific tasks.

## Scanner Reference: Instruction Files and Known Targets

The scanner reads these files for cross-reference and quality analysis (`INSTRUCTION_FILES` in `scanner.py`):

```
CLAUDE.md
AGENTS.md
.cursorrules
CODEX.md
.github/copilot-instructions.md
.copilot-instructions.md
.github/AGENTS.md
```

References that point to one of the following filenames are counted as "resolved" when calculating the cross-reference bonus (`KNOWN_TARGETS` in `scanner.py`):

```
CLAUDE.md        AGENTS.md         .cursorrules      CODEX.md
ARCHITECTURE.md  CONVENTIONS.md    SKILL.md          TESTING.md
API.md           SECURITY.md       CONTRIBUTING.md   PATTERNS.md
DEVELOPMENT.md   DEPLOYMENT.md     MEMORY.md         LEARNINGS.md
HANDOFFS.md      GOVERNANCE.md     SHARED_CONTEXT.md
```

## Remember

🎯 **The goal**: Agents should never wonder "where can I find the coding standards?"

📚 **The solution**: Explicit references in every agent file

⭐ **The critical file**: PR_REVIEW.md - defines quality standards for all code

🔗 **The pattern**: references.md files that centralize all documentation links
