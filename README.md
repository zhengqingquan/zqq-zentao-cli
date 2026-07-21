# zqq-zentao-cli

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

中文 | [English](#english)

禅道（ZenTao）双通道命令行工具：支持 **Web（PATHINFO + Cookie）** 与 **REST（Token）**。

- Python ≥ 3.10，无第三方依赖
- Web 可读写备注；REST 适合任务只读等结构化接口
- Web PATHINFO 接口说明见 [zentao-har-apis.md](./zentao-har-apis.md)

## 安装

```bash
pip install -e .
```

安装后可直接使用 `zentao` 命令；也可不安装，用仓库入口：

```bash
python zentao.py -h
```

## 配置

| 变量 | 说明 |
|------|------|
| `ZENTAO_SERVER` 或 `ZENTAO_URL` | 禅道地址（无尾斜杠） |
| `ZENTAO_ACCOUNT` | 账号 |
| `ZENTAO_PASSWORD` | 密码（不落盘；Web 必填，REST 无 Token 时用于换票） |
| `ZENTAO_TOKEN` | REST Token（有则优先 REST） |
| `ZENTAO_BACKEND` | `web` \| `rest` \| `auto`（默认 `auto`） |
| `ZENTAO_INSECURE` | 默认 `1` 跳过 TLS 校验；设为 `0` 则校验 |

也可回退读取 `~/.config/zentao/zentao.json` 中的 profile（仅 server/account）。

PowerShell 示例：

```powershell
$env:ZENTAO_SERVER = "https://zentao.example.com"
$env:ZENTAO_ACCOUNT = "your_account"
$env:ZENTAO_PASSWORD = "your_password"
```

**不要**在日志或对话中打印 Cookie、密码、Token。

## 用法

```bash
zentao whoami
zentao --backend rest whoami
zentao my-tasks
zentao tasks --execution 1664
zentao task 39973
zentao comment list task 39973
zentao comment add task 39973 "备注内容"
zentao comment edit 1063694 "新备注"
```

| 命令 | 说明 | 后端 |
|------|------|------|
| `whoami` | 当前账号与服务器 | web / rest |
| `my-tasks` | 指派给我的任务 | web / rest |
| `tasks -e <id>` | 某执行下的任务列表 | web / rest |
| `task <id>` | 任务详情（JSON） | web / rest |
| `comment list/add/edit` | 备注增改查 | **仅 web** |

`--backend` 可覆盖 `ZENTAO_BACKEND`。`auto`：有 `ZENTAO_TOKEN` 偏向 rest，否则 web；备注类命令强制 web。

## 目录结构

```
zentao.py          # 入口
src/
  cli.py           # 命令行
  config.py        # 配置
  factory.py       # 按 backend 创建客户端
  web/             # Cookie + PATHINFO
  rest/            # Token + /api.php/v1
  services/        # 领域操作
zentao-har-apis.md # Web 接口说明
LICENSE            # MIT
```

## 许可证

本项目采用 [MIT License](./LICENSE) 授权。Copyright (c) 2026 zhengqingquan。

---

<a id="english"></a>

# English

ZenTao dual-backend CLI: **Web (PATHINFO + Cookie)** and **REST (Token)**.

- Python ≥ 3.10, no third-party dependencies
- Web supports comment read/write; REST fits structured task reads
- Web PATHINFO API notes: [zentao-har-apis.md](./zentao-har-apis.md)

## Install

```bash
pip install -e .
```

After install, use the `zentao` command. Or run without installing:

```bash
python zentao.py -h
```

## Configuration

| Variable | Description |
|----------|-------------|
| `ZENTAO_SERVER` or `ZENTAO_URL` | ZenTao base URL (no trailing slash) |
| `ZENTAO_ACCOUNT` | Account |
| `ZENTAO_PASSWORD` | Password (not stored on disk; required for Web; used for REST token exchange if no token) |
| `ZENTAO_TOKEN` | REST Token (prefers REST when set) |
| `ZENTAO_BACKEND` | `web` \| `rest` \| `auto` (default `auto`) |
| `ZENTAO_INSECURE` | Default `1` skips TLS verify; set `0` to verify |

Falls back to `~/.config/zentao/zentao.json` profile (server/account only).

PowerShell example:

```powershell
$env:ZENTAO_SERVER = "https://zentao.example.com"
$env:ZENTAO_ACCOUNT = "your_account"
$env:ZENTAO_PASSWORD = "your_password"
```

**Never** print Cookie, password, or Token in logs or chat.

## Usage

```bash
zentao whoami
zentao --backend rest whoami
zentao my-tasks
zentao tasks --execution 1664
zentao task 39973
zentao comment list task 39973
zentao comment add task 39973 "comment text"
zentao comment edit 1063694 "updated comment"
```

| Command | Description | Backend |
|---------|-------------|---------|
| `whoami` | Current account and server | web / rest |
| `my-tasks` | Tasks assigned to me | web / rest |
| `tasks -e <id>` | Tasks under an execution | web / rest |
| `task <id>` | Task detail (JSON) | web / rest |
| `comment list/add/edit` | Comment CRUD | **web only** |

`--backend` overrides `ZENTAO_BACKEND`. For `auto`: prefer rest when `ZENTAO_TOKEN` is set, otherwise web; comment commands always use web.

## Layout

```
zentao.py          # entry
src/
  cli.py           # CLI
  config.py        # config
  factory.py       # client factory by backend
  web/             # Cookie + PATHINFO
  rest/            # Token + /api.php/v1
  services/        # domain ops
zentao-har-apis.md # Web API notes
LICENSE            # MIT
```

## License

Released under the [MIT License](./LICENSE). Copyright (c) 2026 zhengqingquan.
