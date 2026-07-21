# zqq-zentao-cli

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
```

## License

MIT
