---
name: check-test-cases
description: 用 mino-scout check 检查用例语法、跨文件引用、原文映射与明显无效的断言。用于编写和交付前静态自检，不将校验通过当作真机或业务验证通过。
---

# 自检用例脚本

每次修改用例、原文 sidecar、config、pages 或 flows 后，在仓根检查。初始化只有配置的仓库可用基础检查：

```bash
mino-scout check .
```

交付用例前使用：

```bash
mino-scout check --require-cases .
```

该选项确保仓库存在用例脚本。输出格式为 `文件:行号: [类型] 说明`；错误退出码为 1，warning 单独标明且不导致失败。修复错误，核对 warning 指向的动态内容；动态 helper 或 source_ref 需要运行证据，不能因为静态不确定就强行改成另一套固定动作语言。

| 类型 | 意思 | 怎么改 |
|---|---|---|
| `forbidden` | 绕开了 Scout（设备库、`subprocess`、线程、`exec`/`eval`、`if platform`） | 设备动作改用 `app.*`，设备命令改用 `app.exec()`，不要并发，平台差异放 `pages` 的 `locator_spec` |
| `reuse` | 自己重复实现了 Scout 已有的能力（`time.sleep`、`imaplib`、直接调模型） | 改用 `case.scout.wait()` / `otp(account)` / `llm()` / `app.expect()` |
| `case_attr` | `case.tap` 之类，`case` 上没有这个成员 | 先 `app = case.init(case.config.<KEY>)`，设备动作写在 `app` 上 |
| `case_init` | `case.init` 的参数不是 `case.config.<KEY>` | 改成 `case.config.<KEY>` |
| `step_title` | `do` / `check` / `prep` 没有写文字标题 | 写这一步具体做什么的一句话 |
| `prep_missing` | `tests/` 里的用例没有 `prep` | 写具体准备动作；确实无需准备时写明理由，记录在 Scout |
| `prep_reason` | 前置标题只有「无」这类空话 | 写清做了什么；确实不用做，就写为什么 |
| `config_missing` | 脚本用了 `config.yaml` 里没有的应用，或没有 `config.yaml` | 补 `config.yaml`，参见 `repo-config` |
| `config_invalid` | `config.yaml` 格式不对 | 顶层 `apps`，每个应用要有 `platform`，key 以英文字母开头；不要写 `app_id`、登录方式或验证码策略。旧仓库的 `otp.code` 仅为兼容字段，新项目不要写 |
| `page_layout` | 页面文件位置不对 | 放到 `pages/<APP_KEY>/` 下，目录名等于 `config.yaml` 里的 key |
| `syntax` / `entry_missing` / `entry_signature` | 语法或 run 入口无效 | 修复到一个同步 `run(case)` 入口 |
| `import_missing` / `import_symbol_missing` | 同仓模块或导入对象不存在 | 检查文件、函数定义与导入路径 |
| `page_missing` / `control_unknown` / `locator_missing` | 页面或控件引用无效 | 用本次 Scout 观察补齐页面，不编造 locator |
| `check_empty` / `check_no_assertion` | check 只有标题或观察，没有有效断言 | 使用注册断言验证原文预期 |
| `check_assertion_unresolved` | helper 是否断言不能静态确认 | 运行后确认对应 check 有 assertion/result |
| `source_*` / `expectations_missing` | 同名原文快照或 source_ref 映射有缺口 | 核对原文版本、条目 ID、类型与覆盖，不删预期凑通过 |
| `cases_missing` | 交付检查没有用例脚本 | 配置就绪不等于用例完成，继续实现 |

注意：

- 只读解析源码，不导入或执行用户仓库。已识别的 app 绑定可检查字面量页面引用，但不能静态证明任意 Python 的全部路径和动态 helper；
- 静态映射、路径执行、业务预期验证是三件事。运行时仍独立拒绝空 check、零断言和未覆盖的原文；
- 新转换用例必须按 `analyze-test-case` 保存同名原文 sidecar；旧无 sidecar 用例的兼容校验通过，不代表原文覆盖已证明；
- 自检不核对 `locator_spec` 是否来自真机。格式能解析不代表能点中。`locator_spec` 只从 `case_run` 之后 `capability_id=hierarchy` 的 `nodes` 或 `hierarchy_text` 里抄；没有这次运行的界面结构就不要写。
- 命令不存在说明本机没装 Scout：按 `onboarding` 门禁 3 协助安装，不要只丢文档链接。
