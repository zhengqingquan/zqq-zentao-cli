# 交接：待办与现状（handoff）

面向接手开发 / Agent：**只写未完成项与怎么接着干**。  
契约（命令面 / ✅⏳）→ [cli-surface.md](./cli-surface.md)；通道选择 → [channel-matrix.md](./channel-matrix.md)；非目标 → cli-surface **G**。

**仓库**：`zqq-zentao-cli`，入口 `zqq-zentao`（勿与官方 npm `zentao` 混淆）。  
**禅道锚点**：22.3（本地只读源码 `…/zentaopms`）；本工具用 **REST APIv1**，未接 v2。  
**更新日期**：2026-07-23  

边界已拍板（勿回退）：放开写、`my-<noun> [--type]`、work+contribute 常用「我的」、自建 CRUD、查他人走 scope+过滤。细节见 cli-surface。

基线已落地（细节勿在此展开）：双通道登录；REST 只读 registry；`my-*`（tasks 默认可 rest，其余 web）；Web 翻页拉全；`comment`；tasks/bugs/stories 过滤（实名/`--status`/`--pick`）；bug/task/story REST 写 + `--yes`；bugs/stories 本人/状态 browseType 映射。里程碑用 `git log --oneline -20`。

遵守 [`.cursor/rules/desensitize.mdc`](../.cursor/rules/desensitize.mdc)（文档/测试勿写真实人名）。

---

## 1. 未完成待办

### P1 — 真机写联调（宣称「全面写」前的门槛；可选另开）

此前 bug/task/story 写仅离线测。在**隔离禅道**上验，勿默认打生产。

建议 checklist（均带 `--yes`，非 TTY 必须）：

1. `bug create` → `assign` / `resolve` / `close` → `activate`；抽测 `update` / `delete`
2. `task create` → `start` / `finish` / `close` → `activate`；抽测 `assign`
3. `story create` → `change` / `review` 族 / `close` → `activate`
4. 失败：对照 `api/v1/entries/*`，再考虑 Web 表单回退（学 `comment`）

- [ ] 隔离环境联调通过（或明确记录「已知失败 + 回退计划」）

### P2 — 其余 CUD（另开；有 REST entry 优先）

契约见 cli-surface **D**。实现时：先查 `docs/zentao-rest-apiv1.md` + `api/v1/entries/`，模式抄 `services/bugs.py` / `tasks.py` / `stories.py` + `rest/writes.py`。

| 优先建议 | 模块 | 切入 |
|----------|------|------|
| **先做** | `todo` | REST todo 相关 entry；我的列表已有 `my-todos` |
| **先做** | `testcase` / `testtask`（及 `testsuite`） | `api/v1/entries/` 下 test*；只读已有 |
| 其次 | `feedback` / `ticket` | 状态动作 `activate`/`close` 等；`my-feedbacks`/`my-tickets` 已有 |
| 其次 | `productplan` / `release` / `build` | 只读已有；写按 entry |
| 更后 | `program` / `product` / `project` / `execution` | 权限高 |
| 契约另轨 | `requirement` / `epic` | 可并入 story 族或独立；见 cli-surface |

- [ ] 上述模块按需落地，并同步 cli-surface 状态列

### P3 — 体验 / 补齐（按收益）

| 优先级 | 项 | 为什么 | 切入点 |
|--------|-----|--------|--------|
| **中** | 补齐次要 `my-*` | `my-requirements` / `my-epics` / `my-docs` / `my-projects` / `my-executions` 契约 ⏳ | 扩 `web/my_pages.py`（复用翻页） |
| **中** | 用户表短缓存 | 实名解析重复打 users | `user_resolve.py`，TTL 按 server+登录账号 |
| **低** | 通用过滤补齐 | `--finishedBy` / `--resolvedBy` / `--pri`；非 users 的 `--search` 仍 ⏳ | 见 cli-surface「通用过滤」；能 REST 则映射，否则客户端 |
| **低** | 双通道失败降级 | `auto` 时一侧挂了试另一侧 | `capabilities` / `factory`；勿默默吞错 |
| **低** | REST my-tasks 大列表 | 确认分页 workaround 不截断 | `rest/tasks.py`；对照 Web 200/页 |

不在本表追、但契约仍 ⏳ 的项：一律以 [cli-surface.md](./cli-surface.md) 为准。

### 文档纪律（实现时做）

每完成一块：改 cli-surface 状态列；勾选本节；必要时改 README / 个人 skill。本文不重复维护大段 ✅ 清单。

---

## 2. 已知坑（接手必读）

| 现象 | 原因 / 对策 |
|------|-------------|
| 问「张三的任务」 | `--assignedTo 张三` 解析实名；多命中列候选。或 `users --search 张三` |
| `GET /bugs` 要 product | 无全局 my-bugs REST → Web `my-bugs` 或 `bugs --product` |
| 查他人 bugs/stories | REST 无任意账号过滤；本人/状态已走 `browse_filter.py`；他人仍客户端全量（stderr 提示）。矩阵见 channel-matrix |
| `GET /tasks` 无 execution | 默认像「我的任务」；查别人 `--assignedTo`（`search=1`） |
| `tasks --openedBy` 单独用 | search 无 openedBy → 须 `-e` 或同时 `--assignedTo` |
| 只有 Token 无 Cookie | `my-*` / `comment` 失败 → `login` 带密码 |
| Web 默认每页 20 | **已修** `recPerPage=200` + 翻页；勿改回短 PATHINFO |
| APIv1 my-tasks 分页错位 | `rest/tasks.py` query 绕过，勿轻易改 |
| Windows 管道中文乱码 | `PYTHONIOENCODING=utf-8`；解析 JSON 勿依赖控制台编码 |
| bug/task/story 写仅离线测 | 见 **P1 联调**；隔离环境 + `--yes` |

源码查阅：[`.cursor/rules/zentao-source-lookup.mdc`](../.cursor/rules/zentao-source-lookup.mdc)。  
PATHINFO 形状：[zentao-web-pathinfo.md](./zentao-web-pathinfo.md)（work/contribute/todo 分页段）。

---

## 3. 关键代码入口

| 路径 | 职责 |
|------|------|
| `src/cli.py` | 命令注册与分发 |
| `src/capabilities.py` / `factory.py` | 选 web / rest |
| `src/user_resolve.py` | 姓名/账号解析、`users --search` |
| `src/list_filter.py` | 客户端用户/状态过滤 |
| `src/rest/resources.py` | REST 只读注册表 |
| `src/rest/tasks.py` | my-tasks / search / execution 任务 |
| `src/rest/writes.py` | REST 写路径与响应校验 |
| `src/rest/browse_filter.py` | bugs/stories → REST `status=` browseType |
| `src/confirm_util.py` / `payload.py` | 写前确认、`--data` 合并 |
| `src/services/bugs.py` / `tasks.py` / `stories.py` | 写与状态动作（确认层） |
| `src/web/my_pages.py` | 「我的」Web 注册表 + 分页 PATHINFO |
| `src/web/lists.py` | zin dtable 翻页拉全 |
| `src/web/comments.py` | 备注 Web |
| `docs/cli-surface.md` / `channel-matrix.md` | 契约 / 通道矩阵 |
| `docs/zentao-rest-apiv1.md` / `zentao-web-pathinfo.md` | 接口对照（v2 见 `zentao-rest-apiv2.md`，未用） |

测试：`python -m pytest`（勿对真实禅道写破坏性测试，除非隔离环境）。

---

## 4. 建议下一刀

总裁决（按序，可跳过已不需要的）：

1. **P1 联调**（若要对外宣称 bug/task/story 全面写）→ 隔离环境 checklist  
2. **低成本 `my-*`**：`my-requirements` / `my-epics`（扩注册表）  
3. **用户表短缓存**  
4. **P2 写**：优先 `todo` 或 `testcase` 族；另开 PR/会话  

勿默认对生产试写。查他人 bugs/stories 无 REST 任意账号过滤——已文档化，非本刀范围。

备选：双通道降级；REST my-tasks 大列表确认。

---

## 5. 修订

| 日期 | 说明 |
|------|------|
| 2026-07-23 | 初版 → 历经 P0 过滤/`my-*`、P1 三角写、Web 翻页、browseType、channel-matrix |
| 2026-07-23 | 瘦身：未完成项为主；P1 联调 checklist；P2 切入表；下一刀总裁决；与 cli-surface 去重 |
