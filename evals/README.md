# Evaluation

The default Markdown skill is evaluated against ordinary HANDOFF.md using [a fixed ten-task protocol](markdown-protocol.md) and [the native runner](run_markdown.py). The native inputs and limitations are frozen before the full run. The historical engine evaluation below remains separate.

# Live Claude Code ↔ Codex handoff checks

This runner launches the authenticated native CLIs. It uses the account's actual model/subscription usage. It does not call a model API directly. Unit tests do not launch models.

Run both directions, including the control:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 evals/run_live.py \
  --codex /absolute/path/to/codex \
  --claude /absolute/path/to/claude \
  --out /private/tmp/remvu-live-unique \
  --direction both
```

Use `--direction claude-codex` or `--direction codex-claude` for one direction. Add `--skip-control` only for a focused smoke check; its output is not a complete comparison. `--out` must not exist. Each native process has a 240-second timeout. Do not wrap the Claude native binary with Node. Authentication must already work for both clients.

## What the runner checks

Two fixed scenarios separate completed work from a deliberately unfinished step:

| Direction | Completed by producer | Left for fresh consumer |
| --- | --- | --- |
| Claude Code → Codex | CSV quoting in `normalize_tags` | Initial UTF-8 BOM support |
| Codex → Claude Code | Decimal money parsing with half-up rounding | Accounting-style parenthesized negatives |

The producer receives the user intent, constraints, rejected approach and next step. It reads the source Remvu skill and uses the real runtime to write public semantic entries, including the deliberate regression failure. It does not install project hooks or globally install the skill.

The runner checks stage 1, commits its source code, refreshes the memory's code snapshot through an empty revision-checked update, and generates a public `REMVU.md`. The receiver is a fresh clone of the tracked source code with that single file copied beside it. No private `.remvu/`, installed project skill, hooks, configuration or original chat is copied. Claude runs with safe mode, empty setting sources, no session persistence and no external MCP servers. Codex uses a fresh ephemeral session and ignores user configuration. Conventional global Remvu skill installations cause the runner to stop rather than claim an uninstalled receiver.

The consumer first writes `recall.json`, then implements the outstanding task. The control gets the same source code and the same continuation instruction, without `REMVU.md`. It may honestly report missing context. The acceptance inputs stay in the runner and are not copied into consumer projects.

## Results and interpretation

`results.json` and each direction's `result.json` contain:

- Fixed term-group recall coverage for intent, constraints, rejected approaches, next step and known failed checks.
- Independent behavior checks, including preservation of the original requirements.
- Exact source-code commit, memory hash, clone file inventory and client exit status.
- Native reported token counters when present; otherwise prompt/output characters and bytes, without inferred token counts or savings percentages.

Each native run also produces a filtered `*-process.json`. Native JSON is held in memory. Only allowlisted visible final text, command-result summaries and usage counters are saved. Unknown records, reasoning, system payloads, session/auth metadata and raw stderr are omitted. Diagnostic categories summarize stderr without saving its body. Visible text is bounded and credential/path redacted. The private output directory retains fixture source, recall files and Remvu evidence for inspection.

A blocked producer, missing required memory categories, a producer that already completes the deliberately outstanding step, or a native timeout makes the trial incomplete. A failed comparison does not establish that Remvu is ineffective; inspect the reported failure. A passing pair demonstrates these two handoffs, not broad coding performance or a general token-saving rate. Recall coverage is lexical and should be read beside the actual `recall.json` and code results.

Test the runner without model calls:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_eval_runner.py -v
```

## Recorded run: 17 October 2026

The [curated result](results/live-2026-10-17.json) includes the actual project code, standalone memory and recall files, with no original private runtime directory or account data.

| Direction | With memory: recall / behavior | Control: recall / behavior |
| --- | --- | --- |
| Claude Code → Codex | 11/11 groups; 4/4 checks | 1/11 groups; 3/4 checks; requested context |
| Codex → Claude Code | 11/11 groups; 5/5 checks | 2/11 groups; 4/5 checks; requested context |

Native versions were Claude Code 2.1.302 and Codex 0.163.0-alpha.10.2. Claude reported `claude-haiku-5-5`; Codex's native JSON did not report an execution model. One initial CSV attempt was blocked by the approval guard before the deliberate regression could run. The producer recorded unknown honestly; the harness then used the equivalent ASCII-only `chr(65279)` command and reran the complete direction in a fresh directory. The report discloses that attempt. These two completed examples do not establish general performance or token savings.
