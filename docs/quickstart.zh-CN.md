# 在项目中安装 Remvu

把下面这段话交给 coding agent：

> 请从 https://github.com/caotaiyi/remvu 为当前本地项目安装 Remvu。
> 先阅读当前版本状态和兼容报告，检查 Python 3.10+ 与 Git；缺少时协助我从
> 官方来源安装。审阅源码后，将它克隆到项目之外，使用 scripts/install.py
> 安装到当前项目，再用安装结果给出的稳定脚本路径运行 doctor。保留已有配置
> 和私人数据，引导我完成客户端正常的 hook 信任流程。分别说明配置是否完成、
> 是否观察到执行，以及当前入口是否经过真实验收。

当前主分支提供 **v0.3.0-beta.1 候选实现**，12 种入口组合的真实验收尚未完成。
已经发布的 v0.2.0 及其证据继续保留，不能据此认定新版已通过验收。

审阅源码后，也可以手动安装：

```bash
git clone https://github.com/caotaiyi/remvu.git
python3 remvu/scripts/install.py --repo /项目的绝对路径 --platform both
```

Windows 使用 Python 3.10+ 对应的启动命令替换 `python3`，例如 `py -3.12`。
安装器检查 Python 和 Git，将 skill 复制到稳定的用户目录，再合并项目配置。
它不会代替你登录或授予 hook 信任，安装后可以移动原来的克隆目录。
只配置一个客户端时选 `--platform claude` 或 `codex`；新项目仅使用 CLI 时选
`none`。`none` 不会卸载已有适配器。

按客户端要求完成 hook 审查和重启，再调用 `/remvu doctor` 或 `$remvu doctor`。
本地执行回执能帮助排错，不能证明自动整理已完成，也不能识别桌面或 IDE 入口。
找不到 skill 时，先使用安装结果中的 CLI 路径，并确认客户端打开的是项目根目录。

平时调用 `/remvu` 或 `$remvu` 更新本地交接。需要可分享文件时再调用 `share`，
并检查生成的 `REMVU.md`。接收方只需要代码和这个文件。自动维护尚未验收的入口
可以尝试手动命令，但兼容状态仍保留待验证。

[维护与恢复](../skills/remvu/references/maintenance.md) · [常见问题](faq.md) ·
[Windows 与其他入口验收](native-acceptance.md)
