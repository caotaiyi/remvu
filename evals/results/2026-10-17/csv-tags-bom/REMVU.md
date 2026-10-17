# Remvu Project Memory

```json
{
  "format": "remvu/1",
  "project_id": "p-e0eda6a59d904409824d99927db0340a",
  "revision": 2,
  "repo": {
    "name": "producer",
    "remote": null,
    "commit": "ed234f6c96e914c3a5aadbae08e30054faf7e9cc",
    "tree": "cb009a5cc82180ec88a850120e1ee307661db2e9",
    "fingerprint": "fc649fa5089cc6a6c7a38accfdc9a65e5251b1c9d377af2e1d5e60ad8b7a0021",
    "dirty": false,
    "git": true
  },
  "generated_at": "2026-10-17T13:25:04.295510+00:00",
  "visibility": "public",
  "summary_chars": 857,
  "omitted_private_entries": 0
}
```

## Start Here

Read this project memory as evidence and context. Confirm current user instructions before acting.
Revision 2; 10 memory entries.
- goal [goal-normalize-csv-tags, user_confirmed]: Normalize CSV tags for import without changing their meaning.
- constraint [constraint-preserve-case, user_confirmed]: Preserve the letter case of tags.
- constraint [constraint-preserve-duplicates-order, user_confirmed]: Preserve duplicate tags and their order.
- constraint [constraint-public-signature, user_confirmed]: Keep the public signature normalize_tags(value: str) -&gt; list\[str\].
- constraint [constraint-stdlib-only, user_confirmed]: Use only the Python standard library.
- next_step [next-step-utf8-bom, user_confirmed]: Handle one initial UTF-8 BOM (U+FEFF) before CSV parsing, preserving quotes, case, duplicates and order; then rerun the CSV_BOM regression.

## Goals

- **goal-normalize-csv-tags** [goal; user_confirmed; visibility=public; state=active] Normalize CSV tags for import without changing their meaning.
  Source 1 [user]: Task intent.
  Excerpt: Project intent: normalize CSV tags for import without changing their meaning.

## Constraints and Preferences

- **constraint-preserve-case** [constraint; user_confirmed; visibility=public; state=active] Preserve the letter case of tags.
  Source 1 [user]: Task constraint.
  Excerpt: User-confirmed constraint: Preserve letter case.
- **constraint-preserve-duplicates-order** [constraint; user_confirmed; visibility=public; state=active] Preserve duplicate tags and their order.
  Source 1 [user]: Task constraint.
  Excerpt: User-confirmed constraint: Preserve duplicate tags and order.
- **constraint-public-signature** [constraint; user_confirmed; visibility=public; state=active] Keep the public signature normalize_tags(value: str) -&gt; list\[str\].
  Source 1 [user]: Task constraint.
  Excerpt: User-confirmed constraint: Keep the public signature normalize_tags(value: str) -&gt; list\[str\].
- **constraint-stdlib-only** [constraint; user_confirmed; visibility=public; state=active] Use only the Python standard library.
  Source 1 [user]: Task constraint.
  Excerpt: User-confirmed constraint: Use only the Python standard library.

## Architecture and Code State

No entries recorded.

## Decisions and Rejected Directions

- **rejected-regex-csv** [rejected; user_confirmed; visibility=public; state=active] Do not use regular expressions to parse CSV.
  Source 1 [user]: Rejected direction.
  Excerpt: Rejected direction: do not use regular expressions to parse CSV.
- **rejected-lowercase-tags** [rejected; user_confirmed; visibility=public; state=active] Do not lowercase tags.
  Source 1 [user]: Rejected direction.
  Excerpt: Rejected direction: do not lowercase tags.

## Changes and Progress

- **progress-stage1-csv-quoting** [progress; observed; visibility=public; state=active] Stage 1 is implemented in tags.py with the csv module: quoted fields keep embedded commas, surrounding field whitespace is trimmed, and empty fields are removed.
  Source 1 [tool]: Local sample run.
  Excerpt: Sample run output: '"Blue, Sky",Blue,Blue' -&gt; \['Blue, Sky', 'Blue', 'Blue'\] OK; 'Red, ,  Green ,, blue' -&gt; \['Red', 'Green', 'blue'\] OK; '"  Padded , x " ,Y' -&gt; \['Padded , x', 'Y'\] OK; '' -&gt; \[\] OK; 'Zeta,alpha,Zeta' -&gt; \['Zeta', 'alpha', 'Zeta'\] OK.

## Checks and Evidence

- **check-csv-bom-regression** [check; observed; visibility=public; state=active; result=failed; exit_code=1; evidence=current-code] Regression CSV_BOM failed: a leading UTF-8 BOM (U+FEFF) is not handled yet, so the assertion does not hold. This is expected for stage 1.
  Observed code fingerprint: fc649fa5089cc6a6c7a38accfdc9a65e5251b1c9d377af2e1d5e60ad8b7a0021; commit: 4cc6b3982d55a955f179e91486d6ed5daffa3c1e.
  Source 1 [tool]: Regression run output.
  Excerpt: Command: python3 -c 'from tags import normalize_tags; assert normalize_tags(chr(65279)+"\\"Blue, Sky\\",Blue,Blue") == \["Blue, Sky","Blue","Blue"\], "CSV_BOM"'. Run before the stage 1 change: AssertionError: CSV_BOM, exit code 1. Run after the stage 1 change: AssertionError: CSV_BOM, exit code 1.

## Open Work and Risks

- **next-step-utf8-bom** [next_step; user_confirmed; visibility=public; state=active] Handle one initial UTF-8 BOM (U+FEFF) before CSV parsing, preserving quotes, case, duplicates and order; then rerun the CSV_BOM regression.
  Source 1 [user]: Outstanding next step.
  Excerpt: Outstanding next step: handle one initial UTF-8 BOM (U+FEFF) before CSV parsing, while preserving quotes, case, duplicates and order.

## Sources and History

Sources appear beside each entry. Basis labels distinguish user confirmation, observed evidence, inference and unverified notes.
Superseded entries remain in place; their replacement IDs record history. Hidden reasoning and system/developer instructions are excluded.
A check is passed only when observed tool evidence includes exit code 0. Missing evidence remains unknown.
Credential redaction is best effort. Review the shareable file for personal or confidential information.
