# Migrating from Agent Task Export

Remvu is the next release of `agent-task-export`. The GitHub repository was renamed to [caotaiyi/remvu](https://github.com/caotaiyi/remvu); the old repository URL redirects, and the version 0.1 release remains available. The new format, `remvu/1`, describes ongoing project memory in one readable file. The old evidence bundle remains useful when a receiver needs indexed tool records.

## Existing installations

Keep the old `skills/agent-task-export` directory while introducing `skills/remvu`. The old `$agent-task-export` invocation and `task_export.py` commands retain their original behavior. Use `$remvu` in Codex or `/remvu` in Claude Code for new memory and handoff work.

Do not rename a version 0.1 `START_HERE.md` file to `REMVU.md`: it lacks the new metadata and code-state checks. Import the verified bundle through `import-legacy` instead. Imported notes identify their source and preserve unknown or unverified outcomes. A bundle's hashes establish integrity, not the truth of its contents.

## File formats

| Version 0.1 | Remvu |
| --- | --- |
| `START_HERE.md` task snapshot | `REMVU.md` project handoff |
| `task.json` authored notes | Revisioned memory update proposal |
| `events.jsonl`, `index.json`, `blobs/` | Optional local evidence, not required by a public receiver |
| No persistent memory | Ignored `.remvu/` memory and incremental recorder |

`remvu/1` is independent of the package version. New metadata or required headings will use a new format identifier. The reference validator reports unsupported versions instead of silently reinterpreting them.
