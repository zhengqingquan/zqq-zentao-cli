# zqq-zentao-cli

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

**中文** | [English](./README.en.md)

禅道（ZenTao）双通道命令行工具：支持 **Web（PATHINFO + Cookie）** 与 **REST（Token）**。

- Python ≥ 3.10，无第三方依赖
- Web 可读写备注；REST 适合任务只读等结构化接口
- 与官方 [zentao-cli](https://github.com/easysoft/zentao-cli) 共用环境变量与 `~/.config/zentao/zentao.json`（本工具另存 `webCookies`）
- Web PATHINFO 接口说明见 [docs/zentao-apis.md](./docs/zentao-apis.md)

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
| `ZENTAO_INSECURE` | 默认 `1` 跳过 TLS 校验；设为 `0` 则校验 | — |

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
zqq-zentao tasks
zqq-zentao tasks --execution 1664
zqq-zentao task 39980
zqq-zentao projects --limit 5
zqq-zentao executions --limit 5
zqq-zentao execution 1664
zqq-zentao users --limit 5
zqq-zentao user admin
zqq-zentao programs
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
| `tasks` | REST 任务列表（`--page` / `--limit`） | **仅 rest** |
| `tasks -e <id>` | 某执行下的任务列表 | web / rest |
| `task <id>` | 任务详情（REST 返回完整字段） | web / rest |
| `users` / `user <account>` | 用户列表 / 详情 | **仅 rest** |
| `projects` | 项目列表 | **仅 rest** |
| `programs` | 项目集列表 | **仅 rest** |
| `executions` / `execution <id>` | 执行列表 / 详情 | **仅 rest** |
| `departments` | 部门列表 | **仅 rest** |
| `comment list/add/edit` | 备注增改查 | **仅 web** |

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
  rest/              # Token + /api.php/v1
  services/
docs/
  zentao-apis.md     # Web 接口说明
LICENSE              # MIT
```

## 许可证

本项目采用 [MIT License](./LICENSE) 授权。Copyright (c) 2026 zhengqingquan。
