# 交接：待办与现状（handoff）

面向接手开发 / Agent：本文只写 **还要做什么** 和 **怎么接着干**。完整命令面契约见 [cli-surface.md](./cli-surface.md)。

**仓库**：`zqq-zentao-cli`，命令入口 `zqq-zentao`（勿与官方 npm `zentao` 混淆）。  
**更新日期**：2026-07-23  

---

## 1. 产品边界（已拍板，勿回退）

| # | 结论 |
|---|------|
| 1 | **放开写**：create / update / delete / 状态动作，不只备注 |
| 2 | 「我的」命令：`my-<noun> [--type …]` |
| 3 | 「我的」范围：work + contribute 常用模块（不限四个） |
| 4 | **本工具自建 CRUD**，不推给官方 CLI |
| 5 | **不限本人**：查/改他人数据用范围列表 + 过滤；`my-*` 仅当前用户快捷入口 |

通道：REST 优先；「我的」/备注/REST 难用时走 Web PATHINFO + zin dtable。能力矩阵在 `src/capabilities.py`。

---

## 2. 已经完成（可当基线）

| 项 | 说明 |
|----|------|
| 双通道登录 | `login` 写 Cookie + Token；`whoami` / `ping` |
| REST 只读浏览 | `rest/resources.py` 注册表：产品/项目/执行/需求/Bug… |
| `my-tasks` | 默认 work+assignedTo：web + rest；其它 type 强制 web |
| `my-bugs` 等「我的」 | **仅 web**；注册表 `web/my_pages.py`；`--type` / `--scope` |
| Web 翻页拉全 | `fetch_dtable_list_paginated`：默认 `recPerPage=200` + pageID 循环；覆盖全部 `my-*` 与 `execution` 任务列表 |
| `comment list/add/edit` | **仅 web** |
| 查别人 | `tasks` / `bugs` / `stories`：`--assignedTo` / `--openedBy`（支持实名）+ `--status` + `--pick` |
| bug / task / story 写 | REST：`create`/`update`/`delete` + 状态动作；写前确认 + `--yes`（非 TTY 必带） |
| 契约文档 | `docs/cli-surface.md`；README 已指向 |
| 提交规范 | 用 `.cursor/scripts/git-commit.ps1`，禁止直接 `git commit`；默认不 push |

近期相关提交（便于 `git log`）：

- `feat: add REST story write and status actions with --yes confirm`
- `feat: paginate Web my-* and execution task lists beyond default 20`
- `feat: add REST bug/task write and status actions with --yes confirm`
- `feat: add my-* --type/--scope registry (stories, todos, tests, feedbacks, tickets)`
- `feat: resolve users by realname; add --status/--pick; ignore .cursor`
- `feat: add --assignedTo/--openedBy filters for tasks, bugs, stories`

---

## 3. 待办清单（按优先级）

### P0 — 已完成（基线，勿回退）

- [x] **P0-A**：姓名 → 账号、`--status`、`--pick`/默认列、鉴权日志走 stderr
- [x] **P0-B**：`my-* --type/--scope`；stories/todos/test…；空 dtable = 成功

### P1 — 核心写（全面操作的关键）

优先 REST（见 `docs/zentao-rest-apis.md`）；不通再 Web 表单（学 `comment`）。

- [x] **bug**：`create` / `update` / `delete` + `confirm` / `resolve` / `close` / `activate` / `assign`（REST）
- [x] **task**：`create` / `update` / `delete` + `start` / `finish` / `close` / `activate` / `assign`（REST）
- [x] **story**：`create` / `update` / `delete` + `change` / `close` / `activate` / `assign` / `review` / `submitreview` / `recall`（REST）
- [x] 写前确认；破坏性操作支持 `--yes`（非 TTY 必须 `--yes`）
- [ ] **联调**：隔离环境对真实禅道验 bug/task/story 写（此前仅离线测）；失败再补 Web 回退
- [x] 更新 skill：已实现才执行，未实现对照本文 / `cli-surface`，勿臆造

### P2 — 其余 CUD

- [ ] productplan / release / build / testcase / testsuite / testtask
- [ ] feedback / ticket / todo 写与状态动作
- [ ] program / product / project / execution 写（权限高，可更后）

### P3 — 工程与体验 / 优化

已完成：

- [x] Web「我的」注册表化（`web/my_pages.py`）
- [x] Web 列表大 `recPerPage` / 翻页拉全（my-*、execution tasks）

仍建议优化（按收益排序）：

| 优先级 | 项 | 为什么 | 切入点 |
|--------|-----|--------|--------|
| **高** | **bugs/stories 服务端搜** | 大产品下客户端滤 `assignedTo` 会先拉全量，慢且易超时 | 查 22.3 REST search / Web 浏览参数；能服务端则服务端，否则文档标明限制 |
| **中** | **用户表短缓存** | 每次实名解析都打 users，批量查询重复 | `user_resolve.py` + 本地 TTL 缓存（按 server+account） |
| **中** | **补齐次要 my-\*** | `my-requirements` / `my-epics` / `my-docs` / `my-projects` / `my-executions` 契约仍 ⏳ | 扩 `my_pages.py` 注册表即可复用翻页 |
| **中** | **README 示例对齐现状** | 写/my-\*/`--pick`/`--status` 示例可能落后 | `README.md` / `README.en.md` + skill |
| **低** | **双通道失败降级** | `auto` 时 rest 挂了自动试 web（或反之） | `capabilities` / `factory`；可选，勿默默吞错 |
| **低** | **REST my-tasks 与 Web 翻页一致体验** | REST 侧分页已有 workaround；确认大列表不截断 | `rest/tasks.py`；对照 Web 200/页行为 |
| **低** | **脱敏 / 日志** | 勿把真实同事名写进仓库文档与测试夹具 | `.cursor/rules/desensitize.mdc` |

### 文档 / 技能（随实现更新）

- [x] 每完成一块，改 `cli-surface.md` 状态列（✅/⏳）与本节勾选（P1 核心三角已 ✅；P2 仍 ⏳）
- [x] 同步 `README.md` / `README.en.md`：写命令、`my-* --type`、翻页已拉全、勿再暗示「只能备注」
- [x] 个人 skill：`~/.cursor/skills/zqq-zentao/SKILL.md`（若仍使用）对齐 cli-surface

参考 PATHINFO（ZenTao 22.3，含分页段）：

- work/contribute：`/my-{scope}-{mode}-{browseType}-{param}-{orderBy}-{recTotal}-{recPerPage}-{pageID}.html?zin=1`
- todo：`/my-todo-{browseType}--all-{orderBy}-{recTotal}-{recPerPage}-{pageID}.html?zin=1`
- 源码：`zentao-22.3-php8.1/.../module/my/control.php`

---

## 4. 已知坑（接手必读）

| 现象 | 原因 / 对策 |
|------|-------------|
| 问「张三的任务」 | `--assignedTo 张三` 会解析实名；多命中时报错列候选。也可用 `users --search 张三` |
| `GET /bugs` 要 product id | 无全局 my-bugs REST；用 Web `my-bugs` 或 `bugs --product` |
| 产品下 `assignedTo` query 无效 | 服务端常忽略 → 客户端过滤（已实现）；**大产品会慢**（P3 待优化服务端搜） |
| `GET /tasks` 无 execution | 默认像「我的任务」；查别人用 `--assignedTo`（`search=1`） |
| `tasks --openedBy` 单独用 | API search 无 openedBy → 须 `-e` 或同时 `--assignedTo` |
| 只有 Token 无 Cookie | Web 命令（`my-*`/`comment`）失败 → 需 `login` 带密码 |
| Web 默认每页 20 | **已修**：CLI 用 `recPerPage=200` + 翻页；勿再改回短 PATHINFO 无分页段 |
| APIv1 my-tasks 分页参数错位 | 已在 `rest/tasks.py` 用 query 绕过，勿轻易改 |
| Windows 管道中文乱码 | 注意 `PYTHONIOENCODING=utf-8`；解析 JSON 时勿依赖控制台编码 |
| bug/task/story 写仅离线测 | 真机写前用隔离环境 + `--yes`；失败对照源码 entry 再补 |

本地禅道源码（接口对照）：`G:\codelib\zentao-22.3-php8.1\zentao-22.3-php8.1\zentaopms`（若路径变更以本机为准）。

查 REST/Web 时遵守仓库规则 [`.cursor/rules/zentao-source-lookup.mdc`](../.cursor/rules/zentao-source-lookup.mdc)（哪里查什么已列表）。

---

## 5. 关键代码入口

| 路径 | 职责 |
|------|------|
| `src/cli.py` | 命令注册与分发 |
| `src/capabilities.py` / `factory.py` | 选 web / rest |
| `src/user_resolve.py` | 姓名/账号解析、`users --search` |
| `src/list_filter.py` | `--assignedTo` / `--openedBy` / `--status` 客户端过滤 |
| `src/rest/resources.py` | REST 只读注册表（含 `user_filters`） |
| `src/rest/tasks.py` | my-tasks / search / execution 任务 |
| `src/rest/writes.py` | REST 写路径与响应校验 |
| `src/confirm_util.py` / `payload.py` | 写前确认、`--data` 合并 |
| `src/services/stories.py` | story 写与状态动作（确认层） |
| `src/web/my_pages.py` | 「我的」Web 页注册表（`--type` / `--scope` + 分页 PATHINFO） |
| `src/web/lists.py` | zin dtable：单页 + **翻页拉全** |
| `src/web/bugs.py` / `web/tasks.py` / `web/comments.py` | Web 拉页与解析 |
| `src/web/parse.py` | zin / dtable |
| `docs/cli-surface.md` | 命令面契约 |
| `docs/zentao-apis.md` / `zentao-rest-apis.md` | 接口说明 |

测试：`python -m pytest`（无第三方依赖；勿对真实禅道写破坏性测试除非有隔离环境）。

---

## 6. 建议下一刀（给 Agent 的一句话）

> **优先 bugs/stories 大产品服务端过滤**（客户端滤慢/易超时）。并行可做：P2 次要模块写（productplan/testcase…）或 README/skill 示例同步；或低成本补 `my-requirements` / `my-epics`。真机写联调另开，勿默认对生产环境试写。

备选（体验刀）：用户表短缓存；或注册 `my-requirements` / `my-epics`（复用翻页注册表，成本低）。

---

## 7. 修订

| 日期 | 说明 |
|------|------|
| 2026-07-23 | 初版交接文档（对齐已拍板边界与当前已实现过滤） |
| 2026-07-23 | P0-A：姓名解析、`--status`、`--pick`/默认列、空 dtable 对齐 |
| 2026-07-23 | P0-B：`my-* --type/--scope` 与 my-stories/todos/test… 注册表 |
| 2026-07-23 | P1：bug/task REST 写与状态动作 + `--yes` 确认 |
| 2026-07-23 | P3：Web my-\*/execution 翻页拉全；重写「已完成 / 优化表 / 下一刀」 |
| 2026-07-23 | P1：story REST 写与状态动作；下一刀改为服务端过滤 / P2 |
