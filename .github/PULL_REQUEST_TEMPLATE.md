# Pull Request

## Description

Provide a clear and concise description of what this PR does.

**Fixes:** #(issue number)

## Type of Change

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Code refactoring
- [ ] Performance improvement
- [ ] Test addition or improvement
- [ ] Build/CI improvement

## Changes Made

List the specific changes made in this PR:

- Change 1
- Change 2
- Change 3

## Testing

Describe the testing you've done:

- [ ] All existing tests pass (`pytest`)
- [ ] Added new tests for new functionality
- [ ] Tested manually with example repositories
- [ ] Tested with different output formats (terminal, JSON, markdown, CSV)
- [ ] Tested edge cases

**Test commands run:**
```bash
# Example
pytest tests/test_scanner.py
python -m measure_ai_proficiency --help
```

## Checklist

- [ ] My code follows the style guidelines (black, ruff)
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] I have updated CHANGELOG.md with my changes
- [ ] Any dependent changes have been merged and published

## Documentation Updates

- [ ] README.md updated (if needed)
- [ ] CHANGELOG.md updated
- [ ] CLAUDE.md updated (if architecture changed)
- [ ] Other documentation updated: _____

## Breaking Changes

If this PR introduces breaking changes, describe:

- What breaks
- Migration path for users
- Why the breaking change is necessary

## Screenshots (if applicable)

Add screenshots to show before/after behavior, especially for terminal output changes.

## Additional Context

Add any other context about the pull request here. Include:

- Related issues or PRs
- References to discussions
- Links to relevant documentation
- Performance implications
- Dependency changes

## Reviewer Notes

Any specific areas you'd like reviewers to focus on?

---

**For Maintainers:**

- [ ] Version bumped appropriately (major/minor/patch)
- [ ] Release notes prepared (if needed)
- [ ] PyPI release planned (if needed)
