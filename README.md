# aipm-dev-skills

面向 AI PM 与 Builder 的轻量工作流 Skills：把产品判断转成可执行的范围、验收与交付约束。

状态：0.1.0-beta.2。按需加载，按风险执行；不是强制全委托，也不是完整 Agent 平台。本文是基础使用说明，可继续按项目定位调整。

## 从哪里开始

| 任务 | Skill |
| --- | --- |
| 产品发现与方向取舍 | [product-discovery](skills/product-discovery/SKILL.md) |
| 定位代码与复用能力 | [aipm-explore](skills/aipm-explore/SKILL.md) |
| L0–L3 分级计划 | [aipm-plan](skills/aipm-plan/SKILL.md) |
| 明确任务的独立执行 | [aipm-delegate](skills/aipm-delegate/SKILL.md) |
| 根因修复 | [aipm-bug-fix](skills/aipm-bug-fix/SKILL.md) |
| 按风险审查代码 | [aipm-code-review](skills/aipm-code-review/SKILL.md) |
| 用户旅程与发布验收 | [delivery-check](skills/delivery-check/SKILL.md) |
| 事件语义与数据证据 | [telemetry-audit](skills/telemetry-audit/SKILL.md) |
| 文档、测试和分支治理 | [aipm-govern](skills/aipm-govern/SKILL.md) |

## 安装与检查

Python 3.11+，安装和检查脚本只依赖标准库。在下载/克隆后的包目录运行：

```sh
python scripts/check.py --force
python scripts/install.py --project /absolute/path/to/project
python scripts/install.py --project /absolute/path/to/project --apply
```

默认预览；目标项目须已存在。安装到 `.agents/skills`，完整复制引用资源，不覆盖不同内容，不修改目标 `AGENTS.md`。将 [项目入口模板](templates/AGENTS.project.md) 按需合入团队规则。

卸载也先预览，只有清单拥有且未修改的文件会删除：

```sh
python scripts/install.py --project /absolute/path/to/project --remove
python scripts/install.py --project /absolute/path/to/project --remove --apply
```

从旧 `oil-*` 活动入口升级：先预览并卸载本包拥有的旧文件，再预览安装新名称；个人修改和独立 Oil 安装保留，由使用者决定迁移。当前版本不自动合并自定义 Skill。安装清单是可信本地记录，不是防篡改认证。

## 执行原则

- 小任务直接做，独立产物/隔离/审查确有收益才委托；L0–L3 不等于派单数量。
- 入口→正文→必要 reference 渐进读取；命令和采集优先使用脚本，日志留本地，只返回必要摘要。
- 交接与换聊天由用户决定，不按阶段自动打断。
- 用户可观察的完成、失败恢复和下一步都属于验收；算法通过不等于体验完成。
- 只复用输入、版本、命令、环境和 Git 状态匹配的成功证据；失败先诊断，CI/发布门禁新跑。
- 不用“部署完成”代替公开访问与实际旅程，不用本地事件代替分析后台入库。

## Codex 委托

需要已认证且支持所请求型号的 Codex CLI。先预览契约：

```sh
python skills/aipm-delegate/scripts/run_task.py --contract templates/task.example.json --dry-run
```

去掉 `--dry-run` 才实际运行。默认只读；implement 才使用 workspace-write。续接绑定任务、工作区、角色、范围和模型档位；不静默换模型。请求型号不等于实际型号，无法从运行元数据证实时保留未知。

`allowed_paths` 是工作合同，不能代替逐文件权限沙箱；运行状态串行写，不能让多个协调者同时操作。`.aipm/` 可能含提示、代码和用户路径，不能提交。请先阅读相关入口及其限制。

## 文档与局限

- [来源与适配](docs/changes.md)
- [匿名案例](docs/case-study.md)
- [验证与限制](docs/validation.md)
- [耗时与 Token 审计](docs/cost-audit.md)

本包已有确定性测试与最小真实 CLI 证据，但没有证明跨项目收益、质量提升或 Token 节省比例。不是所有上游 runner 的兼容实现。

## 许可证

新增内容采用 [MIT](LICENSE)。以 Oil 为工程基础，参考 Addy 的生命周期与交付实践；保留 [版权声明](notices/OIL-MIT.txt)、固定原始快照与锁文件。活动派生 Skill 使用 `aipm-*` 名称，原始来源不改名；这不表示上游工程代码全部重写，也不代表原作者背书。
