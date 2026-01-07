# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-01-07

### Added
- Cross-reference detection in AI instruction files
- Content quality evaluation for AI instruction files (sections, commands, constraints, commits)
- Bonus points system (up to +10 points) based on cross-references and quality
- GitHub organization discovery script (`scripts/find-org-repos.sh`)
- Tool auto-detection (Claude Code, GitHub Copilot, Cursor, OpenAI Codex)
- Repository configuration via `.ai-proficiency.yaml`
- Custom threshold support for level advancement
- Focus areas and skip recommendations configuration
- Quality scoring configuration options
- Comprehensive documentation updates

### Changed
- Recommendations now tailored to detected AI tools
- Verbose output is now the default (use `--quiet` to suppress)
- Improved progress bars with threshold indicators
- Enhanced level breakdown showing both custom and default thresholds

### Fixed
- Pattern detection for all AI tool directories
- Git commit history tracking for quality scoring

## [0.1.0] - 2024-12-XX

### Added
- Initial release
- 8-level maturity model (aligned with Steve Yegge's stages)
- Support for Claude Code, GitHub Copilot, Cursor, and OpenAI Codex
- Multiple output formats (terminal, JSON, markdown, CSV)
- Repository scanning with pattern matching
- Level-specific recommendations
- CLI with multiple scanning modes (single repo, multiple repos, org directory)
- Comprehensive test suite
- Documentation (README, CLAUDE.md, TESTING.md, SPEC.md, PATTERNS.md)

[0.2.0]: https://github.com/pskoett/measuring-ai-proficiency/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/pskoett/measuring-ai-proficiency/releases/tag/v0.1.0
