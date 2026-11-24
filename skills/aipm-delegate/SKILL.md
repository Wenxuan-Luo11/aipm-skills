---
name: aipm-delegate
description: 将边界清楚的实现、探索或独立审查交给 Codex CLI，选择任务模型与权限，返回结构化结果并续接会话；需要实际委托或排查运行器时使用，不用于普通问答或自动拆分小修。
license: MIT
metadata:
  version: "0.1.0-aipm"
---

# Codex 按需委托

本派生版复用 Oil 的 runner、会话续接与结果解析。v0.1 仅启用 Codex；其他上游 runner 保留来源，但实际调用会拒绝。不安装、不登录、不默默换模型。

## 选择最小执行

小修当前 Agent 完成；独立薄片用一个实现者完成代码和快测；核心规则或重要变更才加独立只读审查。不同写任务用独立工作区。不要把主会话完整历史传给执行者。

契约包含目标、工作区、角色、复杂度、入口文件、允许改动、验收命令、交付物及停止条件。缺少真实路径/命令先查清；不把验收命令字符串当作已经运行。

## 运行

先看 [模型与权限配置](references/routing.json)。只有任务明确属于 visual/deep 时使用对应档位，常规任务走 routine。配置是候选选择，不保证该账号可用；拒绝时如实报告，不静默降级。

从本 Skill 所在目录运行：

```text
python scripts/run_task.py --contract /path/to/task.json --dry-run
python scripts/run_task.py --contract /path/to/task.json
```

`run_task.py` 校验契约，按角色确定 read/write，并调用同目录 `delegate.py`；只执行一次，不自动重试/升级。review、critique、explore 始终只读；implement 才允许 workspace-write。调用状态放在目标工作区 `.aipm/delegate`，加入项目忽略规则，不提交原始提示或事件日志。

直接调用仍可用：

```text
python scripts/delegate.py run --runner codex --workspace /path/to/project --mode read --model gpt-6.1-sol --effort low --prompt "按约定只读核查并报告证据" --json
```

默认 read；写模式保留 workspace-write 沙箱，不使用最高权限。新调用返回 session_id；追问同一任务时使用 `--session`，只传新发现。角色隔离不等于不同模型；审查者不能照抄实现者的结论。

## 验收与边界

结果中的 model/model_source 是请求来源，不能冒称实际运行模型。`actual_model` 只在 CLI 事件明确提供时填写，否则 unknown。确认真实改动范围、测试退出码和产物，再宣布完成。可核验的 Git/文件快照用于只读不变性检查；沙箱不是每文件允许清单，allowed_paths 仍需调用方审计。

非零退出、超时、登录失败先诊断；不盲重试，不扩大权限绕过。宿主策略和用户授权优先。CLI 未认证或环境不支持时报告限制，可回到宿主原生委托，不假装 CLI 已成功。

来源与原始适配文档见仓库 upstream/oil-dev-skills；本 Skill 的代码改动和验证见仓库 docs/changes.md、docs/validation.md。
