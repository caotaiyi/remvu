# A cross-agent handoff in 30 seconds

The intended demonstration shows one real task moving between Claude Code and Codex. A receiver gets the project code and `REMVU.md`; it has no original chat and no Remvu installation. Live acceptance results belong in the [validation report](validation-report.md).

## Recording sequence

| Time | Screen action |
| --- | --- |
| 0-6 seconds | Show the source agent's task and the constraint it must preserve. |
| 6-12 seconds | Run `/remvu share` or `$remvu share`; show the generated document's goal, code state and unfinished step. |
| 12-22 seconds | Switch to a fresh receiver with only code and the file. Ask it to read `REMVU.md` and complete that step. |
| 22-30 seconds | Show the resulting code and executed check, then the preserved constraint or avoided rejected direction. |

Display the real elapsed time for any model work omitted by editing. A 30-second recording is a compact presentation, not a claim that the full task takes 30 seconds. Do not stage synthetic output as a real client result.

For a local format walkthrough, use [the synthetic conformance example](../examples/remvu/). It demonstrates the file structure and validator only. The real recording and its evidence can be added after both live handoff directions pass.
