# 认证指导修复与静态验证记录

日期：2026-11-27。仅修改 mino 仓库 skills/ 与 docs/；不修改 Scout/Nexus、运行中的 ws、版本号、提交或安装配置。

## 已读证据

- 四项根因报告及原脚本；300 秒与 OTP 失败没有被当作已复现底层故障。
- 已读 SDK web_api、CaseData、debug command/session 输入与源码快照实现，用于约束建议，不代表本地运行版本或业务接口已验证。

原脚本读取快照 SHA256：

- `/Users/changpengcheng/Documents/Codex/2026-11-26/shang/work/ws/qa_gen2.py`：`1817ba89d70899ab0ab672579ef0f7889c5c6ba0fbcbdb07f7b09a3cfb9d8ffe`。
- `/Users/changpengcheng/Documents/Codex/2026-11-26/shang/work/ws/login_complete.py`：`74e020a8edf73b2088f0f829469e7122f0fd5f28e27e052ce552e8634ca332df`。

## 修改

- 新增 [会话、认证与验证码闭环](../skills/write-test-cases/references/session-authentication.md)：同 chat 非同 session、旧资源管理、command 时长、当前 context 身份、业务认证错误快速失败、兴趣引导独立状态、单一 OTP 窗口。
- 接入 mino / write-test-cases / run-test-cases / check-test-cases 与执行纪律、调试工作区参考；显式 case inputs 与 run/attempt/request 隔离输出。
- 同类问题：去除运行指导中固定 4 个 Web 槽位假设；新增显式 account_id 与返回账号不一致、reset 后认证失效、SDK actor identity 非业务用户、旧 data_outputs/共享 tmp 非冻结证据的门禁。
- 另交付 [国际定制 ws 精确补丁建议](international-ws-authentication-patch-advice.md)，含原文件精确行号、已知请求 path、原生 network 替换位置、输入/输出与错误分类机制。发码/登录/当前用户接口与成功码仍缺真实证据，明确由已有测试 Agent 部署后查证，不虚构。

## 已实际执行

- `python3 skills/mino/scripts/check_routing_contract.py`：`routing_contract: 20 checks passed`。安装/guard 动作仅发生在该检查的 TemporaryDirectory，不改用户安装。
- skill-creator `quick_validate.py`：mino、write-test-cases、run-test-cases、check-test-cases 均 `Skill is valid!`。
- 修改文档与补丁建议链接/Python 代码块校验：9 documents、19 local reference links、12 Python code blocks 通过。初次宽松正则误匹配 fenced code 的 `[case_id](case)`；改为只解析非代码正文后重新执行通过，未将初次失败计为通过。
- 用 Scout 仓库现有 Python 环境执行建议中的纯机制函数：19 个隔离响应/输入/输出检查通过，覆盖 HTTP200/code401、HTTP401/500、成功码/状态类型差异、缺失/截断正文、输入越界与哈希不符、输出拒绝覆盖、不同 request 隔离。未触发 Scout/业务网络/OTP。
- Node 解析建议中的两个 JS 片段；5 个纯内存 DOM fixture 检查通过：兴趣引导、营销弹窗、登录表单、隐藏邮箱、多个引导歧义。没有启动浏览器。
- `git diff --check` 通过。

## 未执行与交接

未运行 pytest、业务用例或真实 UI/账号/取码/生成；静态和隔离 fixture 不证明业务认证或定位通过。未安装技能、改版本、提交、发布或部署。待发布者统一发布/安装后，由已有测试 Agent 接收 ws 修改，在原业务 workflow 下显式管理旧 session、查证接口/身份、固定 inputs，再做 Scout 静态检查与新的受控 attempt；不重放未知写。

## 收尾：新 OTP 进度文案核对

已读 Scout `server_comm/otp_progress.py`、callbacks 的内部 otp_status 与最终 otp 事件、records 的 metadata/snapshot/status 投影。精确更新技能：通过既有 `debug_case_status` 实际返回字段与 `session_events` 的 `run/snapshot.payload.otp_wait` 读取原请求进度；不虚构专用 OTP MCP，也不把内部函数当公开 SDK。列明真实字段、脱敏 request_ref、采样/归属与终态边界；缺顶层字段先读事件，不误称没有进度。

实际用新 Scout 源码与 TemporaryDirectory RecordStore 验证10项，metadata、事件、status 投影、完成态、不可用/失效查询及脱敏关联均通过。初次 fixture 错把事件列表字段写成 events，报 KeyError；读取真实 RecordStore.events 返回 shape 后改用 items，完整重跑10项通过。技能 quick_validate、参考链接与 git diff --check 通过。未连接邮箱、调用业务 MCP/专用 OTP 接口或操作 UI；不改 Scout/Nexus，不安装、不提交发布。
