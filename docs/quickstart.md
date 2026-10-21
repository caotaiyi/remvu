# Install the complete Remvu app

Give the agent this instruction:

> Install the complete standalone Remvu app from https://github.com/caotaiyi/remvu for my system and architecture. Verify the archive checksum, keep its application folder intact and run its install command for this project. Preserve existing skills, hooks and private memory. Keep automatic recording off. Explain client hook trust only if I explicitly enable it. Do not install Python or switch to the notes-only fallback.

The v0.3.0-beta.3 builds are test candidates. Check [artifact availability and verification](standalone.md) first. Git remains required. Users download the bundled runtime; Python is a build/source-development dependency only.

From a reviewed extracted application on macOS:

```sh
'/absolute/path/remvu-app/remvu' install --repo '/absolute/project' --platform both
```

On Windows PowerShell:

```powershell
& 'C:\path\remvu-app\remvu.exe' 'install' '--repo' 'C:\project' '--platform' 'both'
```

Installation verifies and copies the app to a stable user location, merges the project skill/configuration and backs up existing state. Moving the extracted download afterwards does not affect installed adapters. Fresh installation creates no hook config. Project skill discovery can require a new session. To enable recording later, ask the agent to run `recording on --repo PROJECT`; only that choice requires hook review. `recording off --repo PROJECT` removes unchanged owned callbacks while preserving skills, memory and other hooks. Existing installs keep their previous mode through upgrade. `doctor` distinguishes configured adapters from observed callbacks; a receipt alone cannot certify trust.

Use `/remvu save` and `/remvu resume` in Claude Code, `$remvu save` and `$remvu resume` in Codex. Save stays local under `.remvu/handoff/REMVU.md`; only explicit sharing produces a public file. Save while the original agent can still respond. Unreviewed evidence stays pending and failed checks stay failed.

For [DeepSeek Harness](../adapters/dsh/README.md), install `dsh-remvu` through its official plugin flow and use the installed app to generate a project overlay. No user Python or plugin compilation is needed.

Maintenance uses the installed executable. `upgrade --source NEW_APP_FOLDER` stages a reviewed replacement; `upgrade --rollback` selects the previous managed runtime. `uninstall` removes unchanged owned adapters and retains memory. `doctor` and `repair` inspect/recover local state; `diagnose` writes a local allowlisted report for preview and never uploads automatically. All these commands take `--repo PROJECT`.

Source developers can still use `python3 skills/remvu/scripts/remvu.py`. Existing v0.2.0 memory remains readable. The deliberately [notes-only installation](notes-only.md) remains available, with no automatic recording or structured fingerprint/concurrency validation.
