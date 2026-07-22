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
| `my-tasks` | web + rest |
| `my-bugs` | **仅 web**：`/my-work-bug-assignedTo.html?zin=1` |
| `comment list/add/edit` | **仅 web** |
| 查别人（账号） | `tasks` / `bugs` / `stories` 支持 `--assignedTo` / `--openedBy` |
| 契约文档 | `docs/cli-surface.md`；README 已指向 |
| 提交规范 | 用 `.cursor/scripts/git-commit.ps1`，禁止直接 `git commit`；默认不 push |

近期相关提交（便于 `git log`）：

- `feat: add my-bugs via Web my-work-bug-assignedTo page`
- `docs: define CLI surface contract for full ZenTao operations`
- `feat: add --assignedTo/--openedBy filters for tasks, bugs, stories`

---

## 3. 待办清单（按优先级）

### P0-A — 立刻（体验，减少「按姓名查人」那种多步）

- [x] **姓名 → 账号**
  - `users --search` / `--realname`，或
  - `--assignedTo 张三` 自动按 `realname`/`account` 解析
  - 模糊唯一则直接用；多命中则报错列出候选
- [x] **`--status`**（至少 `tasks` / `bugs` / `stories`）
  - 例：只要 `wait`/`doing`，避免一次吐出几十条 `done`
- [x] **默认表格字段收敛** + 可选 `--pick`
- [x] **鉴权日志**：`auth: rest-token(...)` 保持 stderr，文档写明勿与 stdout JSON 混用

### P0-B — 「我的」补齐

- [x] `my-tasks` / `my-bugs` 支持 `--type`（contribute：`openedBy` / `resolvedBy` 等）
- [x] 新增 `my-stories`、`my-todos`、`my-testcases`、`my-testtasks`、`my-feedbacks`、`my-tickets`（Web PATHINFO，对齐禅道 22.3 `my::work` / `my::contribute`）
- [x] 空 dtable（0 条）视为成功，勿当解析失败（`my-bugs` / `my-tasks` / execution 已对齐）

参考路径：

- `/my-work-{mode}-{browseType}.html?zin=1`
- `/my-contribute-{mode}-{browseType}.html?zin=1`
- 源码：`zentao-22.3-php8.1/.../module/my/control.php`

### P1 — 核心写（全面操作的关键）

优先 REST（见 `docs/zentao-rest-apis.md`）；不通再 Web 表单（学 `comment`）。

- [ ] **bug**：`create` / `update` / `delete` + `confirm` / `resolve` / `close` / `activate` / `assign`
- [ ] **task**：`create` / `update` / `delete` + `start` / `finish` / `close` / `activate` / `assign`
- [ ] **story**：`create` / `update` / `delete` + `change` / `close` / `activate` / …
- [ ] 写前确认；破坏性操作支持 `--yes`
- [ ] 更新 skill：已实现才执行，未实现对照本文 / `cli-surface`，勿臆造

### P2 — 其余 CUD

- [ ] productplan / release / build / testcase / testsuite / testtask
- [ ] feedback / ticket / todo 写与状态动作
- [ ] program / product / project / execution 写（权限高，可更后）

### P3 — 工程与体验

- [x] Web「我的」注册表化（`web/my_pages.py` + `fetch_dtable_list`；可继续扩 epic/requirement 等）
- [ ] bugs/stories 过滤：尽量服务端搜，避免「拉全量再滤」过慢
- [ ] Web 列表大 `recPerPage` / 翻页拉全
- [ ] 双通道失败降级（可选）
- [ ] 用户表本地短缓存（服务姓名解析）

### 文档 / 技能（随实现更新）

- [ ] 每完成一块，改 `cli-surface.md` 状态列（✅/⏳）与本节勾选
- [ ] 同步 `README.md` / `README.en.md` 示例
- [ ] 个人 skill：`~/.cursor/skills/zqq-zentao/SKILL.md`（若仍使用）

---

## 4. 已知坑（接手必读）

| 现象 | 原因 / 对策 |
|------|-------------|
| 问「张三的任务」 | `--assignedTo 张三` 会解析实名；多命中时报错列候选。也可用 `users --search 张三` |
| `GET /bugs` 要 product id | 无全局 my-bugs REST；用 Web `my-bugs` 或 `bugs --product` |
| 产品下 `assignedTo` query 无效 | 服务端常忽略 → 客户端过滤（已实现）；大产品会慢 |
| `GET /tasks` 无 execution | 默认像「我的任务」；查别人用 `--assignedTo`（`search=1`） |
| `tasks --openedBy` 单独用 | API search 无 openedBy → 须 `-e` 或同时 `--assignedTo` |
| 只有 Token 无 Cookie | Web 命令（`my-bugs`/`comment`）失败 → 需 `login` 带密码 |
| APIv1 my-tasks 分页参数错位 | 已在 `rest/tasks.py` 用 query 绕过，勿轻易改 |
| Windows 管道中文乱码 | 注意 `PYTHONIOENCODING=utf-8`；解析 JSON 时勿依赖控制台编码 |

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
| `src/web/my_pages.py` | 「我的」Web 页注册表（`--type` / `--scope`） |
| `src/web/lists.py` | zin dtable 列表共用拉取（空表成功） |
| `src/web/bugs.py` / `web/tasks.py` / `web/comments.py` | Web 拉页与解析 |
| `src/web/parse.py` | zin / dtable |
| `docs/cli-surface.md` | 命令面契约 |
| `docs/zentao-apis.md` / `zentao-rest-apis.md` | 接口说明 |

测试：`python -m pytest`（无第三方依赖；勿对真实禅道写破坏性测试除非有隔离环境）。

---

## 6. 建议下一刀（给 Agent 的一句话）

> P0-A / P0-B 已完成。下一刀做 **P1 核心写**：优先 REST 实现 bug/task 的 create/update/状态动作（resolve/start/finish…），写前确认与 `--yes`；同步 `cli-surface` / 本文勾选。

---

## 7. 修订

| 日期 | 说明 |
|------|------|
| 2026-07-23 | 初版交接文档（对齐已拍板边界与当前已实现过滤） |
| 2026-07-23 | P0-A：姓名解析、`--status`、`--pick`/默认列、空 dtable 对齐 |
| 2026-07-23 | P0-B：`my-* --type/--scope` 与 my-stories/todos/test… 注册表 |
