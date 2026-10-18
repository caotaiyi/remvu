# 安装 Markdown skill（无需 Python）

把这句话交给当前项目中的编程 agent：

> 从 https://github.com/caotaiyi/remvu 安装 Markdown 版 Remvu skill。先审阅 scripts/install-skill.sh 或 scripts/install-skill.ps1，再复制到本项目的 Claude Code 和 Codex skill 目录。保留已有 skill，不运行可选 Python 安装器，不启用 hooks。

它只复制 SKILL.md、references/、assets/ 和 agents/，不会安装 Python 文件或改变客户端设置。仍需完成客户端正常的项目信任；新 skill 未出现时，打开新会话。

## 手动安装

macOS，在审阅过的源码中运行：

```sh
REMVU_SOURCE=/path/to/remvu sh /path/to/remvu/scripts/install-skill.sh /absolute/path/to/project
```

指定 REMVU_SOURCE 可以离线安装；未指定时会用 Git 获取仓库当前源码。Windows PowerShell：

```powershell
& 'C:\path\remvu\scripts\install-skill.ps1' -Project 'C:\project' -Source 'C:\path\remvu'
```

安装器不修改执行策略。Windows 真实执行仍待验收。如果客户端或系统限制脚本执行，可以使用文件管理器复制 skills/remvu 中的 SKILL.md、references/、assets/、agents/ 到项目的 `.claude/skills/remvu` 和 `.agents/skills/remvu`，先保留已有目录。

## 保存和接手

Claude Code 输入 `/remvu save`，Codex 输入 `$remvu save`。文件保存在本地 `.remvu/notes/REMVU.md`，写入前 agent 会检查并排除私有目录的 Git 跟踪风险。已经被 Git 跟踪或无法检查时，先选择仓库外的本地保存位置，不要直接写入私有内容。

新会话输入 `/remvu resume` 或 `$remvu resume`。接手方也可以直接读取交接文件，无需安装。换电脑时带上代码与选定文件；公开分享需要单独提出并审阅内容。

## 更新、回退、卸载

更新前保留两个旧 remvu skill 目录，再复制已审阅的新版本；安装器不会覆盖已有目录。需要回退时恢复旧目录。卸载只删除这两个复制的 remvu 目录，保留 `.remvu/` 私有记忆。

这不会移除旧 Python 引擎留下的 hooks。旧引擎需要按[维护说明](../skills/remvu/references/maintenance.md)卸载，或在客户端正常 hook 设置中停用对应的 Remvu handler，不动其他配置。

## 可选引擎

严格格式校验、内容指纹、并发保护和损坏恢复仍由可选引擎提供，需要 Python 3.9+ 和 Git。Markdown skill 不编辑旧 `.remvu/state.json`，也不能替代引擎的冲突解决或事件整理。[具体差异](../skills/remvu/references/notes.md#existing-engine-projects)。
