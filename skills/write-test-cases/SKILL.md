---
name: write-test-cases
description: 将已有人工用例实现为可复用的 MinoScout Python 脚本，关联原文、真实定位和有效断言。用户要求写或修改用例脚本时使用，分析原文见 analyze-test-case。
---

# 编写用例脚本（Scout）

脚本是 Python，一条用例一个文件，在所选设备所属 Scout 的独立进程执行。先按 [analyze-test-case](../analyze-test-case/SKILL.md) 确定原文位置并在 Python 声明 `CASE_SOURCE` 来源变量；仓库与页面配置见 `repo-config`。完整记录保存在执行 Scout，以 Nexus task_id 归档；Nexus 保存任务索引，Workbench 经 Nexus 读取 Scout 详情。

**UI 工具边界：**被测 Android / iOS / Web / 桌面界面的观察、截图、控件树、定位、点击和输入只能来自 Scout Case API，本机编写通过 MCP `debug_case` / `debug_case_execute` 执行，正式用例通过 `case_run` 执行。不得先用 Computer Use、浏览器控制、Playwright、adb、Appium、WDA 或其他桌面自动化工具探路或抄 DOM。

多轮编写按 [Agent 进度与预算](../mino/references/workflow-ledger.md) 记录本轮目标、证据及尝试结果；相同阻塞无新事实时改变有依据的方案或交付阶段，并继续独立用例。源码交付与实际验证分别记录，用户指定发布后测试时先完成本地开发及静态检查。

**全集交付门禁：**开始编写前必须已有从原文读取的 `expected_case_ids`，并把同一清单作为 `agent_workflow_init.expected_units`。每批实现 5–10 条，批次结束后从 `agent_workflow_get.coverage.next_units` 自动取下一批，直到 `all_implemented=true`，或剩余条目分别有明确 blocked/failed/deferred 结论并列入 `blocked_units`。`implementation_complete=true` 只表示当前实现阶段已无未处理项，仍可能有终态阻塞；`complete` 只是它的兼容别名。写成脚本不等于正式测试通过，后续验收必须另看 `verification_missing` 和最终 `all_verified`。不得只写几条后把“当前文件”“需求现有用例”或当前可执行子集说成全部；每轮汇报必须写 `已实现/expected_total` 与剩余 ID。

方法签名以本机安装的运行时为准，不确定时读源码，不要凭记忆：

```bash
python -c "import mino_scout, pathlib; print(pathlib.Path(mino_scout.__file__).parent / 'runtime' / 'script_exec.py')"
```

## 1. 写法

设备动作不挂在 `case` 上。先把被测应用实例化，再通过实例操作：

```python
RUN_PURPOSE = "regression"
MODEL_POLICY = {"mode": "off"}

def run(case):
    camera = case.init(case.config.camera)         # 绑定 config.yaml 里的 camera
    with case.nexus.prep("清理应用缓存", source_ref="P1"):
        camera.clear_cache()
    with case.nexus.do("2-1 启动应用", source_ref="S2"):
        camera.launch()
    with case.nexus.do("2-2 点击快拍按钮", source_ref="S2"):
        camera.tap("splash.quick_snap")             # page_key.control_id，页面在 pages/camera/
    with case.nexus.check("进入取景页面", source_ref="E1"):
        camera.on_page("viewfinder")
```

三类对象：

| 对象 | 需要实例化 | 方法 |
|---|---|---|
| `app`（`case.init(...)` 的返回值） | 是，一个应用一个 | 见 §3 |
| `case.scout` | 否 | `wait(ms)`、`otp(account)`、`llm(prompt, text, schema)` |
| `case.nexus` | 否 | `prep/do/check(title, source_ref="")`、`assert_equal(actual, expected, message="")`、`account(requirements=None, prefer=None)`、`note(text, **fields)`、`fail(message)` |

`case` 上通过 `config`、`env`、`init`、`scout`、`nexus` 组织执行，`data` 保存本次输入和对象输出。`case.tap(...)`、`case.launch()` 这类写法不存在。写错方法名，运行时会报出相近的名字和可用列表，按提示改。

### 单文件可审性（硬约束）

“一条用例一个文件”不是“一条用例一个 wrapper”。打开 `tests/<需求ID>/<case_id>.py`，必须能直接读完这条用例的原文映射、前置、操作、业务断言和阻塞原因，不能再去集中式 `flows/<name>.py` 才能知道实际测了什么。设计目标是原文条目与本脚本一一可核对，不是减少重复代码。

`run(case)` 是该用例唯一的业务入口：

- 所有 `case.nexus.prep/do/check`、`source_ref`、`case.nexus.assert_equal(...)`、业务预期和该类用例自己的阻塞判断都必须直接写在当前文件的 `run(case)` 中；正常用例至少直接包含 `prep`、`do`、`check` 各一处。
- 真前置无法建立时，可以在本文件直接写 `prep`、说明具体缺口的 `note`，并调用 `case.nexus.fail(...)` 或抛出 `ScriptAbort`。必须指出这条用例缺什么，不能生成“加载中”“待接入”之类空跑文件凑数量。
- 禁止把整个业务用例委托给共享函数，例如 `run_articulated_case(case, "UAT-001", prep)`、`run_case(case, case_id)`、`handler_table[case_id](case)`；也禁止 `if case_id == ...`、`match case_id`、`_actual(case_id)` 等按编号分派。
- 禁止在共享文件维护 `_case_001`、`_case_002` 一类 handler，或 `BLOCKED = {"UAT-001": ...}` 一类中央用例表。一个用例现在做不到，就在该用例文件里直接写真实阻塞原因，或直接向用户报告，不要制造 47 个通用占位 wrapper。
- `run(case)` 不能只是一个 `with prep` 加一次共享 dispatch。共享 helper 可以在当前 `with` 块内执行明确动作、观察状态和复用验证方法；断言继承当前原文作用域，不替用例创建步骤报告、编排整例或决定是否阻塞，也不能知道用例编号。

共享代码复用明确业务操作、状态观察、对象绑定及验证方法；整例业务编排留在用例文件：

- `flows/<name>.py` 封装明确业务操作、阶段观察、动态对象定位、等待和验证方法。函数接收 `app`、页面对象、`case.scout` 或普通值；不接收整个 `case`，不调用 `case.nexus.*`，不按 `case_id` 改变行为。可在用例 check 作用域内用 `app.expect_*` 注册断言，或返回实际数据供本文件断言。缺数据后的自动构造和恢复策略只由 Agent 决定。
- `scripts/<name>.py` 只做不碰设备的纯计算。它不接收 `case`，不发事件，不发业务断言。

允许的复用边界：

```python
with case.nexus.do("使用邮箱验证码登录", source_ref="S1"):
    login(app, case.scout)  # flow 执行明确操作，步骤与原文归属在用例中

with case.nexus.check("登录后进入个人主页", source_ref="E1"):
    app.on_page("个人主页")
```

上面的业务步骤、预期归属和断言都在用例文件里；`login()` 只是操作机制。若共享 helper 需要 `case_id` 才知道做什么，它就属于错误的集中式业务实现。

### Web 分辨率属于具体用例

只有 Web 兼容性/分辨率用例才在 `case.init` 上指定 `web_resolution`；它是这个用例文件的执行配置，不是跑批参数。未指定时使用默认 `1080P`：

| 传入值 | 视口 |
|---|---|
| `720P` | 1280×720 |
| `1080P` / `1K` | 1920×1080（默认） |
| `2K` | 2560×1440 |
| `3K/4K` | 3840×2160 |

```python
def run(case):
    page = case.init(case.config.hi3d_web, web_resolution="2K")
    page.launch()
```

分辨率兼容性测试必须**一个分辨率一份用例文件**；该文件按对应视口下的真实 hierarchy、控件位置、换行和显隐状态编写定位与断言。不要在同一脚本里切换分辨率，也不要把一套普通功能用例强行复用到所有分辨率。必要时在 `pages/<APP_KEY>/` 下为该分辨率单独维护页面和控件映射。

## 2. 业务步骤与测试结论

`case.nexus` 是保留的脚本 API 名。`prep/do/check/note` 写入 Scout 本地记录；账号租用仍请求 Nexus。Workbench 根据记录展示原文、步骤和证据：

- `prep/do/check` 只描述原文对应的业务行为；定位比较、截图采集、模型调用、等待和调试说明属于执行诊断。`note` 补事实，不计作问题或有效断言。
- 编写探路进入 `debug_case`，片段不要求原文覆盖和业务断言，结果只作调试记录。正式 `case_run` 使用 `verification` / `regression`，完整性门禁保持有效；只改 `RUN_PURPOSE` 不会把正式任务变成调试会话。修复后的正式 attempt 独立保留，不能覆盖先前失败。
- 报告先给本次范围、预期通过/未通过/未核验/未执行及具体差异，再给证据。`fail` 不是产品缺陷；定位、脚本、OCR、模型策略问题归自动化，资源不足归阻塞，业务差异有证据后仍需说明归因依据。报告消费结构化 `test_report` 与 `assertion/result`，不把日志中的“失败/重试”字样当成问题数。

- `title` 写**这一步具体做什么 / 验证什么**的一句话，取用例原文的意思，例如 `do("输入手机号并点击获取验证码")`、`check("提示验证码已发送")`；
- 不要写 `do("步骤1")`、`do("操作")`，报告里会看不出哪一步坏了；
- 前置、操作、预期都要落进脚本，并且**至少**覆盖原文的每一条：每条前置至少一个 `prep`，每条操作至少一个 `do`，每条预期至少一个 `check`。一条原文可以拆成相邻的几步，标题用原文序号加子号，例如第 2 条操作写成 `do("2-1 打开登录页")`、`do("2-2 输入手机号")`，预期和前置同样用 `1-1`、`2-1`。顺序跟原文一致，先写完前置再写操作；
- 拆步是把一条原文分成几次动作，不是另编原文里没有的步骤。原文缺步骤、对不上或不可判定就停下，并写下差异，不猜；
- 前置写在同文件的 `run`（或同文件的 `pretest`）里，放在所有 `do` 之前。`precondition` 为空、并且确实不用清缓存、登录、安装或授权时，仍然写一条 `prep`，块里可以没有动作，标题写清为什么不做，例如 `prep("不依赖缓存或登录态，安装后直接开始")`。这条标题会写入 Nexus。不要写 `prep("无")`；
- 前置里的「清理缓存 / 清除缓存 / 清除应用数据」，Android 用 `app.clear_cache()`。iOS 上这个方法会 `declined`，不要换别的命令绕过去，做不到就停下问；
- 一个 `with` 块里只放这一步的动作；失败时 Workbench 定位到这个 title；
- 新转换用例的每个原文条目用 `source_ref` 关联执行前从 `CASE_SOURCE` 读取的原文快照，helper 内动作继承当前作用域的 source_ref。静态映射不证明运行覆盖，运行覆盖也不等于业务断言通过；
- 设备动作失败默认中止，保留实际 status/reason_code，不捕获失败后继续冒充成功。`check` 中必须实际执行 `on_page`、`expect`、`vlm(verdict="pass")` 或 `case.nexus.assert_equal(...)` 等注册断言。空 check、仅 screenshot/note 或成功的原生 Python `assert` 都不构成有效断言证据；
- 补充证据用 `case.nexus.note("文字", 键=值)`，不要 `print`；
- 账号用 `case.nexus.account()` 租用，默认使用服务端项目账号约束（旧 YAML 的 `account_requirements` 保留兼容）；需要时显式传 `requirements={"all": [...], "prefer": [...]}` 或 `prefer=[...]`。业务标签辅助排序，缺省或未命中不阻塞选号；实际使用数据时验证原文业务条件，不做全量库存确认。数据需求用 data_need 字符串留存。仓库不写账号密码、登录方式或验证码策略。验证码用 `case.scout.otp(account)`：账号自带码 → Nexus 项目环境配置的 fixed/Gmail/hitl 策略 → 旧仓库兼容码 → 否则 `otp_requires_human`，不猜码。号池为空或没有匹配账号时由 Nexus 按项目环境配置自动补号。

## 3. `app` 的方法与渠道支持

方法名在所有渠道相同，但**不是每个渠道都支持**。不支持的调用会失败并带 `reason_code=declined`，不要用别的写法绕：

| 方法 | android | ios | web | mac | win |
|---|---|---|---|---|---|
| `launch()` `close()` `kill()` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `tap(c)` `input(c, text)` `long_press(c)` `swipe(dir)` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `tap_xy(x, y)` `drag(x1,y1,x2,y2)` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `press(key)` `back()` | ✓ | 仅 home / volume_up / volume_down | ✓ | ✓ | ✓ |
| `set_clipboard(text)` | ✓（部分机型不支持） | ✓ | ✓ | ✓ | ✓ |
| `foreground()` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `exec(script, timeout_ms)` | 设备 shell | 本机命令 | 页面 JS | zsh | PowerShell |
| `install(path)` | ✓ | ✓ | – | ✓ | ✓ |
| `uninstall()` `version()` | ✓ | ✓ | – | – | – |
| `clear_cache()` | ✓ | declined | – | – | – |
| `read_data(key)` `set_ime(ime)` | ✓ | – | – | – | – |
| `reload()` `open_tab(url)` `switch_tab(i)` `upload(path, c)` `wait_ready(ms, c)` | – | – | ✓ | – | – |
| `screenshot()` `sample(ms, interval)` `hierarchy()` `ocr(...)` `on_page(page)` `expect(page=, prompt=)` `expect_text/state/count/value(...)` `wait_for(...)` `vlm(...)` `vlm_frame(i, ...)` | ✓ | ✓ | ✓ | ✓ | ✓ |

`c` 表示控件，写 `page_key.control_id`。`tap` / `input` / `long_press` 可带 `index=`，取同一选择器命中的第几个（0 起，按屏幕顺序）。目前只有 Android 消费 `index`，其他渠道带它会直接 `declined`。所有方法返回 `ActionResult`（`ok`、`summary`、`status`、`data`），`vlm` 系列返回字符串。

### 普通用例默认零模型调用

新用例声明 `MODEL_POLICY={"mode":"off"}`；省略时运行时同样关闭模型。页面身份用 `on_page` 或 `expect(page=...)`，业务文字、状态、数量和值分别用 `expect_text` / `expect_state` / `expect_count` / `expect_value`。`wait_for` 有截止时间，只轮询观察，最后注册一次断言；不靠反复调用模型等待页面。

只有原文需要开放文本语义评价或复杂视觉语义，并且确定性方法不足时，才按 [断言、OCR 与模型例外](references/assertions-and-models.md) 声明原文引用、用途、理由、次数和耗时预算。`expect(prompt=...)` 必须显式 `allow_model=True`；它仍可能调用 LLM/VLM，不能用于普通固定文案检查。VLM 找位置只允许在声明过的 authoring 探路中使用，交付定位优先真实节点，再用显式 OCR 文字/相对关系。

每次有效断言写预期、实际、原文与观察引用。`source_ref` 只是关联编号，不证明语义覆盖：原文 E1 含可见、首位、系列、无重复四个条件时，必须分别验证这四项；登录和到达页面放入前置或操作，不能占用 E1 代替业务验证。交付前逐项对照原文与实际执行的判定，缺失保持未核验。页面成立不能替代业务条件成立。观察截断、缺属性、OCR 置信度不足或多候选时保留未核验/阻塞；不得把未知改成通过。数据比较用 `case.nexus.assert_equal`，页面身份断言不证明账号、数据或业务操作成功。

## 4. 视觉判定与坐标

- `app.vlm(prompt)` 重新采集**这个应用当前屏幕**，返回模型描述；描述本身不算断言；
- `app.vlm(prompt, verdict="pass")`：模型判定未通过会直接中止，`reason_code=vlm_failed`；
- `app.sample(duration_ms, interval_ms)` 连续截图，再用 `app.vlm_frame(i, prompt)` 看第 i 帧；
- Web 的 `app.screenshot()` 默认 `full_page=True`，截取完整文档；只有明确需要当前视口时才写 `full_page=False`；
- 原图与完整事件保存在 Scout。Workbench/Agent 按需通过 Nexus 转发读取，Nexus 不长期保存完整截图；
- `tap_xy` / `drag` 只在控件定位不了、必须依据视觉结果点位置时才用；能用 `pages` 控件就不要用坐标。`vlm` 不返回节点，也不能当成 `locator_spec`。
- 可见文字缺少原生节点时，用 Scout 的 `app.ocr()` 采集文字/边框/置信度，再将实测文字与相对关系声明成 `kind: ocr_text`。不在脚本内安装或自实现 OCR，不保存截图绝对坐标；各端的坐标转换由 Scout 负责。配置与限制见上述参考。

## 5. 规则

- `case.init(...)` 的第一个参数只能写 `case.config.<KEY>`，不写字面量包名 / 地址；Web 分辨率用例只额外写 `web_resolution="720P|1080P|2K|3K/4K"` 关键字；
- 多个应用就多个实例，各管各的页面和截图；同一用例里顺序执行，不并行；
- 控件写 `page_key.control_id`，页面里没有的控件不点；
- `locator_spec` 使用当前平台真实支持并由 Scout 观察到的属性；Android 可用 `resource_id`、`text`、`content_desc`，Web 可用实测角色、属性及容器关系等。对象数据使用本次变量，不将某平台的属性或 button 角色推广到全部应用。用例正文、按钮的中文说法、页面 `label` 都不是选择器。没有这份节点时，页面只留 `id` 和 `label`，不要写 `locator_spec`，也不要写对应的 `tap` / `input`；
  唯一补充是显式 OCR 定位：`ocr_text` 的文字必须来自本次 Scout OCR 结果，区域及相对目标经过该设备核验。OCR 是独立选择器，原生定位失败后不会自动切到它或 VLM。
- 同一屏上这个值出现多次就不能用。优先唯一的 `resource_id`，其次唯一的 `content_desc`，最后才是唯一的 `text`。不可点击的标题和可点击的按钮文案相同，只算可点击的那一个。页面锚点同样只取这一屏真实出现过的文字；
- 用例叫法能对上某个节点的 `text` 或 `content_desc`，定位就用这份文字。对不上时，用这一步截图判断目标在画面的哪一块，只在该区域的真实节点里比较 `locator_spec`。视觉给出的位置不写入 `pages`，也不写 `bounds` 或 `tap_xy`。哪一份定位匹配度最高，用同一调试会话的下一片段点一下再读界面来定，不能把视觉结果原样落成选择器；
- 一格 `selector` 之外还能加 `selectors` 列表，写多把备选（`resource_id` / `text` / `content_desc` / `class` 混着写）。解析按 `resource_id` → `text` → `content_desc` → 包含匹配 → `class` 逐级试，谁先命中用谁。同名节点多时，先用 `resource_id` 收窄，再退回文字；
- 内容型控件用实际容器、组件关系和对象特征收窄；原文指定对象时按运行时引用定位，不默认选首个卡片。只有原文需要某一位置且当前渠道支持 index 时才按序号操作；
- **不要自己再造 Scout 已有的能力**：

| 不要写 | 改用 |
|---|---|
| `time.sleep(...)` | `case.scout.wait(ms)` |
| `imaplib` / `poplib` 取验证码 | `case.scout.otp(account)`（账号自带码 / Nexus 登录策略 / 否则问人） |
| `openai` / `anthropic` 调模型 | `case.scout.llm()` / `app.vlm()` |
| `subprocess`、`os.system`、`exec`、`eval` | `app.exec()` |
| `adbutils`、`playwright`、`appium` 等设备库 | `app.*` |
| `threading`、`multiprocessing`、`asyncio` | 顺序写，不并发（线程挂住会拖垮整个节点） |
| `if platform == ...` | 差异放进 `pages` 的 `locator_spec` |

执行时**不会**拦截这些写法，但它们会让脚本绕开取证、超时和取消，所以写完一定用 `check-test-cases` 自检并按提示改掉。

## 6. 编写流程

涉及业务数据与对象准备时，先读 [运行时数据与业务 flow](references/runtime-data-and-flows.md)。首次进入编写现场时，读 [本机调试会话与两套工作区](references/debug-workspaces.md)。

1. **需求拆解**：按 `analyze-test-case` 固定原文与版本，明确每条前置、操作和业务预期。需求决定测什么，真实页面决定怎么操作。
2. **确认本机现场**：使用 `mino-scout status` 确认本机节点，以 MCP `device_list` 核验该节点设备可执行。没有本机设备时可以整理需求、记录缺口，不能编造定位或声称路径已验证。远端 Scout 只用于正式执行。
3. **启动调试会话**：在整个应用的编写工作区内维护 `config.yaml`、`tests/`、`pages/`、`flows/`。`debug_case` 显式传本机 `node_id`、`sn`、工作区绝对路径、应用 key、环境和请求 ID，不传 Git 地址或 commit。先确认当前 MCP 有这些工具；节点不支持时如实报告，不假设已经部署。
4. **先观察**：使用 `debug_case_execute` 的 `code` 或工作区内 `script_path`，调用 Scout 的 `app.hierarchy()` / `app.screenshot()`。`debug_case_status` 查询请求；`session_events` 按游标读完整证据，截图和大节点沿用原有 screenshot/artifact 接口。接单不是执行完成。
5. **验证定位**：从真实 nodes 或 hierarchy_text 写 pages，确认唯一性、可操作性，再执行动作并验证页面变化。记录会话、请求 ID、workspace_hash、code_hash 和事件引用。同一页面状态的证据可复用；状态或相关定位版本变化后重新核验。
6. **分段打通公共路径**：在同一会话刷新 pages、flows 并反复执行。登录、商详、模型选择、结算等当前需求需要的公共路径先实测，再扩展依赖它们的用例。普通错误只结束当前片段；`write_outcome_unknown` 后只核对证据，不重复写入、不通过 reset 绕过停止。
7. **扩展完整用例**：把已验证路径整理为 `tests/<需求ID>/<case_id>.py` 的 `run(case)`，保留本文件的前置、操作和完整业务断言。到达页面或找到文字不能替代金额、币种、对象关联等预期。缺数据先实际核实，并在已有授权范围内尝试明确准备路径；只有说明和直接 abort 的文件属于缺口记录，不计完整实现。
8. **结束调试并正式验证**：`debug_case_close` 请求结束，等待 Scout 确认停止与资源结算。静态检查通过后固定 Git commit，使用独立初始状态 `case_run`；本机或远端 Scout 都可正式执行。调试现场及片段通过不能拼成整例通过。
9. **修复与定向回归**：按本次失败证据修改，重新核验受影响的定位/路径，固定新版本并创建新的正式 attempt。

进度分别报告：`expected_total`、已声明、草稿、完整实现、路径验证、正式执行，以及正式通过／失败／阻塞／未执行。每项附版本与证据；文件数和 `completed` 不能替代完成用例数或通过数。每批结束都读取 `agent_workflow_get.coverage`，不能凭记忆判断是否还有用例。

正式提交前在编写工作区运行 `mino-scout check --require-cases .`。error 或 warning 必须处理后重新检查；`source_remote/info` 是检查边界，不要求消除。这个正式门禁不阻止向调试会话提交观察片段。调试片段仍遵守 Scout API、设备路由、错误停止及证据要求。
