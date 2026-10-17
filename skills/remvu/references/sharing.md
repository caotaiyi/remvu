# Public sharing

`share` creates a local public document. It does not authorize a Git commit, push, message or upload.

Before sharing, review the selected entries and all their inline sources. Include the facts the receiver needs to continue, with enough context to distinguish user intent from agent inference. Keep private raw logs, credentials, personal paths, unrelated requests and attachment references out of the public file. Resolve retained conflicts explicitly and consolidate reviewed events through their recorded watermark; either remaining condition blocks public sharing.

When code has changed since the recorded state, refresh memory and repeat the relevant checks. Sharing stops when tracked or untracked changes exist. The preferred path is to commit the intended project changes using the project's normal workflow.

If the user explicitly chooses to carry uncommitted work:

```bash
python3 SCRIPT share --repo /path/to/project --out /path/to/REMVU.md --include-patch
python3 SCRIPT validate /path/to/REMVU.md
```

Inspect the included tracked diff. A patch may contain secrets, private comments or unrelated edits even when the memory entries are public. Untracked and ignored contents are not carried by the tracked patch; list any required unavailable resources. A receiver should review a patch before applying it and verify code state afterward.

Common-secret detection and home-path redaction cannot establish that arbitrary text is safe to publish. If a required source cannot be shared, keep its claim private or state that the public receiver cannot verify it. Never replace unavailable evidence with an invented excerpt.

A final response should name the file, relevant exclusions and material gaps. Claims about actual tests, remote CI, live hook execution or token savings require their own observations.
