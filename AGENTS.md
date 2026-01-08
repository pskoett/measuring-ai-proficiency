# Agents

This document defines agent roles and behavioral guidelines for AI assistants working on the measure-ai-proficiency project.

## Agent Roles

### Code Implementer

**Purpose:** Implement features, fix bugs, and maintain the codebase.

**Key behaviors:**
- Follow pure Python conventions (no external dependencies for core functionality)
- Use type hints on all functions and methods
- Use dataclasses for data structures
- Maintain backwards compatibility with Python 3.9+
- Run `pytest tests/ -v` before committing changes

**Files to modify:**
- `measure_ai_proficiency/scanner.py` - Core scanning logic
- `measure_ai_proficiency/config.py` - Level definitions and patterns
- `measure_ai_proficiency/reporter.py` - Output formatting
- `measure_ai_proficiency/repo_config.py` - Configuration handling
- `measure_ai_proficiency/github_scanner.py` - GitHub CLI integration

### Documentation Writer

**Purpose:** Keep documentation accurate and helpful.

**Key behaviors:**
- Update README.md when features change
- Keep CUSTOMIZATION.md current with config options
- Sync skill files across all locations when updating:
  - `.claude/skills/*/SKILL.md`
  - `.github/skills/*/SKILL.md`
  - `skill-template/*/SKILL.md`
- Update `.ai-proficiency.yaml.example` when adding config options

**Constraints:**
- Never add features to docs that don't exist in code
- Always include examples with documentation
- Keep the example output in README.md current

### Skill Developer

**Purpose:** Create and maintain agent skills for this tool.

**Key behaviors:**
- Skills should be self-contained and follow the Agent Skills standard
- Include clear triggers and workflow steps
- Test skills work with both Claude Code and GitHub Copilot
- Sync skills to all three locations after changes

**Available skills:**
- `measure-ai-proficiency` - Run assessments
- `customize-measurement` - Configure for specific repos
- `plan-interview` - Interview-based planning
- `agentic-workflow` - GitHub agentic workflow creation

### Reviewer

**Purpose:** Review changes for quality and consistency.

**Key behaviors:**
- Verify type hints are present
- Check for backwards compatibility
- Ensure tests pass
- Validate documentation is updated
- Check skill files are synced across locations

## Behavioral Guidelines

### All Agents

1. **Test before committing:** Always run `pytest tests/ -v`
2. **Keep skills synced:** Changes to skills must be copied to all three locations
3. **Update version:** Bump version in `pyproject.toml` for releases
4. **Document config options:** New options go in:
   - `repo_config.py` (implementation)
   - `CUSTOMIZATION.md` (documentation)
   - `.ai-proficiency.yaml.example` (example)
   - Skills that use the option

### Exit Codes

Maintain these exit codes:
- `0` - Success
- `1` - No repositories found
- `2` - All repositories at Level 1 (no AI context)

### Scoring System

When modifying scoring:
- Minimum scores per level: L2=15, L3=30, L4=45, L5=55, L6=70, L7=85, L8=95
- Validation penalty: max -4 points
- Cross-reference bonus: max +5 points
- Quality bonus: max +5 points

### Pattern Detection

When adding new patterns:
- Add to appropriate level in `config.py`
- Consider tool-specific filtering (Claude, Copilot, Cursor, Codex)
- Update KNOWN_TARGETS if it's an instruction file
- Add to INSTRUCTION_FILES if it should be scanned for cross-references

## Handoffs

### Implementation to Documentation
After implementing a feature, hand off to documentation:
- Describe what was added/changed
- Note any new config options
- List affected files

### Documentation to Skills
After updating documentation, update skills:
- measure-ai-proficiency skill for assessment features
- customize-measurement skill for config options
