---
name: check-test-cases
description: 用 mino-scout check 检查用例的单文件业务归属、Scout API、跨文件引用、原文映射与明显无效断言。用于编写和交付前静态自检，不将校验通过当作真机或业务验证通过。
---

# 自检用例脚本

自检只有一个入口：MinoScout 自带的 `mino-scout check`。单文件隔离规则是它的一种检查类型 `case_isolation`，不是随技能安装的独立 Python 工具，也不是第二套检查流程。

## 调试与正式检查

`debug_case` 在本机编写工作区执行观察片段，不要求 commit、原文完整映射或业务断言；入口检查脚本语法，运行时记录定位与动作错误。`mino-scout check` 仍检查完整用例，不能为了让草稿通过而写空断言。正式推送与 `case_run` 前执行以下门禁。

## 推送门禁（强制）

任何脚本仓 push 前都必须在仓库根运行：

```bash
mino-scout check --require-cases .
```

输出中的 `error` 和 `warning` 是待解决问题，必须修复并重新运行后才能 commit/push；命令会以非零退出码阻断。`info` 只描述静态检查边界，不要求消除。特别是每条 `CASE_SOURCE` 都会固定产生一条 `source_remote/info`；不要为了去掉它而删除 `CASE_SOURCE`、改回 YAML 或反复执行用例。

静态门禁不替代运行验证：动态原文映射、页面定位、断言和设备行为仍须用目标 Scout 节点完成对应 `case_run`/证据核验。静态检查通过只表示没有 error 和可操作 warning，不表示用例已真实执行通过。

## 全集覆盖门禁（强制）

`mino-scout check` 只检查当前工作区已经存在的脚本，不会知道飞书原文还有多少条；`case_run` 的空 `case_ids` 也只展开当前目录脚本。交付“所有用例”前还必须读取 `agent_workflow_get.coverage`，并把实际 `tests/**/<case_id>.py` 的用例 ID 与原文锁定的 `expected_units` 对账：

- `coverage.missing` 必须为空；否则继续实现，不得只凭 check 通过宣布完成。`coverage.verification_missing` 非空时继续正式验证或明确报告未验证。
- 写脚本全集写齐必须满足 `coverage.all_implemented=true`；正式全集通过必须满足 `coverage.all_verified=true`。`implementation_complete`/`verification_complete` 表示当前阶段无未处理项，仍可能包含 `blocked_units`；`complete` 只是 implementation_complete 的兼容别名，不能拿来证明脚本已全部正式通过。
- 每个 expected ID 必须出现在对应成品文件中，或有该 ID 自己的明确 blocked/failed/deferred 证据。
- 不得用当前文件数反推 expected_total，也不得删除原文预期、空 wrapper 或中央 dispatcher 来消除差集。
- 最终汇报写清 `完整实现 / expected_total`、`路径验证 / expected_total`、`正式通过 / expected_total`；三者不能互相替代。

静态检查、coverage 和 Scout 运行证据是三个独立门禁；任何一项没有通过都不能声称全集完成。

每次修改用例、`CASE_SOURCE`、`config.yaml`、`pages/`、`flows/` 或 `scripts/` 后，在脚本仓根执行：

```bash
mino-scout check .
```

交付用例前执行：

```bash
mino-scout check --require-cases .
```

需要本机已安装 MinoScout `0.1.150` 或更高版本。该命令不是可移植的裸 Python 检查器；它读取 Scout 仓库源码，但不导入、不执行用户仓库，也不访问设备。输出统一为英文，格式为：

```text
<path>:<line>: [<finding>] <message>
<path>:<line>: [<finding>/warning] <message>
<path>:<line>: [<finding>/info] <message>
```

有 `error` 或 `warning` 时退出码为 1；只有 `info` 时退出码为 0。warning 指向动态映射、定位或断言缺口，必须修复或运行核验；info 不计入待解决问题，余下运行边界按交付要求单独核验。

## 检查类型

| 类型 | 意思 | 怎么改 |
|---|---|---|
| `case_isolation` | 用例没有在自己的文件里直接承载业务；或共享模块按用例编号分派、接收整个 `case`、调用 `case.nexus.*` 业务事件/断言 | 把 `prep/do/check`、`source_ref`、业务断言和本条用例自己的阻塞路径直接写回当前文件的 `run(case)`；共享代码只保留可复用机制或纯计算 |
| `forbidden` | 绕开了 Scout（设备库、`subprocess`、线程、`exec`/`eval`、`if platform`） | 设备动作改用 `app.*`，设备命令改用 `app.exec()`，不要并发，平台差异放 `pages` 的 `locator_spec` |
| `reuse` | 自己重复实现了 Scout 已有的能力（`time.sleep`、`imaplib`、直接调模型） | 改用 `case.scout.wait()` / `otp(account)` / `llm()` / `app.expect()` |
| `case_attr` | 使用了 `case.tap` 之类不存在的成员 | 先 `app = case.init(case.config.<KEY>)`，设备动作写在 `app` 上 |
| `case_init` | `case.init` 的第一个参数不是 `case.config.<KEY>`，或关键字不是 `web_resolution` | 改成 `case.init(case.config.<KEY>)`；仅 Web 分辨率用例可写 `web_resolution="720P|1080P|2K|3K/4K"` |
| `step_title` | `prep` / `do` / `check` 没有写文字标题 | 写这一步具体做什么的一句话 |
| `prep_missing` / `prep_reason` | 用例没有 `prep`，或前置标题只有「无」这类空话 | 写具体准备动作；确实无需准备时写清为什么 |
| `config_missing` / `config_invalid` | 缺少 `config.yaml`、格式不对，或脚本引用不存在的应用 | 按 `repo-config` 修正；顶层是 `apps`，每个应用必须有 `platform` |
| `page_layout` | 页面文件不在 `pages/<APP_KEY>/` 下，或目录不是 config 中的应用 key | 移到正确应用目录 |
| `syntax` / `entry_missing` / `entry_signature` | 语法或 `run(case)` 入口无效 | 修成一个同步的模块级 `run(case)` |
| `import_missing` / `import_symbol_missing` | 同仓模块或导入对象不存在 | 检查文件、函数定义与导入路径 |
| `page_missing` / `control_unknown` / `locator_missing` | 页面或控件引用无效 | 用本次从 Scout 取得并核对过的界面结构补页面，不编造定位 |
| `check_empty` / `check_no_assertion` | `check` 只有标题或观察，没有有效断言 | 使用注册断言验证原文预期 |
| `model_implicit` | `expect(prompt=...)` 未显式声明模型使用 | 固定文字/状态改用确定性断言；语义验证需 allow_model=True 和 MODEL_POLICY |
| `model_policy` | 模型策略不是字面量、缺用途/引用/预算，或用例及共享模块使用了未允许的模型 | 默认 mode=off；确需语义判断时按 write-test-cases 的模型例外声明，运行时仍核对当前原文引用与预算 |
| `check_assertion_unresolved` | helper 是否真正产生断言不能静态确认 | 运行后确认对应 check 有 assertion/result |
| `source_remote/info` | 静态检查不读取 Feishu 原文；该提示对每条 `CASE_SOURCE` 固定出现 | 不是缺陷，保留 `CASE_SOURCE`，在 `case_run` 证据中核验原文映射与覆盖 |
| `source_dynamic/warning` / `source_unmapped/warning` | 动态引用或覆盖无法静态确认 | 用执行记录确认覆盖；不能把未知当成已通过 |
| `source_*` / `expectations_missing` | `CASE_SOURCE` 配置或 `source_ref` 映射有缺口 | 核对原文版本、条目 ID、类型与覆盖，不删预期凑通过 |
| `cases_missing` | 交付检查没有发现用例脚本 | 配置就绪不等于用例完成，继续实现 |

## `case_isolation` 的判定

每个 `tests/**/*.py` 用例文件必须满足：

- 模块级声明字面量 `CASE_SOURCE`，并定义唯一的同步入口 `run(case)`；
- `run(case)` 直接包含 `case.nexus.prep/do/check` 中的业务步骤、`source_ref` 和本条用例自己的业务断言；
- 无法执行时，在本文件直接调用 `case.nexus.fail(...)`、写清具体缺口的 `note`，或抛出 `ScriptAbort`；不能生成空跑占位文件凑数量；
- 不把整个业务用例交给 `run_case(case, "UAT-001")`、`run_articulated_case(...)`、handler 表或其他共享 dispatcher；
- 不通过 `case_id`、`case_key`、`_case_001` handler 或中央 `BLOCKED` 表按编号分派。

共享 `flows/` 与 `scripts/` 只能放可复用机制或纯计算：

- 函数接收 `app`、页面对象、`case.scout` 或普通值；
- 不接收整个 `case`；
- 不调用 `case.nexus.prep/do/check/note/fail/assert_equal`；
- 不含用例编号、用例编号分派或集中 handler；
- 不替用例决定业务预期、阻塞原因或最终结果。

只要共享 helper 需要知道用例编号才能决定行为，这段业务就应该移回各自的用例文件。

## 边界

- 新用例只使用 Python + `CASE_SOURCE`，不再创建同名原文 YAML。旧 YAML 仅为已有仓库运行时兼容，不进入新脚本流程。
- 静态检查通过只证明结构、引用和明显契约没有错误；真实定位、账号、验证码、断言和设备行为仍需 `case_run` 执行验证。`source_remote/info` 会持续存在，这是能力边界，不表示还有未解决问题。
- 动态 helper 或动态 `source_ref` 不能因为静态不确定就强行改成另一套固定动作语言；必须用执行记录确认实际覆盖。
- `locator_spec` 是否可用不能靠静态格式判断。定位只从本次调试会话或 `case_run` 后 Scout 返回的 `nodes` 或 `hierarchy_text` 中取得；没有该次界面证据就不要写。
- 命令不存在说明本机没装 Scout：按 `onboarding` 门禁 3 协助安装，不要只丢文档链接。
