# Customizing Measure AI Proficiency

This tool is designed to be customized for your organization's specific conventions and patterns.

## Why Customize?

The default configuration includes hundreds of common patterns, but every organization is different:

- **Different file names**: You might use `SYSTEM_DESIGN.md` instead of `ARCHITECTURE.md`
- **Different folder structures**: `/documentation` instead of `/docs`
- **Custom conventions**: Your own standards for organizing context engineering files
- **Domain-specific patterns**: Finance, healthcare, or other industry-specific documentation

## Quick Start

1. **Run the tool first** to see what it detects:
   ```bash
   measure-ai-proficiency -v
   ```

2. **Review the output**: Look at the files detected vs. your actual documentation

3. **Edit the config**: Modify `measure_ai_proficiency/config.py` to add your patterns

4. **Re-run**: See improved results matching your organization

## How to Customize

### Adding File Patterns

Edit `measure_ai_proficiency/config.py` and add your patterns to the appropriate level:

```python
# Level 2: Add your documentation patterns
LEVEL_2_PATTERNS = LevelConfig(
    file_patterns=[
        # Add your custom patterns at the top
        "SYSTEM_DESIGN.md",              # Your architecture file
        "eng-docs/*.md",                 # Your docs folder
        "team-standards/CODING.md",      # Your conventions
        
        # ... existing patterns below
        "ARCHITECTURE.md",
        "docs/*.md",
        # etc.
    ],
)
```

### Adding Directories

```python
directory_patterns=[
    "eng-docs",           # Your custom docs folder
    "team-standards",     # Your standards folder
    "compliance",         # Industry-specific
    
    # ... existing patterns
    "docs",
    ".claude",
]
```

### Adjusting Thresholds

If scores seem too strict, edit `measure_ai_proficiency/scanner.py`:

```python
def _calculate_overall_level(self, level_scores: Dict[int, LevelScore]) -> int:
    # ...
    
    # Level 2: Change from 20% to 10%
    level_2 = level_scores.get(2)
    if level_2 and level_2.coverage_percent >= 10:  # Was 20
        current_level = 2
    
    # Level 3: Change from 15% to 8%
    level_3 = level_scores.get(3)
    if level_3 and level_3.coverage_percent >= 8:   # Was 15
        current_level = 3
```

## Examples by Organization Type

### Startup / Small Team

```python
# You probably have fewer, more focused files
# Lower the thresholds:
if level_2.coverage_percent >= 5:   # Instead of 20
    current_level = 2
```

### Enterprise

```python
# Add compliance and audit patterns
file_patterns=[
    "COMPLIANCE.md",
    "SOC2.md",
    "SECURITY_AUDIT.md",
    "regulatory/*.md",
    "audit-docs/*.md",
]
```

### Open Source Project

```python
# Focus on contributor documentation
file_patterns=[
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "GOVERNANCE.md",
    "MAINTAINERS.md",
    "docs/development/*.md",
]
```

### Microservices Architecture

```python
# Look for service-specific docs
file_patterns=[
    "services/*/README.md",
    "services/*/ARCHITECTURE.md",
    "services/*/API.md",
    "SYSTEM_OVERVIEW.md",
]
```

## Understanding File Count vs. Percentage

⚠️ **Important**: The percentage is calculated against ALL possible patterns in the config, not your actual files.

**Example:**
- You have 50 documentation files (great!)
- Config has 200 possible patterns
- Coverage: 50/200 = 25%

**This is normal!** Focus on:
1. **Total file count** - More files = better context engineering
2. **Quality** - Are files substantive? (>100 bytes)
3. **Types** - Do you have architecture, API docs, conventions, etc.?

## Testing Your Changes

After customizing, test on a few repositories:

```bash
# Single repo
measure-ai-proficiency /path/to/repo -v

# Multiple repos to compare
measure-ai-proficiency repo1 repo2 repo3 --format csv > results.csv
```

## Sharing Configurations

Consider creating organization-specific forks:

```bash
git clone https://github.com/pskoett/measuring-ai-proficiency
cd measuring-ai-proficiency
git checkout -b acme-corp-config

# Edit config.py with your patterns
# Commit and share with your team
```

## Getting Help

- Check existing patterns in `config.py` for examples
- File an issue if you need patterns for a specific use case
- Share your organization's config as a PR to help others!

## Common Customizations

### I use a different docs folder

```python
file_patterns=[
    "documentation/*.md",
    "*/documentation/*.md",
]
```

### My team doesn't use CLAUDE.md

```python
# Remove from Level 1 or add your equivalent
file_patterns=[
    "AI_INSTRUCTIONS.md",  # Your file
    # "CLAUDE.md",  # Comment out
]
```

### We have nested service directories

```python
file_patterns=[
    "services/*/*/*.md",
    "packages/*/*/*.md",
]
```

### We use GitHub Copilot Skills instead of Claude Skills

```python
# Level 3: Skills patterns
file_patterns=[
    # GitHub Copilot skills (Agent Skills standard)
    ".github/skills/*/SKILL.md",
    ".github/skills/*/*.md",
    ".copilot/skills/*/SKILL.md",
    # Remove if not using Claude
    # ".claude/skills/*/SKILL.md",
]

directory_patterns=[
    ".github/skills",
    ".copilot/skills",
]
```

### We use both Claude and GitHub Copilot Skills

```python
# Level 3: Skills patterns (default includes all three major tools)
file_patterns=[
    ".claude/skills/*/SKILL.md",
    ".github/skills/*/SKILL.md",
    ".copilot/skills/*/SKILL.md",
    ".codex/skills/*/SKILL.md",
    "skills/*/SKILL.md",
]

directory_patterns=[
    ".claude/skills",
    ".github/skills",
    ".copilot/skills",
    ".codex/skills",
    "skills",
]
```

### We only use OpenAI Codex

```python
# Level 3: Codex-only skills
file_patterns=[
    ".codex/skills/*/SKILL.md",
    ".codex/skills/*/*.md",
    "AGENTS.md",  # Codex instruction file
]

directory_patterns=[
    ".codex/skills",
    ".codex",
]
```

### Industry-specific (FinTech)

```python
file_patterns=[
    "COMPLIANCE.md",
    "PCI_DSS.md",
    "SECURITY_STANDARDS.md",
    "regulatory/*.md",
    "audit/*.md",
]
```

### Industry-specific (Healthcare)

```python
file_patterns=[
    "HIPAA.md",
    "PHI_HANDLING.md",
    "SECURITY_COMPLIANCE.md",
    "medical-docs/*.md",
]
```

## Remember

The goal is to **measure context engineering**, not to achieve 100% pattern coverage. The tool works best when adapted to your organization's actual practices.
