# 安装完整 Remvu 独立程序

可以直接把这句话交给 agent：

> 从 https://github.com/caotaiyi/remvu 为我的系统和架构安装完整 Remvu 独立程序。校验下载包，保留整个程序文件夹，再为当前项目安装。保留已有 skill、hook 和私人记忆，默认不启用自动记录，仅在我要求开启时说明客户端 hook 信任步骤。不要安装 Python，不要换成仅笔记版。

v0.3.0-beta.3 是测试候选版，先查看[程序包与验证状态](standalone.md)。仍需 Git；Python 只用于构建或运行源码，用户使用独立程序不需要安装它。

macOS 解压后运行：

```sh
'/绝对路径/remvu-app/remvu' install --repo '/项目绝对路径' --platform both
```

Windows PowerShell：

```powershell
& 'C:\路径\remvu-app\remvu.exe' 'install' '--repo' 'C:\项目' '--platform' 'both'
```

安装会校验并复制完整程序到稳定的用户目录，合并项目配置与 skill，保留原有内容及备份。之后移动下载目录不会影响已安装的适配器。新安装不创建 hook 配置。需要自动记录时，让 agent 执行 `recording on --repo 项目`，再按正常流程审阅信任。已有自动记录项目升级后保留原模式；用 `recording off --repo 项目` 关闭，保留 skill、记忆和其他钩子。`doctor` 会区分已配置与观察到实际回调，不能代替信任审查。

Claude Code 使用 `/remvu save`、`/remvu resume`，Codex 使用 `$remvu save`、`$remvu resume`。保存在本地 `.remvu/handoff/REMVU.md`，不会自动提交或上传。请在原 agent 还能响应时保存；未审阅证据仍待整理，失败检查保留失败。

[DeepSeek Harness 插件](../adapters/dsh/README.md)通过官方安装流程加载，再用已安装的稳定程序生成项目配置。不需要用户安装 Python，也无需编译插件。

升级：用已安装程序执行 `upgrade --source 新程序文件夹 --repo 项目`；回滚用 `upgrade --rollback`。`uninstall` 只移除未被用户改动的自有适配器，保留私人记忆。`doctor`、`repair` 用于检查和恢复；`diagnose` 生成可预览的本地脱敏报告，不自动上传。这些维护命令均可通过自然语言让 agent 执行。

继续兼容 v0.2.0 本地记忆和旧证据导入。仅在主动选择时才使用[仅笔记备用路径](notes-only.md)，它不具备完整程序的记录、指纹和并发校验能力。
