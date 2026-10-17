# Validation report

Release candidate: `0.2.0-rc.1`. Format proposal: `remvu/1`.

This file separates tests of the local implementation from observations in actual agent clients. Results must name the command or task, environment and outcome. Pending rows are release requirements, not passing checks.

## Implementation checks

| Check | Status | Evidence |
| --- | --- | --- |
| Legacy regression suite | Pending final combined run | `python3 -m unittest discover -s tests -v` |
| Memory, provenance and concurrent updates | Pending final combined run | New core tests in the same suite |
| Hook installation and synthetic lifecycle payloads | Pending final combined run | Adapter tests in the same suite |
| Valid and invalid format examples | Six reference CLI cases passed | `python3 spec/validate_examples.py`; optional JSON Schema package not installed locally |
| Skills and package metadata | JSON parsed; YAML parsed with Ruby; name/subtitle/invocation checks passed | Official skill validator pending because local Python lacks PyYAML |
| Remote CI across matrix targets | Pending remote run | Link the actual GitHub Actions run |

## Live client acceptance

| Scenario | Status | Observation to record |
| --- | --- | --- |
| Codex hooks accepted and executed | Pending | Client version, trust action, startup/tool/stop events observed |
| Claude Code hooks accepted and executed | Pending | Client version, trust action, startup/tool/stop events observed |
| Claude Code to Codex handoff | Pending | Source task, code revision, received document, isolated receiver result |
| Codex to Claude Code handoff | Pending | Source task, code revision, received document, isolated receiver result |
| Stop repair remains bounded | Pending live observation | One repair request and visible pending state if repair fails |

The real handoff receiver must have project code and `REMVU.md` only, without the original chat or a Remvu installation. Use a new receiver session and record both the available inputs and the code result. Synthetic fixtures do not replace this test.

## Fixed comparison tasks

Use the same code baseline and task for both conditions: code only, and code plus `REMVU.md`. Freeze the source handoff before either receiver starts. Run both Claude Code to Codex and Codex to Claude Code. Keep each receiver independent.

| Task | Required intent | Outcome checks |
| --- | --- | --- |
| CSV report extension | Preserve existing column order; a streaming rewrite was rejected | Correct new field; unchanged old fields; no repeated rejected rewrite |
| Small API fix | Preserve error code contract; prior test failed and remains unresolved | Fix behavior; do not describe old failed check as passed; rerun relevant tests |
| Feature continuation | One user preference and one agent inference differ; one step remains open | Keep their provenance separate; complete the outstanding step |

Score each required constraint, provenance distinction and open-work item as retained or lost; link the resulting diff and checks. Count repeated investigation only when visible evidence establishes it. Report actual provider usage when available. Otherwise report input/output characters or bytes and the measurement method. Do not turn character counts into estimated token savings.

## Measurement results

No controlled token or cost reduction is claimed by this release candidate until results are recorded here. The local scripts make no model API calls; semantic updates and receiver reads still use model context.

## Sharing review

Public fixtures must be synthetic or reviewed excerpts. Confirm that `.remvu/`, raw sessions, secrets and personal paths are absent from the release archive. Public examples must validate from one file without private attachments. Check dirty-tree refusal, explicit tracked-patch inclusion and missing-resource reporting separately.
