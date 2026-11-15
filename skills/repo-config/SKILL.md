---
name: repo-config
description: 在已绑定的脚本仓里组织目录、写 config.yaml / pages，并用 mino-scout check + MCP repo_apps_sync 完成应用配置。用户说加安卓/iOS/Web、配包名或环境、改脚本仓配置时使用。项目尚未绑定脚本仓时先用 onboarding 门禁 4，不要本技能里新建远程仓。
---

# 脚本仓库配置

脚本仓是项目的 Git 仓库（地址在 `project_list` 的 `repo_url`）。执行时 **Scout 用本机 git 拉取**；Nexus 只记地址 / 分支 / 提交与应用清单，不经手文件内容。

**边界**

| 事 | 谁做 |
|---|---|
| 编辑 `config.yaml` / `pages/` / `tests/`、commit、push | 你在本机 Git 工作副本 |
| `mino-scout check .` | 本机 CLI（改完必跑） |
| `project_script_repo_set`、`repo_apps_sync` / `get` | MCP |
| 新建远程空仓 | **仅当用户明确要求**；否则只使用用户给出的已有 URL |

脚本仓认应用 **key**；`project_id` / `app_id` 是 Nexus 身份，**不要写进 `config.yaml`**。

项目还不存在或 `repo_url` 为空：回到 `onboarding` 门禁 4，**先绑仓再改本技能内容**。

## 0. 新增 / 修改应用：先问齐再写（必做）

用户说「加应用 / 配包名 / 配环境」时：

1. 先用一两句话说明：将问清项目与身份字段 → 改仓 → `check` → push → sync。  
2. **不要**只调 `app_create` 就说完成（那只是空壳）。  
3. **不要**为了「有个地方写 config」而新建 GitHub 仓。

缺信息就问清，**不要猜、不要用示例包名顶替**：

| 要问清的 | 说明 |
|---|---|
| 哪个项目 | `project_list`；无项目用 `project_create`；无 `repo_url` → `project_script_repo_set`，不要自建远程仓 |
| 本地检出 | 必须是该 `repo_url` 的 clone / 已有工作副本 |
| 哪些平台 | 一平台一条应用（一个 key、一个 `platform`）。「安卓 + iOS」= 两条 |
| 环境名 | 与项目一致（如 `test` / `pre` / `prod`）；不知就问 |
| 各环境身份 | Android `package`；iOS `bundle_id`；Web `url`。不同则用 `envs` |
| 登录 / 接码策略 | 不写脚本仓；在 Nexus `resource_env_set` 中配置 |

收集齐并复述确认后：

1. 改 `config.yaml` 的 `apps`（key 合法、**不写** `app_id` / `project_id`）；  
2. 建或保留 `pages/<KEY>/`；  
3. 仓根：`mino-scout check .`，改到无提示；  
4. push；  
5. §3 `repo_apps_sync`（只传 platform / package / bundle_id / url / envs，**不要 otp**）；  
6. `repo_apps_get` 确认后，才可说「应用已加好」。

`app_create` 可选，**不能替代**上述闭环。误建空壳后仍按 key sync 对齐即可。

## 1. 目录构成

| 路径 | 放什么 | 判断标准 |
|---|---|---|
| `config.yaml` | 被测应用清单：key、平台、各环境的包名 / bundle id / URL | 只放应用身份，不放账号、验证码策略或自动新增配置 |
| `pages/<APP_KEY>/<page_key>.yaml` | 某个应用的页面：状态锚点、控件、各渠道 locator | 只描述“页面是什么”，不含动作；一个应用一个子目录 |
| `tests/<需求ID>/<case_id>.py` | 用例，`def run(case)` | 一条用例一个文件；不写平台后缀 |
| `tests/<需求ID>/<case_id>.yaml` | 该用例原文快照：source、preconditions、steps、expectations，可选 account_requirements | 新转换用例必须固定版本；格式见 analyze-test-case，运行时按 source_ref 留证 |
| `flows/<name>.py` | 业务流程：登录、进入某页、下单；多个用例复用 | 函数接收 `app`，编排设备动作 |
| `scripts/<name>.py` | 纯逻辑：数据处理、格式转换、计算 | 入参出参是普通数据，不碰设备 |
| `pretest.py` / `posttest.py` | 项目级前后置钩子 | 可选 |

写之前先找现成的，**不要重复造轮子**：Scout / Nexus 提供的方法 → `pages` 里的控件 → 已有 `flows` → 新写 `flows` → 纯逻辑才写 `scripts`。引用写 `from flows.login import login`。登录**动作**写在 `flows/`；账号仍从号池租。

## 2. config.yaml

放仓库根目录。顶层只有 `apps`，每个应用一项。**key 用英文字母开头的英文、数字、下划线**（`baidu_android`、`baidu_web` 都行），这个 key 同时是脚本里 `case.config.<KEY>` 的名字（所以要是合法的 Python 变量名）和 `pages/<KEY>/` 的目录名。

每个应用**必须有 `platform`**。**不要写 `app_id` / `project_id`**：同步时 Nexus 按 key 对齐或自动创建应用，并把映射留在 Nexus 清单里。

应用在不同环境的身份不同（测试包名、测试域名）时用 `envs` 分环境；环境名与 Nexus 项目里的环境名一致（如 `test`、`prod`）：

```yaml
apps:
  baidu_android:
    platform: android
    envs:
      test: {package: com.example.baidu.test}
      prod: {package: com.example.baidu}
  baidu_web:
    platform: web
    envs:
      test: {url: https://test.example.com}
      prod: {url: https://example.com}
  baidu_ios:                 # 各环境身份相同，可以不写 envs
    platform: ios
    bundle_id: com.example.baidu
```

各平台身份字段：

| platform | 字段 | 说明 |
|---|---|---|
| `android` | `package` | 包名 |
| `ios` | `bundle_id` | bundle id |
| `web` | `url` | `launch()` 打开的地址 |
| `mac` | `bundle_id` | bundle id |
| `win` | `package` | EXE 路径或 AUMID |

### 登录、验证码与自动补号由 Nexus 下发

不要在脚本仓写登录方式、验证码策略、Gmail 收件箱、手机号/Gmail 别名起始序号或“是否自动补号”。这些属于 **Nexus 项目环境配置**，由 `resource_env_get` / `resource_env_set` 读取和维护：

- `login_policies[].secrets.<env>.login.kind` 决定手机号或邮箱登录；
- `login_policies[].secrets.<env>.otp` 决定 fixed / Gmail / hitl / auto；
- `gmail_inbox.address` 提供 Gmail 收件箱；
- `login_policies[].phone_seq` / `gmail_alias` 提供自动新增账号的起始与下一次序号。

号池没有可用且匹配登录身份的账号时，Nexus 自动新增账号，不让脚本仓控制这个开关。脚本只调用 `case.nexus.account()` 租号、`case.scout.otp(account)` 取码，不读仓库密码或接码配置。

`otp.code` 只作为旧仓库兼容兜底，不属于新项目配置方式；新项目和新增应用不要再写。

规则：

- 值从用户给的信息、用例前置条件或已有 `config.yaml` 里取；**拿不到包名 / URL / 环境就问用户，不要猜**（问法见 §0）；
- 已有应用的 key 不要改，改了会让 `pages/` 目录和已有用例对不上；
- 不放账号、密码、token、登录方式或验证码策略（账号由 Nexus 号池租用，策略由 Nexus 项目环境配置下发）；
- 新增应用 = 先按 §0 问齐 → `config.yaml` + `pages/<KEY>/` → `mino-scout check .` → push → `repo_apps_sync`；**仅 `app_create` 不算完成**；  
- **禁止**在用户未明确要求时创建远程 Git 仓库；
- 应用的 `platform` 必须等于本次运行的设备平台；一条应用只对应一个 platform；
- 本次运行的环境由 Nexus 决定，脚本里是 `case.env`，一般不需要判断；`config.yaml` 里声明的环境名必须能对上项目里已有环境；
- 这是应用 key、平台和包名 / bundle id / URL 的唯一真源；Workbench 里的包名 / URL 只读展示，要改就改这个文件并 push，再按下面的约定同步给 Nexus。

## 3. 改了 config.yaml 必须同步给 Nexus

Nexus 不读脚本仓库（仓库可能是私有的），它只能靠你告诉它“这个项目的仓库能跑哪些应用”，Workbench 的“脚本仓库应用”和选应用都依赖这份同步。所以**只要新增、删除或修改了 `config.yaml` 里的应用或环境**，在 push 之后：

1. 取 push 后的提交：`git rev-parse HEAD`；
2. 调 MCP 工具 `repo_apps_sync(project_id, revision=<sha>, branch=<分支>, apps=<本次新增或修改的应用>, remove=<本次删除的应用 key>)`。这是差异更新：只传变化的应用（取自 `config.yaml` 的 **platform / package / bundle_id / url / envs**，**去掉 `otp`**，不要自己编 `app_id`），没传的应用保持不变；删除应用要显式放进 `remove`；
3. 调 `repo_apps_get(project_id)` 确认同步成功，`revision` 与刚 push 的一致，并记下 Nexus 回填的 `app_id`（跑数、选设备用）。

规则：

- 先 push 再同步，同步的 `revision` 必须是已 push 的提交；
- 未带 `app_id` 时 Nexus 按 key 对齐项目里已有同名应用，或自动创建；
- 同步被拒绝（key 命名、platform、字段不合法、误传 otp）就按报错改，改好重新 push 再同步；
- 只改了脚本、没动应用身份字段，不需要同步；
- 新项目第一次写好 `config.yaml` 后也要同步一次。

## 4. 页面文件

`pages/<APP_KEY>/<page_key>.yaml`，目录名必须等于 `config.yaml` 里的 key；直接放在 `pages/` 下不行。字段参照仓库里已有的页面文件：`page_key`、`states[].anchors`、`controls[].id` / `label` / `locator_spec`。

`locator_spec` 按渠道分格：

| 渠道 | 格名 |
|---|---|
| android | `uiautomator` |
| ios | `xcuitest` |
| web | `playwright` |
| mac | `ax` |
| win | `uia` |

每格 `selector` 里有 `kind` 和 `value` / `name`。`value` 必须是设备界面节点上的原文（`resource_id`、`text` 或 `content_desc`），不能用用例正文或 `label` 编一个能解析的选择器。还没有节点时，这一格先不写。`on_page` 用 `states[].anchors` 与界面文字比对，**一组锚点全部出现**才算在这一页；锚点也必须是这一屏真实出现过的文字。同一控件要在多个渠道用，就在 `locator_spec` 里写多格，不要在脚本里按平台分支。
