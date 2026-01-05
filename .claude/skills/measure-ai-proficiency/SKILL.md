---
name: measure-ai-proficiency
description: Assess and improve repository AI coding proficiency and context engineering maturity. Use when users ask about: (1) AI readiness or AI maturity assessment, (2) context engineering quality or improvement, (3) CLAUDE.md, .cursorrules, or copilot-instructions files, (4) measuring how well a repo is prepared for AI coding assistants, (5) recommendations for improving AI collaboration, (6) what context files to add, or (7) comparing their repo to AI proficiency best practices.
---

# Measure AI Proficiency

Assess repository context engineering maturity and provide actionable recommendations for improving AI collaboration.

## Workflow

### 1. Run Assessment

```bash
python -m measure_ai_proficiency -v
```

### 2. Interpret Results

**Maturity Levels:**

| Level | Name | Indicators |
|-------|------|------------|
| 0 | No Context Engineering | No AI-specific files |
| 1 | Basic Instructions | CLAUDE.md, .cursorrules exist |
| 2 | Comprehensive Context | Architecture, conventions documented |
| 3 | Skills & Workflows | Hooks, commands, memory files |
| 4 | Multi-Agent | Specialized agents, orchestration |

**Score interpretation:** File count matters more than percentage. The tool includes hundreds of patterns for comprehensive detection.

### 3. Provide Recommendations

After assessment, offer to create missing high-priority files:

**Level 1 gaps:** Create CLAUDE.md, .cursorrules, or .github/copilot-instructions.md

**Level 2 gaps:** Create ARCHITECTURE.md, CONVENTIONS.md, or TESTING.md

**Level 3 gaps:** Create .claude/commands/, MEMORY.md, or skills/

### 4. Create Missing Files

When creating context files, include:

**CLAUDE.md structure:**
- Project overview (what it does, who it's for)
- Directory structure and key files
- Important conventions and patterns
- Common tasks and how to perform them
- Things to avoid

**ARCHITECTURE.md structure:**
- System overview and purpose
- Key components and responsibilities
- Data flow between components
- Important design decisions

**CONVENTIONS.md structure:**
- Naming conventions
- Code organization patterns
- Error handling approach
- Testing conventions

## Quick Reference

Common triggers for this skill:
- "Assess my AI proficiency"
- "How mature is my context engineering?"
- "What context files should I add?"
- "Help me improve for AI coding"
- "Check my CLAUDE.md setup"
- "Am I ready for AI-assisted development?"

## Reference

For full documentation, see:
- [README.md](../../../README.md) - Tool documentation
- [CUSTOMIZATION.md](../../../CUSTOMIZATION.md) - How to customize patterns
- [measuring-ai-proficiency-context-engineering.md](../../../measuring-ai-proficiency-context-engineering.md) - The thinking behind this tool
