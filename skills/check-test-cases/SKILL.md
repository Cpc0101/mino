---
name: check-test-cases
description: 用 mino-scout check 检查用例的单文件业务归属、Scout API、跨文件引用、原文映射与明显无效断言。用于编写和交付前静态自检，不将校验通过当作真机或业务验证通过。
---

# 自检用例脚本

自检只有一个入口：MinoScout 自带的 `mino-scout check`。单文件隔离规则是它的一种检查类型 `case_isolation`，不是随技能安装的独立 Python 工具，也不是第二套检查流程。

## 推送门禁（强制）

任何脚本仓 push 前都必须在仓库根运行：

```bash
mino-scout check --require-cases .
```

输出里只要还有一条需要解决的问题，就禁止 commit/push。先修复并重新运行；动态原文映射、页面定位、断言或业务覆盖需要真实运行时，先完成对应 `case_run`/证据核验再重跑。不得把 error、未核验 warning 或“待运行验证”的缺口留在已 push 的脚本里。

每次修改用例、`CASE_SOURCE`、`config.yaml`、`pages/`、`flows/` 或 `scripts/` 后，在脚本仓根执行：

```bash
mino-scout check .
```

交付用例前执行：

```bash
mino-scout check --require-cases .
```

需要本机已安装 MinoScout `0.1.149` 或更高版本。该命令不是可移植的裸 Python 检查器；它读取 Scout 仓库源码，但不导入、不执行用户仓库，也不访问设备。输出统一为英文，格式为：

```text
<path>:<line>: [<finding>] <message>
<path>:<line>: [<finding>/warning] <message>
```

有 error 时退出码为 1；只有 warning 时静态命令可以通过，但 warning 指向的动态映射、定位或断言仍是待解决问题，必须由运行记录核验并消除后才能 push。

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
| `check_assertion_unresolved` | helper 是否真正产生断言不能静态确认 | 运行后确认对应 check 有 assertion/result |
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
- 静态检查通过只证明结构、引用和明显契约没有错误；真实定位、账号、验证码、断言和设备行为仍需 `case_run` 执行验证。
- 动态 helper 或动态 `source_ref` 不能因为静态不确定就强行改成另一套固定动作语言；必须用执行记录确认实际覆盖。
- `locator_spec` 是否可用不能靠静态格式判断。定位只从本次 `case_run` 后 Scout 返回的 `nodes` 或 `hierarchy_text` 中取得；没有该次界面证据就不要写。
- 命令不存在说明本机没装 Scout：按 `onboarding` 门禁 3 协助安装，不要只丢文档链接。
