# Standalone beta.2 validation

The tested runtime is **9b9745b8f2cfbe83cb5d27bdd1500ced450d50d0**. It retains the complete engine and bundles its Python runtime. Users need Git, not a Python installation.

[Source CI](https://github.com/caotaiyi/remvu/actions/runs/39203583763) passed all eight jobs. [Standalone and DSH CI](https://github.com/caotaiyi/remvu/actions/runs/39203583716) passed all four jobs. The [machine-readable report](../evals/results/standalone-beta2.json) records artifacts, checks, earlier failures and limits.

| Check | Result |
| --- | --- |
| Source suites | 174 tests discovered per job; Windows has five explicit fixture skips |
| Windows Python 3.10 and 3.12 source stress | Ten trials per job, six writers per trial, no hook warnings |
| Windows x64, macOS ARM64, Linux x64 apps | Sixteen packaged checks each with no Python command on PATH |
| Local macOS run of the CI-built archive | Same sixteen packaged checks passed |
| DSH 0.2.1-rc.2 in Linux CI | Official plugin add, composed layer, actual SDK-profile load with five tools, clean shutdown |
| DSH on local macOS | Published API contract checks, actual local-profile boot and direct pinned GitHub installation/boot passed |
| Model requests in DSH host checks | Zero; these checks do not test model handoff |

Packaged checks cover installation, repeat installation, relocation of the download, upgrade/rollback, DSH overlay generation, the exact generated hook callback, twelve events from six writers, private/pending save, reviewed updates, CAS conflict retention, resume, stale checks, refusal of unsafe sharing, verified recovery, uninstall with retained memory, and bundled legacy export/verification/import including Git collection.

The application files and ZIP checksums were checked after download. Each app manifest identifies the tested source commit and a clean checkout. Binary builds are not claimed reproducible across different Python/toolchain distributions.

## Install the DSH bundle directly

Use a reviewed existing profile with the standalone app installed and its private DSH overlay generated:

```sh
dsh plugin --profile YOUR_PROFILE add github:caotaiyi/remvu#9b9745b8f2cfbe83cb5d27bdd1500ced450d50d0
```

This exact pinned source was installed through the official CLI and loaded in an isolated local SDK profile. The package manager reported peer warnings; they were retained, and the actual DSH runtime still registered all five tools. Installation needs no prepare/build script. See [setup and removal](../adapters/dsh/README.md). GitHub topic `dsh-plugin` is set; no claim is made that an external marketplace has already indexed it or that it is published on npm.

## Failures kept in the record

The first Windows app smoke compared JSON text with an unescaped path. The installer had succeeded; the assertion was fixed to compare decoded values.

An earlier Windows Python 3.10 source stress run timed out on trial seven while waiting for the session ledger. Other pre-fix runs passed, so the failure was intermittent. Durable tool-event writes now occur after releasing that ledger, and activation receipts avoid rewriting already observed event types. The eight-second budget and strict no-warning assertion were retained. Both final Windows jobs passed all ten trials; this is bounded test evidence, not a guarantee under every filesystem load.

A manual packaged legacy check found that export and verification worked while import still used source-relative module lookup. Import now uses the compiled bundled module. The packaged checks were expanded to export, verify and import a legacy bundle with Git collection on all three targets. External Git loading also uses the standalone runtime's loader handling.

## What remains unverified

The twelve-profile real-client acceptance ledger remains pending. Windows runners are not Windows 11 native-client acceptance. DSH model-driven handoff, Web/Desktop UI behavior and Windows DSH operation remain unverified. macOS Intel and Windows ARM64 are outside this artifact matrix.

The apps have no configured distribution signing/notarization. Follow normal OS review; do not bypass system protections. The v0.3.0-beta.2 release is retained as a **draft candidate**, preserving the native acceptance gate. The previous v0.2.0 release and beta.1 draft remain intact.

The earlier notes-only comparison remains a separate historical experiment. No token, cost or accuracy advantage is claimed for this standalone build.
