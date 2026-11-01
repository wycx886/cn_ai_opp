# 最小私人工作区与初始化流程

公共仓库保存方法、空白模板和公开研究；个人事实、偏好、简历与具体机会进展只保存在一个被忽略的私人工作区。

## 默认结构

```text
workspace/
  AGENTS.md
  profile.md
  preferences.md
  resume/
  applications/
    index.md
```

工作区根目录的 `AGENTS.md` 同时承载目录说明与维护规则，不再另建根目录 `README.md`。投递与沟通规则也合并在这一份文件中，applications 不另设 AGENTS 或 README；`applications/index.md` 只作公司路由与状态摘要。

公司 `log.md`、`records/`、`materials/` 按具体个人任务创建，不设 inbox。只有用户明确要求时才建立 `archive/` 并移动指定公司；猎头关系按实际任务记录。不初始化重复的方法、研究、通用草稿或临时目录；简历原件和生成版本进 `resume/`，公司定制草稿进其 `materials/`。

## 新使用者

1. 先检查是否已有个人资料或已提供简历；没有时请用户提供简历文件、本地路径或履历文本。
2. 创建被忽略的工作区，可导入明确指定的简历原件：

```bash
python3 skills/setup-workspace/scripts/init_local.py --resume-file /path/to/resume.pdf
```

程序只建骨架、可复制原件，不执行事实提取。即使手动空跑初始化成功，个人资料仍处于待整理状态。Agent 随后读取简历，按 [事实模板](../assets/templates/profile.md) 整理来源、时间、职责、技能和成果，列明冲突和待核对项，向用户展示摘要。

3. 基于履历提出约 3–5 个候选行业／岗位／地点方向，写入 [偏好模板](../assets/templates/preferences.md) 的建议区，询问用户的行业选择、岗位、期望地点和用户输入的薪资范围及口径。简历所在地、历史收入和 Agent 建议都不能自动成为用户偏好。
4. 用户确认后更新偏好确认区；未决项保留待确认。薪资可明确选暂不设门槛／面议，不因缺失薪资而擅自排除机会。

个人初始化不需要将简历上传到公共仓库；公开公司、渠道、人物和岗位研究也不要求先提供简历。

## 已有工作区

已有 `profile.md` 与 `preferences.md` 时只绑定：

```bash
python3 skills/setup-workspace/scripts/init_local.py --workspace ../my-private-workspace --use-existing
```

仅保存被忽略的本地路径配置，不复制、改写、重新提取或删除旧内容，不强迫已有用户重走首次访谈。新简历的更新是另一个明确任务，先比较差异后更新事实基准，原件保留。旧目录不会因使用新模板而自动删除。

## 个人机会与记录

用 [日志模板](../assets/templates/application-log.md)、[沟通模板](../assets/templates/communication-note.md)、[未发送草稿模板](../assets/templates/outreach-draft.md)。`applications/index.md` 是公司路由；公司 `log.md` 汇总当前状态、各联系线结论与下一步，并链接公司内的 records、materials 和历史依据。每次会话或独立沟通事件的详细经过单独记入公司 `records/YYYY-MM-DD 渠道 人物.md`，同日重复时用已知 `HHmm` 或递增序号区分；未知部分标待核实，不编人物或日期。log 不重复堆积完整聊天流水；定制简历、联系草稿和面试准备进 `materials/`。按用户原有简历构建约定生成，不能手改其要求通过源文件构建的成品。

多 Agent 按公司分工，同一公司由一个写入者维护日志；其他补充直接存该公司 `records/` 的唯一原始记录，再核对并更新公司 log 的摘要与路由。主体不明时记在索引的待核实区，跨公司原始依据确需保留时可存 `applications/records/` 并由日志引用，不另建待处理队列。公开研究直接写共享 `data/companies/`。

无论本人主动拒绝还是招聘方拒绝，先更新对应联系线；不自动归档整家公司。仅按用户明确要求移到 `applications/archive/`，保留原记录、其他联系线状态及不再接触要求，并同步索引与链接。

草稿、真实发送和收到回复分别记录；对外动作沿用使用者明确授权与本地规则。共享提交与私人隔离见 [工具说明](../../../tools/README.md)。
