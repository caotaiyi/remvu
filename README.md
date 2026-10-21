# Remvu

[![Tests](https://github.com/caotaiyi/remvu/actions/workflows/ci.yml/badge.svg)](https://github.com/caotaiyi/remvu/actions/workflows/ci.yml) [![Standalone and DSH](https://github.com/caotaiyi/remvu/actions/workflows/standalone.yml/badge.svg)](https://github.com/caotaiyi/remvu/actions/workflows/standalone.yml)

Save before Claude Code hits its limit. Continue in Codex with the project background intact.

Remvu keeps goals, constraints, rejected approaches, unfinished work and check evidence alongside your project. The complete standalone engine bundles its runtime: **users do not install Python**. Opt-in observable recording, code fingerprints, concurrent updates, recovery and private sharing boundaries remain part of the engine.

[中文](README.zh-CN.md) · [Install](docs/quickstart.md) · [DeepSeek Harness plugin](adapters/dsh/README.md) · [Evidence and limits](docs/standalone.md)

Fresh installations create no hooks. Recording is a separate choice; fingerprints, CAS protection and recovery stay available in manual mode. Resume reads a short preview; details are fetched only when needed.

## Try the complete app

> Install the complete Remvu standalone candidate from https://github.com/caotaiyi/remvu for my OS and architecture. Verify its checksum, extract the entire application folder, then run its install command for this project. Preserve existing settings and memory. Install save/resume without hooks. Enable recording only if I ask; explain any required client trust once. Do not install a system Python or substitute the notes-only fallback.

The v0.3.0-beta.3 application is a test candidate. CI produces platform archives; a production release and the full native-client support matrix remain gated on actual acceptance. See [the build and installation guide](docs/standalone.md) for available artifacts, verification and exact steps. Git is still required. macOS distribution signing/notarization is not configured.

| Everyday action | Claude Code | Codex |
| --- | --- | --- |
| Save a private handoff | `/remvu save` | `$remvu save` |
| Continue in a new session | `/remvu resume` | `$remvu resume` |

`save` asks the current agent to consolidate reviewed evidence and exports `.remvu/handoff/REMVU.md`. A direct program invocation without a proposal exports existing state and leaves pending evidence pending. It never uploads or commits. `resume` checks the saved code state before continuing. The receiver can also read the handoff alongside the code without installing Remvu.

Save while the original agent can still respond. Automatic logs retain observations; they cannot recover an exhausted agent's unwritten understanding. Stop hooks do not block completion or force another model turn.

## A handoff in 30 seconds

1. In Claude Code, ask `/remvu save`.
2. Open the project in Codex and ask `$remvu resume`.
3. Review the next step and any stale checks, pending evidence or conflicts, then continue.

This describes the workflow, not a measured completion-time guarantee. [Earlier real handoff trials](docs/validation-report.md) and the [10-task notes-only comparison](docs/product-validation.md) are published with their limits. The latter found no first-pass accuracy advantage over ordinary HANDOFF notes; it does not measure the new standalone app or prove token savings.

## DeepSeek Harness

The `dsh-remvu` bundle adds five native tools and observable event recording to DeepSeek Harness **0.2.1-rc.2**. It uses the same standalone engine and `.remvu/` state. The JavaScript package needs no compilation or install-time build script. [Install the plugin](adapters/dsh/README.md).

The plugin was installed through the official `dsh plugin add` flow and loaded in a real isolated SDK profile without a model request. Model-driven handoff and GUI acceptance are separate pending checks. Local projects only; it does not claim cloud or remote-filesystem support.

## What stays in memory

Claims distinguish `user_confirmed`, `observed`, `inferred` and `unverified`. Rejected decisions and superseded history survive. Check results retain the code fingerprint they actually tested; later edits make those checks historical. Concurrent proposals cannot silently overwrite newer memory.

Private memory and detailed evidence stay in ignored `.remvu/`. Public `REMVU.md` is generated only on an explicit share request, with public inline evidence and patch review. Hidden reasoning, credentials and unrelated conversations are excluded. `doctor`, `repair`, upgrades, rollback and uninstall remain available when needed; uninstall retains private memory.

## For multi-model platforms and API relay services

“换模型、换客户端，把项目背景一起带走。” A platform that can observe local project changes and tool outcomes can embed the memory engine or build an adapter. Pure API forwarding has no complete view of the project and cannot promise full operation records. The DSH adapter is a concrete local-host integration; no generic relay integration or measured savings percentage is claimed.

## Other paths and contributors

A [notes-only fallback](skills/remvu/assets/markdown-skill.md) remains available for users who deliberately want file-tool save/resume without recording or structured validation. Source developers can still run the standard-library Python engine. Neither path replaces the complete standalone app.

[Open format](spec/README.md) · [Compatibility](docs/compatibility.md) · [Contributing](CONTRIBUTING.md) · [License](LICENSE). Existing `remvu/1` documents and legacy evidence import remain supported.
