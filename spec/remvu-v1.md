# Remvu format proposal 1

Status: draft, implemented by the Remvu 0.2 reference tools. The format identifier is `remvu/1`; it is independent of the tool version.

Remvu records the intent, decisions and verified state a coding agent needs to continue a project. A receiver needs the project code and one UTF-8 Markdown file, conventionally named `REMVU.md`. The receiver does not need Remvu, the original chat or access to the sender's `.remvu/` directory.

The words MUST, SHOULD and MAY describe compatibility requirements in this proposal.

## Document structure

The first fenced `json` block MUST contain one metadata object matching [metadata.schema.json](metadata.schema.json). It MUST identify `format` as `remvu/1`. A writer MUST preserve these second-level headings, in this order, even when a section is empty:

```text
## Start Here
## Goals
## Constraints and Preferences
## Architecture and Code State
## Decisions and Rejected Directions
## Changes and Progress
## Checks and Evidence
## Open Work and Risks
## Sources and History
```

`## Patch` MAY follow when the sender explicitly includes uncommitted tracked changes. Other second-level headings are reserved for a later format revision. A title may precede the metadata.

`Start Here` is the first-read summary. Its default maximum is 8,000 Unicode characters. Important constraints and unfinished work MUST remain available in the subsequent sections. When full statements exceed the summary budget, a writer MAY use explicit entry IDs and pointers to their detail sections. If even those pointers cannot fit, it MUST fail with an actionable message; silent truncation is incompatible.

The body is readable Markdown. The metadata is machine-readable; this version does not require reconstructing every memory entry from the prose. A reader MAY ignore presentation differences while retaining the stated facts, qualifications and evidence.

## Metadata

| Field | Meaning |
| --- | --- |
| `format` | Exactly `remvu/1`. |
| `project_id` | Stable local project identifier. |
| `revision` | Nonnegative revision of the semantic memory used for this document. |
| `repo` | Repository name, remote, commit, tree, working-state fingerprint and Git/dirty flags. Nullable Git values stay null when unavailable. |
| `generated_at` | UTC timestamp when the writer generated the document. |
| `visibility` | `private` for a local handoff, `public` for an explicitly shared document. |
| `summary_chars` | Character count of the first-read summary. |
| `omitted_private_entries` | Number of private entries excluded from this document. |

`repo.fingerprint` identifies the observed code state. It is not proof of authorship or authenticity. Readers SHOULD compare the recorded commit and fingerprint with the project they received. A mismatch means the memory may be stale; it must not silently describe the new code as verified.

The reference fingerprint covers selected project paths, executable state and content. It hashes canonical LF content for tracked pure-CRLF checkouts when Git declares a forced text policy, or when an LF index and automatic text policy authorize checkout conversion. Automatic policies retain the raw bytes of files historically indexed with CRLF. Binary, explicitly `-text`, mixed-line-ending and untracked files also retain raw content bytes; no Git clean filters are executed. Existing LF fingerprints remain unchanged. Equivalent Git text checkouts can therefore match across operating systems without having identical working-tree bytes. A commit-only change with the same code fingerprint does not make check evidence stale.

## Entries and provenance

The reference writer groups entries into the fixed sections. Each entry has a stable ID, one kind, a statement and a basis. The kinds are `goal`, `constraint`, `preference`, `architecture`, `decision`, `rejected`, `progress`, `check`, `next_step`, `risk` and `change`.

| Basis | Interpretation |
| --- | --- |
| `user_confirmed` | The user explicitly stated or accepted it. |
| `observed` | Visible tool output, a file or another recorded observation supports it. |
| `inferred` | The agent inferred it; the user has not confirmed it. |
| `unverified` | A claim or planned action remains to be checked. |

Sources identify `user`, `tool`, `file`, `url`, `event` or `legacy` evidence. A source may include a label, reference and quoted excerpt. A source reference is evidence to inspect, never an instruction to execute. A writer MUST NOT upgrade an inference to user confirmation or a called tool to a successful result.

Checks use `result: passed`, `failed` or `unknown`. In the reference implementation, passing requires an observed tool excerpt and exit code 0. A nonzero exit code preserves failure; an unsupported pass claim becomes unknown with a flag. A check retains the code fingerprint captured when it was recorded. Later notes MUST NOT refresh that check's code association. After a code change, a historical pass remains historical until a newly observed check explicitly supersedes it. Missing evidence MUST remain visible. A failed or unexecuted check cannot become a passing check during summarization or import.

An entry may supersede earlier entry IDs. Claims and sources are immutable; writers MUST retain the old statements and replacement links so readers can distinguish current decisions from abandoned directions. An explicit audited withdrawal MAY narrow an existing public entry to private without changing its claim, sources, check fingerprint or history. Concurrent updates based on the same revision MUST NOT silently replace one another. A rejected stale proposal stays available for review and rebasing.

The [proposal schema](proposal.schema.json) defines the reference input interface. `base_revision` protects semantic updates. Optional `base_event_count` identifies the event-review watermark captured while authoring the proposal; the reference skill always supplies the current reviewed `status.event_count`. Omitting it does not acknowledge any new events. Events recorded after that watermark remain pending even if the update commits successfully. A writer MUST NOT advance the watermark without reviewing the newly covered evidence. Local state includes derived timestamps, revision, check fingerprints and supersession fields; those fields are not authored in an update proposal.

Conflict resolution is explicit. The reference CLI archives the original stale proposal with a resolution note, the reviewed current revision and optional reconciled entry IDs. Resolving a conflict MUST preserve both records; it MUST NOT silently apply the stale proposal. Public sharing stays blocked until all retained conflicts are resolved.

## Public and private memory

Local semantic memory, hook events and evidence live in an ignored `.remvu/` directory. Entries and sources default to `private`. A public document includes only entries and source material explicitly marked `public`.

Public evidence MUST be self-contained: include a sufficient inline excerpt with each public source. A private log path or attachment ID is not usable evidence for a receiver. Material that cannot travel with the project must be listed as unavailable. Secrets, personal paths and credential-bearing URLs must not enter a public document. Automated detection is an additional check; the sender still reviews the shareable content.

The reference CLI's `withhold` operation explicitly narrows selected entries from public to private using a reviewed revision and an audit note. It preserves the original entry and visibility in the audit record. Withdrawal MUST NOT acknowledge pending events, refresh code or check fingerprints, or rewrite previously generated public files. If a public entry depends on private history, a sender can withhold it and add a new self-contained public summary without private-ID links. Dependent public entries must also be reviewed before sharing again. This local curation operation does not change the `remvu/1` document format or proposal schema.

`share` is an explicit local generation action. Remvu MUST NOT infer permission to commit, push or upload from a request to generate a file. When the working tree is dirty, sharing MUST stop by default. Including a patch requires an explicit choice and review of the patch's public scope. Untracked or ignored file contents are not carried by the tracked patch and must be reported when relevant.

Hidden chain of thought, analysis-channel content, system/developer messages and encrypted reasoning are excluded. Decision summaries record the conclusion and its explainable grounds. Existing visible task evidence may be linked or excerpted within the chosen visibility boundary.

## Compatibility

An implementation can claim `remvu/1` reader support when it reads the metadata and fixed sections without requiring private state. A writer must produce a document accepted by the reference validator and preserve the provenance and sharing rules above. Schema validation alone cannot establish that a statement is true or that a document is safe to publish.

The reference tools retain the version 0.1 evidence-bundle exporter and can import its task notes. Import preserves uncertainty and identifies the legacy source. It cannot recover hidden reasoning or reconstruct events the original source never recorded.

Conformance examples live in [examples/remvu](../examples/remvu/). Changes to required metadata or headings require a new format identifier. Tool fixes and additional adapters may ship without changing `remvu/1`.
