# Lifecycle adapters

`init --platform both` installs project-local Codex and Claude Code integration. Choose `codex`, `claude` or `none` when appropriate. It merges the Remvu-managed configuration with existing user settings. Inspect the installation result and follow any trust or restart instructions the client reports.

| Client | Configuration | Events mapped by the reference adapter |
| --- | --- | --- |
| Codex | `.codex/hooks.json` | `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `Stop`, `PreCompact`, `Interrupt`, `SessionEnd` |
| Claude Code | `.claude/settings.local.json` | `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `Stop`, `PreCompact`, `SessionEnd` |

Codex hook trust is managed through `/hooks`. Do not infer activation from the presence of `hooks.json`. Claude Code applies its own settings and hook approval rules. An adapter must not bypass those client controls.

Startup points the current agent at a bounded handoff. Pre-tool events record attempted calls; post-tool events record results using the same call ID, so an interrupted attempt is not presented as completed. Stop requests one semantic update when relevant work is pending. Pre-compaction and interruption/end events retain pending status so incomplete recording stays visible. An abnormal exit can prevent the agent's semantic update; hooks must not label that session complete.

The active agent performs the semantic update from its existing context. Scripts do not make extra model requests. Stop-hook repair is bounded to one request per logical user turn; continuation prompts cannot restart the loop. If repair still fails, report the pending state and stop retrying during that turn.

Codex provides native turn IDs. Claude Code turns are derived from prompt boundaries; an identical prompt delivered again during a still-open interrupted turn cannot be distinguished from a duplicate without parsing unstable transcripts. The adapter does not parse transcripts.

Local hooks and skill shims refer to the absolute installed script location. Re-run initialization after moving that installation and review changed hooks again. Exact ignore rules keep newly generated local paths private. If Git already tracks one of those paths, initialization warns and preserves the index; ignore rules cannot untrack an existing file.

Official references:

- [Codex hooks](https://learn.chatgpt.com/docs/hooks)
- [Claude Code hooks](https://code.claude.com/docs/en/hooks)

Synthetic event tests establish adapter mechanics. Only observed client executions establish that a particular client version activated the hooks. The repository's compatibility report records that distinction.
