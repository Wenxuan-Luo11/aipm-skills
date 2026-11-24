# aipm-dev-skills

按任务加载一个相关入口，再按需读取其参考文件；不全量预加载。定义→计划→构建→验证→审查→发布仅作进度坐标。

| 任务 | 入口 |
| --- | --- |
| 产品发现 | [product-discovery](skills/product-discovery/SKILL.md) |
| 定位代码 | [aipm-explore](skills/aipm-explore/SKILL.md) |
| 分级计划 | [aipm-plan](skills/aipm-plan/SKILL.md) |
| 独立委托 | [aipm-delegate](skills/aipm-delegate/SKILL.md) |
| 修复缺陷 | [aipm-bug-fix](skills/aipm-bug-fix/SKILL.md) |
| 审查改动 | [aipm-code-review](skills/aipm-code-review/SKILL.md) |
| 体验与发布验收 | [delivery-check](skills/delivery-check/SKILL.md) |
| 埋点证据 | [telemetry-audit](skills/telemetry-audit/SKILL.md) |
| 文档、测试与分支治理 | [aipm-govern](skills/aipm-govern/SKILL.md) |

## 执行约定

- 用户最新决定优先；不把案例的产品、平台、期限或模型固化为通用约束。已有授权继续，未决取舍或新增范围再对齐。
- 先查工作区与用户改动；feature 分支开发，经 PR 合并，不直接 push main。外部操作遵循宿主权限，不绕过拒绝。
- 确定性事实先用已有脚本/CLI。小修直接执行，按风险做相关检查；不默认委托、全库扫描或反复重测。模型切换和委托须有实际运行证据。
- 批量独立读取，日志留文件，只返回必要摘要。按输入/版本复用成功证据；CI/发布门禁新跑，失败先诊断。详细预算仅需要时读 [上下文指南](skills/aipm-plan/references/context-handoff.md)。
- 每批简报当前阶段、验收项、调用复杂度与等待来源；执行中报已验收数、证据和下一项。时间有依据才估，无实测标明粗估。
- 交接与换会话由用户决定，原型和连续小修默认继续；不因阶段变化自动打断。
- 保留来源和许可，`upstream/` 不改。原始提示、凭据及事件日志留在被忽略的 `.aipm/`，不提交或对外分享。

## 本包检查

`python scripts/check.py` 汇总本地检查；`--force` 强制新跑。`python scripts/validate.py` 单独核对清单、资源、许可与上游哈希。未运行的检查不报通过，dry-run 不算真实委托。
