# v0.3.0-beta.1 candidate validation

The candidate is **not released**. The twelve-profile native acceptance ledger
is pending. Package/unit checks and historical v0.2.0 evidence cannot certify it.

## Current native regression, 2026-10-18

Two fresh macOS CLI handoffs used Claude Code 2.1.302 and Codex
0.163.0-alpha.10.2 with the updated runtime. These were focused checks without
new no-memory controls. The receiving agent had code and `REMVU.md`, without
project Remvu state or its original conversation.

| Direction | Code behavior | Fixed lexical recall | Strict runner acceptance |
| --- | --- | --- | --- |
| Claude Code → Codex | 4/4 | 10/11 | Failed |
| Codex → Claude Code | 5/5 | 10/11 | Failed |

Both receivers implemented the unfinished behavior, but each missed one
next-step term group in its pre-edit recall. The runner retains these failures;
the scoring rules were not changed to make them pass. Lexical coverage is not
semantic proof.

The Codex producer also retained a stage-1 delivery boundary as a continuing
constraint. The receiver disclosed the conflict and followed the current user
task. The skill now says to separate temporary stage instructions from lasting
constraints. This trial predates that guidance change and does not validate it.

A focused Codex → Claude follow-up after the guidance change passed 11/11 term
groups and 5/5 behavior checks. Its producer recorded the temporary boundary as
progress, rather than an ongoing constraint. [Follow-up summary and actual usage](../evals/results/beta-scope-followup-2026-10-18.json).
This one repeat does not replace the earlier failures or certify other profiles.

[Reviewed summary and actual usage counters](../evals/results/beta-live-2026-10-18.json)
include process times and reported usage. No savings percentage is derived.
Raw provider output, chat logs and private runtime directories are not published.

## Automated checks

The original 137-test suite passed locally on system Python 3.9.6 before the
new lifecycle coverage. A subsequent Python 3.12.15 run passed 151 tests with
one Windows-only path-semantics test skipped on macOS. Later changes require
the final CI and package checks; consult the linked run and committed evidence
before treating a count as the current candidate's result.

New lifecycle coverage includes source relocation, repeated install, checksum
tampering, upgrade/rollback, failed-install preservation of concurrent events,
conservative uninstall, cold read-only doctor, snapshot/ledger recovery,
missing evidence, orphan-journal retention, bounded recovery copies and
allowlisted diagnostics. Shell parsing tests do not replace native Windows hooks.

## Remaining release gates

Windows 11 x64 is user-operated. Desktop and VS Code native lifecycle checks
remain separate work. Each profile needs installation, first use, cold handoff,
intent and failed-check review, upgrade/rollback, uninstall and privacy evidence.
Automatic profiles additionally need real compaction, interruption, concurrency
and repeated-turn checks. See [native acceptance](native-acceptance.md).

Run `python scripts/check_beta_readiness.py --require-ready` before publishing.
A failing gate keeps v0.3.0-beta.1 unpublished. Development source and CI packages
may still be shared as explicitly unverified candidates.
