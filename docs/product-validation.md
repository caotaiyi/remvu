# Markdown product validation

This report covers the new explicit save/resume skill. The historical strict-engine matrix remains in [compatibility](compatibility.md). The beta is still a candidate.

## Local mechanics

The local macOS Python 3.9 test run passed: 167 discovered, 166 passed and one Windows-only skip. Two new tests install the skill into a fresh directory with no Python binary in the installer's PATH and reject existing/symlinked skill targets. This is an installer-mechanics check, not native slash-command or GUI certification. Python is used to run developer tests only.

The main skill uses host file tools and installs no hooks. The optional engine Stop callback now returns without a blocking decision, while pending evidence and observation-gap protections remain. Existing preservation, recovery, privacy and concurrency tests passed. The first new [CI run](https://github.com/caotaiyi/remvu/actions/runs/39135848723) passed the six Linux/macOS jobs but failed Windows tests that decoded UTF-8 skill text with the system default cp1252 codec. The affected tests now explicitly read and write UTF-8; this preserves their original assertions. A new cross-system run is required before citing Windows success.

## Real native pilot

[Two-task pilot measurements](../evals/results/markdown-pilot-2026-10-18.json) preserve one setup failure: Claude Code refused a .git/info/exclude edit, and the producer did not save private content without protection. In the other task, both ordinary HANDOFF.md and Remvu receivers completed all five behavior cases on their first attempt. The Remvu file was 4,212 bytes versus 814 bytes for the ordinary handoff; receiver times were 9.574 and 8.974 seconds respectively. This small trial shows no advantage in speed or size.

The workflow now uses a regular project .gitignore rule before writing private notes, and the note template is shorter. Those changes require a new run. The pilot has not been discarded or relabeled as passed.

## Ten-task comparison

[Protocol and stopping rules](../evals/markdown-protocol.md). The native ten-task run completed in both directions (five tasks per direction). Receivers had only the synthetic code and one handoff file; no Remvu runtime was installed. [Measurements and actual usage](../evals/results/markdown-ten-2026-10-18.json) · [All twenty final code files](../evals/results/markdown-ten-final-code-2026-10-18.json).

| Measure | Ordinary HANDOFF.md | Remvu Markdown |
| --- | ---: | ---: |
| First-attempt tasks passing all fixed cases | 9/10 | 9/10 |
| Tasks passing after at most one correction | 10/10 | 10/10 |
| Evaluator-requested correction rounds | 1 | 1 |
| Sum of receiver elapsed seconds, including corrections | 203.805 | 184.128 |
| Sum of handoff bytes | 10,039 | 34,614 |
| Rejected shortcuts seen in final code review | 0 | 0 |

Both arms failed the same internal-BOM case initially and passed after actual failing-case feedback. That fixture has an underspecified boundary: its accepted starting trim() removes internal U+FEFF, but the fixed rubric preserves it. This correction is not evidence of lost project memory. The frozen fixture and raw result remain visible rather than being silently changed after the run. Final-source review does not measure discarded or attempted approaches. Native usage counters are kept per call; overlapping provider counter views are not summed. Producer usage covers both handoffs jointly and cannot establish the cost of one save.

This run found equal completion and correction outcomes, with larger Remvu files. The measured elapsed totals are one synthetic run with varying native model defaults, caching and two workers; they are not evidence of a speed or token-saving advantage. Task times overlap and these sums are not experiment wall time. Do not promote the timing difference as a savings claim. For a simple task where HANDOFF.md already preserves the required context, this experiment shows no completion benefit from adopting Remvu.

The main product improvement is reduced installation friction and an explicit handoff convention. Its value for long-running projects, source fidelity and repeated sessions still needs suitable tests. Full provider records and private notes are not published.

## Not yet established

Native Windows PowerShell installation, terminal skill discovery, desktop and VS Code entry points, long-term multi-session use, simultaneous Markdown writers and enforced content fingerprints are not certified. Markdown editing cannot promise the strict engine's transactional guarantees. Hidden reasoning is excluded. No cost or token reduction is established.
