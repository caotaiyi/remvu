# Installation and maintenance

Use the absolute runtime script path printed by `install`. Python 3.10+ and Git
are prerequisites. If missing, the installing agent should use their official
installers with normal host permissions, then retry. Remvu has no account.

`install --repo PROJECT [--platform both|claude|codex|none]` copies the complete
reviewed skill into a versioned, checksum-indexed user directory:

- macOS: `~/.local/share/remvu/runtimes/`.
- Windows: `%LOCALAPPDATA%/Remvu/runtimes/`.
- `--home DIRECTORY` overrides this location.

Only after copying and verifying the runtime does Remvu initialize the project.
The original clone or extracted ZIP can then move. Direct `init` remains the
v0.2-compatible source-path setup; use `install` for a stable setup. Individual
platform reinitialization retains already-installed platforms. Use uninstall
first to remove an adapter.

Installation preserves configuration and saves a private lifecycle checkpoint.
Changed configurations roll back if installation fails; concurrently recorded
memory is never rolled back. A checkpoint includes the prior state, adapter
manifest and changed instruction/config files, not a second copy of all evidence.
Evidence and journals remain in place. If an entire disk is lost, this checkpoint
alone cannot reconstruct the project; keep your own private backup.

## Health

`doctor --repo PROJECT` reports memory/check freshness, pending work, conflicts,
missing evidence, runtime checksums, prerequisites and local storage bytes.
Configured hooks begin as `awaiting_host_review`. A successfully invoked hook
writes a local receipt; doctor then says `hook_execution_observed`. A synthetic
invocation can also create that receipt. It is not proof of host trust, a
particular client surface, or successful automatic semantic consolidation.
Review the actual hooks normally and finish the native acceptance checklist.

## Upgrade and rollback

Review a new release and extract or clone it outside the project. Then run the
current CLI with `upgrade --repo PROJECT --source NEW/skills/remvu`.
No remote source is downloaded or executed automatically. Review changed hook
definitions in the host. `upgrade --repo PROJECT --rollback` selects the previous
verified managed runtime and regenerates its adapters; semantic memory is retained.
A legacy v0.2 source checkout is checkpointed but cannot be selected as a verified
managed rollback runtime. `remvu/1` and `remvu-state/1` remain compatible in this release.

## Recovery

`repair --repo PROJECT` uses advisory locks in the normal hook/core order.
Locks release automatically when their owning process exits; never delete a
busy lock to force access. Close the active writer and retry.

Corrupt state is restored only from an integrity-checked snapshot with matching
journal and intact referenced evidence. The last five committed copies plus
latest are retained. Recovery backs up the corrupt file, adds a recovery issue,
and leaves semantic consolidation pending. Orphan journals are retained and
never replayed as committed work. If no verified copy exists, repair refuses;
restore a private backup. Missing evidence in otherwise valid state is reported,
not silently removed or reconstructed.

A corrupt hook ledger is backed up and reset, with a persistent recovery issue
and pending memory. Review compact status recovery flags and retained evidence,
use full status only if necessary, record remaining gaps as risks, and apply a
reviewed semantic proposal before creating a fresh handoff. Repair cannot infer
lost work. Old public files are not changed by repair.

Snapshot recovery reserves a revision above all retained journal revisions,
including uncommitted attempts, so an old writer cannot reuse an earlier number
after recovery. Unreadable journal revision metadata prevents safe automatic
recovery; retain the files and restore a verified private backup instead.

Hook failures also leave private observation-gap markers when the filesystem
allows writing them. Doctor reports these gaps and sharing is blocked. Repair
indexes their existence as pending evidence, retaining the marker in a local
reviewable archive. It cannot recover the failed observation. Record unknown
work explicitly rather than clearing a watermark to imply completeness.

Doctor reports actual storage bytes. Evidence and journals are retained rather
than automatically deleted. The active ledger archives older sessions after 100;
individual long sessions and the evidence index can still grow. Large-project
retention/compaction needs beta measurements and is not claimed solved here.

## Diagnostics and uninstall

`diagnose --repo PROJECT --out PROJECT/.remvu/diagnostic-UNIQUE.json` produces
allowlisted versions, capability presence, issue codes, event counts and bytes.
It excludes entries, outputs, paths, remote URLs, session IDs and configuration
bodies. Preview it before submitting an issue; nothing is uploaded automatically.

`uninstall --repo PROJECT` removes unchanged project skill shims, exact registered
hook definitions and managed instruction blocks. It preserves unrelated settings,
edited hooks, private memory, backups, ignore rules and shared runtime versions.
An edited skill shim stops uninstall for review. Restart clients afterward.
Shared runtimes are not automatically deleted because other projects may use them.
