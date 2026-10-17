# Compatibility

Remvu 0.2.0-rc.1 requires Python 3.10+. The runtime has no third-party Python dependencies. Git supplies repository identity, working-tree fingerprints and tracked patches; non-Git projects retain explicit missing Git metadata.

| Capability | Implementation | Evidence required for a supported claim |
| --- | --- | --- |
| `remvu/1` generation and validation | Reference CLI | Local tests and conformance examples |
| Revisioned memory and public isolation | Reference core | Concurrency, stale revision, reviewed-event watermark, conflict resolution and sharing tests |
| Version 0.1 evidence export/import | Retained exporter and import bridge | Legacy regression suite and import tests |
| Codex lifecycle integration | Project hook adapter | Synthetic payload tests plus observed activation in a named client version |
| Claude Code lifecycle integration | Project hook adapter | Synthetic payload tests plus observed activation in a named client version |
| Claude Code to Codex handoff | Code plus single document | Real receiver without original chat or Remvu installed |
| Codex to Claude Code handoff | Code plus single document | Real receiver without original chat or Remvu installed |
| Linux, macOS and Windows | CI matrix configured | Successful remote run for each matrix target |

The [validation report](validation-report.md) records actual results. A configured adapter or workflow is not a passing observation. The format is readable by other agents; it does not imply that their hooks or transcript formats are implemented. A receiver can check a standalone document against its project without initializing local memory. Recorded checks keep their historical code fingerprints; a later semantic update does not refresh an old passing result.

## Client configuration

Codex uses `.codex/hooks.json` with `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `Stop`, `PreCompact`, `Interrupt` and `SessionEnd`. Review client trust through `/hooks`. Claude Code uses `.claude/settings.local.json` with `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `Stop`, `PreCompact` and `SessionEnd`. Existing configuration is preserved when Remvu adds its managed entries.

The project skill is invoked as `$remvu` in Codex and `/remvu` in Claude Code. Installation provides local skill shims that refer to the installed source; retain that source path or reinitialize after relocating it.

Official references: [Codex hooks](https://learn.chatgpt.com/docs/hooks), [Codex skills](https://learn.chatgpt.com/docs/build-skills), [Claude Code hooks](https://code.claude.com/docs/en/hooks).
