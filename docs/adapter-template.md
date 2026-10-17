# Client adapter contribution

Copy this structure into a pull request for a new adapter. Link test results and the client's official event/configuration documentation.

## Client and scope

- Client name and version:
- Operating system and Python version:
- Official lifecycle reference:
- Supported installation scope and configuration file:
- Client trust/restart procedure:

## Event mapping

| Client event | Remvu behavior | Stable identity fields | Payload limitations |
| --- | --- | --- | --- |
| Session begins | Load bounded memory | | |
| Observable action completes | Record evidence | | |
| Task or session ends | Mark pending or request one update | | |

## Configuration behavior

Describe how the adapter preserves user hooks, handles an existing Remvu installation, quotes executable paths, and reports unsupported configuration. State how users remove only this adapter.

## Evidence

- Synthetic payload, duplicate delivery and interruption tests:
- Concurrent-update, reviewed-event watermark and stale-revision tests:
- Explicit conflict resolution and historical check fingerprint tests:
- Live startup and stop-hook observation:
- Plain receiver with code plus `REMVU.md` only:
- Missing resources and known gaps:

Do not include raw private sessions, credentials or personal paths in a public pull request. Use synthetic fixtures or explicitly reviewed excerpts.
