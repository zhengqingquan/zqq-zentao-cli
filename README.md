# zqq-zentao-cli

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

**中文** | [English](./README.en.md)

禅道（ZenTao）双通道命令行工具：支持 **Web（PATHINFO + Cookie）** 与 **REST（Token）**。

- Python ≥ 3.10，无第三方依赖
- Web 可读写备注；REST 适合任务只读等结构化接口
- 与官方 [zentao-cli](https://github.com/easysoft/zentao-cli) 共用环境变量与 `~/.config/zentao/zentao.json`（本工具另存 `webCookies`）
- Web PATHINFO 接口说明见 [docs/zentao-apis.md](./docs/zentao-apis.md)
- REST API v1（22.3 源码整理）见 [docs/zentao-rest-apis.md](./docs/zentao-rest-apis.md)

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
| `-h` / `--help` | 显示帮助 |

```bash
zqq-zentao -V
zqq-zentao --format json whoami
zqq-zentao --format raw --machine-readable task 39980
zqq-zentao --timeout 10000 --insecure my-tasks
zqq-zentao --config ./zentao.json whoami
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
zqq-zentao my-bugs
zqq-zentao tasks
zqq-zentao tasks --execution 1664
zqq-zentao task 39980
zqq-zentao projects --limit 5
zqq-zentao projects --program 1
zqq-zentao executions --limit 5
zqq-zentao execution 1664
zqq-zentao users --limit 5
zqq-zentao user admin
zqq-zentao programs
zqq-zentao program 1
zqq-zentao products --limit 5
zqq-zentao product 12
zqq-zentao stories --product 12
zqq-zentao story 100
zqq-zentao bugs --product 12
zqq-zentao bug 200
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
| `my-tasks` | 指派给我的任务（REST 用 `/tasks` 过滤指派人） | web / rest |
| `my-bugs` | 指派给我的 Bug（Web：`/my-work-bug-assignedTo.html`） | **仅 web** |
| `tasks` | REST 任务列表（`--page` / `--limit`） | **仅 rest** |
| `tasks -e <id>` | 某执行下的任务列表 | web / rest |
| `task <id>` | 任务详情（REST 返回完整字段） | web / rest |
| `users` / `user <account>` | 用户列表 / 详情 | **仅 rest** |
| `projects` | 项目列表（可选 `--program` / `--product`） | **仅 rest** |
| `project <id>` | 项目详情 | **仅 rest** |
| `programs` / `program <id>` | 项目集列表 / 详情 | **仅 rest** |
| `products` / `product <id>` | 产品列表 / 详情（列表可选 `--program`） | **仅 rest** |
| `executions` / `execution <id>` | 执行列表 / 详情 | **仅 rest** |
| `departments` / `department <id>` | 部门列表 / 详情 | **仅 rest** |
| `stories` / `story` | 需求列表 / 详情（列表需 `--product`/`--project`/`--execution`） | **仅 rest** |
| `bugs` / `bug` | Bug 列表 / 详情（同上 scopes） | **仅 rest** |
| `productplans` / `releases` / `builds` 等 | 计划/发布/版本/测试/反馈/工单/待办/问题/风险/会议/文档等只读 | **仅 rest** |
| `ping` / `groups` / `configurations` 等 | 系统只读 | **仅 rest** |
| `comment list/add/edit` | 备注增改查 | **仅 web** |

REST 只读模块由 [`src/rest/resources.py`](./src/rest/resources.py) 注册表驱动；完整路径对照见 [docs/zentao-rest-apis.md](./docs/zentao-rest-apis.md)。`zqq-zentao -h` 可查看全部子命令。

`--backend` 可覆盖 `ZENTAO_BACKEND`。`auto`：有 Token（环境变量或配置文件）偏向 rest，否则 web；仅 rest / 仅 web 的命令会强制对应通道。`login` 在 `auto` 下会同时完成 Web 与 REST 换票。

## 目录结构

```
src/                 # 安装后映射为包 zqq_zentao_cli，入口命令：zqq-zentao
  cli.py
  config.py
  factory.py
  capabilities.py
  protocol.py
  web/               # Cookie + PATHINFO
  rest/              # Token + /api.php/v1（含 resources.py 只读注册表）
  services/
docs/
  zentao-apis.md      # Web PATHINFO 接口说明
  zentao-rest-apis.md # REST API v1（22.3 源码整理）
LICENSE              # MIT
```

## 许可证

本项目采用 [MIT License](./LICENSE) 授权。Copyright (c) 2026 zhengqingquan。
