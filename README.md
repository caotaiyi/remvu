# Remvu

[![CI](https://github.com/caotaiyi/remvu/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/caotaiyi/remvu/actions/workflows/ci.yml)

Portable project memory for coding agents.

Give the next agent the project code and one `REMVU.md` file. It can read the goal, constraints, decisions, code state, checks and remaining work without installing Remvu or opening the original chat.

[中文](README.zh-CN.md) · [Format proposal](spec/remvu-v1.md) · [Compatibility](docs/compatibility.md) · [Validation report](docs/validation-report.md) · [Handoff walkthrough](docs/demo.md)

Remvu v0.2.0 is a reference implementation and open format proposal. Two real CLI handoffs passed on small fixed tasks: Claude Code to Codex and Codex to Claude Code. In both cases the fresh receiver matched all 11 fixed context term groups and completed the outstanding behavior checks. [Results and limits](docs/validation-report.md).

![30-second replay of the two real cross-agent handoff results](docs/assets/remvu-live-replay.gif)

This is a 30-second evidence replay, not an original screen recording. The actual model run times are shown; [inspect the source results](docs/demo.md).

## Start in an existing project

Requires Python 3.10+ and Git for repository state and patches. The runtime uses the Python standard library and makes no model API calls.

Keep this checkout outside the target project, for example in a dedicated tools directory.

```bash
git clone https://github.com/caotaiyi/remvu.git
python3 remvu/skills/remvu/scripts/remvu.py init --repo /path/to/project --platform both
```

`init` merges project instructions and lifecycle hooks, adds `.remvu/` to the local ignore rules, and installs local skill shims for both clients. It preserves existing settings and refuses to overwrite an unrelated skill. Keep the cloned source at its installation path; rerun `init` after relocating it. Complete the client's hook trust/restart instructions. In Codex, review hook trust with `/hooks`.

| Action | Claude Code | Codex |
| --- | --- | --- |
| Initialize | `/remvu init` | `$remvu init` |
| Update memory and create a local handoff | `/remvu` | `$remvu` |
| Create a public `REMVU.md` | `/remvu share` | `$remvu share` |
| Check memory against code | `/remvu check` | `$remvu check` |

Choose `--platform claude`, `codex` or `none` when initializing for one client or using only the CLI. A plugin package is also available through `plugin.json`; its scripts require a local environment that can read the project.

## What moves with the project

`REMVU.md` has a short first-read summary followed by fixed sections for intent, architecture, decisions, changes, evidence and open work. Its first JSON block identifies the format, memory revision and code state.

Every statement distinguishes user confirmation, observation, inference and unverified claims. A passing check needs evidence and retains the code fingerprint it checked. Later notes do not make an old pass current. Superseded decisions remain visible with their replacements, so the next agent can avoid repeating a rejected approach.

Private semantic memory, incremental events and detailed evidence stay in the ignored `.remvu/` directory. Hooks record observable events; the active agent summarizes relevant work using context it already has. A missed update remains pending, and a stop hook can request one repair. Concurrent updates use revision checks instead of silently overwriting each other.

The scripts make no extra model requests. Writing and reading memory still uses the active agent's context. Remvu does not claim a measured reduction in tokens or cost without a controlled result.

## Share explicitly

Ask `/remvu share` or `$remvu share` to select public entries and generate a local file. Public entries need public inline sources; the receiver must not depend on private logs or attachments. Review the file before publishing it.

```bash
python3 /path/to/remvu/skills/remvu/scripts/remvu.py share --repo /path/to/project --out /tmp/REMVU.md
python3 /path/to/remvu/skills/remvu/scripts/remvu.py validate /tmp/REMVU.md
```

Sharing stops when evidence is still pending or conflicts remain unresolved, and by default when the code has uncommitted changes. Prefer a committed state. `--include-patch` is available after an explicit choice to carry the tracked diff; required untracked or ignored resources must be listed separately. Generating a file never commits, pushes or uploads it.

Hidden chain of thought, analysis messages, system/developer messages and encrypted reasoning are excluded. Decision notes retain conclusions and explainable grounds. Secret detection cannot prove that arbitrary text is safe to publish. Hashes and code fingerprints detect changes, not truth or authorship.

## Use the tools directly

```bash
python3 skills/remvu/scripts/remvu.py status --repo /path/to/project
python3 skills/remvu/scripts/remvu.py entries --repo /path/to/project --offset 0 --limit 20
python3 skills/remvu/scripts/remvu.py show ENTRY_OR_EVENT_ID --repo /path/to/project --max-chars 4000
python3 skills/remvu/scripts/remvu.py update --repo /path/to/project --proposal /tmp/memory-update.json
python3 skills/remvu/scripts/remvu.py handoff --repo /path/to/project
python3 skills/remvu/scripts/remvu.py check --repo /path/to/project --document /tmp/REMVU.md
```

`status` and entry previews are bounded; `status --full` is an explicit full-state read. Update proposals use `base_revision`, a reviewed `base_event_count` watermark and typed entries. Newer events remain pending after an update. The protocol permits older writers to omit the watermark, which acknowledges no new events. `--proposal-json 'JSON'` is an alternative to `--proposal FILE` with the same schema. Use a standalone inline update during hook-driven consolidation to avoid recording a new proposal-file edit. See the [synthetic examples](examples/remvu/) and [proposal schema](spec/proposal.schema.json).

Reconcile a stale proposal against current memory, then record its resolution with `resolve-conflict ID --repo PROJECT --base-revision N --note TEXT`; add `--entry-id ID` for each reconciled entry. The original proposal and resolution stay archived. The first-read summary defaults to 8,000 characters; important detail remains available below it. A receiver can use `check --document FILE --repo PROJECT` without initializing Remvu.

Narrow future shares with `withhold ID [ID...] --repo PROJECT --base-revision N --note TEXT`. It records the withdrawal while retaining the original claims and evidence; existing exported files stay unchanged.

Existing Agent Task Export bundles and commands remain available. Use `import-legacy --repo PROJECT BUNDLE` to bring reviewed notes into memory, or `legacy --help` for the original indexed evidence exporter. The [migration guide](docs/migration.md) describes the differences.

## Build on the format

The [format proposal](spec/remvu-v1.md), schemas and conformance examples are public. Other agents can write or read `remvu/1` without using this implementation. Contributions should include a reproducible handoff case and state what was actually tested.

```bash
python3 -m unittest discover -s tests -v
python3 spec/validate_examples.py
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for client adapters and release requirements. Public prose follows [blader/humanizer](https://github.com/blader/humanizer)'s editing rules. Humanizer is not a runtime dependency.

MIT License.
