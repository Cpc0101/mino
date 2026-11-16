---
name: write-test-cases
description: 将已有人工用例实现为可复用的 MinoScout Python 脚本，关联原文、真实定位和有效断言。用户要求写或修改用例脚本时使用，分析原文见 analyze-test-case。
---

# 编写用例脚本（Scout）

脚本是 Python，一条用例一个文件，在所选设备所属 Scout 的独立进程执行。先按 [analyze-test-case](../analyze-test-case/SKILL.md) 确定原文位置并在 Python 声明 `CASE_SOURCE` 来源变量；仓库与页面配置见 `repo-config`。完整记录保存在执行 Scout，以 Nexus task_id 归档；Nexus 保存任务索引，Workbench 经 Nexus 读取 Scout 详情。

方法签名以本机安装的运行时为准，不确定时读源码，不要凭记忆：

```bash
python -c "import mino_scout, pathlib; print(pathlib.Path(mino_scout.__file__).parent / 'runtime' / 'script_exec.py')"
```

## 1. 写法

设备动作不挂在 `case` 上。先把被测应用实例化，再通过实例操作：

```python
def run(case):
    camera = case.init(case.config.camera)         # 绑定 config.yaml 里的 camera
    with case.nexus.prep("清理应用缓存", source_ref="P1"):
        camera.clear_cache()
    with case.nexus.do("2-1 启动应用", source_ref="S2"):
        camera.launch()
    with case.nexus.do("2-2 点击快拍按钮", source_ref="S2"):
        camera.tap("splash.quick_snap")             # page_key.control_id，页面在 pages/camera/
    with case.nexus.check("出现取景框", source_ref="E1"):
        camera.on_page("viewfinder")
        camera.vlm("画面里有取景框", verdict="pass")
```

三类对象：

| 对象 | 需要实例化 | 方法 |
|---|---|---|
| `app`（`case.init(...)` 的返回值） | 是，一个应用一个 | 见 §3 |
| `case.scout` | 否 | `wait(ms)`、`otp(account)`、`llm(prompt, text, schema)` |
| `case.nexus` | 否 | `prep/do/check(title, source_ref="")`、`assert_equal(actual, expected, message="")`、`account(requirements=None, prefer=None)`、`note(text, **fields)`、`fail(message)` |

`case` 上只有 `config`、`env`、`init`、`scout`、`nexus`。`case.tap(...)`、`case.launch()` 这类写法不存在。写错方法名，运行时会报出相近的名字和可用列表，按提示改。

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

## 2. 步骤事件就是测试报告

`case.nexus` 是保留的脚本 API 名。`prep/do/check/note` 写入 Scout 本地记录；账号租用仍请求 Nexus。Workbench 根据记录展示原文、步骤和证据：

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
- 账号用 `case.nexus.account()` 租用，默认使用服务端项目账号约束（旧 YAML 的 `account_requirements` 保留兼容）；需要时显式传 `requirements={"all": [...], "prefer": [...]}` 或 `prefer=[...]`。只能使用项目已维护的事实，选到账号后仍验证实际前置。仓库不写账号密码、登录方式或验证码策略。验证码用 `case.scout.otp(account)`：账号自带码 → Nexus 项目环境配置的 fixed/Gmail/hitl 策略 → 旧仓库兼容码 → 否则 `otp_requires_human`，不猜码。号池为空或没有匹配账号时由 Nexus 按项目环境配置自动补号。

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
| `screenshot()` `sample(ms, interval)` `hierarchy()` `on_page(page)` `expect(page=, prompt=)` `vlm(...)` `vlm_frame(i, ...)` | ✓ | ✓ | ✓ | ✓ | ✓ |

`c` 表示控件，写 `page_key.control_id`。`tap` / `input` / `long_press` 可带 `index=`，取同一选择器命中的第几个（0 起，按屏幕顺序）。目前只有 Android 消费 `index`，其他渠道带它会直接 `declined`。所有方法返回 `ActionResult`（`ok`、`summary`、`status`、`data`），`vlm` 系列返回字符串。

### 断言用 `expect`，不要一上来就 `vlm`

`app.expect(page="登录页", prompt="当前是登录页")` 按顺序取：

1. 给了 `page`，先独立验证页面锚点；失败就报告该断言失败；
2. 还给了 `prompt`，必须继续验证这条业务预期，不能因在正确页面就跳过；
3. 文本明确回答 no 就失败；只有证据不足时才让视觉模型看新的截图。

每次有效断言写 `assertion/result`，含 checker、原文引用和观察引用。纯数据比较用 `case.nexus.assert_equal(actual, expected)`；预期依赖画面（配色、3D 预览、加载动画）时直接用 `vlm(verdict="pass")`。

## 4. 视觉判定与坐标

- `app.vlm(prompt)` 重新采集**这个应用当前屏幕**，返回模型描述；描述本身不算断言；
- `app.vlm(prompt, verdict="pass")`：模型判定未通过会直接中止，`reason_code=vlm_failed`；
- `app.sample(duration_ms, interval_ms)` 连续截图，再用 `app.vlm_frame(i, prompt)` 看第 i 帧；
- Web 的 `app.screenshot()` 默认 `full_page=True`，截取完整文档；只有明确需要当前视口时才写 `full_page=False`；
- 原图与完整事件保存在 Scout。Workbench/Agent 按需通过 Nexus 转发读取，Nexus 不长期保存完整截图；
- `tap_xy` / `drag` 只在控件定位不了、必须依据视觉结果点位置时才用；能用 `pages` 控件就不要用坐标。`vlm` 不返回节点，也不能当成 `locator_spec`。

## 5. 规则

- `case.init(...)` 的第一个参数只能写 `case.config.<KEY>`，不写字面量包名 / 地址；Web 分辨率用例只额外写 `web_resolution="720P|1080P|2K|3K/4K"` 关键字；
- 多个应用就多个实例，各管各的页面和截图；同一用例里顺序执行，不并行；
- 控件写 `page_key.control_id`，页面里没有的控件不点；
- `locator_spec` 的值必须是这台设备当前界面节点上的 `resource_id`、`text` 或 `content_desc`，逐字复制。用例正文、按钮的中文说法、页面 `label` 都不是选择器。没有这份节点时，页面只留 `id` 和 `label`，不要写 `locator_spec`，也不要写对应的 `tap` / `input`；
- 同一屏上这个值出现多次就不能用。优先唯一的 `resource_id`，其次唯一的 `content_desc`，最后才是唯一的 `text`。不可点击的标题和可点击的按钮文案相同，只算可点击的那一个。页面锚点同样只取这一屏真实出现过的文字；
- 用例叫法能对上某个节点的 `text` 或 `content_desc`，定位就用这份文字。对不上时，用这一步截图判断目标在画面的哪一块，只在该区域的真实节点里比较 `locator_spec`。视觉给出的位置不写入 `pages`，也不写 `bounds` 或 `tap_xy`。哪一份定位匹配度最高，用下一次 `case_run` 点一下再读界面来定，不能把视觉结果原样落成选择器；
- 一格 `selector` 之外还能加 `selectors` 列表，写多把备选（`resource_id` / `text` / `content_desc` / `class` 混着写）。解析按 `resource_id` → `text` → `content_desc` → 包含匹配 → `class` 逐级试，谁先命中用谁。同名节点多时，先用 `resource_id` 收窄，再退回文字；
- 内容型控件（列表卡片、无文字贴图按钮）用 `kind: class` 圈定，再在脚本里传 `index=` 取第几个，不要写死某一行的文案；
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

页面参数、点击、截图、界面结构都只来自 Scout 执行这条用例脚本。`app.hierarchy()`、`app.screenshot()`、`app.tap()`、`app.input()` 就是 Scout 的能力。写的时候调用 `case_run`，由 Scout 跑 `script.run`。不要用浏览器、adb、Playwright 或其他工具去看界面、点控件、抄 DOM。

1. 取**需求**：`case_list` / `requirement_list(project_id)` 给需求索引，不是用例正文。按 `analyze-test-case` 读取原文、确定 `CASE_SOURCE` 来源变量、核对前置与可判定预期；已在当前任务完成这步就复用。
2. 取仓库：`project_list` 拿 `repo_url`、`repo_branch`。
   - 本机路径约定 `~/.mino/workspaces/<project_id>`；
   - 不存在：`git clone --branch <repo_branch> <repo_url>`；
   - 已存在：`git fetch` 后 `git pull --ff-only`；
   - 有未提交改动、有未 push 提交、或 ff 失败：**停下问用户**，不 `reset --hard`，不 force。
3. 选设备：按 `run-test-cases` 调 `device_list`，只选 `executable=true` 且平台与用例一致的一台。没有就停下，**不要按用例正文编 `locator_spec`**。写这一条期间一直用这台设备。
4. 按 `repo-config` 补目录。缺应用就先在 `config.yaml` 加 key（不要写 `app_id`）并建 `pages/<KEY>/`。**改了应用身份字段的话，push 后要调 `repo_apps_sync`**（只传 platform 与包名/URL，不要传 `otp`；见 `repo-config` §3）。Nexus 会按 key 对齐或自动创建应用。
5. 在 `tests/<需求ID>/<case_id>.py` 里用 Scout 把路径走通，再落成可执行脚本。同一份文件改一轮、跑一轮：
   - 还没有真实定位时，脚本只做到达这一屏所必需的事，并调用 `app.hierarchy()` 和 `app.screenshot()`。能用已写好的 `page_key.control_id` 就 `tap` / `input`，没有定位就不点；
   - 通过基础静态检查后，按已有授权 commit/push，用所选设备 `case_run`。只有采集的脚本可能返回 blocked/assertion_missing；这是有证据的探路，不能计为正式通过，继续补齐定位与断言；
   - 从这次会话的 `tool/result` 取界面：`capability_id=hierarchy` 的 `nodes`。没有 `nodes` 时才读同条事件的 `hierarchy_text`，并且只抄里面真实出现的属性。截图用 `session_screenshot`；
   - 一步做完不要只读一帧。用 `app.sample` 连续截几秒，并在这段时间里多次 `app.hierarchy()`。页面可能过一会儿才换。只凭一次读取就说没进到目标页，证据不够；
   - 用这些节点写 `pages/<APP_KEY>/<page_key>.yaml`，只写测过的 `locator_spec`。文字对得上就用文字。对不上时，截图只用来圈定区域，在该区域节点里选出匹配度最高的定位，再用下一次 `case_run` 核对。截图上的坐标不进页面文件；
   - 把对应用例原文的 `prep` / `do` / `check` 补进脚本，只点页面里已经有定位的控件；
   - 一步不是单个控件能完成时（登录填表、滑到底再确认、一组连续输入），写成 `flows/<name>.py`，函数接收 `app`，里面仍然只调用 `app.*`。纯计算、不碰设备的逻辑写成 `scripts/<name>.py`。用例里 `from flows...` 或 `from scripts...` 调用。这两处也要随同一轮 `case_run` 调试，不能只留页面文件；
   - 下一屏重复。原文走完后，脚本必须覆盖每一条前置、操作和预期，不能停在只采集界面的版本。`flows` / `scripts` 搞不定的那一步停下来问，不要换一套工具去点。
6. 写完再按 `run-test-cases` 用同一台设备 `case_run` 调试一遍。`locator_missing`、`control_unknown`、点错控件，回到上一步用这次运行的 hierarchy 改页面，不要按正文重写定位。通过后再向用户汇报。
7. 原文与实际界面不一致时，保留原文快照，把“原文要求、实际观察、差异、证据引用”写入本地 note 并向用户说明。note 记录事实，不能代替断言或自行认定产品缺陷。能验证的后续条目继续处理；受影响条目保持未覆盖/阻塞，不通过改写原文或删除断言让任务通过。
