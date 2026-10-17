# Changelog

## 0.2.0

- Rename the project and primary skill to Remvu, with a short `remvu` invocation.
- Add the `remvu/1` project-memory proposal, JSON metadata and update schemas.
- Add private local memory, revisioned semantic updates, lifecycle adapters and explicit public handoffs.
- Preserve reviewed-event watermarks, archived conflict resolutions and historical code fingerprints for checks; keep default reads bounded.
- Keep the version 0.1 evidence exporter and legacy skill for migration.
- Add compatibility and validation reporting, adapter contribution guidance and CI configuration.
- Publish two real Claude Code/Codex handoff comparisons, with independent code checks, context recall and native usage counters.

This release provides a reference implementation and an open format proposal. See [the validation report](docs/validation-report.md) for observed compatibility and remaining limitations.

## 0.1.0

- Export visible task messages, tool calls and results into a local evidence bundle.
- Add indexed evidence, redaction, Git snapshots, bounded handoffs and integrity checks.
- Publish the original `agent-task-export` skill and synthetic examples.
