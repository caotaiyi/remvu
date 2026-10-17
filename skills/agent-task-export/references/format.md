# Evidence format and coverage

## Inputs

The exporter accepts UTF-8 JSONL. It snapshots the source byte length at startup; later appends are outside that export. The source is never modified. Parsing is sequential, with memory proportional to the largest input record plus the event/call index. It does not require loading the transcript into the model context.

Supported adapters:

- Codex rollout: `response_item.message` for user and visible assistant text, `function_call`, `custom_tool_call`, and their output variants. `session_meta` is used only by metadata discovery. Duplicate `event_msg` message mirrors are excluded.
- Codex `exec --json`: `item.started` command calls, `item.completed` command outputs, agent messages and file change inventories. Other exec event types, including MCP-specific events, are excluded. See [official OpenAI documentation](https://developers.openai.com/codex/noninteractive/). Local rollout schemas are implementation details and may change; coverage reports unknown shapes.
- Portable evidence: objects tagged `"format":"agent-task-evidence/v1"`. Allowed kinds and fields follow below. This format also works for another agent's user-provided visible transcript, after explicit conversion. There is no automatic Claude/ChatGPT adapter.

```json
{"format":"agent-task-evidence/v1","kind":"message","role":"user","text":"Fix the CSV import"}
{"format":"agent-task-evidence/v1","kind":"tool_call","call_id":"c1","tool":"shell","arguments":{"command":"python3 -m unittest"}}
{"format":"agent-task-evidence/v1","kind":"tool_result","call_id":"c1","output":{"exit_code":0,"stdout":"Tests passed"}}
{"format":"agent-task-evidence/v1","kind":"edit","path":"src/import.py","action":"update","patch":"optional recorded patch"}
{"format":"agent-task-evidence/v1","kind":"decision","summary":"Use the standard CSV parser","evidence":["e000001"]}
{"format":"agent-task-evidence/v1","kind":"check","command":"python3 -m unittest","outcome":"passed","evidence":["e000003"]}
```

Only `user` and `assistant` message roles are accepted. Explicit nonpublic channels are excluded. Do not put hidden reasoning inside a portable message: this format declares the supplied fields to be observable evidence. The script cannot determine the provenance of arbitrary text.

## Task notes

Optional `--task task.json` accepts string `goal` and `outcome`, plus string lists `constraints`, `decisions`, `checks`, `next_steps`, and `risks`. Other fields are dropped. Notes are redacted and stored as `task.json`; `START_HERE.md` includes them with evidence counts. Missing notes remain explicitly unknown. The default character budget can be changed with `--max-handoff-chars`; oversized notes fail before a bundle is published. No model generates the notes inside the script.

## Bundle files

| File | Purpose |
| --- | --- |
| `START_HERE.md` | Small first read: goal, outcome, notes, gaps, evidence entry points |
| `index.json` | Event byte offsets, tool groups, call/result pairs, edit references |
| `events.jsonl` | Ordered normalized evidence; original source line numbers |
| `blobs/<sha256>.txt` | Full redacted text, arguments, patches and outputs, deduplicated by bytes |
| `coverage.json` | Scope, counts, malformed lines, exclusions and pairing gaps |
| `task.json` | Agent-authored task notes, kept separate from observed events |
| `git/snapshot.json` | Optional baseline commit, HEAD and status |
| `git/changes.diff` | Optional redacted tracked-file diff, for review only |
| `manifest.json` | Version, storage sizes, file inventory and SHA-256 hashes |

Event IDs are stable only within a bundle. A result's presence means a result record exists; its content still decides success. Multiple calls/results with the same ID are ambiguous. Calls without IDs are counted separately. Patch paths show attempted edits; inspect their result before claiming completion. Git changes can include pre-existing work or concurrent changes. Git rename detection is Git's inference. Untracked-file contents and binary file contents are not copied.

Malformed JSON, partial trailing lines and non-object records are skipped and counted, with the first 20 affected line numbers. Unknown record types are counted without copying their bodies. A source hash covers the snapshotted source bytes, including excluded records; the source file itself is not included. Concurrent in-place modifications are outside the append-only log assumption. A source that has already compacted or truncated content limits what can be exported.

## Cost and integrity

Storage metrics are bytes and counts. Reading the small handoff first and fetching individual events can reduce model input relative to reading a full log. Actual tokens and cost depend on the model and what is read; this project reports no claimed token-saving percentage. File deduplication reduces storage, not necessarily inference tokens.

Redaction changes evidence, so exported patches are not apply-ready backups. Common keys/tokens, auth headers, private-key blocks, URL credentials and home-directory paths are filtered. Custom secrets, arbitrary identities and transcript prose may remain. No automatic secret scanner is claimed.

`verify` checks file hashes, inventory, path containment and symlinks. It does not verify a digital signature or truthfulness. A malicious actor who rewrites both files and manifest can pass it. Verify before `show` when consuming a shared bundle. `show` performs bounded reads of referenced blobs. `archive` verifies before making a fresh ZIP; it never uploads or extracts archives.
