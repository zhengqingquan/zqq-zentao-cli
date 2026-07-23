# 交接：待办与现状（handoff）

面向接手开发 / Agent：**只写未完成项与怎么接着干**。  
契约（命令面 / ✅⏳）→ [cli-surface.md](./cli-surface.md)；通道选择 → [channel-matrix.md](./channel-matrix.md)；非目标 → cli-surface **G**。

**仓库**：`zqq-zentao-cli`，入口 `zqq-zentao`（勿与官方 npm `zentao` 混淆）。  
**禅道锚点**：22.3（本地只读源码 `…/zentaopms`）；**REST v1 默认**（写仅 v1）；**REST v2 可选只读**（`--api v2`）；Web 仍扛 my-* / comment。  
**更新日期**：2026-07-24  

边界已拍板（勿回退）：放开写、`my-<noun> [--type]`、work+contribute 常用「我的」、自建 CRUD、查他人走 scope+过滤。细节见 cli-surface。

基线已落地（细节勿在此展开）：双通道登录；REST 只读 registry（v1 + 常用 v2）；`projects|products|programs --search`；`my-*`（含 requirements/epics/docs/projects/executions）；Web 翻页拉全；`comment`；tasks/bugs/stories 过滤；**写**：bug/task/story + **todo** + **testcase/testsuite/testtask**（REST，`--yes`；均仅离线测）；browseType；`cli_app` 表驱动写；用户短缓存；auto 降级。里程碑用 `git log --oneline -20`。

**暂缓**：本地起禅道 / 真机写联调（避免误伤生产）。P1 勾选保持打开，有隔离环境再做。

遵守 [`.cursor/rules/desensitize.mdc`](../.cursor/rules/desensitize.mdc)（文档/测试勿写真实人名）。

---

## 1. 未完成待办

### P1 — 真机写联调（宣称「写可用」前的门槛；**暂缓**）

凡 REST 写目前都只做了路径/解析离线测。须在**隔离禅道**上验，**勿打生产**。

建议 checklist（均带 `--yes`，非 TTY 必须）：

1. `bug create` → `assign` / `resolve` / `close` → `activate`；抽测 `update` / `delete`
2. `task create` → `start` / `finish` / `close` → `activate`；抽测 `assign`
3. `story create` → `change` / `review` 族 / `close` → `activate`
4. `todo create` → `finish` / `activate`；抽测 `update` / `delete`（finish/activate 为 **GET**）
5. `testcase create`（`--data` 带 `steps`）→ `results`；抽测 update/delete  
   `testsuite create|delete`；`testtask create|delete`（create 需 project+product+execution+build+name+begin+end）
6. 失败：对照 `api/v1/entries/*`，再考虑 Web 表单回退（学 `comment`）

- [ ] 隔离环境联调通过（或明确记录「已知失败 + 回退计划」）— **暂缓，无隔离环境前不要勾**

### P2 — 其余 CUD（有 REST entry 优先）

契约见 cli-surface **D**。抄：`services/*` + `rest/writes.py` + `cli_app/write_dispatch.py`（create 时 path scope 会从 body 剔除，见已知坑）。

| 优先 | 模块 | 状态 |
|------|------|------|
| 已做 | `todo` | ✅ create/update/delete + finish/activate（GET） |
| 已做 | `testcase` / `testsuite` / `testtask` | ✅；suite/task **无 PUT**；case 含 `results` |
| **下一刀** | `feedback` / `ticket` | ⏳ 列表/`my-*` 已有；写按 entry |
| 其次 | `productplan` / `release` / `build` | ⏳ |
| 更后 | `program` / `product` / `project` / `execution` | ⏳ 权限高 |
| 另轨 | `requirement` / `epic` | ⏳ 可挂 story 族 |

- [x] todo + test* 落地（离线；真机归 P1）
- [ ] feedback/ticket 或 plan 族按需落地，并同步 cli-surface

### P3 — 体验 / 补齐

| 优先级 | 项 | 状态 |
|--------|-----|------|
| **中** | 次要 `my-*`（requirements/epics/docs/projects/executions） | ✅ |
| **中** | 用户表短缓存（`user_resolve`，TTL 60s） | ✅ |
| **低** | `--finishedBy`/`--resolvedBy`/`--closedBy`/`--pri`；更多 `--search` | ✅ |
| **低** | `auto` 双通道失败降级 | ✅ |
| **低** | REST my-tasks：首拉 500 + total bump | ✅（离线；真机可再确认） |

可选仍 ⏳：`my-issues` / `my-risks` / `my-meetings`；`--severity`。

### 文档纪律（实现时做）

改 cli-surface 状态列；勾选本节；必要时改 README / 个人 skill。本文不堆大段 ✅。

---

## 2. 已知坑（接手必读）

| 现象 | 原因 / 对策 |
|------|-------------|
| 问「张三的任务」 | `--assignedTo 张三` 解析实名；多命中列候选。或 `users --search 张三` |
| `GET /bugs` 要 product | 无全局 my-bugs REST → Web `my-bugs` 或 `bugs --product` |
| 查他人 bugs/stories | REST 无任意账号过滤；本人/状态走 `browse_filter.py`；他人客户端全量。见 channel-matrix |
| `GET /tasks` 无 execution | 默认像「我的任务」；查别人 `--assignedTo`（`search=1`） |
| `tasks --openedBy` 单独用 | search 无 openedBy → 须 `-e` 或同时 `--assignedTo` |
| 只有 Token 无 Cookie | `my-*` / `comment` 失败 → `login` 带密码 |
| Web 默认每页 20 | **已修** `recPerPage=200` + 翻页；勿改回短 PATHINFO |
| APIv1 my-tasks 分页错位 | `rest/tasks.py` 绕过（首拉 500 + bump），勿轻易改 |
| APIv2 projects 分页不可靠 | 实机易重复/忽略；`projects --search` 勿依赖 v2 翻页拉全 |
| Windows 管道中文乱码 | `PYTHONIOENCODING=utf-8`；解析 JSON 勿依赖控制台编码 |
| 所有 REST 写仅离线测 | 见 **P1**；隔离环境 + `--yes`；**暂缓真机** |
| todo finish/activate | 源码为 **GET**；CLI `--comment` 等 body 无效 |
| testsuite/testtask 无 update | APIv1 无 PUT entry；勿臆造 |
| testcase create 要 steps | `requireFields`；用 `--data '{"steps":[…]}'` |
| create 的 path scope | `write_dispatch` 会从 body **剔除** `--product`/`--execution`/`--project`（已在 URL）；testtask 仍保留 body 内 product/execution/build |
| testtask create 源码 | `testtasks.php` post 里 `$build` 未定义（应为 `$buildID`）；建单主要读 `$_POST`，真机再确认 |
| 任务详情 `operateMenu` | REST 只回 **mainActions**（如 closed→`activate`）；**不含** Web 的 suffix `edit`。关闭态仍可 `task update`（REST PUT=`task::edit`，与 `/task-edit-{id}.html` 同路），**不必**先 activate。详情经 `enrich_task_detail` 会补上 `edit` + `canFieldEdit` |
| 任务改 execution/module/parent | 无专用 REST「选项」API；Web edit 分别用 `getByProject` / `getTaskOptionMenu` / `getParentTaskPairs`。CLI：`task options <id>`（REST 拼装；parent 为客户端按同源规则过滤）或拆开 `executions --project` / `modules --type task --id` |
| auto 降级 | 仅双能力 + `--backend auto`；显式 `--backend` 不降级 |

源码查阅：[`.cursor/rules/zentao-source-lookup.mdc`](../.cursor/rules/zentao-source-lookup.mdc)。  
PATHINFO：[zentao-web-pathinfo.md](./zentao-web-pathinfo.md)。

---

## 3. 关键代码入口

| 路径 | 职责 |
|------|------|
| `src/cli.py` | 控制台入口 / 测试面（转发 `cli_app`） |
| `src/cli_app/parser.py` / `dispatch.py` | 参数与命令分发 |
| `src/cli_app/write_dispatch.py` / `body.py` | 表驱动写、payload；create 剔 path scope |
| `src/cli_app/fields.py` | `--pick` / 默认列 |
| `src/capabilities.py` / `factory.py` | 选 web / rest；`--api`；auto 降级 |
| `src/config.py` | 全局配置（含 `ZENTAO_API`） |
| `src/user_resolve.py` | 姓名/账号解析、短缓存 |
| `src/list_filter.py` | 客户端用户/状态/pri/关键词过滤 |
| `src/rest/resources.py` | REST **v1** 只读注册表（`SPECIAL_CMDS` 含写名词） |
| `src/rest/resources_v2.py` / `v2_search.py` | REST **v2** 只读 |
| `src/rest/tasks.py` | my-tasks / search / execution 任务 |
| `src/rest/writes.py` | REST 写路径与响应校验 |
| `src/rest/browse_filter.py` | bugs/stories → `status=` browseType |
| `src/rest/client.py` | REST 客户端（写始终 v1 session） |
| `src/confirm_util.py` / `payload.py` | 写前确认、`--data` 合并 |
| `src/services/bugs.py` / `tasks.py` / `stories.py` | 三角写确认层；`get_task` 经 `enrich_task_detail` |
| `src/services/task_options.py` | `task options`：execution/module/parent 可填项 |
| `src/task_shape.py` | 列表 summarize；详情补 `edit`/`canFieldEdit`（勿把 mainActions 当能否改字段） |
| `src/services/todos.py` / `testcases.py` / `testsuites.py` / `testtasks.py` | P2 写确认层 |
| `src/web/my_pages.py` | 「我的」注册表 + 分页 PATHINFO |
| `src/web/lists.py` / `comments.py` | dtable 翻页；备注 |
| `docs/cli-surface.md` / `channel-matrix.md` | 契约 / 通道矩阵 |
| `docs/zentao-rest-apiv1.md` / `zentao-web-pathinfo.md` | 接口对照；v2 见 `zentao-rest-apiv2.md` |

测试：`python -m pytest`（勿对真实禅道写破坏性测试，除非隔离环境）。

---

## 4. 建议下一刀

总裁决（按序，可跳过）：

1. **P2 续**（当前默认）：`feedback` / `ticket` 写（有 REST 则挂 `write_dispatch`）；否则 plan/release/build  
2. **P1 联调**（有隔离禅道时再开）：checklist 含三角 + todo/test*  
3. 备选：`my-issues`/`my-risks`/`my-meetings`；`--severity`；`requirement`/`epic`

勿默认对生产试写。查他人 bugs/stories 无 REST 任意账号过滤——已文档化，非本刀范围。

---

## 5. 修订

| 日期 | 说明 |
|------|------|
| 2026-07-23 | 初版 → P0 过滤/`my-*`、P1 三角写、Web 翻页、browseType、channel-matrix |
| 2026-07-23 | 瘦身：未完成项为主；与 cli-surface 去重 |
| 2026-07-24 | REST v1/v2/Web；`--api`；表驱动写；P3 体验项落地 |
| 2026-07-24 | **P2 首刀**：todo + testcase/testsuite/testtask REST 写（对照 22.3；无真机） |
| 2026-07-24 | 审查：create 剔除 path scope；P1 标暂缓；下一刀改默认 P2 续；坑表补 todo/test* |
| 2026-07-24 | 任务关闭态仍可字段编辑：`enrich_task_detail`；handoff/channel-matrix/pathinfo 对齐 Web `task-edit` |
