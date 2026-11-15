# Mino 产品能力与场景覆盖矩阵

> 评估日期：2026-11-15。本文回答「Mino 现在能做什么、覆盖哪些场景、能交付什么、还缺什么」。覆盖等级来自技能与源码静态核查；本次没有连接线上账号、执行业务用例或验收设备。百分比只对应本文固定清单。

Mino 的核心链路是：**Agent 理解测试需求并编写 Python 脚本 → Git 保存配置与测试资产 → Nexus 派发 → Scout 操作真实设备或浏览器 → Workbench / Agent 查看结果**。当前优势集中在 UI 自动化、脚本资产复用和指定版本执行。完整证据、资源管理与规模化执行需要按服务端实现和发布状态分别判断。

**对已有页面定位和脚本的项目，提交基线可以派发基础 UI 测试并读取摘要。首次接入应用的实机编写调试，以及完整证据回溯，仍受默认云端接口缺口限制。** 本文清单的专项覆盖为 **35 / 60（58.3%）**，较完整条目为 **16 / 60（26.7%）**；范围与算法见下文。

## 0. 一页结论

### 0.1 产品覆盖热力矩阵

下表把参考图里的「行业 × 能力」换成 Mino 的「被测端 / 场景 × 交付环节」。分数沿用本文的口径：**3 较完整、2 部分、1 局部、0 未见**。同一行的分数不求和，也不代表整行端到端已经验收；真正判断能否交付时，应看该场景所需链路中最弱的一环。

| 被测端 / 场景 | 接入准备 | UI 操作 | 测试资产 | 断言观察 | 证据回溯 | 批量 / 报告 |
|---|---:|---:|---:|---:|---:|---:|
| Android | 2 | 3 | 3 | 2 | 1 | 1 |
| iOS（WDA） | 2 | 2 | 3 | 2 | 1 | 1 |
| Web / Chromium | 2 | 3 | 3 | 2 | 1 | 1 |
| macOS 原生桌面 | 2 | 2 | 3 | 2 | 1 | 1 |
| Windows 原生桌面 | 2 | 2 | 3 | 2 | 1 | 1 |
| 跨端联动业务 | 1 | 1 | 2 | 1 | 1 | 1 |
| API / 性能 / 安全 / 无障碍 | 0 | 0 | 1 | 0 | 0 | 0 |

这张矩阵得出三个结论：

- **能交付的是单端 UI 回归，而不是「任意业务全自动」。** 已有设备、页面定位、脚本和目标数据时，可以执行基础 UI 流程并读取任务摘要。
- **资产与管理能力明显强于证据和调度能力。** Git、页面、flows、指定 revision 和脚本自检相对完整；完整证据、账号、租约、取消、长批次和报告仍是主要短板。
- **五平台支持不等于五平台同等成熟。** Android 与 Chromium 最深；iOS、macOS、Windows 已有专项渠道但受 WDA、签名、桌面会话和权限等条件约束。

### 0.2 对外表述边界

| 口径 | 可以说什么 | 不能说什么 |
|---|---|---|
| 可承诺（依赖满足时） | 用 Agent 编写 Python UI 用例，经 Git 固定 revision 派发给 Scout，在已接入设备上执行并读取基础结果 | 所有任务都可无人值守通过，或通过摘要完成严谨证据回溯 |
| 可内测 / 有条件试用 | 五平台单端 UI 流程、同平台多应用串联、多环境复用、Nexus 项目环境登录策略、号池自动补号、飞书 / 企业微信通知调用 | 跨浏览器矩阵、跨设备同步事务、未经真实空池与业务登录联调的自动账号流程 |
| 尚未形成产品闭环 | 完整截图 / hierarchy 回读、设备互斥、取消确认、长批次恢复、标准报告与 CI 门禁 | 用前端页面、接口骨架或本地未提交代码证明线上已可交付 |
| 当前不覆盖 | API / 数据库契约、性能压测、安全扫描、无障碍合规和制造 / 工艺真源验证 | 用 `app.exec` 或通用 Python 推断这些专项测试已经完成 |

## 1. 范围与版本基线

本仓是技能入口，不包含整个产品实现。本文交叉核查了关联的三个组件，并以各仓库**已提交的代码**为评分基线；本地未提交增强单列在第 10 节。

| 组件 | 核查版本 / 提交 | 本文使用方式 |
|---|---|---|
| Mino Skills | `0.1.11` / `fb738312aff2f83c1ed86fea3df55b09305d0dc3` | 发布基线 7 个技能、推荐操作路径与声明边界；当前工作区新增 `analyze-test-case`（第 8 个），主评分仍按已提交基线 |
| MinoScout | `0.1.143` / `15d3fed01a5542143906b05d9c4eeff019b2bac3` | 脚本运行时、五类执行渠道、断言、插件和数据源实现 |
| MinoNexus | `f59e59093bbb4e18947e2dd8ed21cc2bca4803e8` | 主评分使用 `cloudflare/`；Python Nexus 另述 |
| MinoWorkbench | 包版本 `0.0.55` / `29d772b68aef755c44d79c55d3349aa74d5b50b8` | 检查真实界面与所依赖接口；页面存在不等于后端能力完成 |

技能默认入口是 [Workbench](https://workbench.minocc.top) 与 [Nexus MCP](https://nexus.minocc.top/mcp)，对应 Cloudflare 路径。Python Nexus 的版本文件为 `0.1.82`，Cloudflare 包版本为 `0.0.1`；两者的能力和版本号不能混用。**本文未核实这些域名当前部署的 commit**，因此提交基线不等于线上发布清单。

### 两种服务端必须分开看

| 能力 | Cloudflare 提交基线 | Python Nexus / 技能声明 | 判断 |
|---|---|---|---|
| 项目、仓库绑定、应用身份同步、需求登记 | 有实现 | 有相应路径 | 可计入基础能力 |
| 指定脚本、设备、提交执行 | 有实现 | 有相应路径 | 可计入，仍需设备和仓库就绪 |
| 任务摘要、用例状态、简化步骤事件 | 有实现 | 更丰富的会话路径 | 基础结果可读，完整回溯有差异 |
| 账号号池、资源租约、写安全恢复 | 项目 / 环境号池、登录策略匹配、空池自动补号与租约已有实现 | 技能描述了租用、隔离与 baseline，Python 树有对应模块 | 可做有条件内测，仍需真实空池、登录和释放联调 |
| `session_events` / `session_screenshot` | 未注册对应 MCP；回调未保存完整 hierarchy / 截图 | 技能要求这些工具，Python 树有相应接口 | 技能操作前必须检查实际工具 |
| Scout 安装 | HTTP 安装与状态查询有实现；MCP 无 `scout_install_token` | 技能要求通过 MCP 申请命令 | HTTP 能力与 Agent 推荐入口存在差距 |
| 长批次、取消、完整任务列表 | 提交基线有明显缺口 | 完整服务端与新工作区有更丰富实现 | 不由前端页面或设计文档推定可用 |

证据：[N1]、[N2]、[N3]、[N4]、[S1]、[S3]。本地其他目录、样例项目和第三方 ESP32 iPhone 原型不纳入产品覆盖率：本次未发现它们与默认执行链的完整接入证据。

## 2. 评分与覆盖率口径

### 覆盖等级

| 分数 | 标记 | 含义 |
|---|---|---|
| 3 | 🟦 较完整 | 在该条目限定的范围内，有较完整的专项提交实现；不代表整个业务、行业或线上部署已验收 |
| 2 | 🔷 部分 | 有专项实现，可完成部分链路，但存在平台、配置、数据、取证或接入限制 |
| 1 | ▫️ 局部 | 只有通用能力可借用、技能声明，或尚未打通的部分链路 |
| 0 | ⬜ 未见 | 在核查范围内未见可交付的专项实现；不表示模型或工程上永远做不到 |
| — | 不适用 | 该平台或该维度不适用，不参与相应统计 |

数字用于表格扫描，标记用于辨认等级。没有历史版本逐格评估，所以不标「提升了多少」或虚构新增百分比。

### 证据状态

- **实现**：已提交代码中存在具体处理路径；不等于线上业务验收。
- **声明**：技能或材料说明了用法，但默认实现的完整性不足。
- **本地变更**：工作区有实现，尚未提交；不计入主覆盖率。
- **待验收**：还需要真实设备、业务数据和完整链路验证。本次所有产品运行效果都属于这一状态。

### 本文计算的指标

第 3 节是唯一计入总百分比的固定清单，共 **60 个功能检查点，6 组，每组 10 项**，等权计分。其中包含基础能力与专项环节的拆分，部分功能相关，不是 60 个互斥能力或全部测试需求的自然总体。业务场景与行业表是能力的不同组合，**不再重复加入分母**。

| 指标 | 算法 | 本次结果 |
|---|---|---|
| 专项覆盖率 | 分数 ≥ 2 的条目 / 60 | **35 / 60 = 58.3%** |
| 较完整条目占比 | 分数 = 3 的条目 / 60 | **16 / 60 = 26.7%** |
| 局部支持占比 | 分数 = 1 的条目 / 60 | 15 / 60 = 25.0% |
| 未见专项支持占比 | 分数 = 0 的条目 / 60 | 10 / 60 = 16.7% |
| 覆盖指数 | 分数总和 / `(60 × 3)` | **101 / 180 = 56.1%** |

覆盖指数只是上述清单的结构性评分。它不是测试通过率、代码覆盖率、用户需求满足率、市场覆盖率或生产可靠性指标。若改变条目粒度或补充测试种类，必须重算并保留旧分母，不能直接比较百分比。

## 3. 工具能力覆盖表：60 项固定清单

评分对象是「Skills + 已提交 Scout + 默认 Cloudflare 控制面 + Workbench 可用接口」的组合。表内明确的边界属于评分的一部分。

### A. 接入、项目与配置

| ID | 能力 | 等级 | 当前可交付范围与主要缺口 | 证据 |
|---|---|---:|---|---|
| A01 | Agent 技能与操作路由 | 3 | 发布基线 7 个技能覆盖上手、配置、编写、自检、执行和更新；工作区新增原文分析技能，发布后为 8 个；需支持 Skills 的客户端 | [S1]、[S8] |
| A02 | MCP OAuth 与授权管理 | 3 | OAuth / 手动 token、授权记录与撤销；需要用户登录授权 | [N1]、[N5] |
| A03 | Workbench 注册与登录 | 3 | 邮箱密码注册、登录、退出和账号会话 | [N4] |
| A04 | Scout 安装与状态验收 | 2 | HTTP 安装 token / 状态、CLI 探活有实现；提交基线缺技能要求的安装 MCP | [S2]、[N4] |
| A05 | 节点、设备和渠道发现 | 3 | REGISTER / HEARTBEAT、在线状态、设备与渠道上报；不把在线等同可执行 | [N6] |
| A06 | 渠道程序与插件运维 | 3 | Chromium、ADB Keyboard、Appium 安装 / 更新及插件状态；只支持既有目录 | [N7] |
| A07 | 项目与应用基础管理 | 3 | 列表、创建项目、创建 / 删除应用；仅 `app_create` 不代表应用配完 | [N1]、[S4] |
| A08 | Git 仓绑定与应用清单同步 | 3 | URL / 分支、应用 key、身份字段、差异更新与 revision；Git 凭据在本机 | [N8]、[S4] |
| A09 | 多环境应用身份 | 2 | `config.yaml envs` 与同步有实现；Cloudflare Workbench 环境管理仍是骨架 | [S4]、[N4] |
| A10 | 模型与节点配置 | 2 | 服务商与节点配置入口、本机文本 / 视觉模型调用；不是所有高级模型管理页都可用 | [R4]、[N4] |

### B. 被测平台与设备动作

| ID | 能力 | 等级 | 当前可交付范围与主要缺口 | 证据 |
|---|---|---:|---|---|
| B01 | Android UI 自动化 | 3 | 控件 / 坐标、输入、手势、界面树、截图、设备 shell；需 ADB 与目标设备就绪 | [R1]、[R5] |
| B02 | iOS UI 自动化 | 2 | WDA 渠道、控件 / 坐标、截图与手势；清应用数据不支持，按键有限 | [R1]、[R6] |
| B03 | Web / Chromium UI 自动化 | 3 | 网页操作、标签页、上传、页面 JS、就绪等待；实际浏览器是 Chromium | [R1]、[R7] |
| B04 | macOS 原生桌面 UI | 2 | 窗口、辅助功能节点、快捷键、截图与安装；需录屏 / 辅助功能权限和可用桌面会话 | [R8] |
| B05 | Windows 原生桌面 UI | 2 | UIA / 坐标、键盘、截图与安装；需正确 EXE / AUMID 和可用桌面会话 | [R8] |
| B06 | Linux 原生桌面被测端 | 0 | Linux 可作部分执行宿主，未见 Linux 原生桌面渠道 | [R1] |
| B07 | Firefox / WebKit / Safari 专项执行 | 0 | Playwright 依赖不代表这些浏览器已接入产品执行链 | [R7] |
| B08 | 同平台多应用串联 | 2 | 一条脚本多个 `case.init`，顺序操作；只能使用本次设备平台的应用 | [S5]、[R1] |
| B09 | 多设备协同与同步交互 | 1 | 可以分别向设备派任务；未见跨设备同步、会合、共享步骤结果的完整编排 | [N2] |
| B10 | 移动应用安装与状态准备 | 3 | Android 装卸、版本、清数据；iOS 装卸、版本；各平台动作差异见第 6 节 | [R5]、[R6] |

### C. 需求、脚本与测试资产

| ID | 能力 | 等级 | 当前可交付范围与主要缺口 | 证据 |
|---|---|---:|---|---|
| C01 | 需求登记与脚本目录映射 | 3 | requirement ID、标题、来源链接，对应 `tests/<需求ID>/` | [S2]、[N9] |
| C02 | 需求原文转 Python 用例 | 2 | Agent 编写 `prep/do/check` 并实机调试；原文必须可读，不能凭需求列表猜步骤 | [S5] |
| C03 | 页面、锚点与跨渠道定位资产 | 3 | `pages/<APP_KEY>`、真实 hierarchy、分渠道 locator、备用选择器 | [S4]、[R1] |
| C04 | 流程、纯逻辑和前后置复用 | 3 | `flows/`、`scripts/`、项目级 pretest / posttest 钩子 | [S4]、[R1] |
| C05 | 指定 Git 提交执行 | 3 | Scout 本机拉仓并定位 revision / 脚本；提交不存在应报错，不悄悄换版本 | [R2] |
| C06 | 脚本源码规范自检 | 2 | `mino-scout check` 检查规范与配置；不检查完整语法、方法名、真实定位 | [S6]、[R3] |
| C07 | 原文条款强覆盖校验 | 1 | 技能要求每条前置 / 操作 / 预期落盘；提交基线没有逐条机器覆盖门禁 | [S5]、[R1] |
| C08 | CSV / XLSX 用例来源读取 | 2 | Scout 有相应用例数据源；不等于默认云端完整用例正文库或表格协作 | [R9] |
| C09 | 飞书表格 / 用例服务来源 | 2 | 存在专用读取路径；字段映射、鉴权和默认 Agent 使用链仍需配置验收 | [R9]、[R10] |
| C10 | 云端用例正文与资产管理闭环 | 1 | 默认需求列表只给元数据；多处资产 / 模块 / 控件页面后端返回空形状 | [N4]、[N9] |

### D. 断言、观察与测试数据

| ID | 能力 | 等级 | 当前可交付范围与主要缺口 | 证据 |
|---|---|---:|---|---|
| D01 | 页面锚点判定 | 3 | 根据页面锚点与界面结构判定页面状态；锚点需要真实采集 | [R11]、[S4] |
| D02 | 界面文字语义判断 | 2 | `expect` 可调文本模型；需要模型配置，存在旧版回退语义限制 | [R11]、[R4] |
| D03 | 截图视觉预期判断 | 2 | VLM 判断画面、布局与视觉状态；不是像素基线或准确率保证 | [R4]、[S5] |
| D04 | 短时多帧采样 | 2 | 连续截图 / 历史帧判断；最多 30 秒、40 帧，不等于录像与 FPS 测量 | [R11] |
| D05 | 强断言门禁与失败锁存 | 1 | 提交基线 `run` 返回即可 pass；原文覆盖与有效断言总量门禁属于本地增强 | [R1]、[R11] |
| D06 | 像素级视觉回归 | 0 | 未见基线图库、diff 阈值、区域忽略与审批闭环 | [R4]、[R11] |
| D07 | 结构化业务数值校验 | 1 | Python 逻辑可辅助比较；提交基线没有专项 `assert_equal` 与业务真源取数闭环 | [R1] |
| D08 | 默认云端账号号池 | 2 | 按 Nexus 项目环境登录策略选择手机号或邮箱账号；无匹配账号时自动新增并递增序号。真实空池、业务登录与并发释放仍需验收 | [N3]、[S3] |
| D09 | 测试固定码与人工验证码 | 2 | 账号自带码 → Nexus 项目环境 fixed / Gmail / hitl 策略 → 旧仓库 `otp.code` 兼容 → `otp_requires_human`；真实登录前置仍需验收 | [S5]、[R4] |
| D10 | Gmail 邮件验证码通道 | 2 | Scout 有显式邮件取码方法 / 插件；普通 `otp()` 不自动回退 Gmail | [R4]、[R12] |

### E. 派发、执行与结果

| ID | 能力 | 等级 | 当前可交付范围与主要缺口 | 证据 |
|---|---|---:|---|---|
| E01 | 指定用例触发与状态查询 | 3 | `case_run`、`task_get`、用例状态、失败原因和执行摘要 | [N1]、[N2]、[N10] |
| E02 | 按需求选择与批量执行 | 2 | `script_targets` / `script.list`；基线一次最多 100 条，顺序执行受长任务限制 | [N2] |
| E03 | 设备互斥与资源占用管理 | 1 | 提交基线没有完整设备互斥租约；技能中的 `executable` / isolation 不能替代实现 | [N2]、[N3]、[S3] |
| E04 | Web 四槽并发与多节点扩展 | 1 | 技能声明每 Scout 四个 Web 会话；默认基线未形成可靠槽位准入闭环 | [S3]、[N2] |
| E05 | 可靠长批次与故障恢复 | 1 | `waitUntil` 顺序派发可借用；持久调度、重启恢复和 ACK 核对未在提交基线闭环 | [N2] |
| E06 | 任务取消闭环 | 0 | Cloudflare 跑批取消写接口尚未迁移；状态枚举含 cancelled 不等于可取消 | [N4] |
| E07 | 测试摘要与失败定位 | 2 | 状态、阶段、耗时、原因、简化步骤 / note；缺完整原始证据时归因受限 | [N3]、[N10] |
| E08 | 完整动作 / hierarchy / 截图回溯 | 1 | Scout 能产生；Cloudflare 基线只保留摘要，未打通完整回读 | [R1]、[N3] |
| E09 | 写操作未知时隔离与 baseline | 1 | 技能有恢复路径；默认基线缺完整写安全、资源释放和证据闭环 | [S3]、[N4] |
| E10 | Workbench 业务实时推送 | 1 | 前端有实时订阅结构；Cloudflare `/ws` 基线仅 ping / pong | [W1]、[N11] |

### F. 工程协作、集成与专业测试

| ID | 能力 | 等级 | 当前可交付范围与主要缺口 | 证据 |
|---|---|---:|---|---|
| F01 | CI 外部触发基础 | 1 | HTTP / MCP 可作为外部编排基础；未见产品级 Actions / GitLab / Jenkins 门禁集成 | [N1]、[N2] |
| F02 | 定时与周期回归 | 0 | 定时设置路由已转向 testing，未见产品级周期任务闭环 | [W1] |
| F03 | 历史趋势、报告对比与标准导出 | 1 | 单任务 JSON 可供外部分析；默认任务历史 / 汇总缺口，未见 JUnit / Allure 完整出口 | [N4]、[N10] |
| F04 | 团队共享与细粒度权限 | 1 | 有按 owner 的账号隔离；组织、角色、共享与 RBAC 未形成完整链路 | [N4]、[W1] |
| F05 | 飞书 / 企业微信通知插件 | 2 | Webhook 配置与调用 / 测试路径存在；不等于测试终态自动通知闭环 | [R12]、[N12] |
| F06 | 缺陷工单自动回写 | 1 | 飞书 / Meego CLI 是集成基础；未见自动建单、去重、关联证据与状态同步闭环 | [R12]、[N7] |
| F07 | API / 协议 / 契约测试 | 0 | 未见专项请求、Schema / 契约、鉴权矩阵和报告链；用例数据源 API 不算接口测试 | [R10] |
| F08 | 性能、压测与稳定性测试 | 0 | 未见负载模型、FPS / CPU / 内存指标、压测执行器和性能阈值报告 | [R11] |
| F09 | 安全与漏洞测试 | 0 | 未见 SAST / DAST、扫描器、漏洞复核与安全报告流程 | [S1]、[N1] |
| F10 | 无障碍合规测试 | 0 | 辅助功能树用于定位；未见 WCAG / 对比度 / 焦点 / 读屏合规验收 | [R8] |

### 分组统计

| 分组 | 专项覆盖（≥2） | 较完整（3） | 局部（1） | 未见（0） | 覆盖指数 |
|---|---:|---:|---:|---:|---:|
| A 接入与配置 | 10 / 10（100%） | 7 / 10 | 0 / 10 | 0 / 10 | 27 / 30（90.0%） |
| B 平台与动作 | 7 / 10（70%） | 3 / 10 | 1 / 10 | 2 / 10 | 18 / 30（60.0%） |
| C 测试资产 | 8 / 10（80%） | 4 / 10 | 2 / 10 | 0 / 10 | 22 / 30（73.3%） |
| D 断言与数据 | 6 / 10（60%） | 1 / 10 | 2 / 10 | 2 / 10 | 15 / 30（50.0%） |
| E 执行与结果 | 3 / 10（30%） | 1 / 10 | 6 / 10 | 1 / 10 | 13 / 30（43.3%） |
| F 工程与专业测试 | 1 / 10（10%） | 0 / 10 | 4 / 10 | 5 / 10 | 6 / 30（20.0%） |
| 合计 | **35 / 60（58.3%）** | **16 / 60** | **15 / 60** | **10 / 60** | **101 / 180（56.1%）** |

较高的接入与 UI 操作评分，不能抵消证据、账号和调度上的缺口。面向交付判断，应逐项检查场景所需的全部环节。

## 4. 业务场景覆盖矩阵

这里的等级评估**场景链路**，比单条工具评分更严格。例如 Android 动作是 3，端到端回归仍可能因账号、断言和取证限制评为 2。所有场景都需要真实界面与目标数据验收。

| 场景 | 等级 | 适用平台 | 当前可以完成 / 交付 | 主要边界 |
|---|---:|---|---|---|
| App / Web 主流程冒烟 | 2 | Android / iOS / Web / macOS / Windows | 启动、导航、关键操作、页面判断、指定提交执行与摘要 | 设备、页面、断言就绪；默认完整证据仍有限 |
| 表单、搜索、筛选、列表回归 | 2 | 五平台 | 可复用页面 / 流程脚本；输入、点击、滚动与结果判断 | 动态内容定位要真实采集；`index` 仅 Android |
| 登录与验证码 | 1 | 五平台 | 登录动作可写成 flow；测试固定码与人工码可辅助 | 默认云端号池不可用；普通 OTP 不自动收短信 / 邮件 |
| 注册、权限弹窗与首次启动 | 2 | 移动端为主 | 操作可见弹窗、验证首次流程、Android 清数据准备 | iOS 无清数据；系统弹窗 / 受保护页面需逐机验证 |
| Android 安装、卸载、清数据回归 | 3 | Android | 版本检查、安装准备与状态重置 | 只指这些设备动作；不包含完整商店发布 / 升级兼容认证 |
| iOS 安装与版本验证 | 2 | iOS | 安装、卸载、读版本及可用 WDA 上的 UI 流程 | 签名、WDA、连接与设备条件；不支持清应用数据 |
| Web 多标签与文件上传 | 2 | Web | 标签切换、上传、等待页面就绪和页面 JS | Chromium 专项；文件访问权限与页面状态需验证 |
| Web 跨浏览器兼容 | 0 | Web | 当前只能完成已接入 Chromium 的验证 | Firefox / Safari / WebKit 未形成专项产品执行链 |
| 桌面业务软件操作回归 | 2 | macOS / Windows | 窗口 / 控件操作、快捷键、界面判断与截图 | 本机桌面会话、权限、应用身份；不是后台服务测试 |
| 多环境相同流程回归 | 2 | 五平台 | config 中按环境切包名 / URL，复用脚本与页面 | 默认 Workbench 环境管理不完整；需核对派发环境 |
| 多机型、多系统兼容验证 | 2 | 已接入平台 | 分别在指定设备运行相应脚本，维护平台 locator | 不等于自动生成全机型矩阵或可靠并行调度 |
| 同平台多 App 串联 | 2 | 五平台 | 多个应用实例按顺序操作，如业务 App 与同平台辅助 App | 同一脚本仅本次平台；不支持跨设备同步闭环 |
| Android + iOS + Web 联动业务 | 1 | 跨平台 | 可拆成各端独立用例、由外部组织执行 | 未见跨端同步、共享账号状态与统一事务断言 |
| 电商浏览、购物车、订单 UI | 2 | 五平台 | 可见页面与流程操作、页面状态检查 | 登录依赖、真实支付、退款、库存 / 财务真源需另接与核验 |
| 提交、删除等有副作用流程 | 1 | 五平台 | 工具能操作；需要明确测试数据与人工确认安排 | 默认写安全隔离 / baseline 不完整，不宜承诺无人值守 |
| 画面、布局、预览与视觉状态 | 2 | 五平台 | VLM、截图与短时多帧观察 | 模型判断，非像素差分、精密色差或视觉准确率保证 |
| 加载态、弹窗消失等短时变化 | 2 | 五平台 | 多次 hierarchy、连续截图、等待与历史帧检查 | 采样不是录像、FPS、启动耗时基准或长期稳定性测试 |
| 需求文档转测试资产 | 2 | 平台无关 + 实机调试 | 需求目录、Python 用例、页面、flows 与 Git 版本 | 需读取原文；不自动补造缺失步骤；强覆盖门禁未发布 |
| CSV / XLSX / 飞书用例接入 | 2 | 用例来源侧 | Scout 有专用读取路径，可辅助转换成脚本 | 与默认需求目录、鉴权和字段映射的整条链需验收 |
| 失败分析与证据回溯 | 1 | 五平台 | 云端摘要、状态、阶段和失败原因 | 完整截图 / hierarchy 回读缺口限制严谨归因 |
| 发布前大规模无人值守回归 | 1 | 多设备 / 多节点 | 可借用脚本资产与派发接口 | 号池、租约、长任务、取消、完整报告、CI 门禁尚需补齐 |
| 周期监控与线上巡检 | 1 | UI 可借用 | 可由外部触发既有脚本 | 内置定时、告警策略、SLA、长周期恢复未见完整实现 |
| API、数据库与后端契约验证 | 0 | 后端 | 当前 UI / 脚本能力可成为未来接入基础 | 没有专项 API / DB / 契约执行与报告链 |
| 性能、安全、无障碍合规验收 | 0 | 专项测试 | 当前只能辅助操作和观察 | 缺专项指标、标准、执行器及合规报告 |

## 5. 行业与产品形态映射

行业表说明「当前工具可覆盖的测试环节」。行业包含的研发、运营、认证与生产过程更广，不把 UI 可操作性转换为整个行业百分比。

| 行业 / 产品形态 | 可覆盖测试场景 | 当前覆盖 | 主要行业缺口 |
|---|---|---|---|
| 电商、零售、交易平台 | 搜索筛选、商品详情、购物车、订单页面 | 部分 UI 链路 | 支付 / 退款、库存对账、促销计价、资金与后端一致性 |
| 企业 SaaS、CRM、ERP、OA | 表单、审批页面、列表、筛选、配置入口 | 部分 UI 链路 | SSO、组织权限、审计、业务数据真源、跨服务事务 |
| 内容、社交、资讯、社区 | 列表、详情、搜索、发布入口、交互状态 | 部分 UI 链路 | 发布副作用、推荐质量、内容安全、实时消息与多账号联动 |
| 教育、学习、考试系统 | 课程导航、题目页面、表单、结果页面 | 部分 UI 链路 | 评分真源、考试完整性、直播 / 音视频、长期学习数据 |
| 金融、保险、支付 | 页面、输入、导航和可见提示 | 局部至部分 | KYC、生物识别、支付安全、账务核对、风控和合规认证 |
| 医疗、健康 | 表单、预约入口、信息展示与客户端流程 | 局部至部分 | 临床正确性、隐私、设备联动、医疗认证与风险验证 |
| 本地生活、物流、出行 | 搜索、订单页面、状态展示和客户端路径 | 部分 UI 链路 | GPS / 地图专项、实时调度、骑手 / 用户多设备协同 |
| 相机、影像、3D 展示 App | 可见按钮、取景 / 预览状态、视觉判断 | 部分 UI 链路 | 图像质量、算法指标、精密色彩、视频质量和硬件性能 |
| 游戏与交互娱乐 | 菜单、登录入口、设置、可见交互与画面 | 局部 | 无节点画面的稳定定位、实时操作、帧率、同步 / 反作弊、引擎测试 |
| 桌面生产力与创作软件 | 打开应用、菜单、窗口、快捷键、表单 | 部分 UI 链路 | 不等于生成专业作品；文件语义、插件生态和专业质量验收另需能力 |
| 开发工具、运维控制台 | Web / 桌面管理页与可见状态 | 部分 UI 链路 | 不等于部署、基础设施运维、服务监控或故障演练平台 |
| IoT、智能硬件、车载 | 已接入客户端的可见 UI | 局部 | 固件、总线协议、传感器、HIL、实物动作与硬件安全 |
| CAD、制造、工业软件 | 已接入桌面软件的界面操作 | 局部 | 参数 / 几何真源、CAE / CAM、工艺、生产执行和实物认证 |
| API 服务、数据平台、AI 服务 | 可以辅助相关管理界面 | 局部 UI，专项测试未覆盖 | 协议、数据质量、模型评测、性能、安全和服务端正确性 |

这些是基于工具的**可适配场景**，不是已经落地的客户案例清单。本次没有客户任务、行业验收样本或业务通过率数据。

## 6. 平台与脚本 API 明细

### 被测端与执行宿主

| 被测端 | 身份字段 | 主要执行渠道 | 必须核实的条件 |
|---|---|---|---|
| Android | `package` | ADB / Android executor | ADB、连接授权、目标设备与输入组件 |
| iOS | `bundle_id` | WDA executor | 配套连接、签名 / WDA 服务与设备状态；安装 Appium 不等于另有 Appium executor |
| Web | `url` | Playwright / Chromium | 已安装 Chromium、页面与网络可达、文件 / 登录权限 |
| macOS | `bundle_id` | 桌面 driver / AX | macOS 本机、已登录图形会话、录屏与辅助功能权限 |
| Windows | EXE 路径或 AUMID（`package`） | 桌面 driver / UIA | Windows 本机、可操作的桌面会话、应用身份与权限 |

Scout 安装面向 macOS、Linux、Windows 宿主。**安装系统数量与被测平台数量是不同维度**：例如 Linux 宿主不增加一个 Linux 桌面被测渠道，安装 Scout 也不自动让五个平台同时就绪。[R1]、[R8]、[N4]

### `app` 公共方法与渠道差异

✓ 表示该渠道有对应实现 / 技能用法，不表示任意应用和设备都成功；受限处写明条件。`—` 表示没有该专项 API 或不适用。参数签名以安装的运行时为准。[S5]、[R1]

| API / 能力 | Android | iOS | Web | macOS | Windows |
|---|---|---|---|---|---|
| `launch` / `close` / `kill` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `tap` / `input` / `long_press` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `swipe` / `tap_xy` / `drag` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `press` / `back` | ✓ | 仅 home / 音量键等限定语义 | ✓ | ✓ | ✓ |
| `set_clipboard` | 部分机型受限 | ✓ | ✓ | ✓ | ✓ |
| `foreground` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `exec` | 设备 shell | 连接设备的本机命令 | 页面 JavaScript | zsh | PowerShell |
| `install` | ✓ | ✓ | — | `.app` / `.pkg` / `.dmg` | `.exe` / `.msi` |
| `uninstall` / `version` | ✓ | ✓ | — | — | — |
| `clear_cache` | ✓，实际为清应用数据路径 | 明确 `declined` | — | — | — |
| `read_data` / `set_ime` | ✓ | — | — | — | — |
| `reload` | — | — | ✓ | — | — |
| `open_tab` / `switch_tab` | — | — | ✓ | — | — |
| `upload` / `wait_ready` | — | — | ✓ | — | — |
| `screenshot` / `hierarchy` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `sample` / `vlm_frame` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `on_page` / `expect` / `vlm` | ✓ | ✓ | ✓ | ✓ | ✓ |
| 控件 `index=` 选择第 N 个 | ✓ | `declined` | `declined` | `declined` | `declined` |

这张表覆盖 32 个公共 `app` 方法，按同类能力合并展示。它不统计执行器内部事件、节点运维 RPC 或第三方库的全部方法。

### 编写和断言的关键限制

1. **跨端复用需要页面资产。** 同一份业务脚本可使用分渠道 locator，但每端仍需真实界面定位；一条运行只能初始化本次平台的应用，不是零配置跨端。
2. **源码自检是提示工具。** 提交基线的 `check` 跳过无法 AST 解析的文件，不检查所有方法名、不验证 locator 来源和实机点击。没有提示不能证明能执行或能通过。
3. **运行成功不必然证明业务预期。** 提交基线中 `run(case)` 返回即可 pass，没有有效断言总量门禁；`expect(page=..., prompt=...)` 的页面锚点命中会先返回，文本模型给 no 后仍可能继续视觉回退。不能把任务 pass 宣称为所有业务条件严格成立。
4. **采样只观察短时画面。** 上限 30 秒、40 帧、间隔 200–5000 ms；没有视频录制、音轨、FPS 或性能基准保证。
5. **通用命令不增加专项覆盖。** `app.exec` 能执行命令，不等于已交付 API 测试、压测、安全扫描、数据库验证、制造工艺或任意专业软件连接器。

## 7. 用户工作流与交付物

| 环节 | 当前入口 | 交付物 / 成功条件 | 关键依赖 |
|---|---|---|---|
| 理解分工与工具选择 | `overview` | 明确 Agent / Git / Nexus / Scout / Workbench 的职责 | Skills 客户端；[S1] |
| 注册、授权、安装和绑定 | `onboarding` | 用户授权、Scout 在线、项目与脚本仓绑定、应用同步 | 安装 MCP 必须实际存在；[S2] |
| 配应用与环境、组织页面 | `repo-config` | `config.yaml`、`pages/`、已 push revision 与同步清单 | 身份字段和环境明确；[S4] |
| 分析人工用例原文 | `analyze-test-case`（工作区新增，待发布） | 固定原文版本、P/S/E 编号、输入 / 前置 / 动作 / 预期及未知项 | 原文可读；未发布前只能作为本地增强；[S8] |
| 把需求写成可执行用例 | `write-test-cases` | `tests/`、复用 `flows/` / `scripts/`、实机定位和调试记录 | 原文、设备、仓库、相应证据读取入口；[S5] |
| 自检与修正 | `check-test-cases` | 源码规范检查结果与修正后的文件 | 本机 CLI；不替代执行；[S6] |
| 触发执行与查看结果 | `run-test-cases` | task ID、revision、设备 / 环境、状态、失败原因与结果链接 | 实际任务 / 会话接口；[S3] |
| 安装 / 更新技能 | `update-skills` | 已安装真实技能目录、版本和变更记录 | GitHub 与客户端加载机制；[S7] |

测试资产的边界：

```text
config.yaml                     应用 key、平台、环境身份（登录与接码策略在 Nexus 项目环境配置）
pages/<APP_KEY>/<page>.yaml      页面状态与控件定位
tests/<requirement_id>/<case>.py 单条可执行检查
flows/<name>.py                 可复用业务动作
scripts/<name>.py               不碰设备的纯逻辑
pretest.py / posttest.py         可选项目级钩子
```

需求列表中的链接提供原文入口，**不提供完整用例步骤正文**。脚本仓保存可执行测试资产；Nexus 不替 Agent 写文件，不拉取私有仓内容，也不保存 Git token。

当前编写调试的一个关键前提是：必须能拿到本次 Scout 执行产生的 hierarchy / 截图。默认 Cloudflare 提交基线不满足技能要求的完整回读，所以「基础脚本能派发」和「Agent 能按推荐路径完成实机编写闭环」需要分别验收。

## 8. MCP、CLI 与外部集成清单

### Cloudflare 提交基线的 18 个 MCP 工具

| 分组 | 工具 | 覆盖范围 |
|---|---|---|
| 使用说明 | `agent_guide` | 工具分工与操作路径 |
| 项目 / 应用 | `project_list`、`project_create`、`app_create`、`app_delete` | 基础元数据管理 |
| 节点 / 设备 | `scout_list`、`device_list` | 在线资源查询 |
| 安装 / 插件 | `plugin_status`、`node_channel_program`、`plugin_install` | 既有渠道程序与插件 |
| 需求 | `case_list`、`requirement_list`、`requirement_save` | 需求元数据和来源链接；前两者是相同需求列表语义 |
| 脚本仓 / 应用清单 | `project_script_repo_set`、`repo_apps_sync`、`repo_apps_get` | 仓绑定、应用身份与 revision 同步 |
| 执行 / 结果 | `case_run`、`task_get` | 指定脚本派发和单任务详情 |

数量来自 [N1] 的注册表。工具别名和相同语义不视作新增业务能力；`agent_guide` 文案中提到某工具，也不证明该工具已注册。

技能点名、但这一提交基线未注册的关键 MCP：`scout_install_token`、`session_events`、`session_screenshot`、`task_write_safety_baseline`。其中安装已有 HTTP 路径，不能由此声称 MCP 入口已可用。当前工作区扩展到 29 个注册工具，见第 10 节；上线调用时仍以实际 `tools/list` 为准。

### 本机 CLI 与节点运维

- `mino-scout` / `status`、`probe`：本机服务与设备就绪检查。
- `mino-scout check .`：脚本资产源码规范自检。
- Cloudflare 节点 HTTP 有日志、停止 / 重启 / 休眠 / 唤醒、更新、claim、插件配置 / 调用、配置导入导出等路径；并非所有动作都有 MCP 入口。

### 外部集成层级

| 集成 | 当前证据 | 可以说什么 | 不能直接推定什么 |
|---|---|---|---|
| Git 仓库 | Scout 拉仓、分支 / revision、需求目录脚本 | 支持 Git 管理测试资产与指定提交执行 | Nexus 托管代码 / 凭据、自动新建仓库 |
| CSV / XLSX | Scout 用例来源解析 | 有用例读取能力 | 通用电子表格产品、云端完整用例库 |
| 飞书表格 | Scout 专用读取路径 | 可作为用例来源，需要鉴权和映射 | 任意飞书文档完整解析 / 双向同步 |
| 用例服务 API | 专用读取客户端 | 可读特定格式的用例来源 | 任意测试管理系统连接器 / API 测试平台 |
| 飞书 CLI / Meego CLI | 安装、配置与节点调用基础 | 有外部协作工具接入基础 | 缺陷自动建单、去重、证据关联、回写闭环 |
| 飞书 / 企业微信 Webhook | 插件配置与通知调用 | 可发配置通道支持的通知 | 测试终态订阅、可靠重试、统一告警策略 |
| Gmail | 显式取码方法、插件 | 有邮件验证码取码通道 | 所有 OTP 自动回退、短信 / TOTP / CAPTCHA 全覆盖 |
| OpenAI 兼容模型服务 | Scout 文本 / 视觉调用实现 | 可配置相应接口的模型进行判断 | 任意厂商 SDK 兼容、判断准确率或完全离线保证 |
| 第三方 MCP 服务 | 只有插件类别，未见具体通用接入项 | 可作为后续扩展方向 | 任意 MCP server 自动注册、发现、调度 |

证据：[R2]、[R4]、[R9]、[R10]、[R12]、[N7]、[N12]。

## 9. 证据、结果与当前交付边界

### 测试证据的三层

| 层级 | 提交基线情况 | 交付判断 |
|---|---|---|
| Scout 产生动作、hierarchy、截图 | 有运行时实现；显式截图可写入 `script.session` 回调 | 能采集不代表云端已保存、Agent 已可读取 |
| Cloudflare 保存结果 | 状态、耗时、原因、简化步骤、动作摘要、notes / fail | 可读基础结果；每用例最多 300 条简化事件 |
| Agent / Workbench 完整回溯 | 提交基线缺 session MCP 和完整截图 / hierarchy 存取 | 不承诺完整回放、逐帧证据或严谨自动归因 |

模型在 Scout 本机调用，和测试证据的传输 / 存储位置是两件事。已有材料里的「截图不回 Nexus」不能直接概括所有版本：提交基线 Scout 会把显式截图写进回调，但 Cloudflare 处理只保存摘要；新工作区则采用本地详细记录与云端摘要索引。对隐私、留存或离线能力作说明前，必须确定实际部署路径。[R1]、[N3]

### 测试结论还应区分

| 情况 | 应报告 | 不应混淆 |
|---|---|---|
| 业务预期有明确证据未成立 | 产品问题候选，附步骤与证据 | 不凭任务 fail 一律判产品缺陷 |
| locator / 方法 / 配置错误 | 脚本或资产问题 | 不说成被测产品缺陷 |
| 渠道不支持，返回 declined | 拒绝执行与 reason code | 不说成环境故障或通过 |
| 前置无法满足或未执行 | blocked / skipped 与原因 | 不把未执行算测试通过 |
| 验证码需要人、资源隔离 | 阻塞及所需动作 | 不自动猜码、抢资源或宣布已恢复 |
| 只有页面锚点成功 / 没有有效业务断言 | 已完成的检查范围 | 不宣称全部业务条件通过 |

技能要求失败后看会话再归因、不要自动重跑、baseline 不改变原 blocked 结论。这些是推荐行为；默认控制面相关工具缺失时应明确停止该步并报告缺口。[S3]

## 10. 本地增强：待提交、待发布、待验收

核查时 Skills、Scout、Nexus、Workbench 均存在未提交变更。下面记录可见实现方向，**全部不计入第 3 节的主覆盖率**，也不标为本版已新增覆盖。

| 本地增强 | 涉及实现 | 可能补足的条目 | 发布后最低验收 |
|---|---|---|---|
| 原文分析与覆盖映射 | Skills `analyze-test-case`；用例原文 sidecar 与 `source_ref` 约定 | A01、C02、C07 | 原文版本可追溯；P/S/E 编号不漂移；未知项不被自动补造 |
| 完整 Scout 本地记录 | Scout `runtime/records.py`、`server_comm/script_records.py`；Workbench 新记录视图 | E07 / E08、C10 | 动作、原文、断言、截图对应一致；重启保留；离线提示明确 |
| 云端摘要 + 按需证据代理 | Nexus `record_proxy.ts`、`execution_routes.ts`；Workbench `scoutRecords.ts` | E08、Agent 编写调试闭环 | 认证读取、分页 / 分块截图、节点离线、无越权；不遗漏原始证据 |
| 持久派发与可靠执行 | Nexus `task_scheduler.ts` / hub；Scout 接单、attempt、摘要 ACK | E03 / E04 / E05 | 设备互斥、Web 四槽、重复请求、断连 / 重启、ACK 丢失不重复写 |
| 账号池与租约 | Nexus `account_pool.ts`、`project_env.ts` | D08、登录场景 | 项目 / 环境匹配、空池自动补号、序号递增一次、租用释放、凭据保护、并发不串号 |
| 取消与未知结果处理 | 调度器、执行 routes 与 Scout 中断链 | E06 / E09 | 取消落地；写结果不明保持隔离；释放不改变原任务结论 |
| 强原文覆盖与有效断言门禁 | Scout `script_validation.py`、运行时 source_ref / `assert_equal` | C07 / D05 / D07 | 无断言不 pass、失败锁存、漏条款拒绝、数值比较有证据 |
| 任务列表与记录展示 | 新执行 routes、Workbench task / record 页面 | E07 / F03 | 列表、汇总、状态与详细记录一致；不是空数组骨架 |
| MCP 扩展与确认流程 | Nexus `mcp.ts`、`mcp_confirm.ts` | A04、E06 / E08 / E09 | 工作区 29 个工具与真实发布 `tools/list` 一致，确认与权限有效 |

涉及跨仓库协议的增强应作为同一条端到端链路验收，不能只上线一端后提高评分。本地文件路径按核查时记录，不承诺下一发布的文件名或接口数量。

## 11. 补齐优先级建议

这是根据当前缺口提出的产品建议，不是已承诺路线图。

| 优先级 | 要补的链路 | 为什么优先 | 完成标准 |
|---|---|---|---|
| P0 | 默认 MCP 与技能对齐 | 安装和实机编写依赖工具缺口会阻断上手 | 发布后新账号按 8 技能完成注册到结果，不绕开规定入口 |
| P0 | 完整证据与强断言 | 只有动作成功和摘要不足以证明业务预期 | 每条预期有可回读证据；无断言 / 失败不能误判 pass |
| P0 | 账号、租约、取消、持久调度 | 决定批量测试和有副作用任务能否可靠交付 | 并发 / 断线 / 重启 / 取消 / 未知写结果均有明确状态 |
| P1 | 环境、用例资产和任务历史 | 前端骨架与真实数据不一致影响日常管理 | 写入持久化、列表 / 汇总一致、来源到脚本可追踪 |
| P1 | CI、标准报告、终态通知 | 让单次执行进入研发发布流程 | 指定 commit 触发、标准结果 / 门禁、证据链接与可靠通知 |
| P1 | 跨浏览器与设备矩阵 | 扩大 Web 与移动兼容验证的实际覆盖 | 明确浏览器 / 版本支持，设备组合可调度，结果可比较 |
| P2 | 专项测试与行业连接器 | 扩大当前 UI 能力之外的业务验证 | API / 性能 / 安全 / 无障碍各有独立执行、指标和报告 |

## 12. 维护与证据索引

### 后续如何更新

1. 固定 Skills / Scout / Nexus / Workbench 的发布提交与部署路径，先核对实际 MCP 注册表和执行器。
2. 逐项记录「实现证据 → 可执行样例 → 业务验收」，本地代码只进入待发布表。
3. 修改 60 项清单的评分时同步修改总表与分组统计；新增 / 删除条目时同步修改分母并留旧版快照。
4. 新增场景必须列交付物、必要依赖和失败边界；行业场景仍不重复计数。
5. 报告实际客户需求覆盖率时，另建该客户需求清单：`已验收需求数 / 适用需求总数`；未执行、阻塞、模型误判不算完成。
6. 真正运行测试后另报 pass / fail / blocked / skipped / declined 与统计分母，不用本文覆盖指数代替运行结果。

在仓库根目录可用下面的只读脚本复算第 3 节，避免更新评分后遗漏统计：

```python
from pathlib import Path
import re

text = Path("CAPABILITY_COVERAGE.md").read_text(encoding="utf-8")
rows = re.findall(r"^\| ([A-F]\d{2}) \| [^|]+ \| ([0-3]) \|", text, re.M)
assert len(rows) == 60 and len(dict(rows)) == 60
for group in "ABCDEF":
    assert [key for key, _ in rows if key.startswith(group)] == [
        f"{group}{i:02d}" for i in range(1, 11)
    ]
for label in [*"ABCDEF", "TOTAL"]:
    scores = [int(v) for k, v in rows if label == "TOTAL" or k.startswith(label)]
    n = len(scores)
    supported = sum(v >= 2 for v in scores)
    print(label, f"专项 {supported}/{n}={supported/n:.1%}",
          {v: scores.count(v) for v in range(4)},
          f"指数 {sum(scores)}/{3*n}={sum(scores)/(3*n):.1%}")
```

### 核查来源

技能证据链接到本仓文件；关联实现链接固定 Git commit，避免本地未提交变更改变取证依据。没有读取账号数据、业务数据库或密钥，没有执行材料中的安装 / 跑数指令。

| 引用 | 来源 | 支持的判断 |
|---|---|---|
| S1 | [overview](skills/overview/SKILL.md) | 定位、四端分工、MCP / CLI 与职责 |
| S2 | [onboarding](skills/onboarding/SKILL.md) | 注册、安装、仓绑定、需求 / 用例关系 |
| S3 | [run-test-cases](skills/run-test-cases/SKILL.md) | 派发、状态、账号 / 资源声明与报告规则 |
| S4 | [repo-config](skills/repo-config/SKILL.md) | 配置、环境、页面、复用、同步 |
| S5 | [write-test-cases](skills/write-test-cases/SKILL.md) | 32 个公共方法、定位、自检、断言与原文要求 |
| S6 | [check-test-cases](skills/check-test-cases/SKILL.md) | 源码自检的范围与限制 |
| S7 | [update-skills](skills/update-skills/SKILL.md) | 技能安装 / 更新入口 |
| S8 | [analyze-test-case](skills/analyze-test-case/SKILL.md) | 工作区新增：固定原文、P/S/E 编号与缺口分析（未计入发布基线） |
| R1 | [Scout script_exec.py][R1]（平台 / 同平台校验 / 运行结果 / 证据 / API） | 五平台、脚本执行、截图生成、断言门禁限制 |
| R2 | [Scout script_repo.py][R2] | Git 拉仓、revision、脚本定位 |
| R3 | [Scout script_check.py][R3] | 自检与跳过语法错误 |
| R4 | [Scout callbacks.py][R4]、[model_call.py][R4m] | OTP、Gmail 方法、文本 / 视觉调用 |
| R5 | [Android executor][R5] | Android 动作与清应用数据 |
| R6 | [iOS WDA executor][R6] | iOS 动作、探活、清数据 / 按键限制 |
| R7 | [Chromium hub][R7] | 实际浏览器渠道 |
| R8 | [desktop driver][R8]、[mac actions][R8m]、[win actions][R8w] | 桌面、权限 / 会话与身份 |
| R9 | [case_sources.py][R9] | CSV / XLSX / 飞书用例来源 |
| R10 | [case_source_api.py][R10] | 专用用例服务来源 |
| R11 | [Scout platform/scout/run.py][R11] | 采样限制与 expect 判断顺序 |
| R12 | [Scout plugins/state.py][R12]、[calls.py][R12c] | 插件种类、配置与外部调用 |
| N1 | [Cloudflare mcp.ts][N1] | 18 个真实注册工具 |
| N2 | [Cloudflare case_runner.ts][N2] | 顺序派发、100 条上限、waitUntil |
| N3 | [Cloudflare script_callback.ts][N3] | 简化事件、截图 / hierarchy 丢弃、号池缺口 |
| N4 | [Cloudflare compat.ts][N4] | HTTP 支持、环境骨架、空列表与 501 缺口 |
| N5 | [Cloudflare mcp_oauth.ts][N5] | MCP 授权实现 |
| N6 | [Cloudflare hub.ts][N6] | 节点出站连接、注册 / 心跳 |
| N7 | [Cloudflare plugin_routes.ts][N7] | 渠道与 CLI 安装目录 |
| N8 | [Cloudflare repo_apps.ts][N8]、[script_repo.ts][N8r] | 仓配置与应用差异同步 |
| N9 | [Cloudflare requirements.ts][N9] | 需求元数据 |
| N10 | [Cloudflare run_store.ts][N10] | 任务状态、300 事件上限、基础统计 |
| N11 | [Cloudflare index.ts][N11] | `/ws` 仅 ping / pong 的提交基线 |
| N12 | [Cloudflare node_control.ts][N12] | 节点配置、运维、插件调用 |
| W1 | [Workbench router][W1]、[TasksPanel][W1t] | 实际页面、规划页 / 重定向及依赖 |

[S1]: skills/overview/SKILL.md
[S2]: skills/onboarding/SKILL.md
[S3]: skills/run-test-cases/SKILL.md
[S4]: skills/repo-config/SKILL.md
[S5]: skills/write-test-cases/SKILL.md
[S6]: skills/check-test-cases/SKILL.md
[S7]: skills/update-skills/SKILL.md
[S8]: skills/analyze-test-case/SKILL.md
[R1]: https://github.com/pengchengluoyi/MinoScout/blob/15d3fed01a5542143906b05d9c4eeff019b2bac3/mino_scout/runtime/script_exec.py
[R2]: https://github.com/pengchengluoyi/MinoScout/blob/15d3fed01a5542143906b05d9c4eeff019b2bac3/mino_scout/runtime/script_repo.py
[R3]: https://github.com/pengchengluoyi/MinoScout/blob/15d3fed01a5542143906b05d9c4eeff019b2bac3/mino_scout/runtime/script_check.py
[R4]: https://github.com/pengchengluoyi/MinoScout/blob/15d3fed01a5542143906b05d9c4eeff019b2bac3/mino_scout/server_comm/callbacks.py
[R4m]: https://github.com/pengchengluoyi/MinoScout/blob/15d3fed01a5542143906b05d9c4eeff019b2bac3/mino_scout/server_comm/model_call.py
[R5]: https://github.com/pengchengluoyi/MinoScout/blob/15d3fed01a5542143906b05d9c4eeff019b2bac3/mino_scout/executors/adb_executor.py
[R6]: https://github.com/pengchengluoyi/MinoScout/blob/15d3fed01a5542143906b05d9c4eeff019b2bac3/mino_scout/executors/wda_executor.py
[R7]: https://github.com/pengchengluoyi/MinoScout/blob/15d3fed01a5542143906b05d9c4eeff019b2bac3/mino_scout/platform/web/playwright_hub.py
[R8]: https://github.com/pengchengluoyi/MinoScout/blob/15d3fed01a5542143906b05d9c4eeff019b2bac3/mino_scout/executors/desktop.py
[R8m]: https://github.com/pengchengluoyi/MinoScout/blob/15d3fed01a5542143906b05d9c4eeff019b2bac3/mino_scout/platform/mac/actions.py
[R8w]: https://github.com/pengchengluoyi/MinoScout/blob/15d3fed01a5542143906b05d9c4eeff019b2bac3/mino_scout/platform/win/actions.py
[R9]: https://github.com/pengchengluoyi/MinoScout/blob/15d3fed01a5542143906b05d9c4eeff019b2bac3/mino_scout/case_sources.py
[R10]: https://github.com/pengchengluoyi/MinoScout/blob/15d3fed01a5542143906b05d9c4eeff019b2bac3/mino_scout/case_source_api.py
[R11]: https://github.com/pengchengluoyi/MinoScout/blob/15d3fed01a5542143906b05d9c4eeff019b2bac3/mino_scout/platform/scout/run.py
[R12]: https://github.com/pengchengluoyi/MinoScout/blob/15d3fed01a5542143906b05d9c4eeff019b2bac3/mino_scout/plugins/state.py
[R12c]: https://github.com/pengchengluoyi/MinoScout/blob/15d3fed01a5542143906b05d9c4eeff019b2bac3/mino_scout/plugins/calls.py
[N1]: https://github.com/pengchengluoyi/MinoNexus/blob/f59e59093bbb4e18947e2dd8ed21cc2bca4803e8/cloudflare/src/mcp.ts
[N2]: https://github.com/pengchengluoyi/MinoNexus/blob/f59e59093bbb4e18947e2dd8ed21cc2bca4803e8/cloudflare/src/case_runner.ts
[N3]: https://github.com/pengchengluoyi/MinoNexus/blob/f59e59093bbb4e18947e2dd8ed21cc2bca4803e8/cloudflare/src/script_callback.ts
[N4]: https://github.com/pengchengluoyi/MinoNexus/blob/f59e59093bbb4e18947e2dd8ed21cc2bca4803e8/cloudflare/src/compat.ts
[N5]: https://github.com/pengchengluoyi/MinoNexus/blob/f59e59093bbb4e18947e2dd8ed21cc2bca4803e8/cloudflare/src/mcp_oauth.ts
[N6]: https://github.com/pengchengluoyi/MinoNexus/blob/f59e59093bbb4e18947e2dd8ed21cc2bca4803e8/cloudflare/src/hub.ts
[N7]: https://github.com/pengchengluoyi/MinoNexus/blob/f59e59093bbb4e18947e2dd8ed21cc2bca4803e8/cloudflare/src/plugin_routes.ts
[N8]: https://github.com/pengchengluoyi/MinoNexus/blob/f59e59093bbb4e18947e2dd8ed21cc2bca4803e8/cloudflare/src/repo_apps.ts
[N8r]: https://github.com/pengchengluoyi/MinoNexus/blob/f59e59093bbb4e18947e2dd8ed21cc2bca4803e8/cloudflare/src/script_repo.ts
[N9]: https://github.com/pengchengluoyi/MinoNexus/blob/f59e59093bbb4e18947e2dd8ed21cc2bca4803e8/cloudflare/src/requirements.ts
[N10]: https://github.com/pengchengluoyi/MinoNexus/blob/f59e59093bbb4e18947e2dd8ed21cc2bca4803e8/cloudflare/src/run_store.ts
[N11]: https://github.com/pengchengluoyi/MinoNexus/blob/f59e59093bbb4e18947e2dd8ed21cc2bca4803e8/cloudflare/src/index.ts
[N12]: https://github.com/pengchengluoyi/MinoNexus/blob/f59e59093bbb4e18947e2dd8ed21cc2bca4803e8/cloudflare/src/node_control.ts
[W1]: https://github.com/pengchengluoyi/MinoWorkbench/blob/29d772b68aef755c44d79c55d3349aa74d5b50b8/src/router/index.tsx
[W1t]: https://github.com/pengchengluoyi/MinoWorkbench/blob/29d772b68aef755c44d79c55d3349aa74d5b50b8/src/domains/testing/tasks/TasksPanel.tsx
