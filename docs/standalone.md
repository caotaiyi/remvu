# Complete standalone candidate

Remvu v0.3.0-beta.3 packages the existing memory engine with CPython. Users install no Python. Git remains required. Storage, opt-in observable recording, code fingerprints, revision checks, private export, reviewed public sharing, recovery and legacy export/import retain their engine behavior.

The default distribution is an application **folder**, not one executable file to detach from its libraries. Keeping the runtime beside the executable avoids unpacking it on every hook invocation. [PyInstaller's operating modes](https://pyinstaller.org/en/stable/operating-mode.html) describe this tradeoff.

The final tested candidate and retained failures are recorded in [the validation report](standalone-validation.md).

## Get the matching build

The [Standalone apps and DSH workflow](https://github.com/caotaiyi/remvu/actions/workflows/standalone.yml) builds macOS, Windows x64 and Linux candidates. Read a completed run's job outcomes and download the matching artifact; GitHub can require login for CI artifacts. Each artifact includes a platform ZIP, its SHA-256 checksum, the application folder and a smoke report. Release drafts are visible only to maintainers. This page does not point users to the old v0.2.0 release as if it contained standalone apps.

macOS ARM64 was built and exercised locally. Windows and Linux outcomes must be read from the recorded CI run; a green build checks packaged behavior, not a real Windows 11 client session. macOS Intel and Windows ARM64 are not certified targets of this build matrix. Do not run a mismatched architecture or relabel another platform's binary.

Verify the ZIP before extraction. On macOS use `shasum -a 256 FILE.zip`; in PowerShell use `Get-FileHash -Algorithm SHA256 'FILE.zip'`, and compare with its `.sha256` file. A checksum detects changed bytes but does not authenticate an unsigned publisher.

Extract the entire folder. macOS archives retain executable permissions when extracted by an appropriate archive tool; if an extractor drops only those permissions, inspect the file before restoring its executable bit. Never remove OS quarantine or disable Gatekeeper to make a candidate run. Distribution signing/notarization is not yet configured. Windows builds are also unsigned; ordinary OS review remains the user's decision.

## Install and maintain

See [quick start](quickstart.md) or [中文快速开始](quickstart.zh-CN.md). Run the program's `install --repo PROJECT --platform both`; it verifies and copies the full app into a stable user directory. Generated project skills and hooks name that stable executable. They never pass a `.py` file to the bundled executable as if it were an interpreter.

The result includes `runtime_launcher`, an argument list naming the stable executable. Use it for maintenance and DSH overlay generation. Installation preserves other config, retains private checkpoints and distinguishes configured from observed hook activation. Fresh save/resume installs need no hook trust review. Only explicitly enabling recording requires the normal client hook trust process.

Use `save` and `resume` day to day. Maintenance and explicit sharing remain available through the agent or the full CLI. For source development, Python 3.9+ is supported on macOS/Linux and 3.10+ on Windows. The standalone build uses Python 3.12, so the user's installed Python version is irrelevant.

## Validation boundaries

Local packaged checks used a PATH containing Git and **no Python command**. They exercised stable/repeated install, the exact generated hook callback, twelve events from six concurrent writers, pending/private save, a reviewed update, retained CAS conflict, resume, stale-code detection, refusal of unsafe public sharing, verified snapshot recovery and memory-preserving uninstall.

The DSH adapter targets published **0.2.1-rc.2**. The official plugin installer, composed config layer, actual SDK-profile startup with five registered tools and clean shutdown were exercised without sending a model request. Separate contract fixtures use real published Cordis/`defineTool` APIs and the bundled engine; they cover event filtering, failure retention, pending saves, context deduplication, plan/read-only state and workspace isolation.

These are packaged/host checks. The [twelve-profile native acceptance ledger](../evals/beta-matrix.json) remains pending. Neither that host startup nor the earlier notes-only comparison establishes DSH model handoff, desktop/IDE compatibility, token savings or full Windows 11 acceptance. A full public beta release remains gated on that evidence.

## Build and reproduce

Developer machines and CI need Python to **build**, not to run the delivered app:

```sh
python -m pip install -r scripts/standalone-build-requirements.txt
python scripts/build_standalone.py --out /outside/checkout/standalone
python scripts/standalone_smoke.py /outside/checkout/standalone/APP_FOLDER
```

Release builds require a clean committed checkout. `--allow-dirty` exists only for development; its manifest marks the result. Binary builds are not claimed byte-for-byte reproducible across toolchains. Each app records its source commit, build platform, bundled Python and file hashes. Internal symlinks are resolved only inside the build output; unexpected external links or private session files fail packaging. Build on the target platform.

For DSH tests, install `@deepseek-ai/dsh@0.2.1-rc.2` and `pnpm@11.25.0` into an isolated Node 24 directory. Copy `adapters/dsh/{index.js,package.json,test.mjs}` into a sibling `plugin/` directory beside its `node_modules`, then run `node plugin/test.mjs ABSOLUTE_REMVU_EXECUTABLE`. Put that pnpm binary on the test PATH and run `node scripts/dsh_host_smoke.mjs DSH_BINARY REMVU_EXECUTABLE REPORT_PATH`. It creates a new temporary DSH home/profile and never sends a model prompt. The workflow contains the exact commands.

The app includes CPython and PyInstaller licenses and CPython's third-party notices under `licenses/`. Remvu remains MIT-licensed. The notes-only fallback remains a separate opt-in artifact.
