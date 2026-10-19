# Remvu

Claude Code 额度快用完时保存，换到 Codex 继续做。

Remvu 把项目目标、约束、被否决的方案、未完成事项和检查依据留在项目里。完整独立程序自带运行环境，**用户不用安装 Python**，自动记录、代码指纹、并发保护、损坏恢复和分享隔离均保留。

[English](README.md) · [安装](docs/quickstart.zh-CN.md) · [DeepSeek Harness 插件](adapters/dsh/README.md) · [验证与限制](docs/standalone.md)

## 交给 agent 安装

> 从 https://github.com/caotaiyi/remvu 为我的系统和架构安装完整 Remvu 独立程序候选版。校验下载包，解压整个程序文件夹，再为当前项目安装。保留已有配置与记忆，引导我完成客户端正常的 hook 信任审查。不要安装系统 Python，也不要换成仅笔记版。

v0.3.0-beta.2 仍是测试候选版。CI 生成各平台程序包；正式发布与客户端支持范围需要逐项真实验收。下载和校验方法见[独立程序说明](docs/standalone.md)。仍需 Git，macOS 分发签名和公证尚未配置。

| 日常操作 | Claude Code | Codex |
| --- | --- | --- |
| 保存本地交接 | `/remvu save` | `$remvu save` |
| 新会话接手 | `/remvu resume` | `$remvu resume` |

`save` 让当前 agent 整理已审阅的证据，生成私有 `.remvu/handoff/REMVU.md`。直接运行程序而不提交整理内容时，只导出现有状态，待整理记录仍保留。保存不会提交代码或上传文件。接收方只拿代码和交接文件也能继续，无需安装 Remvu。

在原 agent 还能响应时保存。自动日志能留下操作事实，无法补出额度耗尽后未写下的理解。Stop hook 不阻塞结束，也不强迫模型再跑一轮。

## 30 秒了解交接流程

1. 在 Claude Code 中调用 `/remvu save`。
2. 用 Codex 打开项目，调用 `$remvu resume`。
3. 核对下一步、过期检查、待整理证据和冲突，继续任务。

这是流程说明，不是完成时间保证。[早期真实接手记录](docs/validation-report.md)和[十任务仅笔记对照实验](docs/product-validation.md)均保留原始结论与限制。后者未显示比普通 HANDOFF 笔记更高的首轮准确率，也没有测量本次独立程序或证明 token 节省。

## DeepSeek Harness 插件

`dsh-remvu` 为 DeepSeek Harness **0.2.1-rc.2** 提供五个原生工具和可观察事件记录，使用同一套独立引擎与本地记忆。插件已经写成 JavaScript，安装无需编译或执行构建脚本。[安装说明](adapters/dsh/README.md)。

已通过官方插件安装流程，并在隔离的真实 SDK 配置中加载；验证过程未请求模型。真实模型接手和 GUI 验收仍待完成。当前适配本地项目，不宣称远程文件系统或云端执行兼容。

## 保留完整功能

记忆区分用户确认、工具观察、agent 推断和待核实内容。旧决定与被否决方向保留历史。检查结果绑定当时的代码指纹，代码变化后不能沿用旧的“通过”。并发提案需核对版本，不能静默覆盖另一方记录。

本地记忆与详细证据留在忽略的 `.remvu/`。只有显式分享才生成公开 `REMVU.md`，公开依据需能独立阅读，未提交补丁需单独审阅。隐藏思考链、凭据和无关对话不导出。排错、恢复、升级、回滚、卸载等能力仍在，卸载保留私人记忆。

## 面向多模型平台与 API 中转站

换模型、换客户端，把项目背景一起带走。能观察本地项目改动和工具结果的平台，可嵌入记忆引擎或编写适配器。纯 API 转发无法完整看到项目操作，不能承诺完整记录。DSH 是已有的本地主机适配，尚无通用中转站集成或节省比例的实测结论。

需要更轻的路径时，可主动选择[仅笔记备用版](skills/remvu/assets/markdown-skill.md)；开发者也可继续运行标准库 Python 源码。完整独立程序是本轮主交付。

[开放格式](spec/README.md) · [兼容状态](docs/compatibility.md) · [贡献指南](CONTRIBUTING.md) · [MIT 许可](LICENSE)。继续支持 `remvu/1` 和旧证据格式导入。
