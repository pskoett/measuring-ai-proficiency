# Measuring AI Proficiency: Context Engineering as a Leading Indicator

If you work in developer experience and platform engineering like me, you have probably been asked some version of this question: "How are we doing with AI?"

It is a reasonable question. Organizations are investing in AI tooling. Leadership wants to know if it is working. But what does "doing well with AI" actually mean? And how would you measure it?

Most teams and tools that measure AI impact reach for adoption metrics. Copilot seats activated. Completions accepted. Chat sessions per week. These are the numbers you can get from GitHub, Anthropic, and others. They are easy to collect and easy to report.

They are also nearly useless for measuring proficiency.

A developer who accepts 200 completions per day might be saving hours. Or they might be accepting low-quality code that creates technical debt. A developer who rarely uses completions might be prompting agents to refactor entire modules. The adoption number does not distinguish between these. High adoption can coexist with zero proficiency.

The question is not how many people are using AI. The question is who is using it the right way, and how do you find them. The gap between adoption and proficiency is where organizations are losing value.

## What Context Engineering Is

Before you can measure AI proficiency, you need to define what it means for your team. This is not something you can copy from a blog post. The tools your team uses, the conventions you have established, the workflows that matter to your codebase: these are specific to you.

The definition should not come from the top down. It should come from the people who are already doing it well. Find them first, then build the definition together.

But there is a common pattern across all effective AI usage: context engineering.

Context engineering is the practice of deliberately preparing information that helps AI understand your specific codebase, conventions, and constraints. It shows up as files in your repositories: instruction files, architecture documentation, pattern guides, skill definitions, memory files.

A developer who opens Claude Code or Cursor and starts prompting is working with an AI that knows nothing about their codebase. The AI will generate something plausible but likely does not fit how things are done in that specific project. A developer who has written a `CLAUDE.md` file explaining the project structure, coding conventions, and common pitfalls is working with an AI that has been taught how to contribute effectively.

The act of creating that context file reveals something about the developer. They have understood that AI collaboration requires preparation. They have moved from using AI to engineering the context that AI operates in. That shift is what proficiency looks like. And the artifacts are measurable evidence that it has happened.

## Context Engineering in Practice

The best way to understand context engineering is to look at repositories that do it well.

Boris Cherny, who created Claude Code, recently [shared his workflow](https://x.com/bcherny/status/2007179832300581177).

He runs 5 Claude instances in parallel in his terminal (numbered tabs 1-5 with system notifications), plus 5-10 more on claude.ai/code, using `--teleport` to hand off sessions between local and web. He starts sessions from his phone each morning and checks in on them later. The Claude Code team maintains a shared `CLAUDE.md` checked into git. Everyone contributes to it multiple times per week. When Claude does something wrong, they add it to `CLAUDE.md` so it does not happen again. During code review, they tag `@.claude` on PRs to update the file as part of the review process.

His `.claude/` directory shows the full stack: slash commands in `.claude/commands/` for inner loop workflows like `/commit-push-pr` (used dozens of times daily), subagents in `.claude/agents/` (`code-simplifier`, `verify-app`, `build-validator`, `code-architect`, `oncall-guide`), PostToolUse hooks for auto-formatting, and shared permissions in `.claude/settings.json`. His `.mcp.json` connects Claude to Slack, BigQuery for analytics, and Sentry for error logs.

His key insight: "Give Claude a way to verify its work. If Claude has that feedback loop, it will 2-3x the quality of the final result." For changes to claude.ai/code, Claude uses the Chrome extension to open a browser, test the UI, and iterate until the code works and the UX feels good.

This is compound engineering: every correction becomes permanent context, and the cost of a mistake pays dividends forever.

Other projects show different patterns. [Clawdbot](https://github.com/clawdbot/clawdbot) splits context across `AGENTS.md`, `SOUL.md`, and `TOOLS.md` with a full skills system. Cole Medin's [context-engineering-intro](https://github.com/coleam00/context-engineering-intro) uses PRPs (Product Requirements Prompts) as AI-specific alternatives to PRDs.

At the frontier, Steve Yegge's [Gas Town](https://github.com/steveyegge/gastown) shows what multi-agent orchestration looks like. Multiple agents with specialized roles work in parallel. Work state persists across sessions and crashes. Structured workflows define how tasks get broken down and handed off. This is infrastructure for running 20-30 agents simultaneously. Most teams will not need this, but it shows where the ceiling is.

The specific structure matters less than the principle: these teams or individuals have thought deliberately about what their AI assistant needs to know. They have documented architecture, conventions, patterns, and anti-patterns. They have created workflows that make the AI more effective over time.

Different AI tools use different context files, but they serve the same purpose:

- **Claude Code**: `CLAUDE.md`, `AGENTS.md`, `.claude/commands/`, `.claude/hooks/`
- **GitHub Copilot**: `.github/copilot-instructions.md`, `.github/instructions/`, `.github/agents/`
- **Cursor**: `.cursorrules`, `.cursor/rules/`
- **OpenAI Codex CLI**: `AGENTS.md`

Beyond tool-specific files, mature teams create supporting context: `ARCHITECTURE.md`, `PATTERNS.md`, `CONVENTIONS.md`, ADRs, `SKILL.md` files following the [Agent Skills](https://agentskills.io/) open standard, memory files like `LEARNINGS.md`, or hook scripts that enforce quality automatically.

**The specific files will be different for your organization.** If your team uses Aider, Cody, or Continue, you will have different patterns. The point is not to adopt someone else's checklist. The point is to define what context engineering looks like for you, then measure whether it is happening.

## The Progression

When you scan repositories, you will see patterns at different stages of sophistication. Steve Yegge describes this progression well in "[Welcome to Gas Town](https://steve-yegge.medium.com/welcome-to-gas-town-4f25ee16dd04)."

Most teams start with nothing. No AI-specific files. Developers use completions and occasionally ask questions in chat. AI is fancy autocomplete.

The first shift happens when someone writes a `CLAUDE.md` or `.cursorrules` with basic instructions. A paragraph or two about coding style. This is where teams start to see that context matters.

The real productivity jump comes when context files become comprehensive. Architecture, conventions, patterns, anti-patterns. Developers trust the agent enough to let it run. AI becomes a collaborator that understands how things work in this specific codebase.

Beyond that, you see automation: hooks that enforce quality, slash commands for repeated workflows, subagents for specific tasks, MCP integrations connecting AI to other tools. Some teams go further into multi-agent coordination, but that is the frontier where very few have arrived.

The tool I built uses maturity stages to categorize these patterns, but the stages are not the point. The point is recognizing where teams are so you can find the ones who are ahead. A team with comprehensive context files and hooks has figured something out. Go talk to them.

## Context Engineering as a Leading Indicator

This is why context engineering matters for measurement: it is a leading indicator.

Adoption metrics are lagging indicators. They tell you what has already happened. By the time you see the numbers, the behavior is in the past. If adoption is low, you have already lost months. If adoption is high but unproductive, the damage is done.

Context engineering artifacts predict future productivity gains. A team that has just started writing `CLAUDE.md` files is about to become more effective, even if the impact has not appeared in throughput metrics yet. You can see the investment happening before the returns arrive.

## What to Measure and Who to Find

Leadership wants dashboards. The point is not to replace adoption metrics. The point is to add this measurement so you know if the adoption is actually working. High Copilot usage plus zero context engineering means you have adoption without proficiency. High Copilot usage plus growing context engineering means the investment is paying off.

Context engineering metrics answer the question that adoption metrics cannot: are people getting better at this, or just using it more?

If you are responsible for developer experience or engineering effectiveness, here is what I would track:

**Distribution**: Which teams are at which stage of maturity? Where are the pockets of sophistication? Who has figured this out? This is the most valuable output of the entire exercise. You are not measuring for a dashboard. You are measuring to find the people who have reached proficiency, and who can help others get there.

**Coverage**: What percentage of active repositories have context engineering artifacts? Scan repositories with commits in the last 90 days and at least one of the common instruction files: `CLAUDE.md`, `AGENTS.md`, `.cursorrules`, `.github/copilot-instructions.md`. This gives you a baseline.

**Quality**: For repositories that have context files, how detailed are they? A `CLAUDE.md` with two sentences is very different from one with architecture documentation and anti-patterns. Consider file size, last updated date, and whether the content reflects current codebase state.

**Trend**: Run this assessment quarterly. Are more repositories getting context files? Is quality improving? The trend tells you whether AI proficiency is actually growing across your organization.

When you report to leadership, you can show both. Adoption is X. Proficiency, measured by context engineering artifacts, is Y. The distance between X and Y is where the work needs to happen. And here are the people who have already reached proficiency, who can help get everyone else there.

## Working With Your Early Adopters

When you scan your repositories for context engineering artifacts, you are not just getting a score. You are identifying people.

The developers who have already written comprehensive `CLAUDE.md` files, who have set up hooks and custom commands, who have documented their patterns for AI consumption: these are your early adopters. They figured this out on their own. They are already getting value that others are not.

These people are gold for a developer experience team.

They can tell you what they do. You can tell them what you know. Together you can collaborate to spread practices across the organization. The productivity gains from context engineering compound in ways that traditional tooling improvements do not.

But there is something more important than spreading existing practices. These early adopters can help you define what good context engineering looks like for your organization. The patterns in this article are starting points, not answers. Your codebase, your tools, your conventions will require their own definition of maturity. The people who are already ahead are the ones who can help you build that definition.

If you are trying to accelerate AI proficiency across an organization, you do not start by training everyone. You start by finding the people who are already proficient, learning from them, and working with them to define and spread what works.

## A Tool to Get Started

I built a CLI tool that automates this scanning: [measure-ai-proficiency](https://github.com/pskoett/measuring-ai-proficiency). It scans repositories for file patterns, calculates maturity stages, and generates recommendations for what to add next based on what is already there. If a repository has a `CLAUDE.md` but no `ARCHITECTURE.md`, it will suggest that. If a team is at an early stage, it tells them what the next stage looks like.

**You will need to customize it.** The tool ships with patterns for Claude Code, GitHub Copilot, Cursor, and OpenAI Codex. Add patterns for the tools your team actually uses. Remove patterns for tools you do not. Adjust the thresholds based on what makes sense for your organization. The repository includes detailed instructions for customization.

The tool is a starting point for building your own measurement practice, not a universal standard.

Once you find your early adopters and start spreading practices, keep measuring. Run the scan quarterly. Track whether teams are progressing through maturity stages. The tool is not just for finding who is ahead. It is for seeing whether everyone else is catching up.

## Limitations

I want to be clear about what this metric does not capture.

It does not measure individual proficiency. A team might have excellent context files written by one person while everyone else ignores them.

It does not capture all forms of AI proficiency. Some developers are highly effective without context files, particularly on smaller projects.

And presence does not equal quality. This is why quality assessment matters alongside coverage.

But as a signal for organizational AI proficiency maturity, I believe it is more meaningful than what most organizations currently track.

## Measuring What Matters

The next time someone asks "how are we doing with AI?", you will have an answer that actually means something. Not seats activated. Not completions accepted. Who has figured this out, and is the rest of the organization learning from them.

---

*A CLI tool, agent skill, and GitHub Actions for measuring context engineering are available at [github.com/pskoett/measuring-ai-proficiency](https://github.com/pskoett/measuring-ai-proficiency). Fork it and customize for your team's tools and conventions.*
