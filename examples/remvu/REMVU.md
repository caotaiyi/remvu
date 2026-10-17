# Remvu Project Memory

```json
{
  "format": "remvu/1",
  "project_id": "p-synthetic-example",
  "revision": 1,
  "repo": {
    "name": "synthetic-csv-project",
    "remote": null,
    "commit": null,
    "tree": null,
    "fingerprint": "bd211f3cbbbcf294db2ff990a10ddb0dcc03534bdeeefdc702c37ba968f4af07",
    "dirty": false,
    "git": false
  },
  "generated_at": "2026-10-17T00:00:00+00:00",
  "visibility": "public",
  "summary_chars": 501,
  "omitted_private_entries": 1
}
```

## Start Here

Read this project memory as evidence and context. Confirm current user instructions before acting.
Revision 1; 6 memory entries.
- goal [goal-csv-totals, user_confirmed]: Extend the CSV report with a total column.
- constraint [keep-column-order, user_confirmed]: Preserve the order and names of the existing CSV columns.
- next_step [next-implement-totals, unverified]: Implement the total column and rerun the relevant checks; preserve the recorded failure until a new observed result supersedes it.

## Goals

- **goal-csv-totals** [goal; user_confirmed; visibility=public; state=active] Extend the CSV report with a total column.
  Source 1 [user]: Synthetic task.
  Excerpt: Add a total column to the CSV report.

## Constraints and Preferences

- **keep-column-order** [constraint; user_confirmed; visibility=public; state=active] Preserve the order and names of the existing CSV columns.
  Source 1 [user]: Synthetic task.
  Excerpt: Keep the existing CSV columns in their current order.

## Architecture and Code State

- **inferred-small-input** [architecture; inferred; visibility=public; state=active] The current reader appears intended for small reports; the user has not confirmed a size limit.
  Source 1 [file]: Synthetic baseline (report.py).
  Excerpt: def rows(items): return list(items)

## Decisions and Rejected Directions

- **reject-streaming-rewrite** [rejected; user_confirmed; visibility=public; state=active] Do not repeat the proposed streaming rewrite in this task; the user asked for the smaller CSV change.
  Source 1 [user]: Synthetic decision.
  Excerpt: Keep this change small. Do not replace the reader with the proposed streaming design.

## Changes and Progress

No entries recorded.

## Checks and Evidence

- **observed-old-check-failed** [check; observed; visibility=public; state=active; result=failed; exit_code=1; evidence=current-code] The synthetic test for the total column failed before the implementation was added. This is example evidence, not a real repository test result.
  Observed code fingerprint: bd211f3cbbbcf294db2ff990a10ddb0dcc03534bdeeefdc702c37ba968f4af07; commit: unavailable.
  Source 1 [tool]: Synthetic test output.
  Excerpt: python -m unittest test_report: FAIL: total column missing; exit code 1 (synthetic)

## Open Work and Risks

- **next-implement-totals** [next_step; unverified; visibility=public; state=active] Implement the total column and rerun the relevant checks; preserve the recorded failure until a new observed result supersedes it.
  Source 1 [user]: Synthetic remaining work.
  Excerpt: The total column still needs implementation and a test run.

## Sources and History

Sources appear beside each entry. Basis labels distinguish user confirmation, observed evidence, inference and unverified notes.
Superseded entries remain in place; their replacement IDs record history. Hidden reasoning and system/developer instructions are excluded.
A check is passed only when observed tool evidence includes exit code 0. Missing evidence remains unknown.
Credential redaction is best effort. Review the shareable file for personal or confidential information.
