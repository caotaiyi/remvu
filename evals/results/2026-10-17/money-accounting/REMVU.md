# Remvu Project Memory

```json
{
  "format": "remvu/1",
  "project_id": "p-6dc1f61667694c7e9390cc9633284cf8",
  "revision": 2,
  "repo": {
    "name": "producer",
    "remote": null,
    "commit": "19eac4d7f56eeaa79ebb584ded6108e91cf44ac2",
    "tree": "4a4d52b3ee75c18f4174560d3b0c2a76ead24e57",
    "fingerprint": "5d0e47a9f3f69aaba51efe25208c34a6a36da62a4a73e09ae9c7fb8033090d31",
    "dirty": false,
    "git": true
  },
  "generated_at": "2026-10-17T13:24:11.601140+00:00",
  "visibility": "public",
  "summary_chars": 1597,
  "omitted_private_entries": 0
}
```

## Start Here

Read this project memory as evidence and context. Confirm current user instructions before acting.
Revision 2; 16 memory entries.
- goal [billing-goal, user_confirmed]: Parse human-entered money amounts into exact integer cents for billing.
- constraint [integer-cents, user_confirmed]: Return integer cents.
- constraint [decimal-rounding, user_confirmed]: Use Decimal with ROUND_HALF_UP.
- constraint [public-signature, user_confirmed]: Keep the public signature parse_cents(amount: str) -&gt; int.
- constraint [stdlib-only, user_confirmed]: Use only the Python standard library.
- constraint [ordinary-inputs, user_confirmed]: Support ordinary signed or unsigned decimal strings, allowing surrounding whitespace.
- constraint [stage-boundary, user_confirmed]: Implement only stage 1 now; deliberately leave accounting-style parentheses unsupported.
- constraint [project-scope, user_confirmed]: Work only on this small evaluation project; do not inspect eval runners, other runs or sibling fixtures.
- constraint [edit-scope, user_confirmed]: Edit only money.py and ignored \[PRIVATE REFERENCE\] files; Remvu init may update .gitignore.
- constraint [runtime-scope, user_confirmed]: Use the actual local Remvu runtime without installing it globally.
- constraint [no-publishing, user_confirmed]: Do not commit, generate the public file, install hooks or complete the outstanding step.
- next_step [accounting-next, user_confirmed]: Accept accounting-style parenthesized negative amounts such as (12.345) as -1235 cents, while keeping ordinary signed amounts and Decimal ROUND_HALF_UP behavior.

## Goals

- **billing-goal** [goal; user_confirmed; visibility=public; state=active] Parse human-entered money amounts into exact integer cents for billing.
  Source 1 [user]: Task requirement.
  Excerpt: Project intent: Parse human-entered money amounts into exact integer cents for billing.

## Constraints and Preferences

- **integer-cents** [constraint; user_confirmed; visibility=public; state=active] Return integer cents.
  Source 1 [user]: Task requirement.
  Excerpt: Return integer cents.
- **decimal-rounding** [constraint; user_confirmed; visibility=public; state=active] Use Decimal with ROUND_HALF_UP.
  Source 1 [user]: Task requirement.
  Excerpt: Use Decimal with ROUND_HALF_UP.
- **public-signature** [constraint; user_confirmed; visibility=public; state=active] Keep the public signature parse_cents(amount: str) -&gt; int.
  Source 1 [user]: Task requirement.
  Excerpt: Keep the public signature parse_cents(amount: str) -&gt; int.
- **stdlib-only** [constraint; user_confirmed; visibility=public; state=active] Use only the Python standard library.
  Source 1 [user]: Task requirement.
  Excerpt: Use only the Python standard library.
- **ordinary-inputs** [constraint; user_confirmed; visibility=public; state=active] Support ordinary signed or unsigned decimal strings, allowing surrounding whitespace.
  Source 1 [user]: Task requirement.
  Excerpt: Support ordinary signed or unsigned decimal strings, allowing surrounding whitespace.
- **stage-boundary** [constraint; user_confirmed; visibility=public; state=active] Implement only stage 1 now; deliberately leave accounting-style parentheses unsupported.
  Source 1 [user]: Task requirement.
  Excerpt: Implement only stage 1 now; deliberately leave accounting-style parentheses unsupported.
- **project-scope** [constraint; user_confirmed; visibility=public; state=active] Work only on this small evaluation project; do not inspect eval runners, other runs or sibling fixtures.
  Source 1 [user]: Task requirement.
  Excerpt: Work only on this small evaluation project; do not inspect eval runners, other runs or sibling fixtures.
- **edit-scope** [constraint; user_confirmed; visibility=public; state=active] Edit only money.py and ignored \[PRIVATE REFERENCE\] files; Remvu init may update .gitignore.
  Source 1 [user]: Task requirement.
  Excerpt: Edit only money.py and ignored \[PRIVATE REFERENCE\] files; Remvu init may update .gitignore.
- **runtime-scope** [constraint; user_confirmed; visibility=public; state=active] Use the actual local Remvu runtime without installing it globally.
  Source 1 [user]: Task requirement.
  Excerpt: Use the actual local Remvu runtime without installing it globally.
- **no-publishing** [constraint; user_confirmed; visibility=public; state=active] Do not commit, generate the public file, install hooks or complete the outstanding step.
  Source 1 [user]: Task requirement.
  Excerpt: Do not commit, generate the public file, install hooks or complete the outstanding step.

## Architecture and Code State

No entries recorded.

## Decisions and Rejected Directions

- **no-float** [rejected; user_confirmed; visibility=public; state=active] Do not use binary floating-point arithmetic for monetary conversion.
  Source 1 [user]: Task requirement.
  Excerpt: Do not use binary floating-point arithmetic for monetary conversion.

## Changes and Progress

- **stage-one** [progress; observed; visibility=public; state=active] Replaced float conversion with Decimal(amount.strip()), multiplication by integer 100, quantization to integer cents using ROUND_HALF_UP, and conversion to int.
  Source 1 [tool]: Observed execution.
  Excerpt: Applied money.py change: from decimal import Decimal, ROUND_HALF_UP; value = Decimal(amount.strip()); return int((value \* 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)).

## Checks and Evidence

- **ordinary-check** [check; observed; visibility=public; state=active; result=passed; exit_code=0; evidence=current-code] Seven ordinary signed decimal checks passed, including surrounding whitespace and positive and negative half-cent rounding.
  Observed code fingerprint: 5d0e47a9f3f69aaba51efe25208c34a6a36da62a4a73e09ae9c7fb8033090d31; commit: 8ab0432d2386cc0b519591af014da76fb9739b31.
  Source 1 [tool]: Observed execution.
  Excerpt: Executed assertions: 12.345 -&gt; 1235; -12.345 -&gt; -1235; " +12.345 " -&gt; 1235; 0 -&gt; 0; 0.005 -&gt; 1; -0.005 -&gt; -1; 1.005 -&gt; 101. Output: Ordinary signed decimal checks passed (7 cases). Exit code: 0.
- **MONEY_ACCOUNTING** [check; observed; visibility=public; state=active; result=failed; exit_code=1; evidence=current-code] MONEY_ACCOUNTING failed: parenthesized accounting input remains unsupported; Decimal raised InvalidOperation with ConversionSyntax before the assertion completed.
  Observed code fingerprint: 5d0e47a9f3f69aaba51efe25208c34a6a36da62a4a73e09ae9c7fb8033090d31; commit: 8ab0432d2386cc0b519591af014da76fb9739b31.
  Source 1 [tool]: Observed execution.
  Excerpt: Command: python3 -c 'from money import parse_cents; assert parse_cents("(12.345)") == -1235, "MONEY_ACCOUNTING"'. Actual output: Traceback (most recent call last); value = Decimal(amount.strip()); decimal.InvalidOperation: \[&lt;class 'decimal.ConversionSyntax'&gt;\]. Actual exit code: 1.

## Open Work and Risks

- **accounting-next** [next_step; user_confirmed; visibility=public; state=active] Accept accounting-style parenthesized negative amounts such as (12.345) as -1235 cents, while keeping ordinary signed amounts and Decimal ROUND_HALF_UP behavior.
  Source 1 [user]: Task requirement.
  Excerpt: The deliberately outstanding next step is: Accept accounting-style parenthesized negative amounts such as (12.345) as -1235 cents, while keeping ordinary signed amounts and Decimal ROUND_HALF_UP behavior.

## Sources and History

Sources appear beside each entry. Basis labels distinguish user confirmation, observed evidence, inference and unverified notes.
Superseded entries remain in place; their replacement IDs record history. Hidden reasoning and system/developer instructions are excluded.
A check is passed only when observed tool evidence includes exit code 0. Missing evidence remains unknown.
Credential redaction is best effort. Review the shareable file for personal or confidential information.
