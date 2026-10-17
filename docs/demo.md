# A 30-second replay of real handoffs

![Evidence replay of the native Claude Code and Codex results](assets/remvu-live-replay.gif)

This animation replays recorded results from two actual native-CLI handoffs on 2026-10-17. It is not an original screen recording. Its 30-second presentation is shorter than the model executions, whose actual elapsed times appear in the replay and below.

| Direction and task | Producer | Receiver with memory | Control without memory |
| --- | --- | --- | --- |
| Claude Code to Codex: CSV tags and initial BOM | 52.734 s | 36.642 s; 11/11 recall term groups, 4/4 behavior checks | 23.042 s; stopped for missing context, 1/11 recall, 3/4 baseline checks |
| Codex to Claude Code: exact money and accounting negatives | 59.362 s | 37.901 s; 11/11 recall term groups, 5/5 behavior checks | 22.093 s; stopped for missing context, 2/11 recall, 4/5 baseline checks |

Each receiver had project code and Git history; the memory arm additionally received one `REMVU.md`. No original chat, private memory, project Remvu installation or hidden acceptance tests were copied. Both arms received the same continuation instruction. Recall scores use fixed lexical term groups; the behavior checks test the produced code independently.

The controls left the deliberately unfinished step incomplete, so their shorter runs do not measure equivalent completed work. These two examples establish functional handoff results, not a general coding benchmark or a token-saving rate.

## Inspect or reproduce

The [safe result JSON](../evals/results/live-2026-10-17.json) contains client versions, native usage counters, file hashes, code checks and reviewed visible excerpts. The linked result directories contain the actual stage-one code, completed code, handoff and recall files. Raw private sessions are excluded.

The [replay manifest](assets/remvu-live-replay.json) records the animation and source-report hashes. Rendering uses the optional development dependency Pillow. Rebuild it from the report with:

```bash
python3 evals/render_demo.py
```

Reproduce the model trial with [the live evaluation runner](../evals/README.md). It requires authenticated native clients and consumes the accounts' real model/subscription usage. The [validation report](validation-report.md) separates these handoffs from lifecycle-hook observations and local regression tests.
