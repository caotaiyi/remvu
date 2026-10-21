# Standalone v0.3.0-beta.3 candidate

The primary path is now the complete app with its runtime bundled; users need no Python installation. Fresh installations expose save/resume without installing hooks. Fingerprints, CAS and recovery remain available. Automatic recording is opt-in; existing installations preserve their recording preference. [Standalone evidence and limitations](standalone.md) distinguish packaged checks, actual DSH host startup and pending model/native acceptance. DSH targets exactly 0.2.1-rc.2; no desktop/Web or Windows DSH certification is implied.

The source-development engine still supports Python 3.9+ on macOS/Linux and 3.10+ on Windows. Windows source Python 3.9 failed repeated pressure tests and remains unsupported; the bundled app uses modern Python internally. Earlier [eight-job source CI](https://github.com/caotaiyi/remvu/actions/runs/39138270476) belongs to b29423b. Its results and the old notes-only comparison are historical, not certification of this new app.

# Compatibility

## Current candidate native-client gate

The candidate adds managed installation and maintenance. Native support is tracked independently for each entry point; no row inherits v0.2.0 certification.

| System / client | Terminal | Desktop local project | VS Code official extension |
| --- | --- | --- | --- |
| macOS / Claude Code | Acceptance pending | Acceptance pending | Acceptance pending |
| macOS / Codex | Acceptance pending | Acceptance pending | Acceptance pending |
| Windows 11 x64 / Claude Code | Acceptance pending | Acceptance pending | Acceptance pending |
| Windows 11 x64 / Codex | Acceptance pending | Acceptance pending | Acceptance pending |

Manual commands are the fallback design, not an unverified compatibility claim. Automatic support additionally requires multi-turn, compaction, interruption, concurrency and bounded-repair evidence. The [acceptance guide](native-acceptance.md) and [machine-readable ledger](../evals/beta-matrix.json) define the release gate.

Windows bookkeeping now recognizes only the exact installed Python/runtime in a canonical single-quoted PowerShell invocation. Other forms remain observations. Unit/CI coverage is separate from native Windows validation. Desktop tests use local coding projects; ordinary chat and cloud workspaces are excluded. Codex IDE does not currently support plugins, so use project skills/configuration instead of a plugin ZIP. See [official plugin support](https://learn.chatgpt.com/docs/plugins).

## Historical v0.2.0 evidence

Remvu v0.2.0 is a reference implementation of the `remvu/1` open format proposal. It declares Python 3.10+ and uses no third-party runtime Python packages. Git supplies repository identity, working-tree fingerprints and tracked patches; non-Git projects keep explicit missing Git metadata.

| Capability | Current observation |
| --- | --- |
| `remvu/1` generation and validation | Seven conformance cases passed, including JSON Schema checks |
| Revisioned memory, evidence and public isolation | Complete local suite: 137 passed, zero skips on macOS Python 3.9.6 |
| Version 0.1 export and import | Legacy regression and import checks passed in the local suite |
| Claude Code to Codex handoff | Real fresh receiver: 11/11 context term groups and 4/4 behavior checks |
| Codex to Claude Code handoff | Real fresh receiver: 11/11 context term groups and 5/5 behavior checks |
| Claude Code lifecycle hooks | On macOS, native activation, tool events, bounded Stop and clean skill-guided consolidation observed |
| Codex lifecycle hooks | On macOS, native activation, tool events, bounded Stop and clean skill-guided consolidation observed |
| Linux and macOS, Python 3.10 and 3.12 | All four final runtime CI jobs passed; 137 tests and zero skips per job |
| Windows, Python 3.10 and 3.12 | Both final runtime CI jobs passed; 135 tests executed and two POSIX symlink-fixture skips per job |

The native handoff clients were Claude Code `2.1.302` and Codex `0.163.0-alpha.10.2`. These two small functional tasks do not establish broad coding performance or token savings. [Final runtime CI passed all six jobs](https://github.com/caotaiyi/remvu/actions/runs/39038137341); the [validation report](validation-report.md) records earlier failures, native artifacts and exact usage.

Initial natural hook runs retained pending events when agent bookkeeping created observations beyond its reviewed watermark. Subsequent skill-guided continuations reached clean handoffs and current checks in both clients. Native client observations are limited to macOS; CI checks local code and synthetic payloads across operating systems. Detailed repair counts and the original pending outcomes are retained in the [native hook report](../evals/live-hooks-report.json) and [validation report](validation-report.md).

Windows shell commands are recorded conservatively rather than classified as safe bookkeeping. They may leave pending events for human or agent review; native Windows automatic clean consolidation is not supported. For a new manual CLI-only setup, choose `init --platform none`. CLI/core behavior and UTF-8 hook transport have separate CI coverage. On other platforms, bookkeeping detection requires the exact installed runtime in a recognized standalone Python or Bash invocation; compound commands, substitutions, same-named scripts and unknown file tools remain evidence.

A receiver can check a standalone document against its project without initializing local memory. Recorded checks retain their historical code fingerprints; later notes do not refresh an old passing result. Other agents can read the Markdown format, but no native lifecycle adapter is claimed for them.

Reference fingerprints follow Git's declared text/line-ending policy. Authorized tracked CRLF text is normalized to LF; automatic policies preserve historically CRLF-indexed files. Binary, `-text`, mixed-line-ending and untracked content stays byte-sensitive, and existing LF fingerprints remain unchanged. Equivalent text checkouts can match without having identical working-tree bytes. This does not execute Git content filters.

## Client configuration

Fresh installs add project skills and no hooks. Explicit `recording on` installs three Codex events (`SessionStart`, `UserPromptSubmit`, `PostToolUse`) or four Claude Code events (the same three plus `PostToolUseFailure`). Review client hook trust when enabling recording. No Stop handler is installed in this profile. `recording off` removes only recognized managed handlers, preserving unrelated configuration and private memory.

Older installations can contain a larger event mapping; historical observations above describe those older adapters. They do not certify this candidate's reduced profile. Native compaction, interruption and multi-round acceptance remain pending.

The project skill is invoked as `$remvu` in Codex and `/remvu` in Claude Code. Managed installations use a stable runtime location. Ignore rules cannot remove private files already tracked by Git; initialization reports those paths for review without changing the index.

Official references: [Codex hooks](https://learn.chatgpt.com/docs/hooks), [Codex skills](https://learn.chatgpt.com/docs/build-skills), [Claude Code hooks](https://code.claude.com/docs/en/hooks).
