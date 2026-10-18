# Lifecycle adapters

`install --platform both` copies the reviewed runtime to stable user storage and configures project-local Codex and Claude Code integration. Choose `codex`, `claude` or `none` for a new setup. Existing adapters are retained until explicitly uninstalled. Legacy `init` remains available but refers directly to its source path. Inspect the result and follow normal client trust/restart instructions. See [maintenance](maintenance.md).

| Client | Configuration | Events mapped by the reference adapter |
| --- | --- | --- |
| Codex | `.codex/hooks.json` | `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `Stop`, `PreCompact`, `Interrupt`, `SessionEnd` |
| Claude Code | `.claude/settings.local.json` | `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `Stop`, `PreCompact`, `SessionEnd` |

Codex hook trust is managed through `/hooks`. Do not infer activation from the presence of `hooks.json`. Claude Code applies its own settings and hook approval rules. An adapter must not bypass those client controls.

Startup points the current agent at a bounded handoff. Pre-tool events record attempted calls; post-tool events record results using the same call ID, so an interrupted attempt is not presented as completed. Stop never blocks completion or asks the agent to restart; pending events remain available for an explicit update. Pre-compaction and interruption/end events retain pending status so incomplete recording stays visible. An abnormal exit can prevent the agent's semantic update; hooks must not label that session complete.

The active agent performs the semantic update from its existing context. Scripts do not make extra model requests. Consolidation is explicit. Do not trigger semantic updates from Stop. Failed updates retain pending state for later review.

Bookkeeping detection recognizes only the exact installed runtime in a standalone supported invocation. On Windows it accepts the literal, single-quoted PowerShell form shown in the skill, including an absolute interpreter path and leading call operator. Compound commands, interpolation, other shell forms, same-named scripts and unknown file tools stay recorded. Parser/CLI coverage does not certify native Windows automatic consolidation; that remains pending real client acceptance.

Codex provides native turn IDs. Claude Code turns are derived from prompt boundaries; an identical prompt delivered again during a still-open interrupted turn cannot be distinguished from a duplicate without parsing unstable transcripts. The adapter does not parse transcripts.

Local hooks and skill shims refer to an absolute runtime location. Managed installation keeps that location independent of the clone; moving a legacy direct-init runtime requires reinitialization. Upgrade and rollback select managed versions and may require reviewing changed hook definitions. Exact ignore rules keep newly generated local paths private. If Git already tracks one of those paths, initialization warns without changing the index.

Initialize each separate worktree in its actual directory. A hook configured for
one project refuses payloads reporting a working directory outside that project;
the original project receives a gap marker, never the other project's tool body.
Shared automatic memory across separate worktrees is not certified by this adapter.

Official references:

- [Codex hooks](https://learn.chatgpt.com/docs/hooks)
- [Claude Code hooks](https://code.claude.com/docs/en/hooks)

Synthetic event tests establish adapter mechanics. Only observed client executions establish that a particular client version activated the hooks. The repository's compatibility report records that distinction.
