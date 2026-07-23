# zqq-zentao-cli

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

**中文** | [English](./README.en.md)

禅道（ZenTao）双通道命令行工具：支持 **Web（PATHINFO + Cookie）** 与 **REST Token（APIv1 默认 / APIv2 可选只读）**。

- Python ≥ 3.10，无第三方依赖
- 命令入口 **`zqq-zentao`**（勿与官方 npm `zentao` 混淆）
- 契约 / 交接 / 通道矩阵见下方 [文档](#文档)

## 目标与定位

**目标**：在账号权限内，用命令行全面操作禅道——查任何人/对象、`my-*` 快捷入口、CRUD/状态流转与备注（分期见契约）。

| | 本工具 `zqq-zentao` | 官方 [zentao-cli](https://github.com/easysoft/zentao-cli) `zentao` |
|--|---------------------|---------------|
| 实现 | Python，无第三方依赖 | Node/npm |
| 通道 | Web Cookie + REST Token | 主要为 REST |
| 能力面 | 自建完整目标面（含 Web 补洞）；分期见契约 | 贴近官方 REST CRUD |
| 配置 | 共用 `~/.config/zentao/zentao.json`，另存 `webCookies` | 同文件，忽略 `webCookies` |

**为何双通道？** 不是官方 CLI「写坏了」，而是禅道 **REST 能力面本身有缺口**（尤其 APIv1）：例如无全局 my-bugs/my-stories、备注更适合 Web、部分过滤语义怪异（`status` 实为 browseType）、查他人 Bug 无任意账号过滤、users 等无稳定 search。官方 CLI 主要吃 REST，这些缺口会原样暴露。本工具策略是：**REST 能稳定表达则用 REST；不能则用 Web；必要时客户端过滤/搜索兜底**。场景对照见 [docs/channel-matrix.md](./docs/channel-matrix.md)。

关于 REST 版本与「搜索」：

- 默认 **REST v1**（写始终 v1）；`--api v2` 为**可选只读**（v2 常 redirect 到 Web 再抽 JSON，search 常依赖 Session，分页也有坑）
- 「不能搜索」并不绝对：v1 按模块能力不一（如 tasks 有 `search=1`，users 无）；本工具对关键词多用客户端扫描或有限 REST 映射

## 架构与通道选择

```text
zqq-zentao
  → cli_app（参数 / 分发 / 表驱动写）
  → capability + capabilities（本命令允许 web / rest）
  → factory（建 RestClient 或 WebClient；auto 双能力时可失败降级）
  → services → rest/* 或 web/*
```

| 层 | 职责 |
|----|------|
| `cli_app` | 命令面、写操作分发 |
| `capabilities` | 能力 → 允许的后端 |
| `factory` | 选通道建客户端；`auto` 时一侧失败可试另一侧 |
| `rest/` | Token + `/api.php/v1`（读可选 v2） |
| `web/` | Cookie + PATHINFO（`my-*`、备注等） |
| `services/` | 过滤、确认、业务编排 |

通道选择是**规则驱动**，不是每次请求现场「算最优」：

1. 能力仅 web / 仅 rest → **强制**对应通道  
2. `auto`（默认）且双通道 → **有 Token 偏 REST，否则偏 Web**  
3. `--backend` / `ZENTAO_BACKEND` 可显式覆盖  
4. `auto` + 双能力时，首选失败（登录/超时等）可降级到另一侧（stderr 有 warn）

## 文档

| 文档 | 说明 |
|------|------|
| [docs/cli-surface.md](./docs/cli-surface.md) | 命令面契约（`my-*` / 过滤 / CRUD 分期 / ✅⏳） |
| [docs/handoff.md](./docs/handoff.md) | 交接：未完成待办、已知坑、建议下一刀 |
| [docs/channel-matrix.md](./docs/channel-matrix.md) | REST vs Web 场景矩阵与挖缺口方法 |
| [docs/zentao-web-pathinfo.md](./docs/zentao-web-pathinfo.md) | Web PATHINFO（我的地盘 / 备注等） |
| [docs/zentao-rest-apiv1.md](./docs/zentao-rest-apiv1.md) | REST API v1（22.3 源码整理；默认读/写） |
| [docs/zentao-rest-apiv2.md](./docs/zentao-rest-apiv2.md) | REST API v2 路由全文（`--api v2` 可选只读；写仍 v1） |

## 安装

```bash
pip install -e .
zqq-zentao -h
```

安装后命令为 **`zqq-zentao`**（包名 `zqq-zentao-cli`），不占用官方 `zentao`。

## 配置与登录

推荐与官方 CLI 一样显式登录（凭证写入 `~/.config/zentao/zentao.json`，**不存密码**）：

```bash
zqq-zentao login -s https://zentao.example.com -u your_account -p your_password
```

| 参数 | 说明 | 环境变量回退 |
|------|------|----------------|
| `-s` / `--server` | 禅道地址（无尾斜杠） | `ZENTAO_URL`（推荐）或 `ZENTAO_SERVER` |
| `-u` / `--account` | 账号 | `ZENTAO_ACCOUNT` |
| `-p` / `--password` | 密码 | `ZENTAO_PASSWORD` |

登录成功后写入当前 profile：

- `webCookies`：Web 会话 Cookie（本工具字段；官方 CLI 会忽略）
- `token`：REST Token（与官方字段一致）

也可仅用环境变量；未登录时业务命令会提示执行 `zqq-zentao login`。

| 变量 | 说明 | 官方 zentao-cli |
|------|------|-----------------|
| `ZENTAO_URL` | 禅道地址（推荐，与官方一致） | ✅ |
| `ZENTAO_SERVER` | 同上，本工具别名 | ❌ |
| `ZENTAO_ACCOUNT` | 账号 | ✅ |
| `ZENTAO_PASSWORD` | 密码（不落盘；`login` 或缺 Cookie/Token 时需要） | ✅ |
| `ZENTAO_TOKEN` | REST Token（有则优先于文件内 token） | ✅ |
| `ZENTAO_BACKEND` | `web` \| `rest` \| `auto`（默认 `auto`） | — |
| `ZENTAO_API` | REST 读版本 `v1` \| `v2`（默认 `v1`；写始终 v1） | — |
| `ZENTAO_INSECURE` | 默认 `1` 跳过 TLS 校验；设为 `0` 则校验 | —（官方用 `--insecure`） |
| `ZENTAO_CONFIG_FILE` | 自定义配置文件路径 | ✅ |

### 全局选项（对齐官方 zentao-cli）

| 选项 | 说明 |
|------|------|
| `-V` / `--version-flag` | 显示版本号 |
| `--format <markdown\|json\|raw>` | 输出格式；默认 `markdown`（列表为表格，对象为键值列表）；`json` 包装为 `{status,data}`；`raw` 为原始 JSON |
| `--silent` | 静默模式（不打印结果） |
| `--insecure` / `--secure` | 跳过 / 强制 TLS 证书校验 |
| `--timeout <ms>` | 请求超时（毫秒，默认 60000） |
| `--config <file>` | 自定义配置文件（亦可用 `ZENTAO_CONFIG_FILE`） |
| `--machine-readable` | 机器可读：紧凑 JSON、禁用颜色 |
| `--pick <fields>` | 表格输出字段（逗号分隔；覆盖默认列） |
| `--backend <web\|rest\|auto>` | 传输通道（默认 `ZENTAO_BACKEND` / auto） |
| `--api <v1\|v2>` | REST **读**版本（默认 `ZENTAO_API` / v1；写始终 v1） |
| `-h` / `--help` | 显示帮助 |

```bash
zqq-zentao -V
zqq-zentao --format json whoami
zqq-zentao --format raw --machine-readable task 39980
zqq-zentao --timeout 10000 --insecure my-tasks
zqq-zentao --config ./zentao.json whoami
zqq-zentao --pick id,name,code projects --search FM270
zqq-zentao --api v2 projects --search FM270
```

TLS 跳过证书校验（自签 / 内网 HTTPS 常用）：

```bash
# 全局选项（与官方 zentao --insecure 同义）；也可不写——默认已跳过校验
zqq-zentao --insecure login -s https://zentao.example.com -u your_account -p your_password
zqq-zentao --insecure task 39980

# 强制校验证书
zqq-zentao --secure whoami
# 或
# $env:ZENTAO_INSECURE = "0"
```

优先级：`--insecure` / `--secure` > `ZENTAO_INSECURE`（默认跳过）。

与官方 CLI **共用同一套变量**时请用 `ZENTAO_URL`，不要只设 `ZENTAO_SERVER`。

PowerShell 示例：

```powershell
$env:ZENTAO_URL = "https://zentao.example.com"
$env:ZENTAO_ACCOUNT = "your_account"
$env:ZENTAO_PASSWORD = "your_password"
zqq-zentao login
```

鉴权行为简述：

- **Web**：优先用缓存 `webCookies`；失效且有 `ZENTAO_PASSWORD` 时自动重登并写回；否则提示 `zqq-zentao login`
- **REST**：`ZENTAO_TOKEN` → 配置文件 `token` → 密码换票

**不要**在日志或对话中打印 Cookie、密码、Token。

## 用法

```bash
zqq-zentao login -s https://zentao.example.com -u admin -p secret
zqq-zentao whoami
zqq-zentao my-tasks
zqq-zentao my-bugs --type resolvedBy
zqq-zentao my-stories
zqq-zentao my-todos --type today
zqq-zentao tasks
zqq-zentao tasks --assignedTo alice
zqq-zentao tasks --assignedTo 张三 --status wait,doing
zqq-zentao tasks --execution 100 --openedBy bob
zqq-zentao bugs --product 12 --assignedTo alice --status active
zqq-zentao stories --project 5 --openedBy bob
zqq-zentao --pick id,status,title bugs --product 12
zqq-zentao users --search 张
zqq-zentao task 39980
zqq-zentao projects --limit 5
zqq-zentao projects --program 1
zqq-zentao executions --limit 5
zqq-zentao execution 100
zqq-zentao users --limit 5
zqq-zentao user admin
zqq-zentao programs
zqq-zentao program 1
zqq-zentao products --limit 5
zqq-zentao product 12
zqq-zentao stories --product 12
zqq-zentao story 100
zqq-zentao story create --product 12 --title "need login" --spec "as a user I can log in" --yes
zqq-zentao story change 100 --title "need SSO login" --spec "…" --yes
zqq-zentao story close 100 --closedReason done --yes
zqq-zentao bugs --product 12
zqq-zentao bug 200
zqq-zentao bug resolve 200 --resolution fixed --yes
zqq-zentao task start 39980 --yes
zqq-zentao task create --execution 100 --name "demo" --type devel --assignedTo alice --estStarted 2026-01-01 --deadline 2026-01-02 --yes
zqq-zentao todo create --name "buy milk" --yes
zqq-zentao todo finish 9 --yes
zqq-zentao testcase create --product 12 --title "login" --data '{"steps":[{"desc":"open","expect":"ok"}]}' --yes
zqq-zentao testsuite create --product 12 --name "smoke" --yes
zqq-zentao ping
zqq-zentao departments
zqq-zentao comment list task 39973
zqq-zentao comment add task 39973 "备注内容"
zqq-zentao comment edit 1063694 "新备注"
```

| 命令 | 说明 | 后端 |
|------|------|------|
| `login` | 登录并缓存 Cookie / Token | web + rest（`auto`） |
| `whoami` | 当前账号与服务器 | web / rest |
| `my-tasks` | 我的任务；`--type` / `--scope`（默认指派给我） | web / rest（仅默认） |
| `my-bugs` / `my-stories` / `my-requirements` / `my-epics` / `my-todos` / `my-testcases` / `my-testtasks` / `my-feedbacks` / `my-tickets` / `my-docs` / `my-projects` / `my-executions` | 我的地盘列表（Web；可 `--type`） | **仅 web** |
| `tasks` | REST 任务列表；可 `--assignedTo`（查别人） | **仅 rest** |
| `tasks -e <id>` | 某执行下的任务；可 `--assignedTo` / `--openedBy` | web / rest |
| `task <id>` / `task <action> <id>` | 任务详情；写/动作（create/update/delete/start/finish/close/activate/assign，REST） | 详情 web/rest；写 **rest** |
| `bug <id>` / `bug <action> <id>` | Bug 详情；写/动作（create/update/delete/confirm/resolve/close/activate/assign，REST） | **rest** |
| `story <id>` / `story <action> <id>` | 需求详情；写/动作（create/update/delete/change/close/activate/assign/review/submitreview/recall，REST） | **rest** |
| `todo <id>` / `todo <action> <id>` | 待办详情；写/动作（create/update/delete/finish/activate，REST；finish/activate 为 GET） | **rest** |
| `testcase <id>` / `testcase <action> <id>` | 用例详情；写（create/update/delete/results，REST；steps 用 `--data`） | **rest** |
| `testsuite <id>` / `testsuite create\|delete` | 套件详情；create/delete（APIv1 无 PUT） | **rest** |
| `testtask <id>` / `testtask create\|delete` | 测试单详情；create（需 project+product+execution+build）/delete | **rest** |
| `users` / `user <account>` | 用户列表（可 `--search`）/ 详情 | **仅 rest** |
| `projects` | 项目列表（可选 `--program` / `--product`） | **仅 rest** |
| `project <id>` | 项目详情 | **仅 rest** |
| `programs` / `program <id>` | 项目集列表 / 详情 | **仅 rest** |
| `products` / `product <id>` | 产品列表 / 详情（列表可选 `--program`） | **仅 rest** |
| `executions` / `execution <id>` | 执行列表 / 详情 | **仅 rest** |
| `departments` / `department <id>` | 部门列表 / 详情 | **仅 rest** |
| `stories` / `story` | 需求列表 / 详情与写（列表需 scope；可 `--assignedTo` / `--openedBy`） | **仅 rest** |
| `bugs` / `bug` | Bug 列表 / 详情与写（列表需 scope；可 `--assignedTo` / `--openedBy`） | **仅 rest** |
| `productplans` / `releases` / `builds` 等 | 计划/发布/版本/测试/反馈/工单/待办/问题/风险/会议/文档等只读 | **仅 rest** |
| `ping` / `groups` / `configurations` 等 | 系统只读 | **仅 rest** |
| `comment list/add/edit` | 备注增改查 | **仅 web** |

REST 只读模块由 [`src/rest/resources.py`](./src/rest/resources.py) 注册表驱动。目标命令面与接口对照见上方 [文档](#文档)。`zqq-zentao -h` 可查看当前已实现子命令。

`--backend` 可覆盖 `ZENTAO_BACKEND`。`auto`：有 Token（环境变量或配置文件）偏向 rest，否则 web；仅 rest / 仅 web 的命令会强制对应通道。`login` 在 `auto` 下会同时完成 Web 与 REST 换票。

## 目录结构

```
.
├── pyproject.toml          # 包元数据；入口 zqq-zentao → zqq_zentao_cli.cli:main
├── README.md / README.en.md
├── LICENSE
├── docs/                   # 契约 / 交接 / 通道矩阵 / 接口对照（见「文档」）
├── tests/                  # 离线 pytest（不打真实禅道写）
└── src/                    # 安装后包名 zqq_zentao_cli
    ├── cli.py              # 控制台入口（转发 cli_app）
    ├── config.py           # 配置 / 环境变量 / profile
    ├── capabilities.py     # 能力 → 允许的 web|rest
    ├── factory.py          # 建客户端；auto 双通道降级
    ├── protocol.py         # ZenTaoClient 协议
    ├── user_resolve.py     # 实名→账号；用户表短缓存
    ├── list_filter.py      # 客户端过滤 / --search 文本匹配
    ├── *_shape.py          # 列表行摘要（task/bug/my…）
    ├── confirm_util.py / payload.py / output.py
    ├── cli_app/            # 参数、分发、表驱动写
    │   ├── parser.py / dispatch.py / capability.py
    │   └── write_dispatch.py / fields.py / body.py
    ├── rest/               # Token + /api.php/v1（读可选 v2）
    │   ├── client.py / session.py / resources.py / resources_v2.py
    │   ├── tasks.py / browse_filter.py / writes.py / v2_search.py
    ├── web/                # Cookie + PATHINFO
    │   ├── client.py / session.py / my_pages.py / lists.py
    │   └── comments.py / tasks.py / bugs.py / parse.py
    └── services/           # 业务编排（auth / my_pages / resources / bugs|tasks|stories / comments）
```

## 许可证

本项目采用 [MIT License](./LICENSE) 授权。Copyright (c) 2026 zhengqingquan。
