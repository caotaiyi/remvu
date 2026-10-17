# Validation report

Date: 2026-10-17 (Asia/Singapore). Reference implementation: `0.2.0`. Open format proposal: `remvu/1`.

Two real handoffs passed with fresh receivers. Local regression tests and client-hook observations are reported separately below. The public [machine-readable result](../evals/results/live-2026-10-17.json) includes native usage counters, code checks, file hashes and reviewed excerpts.

## Cross-agent handoffs

The receiver had tracked project code, `.gitignore` and Git history. The memory arm additionally received one `REMVU.md`. No original chat, private `.remvu/`, project skill installation, hook configuration or hidden acceptance tests were copied. Both arms received the same continuation instruction in fresh sessions.

| Direction and task | Condition | Context term groups | Behavior checks | Receiver time |
| --- | --- | --- | --- | --- |
| Claude Code to Codex: CSV tags and initial BOM | With memory | 11/11 | 4/4 | 36.642 s |
| Same baseline and instruction | Without memory | 1/11 | 3/4 | 23.042 s |
| Codex to Claude Code: exact cents and accounting negatives | With memory | 11/11 | 5/5 | 37.901 s |
| Same baseline and instruction | Without memory | 2/11 | 4/5 | 22.093 s |

Both controls wrote `needs_context: true` and stopped before implementing the outstanding step. Their passing cases come from the producer's existing baseline. The completed receivers preserved those cases and fixed the deliberately failing next-step regression.

Recall uses fixed lexical term groups for intent, constraints, rejected directions, next step and known failed checks. It measures term coverage, not general semantic understanding. The code checks are independent behavior assertions. These are two functional examples, without repeated-trial statistics or a general coding-performance claim.

Claude Code was version `2.1.302` and reported `claude-haiku-5-5` in native model usage. Codex was `0.163.0-alpha.10.2`; its native JSON did not report a model name. Producers took 52.734 s for the CSV task and 59.362 s for the money task. The handoff files were 5,664 and 8,503 characters respectively; these counts cover the whole files, including detail sections.

Inspect the actual artifacts:

- CSV: [handoff](../evals/results/2026-10-17/csv-tags-bom/REMVU.md), [producer code](../evals/results/2026-10-17/csv-tags-bom/stage1.py), [completed code](../evals/results/2026-10-17/csv-tags-bom/completed.py), [with-memory recall](../evals/results/2026-10-17/csv-tags-bom/with-memory-recall.json), [control recall](../evals/results/2026-10-17/csv-tags-bom/without-memory-recall.json).
- Money: [handoff](../evals/results/2026-10-17/money-accounting/REMVU.md), [producer code](../evals/results/2026-10-17/money-accounting/stage1.py), [completed code](../evals/results/2026-10-17/money-accounting/completed.py), [with-memory recall](../evals/results/2026-10-17/money-accounting/with-memory-recall.json), [control recall](../evals/results/2026-10-17/money-accounting/without-memory-recall.json).

The first CSV producer attempt was blocked by the native approval guard because a regression command contained Unicode whitespace. It was changed to the equivalent ASCII-only `chr(65279)` expression and the complete direction was rerun in a fresh directory. That blocked attempt is disclosed in the JSON and excluded from the passing comparison counts.

## Native usage

The following counters are copied from the completed native result records. Provider fields have different meanings; they are not converted into a shared token estimate. The full report also retains producer counters and character/byte measurements.

Codex CSV receiver:

| Condition | `input_tokens` | `cached_input_tokens` | `output_tokens` |
| --- | --- | --- | --- |
| With memory | 128582 | 98816 | 1078 |
| Without memory | 97996 | 72960 | 568 |

Claude Code money receiver, using the top-level `result` counters:

| Condition | `input_tokens` | `cache_creation_input_tokens` | `cache_read_input_tokens` | `output_tokens` |
| --- | --- | --- | --- | --- |
| With memory | 18 | 11531 | 103434 | 6239 |
| Without memory | 10 | 4028 | 34661 | 1815 |

Claude's top-level and per-model counters overlap and must not be added together. The controls stopped for missing context, so their smaller counts do not measure equivalent completed work. No token-saving percentage, cost reduction or repeated-investigation reduction is claimed. Runtime scripts make no model API calls; semantic updates and receiver reads still consume the active agent's context.

## Implementation checks

| Check | Observed result | Evidence |
| --- | --- | --- |
| Complete local regression suite | 108 passed in the earlier complete run; final release rerun pending | `python3 -m unittest discover -s tests -v` on macOS system Python 3.9.6 |
| Format conformance | Seven cases passed with strict JSON Schema validation | `python3 spec/validate_examples.py --require-jsonschema` |
| Skill validation | Official skill validator passed | Remvu frontmatter and metadata validation |
| Public handoff integrity | Both real handoffs and all published artifact hashes verified | Artifact records in the live JSON |
| Repository migration | Rename, old URL 301 redirect and retained `v0.1.0` verified | [Remvu repository](https://github.com/caotaiyi/remvu) |
| Remote CI first run | Four Linux/macOS jobs passed; two Windows jobs failed, fix and rerun pending | [Run 39036609097](https://github.com/caotaiyi/remvu/actions/runs/39036609097) |

The declared minimum is Python 3.10. The local system Python 3.9.6 run does not replace checks of the supported range. CI targets Python 3.10 and 3.12 on Linux, macOS and Windows. New regression cases cover stale check evidence, event-review watermarks, retained conflicts and explicit resolution, cold receiver checks and strict metadata.

The first Windows jobs exposed three issues: Git text checkout line endings changed a code fingerprint, the legacy CLI used cp1252 for Chinese output, and a hook fixture executed its POSIX command instead of its Windows branch. The fixes constrain normalization to Git-authorized text, use UTF-8 standard streams for CLI/hooks, and exercise `commandWindows` with Chinese paths and content. The first failing run remains linked above; the follow-up remote result will be recorded separately.

## Lifecycle hooks

Both native clients activated hooks in temporary test projects on macOS arm64, using their normal trust/account controls and no bypass flags. The [curated hook report](../evals/live-hooks-report.json) records the exact commands, observations, native usage and limitations. Startup canaries, real file edits and assertions were observed; call/result events and session-end delivery were recorded.

| Client | Initial natural run | Explicit skill-guided continuation | Stop repair requests, initial / guided | Final handoff check |
| --- | --- | --- | --- | --- |
| Claude Code 2.1.302 | Pending, 8/17 events reviewed | Clean, 24/24 reviewed; memory and handoff revision 4 | 1 / 1 | Exit 0, no issues |
| Codex 0.163.0-alpha.10.2 | Pending, 7/9 events reviewed | Clean, 22/22 reviewed; memory and handoff revision 3 | 1 / 0 | Exit 0, no issues |

The initial natural runs left events pending because compound bookkeeping and proposal operations created observations beyond their reviewed watermark. That outcome remains in the report. The documented guided path completed in both clients without a further user prompt during either run. Claude retained an actual failed pre-consolidation check alongside its passing task recheck; Codex retained its observed passing recheck with tool evidence.

These results establish native activation, bounded repair in the observed sessions and working skill-guided consolidation. They do not establish unattended consolidation reliability for arbitrary tasks. Native compaction and interruption were not exercised, and native hooks were not tested on Windows or Linux. Codex emitted a nonfatal error item and stderr in both smoke sessions; their bodies were excluded by the capture allowlist, so this is not an error-free bootstrap claim.

Windows shell commands deliberately remain recorded instead of being guessed to be bookkeeping. This can preserve pending events for review; native Windows automatic clean consolidation is unsupported. Its CLI/core and UTF-8 transport checks are separate from the macOS native-client observations.

## Reproduce and review

Use [the live evaluation runner](../evals/README.md) for the two fixed handoffs. It requires authenticated native clients and uses real account model/subscription usage. The [30-second evidence replay](demo.md) compresses the presentation and shows actual run times; it is not an original screen recording.

Only synthetic fixtures and reviewed task artifacts are public. Raw provider JSON, hidden reasoning, account/session/auth data and original private runtime directories are excluded. Public generation, dirty-tree refusal, explicit tracked-patch inclusion, missing-resource reporting and conflict handling are covered separately in the regression suite.
