# Roadmap

## Individual public beta: current work

Stable installation, upgrade/rollback, health and recovery commands, Windows
literal bookkeeping, bounded reads and private diagnostics are candidate code.
Publish v0.3.0-beta.1 only after the twelve-profile [acceptance ledger](../evals/beta-matrix.json)
passes reviewed native checks. Keep unsupported automation explicit and offer
manual invocation where it has been verified. No volunteer study or savings
percentage is required before the public beta.

## Platform integration: after individual beta feedback

Keep the local memory engine separate from client lifecycle adapters. The current
Python boundary is `init_state`, `load_state`, `record_event`, `apply_update`,
`check_project` and `write_document`; `remvu/1` remains the portable file interface.
Before promising a supported SDK, specify its versioned error/result contract,
provide an adapter example and complete one real platform pilot with project and
observable-tool access. A plain API gateway cannot claim full project capture.
Pilot selection and platform-specific APIs remain future work.

## Open source self-hosting: after the pilot

Use pilot evidence to specify authenticated project isolation, concurrent updates,
storage/retention and data export. Keep single-file `REMVU.md` handoffs independent
of any service. An operated Remvu SaaS and account requirement are outside the
current plan. Do not add a server or storage migration before that decision.
