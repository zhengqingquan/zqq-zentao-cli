# 通道选择矩阵（REST vs Web）

面向接手开发 / Agent：回答 **「什么时候该用 REST，什么时候 Web 更方便」**，以及 **怎么继续挖缺口**。

命令契约见 [cli-surface.md](./cli-surface.md)；待办见 [handoff.md](./handoff.md)。  
REST 路径：[zentao-rest-apiv1.md](./zentao-rest-apiv1.md)（v1，本工具在用）、[zentao-rest-apiv2.md](./zentao-rest-apiv2.md)（v2，未接入）。  
运行时裁决在 `src/capabilities.py`；「我的」Web 注册表在 `src/web/my_pages.py`。

**禅道版本**：以本地 22.3 源码为准（`…/zentaopms`，只读）。  
**更新日期**：2026-07-23

---

## 1. 决策规则（短）

| 优先 | 条件 |
|------|------|
| **REST** | 结构化 CRUD / 详情 / 带稳定 path 的范围列表；写动作有 entry（`bugresolve`、`taskstart`…） |
| **Web** | 「我的地盘」列表；备注；REST 强制 scope 且无「我的」等价物；高级搜索 / Session 查询；browseType 视角且 REST 未暴露 |
| **REST + browseType** | 产品/项目/执行下列表：`status` query = browseType（本人可用 `assigntome` 等），见 `src/rest/browse_filter.py` |
| **REST + 客户端滤** | 查**他人** `assignedTo`/`openedBy`（bugs/stories）：无任意账号 REST 过滤 → 拉全量再滤（大产品慢） |

`auto`：有 Token 偏 rest；能力仅 web/仅 rest 时强制对应通道。

---

## 2. 怎么继续找出「REST 不便、Web 方便」

对每个场景做三步对照（不要凭记忆）：

1. **Web**：`module/<name>/control.php` 的 public 方法 → PATHINFO `/{module}-{method}-….html`；「我的」看 `module/my/control.php`（`work`/`contribute`/`todo`/…）。
2. **REST**：`config/apiv1.php` 路由 + `api/v1/entries/<entry>.php` 的 `get()`/`post()`：实际调用了哪个 control、吃哪些 `param`。
3. **判定**：REST 能否无损表达同一过滤/范围？  
   - 不能 → 记入下表「偏 Web」  
   - 能但参数语义怪异（如 `status`=browseType）→ 记「REST 可用，注意语义」并在 CLI 做映射

**不方便信号**（出现即值得开一行）：

- 无全局 / 无「我的」列表，强制 `--product` 等 scope  
- query 名在但服务端忽略，或语义≠字段（`status`≠行状态）  
- 只能「指派给我」，不能「指派给 alice」  
- 依赖 Session 搜索（`bysearch` + queryID）  
- 分页参数错位、要 workaround  

实机探针：同一意图各打一枪——REST 带疑似 query；Web 对应 PATHINFO + `?zin=1` 看 dtable 是否已是目标子集。

查阅目录表见 [`.cursor/rules/zentao-source-lookup.mdc`](../.cursor/rules/zentao-source-lookup.mdc)。

---

## 3. 场景矩阵（本 CLI 已核对）

图例：✅ 已用该通道 · ⚠ 能用但有坑 · ❌ 不宜/缺失 · ⏳ 契约有、CLI 未做

### 3.1 「我的」列表

| 场景 | Web | REST | CLI 结论 |
|------|-----|------|----------|
| 我的任务（指派给我） | `/my-work-task-assignedTo-…` | `GET /tasks`（默认像我的） | ✅ 双通道；默认可 rest |
| 我的任务（其它 type） | contribute / 其它 browseType | 无稳定对等 | ✅ **仅 web**（`my-page`） |
| 我的 Bug | `/my-work-bug-assignedTo-…` | **无**全局 my-bugs | ✅ **仅 web** |
| 我的需求/评审 | `/my-work-story-…` | 无全局 my-stories | ✅ **仅 web** |
| 我的待办 | `/my-todo-…` | 列表 REST 有，非「我的」页语义 | ✅ **仅 web** |
| 我的用例/测试单/反馈/工单 | my-work / contribute | 无对等「我的」列表 | ✅ **仅 web** |
| 我的用户需求/史诗/文档/项目/执行 | `my::requirement` 等 | 无对等 my-* | ⏳ 扩 `my_pages.py`（偏 **web**） |

### 3.2 范围列表 + 按人过滤

| 场景 | Web | REST | CLI 结论 |
|------|-----|------|----------|
| 任务：查任意人 | 执行下任务页 + 滤 | `GET /tasks?search=1&assignedTo=` | ✅ **rest**（search） |
| 任务：仅 `--openedBy` | 执行页 | search **无** openedBy | ⚠ 须 `-e` 或同时 `--assignedTo` |
| 执行下任务列表 | `execution-task-…` | `/executions/:id/tasks` | ✅ 双通道；Web 已翻页拉全 |
| Bug：产品下指派**给我** | browse `assigntome` | `status=assigntome` | ✅ **rest**（browseType 映射） |
| Bug：产品下指派给**他人** | 高级搜索 / 客户端 | **无**任意账号过滤 | ⚠ **客户端全量滤**（慢）；stderr 提示 |
| Bug：按行状态 active | browse `unresolved` | `status=unresolved` | ✅ 映射；勿把 `status` 当字段直传 |
| Story：同上 | `assignedtome` / `activestory`… | 同左（`status=`） | ✅ 同 bugs |
| users 关键词搜 | — | `/users` 无 search | ✅ **客户端扫**（`users --search`） |

### 3.3 写操作 / 备注

| 场景 | Web | REST | CLI 结论 |
|------|-----|------|----------|
| Bug/Task/Story CUD + 状态动作 | 表单 | 有稳定 entry | ✅ **rest** + `--yes` |
| 备注 list/add/edit | `action-ajaxGetList` / comment | `/comments` 弱或不适合本流程 | ✅ **仅 web** |
| 计划/测试/反馈等写 | 表单 | 部分有 entry | ⏳ P2；优先试 REST，不通再 Web |

### 3.4 会话

| 场景 | Web | REST | CLI 结论 |
|------|-----|------|----------|
| login | Cookie | Token | ✅ `auto` 两者都换 |
| whoami | Cookie 会话 | Token 资料 | ✅ 双通道 |
| 仅 Token、无 Cookie | — | 可读 REST | ⚠ `my-*` / `comment` 失败 → 需密码 login |

---

## 4. 源码锚点（22.3）

| 意图 | 路径（相对 `zentaopms/`） |
|------|---------------------------|
| 我的地盘 | `module/my/control.php` |
| Bug 产品列表 browseType | `module/bug/tao.php` `getListByBrowseType`；REST `api/v1/entries/bugs.php`（`status`→browse） |
| Story 产品列表 | `module/product/model.php` `getStories`；REST `stories.php` |
| 任务 search | `api/v1/entries/tasks.php`；CLI `rest/tasks.py` |
| 备注 | `module/action/control.php` |
| REST 路由表 | `config/apiv1.php` |

---

## 5. 维护约定

- 新发现「REST 坑 / Web 捷径」：**先改本表**，再改 `capabilities` / `my_pages` / `browse_filter`，并在 [handoff.md](./handoff.md) 已知坑补一行。  
- 已实现通道以 `zqq-zentao -h` 与 `capabilities.py` 为准；本文「结论」列与代码冲突时以代码为准并回写本文。  
- 脱敏：表内示例账号用 `alice` / `bob`，勿写真实同事名。
