# Questions / 常见问题

**Do I need Python? / 需要 Python 吗？**

No for the default Markdown skill. Save and resume use the agent's file tools. The optional strict engine needs Python 3.9+ on macOS/Linux, 3.10+ on Windows, and Git. Windows Python 3.9 failed repeated recorder stress and is unsupported by managed installation. Do not run scripts/install.py when you only want the Markdown workflow.

**Will Remvu stop my session? / 会拦截结束吗？**

The default skill installs no hooks. The optional recorder's Stop handler is now quiet and nonblocking. Old installed copies retain old code: update the runtime or disable the exact Remvu Stop handler through normal client settings. Unreviewed work stays pending until explicitly consolidated.

**Is Markdown as reliable as the engine? / 轻量版有哪些限制？**

It has provenance labels, rejected decisions and explicit gaps, but no enforced concurrent lock, content fingerprint or automatic secret scan. Use one writer at a time and rerun relevant checks after code changes. Agent read-back catches some omissions; it does not certify completeness.

**Installed, but the command is missing? / 装了但找不到命令？**

Open a fresh session in the correct project and check the client supports project skills. Claude Code uses /remvu save; Codex uses $remvu save. Normal project trust still applies. Native desktop, VS Code and Windows verification remains pending. A receiver can read the file directly without installation.

**Can I upgrade or uninstall? / 怎么升级或卸载？**

For the Markdown copy, preserve the existing two remvu skill folders and replace them with a reviewed version; restore the preserved folders to roll back. Remove only those folders to uninstall. Keep .remvu/ memory. The installer refuses to overwrite existing skills. Earlier engine adapters require their own uninstall; see [maintenance](../skills/remvu/references/maintenance.md).

**Old engine state is pending or damaged? / 旧引擎状态待整理或损坏？**

Read [the engine workflow](../skills/remvu/references/engine-workflow.md). A Markdown save does not acknowledge engine events or resolve conflicts. doctor and repair preserve gaps and unknown work. Never force a watermark forward or turn a failed check into success. Do not delete live OS locks.

**Will this save tokens? / 能省 token 吗？**

Saving and reading still use the current agent's context. No extra model API is called by the default workflow. Compare measured completed tasks and include overhead; no savings percentage is established.

**Can I submit diagnostics? / 诊断会上传聊天吗？**

The optional engine's diagnose command produces a local allowlisted report. Preview it, then submit only on explicit instruction. There is no telemetry or automatic upload. Keep raw private notes and logs out of public issues.

**Can a relay service integrate it? / 中转站能接入吗？**

A useful integration needs project files and observable results. API forwarding alone does not provide them. The format is open; a dedicated platform adapter and self-hosted server are not bundled.
