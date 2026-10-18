# Native beta acceptance / Windows 验收

The v0.3.0-beta.1 candidate is not released until the twelve profiles in
`evals/beta-matrix.json` have reviewed evidence. CI, package smoke checks and
local hook receipts do not complete this checklist.

## Windows: prepare before testing

1. Use Windows 11 x64, Python 3.10+ from [python.org](https://www.python.org/downloads/windows/)
   and Git from [git-scm.com](https://git-scm.com/download/win).
2. Sign in normally to Claude Code and Codex. Open the local Code workspace in
   each desktop app and its official VS Code extension. Ordinary desktop chat
   and cloud workspaces are outside this test.
3. Clone or extract this reviewed candidate outside your real projects.
   Run `scripts/windows-preflight.ps1` if script execution is permitted normally.
   Do not change your execution policy to run it; manual command checks suffice.
4. Use `python scripts/package_smoke.py PATH_TO_SKILL_ZIP` to check the downloaded
   package. This creates only temporary synthetic projects, then removes them.
   Save the JSON result if you want to send it back. It does not prove native
   client compatibility.

Windows 准备好上述工具和登录后即可离开。后面的实际验收仍需在客户端中
执行；安装、版本检查或脚本通过不能代替它。不要发送账号密码、密钥或原始聊天。

## One profile at a time

Use `python3` on macOS and your Python 3.10+ launcher (`python` or `py -3.12`)
on Windows. Commands below use `python`.

```text
python scripts/native_acceptance.py prepare --out NEW_TEST_DIRECTORY --profile claude-cli
```

Profiles: `claude-cli`, `codex-cli`, `claude-desktop`, `codex-desktop`,
`claude-vscode`, `codex-vscode`. Run all six on each target system.

Open `producer/` in the selected real client and paste `producer-prompt.txt`.
Use its local working directory directly. If a desktop client creates another
worktree, initialize Remvu there as a separate test project. A hook bound to the
original project must not record another worktree's payload into its memory;
mismatched directories produce a visible gap.
Install this candidate, finish the normal project trust/hook review and note
the actual app, CLI and extension versions. Record the installed runtime digest
from `.runtime.json`. Do not enable permission bypass flags.

The producer implements a small tag normalizer and records its remaining BOM
task in a valid, explicitly shareable `REMVU.md`. Review its sharing scope. Then:

```text
python scripts/native_acceptance.py receive --root TEST_DIRECTORY
```

Open the newly created `receiver/` in a **fresh session of the other agent** on
the same surface. Use `receiver-prompt.txt`. The script copies only the fixed
code/test files and `REMVU.md`; no original prompts, hidden state or adapters.
Use a client profile without a global Remvu installation. Do not grant it access
to the producer folder. Then:

```text
python scripts/native_acceptance.py verify --root TEST_DIRECTORY --out NEW_REPORT.json
```

The report verifies baseline behavior, the unfinished BOM task and the absence
of private project adapter files. A reviewer must separately check that the
receiver preserved the signature, no-dependency constraint, rejected regex
direction and scope of the BOM change. The report never self-certifies a native
client or claims a cost saving.

## Lifecycle checks

For each producer profile, record observed outcomes for:

- Fresh install and first use, normal hook trust/restart, cold handoff and intent review.
- A deliberately failing check recorded as failed, still historical after a code change.
- Repeated install, source relocation, upgrade from reviewed source and rollback.
- Uninstall preserving unrelated settings and private memory.
- A diagnostic preview with no private text/paths/outputs; sharing remains explicit.

For **automatic** support additionally run several task turns, a real context
compaction, interruption/restart and simultaneous sessions. Verify no lost
constraints/events, stale-code warnings, retained conflicts and at most one Stop
repair per turn. Artificial hook payloads cover regressions but cannot substitute
for these native actions. If an entry supports manual skill invocation only,
record it as manual after its manual lifecycle checks pass.

The IDE uses project skills/configuration. Codex IDE does not currently support
plugin installation; a plugin ZIP is not its setup path. See [Codex plugins](https://learn.chatgpt.com/docs/plugins)
and [hooks/trust](https://learn.chatgpt.com/docs/hooks). Claude desktop tests use
the [local Code tab](https://code.claude.com/docs/en/desktop), not ordinary Chat.

## Return results

Send the small behavior report plus a factual checklist of what you actually
did and the client versions. Keep raw transcripts, hook payloads and local
memory private. A reviewed, synthetic-only evidence summary can be committed
under `evals/`; its path, runtime digest, client versions and individual checks
are referenced in the matrix. Unknown outcomes remain pending.

```text
python scripts/check_beta_readiness.py --require-ready
```

This is the release gate, not a benchmark. Usage counters may be reported when
the client supplies them. Otherwise report time, characters or bytes with their
units. A savings comparison requires both groups to finish the same task.
