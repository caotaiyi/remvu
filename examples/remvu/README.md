# Synthetic conformance examples

These fixtures test the format. The user statements, code excerpts and failed command output are synthetic; they are not results from the Remvu repository or a real client session.

| File | Expected result |
| --- | --- |
| `REMVU.md` | Valid public document with six public entries and one omitted private entry |
| `invalid-format.md` | Reject an unsupported format identifier |
| `invalid-missing-section.md` | Reject a missing required section |
| `invalid-private-path.md` | Reject a public document containing a private path |
| `update.proposal.json` | Accept an update at revision 0 |
| `invalid-unknown-field.proposal.json` | Reject an unknown field instead of silently losing it |
| `invalid-negative-event-count.proposal.json` | Reject a negative evidence-review watermark |

From the repository root:

```bash
python3 spec/validate_examples.py
python3 skills/remvu/scripts/remvu.py validate examples/remvu/REMVU.md
```

The valid proposal's `base_event_count: 0` explicitly acknowledges the zero observed events in its newly initialized synthetic project. For a real update, use the event count covered by the agent's evidence review; new events remain pending. The validator runs proposal cases in isolated temporary directories. If the optional development package `jsonschema` is installed, it also validates the metadata and proposal schemas. CI requires that schema check with `--require-jsonschema`; runtime commands do not need the package.
