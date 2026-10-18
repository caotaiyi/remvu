# Markdown product validation

This report covers the new explicit save/resume skill. The historical strict-engine matrix remains in [compatibility](compatibility.md). The beta is still a candidate.

## Local mechanics

The local macOS Python 3.9 test run passed: 165 discovered, 164 passed and one Windows-only skip. Two new tests install the skill into a fresh directory with no Python binary in the installer's PATH and reject existing/symlinked skill targets. This is an installer-mechanics check, not native slash-command or GUI certification. Python is used to run developer tests only.

The main skill uses host file tools and installs no hooks. The optional engine Stop callback now returns without a blocking decision, while pending evidence and observation-gap protections remain. Existing preservation, recovery, privacy and concurrency tests passed. The latest previously published CI result predates this change; a new run is required before citing CI for it.

## Real native pilot

[Two-task pilot measurements](../evals/results/markdown-pilot-2026-10-18.json) preserve one setup failure: Claude Code refused a .git/info/exclude edit, and the producer did not save private content without protection. In the other task, both ordinary HANDOFF.md and Remvu receivers completed all five behavior cases on their first attempt. The Remvu file was 4,212 bytes versus 814 bytes for the ordinary handoff; receiver times were 9.574 and 8.974 seconds respectively. This small trial shows no advantage in speed or size.

The workflow now uses a regular project .gitignore rule before writing private notes, and the note template is shorter. Those changes require a new run. The pilot has not been discarded or relabeled as passed.

## Ten-task comparison

[Protocol and stopping rules](../evals/markdown-protocol.md). The native ten-task run is in progress. Report actual paired outcomes, bytes, corrections and usage without inferring a savings percentage. Keep setup failures and both failed and successful cases. Full provider records and private notes are not published.

## Not yet established

Native Windows PowerShell installation, terminal skill discovery, desktop and VS Code entry points, long-term multi-session use, simultaneous Markdown writers and enforced content fingerprints are not certified. Markdown editing cannot promise the strict engine's transactional guarantees. Hidden reasoning is excluded. No cost or token reduction is established.
