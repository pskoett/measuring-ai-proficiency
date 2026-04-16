# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - 2026-04-16

### Added
- **Agent Factory Chain**: 11 agentic workflows powered by GitHub Agentic Workflows (gh-aw)
  - `spec-refiner`: Structured plan files from issue context using plan-interview skill
  - `reviewer`: Plan-aware code review with implementer calibration
  - `self-improvement-meta`: Nightly learning extraction and prevention rule promotion
  - `ci-cleaner`: Auto-fix lint, test, and compile issues on main
  - `contribution-checker`: PR compliance checking against CONTRIBUTING.md
  - `implementer-dispatcher`: Auto-assigns sub-issues to agents from parent issue's `impl:*` label
  - `issue-triage`, `plan`, `pr-fix` (from githubnext/agentics)
  - `ai-proficiency-pr-review`, `ai-proficiency-weekly-report` (project-specific)
- **Implementer Dispatcher**: Automatic sub-issue assignment based on `impl:*` label from parent issue. Eliminates manual agent assignment per sub-issue.
- **MCP Server** (`measure_ai_proficiency/mcp_server.py`): Real-time AI proficiency awareness for AI assistants
  - `scan_current_repo`: Analyze AI proficiency of the current repository
  - `get_recommendations`: Get specific improvement suggestions
  - `check_cross_references`: Validate references between AI context files
  - `get_level_requirements`: Show requirements for the next maturity level
  - `scan_github_repo`: Analyze remote GitHub repository without cloning
  - `scan_github_org`: Analyze entire GitHub organizations
  - `validate_file_quality`: Check quality score of a specific file
  - Installable as `measure-ai-proficiency-mcp` entry point
  - Configurable via `.mcp.json` at repository root
- **Skills** (11 skills in `.claude/skills/`):
  - `plan-interview`: Structured requirements interview before planning
  - `intent-framed-agent`: Intent contract to prevent scope drift
  - `context-surfing`: Context window health monitoring
  - `simplify-and-harden`: Post-completion quality and security sweep
  - `verify-gate`: Machine verification gate (tests, lint) before quality review
  - `eval-creator`: Regression test cases from promoted learnings
  - `learning-aggregator`: Cross-session pattern detection and promotion ranking
  - `pre-flight-check`: Session-start scan of relevant learnings and eval status
  - `measure-ai-proficiency`: Run AI proficiency assessments
  - `customize-measurement`: Configure measurement for specific repos
  - `agentic-workflow`: GitHub agentic workflow creation
- `docs/AGENT_FACTORY.md`: Full factory chain guide with step-by-step instructions
- `docs/chain.md`: Architecture diagram and design rationale
- `docs/plans/`: Plan files directory with `plan-NNN-<slug>.md` naming convention
- `.ai-proficiency.yaml.example`: Example configuration file

### Changed
- Factory chain uses choreography (label-based handoffs) instead of orchestration (central DAG)
- Implementer routing determined by `impl:*` labels set by spec-refiner at plan time

## [0.3.0] - 2026-01-08

### Added
- **GitHub CLI Integration**: Scan repositories without cloning them
  - New `--github-repo OWNER/REPO` flag to scan single GitHub repositories
  - New `--github-org ORG` flag to scan entire GitHub organizations
  - New `--limit N` flag to control maximum repos scanned from organizations
  - Smart file filtering - only downloads AI proficiency files (not full clones)
  - Automatic temp directory management with cleanup
  - Minimal .git structure creation for compatibility
- **AI Context Improvement Agent**: Systematic repository context enhancement
  - Integrated workflow using plan-interview, customize-measurement, and measure-ai-proficiency skills
  - Available in `.github/agents/improve-ai-context.agent.md` and `.claude/agents/improve-ai-context.agent.md`
  - Context-aware configuration and requirements gathering
  - Quality templates for CLAUDE.md, ARCHITECTURE.md, CONVENTIONS.md, SKILL.md
  - Intelligent workflow mode selection (full, quick, config-only)
- Rate limit handling with exponential backoff retry logic
- Comprehensive test suite for GitHub scanner module

### Changed
- Documentation updates across 7+ files (README, CLAUDE.md, copilot-instructions, skills, etc.)
- Skill templates restructured with three scanning methods (GitHub direct, discover+clone, local)
- scripts/README.md now recommends direct GitHub scanning over discovery script

### Fixed
- GitHub API rate limit handling with retry logic
- Temporary directory cleanup in all error scenarios

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

[0.5.0]: https://github.com/pskoett/measuring-ai-proficiency/compare/v0.3.0...v0.5.0
[0.3.0]: https://github.com/pskoett/measuring-ai-proficiency/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/pskoett/measuring-ai-proficiency/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/pskoett/measuring-ai-proficiency/releases/tag/v0.1.0
