# Agent 进度、重复阻塞与调查预算

理解需求、编写脚本、准备数据和正式验证分别记录为 `analysis/authoring/preparation/verification`。进度通过 Nexus MCP 保存到服务端当前数据库，按登录用户与 workflow_id 隔离；Python 部署使用 SQLite，Cloudflare 部署使用 D1。Agent 和 Scout 都不创建本地进度数据库。

先调用 `agent_guide` 确认当前服务提供 `agent_workflow_init/start/finish/resolve/get`。scope 包含项目、需求和本次范围，独立用例或缺口作为 unit。同一 workflow_id 继续使用原范围和预算，不能重置预算来绕过收敛。每个 unit、阶段默认 6 轮，整个 workflow 默认 24 轮；按已授权范围在 init 配置。普通任务状态轮询不另占调查预算。

```json
{"workflow_id":"custom-trade","scope":"PRJ005 / 定制交易二期 / 当前批次","units":["model-preview","purchase"],"stage_budget":6,"total_budget":48}
```

上面的对象传给 `agent_workflow_init`。每轮调查明确要消除的不确定性、动作、现有事实及是否包含写入，调用 `agent_workflow_start`：

```json
{"workflow_id":"custom-trade","attempt_id":"model-preview-1","unit":"model-preview","stage":"authoring","action":"按本次节点修正生成入口定位","blocker":"locator_missing","evidence":["生成入口当前可交互节点 role=link，位于生成面板"],"writes":false}
```

`allowed=true` 才开展声明的这一轮调查。它只表示调查预算允许，不授予执行权限，不修改 Nexus 资源约束或原文条件。Agent 决定下一步，服务只记录。`allowed=false` 时按 reason/next 读取已有尝试、改变有依据的方案或交付阶段。某条受阻后继续独立条目，不能重复申请账号等待完美匹配。

调查完成后调用 `agent_workflow_finish`，支持 progress、blocked、complete、failed、deferred。blocked/failed 必须描述具体 blocker；complete 必须有事实证据。已结束记录不可改写，同内容幂等。ACK 丢失后再次 start 同一个 attempt_id 返回 attempt_exists，不授权重复执行；先用 `agent_workflow_get` 读取历史和原 task_id。

证据使用实际观察的语义指纹或稳定内容哈希，保存少量引用；不保存凭据、图片或完整事件。新增时间戳、另一个 task_id、重排或重复读取同一事实不算新证据。task_id 单独传入 finish。相同 unit、阶段、动作和阻塞无新增事实时，start 返回 repeated_blocker_without_evidence；阶段预算耗尽交付该阶段，总预算耗尽交付当前范围和剩余工作。

业务写入调查在 start 传 `writes=true`。写结果未知时 finish 必须传 `write_outcome="unknown"` 与原 task_id，该 unit 的下一次写入会返回 write_outcome_unknown。只读查询原任务和独立 unit 可继续。核对原任务和对象后调用 `agent_workflow_resolve`：

```json
{"workflow_id":"custom-trade","attempt_id":"prepare-1","task_id":"原准备任务ID","evidence":["原任务已结束，创建回执与本次对象 ID 已核对"]}
```

resolve 追加同一任务的核对事实，保留原 attempt 的 unknown 历史，不修改测试结论或解除资源隔离。并发冲突返回 409 时先读取原 attempt，不能重放结果未知的写入。

`agent_workflow_get` 分列四阶段状态、消耗与剩余预算、全部调查历史、原任务、未核对写入及独立待办。verification complete 仅是 Agent 的交付记录，正式测试结论仍须引用原 Scout 任务断言与证据。源码实现完成、等待打包验证和正式验证通过分别表达。
