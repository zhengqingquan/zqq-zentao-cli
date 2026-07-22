# CLI 命令面契约（cli-surface）

本文档是 **zqq-zentao** 的目标命令面与产品边界。实现以本文为准；与当前代码不一致处标为「待实现」。

接手开发请同时阅读 [handoff.md](./handoff.md)（待办勾选、已知坑、建议下一刀）。

## 定位

**用命令行全面操作禅道**：在账号权限允许的前提下，覆盖组织内任意对象的查询、创建、更新、删除与状态流转——**不限于当前登录人自己的待办**。

- `my-*`：当前用户的快捷入口（我的地盘）
- 范围列表 + 过滤：查**任何人**名下的任务/Bug/需求等（如 `--assignedTo alice`）
- CRUD / 动作：对任意有权限的对象执行写操作

## 已拍板的产品边界

| # | 决策 | 结论 |
|---|------|------|
| 1 | 写操作 | **放开写**：不只备注，含 create / update / delete / 状态动作 |
| 2 | 「我的」命名 | **`my-<noun> [--type …]`**，默认 type 为「指派给我」类 |
| 3 | 「我的」范围 | **更多**：覆盖我的地盘 work + contribute 常用模块，不限四个 |
| 4 | 与官方关系 | **本工具也做 CRUD**；官方 `zentao` 可并存，不互相推诿 |
| 5 | 查询主体 | **不限本人**：可查/可操作他人名下数据（受禅道权限约束）；`my-*` 只是快捷方式 |

通道策略（不变）：

- REST 结构化好 → 优先 REST
- REST 要强制 scope / 过滤失效 / 「我的」列表 → **Web PATHINFO + zin dtable**
- 写操作：REST 有稳定 POST/PUT 则用 REST；否则走 Web 表单（与 `comment` 同模式）
- `capabilities.py` 声明每条能力的 `web` / `rest`；`auto` 按能力强制或启发式选择

---

## 命令约定

```text
# 会话
zqq-zentao login|whoami|ping

# 我的（仅当前登录账号；--type 切换视角）
zqq-zentao my-<noun> [--type <browseType>] [--page] [--limit]

# 范围浏览（任意对象；可加用户/字段过滤）
zqq-zentao <nouns> [scopes…] [--assignedTo|--openedBy|…] [--page] [--limit]
zqq-zentao <noun> <id>

# 按用户查（与 my-* 互补：指定 account，不限本人）
zqq-zentao tasks --assignedTo alice
zqq-zentao bugs --product 12 --assignedTo bob
zqq-zentao stories --project 5 --openedBy carol

# CRUD（对任意有权限的 id）
zqq-zentao <noun> create [--field=value…]
zqq-zentao <noun> update <id> [--field=value…]
zqq-zentao <noun> delete <id> [--yes]

# 状态 / 业务动作
zqq-zentao <noun> <action> <id> [--field=value…]

# 备注（跨对象）
zqq-zentao comment list|add|edit …
```

字段传入：`--key=value` 与/或 `--data='JSON'`（对齐官方习惯，便于 AI）。

写操作前：默认向用户确认；批量删除等可加 `--yes`。

### `my-*` vs 范围列表（必读）

| 场景 | 用什么 |
|------|--------|
| 我自己的待办 / 指派给我 | `my-tasks` / `my-bugs` / … |
| 某同事名下、某产品下、按字段筛选 | `tasks` / `bugs --product … --assignedTo …` 等 |
| 某个具体 ID | `task 123` / `bug 456` |

**禁止**把「查别人」做成扫全站 `my-*`；应走 **scope + 过滤**（或后续 `user <account> tasks` 类组合，若实现则写入本文）。

### 通用过滤（目标）

范围列表逐步支持与官方类似的过滤（名称以实机/REST 为准）：

| 参数 | 含义 | 状态 |
|------|------|------|
| `--assignedTo <account\|实名>` | 指派给某人（实名唯一则解析为账号） | ✅ `tasks` / `bugs` / `stories` |
| `--openedBy <account\|实名>` | 由某人创建 | ✅ `bugs` / `stories`；`tasks` 需配合 `-e` 或同时 `--assignedTo` |
| `--finishedBy` / `--resolvedBy` / `--closedBy` | 完成/解决/关闭人 | ⏳ |
| `--status` | 状态（逗号分隔多值，如 `wait,doing`） | ✅ `tasks` / `bugs` / `stories` |
| `--pri` / `--severity` | 优先级等 | ⏳ |
| `--search` | 关键词（`users --search` 按账号/姓名/拼音） | ✅ `users`；其它名词 ⏳ |
| `--pick` | 摘取字段（全局，逗号分隔） | ✅ |

说明：

- `tasks --assignedTo`：先姓名→账号解析，再 REST `GET /tasks?search=1&assignedTo=…`，客户端校对；可加 `--status`
- `bugs` / `stories`：在 scope 下列全量后客户端过滤（服务端 query 不可靠）
- `tasks --openedBy` 单独使用时请加 `-e <executionId>`（全局 search 无 openedBy 字段）
- 鉴权日志（`auth: rest-token(...)` 等）打在 **stderr**，勿与 stdout JSON 混用

---

## A. 会话 / 系统

| 命令 | 状态 | 通道 | 说明 |
|------|------|------|------|
| `login` | ✅ | web+rest | 同时缓存 Cookie 与 Token |
| `whoami` | ✅ | web/rest | |
| `ping` | ✅ | rest | |
| `langs` / `views` / `groups` / `tabs` / `options` | ✅ 只读 | rest | 低频，保留 |
| `configurations` / `configuration` / `required-fields` | ✅ 只读 | rest | 低频 |

---

## B. 我的地盘 `my-*`（仅当前登录用户的快捷入口）

> **不是**查别人的入口。查同事请用 C 节范围列表 + `--assignedTo` 等过滤。

路径模式（ZenTao 22.3）：

- 工作：`/my-work-{mode}-{browseType}.html?zin=1`
- 贡献：`/my-contribute-{mode}-{browseType}.html?zin=1`
- 待办：对齐 `my::todo`（PATHINFO 以源码/实机为准）

| 命令 | 默认 `--type` | 其它常用 type | 状态 | 通道倾向 |
|------|---------------|---------------|------|----------|
| `my-tasks` | `assignedTo` | work: —；contribute: `openedBy` `finishedBy` `myInvolved` `closedBy` `canceledBy` `assignedBy` | ✅ `--type`/`--scope` | web/rest（仅默认 work+assignedTo 走 rest） |
| `my-bugs` | `assignedTo` | contribute: `openedBy` `resolvedBy` `closedBy` `assignedBy` | ✅ | **web** |
| `my-stories` | `assignedTo` | work: `reviewBy`；contribute: `openedBy` `reviewedBy` `closedBy` `assignedBy` | ✅ | web |
| `my-requirements` | `assignedTo` | 同 story + `reviewBy` | ⏳ | web |
| `my-epics` | `assignedTo` | 同 requirement | ⏳ | web |
| `my-todos` | `all` | `undone` `future` `today` `thisWeek` `thisMonth` | ✅ | web |
| `my-testcases` | `assigntome` | contribute: `openedbyme` | ✅ | web |
| `my-testtasks` | `assignedTo` | work: `wait`；contribute: `done` | ✅ | web |
| `my-feedbacks` | `assigntome` | work: `assignedby`；contribute: `openedbyme` | ✅ | web |
| `my-tickets` | `assignedtome` | contribute: `openedbyme` | ✅ | web |
| `my-docs` | `openedbyme` | `editedbyme` | ⏳ | web |
| `my-projects` | `doing` | 按 my::project | ⏳ | web |
| `my-executions` | `undone` | 按 my::execution | ⏳ | web |
| `my-issues` | `assignedTo` | （非 open 版可能有） | ⏳ 可选 | web |
| `my-risks` | `assignedTo` | 可选 | ⏳ 可选 | web |
| `my-meetings` | `futureMeeting` | 可选 | ⏳ 可选 | web |

实现要点：

- 注册表：`src/web/my_pages.py`；共用 `fetch_dtable_list` + `*_shape` / `my_shape`
- CLI：`my-<noun> [--type …] [--scope work|contribute]`（todos 无 `--scope`）
- `capabilities`：多数 **仅 web**；`my-tasks` 默认双通道，其它 type 强制 web（`my-page`）
- 空列表：有 dtable 且 `data:[]` 视为成功（0 条）

---

## C. 范围浏览（列表 / 详情）— 任意有权限对象

保持现有复数/单数与 registry scope；**列表目标支持按用户/字段过滤**（见上文「通用过滤」）。

| 列表 | 详情 | 列表 scope |
|------|------|------------|
| `programs` | `program` | — |
| `products` | `product` | 可选 `--program` |
| `projects` | `project` | 可选 `--program` `--product` |
| `executions` | `execution` | 可选 `--project` |
| `users` | `user` | — |
| `departments` | `department` | — |
| `stories` | `story` | **必填** product/project/execution |
| `bugs` | `bug` | **必填** 同上 |
| `productplans` | `productplan` | **必填** `--product` |
| `releases` | `release` | **必填** product 或 project |
| `builds` | `build` | **必填** project 或 execution |
| `testcases` | `testcase` | **必填** scope |
| `testsuites` | `testsuite` | **必填** `--product` |
| `testtasks` | `testtask` | 可选 `--project` |
| `feedbacks` | `feedback` | — |
| `tickets` | `ticket` | — |
| `todos` | `todo` | — |
| `issues` | `issue` | 可选 |
| `risks` | `risk` | 可选 |
| `meetings` | — | **必填** `--project` |
| `doclibs` / `docs` | `doc` | docs **必填** `--lib` |
| `file` | `file` | 仅详情 |
| `modules` | — | **必填** `--type` `--id` |
| `story-grades` | — | 可选 query |
| `stakeholders` | — | **必填** `--program` |

任务便捷（已有）：

| 命令 | 状态 | 通道 |
|------|------|------|
| `tasks` | ✅ | 仅 rest（无 `-e`） |
| `tasks -e` | ✅ | web/rest |
| `task <id>` | ✅ | web/rest |

约定：**「某产品下 Bug」用 `bugs --product`；「我的 Bug」用 `my-bugs`。**

---

## D. CRUD 与状态动作 — 目标面（⏳ 为主）

模块命令形态对齐官方：`zqq-zentao <noun> create|update|delete|<action>`。

下列「本项目」列：✅ 已有只读；⏳ 写/动作待做。通道以 REST 文档为准，缺失则 Web。

### D1. 核心业务（优先实现写）

| 模块 | 列表/详情 | create / update / delete | 动作 |
|------|-----------|--------------------------|------|
| `task` | ✅ | ✅ REST（`task create\|update\|delete`，需 `--execution` 创建） | ✅ `start` `finish` `close` `activate` `assign` |
| `bug` | ✅ | ✅ REST（`bug create\|update\|delete`，需 `--product` 创建） | ✅ `confirm` `resolve` `close` `activate` `assign` |
| `story` | ✅ | ⏳ | ⏳ `change` `close` `activate` `review` … |
| `requirement` / `epic` | ⏳ 列表可并入 story 族或独立 | ⏳ | ⏳ 同 story |
| `todo` | ✅ | ⏳ | ⏳ 按禅道 todo 动作 |
| `feedback` | ✅ | ⏳ | ⏳ `activate` `close` … |
| `ticket` | ✅ | ⏳ | ⏳ `activate` `close` … |

### D2. 计划 / 版本 / 测试

| 模块 | 列表/详情 | CUD | 备注 |
|------|-----------|-----|------|
| `productplan` | ✅ | ⏳ | link/unlink stories/bugs 可选 |
| `release` | ✅ | ⏳ | |
| `build` | ✅ | ⏳ | |
| `testcase` | ✅ | ⏳ | results 可选 |
| `testsuite` | ✅ | ⏳ | |
| `testtask` | ✅ | ⏳ | |

### D3. 组织对象（按需）

| 模块 | 列表/详情 | CUD |
|------|-----------|-----|
| `program` / `product` / `project` / `execution` | ✅ | ⏳（权限要求高，可二期） |
| `user` | ✅ | ⏳（谨慎；多环境只读即可） |

### D4. 备注（已有写）

| 命令 | 状态 | 通道 |
|------|------|------|
| `comment list\|add\|edit` | ✅ | **仅 web** |

---

## E. 实现分期（建议）

### P0 — 契约、「我的」与「查别人」过滤

1. ✅ 本文档落地；README / skill 指向本文  
2. ✅ `my-*` 扩展：`stories` `todos` `testcases` `testtasks` `feedbacks` `tickets` + 各命令 `--type`  
3. ✅ `my-tasks` / `my-bugs` 支持 `--type` / `--scope`  
4. ✅ 范围列表：`tasks` / `bugs` / `stories` 支持 `--assignedTo` / `--openedBy`（及 `--status` / 姓名解析 / `--pick`）  

### P1 — 核心写路径

1. ✅ `bug`：create / update / delete / confirm / resolve / close / activate / assign（REST）  
2. ✅ `task`：create / update / delete / start / finish / close / activate / assign（REST）  
3. `story`：create / update / close / activate / change  

写前确认 + `--yes`（非 TTY 必须带 `--yes`）。优先 REST；不通则 Web。

### P2 — 其余 CUD + 组织对象

计划/发布/版本/测试/反馈/工单；program/product/project/execution 按需。

### P3 — 体验

- ✅ Web `my-*` 注册表化（`web/my_pages.py`）
- 双通道失败降级（可选）
- 分页：Web 大 `recPerPage` / 翻页拉全（my-*、execution tasks 已实现）
- 用户表本地短缓存（姓名解析）

---

## F. 现状速查（相对本文）

| 类别 | 进度 |
|------|------|
| 会话 / 只读浏览 registry | 大部分 ✅ |
| `my-tasks` / `my-bugs` + `--type`/`--scope` | ✅ |
| 其它 `my-*`（stories/todos/test…） | ✅（epic/requirement/docs 等仍 ⏳） |
| CRUD / 状态动作 | bug/task ✅ REST；story 等 ⏳；`comment` 写 ✅ |
| 文档宣称「做 CRUD」 | ⏳ → 随本文与 README 同步 |

---

## G. 非目标（仍排除）

- 不替换禅道 Web UI 全部交互（复杂审批流、可视化看板等）
- 不在日志/对话中打印 Cookie、密码、Token
- 不默认自动 `git push` / 不提交密钥文件

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-07-23 | 初版：边界拍板（放开写、`my-* --type`、更多我的、本工具做 CRUD） |
| 2026-07-23 | 补充定位：全面 CLI；不限本人；`my-*` 与 scope+过滤分工 |
| 2026-07-23 | P0-B：`my_pages` 注册表；多 my-* + `--type`/`--scope` |
