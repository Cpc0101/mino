# 国际定制 ws 精确补丁建议（未应用）

2026-11-27。仅交付建议，不覆盖正在运行的工作区，不执行登录/生成/取码。已有测试 Agent 在部署后按本说明、当前工具 schema 和原文范围接收修改。

## 原文件与已确认边界

- 原文件：`/Users/changpengcheng/Documents/Codex/2026-11-26/shang/work/ws/qa_gen2.py`；以下行号对应本次读取快照。
- 原文件：`/Users/changpengcheng/Documents/Codex/2026-11-26/shang/work/ws/login_complete.py`。
- 补充读取 `login_finish.py`、`login_send_probe.py`、`login_probe4.py`：已有 Log in button、邮箱/验证码 input、Send/Continue 的脚本定位；兴趣问题 “What do you use Hi3D for?” 与 Skip 来自现有脚本/原事件。它们仍需当前 Scout 观察复核，不据此新增未观察到的 CSS 类或身份定位。
- 四项报告：`/Users/changpengcheng/Documents/Codex/2026-11-27/mino-four-issues/四个问题根因分析.md`。seq184 已证实 POST `/aigc/api/image-task/img-edit` 返回 HTTP200、正文 code401；seq271 已证实原取码成功；seq280/311 为兴趣引导，不是取码失败。
- SDK 已读：`/Users/changpengcheng/code/MinoScout/mino_scout/runtime/web_api.py` 的 `app.network.expect_response`、`response.body.fields`、`response.expect.status/json_field`；这是原生 Scout 网络证据接口，不用 window.fetch monkey patch 充当原生证据。
- **未确认**：发码/登录接口精确 method/path、成功业务码、当前用户接口/字段、Nexus 账号到业务用户的映射。`app.identity` 是 browser actor/context/page 归属，不是后端登录用户，不能拿它替代认证。下面的 contract 输入仅承接部署后实际查证结果，不内置猜测。

## A. 两脚本的显式输入与输出（先做）

`qa_gen2.py:64` 删除共享 tmp 读取，替换为：

```python
p = case.data.require("qa_params", description="本次生成的商品、图片与原文引用")
expected_account_id = case.data.require("account_id", description="本次需认证的 Nexus 账号")
account = case.nexus.account()
case.nexus.assert_equal(str(account.id), str(expected_account_id), "本次租号与显式输入一致")
```

该断言应放在本文件的原文 prep/check 作用域，不能占生成预期。`login_complete.py:82–84` 同样先 require account_id、调用 account() 并核对身份，删除固定 acc ID 和固定 APP003；应用由本次绑定 config 决定，确需显式 app_id 时由当前已核验绑定输入传入。不同 run 租约冲突先管理原 session，不自动改号。

正式 `case_run.case_inputs` 的值按真实用例 ID 或脚本路径组织；不要给 `debug_case_execute` 添加 schema 不存在的参数。旧 debug 版本没有结构化输入时，将非敏感参数固定在捕获的 code 中，或将 JSON 固定为 workspace 输入资源并核对捕获哈希；正式脚本仍消费 case.data。不能靠旧 code 全局变量、共享 qa_params.json 或人为注入 case 私有字段续接。

输入至少包含 qa_params、account_id、execution_ref；qa_params.image 使用 workspace 内的相对资源路径，另传 image_sha256。替换 `qa_gen2.py:76` 的绝对共享路径读取，使用以下公共机制；同一代码也适用于两脚本的输出（留在各脚本或纯机制 helper，不接收整个 case）：

```python
import hashlib
import json
from pathlib import Path

def input_bytes(workspace, relative_path, expected_sha256):
    root = Path(workspace).resolve()
    path = (root / relative_path).resolve()
    if Path(relative_path).is_absolute() or not path.is_relative_to(root):
        raise ValueError("input_path_outside_workspace")
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected_sha256:
        raise ValueError("input_hash_mismatch")
    return data

def save_output(output_dir, execution_ref, name, value):
    if not isinstance(execution_ref, dict) or set(execution_ref) != {"run", "attempt", "request"}:
        raise ValueError("execution_ref_invalid")
    parts = []
    for key in ("run", "attempt", "request"):
        part = execution_ref[key]
        if not isinstance(part, str) or not part or len(part) > 200:
            raise ValueError("execution_ref_invalid")
        if part in {".", ".."} or any(c in part for c in ("/", "\\", "\x00")):
            raise ValueError("execution_ref_invalid")
        parts.append(part)
    if name not in {"qa_result.json", "login_pre_send.json", "login_complete.json"}:
        raise ValueError("output_name_invalid")
    # 哈希目录避免跨平台路径字符差异；正文保留真实执行引用。
    namespace = hashlib.sha256(json.dumps(parts, ensure_ascii=False).encode()).hexdigest()
    directory = Path(output_dir) / namespace
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / name).open("x", encoding="utf-8") as stream:
        json.dump({"execution_ref": execution_ref, "result": value}, stream, ensure_ascii=False, indent=2)
    return str(directory / name)
```

execution_ref 来自真实回执，debug request 就是本次 client_request_id；调用者在提交前核对，不能随便写标签。`case.output_dir` 本已按 task/attempt 隔离，再按 request 命名防 debug 片段互相覆盖。将 `qa_gen2.py:112/131` 的结果写入收敛为异常/正常出口各一次，不能两次保存同一文件；FileExistsError 保留为冲突，不改为覆盖。`login_complete.py:97/124–125` 分别保存脱敏 pre_send 和 final，删除 email、验证码、完整 body 与 raw request body。保存 path 后通过当前证据接口获取 artifact；不能凭文件存在说已封存。大结果不塞入 16KiB 的 case.data.bind。

## B. qa_gen2.py

### B1. 先看可见 Log in，再核验当前用户

在 INFO:7–10 增加可见性判断（沿用原文件与 login_complete 的 button 文案，不新增身份选择器）：

```javascript
const vis=e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return s.display!=='none'&&s.visibility!=='hidden'&&r.width>0&&r.height>0;};
const loginVisible=[...document.querySelectorAll('button')].some(e=>vis(e)&&/^Log in$/i.test(c(e.textContent)));
const emailBox=[...document.querySelectorAll('input[type=email]')].some(vis);
```

返回 loginVisible/emailBox；`qa_gen2.py:73–74` 在 upload、tap Generate **之前**阻断任一条件为真，reason_code 为 authentication_required。二者都 false 仍只是不见登录 UI，必须在当前 context 观察可靠的只读用户身份与成功业务码，按实际映射核对 expected_account_id，再允许 upload/Generate。

当前已读文件没有该接口/定位，不能填一个 `/me`、假 `userId` 字段或把隐藏 email/localStorage token 当身份。已有测试 Agent 部署后先通过 Scout 查询需求接口资料和当前用户事实，记录环境、method/path、字段、映射、成功码及证据引用，形成明确认证 flow。缺失时保留以下 fail-closed 出口而非绕过：

```python
from mino_scout.runtime.script_exec import ScriptAbort
raise ScriptAbort("当前 context 的账号身份与映射尚未核验，禁止生成", reason_code="authentication_identity_unverified", status="blocked")
```

这是必要条件缺口，不是可用于宣称认证修复已通过的完整登录实现。也不要将离线 inputs 中的 authenticated=true 当本次认证证明。

### B2. 原生响应窗口 + code401 快速失败

删除 `PATCH/DUMP` 和 `qa_gen2.py:89–107` 的 fetch hook/正则反复找 taskId。在已核验账号与 Generate 控件后，**点击前**登记只覆盖本次动作的响应窗口；不设置 `status=200/json_fields={code:成功码}`，否则失败响应会被过滤成等待超时。

method/path 可使用报告已证实的 POST `/aigc/api/image-task/img-edit`，部署后核对本环境是否仍为该请求；taskId 的准确字段路径与成功码必须从实际成功响应确认，不能只凭旧正则推定顶层位置。contract 在输入中必须带查证出处；不是由测试数据任意设一个成功值。

```python
with app.network.expect_response(
    method="POST", path="/aigc/api/image-task/img-edit", timeout_ms=20000,
    capture_fields=["code", "msg", generation_contract["task_id_field"]],
) as generated:
    app.tap_xy(b["x"], b["y"])
validate_business_response(generated, generation_contract["success_code"], generation_contract["http_status"])
# 经真实字段契约提取 taskId；无字段/空值返回证据缺口，禁止重新点击。
```

多个候选时保留原生 ambiguous，不加 occurrence=1 取首项。Generate 当前原脚本 en[-1] 也没有唯一性证明，部署后确认真实控件唯一性，再改成 Scout pages 定位；不能复用此前坐标。

公共分类机制如下，适用于生成、发码、登录及结果查询的原生 response；业务码的成功值由已验证接口契约提供，不猜 0/200：

```python
from mino_scout.runtime.script_exec import ScriptAbort

def validate_business_response(response, expected_code, expected_status):
    fields = response.body.get("fields", {})
    code = fields.get("code", {})
    if response.status == 401 or (code.get("found") and code.get("value") in (401, "401")):
        raise ScriptAbort("当前请求被拒绝认证；HTTP 与业务码见原生回执", reason_code="authentication_required", status="blocked")
    if not 200 <= response.status < 300 or response.status != expected_status:
        raise ScriptAbort("请求 HTTP 失败，停止业务等待", reason_code="business_http_failed", status="fail")
    if response.body.get("available") is not True or response.body.get("format") != "json" or response.body.get("truncated"):
        raise ScriptAbort("响应体证据不足，不能判断业务成功", reason_code="business_response_unverified", status="blocked")
    if not code.get("found"):
        raise ScriptAbort("响应缺少已约定业务码", reason_code="business_response_unverified", status="blocked")
    actual = code.get("value")
    if type(actual) is not type(expected_code) or actual != expected_code:
        raise ScriptAbort("明确业务错误，停止等待任务 ID", reason_code="business_response_failed", status="fail")
    response.expect.status(expected_status)
    response.expect.json_field("code", expected_code)
```

异常不捕获成空 reqs/无 taskId。异常出口保存脱敏的原生 request_id/status/code 与截图引用，不重复读取同一错误、更不重放生成。HTTP200/code401 分类为认证拒绝，不断言 cookie 丢失或自然过期。

`qa_gen2.py:54–59、118–122` 结果查询也必须先检查 HTTP 与业务码，再看 task state；不能丢掉 r.status 或 catch 成 `{err:poll...}` 后继续等 60 次。原 POLL 的结果查询路径来自原文件，但其有效性、success code 和成功/失败 state 枚举仍需实际确认。不将泛化 done/任意 result URL 当本模型已成功；task ID、模型 ID 与本次商品归属一起验证。

## C. login_complete.py

### C1. 不把兴趣引导归为未登录

替换 STATE:41–49 的任意 modal 条件：

```javascript
const vis=e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return s.display!=='none'&&s.visibility!=='hidden'&&r.width>0&&r.height>0;};
const emailBox=[...document.querySelectorAll('input[type=email]')].some(vis);
const codeInput=[...document.querySelectorAll('input[type=text]')].some(e=>vis(e)&&/code/i.test(e.placeholder||''));
const dialogs=[...document.querySelectorAll('[role="dialog"],.ant-modal,[class*="modal" i]')].filter(vis);
const interest=dialogs.filter(e=>/What do you use Hi3D for\??/i.test(c(e.innerText)));
const loginDialog=emailBox||codeInput;
const onboarding=interest.length===1;
const onboardingAmbiguous=interest.length>1;
const otherDialog=dialogs.some(e=>!interest.includes(e)&&!e.querySelector('input[type=email],input[type=text][placeholder*="Code" i]'));
```

返回独立的 loginDialog/onboarding/onboardingAmbiguous/otherDialog/loginVisible。不再保留 `not dialog => logged`。兴趣引导若出现，说明可能已进入新用户流程，**不赋 logged=True、不重新发码**。仅当当前 context 身份已核验，才按原文/既有准备授权处理具体 Skip 或填写选择，之后重读结构；不从 DOM 删除 modal。其他 modal 单独处理，冲突状态保持 unknown。`login_finish.py` 中 “没有 emailBox/onboard + /workspace URL” 也不足以认证，不能当认证 flow 复用。

### C2. 发码和登录各有原生证据

在原 `otp_request(account)` **之前**读取并确认 send_contract/login_contract 的 method/path/http_status/success_code、证据出处；缺接口事实立即 data_missing，不发送验证码去猜接口。原 LOCATE 中 Send/Continue 来自已有脚本，但部署后仍应核验当前可见控件的唯一性。

替换 :95–103：

```python
req = case.scout.otp_request(account)
with app.network.expect_response(
    method=send_contract["method"], path=send_contract["path"],
    timeout_ms=20000, capture_fields=["code", "msg"],
) as sent:
    app.tap_xy(loc["send"]["x"], loc["send"]["y"])
validate_business_response(sent, send_contract["success_code"], send_contract["http_status"])
code = case.scout.otp(account, request=req)
```

先注册再 tap，只在真实发码成功后消费同一 OTP request；原生 matcher 不按成功状态过滤，不并行 resource_account_otp，不打印 code。保存脱敏 response.request_id/业务码，保留原窗口耗时；失败/超时先核对原发码结果，不能自动重发。

同样用 login_contract 的精确响应窗口包裹 :112 的 Continue，校验登录业务回执；不要抓取 token 字段或完整登录 body。之后在原 :114–129 的等待中区分登录表单/兴趣/营销/未知，并核验当前用户身份。只有后端身份归属、登录业务成功、目标页面可操作均成立才形成有效注册断言；页面或 OTP 通过不替代它。

原 FILL_EMAIL/FILL 用 `%s` 嵌入邮箱/OTP，容易破坏 JS 字符串，并使 exec 证据含敏感值；接受修改时优先当前实测 Scout input 控件能力及其脱敏机制，不把凭据写入共享 tmp 或原始 note。不得凭此建议虚构 YAML 控件键。

## 部署后的验收边界

这份交接没有运行业务 UI，也没有证明当前用户接口、发码接口或新定位有效。已有测试 Agent 收到部署通知后在原业务 workflow 下，先显式管理旧 session，再查当前账号与原生接口证据、固定 inputs、修改本地脚本、跑 Scout 静态门禁及新的受控 attempt。写结果未知时只读原记录，不重放生成/发码。四项原失败和已成功 OTP 记录保留，不覆盖成“修复后通过”。
