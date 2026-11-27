# 本机调试与执行工作区

## 两套工作区

编写工作区是本机应用项目的现有目录，由 Agent 编辑。用例、pages、flows 与 config 放在这里。`debug_case` 要求本机 Scout 也能读取该目录，不拉仓、不重置文件、不要求提交版本。首期不支持跨机器编写或同步；远端 Scout 只接正式 `case_run`。

执行工作区由 Scout 管理，按登录归属隔离，布局为：

```text
<Scout 配置目录>/accounts/<profile>/workspaces/execution/<task_id>/
  records.sqlite3                 # 所有 attempt 的事件、摘要与片段请求
  artifacts/<attempt_id>/         # 原有截图、控件树与大对象证据
  attempts/<attempt_id>/
    source/                      # 正式执行的固定 Git 副本；调试不从这里运行
    output/                      # 本次执行产生的文件，进程工作目录
```

代码通过 `case.workspace` 引用源码和输入资源，通过 `case.output_dir` 写生成文件。调试时 workspace 指向编写目录；正式执行指向 source。实际路径由 `session_record` 返回，勿按示例猜本机配置根。旧 records 目录保留兼容读取，不搬动历史数据。

## 会话操作

续接、旧账号占用、认证或 OTP 问题先读 [会话、认证与验证码闭环](session-authentication.md)。先查原 session 和指定 request，再决定复用或关闭；同 chat/目录/sn 不构成相同 session。

先读当前 `agent_guide` 和工具表，再用本机 `mino-scout status` 与 MCP 设备信息核对 `node_id` / `sn`。用 `debug_case` 传 `workspace` 绝对路径、`app_id`、`app_key`、环境和稳定的 `client_request_id`。启动是异步的，拿到 session_id 后查询 `debug_case_status`，到 ready 才执行片段。

`debug_case_execute` 传同一 session_id、新的请求 ID，以及二选一的输入：

- `code`：几条 Python 语句，可直接使用 `case` 和绑定应用 `app`。
- `script_path`：编写工作区内的 `.py` 相对路径。定义 `run(case)` 时执行该入口，支持正式用例相同的 Scout API。

初次观察可执行：

```python
app.launch()
app.hierarchy()
app.screenshot()
```

后续片段省略 launch，在已有页面观察、验证定位和操作。调试不自动执行项目或用例 pretest/posttest；需要的准备操作由片段显式调用。Python 变量和应用上下文持续保留；每段刷新 pages 及本地模块，已从模块导入的函数会刷新，旧模块的实例需要重新构造。config 改动需要结束后重建会话。

每段记录 workspace_hash、code_hash、文件哈希、动作范围和断言。可传 `workspace_hash` 拒绝意外变化；不传时使用本次执行开始时捕获的版本。`observed` 仅表示片段完成，`assertions_passed` 只证明这一片段实际运行的断言；均不构成正式用例通过。历史证据不自动证明修改后的版本有效。

重复投递同一请求保留请求 ID 与参数，查询原结果；参数变化必须使用新 ID。同一会话同时只接收一段执行。`timeout_sec` 限制当前片段（1–3600 秒，默认 60），会话没有固定总时长。超时按指定 command 的 started_at/finished_at 与预算判断，不用顶层 session elapsed_ms；ready/idle 仍可持有租约，不代表释放。

- `debug_case_cancel`：取消指定片段，能够协作停止时保留现场。强制终止执行进程时会话中断，资源保持隔离。
- `debug_case_reset`：显式关闭并重新启动绑定应用、清除片段变量，保留租约和证据，不清应用缓存。
- `debug_case_close`：持久提交结束意图，Scout 确认停止后才结算资源。结束请求成功不等于资源已经释放。

普通脚本错误后可以修改并执行下一段。`write_outcome_unknown` 后保持写停止，允许读取证据；不能吞异常、换请求 ID 重写或用 reset 绕过。节点断线、重启、强制取消或租约到期不得被当成释放证明，也不能建议等待到期后自动恢复可用。关闭失败时保留服务返回的 reason_code、message、reason_detail；先读取原会话与资源状态，取得原 Scout 停止证据和 Nexus 释放回执后才报告释放，不能通过重建会话绕过隔离。

正式运行前结束调试，完成静态检查，提交完整用例和依赖并固定 commit。从可复现的初始状态执行 `case_run`，不携带调试变量、浏览器上下文或局部通过结论。

## 保存阶段并关联正式版本

用 `debug_case_checkpoint` 登记 script_path 与 stage（draft、implemented、path_validated）。完整实现会对捕获的源码执行静态检查；路径验证还须传 evidence_request_id，指向同版本同路径的成功执行及断言。仅声明阻塞或直接 abort 的文件不能登记为完整实现。每次修改后重新检查，不以历史检查点证明新代码有效。

`debug_case_status.authoring_progress` 按用例路径列出阶段及与最近捕获版本的差异；formal_runs 分开列出关联正式任务和真实通过/失败/阻塞统计。它与 agent_workflow 的调查预算各自记录，不互相替代。

结束会话并确认资源结算，push 完整用例后，`case_run` 传 40 位 commit SHA、相同用例的 script_targets 以及 `debug_origin: {session_id, checkpoint_id}`。Nexus 读取原 Scout 的 path_validated 检查点；目标 Scout 在操作前核对检出版本，不一致返回 debug_version_mismatch，不能改用不带来源的请求绕过核验。一次引用关联一个用例；其他用例使用各自检查点和正式任务。
