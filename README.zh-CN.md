# Remvu

[![CI](https://github.com/caotaiyi/remvu/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/caotaiyi/remvu/actions/workflows/ci.yml)

随项目流转的 AI 记忆。

把项目代码和一个 `REMVU.md` 文件交给下一个 agent，它就能读取目标、约束、关键决策、代码状态、验证结果和下一步。接收方无需安装 Remvu，也无需拿到原聊天。

[English](README.md) · [格式提案](spec/remvu-v1.md) · [兼容情况](docs/compatibility.md) · [验证报告](docs/validation-report.md) · [接手演示](docs/demo.md)

主分支提供 **v0.3.0-beta.1 候选实现**，新增稳定安装、升级回滚、健康检查、恢复和本地诊断。macOS、Windows 及终端、桌面、VS Code 的真实验收尚未完成，该测试版还未发布。[快速开始](docs/quickstart.zh-CN.md) · [验收说明](docs/native-acceptance.md)。

已发布的 v0.2.0 提供参考实现和 `remvu/1` 开放格式提案，其两项小型真实 CLI 接手已通过。这些历史结果不能证明新版通过验收。[结果与限制](docs/validation-report.md)。

![两项真实跨 agent 接手结果的 30 秒回放](docs/assets/remvu-live-replay.gif)

这是 30 秒证据回放，并非原始屏幕录像。画面标有模型实际运行耗时；[查看对应结果](docs/demo.md)。

## 面向多模型平台与 API 中转站

**换模型、换客户端，把项目背景一起带走。**

多模型平台和 API 中转站的用户，可以把已经记录的目标、约束、被否定的方案和未完成事项带入新的 coding agent 会话。下一个 agent 接到的不只是代码，还有这些代码为什么这样写，减少重新交代背景的工作。

平台运营者可以将开放格式接入自己的 agent 客户端或工作流，作为项目记忆与跨模型接手能力。这需要访问项目文件和可观察的工具结果；单纯转发 API 请求不会自动获得这些上下文。中转平台集成属于可扩展场景，当前没有附带专用中转适配器；现有真实验证覆盖 Claude Code 与 Codex 接手，尚不能据此得出 token 或费用节省结论。

## 安装到项目

需要 Python 3.10+。获取 Git 状态和补丁还需要 Git。运行时仅用 Python 标准库，不调用模型 API。

将 Remvu 克隆到目标项目之外，例如专门存放工具的目录。

```bash
git clone https://github.com/caotaiyi/remvu.git
python3 remvu/scripts/install.py --repo /path/to/project --platform both
```

安装器将审阅过的 skill 复制到稳定的用户目录，再合并项目指令和 hooks，保留已有设置和私人记忆，之后可以移动原来的克隆目录。Windows 用 Python 3.10+ 对应的启动命令替换 `python3`，例如 `py -3.12`。按照客户端提示完成正常的 hook 信任与重启；Codex 可通过 `/hooks` 审查。再运行 `doctor`，区分已经配置与观察到实际执行的状态。

| 操作 | Claude Code | Codex |
| --- | --- | --- |
| 初始化 | `/remvu init` | `$remvu init` |
| 更新记忆并生成本地交接 | `/remvu` | `$remvu` |
| 生成公开文件 | `/remvu share` | `$remvu share` |
| 检查记忆与代码状态 | `/remvu check` | `$remvu check` |
| 检查健康状态 | `/remvu doctor` | `$remvu doctor` |
| 恢复本地文件 | `/remvu repair` | `$remvu repair` |
| 升级或回滚 | `/remvu upgrade` | `$remvu upgrade` |
| 卸载项目适配器 | `/remvu uninstall` | `$remvu uninstall` |

只使用一个客户端时，可选择 `--platform claude` 或 `codex`；只用命令行时选 `none`。仓库也提供 `plugin.json`，脚本仍需要可访问项目文件的本地环境。

[维护说明](skills/remvu/references/maintenance.md)介绍升级、回滚、保留记忆卸载和本地诊断。[常见问题](docs/faq.md)包含待整理、信任和恢复问题。平台集成与开源自托管将在个人版公开测试之后推进，当前没有附带专用中转适配器或服务端；见[路线图](docs/roadmap.md)。

## 记住什么

文件先给出默认不超过 8,000 字符的摘要，再保留详细的目标、偏好、架构、决策历史、修改、检查和未完成事项。JSON 元数据标明记忆版本及对应代码状态。

每条记录区分用户确认、工具观察、agent 推断和待核实内容。检查结果需要依据，并保留检查时的代码指纹；补写普通笔记不会让旧的通过结果变成当前验证。被替代的决定继续保留，避免下一个 agent 重新走已经否定的方向。

完整本地记忆、增量事件和证据放在忽略的 `.remvu/`。Hooks 记录可观察事件，由当前 agent 使用已有上下文整理语义记忆。遗漏更新会保留待整理状态，停止 hook 最多请求一次补写。并发更新检查 revision，不能静默覆盖另一位 agent 的记录。

脚本不额外调用模型 API，整理和阅读记忆仍会消耗当前 agent 的上下文。项目仅在有对照实测时报告 token 或费用变化。

## 明确选择后分享

使用 `/remvu share` 或 `$remvu share` 选择可公开内容并生成本地 `REMVU.md`。公开条目必须有可一起带走的公开来源摘录，不能依赖私人日志或附件。发布前检查内容。

存在待整理事件或未解决冲突时会停止分享；代码有未提交改动时也默认停止。建议先提交预期修改；明确选择后可用 `--include-patch` 携带 tracked diff。补丁无法携带的必要资源须另行列明。生成文件不会自动提交、推送或上传。

隐藏思考链、分析通道、系统与开发者消息及加密推理不会进入文件。决策摘要保留结论和可解释的依据。秘密检测可能遗漏自定义敏感内容；哈希和代码指纹也不能证明来源可信或测试通过。

## 命令行与扩展

```bash
python3 skills/remvu/scripts/remvu.py status --repo /path/to/project
python3 skills/remvu/scripts/remvu.py entries --repo /path/to/project --offset 0 --limit 20
python3 skills/remvu/scripts/remvu.py show ENTRY_OR_EVENT_ID --repo /path/to/project --max-chars 4000
python3 skills/remvu/scripts/remvu.py update --repo /path/to/project --proposal /tmp/memory-update.json
python3 skills/remvu/scripts/remvu.py handoff --repo /path/to/project
python3 skills/remvu/scripts/remvu.py check --repo /path/to/project --document /tmp/REMVU.md
```

`status` 与条目预览都有长度限制，只有显式 `status --full` 才读取完整状态。更新时记录 `base_revision` 和已经审阅的 `base_event_count`；水位之后的新事件继续待整理，省略水位不会确认任何新事件。`--proposal-json 'JSON'` 可替代 `--proposal FILE`，两者格式相同且不能同时使用。Hook 驱动的整理使用独立的 inline 更新命令，避免写 proposal 文件又产生新的编辑事件。

冲突经核对并应用协调后的修改后，用 `resolve-conflict ID --repo PROJECT --base-revision N --note TEXT` 记录处理结果，可重复 `--entry-id ID` 关联条目。原提案与处理记录一起保留。

用 `withhold ID [ID...] --repo PROJECT --base-revision N --note TEXT` 可将已选公开条目收窄为私有，并保留原始主张、依据和审计记录。它只影响后续分享，已生成的公开文件不会被改写。

接收方无需初始化本地记忆，便可运行 `check --document FILE --repo PROJECT`。更新格式见[合成示例](examples/remvu/)和 [proposal schema](spec/proposal.schema.json)。原有 `$agent-task-export` skill 和证据导出器继续保留；可通过 `import-legacy` 导入经过检查的旧记录包，或用 `legacy --help` 调用原命令，详见[迁移说明](docs/migration.md)。

[格式规范](spec/remvu-v1.md)、schemas 和兼容样例允许其他 agent 独立实现读写。开发与发布要求见 [CONTRIBUTING.md](CONTRIBUTING.md)。

```bash
python3 -m unittest discover -s tests -v
python3 spec/validate_examples.py
```

介绍文案按 [blader/humanizer](https://github.com/blader/humanizer) 规则润色；Humanizer 不参与运行。MIT License。
