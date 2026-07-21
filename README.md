# zqq-zentao-cli

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

**中文** | [English](./README.en.md)

禅道（ZenTao）双通道命令行工具：支持 **Web（PATHINFO + Cookie）** 与 **REST（Token）**。

- Python ≥ 3.10，无第三方依赖
- Web 可读写备注；REST 适合任务只读等结构化接口
- Web PATHINFO 接口说明见 [zentao-har-apis.md](./zentao-har-apis.md)

## 安装

```bash
pip install -e .
zentao -h
```

## 配置与登录

推荐与官方 CLI 一样显式登录（凭证写入 `~/.config/zentao/zentao.json`，**不存密码**）：

```bash
zentao login -s https://zentao.example.com -u your_account -p your_password
```

| 参数 | 说明 | 环境变量回退 |
|------|------|----------------|
| `-s` / `--server` | 禅道地址（无尾斜杠） | `ZENTAO_SERVER` 或 `ZENTAO_URL` |
| `-u` / `--account` | 账号 | `ZENTAO_ACCOUNT` |
| `-p` / `--password` | 密码 | `ZENTAO_PASSWORD` |

登录成功后写入当前 profile：

- `webCookies`：Web 会话 Cookie（本工具字段）
- `token`：REST Token（与官方字段一致）

也可仅用环境变量；未登录时业务命令会提示执行 `zentao login`。

| 变量 | 说明 |
|------|------|
| `ZENTAO_SERVER` 或 `ZENTAO_URL` | 禅道地址 |
| `ZENTAO_ACCOUNT` | 账号 |
| `ZENTAO_PASSWORD` | 密码（不落盘；`login` 或缺 Cookie/Token 时需要） |
| `ZENTAO_TOKEN` | REST Token（有则优先于文件内 token） |
| `ZENTAO_BACKEND` | `web` \| `rest` \| `auto`（默认 `auto`） |
| `ZENTAO_INSECURE` | 默认 `1` 跳过 TLS 校验；设为 `0` 则校验 |

PowerShell 示例：

```powershell
$env:ZENTAO_URL = "https://zentao.example.com"
$env:ZENTAO_ACCOUNT = "your_account"
$env:ZENTAO_PASSWORD = "your_password"
zentao login
```

**不要**在日志或对话中打印 Cookie、密码、Token。

## 用法

```bash
zentao login -s https://zentao.example.com -u admin -p secret
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
| `login` | 登录并缓存 Cookie / Token | web + rest（`auto`） |
| `whoami` | 当前账号与服务器 | web / rest |
| `my-tasks` | 指派给我的任务 | web / rest |
| `tasks -e <id>` | 某执行下的任务列表 | web / rest |
| `task <id>` | 任务详情（JSON） | web / rest |
| `comment list/add/edit` | 备注增改查 | **仅 web** |

`--backend` 可覆盖 `ZENTAO_BACKEND`。`auto`：有 Token（环境变量或配置文件）偏向 rest，否则 web；备注类命令强制 web。`login` 在 `auto` 下会同时完成 Web 与 REST 换票。

## 目录结构

```
src/                 # 安装后映射为包 zqq_zentao_cli，入口命令：zentao
  cli.py
  config.py
  factory.py
  web/               # Cookie + PATHINFO
  rest/              # Token + /api.php/v1
  services/
zentao-har-apis.md   # Web 接口说明
LICENSE              # MIT
```

## 许可证

本项目采用 [MIT License](./LICENSE) 授权。Copyright (c) 2026 zhengqingquan。
