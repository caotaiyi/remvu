# Install Remvu in a project

Give your coding agent this instruction:

> Install Remvu from https://github.com/caotaiyi/remvu in this local project.
> Read its current candidate status and compatibility report first. Check Python
> 3.10+ and Git; help me install missing prerequisites from their official sources.
> Review and clone the source outside my project, run scripts/install.py for this
> project, then run doctor using the stable runtime path it prints. Preserve my
> existing settings and private data. Guide me through the client's normal hook
> review; report configuration, observed execution and native support separately.

The current main branch contains a **v0.3.0-beta.1 candidate**. Its twelve-profile
native acceptance is still pending. The published v0.2.0 release and its evidence
remain available; they do not certify the candidate.

For a manual install after reviewing the source:

```bash
git clone https://github.com/caotaiyi/remvu.git
python3 remvu/scripts/install.py --repo /absolute/path/to/project --platform both
```

On Windows use your Python 3.10+ launcher, for example `py -3.12`, in place of
`python3`. The installer checks Python and Git, copies the skill to a stable user
directory and merges project adapters. It does not sign you in or grant trust.
You may move the source checkout afterward. Use `--platform claude`, `codex` or
`none` when appropriate. `none` does not uninstall already-configured adapters.

Restart the client if required and complete normal hook review. Then ask
`/remvu doctor` in Claude Code or `$remvu doctor` in Codex. Hook execution receipts
are useful diagnostics, but do not prove automatic consolidation or identify the
desktop/IDE entry point. If the skill is not discovered, run the printed CLI
directly and check that you opened the project root in the client.

Use `/remvu` or `$remvu` to save a local handoff. Use `share` only when you want
a reviewed, shareable `REMVU.md`. A receiving agent needs project code and that
file; it need not install Remvu. An unsupported automatic flow can use manual
commands while its native compatibility remains pending.

[Maintenance and recovery](../skills/remvu/references/maintenance.md) ·
[FAQ](faq.md) · [Native test instructions](native-acceptance.md)
