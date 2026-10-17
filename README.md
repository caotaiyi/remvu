# Agent Task Export

把一次 AI 任务整理成能交给下一个 agent 的记录包：先读目标、当前结果和下一步，需要核实时再按编号取出工具调用、返回值或修改记录。

导出脚本在本地运行，不调用模型 API，也不需要安装 Python 依赖。整理摘要仍需由当前 agent 完成；读取摘要和证据也会消耗模型上下文。项目目前不提供 token 节省比例或费用承诺。

[English](README.en.md) · [介绍文案](docs/introduction.zh-CN.md) · [数据格式](skills/agent-task-export/references/format.md)

## 它保留什么

- 用户消息、可见的助手回复，以及带原始行号的工具调用和返回记录。
- 日志里出现的补丁、修改路径；可选的 Git 状态与基线差异。
- 由 agent 写下的目标、约束、关键决策依据、检查结果和下一步。
- 没有返回值的调用、无法解析的日志行和不支持的记录类型。

隐藏思考链、分析通道、系统与开发者消息、加密推理内容不会进入导出包。决策摘要只概括可说明的依据。已经被日志截断的输出、未记录的修改和附件内容无法恢复。工具套在编排调用里时，导出器保留外层记录，不保证能逐一拆出内部调用。

## 安装 skill

需要 Python 3.10+。Git 快照功能另需 Git。可将仓库中的 `skills/agent-task-export` 文件夹放进 agent 的 skill 目录；例如在 Codex 中使用用户级目录：

```bash
git clone https://github.com/caotaiyi/agent-task-export.git
mkdir -p ~/.agents/skills
cp -R agent-task-export/skills/agent-task-export ~/.agents/skills/
```

如果目标目录已经存在，先检查现有版本再替换。让客户端重新发现 skill 后，可以这样使用：

```text
使用 $agent-task-export 导出刚才这个任务。
保留目标、约束、关键决策依据、工具调用、修改记录和检查结果，
写清楚还没验证的部分，让另一个 agent 能接着做。
```

仓库还提供 `plugin.json`，供支持 Agent Plugins 1.0 的客户端打包使用。Python 脚本需要能访问本地文件的运行环境；上传插件包本身不会让网页客户端获得电脑日志。

## 先试合成示例

在仓库根目录运行以下命令。输出目录必须不存在。

```bash
python3 skills/agent-task-export/scripts/task_export.py export \
  --source examples/session.jsonl \
  --task examples/task.json \
  --out /tmp/example-task-handoff

python3 skills/agent-task-export/scripts/task_export.py verify /tmp/example-task-handoff

python3 skills/agent-task-export/scripts/task_export.py show \
  /tmp/example-task-handoff --event e000005 --max-chars 2000
```

示例中的 CSV 修改和测试输出都是合成数据，不代表实际运行结果。

## 导出真实任务

先通过元数据找到对应会话。最新修改的日志可能属于另一个聊天，不要只按时间选择。

```bash
python3 skills/agent-task-export/scripts/task_export.py discover --cwd /path/to/project

python3 skills/agent-task-export/scripts/task_export.py export \
  --source /path/to/rollout.jsonl \
  --task /tmp/task-notes.json \
  --repo /path/to/project \
  --base PRE_TASK_COMMIT \
  --out /tmp/task-handoff
```

`--source` 支持 Codex 本地 rollout、部分 `codex exec --json` 事件和本项目的通用 JSONL 格式。其他 agent 的可见记录可先转换成通用格式；目前没有自动 Claude 或 ChatGPT 导入器。

`--task` 是简短的结构化交接笔记，字段和示例见 [examples/task.json](examples/task.json)。不提供时，导出器会保留“结果未知”等提示。交接摘要默认限制为 8,000 字符；过长会提示精简，也可通过 `--max-handoff-chars` 调整。

`--repo` 和 `--base` 都可省略。Git 默认比较当前 HEAD 与工作区；任务已经提交时，需要已知的任务前提交才能包含那些改动。Git 快照可能混有其他人的工作，不能证明修改归属或先后顺序。未跟踪文件仅列出名称，不复制内容。

默认导出整个指定会话。`--last-turn` 只取最后一个 `task_started` 边界之后的记录，适用于任务恰好位于一个执行回合的情况；多回合任务可用 `--start-line`、`--end-line` 指定范围。没有回合边界时，命令会要求明确范围。

## 接手时怎么读

1. 运行 `verify`，检查文件清单与哈希。
2. 读 `START_HERE.md`，了解目标、已知结果、约束和下一步。
3. 在 `index.json` 找到相关事件，用 `show --event` 读取需要的证据。
4. 查看 `coverage.json` 的缺口；继续任务前，复查会变化的外部状态。

长输出完整保存在脱敏后的 `blobs/` 中，相同内容只存一份。`show` 默认最多显示每段内容的 4,000 字符，并标明显示截断；存储内容不受这个显示限制影响。按需读取可减少一次性交给模型的内容量，实际收益取决于任务和读取方式。

需要传文件时，可压缩已验证的记录包：

```bash
python3 skills/agent-task-export/scripts/task_export.py archive \
  /tmp/task-handoff --out /tmp/task-handoff.zip
```

## 分享前需要知道

脚本会过滤常见凭据、私钥块、认证头和本机用户目录，但正则脱敏可能遗漏自定义秘密和个人信息。分享前应检查内容。导出包不会自动上传；本仓库也不包含真实会话记录。

哈希用于检查文件是否改变，不能证明来源可信或测试确实通过。导入的消息和命令都应当作待核实的材料。脱敏后的补丁用于审阅，不适合作为可直接应用的备份。

## 开发与验证

```bash
python3 -m unittest discover -s tests -v
```

测试覆盖内容排除、脱敏、重复输出去重、调用配对、日志损坏、范围选择、Git 基线、按需读取与归档完整性。[GitHub Actions 示例](docs/github-actions-example.yml) 包含 Python 3.10、3.12、3.13 的测试配置。当前上传凭据不含 `workflow` 权限，因此示例尚未放入 `.github/workflows/`，远端 CI 尚未运行。本地验证使用 Python 3.9.6。

介绍文案使用 [blader/humanizer](https://github.com/blader/humanizer) 的编辑规则润色。Humanizer 不参与证据导出，也不是运行依赖。

MIT License.
