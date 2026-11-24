---
name: analyze-test-case
description: 把已有人工用例整理为可自动化的前置、操作、预期与取证方案，固定原文快照并识别缺口。用于开始转换人工用例或排查脚本覆盖不完整，不负责自行扩展测试范围。
---

# 分析已有用例

测试任务先读[测试质量、缺口求助与逐条回执](../mino/references/execution-discipline.md)：缺口立即查证或问人，不编账号、不改原文预期；正式终态逐条在可见对话回执，调试/准备不计正式通过。

近期目标是把用户已有的人工用例转成可执行、可复用的 Python 脚本。先固定“要验证什么”，再用真实设备确定“如何操作”。脚本仍可自由使用 Python、flows 和 scripts；原文快照只描述人工用例，不另造动作语言。

## 原文与实现的边界

`requirement_list` / `case_list` 给的是需求索引与原文入口，不等于已拿到全部用例。打开 source_url 或读取用户提供的文件，确认本次用例正文与范围。保留原文内容及出处，不根据当前界面补写新预期。

## 全集清单门禁（写第一条脚本前）

用户说“所有用例”“全部用例”“继续把所有用例写完”时，范围是需求正文里的全部明细，不是当前 `tests/` 里已有的文件，也不是当前设备能立即跑通的子集。必须先从原文机器读取并锁定完整清单，再分析和编写。

飞书正文必须通过 MCP `cli_query` 的 `feishu` CLI 读取，不得用 Computer Use、浏览器截图或手工抄页面代替：

1. `wiki +node-get` 从文档/表格 URL 取得 Wiki node 与真实对象 token；
2. `sheets +sheet-list` 取得工作表、行范围和当前 revision；
3. `sheets +cells-get` 读取完整单元格区域，按原文稳定用例 ID 去重生成 `expected_case_ids`。

具体 options 以当前飞书 CLI `help` 为准；凭据、token 和完整正文不写入回复或仓库。非飞书来源同样要读取完整原文，并记录文件版本或内容哈希。

写脚本前必须先形成并保存这份清单：

```text
source_url
spreadsheet_token / sheet_id / range / revision（或本地文件哈希）
expected_case_ids（完整、唯一）
expected_total
当前 implemented / path_validated / formal_verified / blocked / missing
missing / verification_missing / blocked_units / next_units
implementation_complete / verification_complete
all_implemented / all_verified（complete 只是 implementation_complete 的兼容别名）
```

同时通过 `case_source_list → case_source_read` 取得成功 `read_id`，以 `source_read_id` 初始化 Nexus 工作记录；服务端从成功收据锁定完整 `expected_units` 和来源。`units` 只能是该全集子集，省略时默认全集。不得只传当前打算先写的几条；其余条目必须作为 pending 被看见。原文有重复 ID、空 ID、读取截断或范围未确认时先阻塞，不能猜全集。

当前脚本文件集合只能与 `expected_case_ids` 做差集，绝不能反过来当作用例全集。差集非空时继续按批次实现；任何“需求现有 N 条”“全部完成”的表述都必须满足 `N == expected_total` 或明确列出 `blocked` 与剩余 ID。

逐条检查：

- **前置**：环境、应用版本、账号身份、业务状态、权限、数据。哪些已知，哪些需要在设备上验证，哪些目前无法建立。
- **操作**：原文目标、涉及的应用与页面、需要的数据。页面文字不是选择器，真实 locator 要在 Scout 观察后确定。
- **预期**：明确要证明的业务事实、可观察证据和断言方式。页面打开、按钮点击成功都不能替代业务预期。
- **收尾**：会改变什么状态，哪些可以明确恢复，哪些写操作不能盲目重试。

选择文本/节点、数据比较或视觉证据来验证每一条预期。存在多个合理含义且会改变结论时，把具体缺口交给用户；先继续不依赖该答案的分析和采集。原文缺失与产品不符合原文分别记录，不把它们都归为脚本失败。

## 用例来源变量与执行快照

飞书表格是用例正文的唯一维护入口。新用例不创建同名 YAML，在 Python 顶层声明字面量 `CASE_SOURCE`：

```python
CASE_SOURCE = {
    "kind": "feishu_sheet",
    "url": "https://example.feishu.cn/wiki/TOKEN?sheet=SHEET_ID",
    "sheet_id": "SHEET_ID",
    "range": "A2:H1000",
    "case_id": "order_total",
    "columns": {"case_id": "A", "preconditions": "D", "steps": "E", "expectations": "F"},
}
```

链接、工作表、范围、稳定用例 ID 和列位置来自实际读取结果，不猜位置。`case_id` 按单元格值唯一匹配，不绑定易移动的行号。每个前置、操作、预期单元格内一条原文占一行；可在飞书中使用 `P1:` / `S1:` / `E1:` 等稳定编号。未显式编号时按非空行顺序生成对应编号。

Scout 在每次执行前通过本机已授权的飞书插件读取当前原文，固定内容哈希、来源位置和读取时间，归档到该次执行记录。用户只维护飞书和 Python，不手动维护快照文件。原文读取失败、内容不完整、用例 ID 不唯一、预期缺失或引用不匹配时必须阻塞，不能回退到旧快照继续运行。

用 `prep/do/check(title, source_ref="P1/S1/E1")` 关联原文。多块实现可以引用同一条原文；修改飞书的步骤结构后仍需核对 Python 的映射和业务断言。静态检查只验证来源变量配置，运行记录才证明原文覆盖和断言通过。

已有同名 YAML 保留兼容；迁移到 `CASE_SOURCE` 时删除同名 YAML，禁止两个来源并存。账号密码和验证码只从项目账号资源取得，不放入来源变量或飞书用例。

## 转入编写

将每条原文映射到准备动作、操作与有效断言，必要时附依赖和缺失数据。确定被测应用和设备后进入 [write-test-cases](../write-test-cases/SKILL.md)。已有前置流程可复用，但必须核对它是否实际建立本用例所需状态。

区分三个完成度：

- **静态映射完成**：原文条目有实现引用，文件和引用校验通过。
- **路径执行完成**：真实设备上的动作走通，有对应观察记录。
- **预期验证完成**：每条预期实际执行了有效断言并有证据。产品有缺陷时，可信的失败用例仍是有效自动化产物，应报告失败依据。

只有采集截图、只写标题或只通过静态 check，都不能称为完整测试。若暂时只能探路，保留本次 blocked 与采集记录，继续补定位和断言；不得把采集任务算成通过。

## 输入数据与对象关系

跨多轮分析与实现时，按 [Agent 进度与预算](../mino/references/workflow-ledger.md) 通过 Nexus MCP 初始化工作记录，分别跟踪分析、编写、准备及验证。原文缺口或重复阻塞记录具体事实，继续独立条目；分析 complete 不等于路径或预期已验证。

分析时区分原文前置、需要的数据、被测行为和辅助标签；不要因为资产台账缺失增加库存确认或标签门禁。记录数据生产者、消费者、运行时对象引用，以及跨页/跨应用需要验证的关系。缺数据由 Agent 在授权范围内准备；脚本仓只执行明确操作，不能内置自动补数策略。分析交付与被测执行分开，用户仅要方案时不运行用例。
