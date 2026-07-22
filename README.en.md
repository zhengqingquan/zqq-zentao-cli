# zqq-zentao-cli

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

[中文](./README.md) | **English**

ZenTao dual-backend CLI: **Web (PATHINFO + Cookie)** and **REST (Token)**.

- Python ≥ 3.10, no third-party dependencies
- **Target surface**: **full ZenTao CLI** (query anyone/anything within ACL + CRUD/status actions + comments); see [docs/cli-surface.md](./docs/cli-surface.md)
- `my-*` is only a shortcut for the logged-in user; use scoped lists + `--assignedTo` (etc.) for others (target API, rolling out)
- Web handles comments and “My” pages where REST is awkward; REST fits structured browse/filter and writes
- Shares env vars and `~/.config/zentao/zentao.json` with the official [zentao-cli](https://github.com/easysoft/zentao-cli) (this tool also stores `webCookies`); **this tool owns a full capability surface including CRUD**
- Web PATHINFO API notes: [docs/zentao-apis.md](./docs/zentao-apis.md)
- REST API v1 (from 22.3 source): [docs/zentao-rest-apis.md](./docs/zentao-rest-apis.md)
- **CLI contract (phased)**: [docs/cli-surface.md](./docs/cli-surface.md)

## Install

```bash
pip install -e .
zqq-zentao -h
```

After install the console command is **`zqq-zentao`** (package `zqq-zentao-cli`); it does not take over the official `zentao` name.

## Config & login

Preferred (same idea as official CLI). Credentials go to `~/.config/zentao/zentao.json` (**password is never stored**):

```bash
zqq-zentao login -s https://zentao.example.com -u your_account -p your_password
```

| Flag | Description | Env fallback |
|------|-------------|--------------|
| `-s` / `--server` | ZenTao base URL (no trailing slash) | `ZENTAO_URL` (preferred) or `ZENTAO_SERVER` |
| `-u` / `--account` | Account | `ZENTAO_ACCOUNT` |
| `-p` / `--password` | Password | `ZENTAO_PASSWORD` |

On success, the current profile stores:

- `webCookies` — Web session cookies (this tool; ignored by official CLI)
- `token` — REST token (same field as official CLI)

Env-only setups still work; unauthenticated commands hint you to run `zqq-zentao login`.

| Variable | Description | Official zentao-cli |
|----------|-------------|---------------------|
| `ZENTAO_URL` | ZenTao base URL (preferred; matches official) | ✅ |
| `ZENTAO_SERVER` | Same, this tool’s alias | ❌ |
| `ZENTAO_ACCOUNT` | Account | ✅ |
| `ZENTAO_PASSWORD` | Password (not on disk; needed for `login` or when Cookie/Token missing) | ✅ |
| `ZENTAO_TOKEN` | REST token (overrides file token) | ✅ |
| `ZENTAO_BACKEND` | `web` \| `rest` \| `auto` (default `auto`) | — |
| `ZENTAO_INSECURE` | Default `1` skips TLS verify; set `0` to verify | — (official uses `--insecure`) |
| `ZENTAO_CONFIG_FILE` | Custom config file path | ✅ |

### Global options (aligned with official zentao-cli)

| Option | Description |
|--------|-------------|
| `-V` / `--version-flag` | Show version |
| `--format <markdown\|json\|raw>` | Output format; default `markdown` (tables / key lists); `json` wraps `{status,data}`; `raw` is plain JSON |
| `--silent` | Suppress result output |
| `--insecure` / `--secure` | Skip / force TLS certificate verification |
| `--timeout <ms>` | Request timeout in milliseconds (default 60000) |
| `--config <file>` | Custom config file (or `ZENTAO_CONFIG_FILE`) |
| `--machine-readable` | Compact output, disable colors |
| `-h` / `--help` | Show help |

```bash
zqq-zentao -V
zqq-zentao --format json whoami
zqq-zentao --format raw --machine-readable task 39980
zqq-zentao --timeout 10000 --insecure my-tasks
zqq-zentao --config ./zentao.json whoami
```

Skip TLS certificate verification (common for self-signed / internal HTTPS):

```bash
# Global flag (same idea as official zentao --insecure); optional — default already skips verify
zqq-zentao --insecure login -s https://zentao.example.com -u your_account -p your_password
zqq-zentao --insecure task 39980

# Force certificate verification
zqq-zentao --secure whoami
# or
# export ZENTAO_INSECURE=0
```

Priority: `--insecure` / `--secure` > `ZENTAO_INSECURE` (default skip).

To share env with the official CLI, set `ZENTAO_URL` — do not rely on `ZENTAO_SERVER` alone.

PowerShell example:

```powershell
$env:ZENTAO_URL = "https://zentao.example.com"
$env:ZENTAO_ACCOUNT = "your_account"
$env:ZENTAO_PASSWORD = "your_password"
zqq-zentao login
```

Auth behavior:

- **Web**: prefer cached `webCookies`; on expiry, re-login with `ZENTAO_PASSWORD` if set and rewrite; otherwise hint `zqq-zentao login`
- **REST**: `ZENTAO_TOKEN` → profile `token` → password exchange

**Never** print Cookie, password, or Token in logs or chat.

## Usage

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
zqq-zentao comment add task 39973 "comment text"
zqq-zentao comment edit 1063694 "updated comment"
```

| Command | Description | Backend |
|---------|-------------|---------|
| `login` | Login and cache Cookie / Token | web + rest (`auto`) |
| `whoami` | Current account and server | web / rest |
| `my-tasks` | Tasks assigned to me (REST filters `/tasks` by assignee) | web / rest |
| `my-bugs` | Bugs assigned to me (Web: `/my-work-bug-assignedTo.html`) | **web only** |
| `tasks` | REST task list (`--page` / `--limit`) | **rest only** |
| `tasks -e <id>` | Tasks under an execution | web / rest |
| `task <id>` | Task detail (REST returns full fields) | web / rest |
| `users` / `user <account>` | User list / detail | **rest only** |
| `projects` | Project list (optional `--program` / `--product`) | **rest only** |
| `project <id>` | Project detail | **rest only** |
| `programs` / `program <id>` | Program list / detail | **rest only** |
| `products` / `product <id>` | Product list / detail (list may use `--program`) | **rest only** |
| `executions` / `execution <id>` | Execution list / detail | **rest only** |
| `departments` / `department <id>` | Department list / detail | **rest only** |
| `stories` / `story` | Story list / detail (list needs `--product`/`--project`/`--execution`) | **rest only** |
| `bugs` / `bug` | Bug list / detail (same scopes) | **rest only** |
| `productplans` / `releases` / `builds` / … | Read-only plans, releases, builds, test, feedback, tickets, todos, issues, risks, meetings, docs | **rest only** |
| `ping` / `groups` / `configurations` / … | System read-only | **rest only** |
| `comment list/add/edit` | Comment CRUD | **web only** |

REST read-only modules are driven by [`src/rest/resources.py`](./src/rest/resources.py). Path map: [docs/zentao-rest-apis.md](./docs/zentao-rest-apis.md). Target CLI surface (including `my-* --type` and phased CRUD): [docs/cli-surface.md](./docs/cli-surface.md). Run `zqq-zentao -h` for currently implemented commands.

`--backend` overrides `ZENTAO_BACKEND`. For `auto`: prefer rest when a token exists (env or config file), otherwise web; rest-only / web-only commands force that backend. `login` with `auto` performs both Web and REST credential exchange.

## Layout

```
src/                 # installed as package zqq_zentao_cli; console: zqq-zentao
  cli.py
  config.py
  factory.py
  capabilities.py
  protocol.py
  web/               # Cookie + PATHINFO
  rest/              # Token + /api.php/v1 (incl. resources.py read-only registry)
  services/
docs/
  zentao-apis.md      # Web PATHINFO notes
  zentao-rest-apis.md # REST API v1 (from 22.3 source)
  cli-surface.md      # CLI contract (my-* / phased CRUD)
LICENSE              # MIT
```

## License

Released under the [MIT License](./LICENSE). Copyright (c) 2026 zhengqingquan.
