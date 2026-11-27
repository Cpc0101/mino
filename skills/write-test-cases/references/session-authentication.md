# 会话、认证与验证码闭环

在继续调试、租号冲突、登录/OTP 排障、认证前置和生成任务等待时读取。以下是 Agent 与脚本的行为门禁，不代表未部署的 SDK/MCP 能力已经可用；先读当前 `agent_guide` 和工具 schema，缺字段或接口时保留未知，不编造调用。

## 1. 先确认执行身份，再决定续接

同一 chat、工作目录、物理 Web `sn` 或登录邮箱，不等于同一执行 session。分别记录业务 `agent_task_id/workflow_id` 和执行 `task_id/run_id/session_id/attempt_id`、片段 `client_request_id`、原 Scout、应用与环境；值来自回执，不能从 ID 格式推导。聊天续接保持业务工作流，不意味着浏览器 context 或账号租约自动续接。

- 继续已有调试：先查询原 `session_id` 与指定 request 的 `debug_case_status`；原 session ready 且环境/工作区相符时优先复用，不默认创建新 session。ready/idle 表示没有片段正在执行，不表示 session 已关闭或账号已释放。
- 同 run 同 slot 的活动租约可按服务契约复用；不同 run 的账号互斥不是“占用自己的账号”。显式请求的 `account_id` 与返回身份不符立即停止，不接受旧 slot 中的另一个账号，不改 slot 或换号绕过冲突。
- 租约冲突先读取返回的脱敏 holder/request run、session、slot 和资源状态。旧服务缺这些字段时只读查询原任务/会话与租约记录，不猜 holder。未知写操作只核对原 attempt 与对象，不重放。
- 确需新 session：明确选择继续保留旧 session，还是结束它。结束用 `debug_case_close`，再核验原 Scout 停止证据和 Nexus 释放回执；提交关闭、cancel、片段终态、TTL 到期或节点断线均非释放证明。旧资源未确认释放时不恢复租约、不强抢、不重启节点绕隔离。
- 若业务本来允许两个独立账号并行，明确各自 run/slot/账号与目的后使用不同资源；不能为掩盖前置缺口而自动换号。复用原账号的数据也必须重新确认当前 context 的认证。

### 只按指定片段判断超时

优先读指定 request 的 command state、started_at、finished_at、elapsed_ms、timeout_sec/deadline_at；session age 与顶层 elapsed_ms 不代替片段耗时。旧服务缺片段 elapsed/deadline 时用该 command 的时间与预算计算并注明“本地计算”；没有 started_at 则未知，queued 不能按 session 开始时间判超时。已完成片段不因 session 存活超过预算而判仍 executing。保存 timeout/cancel/interrupt 的原始原因，不把它们统称脚本失败或根据无限 session deadline推断片段原因。

## 2. 当前 browser context 的认证前置

账号租用只证明资源身份，不证明页面已登录；以前的成功片段、另一个 run 的 cookie、邮箱变量或跳转成功都不是本 context 的认证证据。正式 run 使用独立 context，不能偷拷贝旧 cookie、token、localStorage 或依赖调试变量。

业务写动作前按应用真实契约建立并核验：

1. 从显式输入取得目标 `account_id`，由 `case.nexus.account()` 租用并核对返回身份及环境；无固定身份需求也要记录本次实际租号。
2. 在当前 app/context 观察登录入口、登录表单和已认证 UI；“没有 email input”只能说明没有该输入框，可能尚未打开登录弹窗，不能当已登录。
3. 登录流程记录发码、登录的实际网络业务回执（应用支持时用 `app.network.expect_response` 由 Scout 原生观察；只读页面事实可用 `app.exec` 在当前 context 读取），再调用应用文档明确的只读身份入口核对业务成功与当前账号归属。不得猜接口、直接调用外部 HTTP 客户端代替当前 browser context，或把 cookie/token 内容写入事件。
4. 身份入口返回的业务用户 ID 与 Nexus `account_id` 不一定相同：按已验证映射或租号身份特征比较，不直接等同。只有 UI 证据而缺可靠身份映射时说明认证身份未核验，暂停依赖它的业务写操作；不借模型给出肯定结论。
5. 在对应原文 prep/check 内使用有效注册断言；登录前置不占业务生成/支付等原文预期的通过数。

HTTP 状态与响应业务状态分别判断。HTTP 200 且正文 `code=401, msg=login expired` 是业务认证拒绝，不是 HTTP 401，更不能证明令牌自然过期或 cookie 丢失。按本应用成功码契约先检查业务错误，再等 taskId/对象 ID：明确认证拒绝立即停止本次写路径，分类为需要认证/认证失效并保留原始 code、脱敏 message 和证据引用；缺身份证据不猜 expired。其他明确业务失败同样停止，不以“没有 taskId”覆盖它、不反复读同一失败响应、不重新点击生成。若登录本身就是被测业务，按原文预期判定；否则前置无法成立记录具体阻塞，不泛化归因产品 bug。

登录后发生 reset、launch/close、切 context、重建 session 或环境变化时，重新观察认证；`reset` 保留租约不等于保留 cookie 或当前用户身份。只读认证核验与重登录分开，后者是新动作，不自动重放结果未知的业务操作。

## 3. 登录弹窗与新号兴趣引导分开

状态判定使用当前 Scout 观察到的特定控件与应用回执，不以“任意大 modal”作登录状态：

| 状态 | 所需区分证据 | 后续动作 |
|---|---|---|
| 未登录/登录入口 | 登录入口与认证未成立 | 明确打开登录表单 |
| 登录表单/等待验证码 | 已核验的邮箱/验证码控件与发码请求状态 | 只等待原取码请求 |
| 登录提交失败 | 登录业务失败回执或明确错误控件 | 保留错误并停止，不继续猜码 |
| 新号兴趣引导 | 特定问题/选项、Skip/Confirm 等实测控件；认证独立核验 | 按原文/已有准备授权选择跳过或填写，再重新观察 |
| 已认证可操作 | 当前 context 身份与业务成功、目标页面就绪 | 才进入依赖认证的业务步骤 |
| 营销弹窗/未知 | 不属于以上的 modal 或证据冲突 | 单独处理/报告未知，不重登录 |

兴趣引导存在不证明未登录，消除引导也不证明后端认证或生成业务成功。新账号注册、认证、引导完成、初始业务数据分别核验；不能把新号与旧号共享一个“无 dialog 或有 Log out 就成功”的条件。没有明确跳过权限/可选行为时保留前置缺口，不能直接从 DOM 删除弹窗冒充用户完成。

## 4. OTP 只有一条取码链路

已部署 `otp_request` 的节点先在发码前执行 `request = case.scout.otp_request(account)`，再用 `app.network.expect_response` 在点击前登记精确响应窗口，通过真实控件发码并核验 HTTP 与业务回执（不以成功码过滤掉失败响应），最后 `case.scout.otp(account, request=request)` 消费同一请求。固定码策略可能返回 None，不凭此判断发码失败；旧节点不支持该能力时说明边界，不伪造邮箱基线。每次实际新发码应建立新边界，不能用旧请求、旧邮件或另一个账号的请求满足它。

- 取码在进行时通过已有只读 MCP `debug_case_status(session_id, client_request_id)` 查询原片段；读取其实际返回的 `otp_wait`（若有），并用 `session_events(session_id, from_seq, limit)` 按返回游标续读 `type="run/snapshot"` 事件的 `payload.otp_wait`。`otp_progress.Progress.publish()` 将进度写入 metadata，RecordStore 同时追加该事件；不是新的专用 OTP MCP 接口。旧节点/投影没有顶层字段时先查原事件，事件也无进度则说明“未取得进度证据”，不能据此断言未发码或邮件未到。不要虚构 MCP `otp_status/otp_progress`，Scout 0.1.176 新增公有 `case.scout.otp_status(request=request)`，只在脚本内读取该 Case 已有请求，不发码、不取码；并行诊断仍用上述 MCP 状态/事件，不另起片段。内部 `callbacks.otp_status` / `otp_progress.snapshot` 不是专用 MCP 接口；旧节点不可假定具备新 SDK 方法。
- `otp_wait` 的实际字段包括 `state/phase/elapsed_ms/remaining_ms/max_wait_ms/deadline_exceeded`，以及可选 `request_ref`、计数 `polls/messages/matched/connection_attempts/reconnects`、白名单 `error_code`。`request_ref` 是 OTP 请求标识的 SHA256 前16位，只作脱敏关联，不是可重投的请求 token；同 session 连续取码时还要按原 command、事件序号和请求引用确认归属，不拿最新快照代替指定旧请求。进度是采样时的事实（活跃 tracker 约每秒尝试发布），不是实时倒计时或完整邮件明细；准备完成后的快照也可能不再刷新。`deadline_exceeded`、prepared/expired 或缺计数不替代 command/OTP 最终回执，更不证明 worker 已停止、资源释放或认证成功。
- `resource_account_otp`、再次 `case.scout.otp`、另开片段/账号、直接 IMAP 取信都是新的取码操作，不是只读诊断。禁止在活跃取码窗口旁并行执行它们，亦不发第二次验证码来探测邮箱。
- 按原请求区分准备、连接、搜索/读信、匹配、完成、失败、取消；总耗时不全等于邮件投递延迟。原事件已经 otp pass 后停止“等邮件”的调查，转查登录提交、业务回执和兴趣引导。
- 超时/取消后先确认原动作停止及写结果；无新事实不换 request ID 重取或重发。必须重新发码时单独说明依据，保留原失败、执行新的发码边界与预算。
- 只汇报 request 引用、阶段、耗时、计数、原始 reason_code 和证据；不输出 OTP、邮箱密码、token、cookie 或完整邮件。发码按钮动作成功不等于发码成功，取码成功不等于认证成功。

## 5. 输入和输出不得跨 run 隐式共享

见 [运行时数据与业务 flow](runtime-data-and-flows.md) 的“显式输入与隔离输出”。身份/模型参数必须随本次请求固定；共享 `/tmp` 文件、上次 q_tag.json、最新路径或 debug 全局变量不能充当历史冻结输入或当前账号证明。
