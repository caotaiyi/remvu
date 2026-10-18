# Paired Markdown handoffs, protocol 1

The frozen task input is [markdown-tasks.json](markdown-tasks.json). Ten small JavaScript maintenance tasks cover preserved false/zero values, duplicates, opaque IDs, newline boundaries, redaction without mutation and rejected shortcuts. The public fixture cases are held outside receivers' working directories during a run. Reading this public repository could expose the rubric; a receiver is instructed to use only its supplied project and note. This is process isolation by instruction, not an OS-enforced information barrier.

A native producer receives an accepted starting implementation, the next requested change, durable constraints, rejected directions and a truthful evaluator result. It writes an ordinary HANDOFF.md first, then uses the Markdown Remvu skill to save a note. Code must remain unchanged. Missing documents or changed source are setup failures. They are retained, not replaced with fabricated successes.

Two fresh receivers get identical starting code and the same next-feature prompt. Each receives exactly one HANDOFF.md: one ordinary, one Remvu note. Neither has Remvu, producer private state or original conversation. The receiver can run Node for project checks; no Remvu runtime is installed. Alternate task directions Claude→Codex and Codex→Claude; alternate arm order. Client-selected model IDs and native usage counters are retained, because defaults can vary.

Evaluate the first result against fixed behavioral cases, including input immutability. If checks fail and the CLI returned success, allow one fresh-session correction with the actual failed inputs/expected outputs, identically for both arms. Record before/after case counts, corrective rounds, failure/timeouts, elapsed receiver time, handoff bytes and actual native usage. One correction is a stopping rule, not permission to hide residual failures. Declared CLI completion without behavioral success is not task completion.

`repair_rounds` counts evaluator-requested corrections, not all internal rework. Final code and visible output can be reviewed for rejected approaches; this runner does not claim to measure how often an agent considered or tried them. Hidden reasoning is never requested or recorded. Model-reported final claims are not the behavioral judge.

Setup usage covers both document types jointly and cannot isolate Remvu save cost. Report it separately from receiver usage. Provider `result` and `modelUsage` counters overlap and must not be added together. Do not equate cached/uncached input, sum unlike provider counters, infer tokens from bytes, or extrapolate savings from a single sample. Task-level paired outcomes matter more than pooled headline percentages.

This task set is small and synthetic, with one observation per condition. It tests useful handoff mechanics, not large-project reliability, real quota exhaustion, GUI support or long-term memory quality. Plain HANDOFF.md may be equally effective or smaller. Report that result if observed.

Developer execution uses Python and Node; the installed skill does not:

```sh
python3 evals/run_markdown.py --codex /path/to/codex --claude /path/to/claude --out /private/tmp/remvu-markdown-unique --workers 2
```

The first two-task pilot failed to save one note because `.git/info/exclude` was protected. The other task passed in both arms, with a larger Remvu note. Preserve that pilot separately. The revised workflow uses ordinary `.gitignore` edits before private writes and a shorter note template; its results are a new run, not a replacement for the failed pilot.

Postrun limitation: the labels-bom fixture underspecifies its internal-U+FEFF boundary relative to the accepted trim() implementation. Both arms needed that boundary clarified. Keep its outcome, but do not interpret that correction as a memory-retention failure. A future task-set revision should state the boundary explicitly and use a new manifest hash.
