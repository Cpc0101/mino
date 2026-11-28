# 测试资产与主动准备

## 先分清资源与工具错误

- `plugin`、command、session/attempt/workflow/node 标识、参数位置错误是 Agent 自修任务，不发用户问题。读 schema、原任务、项目/应用/渠道/设备映射，使用精确返回值修正。内部默认值不当作用户指定目标。
- 存在多个符合用户明确要求的真实目标才问；已经回答的问题先回读并 acknowledge，不换 task 重问。
- 没有某个图片/模型/拆件结果是准备缺口，不是最终阻塞理由。查完当前账号不能直接结束任务。

## 三种状态

文件有三个位置。生成任务的 output、可复用库、用例本次副本不能互相代替。Nexus 只保存目录、权限、持有节点和准备状态。Git 不含文件正文；超过 500 KiB 的文件会被 Scout 仓库检查拒绝。

1. **执行任务时生成。** 准备脚本把文件写在 `case.output_dir`，也就是 `~/.mino/scout/accounts/<profile>/workspaces/execution/<task_id>/attempts/<attempt>/output/`。`publish` 只接受这个目录里的文件，复制进本机库并返回 `{asset_id, version, role: "generated"}`。这次任务继续用自己写出的路径，不把库文件再 fetch 回来。
2. **使用之前的。** 之后的 Agent 用 `resource_asset_list` 或准备任务的 `reuse` 取得已有引用。只传递引用，不打开旧任务的 output，也不重新生成。派回 `source.node_id` 那台 Scout；换节点是 `asset_not_on_this_scout`。
3. **用例执行时。** 正式用例从 `case_inputs` 拿到引用。`fetch` 从 `~/.mino/scout/assets/<账号>/library/<sha256>` 校验后，复制到本次用例自己的 `output_dir/.assets/<asset_id>/v<version>/`。用例改的是这份副本。库和当初生成任务的 output 都不变。

```python
generated = case.output_dir / "doll-150.3mf"
# 本次任务把文件写到 generated，再发布
ref = case.assets.publish(
    generated, asset_id="doll-height-150mm", version=1,
    kind="doll", attributes={"height_mm": 150, "joint_mode": "A"},
    source={"generation_task_id": real_generation_id},
)
case.data.bind("doll_input", ref)
```

上述是生成任务的写法，不是完整用例；业务操作/断言/source_ref 仍在本用例 run 内。发布的属性来自实际观察或独立测量，不伪造。文件输入不等于账号历史业务对象；业务记录仍通过账号数据记忆登记并检查环境、归属和当前状态。生成文件不自动成为正确性基准。

```python
ref = case.data.require("doll_input")
path = case.assets.fetch(ref["asset_id"], version=ref["version"])
```

这是用例执行时的取用。按条件选任一合格素材可用 `case.assets.require("doll_input", kind="doll", attributes={"height_mm":150})`；正式复跑通过 case_inputs 注入上次固定版本。账号/应用隔离的待登记队列不会随工作区清理丢失，`case.assets.flush()` 在本应用的新准入任务内重试明确的旧登记，不重做生成。引用不携带路径或传输地址，也不进入报告。

## 缺口处理顺序

1. 开跑前从原文整理所有用例的资源依赖，按环境/类型/属性合并共享需求。
2. `resource_asset_list(state="ready")` 查询可复用资产；查号池对象记忆、原准备脚本、需求和 Scout 事实，验证适用性。
3. 尚无资源时，Agent 选择明确准备脚本，调用 `resource_asset_prepare(task_id,demand={app_id,environment,kind,attributes},recipe_ref)`。任务 ID 属于当前账号和项目。
4. 只有 `claimed=true/action=prepare` 才执行该准备：本机 debug 或固定版本 case_run，生成结果未知先查原生成任务；不因超时换配方、改 demand 或换任务重复花费。
5. `wait`：保持原准备关联，继续独立用例；`reuse`：传回固定资产引用；`inspect`：查原失败结果，已知失败且有新证据才带 retry/retry_evidence 申请新准备次数。每任务准备预算由项目所有者一次配置；0 是未授权自动准备，不逐素材询问。
6. 准备脚本验证文件和属性、publish、bind，Agent 核对 data_outputs 后 `resource_asset_prepared(state="ready",asset_ref,evidence)`。准备失败如实登记 failed。
7. 准备通过不计业务 PASS；以原 account_id、对象与固定资产版本恢复原用例，正式证据仍来自 Scout。

只有查找、探索和现有授权内准备均无法建立前置、必要权限/历史样本无法补齐或预算耗尽时，才带来源、尝试、影响 ID、独立分支进度求助。历史算法样本不能用当前算法新造，生成成本边界不能通过重建 task 绕过。服务端不替 Agent 选择业务配方、生成数据或判断下一步 UI 动作。
