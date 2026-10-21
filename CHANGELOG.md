# Changelog

## 0.3.0-beta.3 candidate

- Default new installs to complete save/resume skills with no hooks. Add explicit recording on/off, preserving memory, foreign hooks and prior upgrade preferences.
- Opt-in recording uses four Claude events and three Codex events, without Stop, pre-tool, compaction or end hooks.
- Reduce resume memory previews to a 2,400-character component budget. Keep omitted-entry counts, provenance and full retrieval paths; detailed checks remain explicit.
- Make DSH capture/context opt-in and inject once per session/compaction window, including one failure notice at most. Defer advanced tool schemas.
- Consolidate on requested save, not automatically after ordinary observations. No measured token-savings claim.

## 0.3.0-beta.2 candidate (not released)

- Make the complete standalone app the primary path; bundle CPython so users need no Python installation.
- Keep automatic observable recording, code fingerprints, CAS conflicts, recovery, sharing boundaries and legacy export/import.
- Add save/resume to the full engine, stable binary-backed hooks, app integrity manifests, bundled upgrades/rollback and DSH overlay generation.
- Add a prebuilt DeepSeek Harness 0.2.1-rc.2 bundle with five tools, bounded context, queued observable events and explicit read-only/workspace boundaries.
- Verify actual DSH plugin installation and SDK-profile boot without a model request; keep model/GUI/Windows native acceptance pending.
- Add target-platform standalone CI and no-Python-PATH packaged tests, including concurrent writes and upgrade/rollback.
- Preserve the notes-only workflow as a separate optional fallback. Earlier benchmark results remain historical; no savings claim is added.

## 0.3.0-beta.1 candidate (not released)

- Make a no-Python Markdown skill the default, with save/resume as the two primary actions; keep the strict engine optional.
- Add native shell/PowerShell skill-copy installers and a Markdown-only archive, without configuring hooks.
- Make engine Stop handling quiet and nonblocking, preserving pending evidence.
- Support the optional engine on macOS/Linux Python 3.9+ and Windows Python 3.10+; reject Windows 3.9 managed installs after retained recorder stress failures. Keep its strict manual reproduction workflow.
- Add a fixed ten-task HANDOFF.md comparison protocol with native clients; report results and limits separately.

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
