# Markdown workflow and existing engine projects

The default skill now saves a lightweight `remvu-note/1` Markdown note in `.remvu/notes/REMVU.md`. It uses no Python or hooks. This is separate from strict `remvu/1` engine documents and does not replace or edit `.remvu/state.json`, archived evidence, or previously generated files.

Existing engine users may keep their runtime. Stop is nonblocking in the new source, but installed managed copies keep their old behavior until upgraded from reviewed source. Alternatively disable only the exact Remvu Stop handler using normal client settings. Never disable unrelated handlers or bypass trust. A Markdown save does not clear pending engine events, resolve engine conflicts or refresh code fingerprints.

If moving Markdown facts into the engine, author an ordinary reviewed proposal with retained basis, excerpts and superseded decisions. Do not claim a note was validator-checked, invent hashes or promote a secondhand user claim without original supporting evidence. Missing sources stay unverified. Plain receivers can read both file types; the strict validator accepts only actual `remvu/1` metadata and sections.

The earlier migration path below remains available.

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
