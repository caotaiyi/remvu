# Complete standalone installation

The application folder contains the executable and its bundled runtime. Keep the folder intact; users do not install Python. Git remains required for code-state checks. Supported build targets and test evidence are in the repository's `docs/standalone.md`; platform artifacts do not imply native-client certification.

Ask the agent to download the matching reviewed Remvu standalone release archive and its checksum, verify the checksum, extract the whole folder and run the executable's `install --repo PROJECT --platform both`. On macOS the executable is `remvu`; on Windows it is `remvu.exe`. In PowerShell use `& 'ABSOLUTE\remvu.exe' 'install' '--repo' 'PROJECT' '--platform' 'both'`. Do not bypass OS signing checks or client trust prompts.

Installation verifies the app manifest and copies the entire runtime to a stable per-user directory. It merges project adapters, preserves other hooks/instructions and retains a private checkpoint. Use the `runtime_scripts` result to locate its app root (three parents above `_internal/skill/scripts`); the generated project skill contains the exact executable. Moving the downloaded source folder afterwards does not break installed hooks.

The result distinguishes configuration from observed activation. Complete official client login and exact hook trust review, then open a new session. `doctor` reports observed events; it cannot certify a host trust choice or an untested desktop/IDE.

Upgrade using the installed executable's `upgrade --source NEW_APPLICATION_FOLDER --repo PROJECT`; it verifies and stages that app before initialization. `upgrade --rollback --repo PROJECT` selects the previous recorded runtime. `uninstall --repo PROJECT` removes only unchanged owned adapters, retaining private memory and runtime caches. Never remove another client's settings to make installation pass.

Two normal actions: `save` and `resume`. The full engine still exposes all format, fingerprint, privacy, recovery and CAS tools. A direct `save` without a reviewed semantic proposal cannot recover an exhausted agent's unwritten understanding. Observations remain available to the next agent, and pending status stays visible.
