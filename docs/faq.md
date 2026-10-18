# Troubleshooting / 常见问题

**Installed, but hooks do not run? / 安装后没有自动记录？**

Run `doctor`. Configuration and hook trust are separate. Open the correct local
project, review exact hook definitions normally and restart if required. A runtime
upgrade changes definitions and may require a new review. Do not bypass approval.
Use the manual skill while investigating; do not mark the memory complete.

**Memory remains pending? / 一直显示待整理？**

Finish project operations, then ask `/remvu` or `$remvu` to review evidence and
save an update. Commands must be separate. Windows PowerShell uses the literal
single-quoted invocation shown in the skill. Compound commands and unknown shell
forms are intentionally retained. The Stop hook requests at most one repair per
turn; a pending result is truthful, not a reason to force the watermark forward.

**Damaged state or a busy lock? / 状态损坏或锁忙？**

Run `doctor`, then `repair` for verified snapshot/ledger recovery. A busy OS lock
belongs to a running writer: close it and retry. Repair retains originals and
pending work; it cannot recreate missing evidence. Do not delete state or replay
orphan journals. See the [recovery instructions](../skills/remvu/references/maintenance.md).

**Can I move the clone or uninstall? / 能移动目录或卸载吗？**

After managed `install`, yes: adapters point to the stable runtime copy. Legacy
direct `init` still points at its source. Upgrade with reviewed source; rollback
selects the previous managed runtime. Uninstall preserves memory, backups, ignore
rules and shared runtimes, and retains edited hooks for review.

**Can I share a diagnostic? / 诊断会上传聊天吗？**

`diagnose` writes an allowlisted local report. Preview it before choosing to
attach it to an issue. It excludes entry text, tool output, session IDs, paths,
remote URLs and config bodies. No telemetry or automatic upload is enabled.

**Will it save tokens? / 能节省 token 吗？**

The runtime makes no model requests. Semantic updates use the active agent and
still consume context. Doctor reports actual local bytes and counts; native
evaluation reports usage when available. No savings percentage is established.

**Can an API relay host this? / 中转站能直接接入吗？**

The open format is available now. A useful integration needs project-file and
observable-tool access. The dedicated platform pilot and self-hosted server are
later stages; neither is bundled with this candidate.
