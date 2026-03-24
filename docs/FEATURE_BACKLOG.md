# Feature Backlog

Advanced metrics and architectural patterns for future development of measure-ai-proficiency.

These ideas represent the frontier of context engineering measurement—moving beyond artifact detection toward understanding the **integrity of feedback loops** between AI architects and agents.

> *If traditional metrics are like counting how many bricks a worker lays per day, context engineering is reviewing the blueprints, site rules, and automated safety gear the architect has provided.*

---

## 1. Advanced Quantitative Constructs (CMI)

While the current tool measures "Freshness" and "Quality," these academic and theoretical primitives could provide deeper insights into context health:

### Contextual Entropy

Measures the rate at which memory coherence deteriorates in distributed systems, leading to unrecoverable decision rationale.

**Implementation idea:** Measure the **semantic divergence** or "fragmentation" between a root context file and its nested directory-specific counterparts.

### Insight Drift

Tracks the semantic misalignment between an original rationale (why a decision was made) and its later interpretations.

**Implementation idea:** Using vector-space similarity scores, detect if the instructions in `MEMORIES.md` or `LEARNINGS.md` are drifting away from the actual architectural patterns present in the code.

### Resonance Intelligence

Assesses a system's ability to detect misalignment between current reasoning and relevant historical context.

**Implementation idea:** A "Consistency Score" that verifies if new `SKILL.md` definitions resonate with established project standards.

---

## 2. Deeper Technical Automation Hooks

The tool tracks "Hooks" at Level 4, but could broaden detection to specific types of automated feedback loops:

### Post-Action Tool Validation

Mature context engineering uses **PostToolUse hooks** to automatically trigger deterministic tools like linters or formatters immediately after an agent edits a file.

**Detection:** Look for hook configurations that chain tool invocations.

### Stop Hooks and Human-in-the-Loop (HITL)

Proficiency is also indicated by the presence of "Stop" hooks that mandate human approval for sensitive actions, such as modifying authentication logic or deleting production databases.

**Detection:** Scan for approval gates and restricted action patterns.

### Slash Command Depth

Beyond just checking for the `.claude/commands/` directory, analyze the complexity of the commands.

**Detection:** High proficiency is marked by commands that encapsulate **multi-step reasoning**, such as a `/fix-github-issue` command that chains research, implementation, and testing.

---

## 3. Architectural Patterns: Progressive Disclosure

Effective context engineering is about "stuffing smarter, not just stuffing more" to manage a model's finite attention budget.

### Hierarchy and Locality

Measure the **depth of nested context files**. A single 1,000-line root file is often less effective than a lean root file that uses **Progressive Disclosure** to point to directory-specific instructions only when they become relevant.

**Metrics:**
- Root file line count vs. distributed file count
- Cross-reference graph depth
- Locality score (how close context is to relevant code)

### Prompt Altitude

Proficiency is found in the "Goldilocks zone" between brittle hardcoded logic and vague high-level guidance.

**Detection:** Scan for **heuristics and architectural principles** (the "Why") rather than just lists of bash commands (the "How").

---

## 4. Security and Least Privilege Governance

As teams reach Level 5+, the risk of "context sprawl" and secret leakage increases.

### AI-Specific Ignore Files

The presence of AI-targeted ignore files is a strong indicator of mature security governance. These prevent agents from indexing sensitive configuration files or legacy modules that should remain untouched.

**Files to detect:**
- `.codeiumignore`
- `.aider.ignore`
- `.cursorignore`
- `.github/copilot-ignore` (proposed)

### Least Privilege Artifacts

Scan for evidence of **scoped environment variables** or instructions that explicitly forbid an agent from accessing high-impact directories.

**Detection:** Look for deny lists, restricted paths, and permission boundaries in context files.

---

## 5. Spec-Driven Development (SDD) Evidence

Moving beyond vibe coding requires a "Plan-then-Execute" workflow.

### Interim Planning Files

Look for persistent checklist files that are actively updated by the agent. These serve as shared working states that survive session crashes.

**Files to detect:**
- `plan.md`
- `todo.md`
- `architecture.md`
- `.claude/plans/`
- `.github/plans/`

### Evaluation-Driven Artifacts

High-maturity teams create "Judge" prompts or **G-Eval steps** to have one agent programmatically verify the performance of another.

**Detection:** Look for evaluation prompts, scoring rubrics, and automated quality gates.

---

## Summary: Proficiency Indicators to Add

| Indicator | Context Engineering Principle | Priority |
|:----------|:------------------------------|:---------|
| **Ignore Artifacts** | Least Privilege Security | High |
| **PostToolUse Hooks** | Automated Reliability | Medium |
| **Nesting Depth** | Progressive Disclosure | Medium |
| **Judge Prompts** | Evaluation-Driven Development | Low |
| **Persistent Plans** | Nondeterministic Idempotence | Medium |
| **Command Complexity** | Multi-step Reasoning | Low |
| **Semantic Drift Detection** | Context Health Monitoring | Research |

---

## Implementation Notes

### Quick Wins (can add to existing patterns)

1. **Ignore file detection** - Add to Level 5+ patterns in `config.py`
2. **Planning file detection** - Add `plan.md`, `todo.md` to Level 4+ patterns
3. **Hook complexity scoring** - Extend hook analysis in `scanner.py`

### Medium Effort (new analysis logic)

1. **Progressive disclosure scoring** - Measure file distribution vs. monolithic context
2. **Command depth analysis** - Parse command files for multi-step patterns
3. **Cross-reference graph depth** - Extend existing cross-ref detection

### Research Required

1. **Semantic drift detection** - Requires embedding models or LLM analysis
2. **Contextual entropy** - Needs formal definition and implementation
3. **Resonance intelligence** - Complex consistency checking

---

## Contributing

These features represent the future direction of the tool. If you're interested in implementing any of them:

1. Open an issue to discuss the approach
2. Reference this file in your PR description
3. Add tests for new detection patterns
4. Update documentation and examples

See [CONTRIBUTING.md](CONTRIBUTING.md) for general contribution guidelines.
