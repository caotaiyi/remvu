# Remvu

[![CI](https://github.com/caotaiyi/remvu/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/caotaiyi/remvu/actions/workflows/ci.yml)

**Claude Code reached its limit? Save your project context and continue in Codex.**

Remvu is a Markdown skill for handing a project to the next coding agent. Save the goal, constraints, rejected approaches and unfinished work; let the next agent read the file alongside your code. The default workflow needs **no Python, hooks, account or background service**.

[中文](README.zh-CN.md) · [Quick start](docs/quickstart.md) · [What is verified](docs/compatibility.md)

## Try it

Give your coding agent this instruction:

> Install the Markdown Remvu skill from https://github.com/caotaiyi/remvu into this project's Claude Code and Codex skill folders. Use scripts/install-skill.sh on macOS or scripts/install-skill.ps1 on Windows after reviewing it. Preserve existing skills. Do not run the optional Python installer or enable hooks.

The installer copies project skills, leaving client settings alone. It uses Git to fetch source; a reviewed local checkout also works offline. Ordinary client project trust still applies. Open a new session if the client has not discovered the skill. [Manual installation and removal](docs/quickstart.md).

| | Claude Code | Codex |
| --- | --- | --- |
| Save before leaving | `/remvu save` | `$remvu save` |
| Continue in a fresh session | `/remvu resume` | `$remvu resume` |

`save` writes a private local note under `.remvu/notes/REMVU.md`. It does not commit or upload. `resume` reads the handoff, compares its recorded code state with the project and continues the requested work. The recipient can also just be told “Read this file and continue”; Remvu installation is optional on the receiving side. On another machine, take the project code and the selected note with you.

## The handoff, in 30 seconds

1. In Claude Code: `/remvu save`.
2. Open the same project in Codex: `$remvu resume`.
3. Review the reported next step and any stale or missing evidence, then continue.

This is the intended quota-switch workflow; it does not require deliberately exhausting an account. The older clip below replays two real small CLI trials. It is an evidence replay, not a screen recording or a timing claim about the new Markdown workflow.

![30-second replay of historical CLI trial results](docs/assets/remvu-live-replay.gif)

[Source results and limits](docs/demo.md). The new ten-task CLI comparison completed, with results below; older engine trials do not certify this workflow.

## What survives the switch

Notes distinguish **user-confirmed, observed, inferred and unverified** claims. They keep rejected directions, failed checks and open work, with short sources and retained decision history. The first-read summary is usually under 2,000 characters; essential detail remains below it.

Save is explicit. Remvu does not interrupt completion or ask a Stop hook to restart the agent. The optional recorder now also leaves pending work pending without blocking. A save can still be incomplete; the agent reads it back and reports gaps rather than claiming an automatic transcript.

Markdown notes use the lightweight `remvu-note/1` convention. They have no automatic content fingerprint, transaction lock or validator guarantee. The agent must inspect changed code and rerun relevant checks. [Note rules and limits](skills/remvu/references/notes.md).

## Optional engine and open format

Existing Python tools remain available for `remvu/1` documents, code fingerprints, evidence indexing, revision-checked updates, privacy review and recovery. They use Python 3.9+ and Git; they are optional for save/resume. Existing memory, releases and formats are retained. [Engine workflow](skills/remvu/references/engine-workflow.md) · [Maintenance](skills/remvu/references/maintenance.md) · [Format proposal](spec/remvu-v1.md).

Public sharing is a separate, explicit request. Review selected project facts and safe inline evidence before generating a root `REMVU.md`. A local private note is never automatically made public. Hidden reasoning, secrets and unrelated conversations are excluded. [Sharing rules](skills/remvu/references/notes.md#explicit-public-share-advanced).

## For multi-model platforms and API relay services

Change models or clients, and take the project context with you. A platform can adopt the open format when it can access project files and observable results. API forwarding alone cannot reconstruct a project's actions. A dedicated relay adapter is not bundled.

## Status and evidence

This branch remains a **v0.3.0-beta.1 candidate**. Native desktop/VS Code and Windows acceptance are pending; a file-copy test or CLI trial cannot certify those surfaces. The published v0.2.0 engine and historical results remain available. [Compatibility](docs/compatibility.md) · [Beta report](docs/beta-validation.md) · [Feedback](.github/ISSUE_TEMPLATE/bug.yml).

The new ten-task comparison found the same outcomes for ordinary HANDOFF.md and Remvu: 9/10 first-attempt completions, 10/10 after one correction on the remaining task. Remvu notes were larger (34,614 versus 10,039 bytes in total). This does not establish a token, cost or speed advantage. [Full results, usage and limits](docs/product-validation.md) · [Protocol](evals/markdown-protocol.md).

MIT licensed. [Contributing](CONTRIBUTING.md).
