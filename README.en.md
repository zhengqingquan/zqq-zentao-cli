# zqq-zentao-cli

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

[中文](./README.md) | **English**

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
