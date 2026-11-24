# 探索采集与个人偏好

仅在陌生仓库采集、查偏好或用户要求修改偏好时阅读。`SKILL_DIR` 指本 Skill 的绝对目录；使用可用 Python 3.11+。结构采集入口：

```text
python <SKILL_DIR>/scripts/repo_map.py --workspace <项目路径> --json
```

遵循 Git 忽略规则，采集目录、规范、已定义脚本、CI运行命令和工作树。先用 --help 确认可选参数；直接运行，无需预读脚本源码。已知路径的 quick/medium 查询直接检索，不强跑采集。若输出太大，程序提取相关字段，只把路径与摘要送入上下文。

只在用户设置偏好、或独立探索确实需要时读取：

```text
python <SKILL_DIR>/scripts/preferences.py get aipm-explore --host <宿主>
```

旧 ~/.oil-dev/preferences.md 及 OIL_DEV_HOME 保持兼容。shared 为跨宿主设置，host_text 为宿主覆盖；不能越过项目规则、当前用户指令或权限限制。无配置/读取失败使用可用最小流程，不为此打断任务。模型不可指定时如实报告，不能声称切换。

用户明确要求保存偏好时先 get，合并现有内容，再 set（整段替换）：

```text
python <SKILL_DIR>/scripts/preferences.py set aipm-explore --host <宿主> --text <合并后的文字>
```

所有宿主用 --all-hosts；查看用 show；删除单宿主设置用 unset aipm-explore --host <宿主>。写入前确认已获授权，失败报告错误，不改全局环境来绕过。并行切片与摘要格式只在需要时读 parallel-exploration.md。
