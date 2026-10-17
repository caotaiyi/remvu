# Memory updates and handoffs

An update proposal is JSON with the current `base_revision`, a reviewed `base_event_count` watermark and an `entries` array. Get both counters with `status --repo PROJECT`; apply it with `update --repo PROJECT --proposal FILE` or `update --repo PROJECT --proposal-json 'JSON'`. These two inputs are mutually exclusive and use the same schema. During a hook-driven update, prefer one standalone `--proposal-json` command: it avoids creating a proposal file that would itself become a new observed edit. Do not combine the memory command with other shell operations.

```json
{
  "base_revision": 0,
  "base_event_count": 0,
  "entries": [
    {
      "id": "keep-csv-interface",
      "kind": "constraint",
      "text": "Keep the CSV column order unchanged.",
      "basis": "user_confirmed",
      "visibility": "public",
      "sources": [
        {
          "type": "user",
          "label": "Task requirement",
          "excerpt": "Keep the CSV column order unchanged.",
          "visibility": "public"
        }
      ]
    }
  ]
}
```

This is a synthetic example. Do not reuse its facts for a real project.

## Entry fields

| Field | Values or behavior |
| --- | --- |
| `id` | Optional stable ID; letters, digits, `.`, `_` or `-`, up to 96 characters. Omission generates a deterministic ID. |
| `kind` | `goal`, `constraint`, `preference`, `architecture`, `decision`, `rejected`, `progress`, `check`, `next_step`, `risk`, `change`. |
| `text` | One nonempty claim, at most 100,000 characters. Keep it much shorter in normal use. |
| `basis` | `user_confirmed`, `observed`, `inferred`, `unverified`. |
| `visibility` | `private` by default; `public` only for selected shareable material. |
| `sources` | Up to 100 sources with `type` and optional `label`, `ref`, `excerpt`, `visibility`. |
| `supersedes` | Existing entry IDs replaced by this statement; history stays available. |
| `result` | For `check` entries: `passed`, `failed`, `unknown`. |
| `exit_code` | Optional observed integer exit code for a check. |

Source types are `user`, `tool`, `file`, `url`, `event` and `legacy`. Sources default to private independently of entry visibility. Public entries require at least one source; every source must be public and have a nonempty inline excerpt. A private path is not a usable public citation. Unknown fields are rejected to prevent silent loss.

Use a check entry for an executed test or an unresolved verification claim. Keep the outcome and source consistent. Record a planned test as `unknown`; do not infer success from the absence of a reported error. Put an unsupported interpretation under `inferred` or `unverified`. Each check retains its recorded code fingerprint. An old pass remains historical after code changes, including when unrelated notes update the project memory. Rerun the check and add a new observed check with `supersedes` to record current validation.

## Storage and concurrency

`.remvu/` holds local memory, recorder data, pending status and retained conflicts. Do not edit its state directly. Writers use revision checks and atomic replacement. `status` is bounded; use `entries --offset 0 --limit 20` to paginate entry previews and `show ID --max-chars 4000` to read one entry or event. These commands also accept `--repo PROJECT`.

Always include the `base_event_count` you reviewed while authoring a proposal. The protocol permits omission for older writers, but omission acknowledges no new events. An update can succeed while leaving newer events pending. Do not replace the saved count with the latest count unless you have reviewed the newly covered evidence.

A stale proposal must be reconciled against newer entries before resubmission; merely changing its revision number can discard another agent's decision. After applying the reconciled update, close the retained conflict explicitly against the current reviewed revision:

```bash
python3 SCRIPT resolve-conflict CONFLICT_ID --repo /path/to/project --base-revision CURRENT_REVISION --note "Reconciled against the current memory." --entry-id RECONCILED_ENTRY_ID
python3 SCRIPT check --repo /path/to/project
```

Repeat `--entry-id` for additional reconciled entries; omit it when the reviewed resolution adds none. The original proposal and resolution are archived together. This command records the resolution; it does not apply the stale proposal. Unresolved conflicts block public sharing.

Claims and sources stay immutable. To narrow previously selected public material, use `withhold ID [ID...] --repo PROJECT --base-revision CURRENT_REVISION --note "Reason"`. The command records the original entry/visibility and note, then makes those entries private. It does not acknowledge events or refresh code/check fingerprints. A withdrawn claim remains in local history; create a new self-contained public summary when needed. Review public entries that refer to a withdrawn ID, because sharing cannot depend on private history. Already generated files remain unchanged.

The generated `REMVU.md` uses `remvu/1` metadata and fixed sections. `Start Here` defaults to 8,000 characters; long entries use explicit pointers to the full statements below. If even those pointers cannot fit, generation fails instead of silently dropping constraints or open work. `check` compares the recorded code state with the current project. A mismatch invalidates assumptions about freshness, not the historical record.
