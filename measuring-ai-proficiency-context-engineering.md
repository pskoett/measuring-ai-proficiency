# Measuring AI Proficiency: Context Engineering as a Leading Indicator

There is a lot of discussion about AI adoption rates right now. 91% of developers use AI tools according to recent data. But that number tells you very little about whether people are actually proficient at using them.

I have seen developers save 4+ hours a week with AI. I have also seen developers get slower with the same tools. Same access, very different outcomes.

So how do you measure AI proficiency? Not adoption. Actual proficiency.

I want to propose something concrete: measure context engineering. Look at whether teams are creating files like `CLAUDE.md`, `.cursorrules`, `spec.md`, and `SKILL.md`. These artifacts indicate that someone has moved beyond treating AI as fancy autocomplete and started deliberately shaping how AI understands their work.

## What Context Engineering Means

The effectiveness of AI tools depends heavily on the context you provide.

A developer who opens Claude Code or Cursor and starts prompting is working with an AI that knows nothing about their codebase, conventions, or architecture. The AI will generate something plausible but likely does not fit how things are done in that specific project.

A developer who has written a `CLAUDE.md` file explaining the project structure, coding conventions, key abstractions, and common pitfalls is working with an AI that has been taught how to contribute effectively to that specific codebase.

The difference in output quality is significant.

But more importantly, the act of creating that context file reveals something about the developer. They have understood that AI collaboration requires preparation. They have moved from using AI to engineering the context that AI operates in.

That shift is what proficiency looks like. And the artifacts are measurable evidence that it has happened.

## The Files That Signal Proficiency

Different AI tools use different context files, but they all serve the same purpose: giving AI persistent knowledge about how to work in a specific codebase.

One important note: the context engineering landscape is changing constantly. New files, new conventions, new tools. What I list here reflects late 2025, but this shifts every few months. The specific files matter less than the underlying principle of deliberate context preparation.

**Agent instruction files:**
- `CLAUDE.md` or `AGENTS.md` for Claude Code
- `.github/copilot-instructions.md` for GitHub Copilot
- `.github/instructions/*.instructions.md` for scoped Copilot instructions
- `.github/agents/*.agent.md` for custom Copilot agents
- `.github/skills/*/SKILL.md` for GitHub Copilot project skills
- `~/.copilot/skills/*/SKILL.md` for GitHub Copilot personal skills
- `.cursorrules` or `.cursor/rules/` for Cursor
- `AGENTS.md` for OpenAI Codex CLI

**Specification and architecture files:**
- `spec.md` for project or feature specifications AI can reference
- `ARCHITECTURE.md` or `docs/architecture/` documenting system design
- Architecture Decision Records (ADRs) in `docs/adr/`
- `DESIGN.md` or `docs/design/` for design documents
- `docs/rfcs/` for Request for Comments
- `TECHNICAL_OVERVIEW.md` for high-level technical context
- `API.md` or `docs/api/` documenting API contracts
- `DATA_MODEL.md` or `docs/data/` explaining data structures
- `PATTERNS.md` documenting common patterns in the codebase
- `CONVENTIONS.md` or `STYLE.md` for coding standards
- `GLOSSARY.md` defining domain terms
- `DOMAIN.md` for domain-driven design context

**Skill and workflow files:**
- `SKILL.md` files following the [Agent Skills](https://agentskills.io/) open standard
- Project skills in `.claude/skills/`, `.github/skills/`, or `.codex/skills/` directories
- Personal skills in `~/.copilot/skills/`, `~/.claude/skills/`, or `~/.codex/skills/`
- `skills/` folder with domain-specific skills
- Custom workflow definitions
- `.claude/commands/` for custom slash commands
- `PROMPTS.md` or `.prompts/` folders with effective saved prompts
- `WORKFLOWS.md` documenting automated processes
- `COMMANDS.md` listing available commands

**Hooks and automation files:**
- `.claude/hooks/` folder with hook scripts
- `.claude/settings.json` for Claude Code configuration and hooks
- `.husky/` for Git hooks
- MCP server configurations (`mcp.json`, `.mcp/`, `mcp-config.json`)
- Custom tool integrations

**Memory and learning files:**
- `MEMORY.md` capturing persistent context
- `LEARNINGS.md` documenting what has been discovered
- `DECISIONS.md` tracking choices and rationale
- `.memory/` folders for structured memory storage
- `RETROSPECTIVES.md` capturing post-project learnings
- `KNOWN_ISSUES.md` documenting current limitations
- `TROUBLESHOOTING.md` with common problems and solutions
- `GOTCHAS.md` warning about non-obvious pitfalls
- `context.yaml` or `context.json` for structured context data

**Supporting context:**
- Well-structured `README.md` files that help AI understand the project
- `CONTRIBUTING.md` with context for working in the codebase
- `TESTING.md` with testing strategies and conventions
- `DEVELOPMENT.md` or `SETUP.md` for environment setup
- `DEBUGGING.md` with common debugging approaches
- `SECURITY.md` documenting security considerations
- `.context/` or `.ai/` folders organizing context by domain

When these files exist in a repository, someone has deliberately invested in making AI more effective there. When they do not exist, teams are likely still at the basic prompting stage.

## A Maturity Model

Based on what I have observed, here is how teams tend to progress. This 8-level model directly aligns with Steve Yegge's 8-stage behavioral model from "Welcome to Gas Town." It combines two dimensions: the behavioral progression (how developers interact with AI tools) and the infrastructural progression (what context engineering artifacts exist). Both matter.

Steve Yegge's 8 stages range from "maybe code completions" to "building your own orchestrator." The context engineering artifacts I describe here are the infrastructure that makes progression through those behavioral stages effective. You can be at Stage 6 behaviorally (running multiple parallel agents) with zero context files, but you will be far less effective than someone at the same stage with comprehensive context engineering in place.

**Level 1: Zero or Near-Zero AI (Yegge Stage 1)**

No AI-specific files in the repository. Developers use AI tools for code completions and occasionally ask questions in chat. AI is treated as a slightly smarter search engine or autocomplete. This is where most teams currently are.

Behavioral indicators:
- Using Copilot completions or ChatGPT for questions
- Copy-pasting code snippets from chat
- AI has no awareness of project conventions

**Level 2: Basic Instructions (Yegge Stage 2)**

Developers have started using coding agents (Claude Code, Cursor agent mode, Copilot chat) but with limited project context. Basic instruction files exist. The AI has surface-level awareness of the project. Agents typically run with permissions enabled.

Files at this level:
- `CLAUDE.md` or `AGENTS.md` with a paragraph or two about the project
- `.cursorrules` with basic coding style preferences
- `.github/copilot-instructions.md` with simple guidelines
- A decent `README.md` that explains what the project does

Behavioral indicators:
- Running agents with permissions enabled (approve each action)
- Agents work on small, well-defined tasks
- Frequent corrections needed for project conventions

**Level 3: Comprehensive Context (Yegge Stage 3)**

Comprehensive instruction files covering architecture, conventions, patterns, and anti-patterns. Developers trust the agent enough to reduce permission prompts. AI becomes a genuinely useful collaborator that understands how things work.

*Agent instruction files:*
- Detailed `CLAUDE.md` with architecture overview, key abstractions, and things to avoid
- `.github/copilot-instructions.md` for repository-level Copilot configuration
- `.github/instructions/` folder with scoped `*.instructions.md` files
- `.cursorrules` or `.cursor/rules/` with comprehensive guidance
- `AGENTS.md` for Codex CLI with detailed project context

*Architecture and specification files:*
- `ARCHITECTURE.md` or `docs/architecture/` explaining system design
- `spec.md` files for features or components
- Architecture Decision Records (ADRs) in `docs/adr/` or `docs/architecture/decisions/`
- `DESIGN.md` or `docs/design/` for design documents
- `docs/rfcs/` for Request for Comments on significant changes
- `TECHNICAL_OVERVIEW.md` for high-level technical context
- `API.md` or `docs/api/` documenting API contracts
- `DATA_MODEL.md` or `docs/data/` explaining data structures and relationships
- `SECURITY.md` documenting security considerations and requirements
- `GLOSSARY.md` defining domain terms (especially valuable for AI understanding)
- `DOMAIN.md` for domain-driven design context and bounded contexts

*Conventions and standards files:*
- `CONVENTIONS.md` or `STYLE.md` documenting coding standards
- `CONTRIBUTING.md` with context for how to work in the codebase
- `PATTERNS.md` documenting common patterns used in the project
- `ANTI_PATTERNS.md` documenting what to avoid and why
- `CODE_REVIEW.md` with review criteria and expectations
- `NAMING.md` for naming conventions across the codebase

*Development context files:*
- `DEVELOPMENT.md` or `SETUP.md` for development environment setup
- `TESTING.md` with testing strategies, conventions, and examples
- `DEBUGGING.md` with common debugging approaches and tools
- `PERFORMANCE.md` documenting performance considerations and benchmarks
- `DEPLOYMENT.md` explaining deployment processes
- `INFRASTRUCTURE.md` documenting infrastructure dependencies
- `DEPENDENCIES.md` explaining key dependencies and why they were chosen
- `MIGRATION.md` for database or breaking change migrations
- `docs/runbooks/` for operational procedures
- `docs/guides/` for how-to documentation
- `examples/` folder with well-documented example code

Behavioral indicators:
- Running agents in "YOLO mode" (auto-approve most actions)
- Agent fills more of the screen; code editor is primarily for reviewing diffs
- Agents handle larger, more complex tasks with fewer corrections
- Trust has been earned through consistent, convention-following output

**Level 4: Skills & Automation (Yegge Stage 4)**

Beyond instructions, the team has created skill files, memory systems, hooks, and workflow definitions. AI can execute complex tasks correctly, enforce quality gates automatically, and maintain context across sessions.

*Skill files:*
- `SKILL.md` files following the [Agent Skills](https://agentskills.io/) open standard
- Project skills in `.claude/skills/`, `.github/skills/`, or `.codex/skills/` directories
- Domain-specific skills (`skills/testing/SKILL.md`, `skills/deployment/SKILL.md`)
- Personal skills in `~/.copilot/skills/`, `~/.claude/skills/`, or `~/.codex/skills/` (shared across projects)
- `CAPABILITIES.md` documenting what the AI can do in this repo

*Workflow and automation files:*
- Custom workflow definitions for deployment, testing, documentation
- `WORKFLOWS.md` documenting automated processes
- `COMMANDS.md` listing available commands and their purposes
- `.claude/commands/` for custom Claude Code slash commands
- `Makefile` or `justfile` with well-documented targets
- `scripts/` folder with documented automation scripts
- `.husky/` hooks with context for AI understanding

*Memory and learning files:*
- `MEMORY.md` capturing persistent context
- `LEARNINGS.md` documenting what has been discovered
- `DECISIONS.md` tracking architectural choices and their rationale
- `.memory/` folders for structured memory storage
- `RETROSPECTIVES.md` capturing post-project learnings
- `KNOWN_ISSUES.md` documenting current limitations and workarounds
- `TROUBLESHOOTING.md` with common problems and solutions
- `FAQ.md` answering frequent questions about the codebase
- `GOTCHAS.md` warning about non-obvious pitfalls
- `CHANGELOG.md` maintained to help AI understand project evolution
- `HISTORY.md` for longer-term historical context
- `context.yaml` or `context.json` for structured context data

*Agent configuration files:*
- Custom Copilot agents in `.github/agents/*.agent.md`
- `.context/` or `.ai/` folders organizing context by domain
- `PROMPTS.md` or `.prompts/` with saved effective prompts
- `personas/` folder with different AI interaction styles for different tasks

*Hooks and automation:*
- `.claude/hooks/` folder with hook scripts (formatters, validators, notifications)
- `.claude/settings.json` for project-level hook configuration
- `PreToolUse` hooks for validation and blocking risky operations
- `PostToolUse` hooks for automatic formatting and quality checks
- `Stop` hooks for end-of-turn quality gates
- Git hooks integrated with AI workflows
- MCP server configurations for tool integrations

Behavioral indicators:
- Primarily working from CLI (Claude Code, Codex CLI)
- Agent fills more of the screen; wide agent view
- Diffs scroll by; review is selective rather than comprehensive
- Hooks enforce quality automatically; less manual review needed
- Full trust in single agent instance

**Level 5: Multi-Agent Ready (Yegge Stage 5)**

Multiple agents with different roles and responsibilities configured. MCP integrations enable tool usage. Basic orchestration patterns and handoff documentation.

*Multi-agent configuration:*
- `.github/agents/` folder with role-specific `.agent.md` files
- `.github/agents/reviewer.agent.md` - code review specialist agent
- `.github/agents/tester.agent.md` - testing and QA agent
- `.github/agents/documenter.agent.md` - documentation agent
- `.github/agents/security.agent.md` - security review agent
- `.github/agents/architect.agent.md` - architecture decision agent
- `roles/` folder for role-based configurations
- Agent handoff protocols in `agents/HANDOFFS.md`
- `agents/ORCHESTRATION.md` explaining how agents coordinate

*Tool and integration configurations:*
- MCP server configurations (`mcp.json`, `.mcp/`, `mcp-config.json`)
- `.mcp/servers/` for multiple MCP server definitions
- `.claude/settings.json` with MCP and tool configurations
- Custom tool definitions in `tools/` folder
- `tools/TOOLS.md` documenting available custom tools

Behavioral indicators:
- Running 3-5 parallel agent instances regularly
- Work queued up ahead of time; agents execute while you plan
- Significant productivity increase from parallelism
- Manual management via tmux or similar tools

**Level 6: Fleet Infrastructure (Yegge Stage 6)**

Advanced memory systems, shared context across packages, and workflow pipeline definitions. Infrastructure for managing parallel agent instances at scale.

*Memory and persistence systems:*
- `.beads/` for Beads memory system (persistent external memory)
- `memory/global/` for shared learnings within monorepo
- `memory/project/` for project-specific context
- Persistent agent state in `.agent_state/`

*Shared context (within repo):*
- Monorepo-aware context in `packages/*/CLAUDE.md`, `services/*/CLAUDE.md`
- `SHARED_CONTEXT.md` documenting shared context across packages

*Workflow pipelines:*
- `workflows/` folder with YAML workflow definitions
- `pipelines/` folder for multi-step processes
- `workflows/code_review.yaml` - full review pipeline
- `workflows/feature_development.yaml` - feature delivery pipeline
- `workflows/incident_response.yaml` - debugging and fix pipeline

*Fleet configuration:*
- `FLEET.md` documenting fleet setup and configuration
- `.fleet/` folder for fleet management configs

Behavioral indicators:
- You are very fast - marked jump in output velocity
- Capability to context-switch between agents quickly
- Asynchronous agent execution; continuous output stream
- Human may or may not review all changes

**Level 7: Agent Fleet (Yegge Stage 7)**

Large agent fleet with governance, scheduling, and multi-agent pipelines. Managing 10+ agents with structured work decomposition.

*Governance and policies:*
- `GOVERNANCE.md` documenting agent permissions and boundaries
- `agents/PERMISSIONS.md` defining what agents can do
- `AGENT_POLICIES.md` for compliance and security rules

*Fleet-scale agent management:*
- `agents/specialists/` for specialized agent definitions
- `agents/roles/` for role-based configurations
- `agents/SCHEDULING.md` for priority and scheduling rules
- `agents/PRIORITY.md` for work prioritization
- `.queue/` or `queue/` for agent work queues

*Work decomposition (Gas Town style):*
- `convoys/` folder for coordinated agent groups
- `molecules/` folder for atomic work units
- `epics/` folder for large task decomposition

*Multi-agent pipelines:*
- `pipelines/multi_agent/` for complex workflows
- `workflows/release_pipeline.yaml`
- `workflows/security_audit.yaml`
- `workflows/deployment.yaml`

*Agent metrics:*
- `agents/METRICS.md` tracking agent performance
- `.metrics/agents/` for performance data

Behavioral indicators:
- Running 10+ agents simultaneously
- Approaching limits of manual management
- Requires tooling to manage coordination
- Inter-agent communication and mail systems
- Work queued in structured plans (molecules, epics, convoys)

**Level 8: Custom Orchestration (Yegge Stage 8)**

Building custom orchestration frameworks and meta-automation. This is the frontier - automating agent workflows programmatically.

*Custom orchestration:*
- `orchestration.yaml` or `orchestration/` folder
- `ORCHESTRATOR.md` documenting orchestration architecture
- `orchestration/ARCHITECTURE.md` for orchestrator design

*Gas Town / custom orchestrators:*
- `.gastown/` configuration for Steve Yegge's orchestrator
- `gastown.config.yaml` or `gastown.config.json`

*Meta-automation:*
- `meta/` folder for automation that generates automation
- `generators/` for code and config generators
- `AUTO_GENERATE.md` documenting auto-generation

*Agent composition:*
- `agents/COMPOSITION.md` for agent composition patterns
- `agents/TEMPLATES.md` for agent templates
- `agent_templates/` folder for reusable agent definitions

*Frontier tooling:*
- `.frontier/` or `experimental/` for cutting-edge experiments
- `EXPERIMENTAL.md` documenting frontier techniques

*Custom tools and SDK:*
- `tools/custom/` for custom tool definitions
- `tools/REGISTRY.md` for tool registry
- `agent_sdk/` or `agent_framework/` for custom frameworks
- `protocols/` for custom communication protocols

*Infrastructure as code:*
- `infra/agents/` for agent infrastructure
- `k8s/agents/` for Kubernetes-based agent deployment

Behavioral indicators:
- Building custom orchestration to manage agent workflows
- Automating agent workflows programmatically
- Creating specialized agent coordination logic
- Pushing coding agents "as hard as anyone on the planet"
- Human role shifts from coding to planning, reviewing, and unblocking agents
- Throughput measured in PRs per hour rather than lines of code

Most teams I encounter are at Level 1 or 2. The gap between that and Level 3+ is where the real productivity differences emerge. Levels 6-8 represent the frontier - very few teams have reached these levels yet.

## How to Measure This

If you want to assess your organization's AI proficiency, here is a practical approach:

**Scan your active repositories.** Identify repositories with commits in the last 90 days. These are your active codebases where AI proficiency matters.

**Check for context files.** For each repository, look for:
- Agent instruction files (`CLAUDE.md`, `AGENTS.md`, `.github/copilot-instructions.md`, `.cursorrules`, `.github/agents/*.agent.md`)
- Architecture and specification files (`ARCHITECTURE.md`, `spec.md`, ADRs, `PATTERNS.md`, `DESIGN.md`, `API.md`, `DATA_MODEL.md`)
- Conventions files (`CONVENTIONS.md`, `STYLE.md`, `ANTI_PATTERNS.md`, `NAMING.md`, `CODE_REVIEW.md`)
- Skill files (`.claude/skills/*/SKILL.md`, `.github/skills/*/SKILL.md`, `.codex/skills/*/SKILL.md`, `skills/`, `WORKFLOWS.md`, `.claude/commands/`)
- Hooks and automation (`.claude/hooks/`, `.claude/settings.json`, `mcp.json`, `.mcp/`)
- Memory files (`MEMORY.md`, `LEARNINGS.md`, `.memory/`, `DECISIONS.md`, `RETROSPECTIVES.md`)
- Supporting context (`TESTING.md`, `DEBUGGING.md`, `GLOSSARY.md`, `.context/` folders)

This can be automated with a simple script that scans for these patterns.

The specific files to check will evolve as tools change. Build your scanning to be adaptable, or update your checklist as the landscape shifts.

**Calculate coverage.** What percentage of active repositories have context engineering artifacts? This gives you a baseline.

**Assess quality.** For repositories that have context files, how detailed are they? When were they last updated? Stale files that no longer reflect the codebase are almost as problematic as no files at all.

**Track over time.** Run this assessment quarterly. Are more repositories getting context files? Is quality improving? This tells you whether AI proficiency is actually growing across your organization.

## A Tool to Get Started

I have built a CLI tool that automates this measurement: [measure-ai-proficiency](https://github.com/pskoett/measuring-ai-proficiency).

```bash
# Install
pip install measure-ai-proficiency

# Scan a single repository
measure-ai-proficiency /path/to/repo

# Scan all repos in your organization
measure-ai-proficiency --org /path/to/cloned-repos

# Get JSON output for tracking over time
measure-ai-proficiency --org /path/to/repos --format json --output q1-2025.json
```

The tool scans for the file patterns described in this article and calculates a maturity level (0-4) for each repository. It generates recommendations for what to add next.

**Important: You will need to customize this for your team.**

The tool ships with patterns for the big four AI coding tools: Claude Code, GitHub Copilot, Cursor, and OpenAI Codex CLI. But your team might use different tools, or have established different conventions.

To adapt it:

1. **Fork the repository** and edit `config.py`
2. **Add patterns for your tools.** If your team uses Aider, Cody, Continue, or other AI tools, add their context file patterns to the appropriate level
3. **Remove patterns you do not use.** If nobody on your team uses Cursor, remove `.cursorrules` from your fork so it does not skew coverage percentages
4. **Add your own conventions.** If your team has standardized on `AI_CONTEXT.md` instead of `CLAUDE.md`, add that pattern
5. **Adjust thresholds.** The default requires 20% coverage for Level 2, 15% for Level 3, 10% for Level 4. Tune these based on what makes sense for your organization

The tool is meant as a starting point, not a universal standard. Context engineering practices vary across teams and tools. The value is in measuring your team's specific practices consistently over time, not in comparing yourself to some external benchmark.

Example customization for a team using Aider and their own conventions:

```python
# In config.py, add to LEVEL_1_PATTERNS.file_patterns:
".aider.conf.yml",
"AI_CONTEXT.md",
".aider/conventions.md",

# Add to CORE_AI_FILES:
".aider.conf.yml",
"AI_CONTEXT.md",
```

Run your customized version quarterly. Track the trend. That is the metric that matters.

## An Agent Skill for Continuous Improvement

Beyond the CLI tool, I have created an agent skill that you can add to any repository. This skill lets AI coding assistants assess and improve context engineering directly within your workflow.

### What the Skill Does

When you add this skill to your repository, Claude Code, GitHub Copilot, and other skill-aware AI tools can:

1. **Automatically assess** your repository's context engineering maturity when you ask about AI readiness
2. **Provide actionable recommendations** for what files to add next
3. **Create starter content** for missing context files
4. **Explain the maturity model** and what each level means for your workflow

### Installing the Skill

Agent Skills follow an [open standard](https://agentskills.io/) and work with Claude Code, GitHub Copilot, and OpenAI Codex. Copy the skill to your repository:

**For Claude Code:**
```bash
# Create the skills directory
mkdir -p .claude/skills/measure-ai-proficiency

# Copy the skill file
curl -o .claude/skills/measure-ai-proficiency/SKILL.md \
  https://raw.githubusercontent.com/pskoett/measuring-ai-proficiency/main/skill-template/measure-ai-proficiency/SKILL.md
```

**For GitHub Copilot:**
```bash
# Create the skills directory
mkdir -p .github/skills/measure-ai-proficiency

# Copy the skill file
curl -o .github/skills/measure-ai-proficiency/SKILL.md \
  https://raw.githubusercontent.com/pskoett/measuring-ai-proficiency/main/skill-template/measure-ai-proficiency/SKILL.md
```

**For OpenAI Codex:**
```bash
# Create the skills directory
mkdir -p .codex/skills/measure-ai-proficiency

# Copy the skill file
curl -o .codex/skills/measure-ai-proficiency/SKILL.md \
  https://raw.githubusercontent.com/pskoett/measuring-ai-proficiency/main/skill-template/measure-ai-proficiency/SKILL.md
```

Or manually create the `SKILL.md` file in either location with the content from the [skill-template](https://github.com/pskoett/measuring-ai-proficiency/tree/main/skill-template/measure-ai-proficiency) directory.

### Using the Skill

Once installed, simply ask your AI assistant:

- "Assess my repository's AI proficiency"
- "How can I improve my context engineering?"
- "What level is my AI maturity?"
- "Help me create better context for AI coding"

Claude Code, GitHub Copilot, OpenAI Codex, and other skill-aware tools will automatically use the skill to scan your repository, explain your current level, and offer to create any missing context files.

### Why a Skill Matters

Skills represent Level 3 maturity in the context engineering model. By adding this skill to your repository, you are:

1. **Practicing what you measure**: Using skills to improve your use of skills
2. **Making improvement automatic**: The AI can proactively suggest improvements
3. **Building team awareness**: Everyone with access to the repo can assess and improve context engineering
4. **Creating a feedback loop**: Regular assessment leads to continuous improvement

The skill itself is an example of context engineering. It teaches AI how to help you get better at AI collaboration.

## Automating Assessment with GitHub Actions

For teams that want to track AI proficiency continuously, I have created GitHub Action workflows that integrate with your CI/CD pipeline.

### What the GitHub Action Does

The action provides two workflows:

1. **PR Assessment**: Automatically comments on pull requests with the repository's current proficiency level, highlights any context engineering files being added, and provides recommendations.

2. **Weekly Reports**: Creates a GitHub issue every Monday tracking progress over time, comparing to previous weeks, and suggesting next improvements.

### Two Implementation Options

**Option 1: GitHub Agentic Workflows**

Uses [GitHub's Agentic Workflows](https://githubnext.com/projects/agentic-workflows/), a natural language approach powered by GitHub Copilot:

```bash
gh extension install githubnext/gh-aw
gh aw add pskoett/measuring-ai-proficiency/.github/workflows/ai-proficiency-pr-review --create-pull-request
gh aw add pskoett/measuring-ai-proficiency/.github/workflows/ai-proficiency-weekly-report --create-pull-request
```

**Option 2: Claude Code Action**

For teams using the Anthropic API, the [Claude Code Action](https://github.com/anthropics/claude-code-action) provides deeper AI-powered analysis:

```bash
# In Claude Code terminal
/install-github-app
```

Then add the workflow file from the repository.

### Why Automate This

Automation serves several purposes:

1. **Visibility**: Every PR shows the team's context engineering status
2. **Accountability**: Weekly reports create natural checkpoints
3. **Gamification**: Watching the level increase motivates continued improvement
4. **Onboarding**: New team members immediately see what context files exist and what to add

The goal is not to gate PRs on proficiency level. The goal is to make the invisible visible. When everyone can see the current state and the path forward, improvement happens naturally.

## What This Metric Reveals

A team with context engineering artifacts in most of their repositories has made a deliberate investment in AI collaboration. They are not just using AI tools. They are integrating AI into how they work.

A team with no context files, even if they report high AI tool usage, is likely stuck at the autocomplete stage. They are getting some value, but nowhere near what is possible.

This metric is also a leading indicator. The presence of context engineering artifacts predicts future productivity gains. A team that has just started writing `CLAUDE.md` files is about to become more effective, even if the impact has not appeared in throughput metrics yet.

Compare this to tracking AI usage rates, which is a lagging indicator that tells you what has already happened but not whether it is working.

## Limitations

I want to be clear about what this metric does not capture.

It does not measure individual proficiency. A team might have excellent context files written by one person while everyone else ignores them.

It does not measure prompt quality. Good context files combined with poor prompts still produce mediocre results.

It does not capture all forms of AI proficiency. Some developers are highly effective without context files, particularly on smaller projects.

And presence does not equal quality. A `CLAUDE.md` file with two sentences is very different from one with comprehensive documentation.

But as a signal for organizational AI maturity, I believe it is more meaningful than what most companies currently track.

## The Landscape Keeps Changing

The context engineering landscape is not stable.

Six months ago, most of these file conventions did not exist. Six months from now, there will likely be new ones. Tools are evolving rapidly. Best practices are still being established.

This is not a reason to avoid context engineering. It is a reason to treat it as a practice rather than a checklist. The specific files matter less than the habit of deliberately preparing context for AI collaboration.

Teams that build this capability will adapt as tools change. Teams that never start will continue falling behind regardless of what the current best practice happens to be.

Measure what exists now, but expect to update your criteria. The principle remains constant even as the implementation evolves.

## Getting Started

If you want to improve AI proficiency in your organization, start by making context engineering visible.

Create a template for `CLAUDE.md` or whatever context file matches your tooling. Show people what effective context looks like.

Add context file creation to your repository setup process. Make it part of how new projects begin.

Share examples of effective context files across teams. Let people see what others are doing.

Measure and report on coverage. What gets measured gets attention.

The goal is not to mandate context files. The goal is to make it easy and visible, so developers who are ready to improve have a clear path forward.

## The Bottom Line

Adoption metrics tell you who is using AI tools. Context engineering metrics tell you who understands how to use them effectively.

If you want to know where your organization actually stands on AI proficiency, look at your repositories. Count the context files. Assess their quality. Track the trend over time.

That will tell you more than any usage dashboard.