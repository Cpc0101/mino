# Agent 进度、重复阻塞与调查预算

理解需求、编写脚本、准备数据和正式验证分别记录为 `analysis/authoring/preparation/verification`。进度通过 Nexus MCP 保存到服务端当前数据库，按登录用户与 workflow_id 隔离；当前 Python 部署使用 SQLite。Agent 和 Scout 都不创建本地进度数据库。

先调用 `agent_guide` 确认当前服务提供 `agent_workflow_init/start/finish/resolve/get`。scope 包含项目、需求和本次范围，独立用例或缺口作为 unit。同一 workflow_id 继续使用原范围和预算，不能重置预算来绕过收敛。每个 unit、阶段默认 6 轮；总预算默认至少为 `expected_units × 4`，42 条用例即至少 168 轮。普通任务状态轮询不另占调查预算。

“所有用例”必须先从原文锁定 `expected_units`。`units` 只能是它的子集，可只声明首批 5–10 条；后续 `start` 会自动登记 `expected_units` 内的新 unit，不能因此缩小全集。省略 `units` 时服务端默认声明全部 `expected_units`，这样未开始的条目也会显示为 pending。先用 `case_source_list → case_source_read` 取得成功 read_id；init 传 source_read_id，服务端从该收据固定来源与全集。不得用当前 `tests/` 文件清单创建 expected scope，也不得在后续 init 中缩范围。

执行阶段同样不能把 `case_run` 的 `script_targets[].case_ids=[]` 当成原文全集：它只展开 `tests/<需求ID>/` 下当前已有的脚本。用户要求“继续测试/跑所有用例”时，先读取 workflow 的 `expected_units`、`coverage.missing`、`coverage.verification_missing` 和 `coverage.blocked_units`；缺脚本则继续实现，已有脚本执行结果只能报告为当前已实现子集，不能写成需求全集通过。

```json
{
  "workflow_id":"overseas-zh-cn",
  "scope":"海外后台 / 新增语言中文 / 全部用例",
  "source_read_id":"本次成功 case_source_read 返回的 read_id",
  "units":["OPS-001","OPS-002","WEB-001","WEB-002"],
  "stage_time_budget_sec":300,
  "total_time_budget_sec":1800,
  "stage_budget":6,
  "total_budget":24
}
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

`agent_workflow_get` 分列四阶段状态、消耗与剩余预算、coverage、全部调查历史、原任务、未核对写入及独立待办。coverage 至少包含 `expected`、`declared`、`implemented`、`path_validated`、`formal_verified`、`blocked`、`missing`、`verification_missing`、`blocked_units`、`next_units`、`implementation_complete`、`verification_complete`、`all_implemented` 和 `all_verified`。`missing` 是尚未实现的非终态条目；`verification_missing` 是尚无正式 Scout 证据的非终态条目。写脚本一轮先处理 `missing`，写齐后再处理 `verification_missing`。`implementation_complete`/`verification_complete` 表示当前阶段已无未处理项，但终态阻塞仍会出现在 `blocked_units`，不能据此说全集成功。只有 `all_implemented=true` 才能说脚本全集写齐，只有 `all_verified=true` 才能说正式全集通过；`complete` 仅为 `implementation_complete` 的兼容别名。若有 blocked，只能报告“已逐条收敛，仍有 N 条阻塞”并列出 ID。formal_verified 必须引用对应 Scout task_id 的断言与证据。源码实现完成、等待打包验证和正式验证通过分别表达。

每批处理 5–10 条，完成一批后立即从 `coverage.next_units` 取下一批自动继续，不需要用户重复说“继续”。写脚本阶段只有 `all_implemented=true` 才能说脚本全集写齐；正式测试阶段只有 `all_verified=true` 才能说正式全集通过。`implementation_complete`/`verification_complete` 只用于判断当前阶段是否还有未处理项，存在 `blocked_units` 时必须逐条列出。任何阶段都可在所有剩余条目已有明确阻塞/失败/延期结论、需要用户提供业务数据或决策、设备/Scout 不可用、或预算确实耗尽时交付当前进度。预算耗尽也必须报告 `已完成/expected_total` 和全部剩余 ID，不得说“全部完成”。

## 时间预算与用户求助

支持新版契约时，init同时锁定累计调查时间：每个unit/阶段默认300秒，总计默认max(1800,expected_total×120)秒。get/start/finish返回time_budget，包含累计调查耗时、剩余秒数和overdue_attempts。累计每个start到finish的时间，包括其中等待；用户在两个attempt之间等待不计入，重建工作流不可用于绕预算。超限只阻止继续开启调查，仍允许核对原任务、finish和resolve；不取消设备任务，不降低原文预期。

finish可在blocked/deferred时保存help_request：question、missing、checked_sources、affected_units。get列出当前未解决问题。收到requires_visible_receipt、overdue或help_request立即在可见对话输出，继续独立条目，不等最终报告。

verification complete必须有原task_id；新版Nexus会核验该用例所有匹配设备执行的封存Scout记录、有效原文断言、覆盖与上下文，而不是信任Agent自报complete。路径验证归preparation，调试与补数据不算正式通过。

完整判定与回执纪律见[测试质量、缺口求助与逐条回执](execution-discipline.md)。
