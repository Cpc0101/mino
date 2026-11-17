# 确定性断言、OCR 与模型例外

下列均是 Scout 的实际公共 API。普通脚本声明 `RUN_PURPOSE="regression"`、`MODEL_POLICY={"mode":"off"}`。探路与验收分别使用 `authoring`、`verification`，不会豁免断言或覆盖。

## 确定性检查

```python
with case.nexus.check("显示保存成功提示", source_ref="E1"):
    app.expect_text("保存成功", timeout_ms=5000)
with case.nexus.check("提交按钮可用", source_ref="E2"):
    app.expect_state("edit.submit", "enabled", True)
with case.nexus.check("列表包含三条记录", source_ref="E3"):
    app.expect_count("list.item", 3)
with case.nexus.check("输入内容已显示", source_ref="E4"):
    app.expect_value("edit.name", "Alice")
```

`expect_text(text, control="", present=True, timeout_ms=0, ocr=False, region=None)` 精确比较文字，不作包含匹配或语义改写。`expect_state` 支持 visible/enabled/checked/selected/focused；未暴露状态不能用文字猜。`expect_count` 要求完整结构化观察；截断树不能证明总数或不存在。`expect_value` 只检查可公开读取的值，秘密内容不回读。

`wait_for(control="", text="", state="", expected=True, timeout_ms=5000, ocr=False, region=None)` 轮询只读观察，命中或到期才产生一次断言。明确失败不能通过再问模型覆盖。已注册失败会中止后续写入。

## OCR 与相对定位

OCR 在执行 Scout 本机运行：macOS 使用系统 Vision（需 Swift 编译器，首次初始化计入耗时，编译缓存供后续用例复用）；其他宿主使用 Tesseract 及本机语言包。被测平台与宿主 OCR 引擎是不同概念。缺引擎/语言包返回 blocked，不调用模型兜底。

```python
app.ocr(region=[0.0, 0.0, 1.0, 0.5])
app.expect_text("保存成功", ocr=True, region=[0.0, 0.0, 1.0, 0.5])
```

页面中使用实际平台的 cell（uiautomator/xcuitest/playwright/ax/uia）：

```yaml
locator_spec:
  playwright:
    selector:
      kind: ocr_text
      value: 账户名称
      confidence: 0.8
      region: [0, 0, 1, 0.5]
      relative:
        text: 编辑
        relation: right
        max_distance: 0.3
        alignment: 0.08
```

没有 `relative` 时点击 OCR 文字自身。相对目标也必须有实测文字，relation 是 left/right/above/below；距离与垂直对齐范围按屏幕宽高归一化。重复锚点、多候选、低置信度或定位后画面变化均阻塞。没有文字的图标不能靠 OCR 猜；节点能定位时继续用节点。Web 只采当前视口，iOS 转换为 WDA 点坐标，桌面转换为绑定截图坐标；无需脚本手写平台分支。

## 模型例外

```python
RUN_PURPOSE = "regression"
MODEL_POLICY = {
    "mode": "allow",
    "max_calls": 1,
    "timeout_ms": 15000,
    "total_timeout_ms": 15000,
    "allow": [{
        "kind": "vlm", "source_ref": "E1", "purpose": "visual_assertion",
        "reason": "原文要求验证三维预览内容，当前界面没有可直接核验的状态或基准图",
        "max_calls": 1,
    }],
}

def run(case):
    # 前置及操作仍按原文写在本文件。
    with case.nexus.check("显示原文要求的三维场景", source_ref="E1"):
        app.vlm("检查原文要求的三维场景内容", verdict="pass")
```

`kind=llm` 对应 `purpose=text_assertion`，`kind=vlm` 对应 `visual_assertion`。只返回描述的 `app.vlm` 属于 exploration，仅允许 `RUN_PURPOSE=authoring` 并声明对应原文引用。规则绑定当前 prep/do/check 的 source_ref，调用次数包含失败请求；所有 helper 和前后置共用本条用例预算。`expect(prompt=..., allow_model=True)` 可能先调用 LLM 再 VLM，需要分别声明两条规则及总预算。

普通文字存在、位置、状态、数量、等待不批准模型例外。缺证据、超预算、服务不可用保持 blocked，不生成通过结果。模型日志仅记录请求类型、用途、耗时及服务返回的 token 用量；未返回用量显示未报告。

旧脚本迁移：保留 `expect(page=...)`；将固定文案 prompt 改为 `expect_text`，将状态/数量/值改为对应 API。确需语义验证时增加显式政策，不能为了零模型把业务验证删成页面身份检查。
