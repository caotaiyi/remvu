# Save/resume candidate validation

Version: 0.3.0-beta.3. This candidate changes installation defaults and context delivery; the public memory format remains `remvu/1`.

Fresh installs add project skills without hooks. Explicit recording installs four Claude Code events or three Codex events, without Stop. Upgrades preserve existing opt-in preferences. Turning recording off retains private memory, skills and unrelated configuration.

Default resume returns a short entry index and health summary. Detailed evidence remains available by ID; omitted entries are counted. Save retains revision checks, observation watermarks, fingerprints and unresolved conflicts. An incomplete review remains incomplete.

DSH defaults to manual tools. When recording is explicitly enabled, automatic context is injected once per session/compaction window; ordinary events do not reinject it. A failed injection warns once. Save and resume are visible tools; advanced tools load on demand.

## Context-size fixture

The [synthetic fixture result](../evals/beta3-context-budget.json) records 45 long constraints. Default resume returned 2,667 characters; explicit detailed resume returned 8,101. All 45 entries remained stored, and the default response reported 41 omitted previews. These are response sizes for one fixture, not measured model token usage or a savings estimate.

## Local verification

On macOS with Python 3.12, the final source suite discovered 176 tests and passed with one Windows-only path-semantics test skipped. All seven format examples matched their expected outcomes with JSON Schema validation enabled. The acceptance-ledger checker passed and correctly reported `release_ready: false`.

## Acceptance boundaries

Local source, packaged-runtime and published DSH SDK contract checks are tracked separately from native client acceptance. Existing beta.2 validation reports describe that older source revision. The current [native matrix](compatibility.md) remains pending; no model-driven handoff, desktop, VS Code or Windows 11 certification follows from a successful package test.

The new recording profile must still complete multi-round native acceptance before public beta publication. There is no automatic submission of project logs or diagnostics.
