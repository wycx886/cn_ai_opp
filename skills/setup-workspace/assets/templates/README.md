# 空白模板

这里只维护通用结构，不填写真实个人信息。首次由 Agent 先获取简历、整理事实并访谈偏好；初始化程序仅将空白模板复制到被忽略的 `workspace/`，可导入明确指定的简历原件；若使用已有私人工作区，初始化只保存本地路径配置，不复制另一套档案。

| 模板 | 私人工作区中的用途 |
| --- | --- |
| [workspace-agent-rules.md](workspace-agent-rules.md) | `AGENTS.md`，合并目录说明与维护规则的唯一工作区入口 |
| [profile.md](profile.md) | `profile.md`，本人事实基准 |
| [preferences.md](preferences.md) | `preferences.md`，目标和约束 |
| [applications-index.md](applications-index.md) | `applications/index.md`，公司路由与状态摘要 |
| [application-log.md](application-log.md) | 有实际任务时复制到 `applications/<organization-id>/log.md`，公司状态摘要与内部路由 |
| [communication-note.md](communication-note.md) | 公司 `records/YYYY-MM-DD 渠道 人物.md`，一次沟通的详细记录 |
| [outreach-draft.md](outreach-draft.md) | 公司 `applications/<公司>/materials/` 中的未发送草稿 |

初始化与复用已有资料的命令见 [本地工作流](../../references/workflow.md)。
