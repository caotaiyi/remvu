# Changelog

## 0.3.0-beta.1 candidate (not released)

- Add managed, checksum-indexed runtime installation independent of the source clone.
- Add doctor, reviewed-source upgrade/rollback, conservative uninstall, verified snapshot/ledger repair and allowlisted local diagnostics.
- Preserve configuration checkpoints and concurrent evidence on failed installation; retain private memory on uninstall.
- Recognize only canonical literal PowerShell bookkeeping; retain ambiguous commands as evidence.
- Record hook execution separately from trust and surface certification; preserve observation gaps for review.
- Retain five recovery snapshots and archive old hook sessions without deleting evidence/journals.
- Add package lifecycle smoke, native acceptance fixtures, twelve-profile release readiness and bilingual onboarding/feedback guides.

Release remains gated on real client acceptance. Historical results and CI do not satisfy it.

## 0.2.0

- Rename the project and primary skill to Remvu, with a short `remvu` invocation.
- Add the `remvu/1` project-memory proposal, JSON metadata and update schemas.
- Add private local memory, revisioned semantic updates, lifecycle adapters and explicit public handoffs.
- Preserve reviewed-event watermarks, archived conflict resolutions and historical code fingerprints for checks; keep default reads bounded.
- Add audited public-to-private withdrawal for future shares while preserving the original claims, sources and history.
- Keep the version 0.1 evidence exporter and legacy skill for migration.
- Add compatibility and validation reporting, adapter contribution guidance and CI configuration.
- Publish two real Claude Code/Codex handoff comparisons, with independent code checks, context recall and native usage counters.
- Use UTF-8 CLI/hook streams and Git-authorized text line-ending normalization; keep Windows shell recording conservative instead of guessing which commands are bookkeeping.

This release provides a reference implementation and an open format proposal. See [the validation report](docs/validation-report.md) for observed compatibility and remaining limitations.

## 0.1.0

- Export visible task messages, tool calls and results into a local evidence bundle.
- Add indexed evidence, redaction, Git snapshots, bounded handoffs and integrity checks.
- Publish the original `agent-task-export` skill and synthetic examples.
