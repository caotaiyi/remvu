# Optional notes-only fallback (no recording or structured validation)

Ask the agent to review this repository and install only its project skill. Choose this path explicitly only when you want file-tool notes without the complete engine. It does not configure hooks.

From a reviewed checkout on macOS:

```sh
sh /path/to/remvu/scripts/install-skill.sh /absolute/path/to/project
```

Set `REMVU_SOURCE=/path/to/remvu` for offline installation from that checkout; otherwise the script fetches a fresh source with Git. On Windows PowerShell, after reviewing the source:

```powershell
& 'C:\path\remvu\scripts\install-skill.ps1' -Project 'C:\project' -Source 'C:\path\remvu'
```

The scripts copy `skills/remvu` into `.claude/skills/remvu` and `.agents/skills/remvu`. They refuse existing skills and symlink/reparse destinations. The Markdown installers copy only SKILL.md, references/, assets/ and agents/. They do not alter execution policy, client settings, hooks, Python or global configuration. Normal client project trust still applies. Native Windows execution is pending verification.

You can also copy the skill directory to those locations with the file manager. Preserve any existing Remvu skill first. A manual full-directory copy includes optional Python files, but the Markdown installers exclude them. Those files are never used for Markdown save/resume. For a manual minimal copy, use assets/markdown-skill.md as the installed SKILL.md, plus references/, assets/ and agents/. The main skill entry now targets the complete standalone engine.

Open a fresh session if the skill is not discovered. In Claude Code ask `/remvu save`; in Codex ask `$remvu save`. To continue, ask the receiving agent for `remvu resume` using its native skill syntax, or simply tell it to read the handoff file.

Save protects the local `.remvu/` path before writing memory. If the directory is already tracked or privacy cannot be checked, it asks for an external local destination. Do not commit private notes. Only an explicit share request produces a reviewed public file.

To update, preserve the old skill directories and copy a reviewed new version; the installer does not overwrite them. To undo that update, restore the preserved directories. To remove this Markdown installation, remove only the two copied `remvu` skill directories; preserve `.remvu/` memory. This does not remove adapters from a previous Python engine installation: use the engine's documented uninstall or the client's hook settings for those.

## Optional engine

The existing managed engine installation, upgrade, rollback, diagnostics and uninstall remain available with Python 3.9+ on macOS/Linux, Python 3.10+ on Windows, and Git. See [maintenance](../skills/remvu/references/maintenance.md). Existing engine `.remvu/state.json` files are never edited by the Markdown skill. Existing engine projects should read the migration notes in [note rules](../skills/remvu/references/notes.md#existing-engine-projects).
