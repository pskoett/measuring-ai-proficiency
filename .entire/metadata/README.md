# .entire/metadata/ — Schema Documentation

This directory holds schema documentation for Entire CLI session captures. Raw session data is never committed here (it stays in GitHub Actions artifact storage). Only this README is tracked in git.

## Purpose

The `.entire/` directory is the designated mount point for [Entire CLI](https://github.com/entireio/cli) session captures when Entire is enabled on this repository. Entire captures local Claude Code sessions (prompts, tool calls, tool outputs) as JSONL on a shadow branch.

For the factory's agent workflows (the gh-aw-compiled `.github/workflows/*.lock.yml` files), session transcripts are stored as **GitHub Actions artifacts** named `agent`, not in `.entire/`. See `docs/AGENT_FACTORY.md#observability` for details on factory transcript storage, retention, and analysis.

## Directory layout when Entire is active

```
.entire/
├── metadata/
│   ├── README.md                  ← this file (committed to git)
│   └── <session-id>/              ← gitignored (raw session data)
│       ├── full.jsonl             ← full session transcript (JSONL)
│       └── prompt.txt             ← the initial prompt
└── tmp/                           ← gitignored (working files)
```

Raw session directories under `metadata/<session-id>/` are excluded from git via `.gitignore`. They contain full conversation data that may include PII from issue bodies, commit messages, and file contents.

## JSONL transcript format

Each line in `full.jsonl` is a JSON object representing one event in the session:

```json
{
  "type": "user" | "assistant" | "tool_use" | "tool_result",
  "timestamp": "ISO 8601",
  "session_id": "uuid",
  "content": "...",
  "tool": "optional tool name for tool_use/tool_result",
  "input": "optional tool input",
  "output": "optional tool output"
}
```

## Relationship to GitHub Actions artifacts

| Capture surface | Storage location | Retention | Access |
|-----------------|-----------------|-----------|--------|
| Local Claude Code sessions (Entire) | `.entire/metadata/` (local only, shadow branch) | Until cleared locally | Developer's machine |
| gh-aw factory workflow sessions | `agent` artifact per workflow run | 90 days | GitHub Actions (repo read access) |

The `learning-aggregator-ci` workflow reads from GitHub Actions artifacts. It does not read from `.entire/metadata/` because `.entire/` is local-only storage.

## PII and retention policy

Both capture surfaces may contain:
- Issue body text (user-authored content)
- Commit messages and PR descriptions
- File contents and error messages

**Policy**: Do not copy raw transcript content into issues, `.learnings/` entries, or PR descriptions. Extract structural patterns (tool sequences, error categories, retry counts) only.

For GitHub Actions artifacts, the retention period is 90 days and is configurable in Settings > Actions > Artifact and log retention. After 90 days, artifacts are automatically deleted.

For Entire captures, delete session directories from `.entire/metadata/` when they are no longer needed for analysis.
