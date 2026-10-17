# Contributing to Remvu

Remvu accepts fixes, format feedback and client adapters. Keep contributions tied to a reproducible handoff problem: lost constraints, inconsistent claims, repeated work or unavailable evidence.

## Development

Use Python 3.10+ and Git. The runtime uses the Python standard library. From the repository root:

```bash
python3 -m unittest discover -s tests -v
```

Run the example validator described in [examples/remvu](examples/remvu/) after changing the format. Add tests for behavior and failure handling. Keep fixtures synthetic; do not check private traces or `.remvu/` state into the repository.

## Pull requests

Describe the triggering case, expected behavior, actual result and validation you ran. Include the client/version only when it affects the issue. Preserve the legacy exporter and existing evidence format while changing the memory layer.

Format changes should update the [proposal](spec/remvu-v1.md), schema and conformance examples together. Explain whether the change can retain `remvu/1` or needs a new identifier. Preserve reviewed-event watermarks, archived conflict resolutions and check-specific code fingerprints in adapters and importers. Adapter proposals follow [the adapter guide](docs/adapters.md).

A test run does not establish a live client integration or a token-saving claim. Report live observations separately from simulated payload tests. For measurements, publish the fixed task, receiver conditions, outcome rubric and available usage data; use characters or bytes if token usage is unavailable.

## Release requirements

Before a release, pass the checks in [the validation report](docs/validation-report.md), including real Claude Code to Codex and Codex to Claude Code handoffs. A receiver must have code and `REMVU.md` only, with no original chat or Remvu installation. Release automation must not substitute fixture tests for these observations.

Build the distributable packages from a committed revision into a fresh directory outside the repository:

```bash
python3 scripts/build_release.py --out /tmp/remvu-release
```

The default source is `HEAD`; use `--ref COMMIT` to reproduce a specific revision. The standard-library builder writes the versioned plugin ZIP, standalone skill ZIP and `SHA256SUMS`, and audits their contents. Packages contain the manifest/skills/license components they use. Tests, evaluation reports and full source remain in the repository and GitHub's source archive. Before uploading, extract each final package at a new path and verify initialization, update, sharing and checks without relying on the source checkout.

MIT-licensed contributions retain the project's existing license. Prose should use plain language and claims supported by evidence. The public introduction follows [Humanizer](https://github.com/blader/humanizer)'s editing rules; it is not a runtime dependency.
