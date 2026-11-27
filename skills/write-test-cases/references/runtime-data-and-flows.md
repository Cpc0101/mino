# 输入数据、运行时绑定与业务 flow

缺数据后的查找、构造、替代和重试决策只属于 Agent。脚本仓不写 `get_or_create`、缺数据自动补数、自动换账号或吞掉失败后继续跑的恢复策略。脚本按明确输入执行；输入缺失时返回具体缺口和当前观察。Agent 在已有授权范围内准备数据后，以新的 attempt 继续验证。

编写前记录输入需求、数据生产者、消费者及对象关联。账号申请用 `case.nexus.account(data_need="需要一个已生成的模型，供商详预览使用")` 留下需求描述。业务标签用作选号偏好；没有标签或账号资产台账不阻塞选号。通过 MCP `resource_account_data_list` 查账号对象记忆，已观察或创建的对象用 `resource_account_data_save` 保存稳定 data_id、object_ref、kind、应用和少量特征。记录只是线索，不是全量库存证明。

原文要求“生成模型”时，用例显式调用生成操作；模型只是输入时，Agent 决定复用还是另行准备。准备也通过 Scout 脚本及 MCP 执行，但不会因此把自动造数策略写入脚本仓。不改变原文操作，不用手工选择其他模型掩盖“当前模型自动带入”的失败。

`flows/` 接收 app、case.scout、页面对象和普通值，维护明确业务操作、阶段观察、有截止时间的等待、对象定位和验证方法。可以用 app.expect_* 注册当前原文作用域内的断言；也可返回结构化实际数据，由用例调用 case.nexus.assert_equal。共享函数不接收整个 case，不创建 prep/do/check，不按 case_id 分派，不决定整例是否阻塞。

用普通字典、dataclass 或函数返回值绑定本次对象：优先实际业务 ID，其次本次可区分的名称、类型、创建标记等组合。同页传变量；弹窗重绘后重读节点；跨页传对象引用并在目标页重新匹配；跨应用传双方可识别的业务 ID 或映射并核验关系。页面句柄、旧节点和坐标不作为长期对象引用。多个候选时不得默认取首项。

阶段判定结合该业务的页面、组件、元素和目标对象，区分进行中、完成、明确失败和未知。固定文案或全局 Download 不证明模型生成完成。定位可使用当前应用真实支持的角色、属性、容器关系和对象特征，不假定所有交互控件都是 button；Web、原生和 OCR 使用各自实测的选择器契约。

每轮调试明确本轮要消除的一个不确定性及截止时间。相同缺口在没有新观察时不重新申请账号或重跑整例；Agent 选择有依据的下一条路径。写入结果未知时先查同一任务和对象，避免重复创建。独立用例继续推进；阶段汇报分别列出分析、实现、数据准备、正式验证。authoring 探针保留诊断结果，不能进入正式通过/失败统计。


## 可执行的数据与定位契约

通用阶段观察、有限等待、对象读取与关联检查由 Scout SDK 的 `mino_scout.runtime.business_state` 提供，脚本仓直接 import。明确的单次生成模板随 Scout 安装包提供，可通过 `importlib.resources.files("mino_scout.templates.script_repo.flows").joinpath("generation.py")` 读取并复制到当前脚本仓 `flows/`，再填入应用真实控件与阶段规则。没有隐式补数、换号或重复创建。Agent 侧调查记录使用 [进度与预算](../../mino/references/workflow-ledger.md) 的 Nexus MCP，skill 不提供执行脚本或本地进度数据库。

`app.observe(control, field="visible|enabled|checked|selected|focused|value|text|count")` 返回 `data.value/known/detail/observation_id`。精确存在文字使用 `field="text_present", text=...`。它记录读取事实，不注册业务断言；`known=false` 不能推测成功或失败。绑定选择器重复命中时保持不确定。正式预期由原文 check 中的 `app.expect_*` 或 `case.nexus.assert_equal` 验证。

`observe_phase` 要求规则的全部信号已知且匹配；多阶段同时成立、可能成立的竞争阶段或不足观察分别保持冲突/未知。`wait_phase` 仅轮询这些读操作，返回 reached、reason、最后观察及耗时；达到明确失败阶段返回 business_failed，截止时间返回 timeout，用例根据原文作出断言。中间轮询不增加辅助断言。

下面展示应用 flow 的规则结构。控件名须换成当前应用已采集并核验的 YAML 键，规则中的完成信号需反映该业务真实状态；这组名称不是 Hi3D 的实测定位。

```python
from mino_scout.runtime.business_state import Phase, Signal, ObjectField, wait_phase, read_object, expect_object

def wait_generated_model(app, scout, model):
    phases = (
        Phase("generating", (Signal("generation.progress", "visible", True),)),
        Phase("ready", (
            Signal("generation.progress", "visible", False),
            Signal("generation.current_name", "text", model["name"]),
            Signal("generation.ready_marker", "visible", True),
            Signal("generation.purchase", "enabled", True),
        )),
        Phase("failed", (Signal("generation.error", "visible", True),)),
    )
    return wait_phase(app, scout, phases, target="ready", failures=("failed",),
                      values={"model": model}, timeout_ms=60000, stable_polls=2)

def read_generated_model(app, requested_name):
    return read_object(app, {"id": ObjectField("generation.current_id"),
                             "url": ObjectField("generation.current_url")},
                       values={"request": {"name": requested_name}})

def expect_preview_model(app, model):
    # 读取实际自动带入的预览，不寻找页面上的另一个同名卡片来代替它。
    expect_object(app, {"id": model["id"], "url": model["url"]},
                  {"id": ObjectField("details.preview_id"), "url": ObjectField("details.preview_url")})
```

用例直接调用 flow，在当前 check 中断言等待结果并验证对象关系。read_object 的 missing 和 evidence 留给用例及 Agent；已读对象值及时 case.data.bind，输出不代表业务预期通过。跨应用时由用例传入目标应用的实际 ID 映射，再复用 expect_object；flow 不推测双方关系。

`case.data.inputs` 返回输入副本；`get(name)` 先读本次输出再读输入；`require(name, description=..., kind=..., attributes=...)` 缺值只返回结构化缺口并终止本次执行，不生成数据；`bind(name, value)` 保存可序列化的本次对象值。单次输出最多 16KiB；禁止凭据、页面句柄和旧节点。`case.nexus.account(data_need=..., data_requirements=[{kind, attributes}])` 记录需求、按记忆偏好选号；输入中有 `account_id` 时锁定该身份，仍遵守租约及环境约束。

```python
# 原用例：明确消费输入，缺值交回 Agent。
with case.nexus.prep("读取商详预览所需模型", source_ref="P1"):
    model = case.data.require("model", description="商详预览需要已生成模型", kind="model")
    account = case.nexus.account(data_need="商详预览需要已生成模型")

# 明确生成操作的准备脚本：generate_model 是该脚本仓已有业务 flow。
# 不在此函数内决定是否补数，也不接收整个 case。
model = generate_model(app, case.scout, requested_name)
case.data.bind("model", model)  # 例如 {"id":"m123", "name":"本次名称", "url":"..."}
case.data.bind("account_id", account.id)
```

页面 YAML 使用 `selector.value: '[data-model-id="{{model.id}}"]'`（CSS）或 `kind: role, name: button, value: '{{model.name}}'`（角色与可见名称）。`app.bind("workshop.model", model=model)` 返回该 app 内的临时控件键；`tap/expect_text/expect_value/expect_state` 接受该键。变量以数据值填充，CSS 自动转义，动作和观察每次重新定位，多个候选明确返回 `locator_ambiguous`，不允许 index 或备用首项。原生使用该平台支持的文字/ID定位；不支持的定位返回明确错误。

- 同页：生成得到 `model`，绑定卡片后验证本次名称/ID。
- 弹窗或重绘：仍传 `model`，在新结构对应的控件模板重新绑定和观察。
- 跨页：携带 `model` 到商详页，绑定预览控件，并用 `expect_value` 等核验同一 ID/URL；导航成功不能替代对象关系验证。
- 跨应用：传普通值到 B，按 B 实际展示的业务 ID 或明确映射生成 B 的绑定键；A 的绑定键只属于 A，不能跨 app 复用。没有共有 ID 时用实际映射及足以区分的组合特征，候选不唯一返回歧义。

## 显式输入与隔离输出

- 正式执行通过 `case_run.case_inputs` 按用例 ID/脚本路径显式传 `account_id`、目标模型/对象、参数和需要的输入资源引用。脚本通过 `case.data.inputs/require` 消费；不从共享 `/tmp/.../qa_params.json`、环境残留或“最新结果”隐式读取。凭据仍由 Nexus 租号提供，不放 inputs。
- 调试只使用当前工具 schema 明确支持的输入方式；不能猜 `debug_case_execute.inputs/case_inputs` 字段。若版本没有结构化输入，非敏感参数作为本片段 `code` 中的显式字面量固定并随 code_hash 留证；输入资源在 workspace 内保留不可变副本并核对捕获文件哈希。不能依赖片段外可变的共享文件。无法固定必需输入时记录缺口，不伪称可复现。
- `script_path` 的新执行可能刷新 `case.data`；code 片段变量保留不等于正式输入继承。重建 session、run 或 attempt 必须重新提供输入，准备任务产出经核验后显式传入续跑任务；不把旧 data_outputs 自动混入本次。
- 输出写到当前 `case.output_dir`。正式 attempt 的目录由 Scout 隔离；debug 多片段可共享同一 attempt 目录，所以还需以本次实际 request 引用建立唯一子目录/文件名，不能仅用可重复 tag 写回共享 q_tag.json。引用来自回执或显式非敏感参数；不猜内部 case.request_id 属性。禁止覆盖前一次文件。
- 对外引用输出时记录 task/run/session/attempt/request、实际账号与环境、输入/源码/输出哈希、对象归属及 artifact 引用。大文件留在隔离输出并通过现有证据接口读取，`case.data.bind` 只保存允许大小的可序列化对象值；输出存在或文件修改时间不等于封存证据或业务通过。
- 账号资源记忆和报告导出可作为索引，但原始输出仍按执行身份保存；跨 run 使用必须显式传对象引用并核验归属，不能将当前共享文件冒充旧 attempt 的输入/结果。
