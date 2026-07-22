# 禅道 REST API v1（22.3）

从源码 `zentao/zentao-22.3-php8.1/zentaopms` 整理：路由见 `config/apiv1.php`，实现见 `api/v1/entries/*.php`。
本项目 REST 通道（`src/rest/`）基址为 `{server}/api.php/v1`。

Web PATHINFO 接口见 [zentao-apis.md](./zentao-apis.md)。

## 公共约定

| 项 | 说明 |
|----|------|
| Base URL | `{server}/api.php/v1` |
| 鉴权 | 请求头 `Token: <session_id>`（`POST /tokens` 返回）；框架用 `HTTP_TOKEN` 恢复 API session |
| Body | `POST`/`PUT` 为 JSON（`Content-Type: application/json`） |
| 分页 | 常见查询参数：`page`、`limit`、`total`、`order`；列表响应常含 `page`/`total`/`limit` + 资源数组 |
| 未登录 | 多数 entry 继承 `entry`，未登录返回 **401 Unauthorized**；`tokens` 继承 `baseEntry`，无需 Token |
| CORS | 允许头含 `Token`、`Authorization` |
| 源码版本 | ZenTao **22.3**（`zentaopms/VERSION`） |

### 登录换票

```http
POST /api.php/v1/tokens
Content-Type: application/json

{"account":"admin","password":"your-password"}
```

成功约 **201**：`{"token":"<session_id>"}`。也可用 `authKey`（IM 无密码登录，见 `tokens.php`）。

后续请求：

```http
GET /api.php/v1/tasks?page=1&limit=20
Token: <session_id>
Accept: application/json
```

### 本项目已接入（REST）

只读模块由 `src/rest/resources.py` 注册表驱动（复数列表 / 单数详情 + scopes）。

| Method | Path | CLI / 用途 |
|--------|------|------------|
| POST | `/tokens` | login（换 Token） |
| GET | `/user` | whoami |
| GET | `/tasks` | tasks / my-tasks |
| GET | `/executions/:id/tasks` | tasks -e |
| GET | `/tasks/:id` | task <id> |
| GET | 见下方完整清单「本项目」列 | `products`/`stories`/`bugs`/… 等只读子命令 |

> 备注（comment）在路由表有 `/comments`，但开源包 **无** `comments.php` entry，故本工具走 Web PATHINFO，见 [zentao-apis.md](./zentao-apis.md)。
> 本批 **仅 GET**；写操作与缺 entry 路由未接。


### 任务列表要点（接入参考）

| 请求 | 行为（源码 `tasks.php`） |
|------|--------------------------|
| `GET /tasks` | 默认「我的任务」。开源 `tasks.php` 调 `my->task` **参数错位**（`page`→`recPerPage`），本工具用 query 绕过并一次拉全；`tasks --page/--limit` 在客户端切片 |
| `GET /executions/{id}/tasks` | 某执行下任务；`status` 默认 `all`；默认 `limit=100` |
| `GET /tasks?search=1&…` | 条件搜索：`pri`/`assignedTo`/`status`/`id`/`name`（及对应 List 参数） |
| `POST /executions/{id}/tasks` | 创建任务；必填约 `name,assignedTo,type,estStarted,deadline` |
| `GET/PUT/DELETE /tasks/{id}` | 详情 / 编辑 / 删除 |
| `POST /tasks/{id}/start` 等 | 状态流转：assignto / start / pause / restart / finish / close / active / estimate |

---

## 完整路由清单

Methods 从对应 `api/v1/entries/<entry>.php` 的 `get`/`post`/`put`/`delete` 扫描；`?` 表示路由已声明但本开源包缺少 entry 文件（可能企业版或未发布）。

### 认证与系统

| Method | Path | 说明 | Entry | 本项目 |
|--------|------|------|-------|--------|
| POST | `/tokens` | 获取 Token（登录） | `tokens` | `login（换 Token）` |
| GET | `/ping` | 心跳 | `ping` | `ping` |
| GET | `/langs` | 语言包 | `langs` | `langs` |
| GET | `/views` | 视图 | `views` | `views` |
| GET | `/groups` | 用户组 | `groups` | `groups` |
| GET | `/tabs/:module` | 标签页 | `tabs` | `tabs` |
| GET | `/options/:type` | 选项（下拉等） | `options` | `options` |
| GET | `/configurations` | 配置列表 | `configs` | `configurations` |
| GET | `/configurations/:name` | 配置项 | `config` | `configuration <id>` |
| GET | `/requiredFields` | 必填字段 | `requiredfields` | `required-fields` |
| ? | `/comments` | 备注 | `comments` |  |

### 用户与组织

| Method | Path | 说明 | Entry | 本项目 |
|--------|------|------|-------|--------|
| GET,POST | `/users` | 用户列表/创建 | `users` | `users` |
| GET,PUT,DELETE | `/users/:id` | 用户详情/当前用户 | `user` | `user <account>` |
| GET,PUT,DELETE | `/user` | 用户详情/当前用户 | `user` | `whoami` |
| GET | `/departments` | 部门列表 | `departments` | `departments` |
| GET,PUT,DELETE | `/departments/:id` | 部门详情 | `department` | `department <id>` |

### 项目集 / 产品 / 项目 / 执行

| Method | Path | 说明 | Entry | 本项目 |
|--------|------|------|-------|--------|
| GET,POST | `/programs` | 项目集列表/创建 | `programs` | `programs` |
| GET,PUT,DELETE | `/programs/:id` | 项目集详情/更新/删除 | `program` | `program <id>` |
| GET,POST | `/programs/:id/products` | 产品列表/创建 | `products` | `products --program` |
| GET,POST | `/programs/:id/projects` | 项目列表/创建 | `projects` | `projects --program` |
| GET,POST | `/programs/:id/stakeholders` | 干系人 | `stakeholders` | `stakeholders --program` |
| GET,POST | `/products` | 产品列表/创建 | `products` | `products` |
| GET,PUT,DELETE | `/products/:id` | 产品详情/更新/删除 | `product` | `product <id>` |
| GET,PUT,DELETE | `/product/:id` | 产品详情/更新/删除 | `product` | `product <id>` |
| ? | `/productlines` | 产品线列表 | `productLines` |  |
| ? | `/productlines/:id` | 产品线详情 | `productLine` |  |
| GET,POST | `/products/:id/projects` | 产品下项目 | `productProjects` | `projects --product` |
| GET,POST | `/projects` | 项目列表/创建 | `projects` | `projects` |
| GET,PUT,DELETE | `/projects/:id` | 项目详情/更新/删除 | `project` | `project <id>` |
| GET,POST | `/projects/:id/executions` | 执行列表/创建 | `executions` |  |
| GET,POST | `/executions` | 执行列表/创建 | `executions` | `executions` |
| GET,PUT,DELETE | `/executions/:id` | 执行详情/更新/删除 | `execution` | `execution <id>` |
| ? | `/executions/:id/members` | 执行成员 | `executionMembers` |  |

### 任务

| Method | Path | 说明 | Entry | 本项目 |
|--------|------|------|-------|--------|
| GET,POST | `/tasks` | 任务列表/创建 | `tasks` | `tasks / my-tasks` |
| GET,POST | `/executions/:id/tasks` | 任务列表/创建 | `tasks` | `tasks -e` |
| GET,PUT,DELETE | `/tasks/:id` | 任务详情/更新/删除 | `task` | `task <id>` |
| POST | `/executions/:id/tasks/batchCreate` | 批量创建任务 | `taskBatchCreate` |  |
| POST | `/tasks/batchCreate` | 批量创建任务 | `taskBatchCreate` |  |
| POST | `/tasks/:id/assignto` | 指派任务 | `taskAssignTo` |  |
| POST | `/tasks/:id/start` | 开始任务 | `taskStart` |  |
| POST | `/tasks/:id/pause` | 暂停任务 | `taskPause` |  |
| POST | `/tasks/:id/restart` | 继续任务 | `taskRestart` |  |
| POST | `/tasks/:id/finish` | 完成任务 | `taskFinish` |  |
| POST | `/tasks/:id/close` | 关闭任务 | `taskClose` |  |
| GET,POST | `/tasks/:id/estimate` | 任务记工时 | `taskRecordEstimate` |  |
| POST | `/tasks/:id/active` | 激活任务 | `taskActive` |  |

### 需求

| Method | Path | 说明 | Entry | 本项目 |
|--------|------|------|-------|--------|
| GET,POST | `/stories` | 需求列表/创建 | `stories` |  |
| GET,POST | `/products/:id/stories` | 需求列表/创建 | `stories` | `stories --product`；`story create --product` |
| GET | `/projects/:id/stories` | 项目下需求 | `projectStories` | `stories --project` |
| GET | `/executions/:id/stories` | 执行下需求 | `executionStories` | `stories --execution` |
| GET,PUT,DELETE | `/stories/:id` | 需求详情/更新/删除 | `story` | `story <id>`；`story update\|delete <id>` |
| POST | `/stories/:id/change` | 变更需求 | `storyChange` | `story change <id>` |
| POST | `/stories/:id/close` | 关闭需求 | `storyClose` | `story close <id>` |
| POST | `/stories/:id/active` | 激活需求 | `storyActive` | `story activate <id>` |
| POST | `/stories/:id/assign` | 指派需求 | `storyAssignto` | `story assign <id>` |
| GET,POST | `/stories/:id/estimate` | 需求估时 | `storyRecordEstimate` |  |
| DELETE | `/stories/:id/recall` | 撤销评审 | `storyRecall` | `story recall <id>` |
| POST | `/stories/:id/review` | 评审需求 | `storyReview` | `story review <id>` |
| POST | `/stories/:id/submitreview` | 提交评审 | `storySubmitReview` | `story submitreview <id>` |
| GET | `/storyreviewerrequired/:type` | 评审人是否必填 | `storyreviewerrequired` |  |
| GET | `/storygrades` | 需求层级/级别 | `storygrade` | `story-grades` |

### Bug

| Method | Path | 说明 | Entry | 本项目 |
|--------|------|------|-------|--------|
| GET,POST | `/bugs` | Bug 列表/创建 | `bugs` |  |
| GET,POST | `/products/:id/bugs` | Bug 列表/创建 | `bugs` | `bugs --product` |
| GET | `/projects/:id/bugs` | 项目下 Bug | `projectBugs` | `bugs --project` |
| GET | `/executions/:id/bugs` | 执行下 Bug | `executionBugs` | `bugs --execution` |
| GET,PUT,DELETE | `/bugs/:id` | Bug 详情/更新/删除 | `bug` | `bug <id>` |
| POST | `/bugs/:id/close` | 关闭 Bug | `bugClose` |  |
| POST | `/bugs/:id/assign` | 指派 Bug | `bugAssign` |  |
| POST | `/bugs/:id/confirm` | 确认 Bug | `bugConfirm` |  |
| POST | `/bugs/:id/resolve` | 解决 Bug | `bugResolve` |  |
| POST | `/bugs/:id/active` | 激活 Bug | `bugActive` |  |
| GET,POST | `/bugs/:id/estimate` | Bug 记工时 | `bugRecordEstimate` |  |

### 产品计划 / 发布 / 版本

| Method | Path | 说明 | Entry | 本项目 |
|--------|------|------|-------|--------|
| GET,POST | `/productplans` | 产品计划列表/创建 | `productPlans` |  |
| GET,POST | `/products/:id/plans` | 产品计划列表/创建 | `productPlans` | `productplans --product` |
| GET,PUT,DELETE | `/productplans/:id` | 产品计划详情/更新/删除 | `productPlan` | `productplan <id>` |
| POST | `/productplans/:id/linkstories` | 计划关联需求 | `productPlanLinkStories` |  |
| POST | `/productplans/:id/unlinkstories` | 计划取消关联需求 | `productPlanUnlinkStories` |  |
| POST | `/productplans/:id/linkbugs` | 计划关联 Bug | `productPlanLinkBugs` |  |
| POST | `/productplans/:id/unlinkbugs` | 计划取消关联 Bug | `productPlanUnlinkBugs` |  |
| GET | `/releases` | 发布列表/创建 | `releases` |  |
| GET | `/products/:id/releases` | 发布列表/创建 | `releases` | `releases --product` |
| GET,POST | `/projects/:id/releases` | 项目下发布列表 | `projectReleases` | `releases --project` |
| GET,PUT,DELETE | `/releases/:id` | 发布详情/更新/删除 | `release` | `release <id>` |
| GET,POST | `/builds` | 版本列表/创建 | `builds` |  |
| GET,POST | `/projects/:id/builds` | 版本列表/创建 | `builds` | `builds --project` |
| GET | `/executions/:id/builds` | 执行下版本 | `executionBuilds` | `builds --execution` |
| GET,PUT,DELETE | `/builds/:id` | 版本详情/更新/删除 | `build` | `build <id>` |

### 测试

| Method | Path | 说明 | Entry | 本项目 |
|--------|------|------|-------|--------|
| GET,POST | `/testcases` | 用例列表/创建 | `testcases` |  |
| GET,POST | `/products/:id/testcases` | 用例列表/创建 | `testcases` | `testcases --product` |
| GET | `/projects/:id/testcases` | 项目下用例 | `projectCases` | `testcases --project` |
| GET | `/executions/:id/testcases` | 执行下用例 | `executionCases` | `testcases --execution` |
| GET,PUT,DELETE | `/testcases/:id` | 用例详情/更新/删除 | `testcase` | `testcase <id>` |
| GET,POST | `/testcases/:id/results` | 用例执行结果 | `testresults` |  |
| GET,POST | `/testsuites` | 套件列表/创建 | `testsuites` |  |
| GET,POST | `/products/:id/testsuites` | 套件列表/创建 | `testsuites` | `testsuites --product` |
| GET,DELETE | `/testsuites/:id` | 套件详情/更新/删除 | `testsuite` | `testsuite <id>` |
| GET,POST | `/testtasks` | 测试单列表/创建 | `testtasks` | `testtasks` |
| GET,POST | `/projects/:projectID/testtasks` | 测试单列表/创建 | `testtasks` | `testtasks --project` |
| GET,DELETE | `/testtasks/:id` | 测试单详情/更新/删除 | `testtask` | `testtask <id>` |

### 反馈 / 工单 / 待办

| Method | Path | 说明 | Entry | 本项目 |
|--------|------|------|-------|--------|
| GET,POST | `/feedbacks` | 反馈列表/创建 | `feedbacks` | `feedbacks` |
| GET,PUT,DELETE | `/feedbacks/:id` | 反馈详情/更新/删除 | `feedback` | `feedback <id>` |
| GET,POST | `/feedbacks/:id/assign` | 反馈指派 | `feedbackAssignto` |  |
| POST | `/feedbacks/:id/close` | 关闭反馈 | `feedbackClose` |  |
| GET,POST | `/tickets` | 工单列表/创建 | `tickets` | `tickets` |
| GET,PUT,DELETE | `/tickets/:id` | 工单详情/更新/删除 | `ticket` | `ticket <id>` |
| ? | `/tickets/:id/assign` | 工单指派 | `ticketAssignto` |  |
| ? | `/tickets/:id/close` | 关闭工单 | `ticketClose` |  |
| GET,POST | `/todos` | 待办列表/创建 | `todos` | `todos` |
| GET,PUT,DELETE | `/todos/:id` | 待办详情/更新/删除 | `todo` | `todo <id>` |
| GET | `/todos/:id/finish` | 完成待办 | `todoFinish` |  |
| GET | `/todos/:id/activate` | 激活待办 | `todoActivate` |  |

### 问题 / 风险 / 会议

| Method | Path | 说明 | Entry | 本项目 |
|--------|------|------|-------|--------|
| GET,POST | `/issues` | 问题列表/创建 | `issues` | `issues` |
| GET | `/products/:id/issues` | 产品下问题 | `productIssues` | `issues --product` |
| GET,POST | `/projects/:id/issues` | 问题列表/创建 | `issues` | `issues --project` |
| GET,PUT,DELETE | `/issues/:id` | 问题详情/更新/删除 | `issue` | `issue <id>` |
| GET,POST | `/risks` | 风险列表/创建 | `risks` | `risks` |
| GET,POST | `/projects/:projectID/risks` | 风险列表/创建 | `risks` | `risks --project` |
| GET,PUT,DELETE | `/risks/:id` | 风险详情/更新/删除 | `risk` | `risk <id>` |
| GET,POST | `/meetings` | 会议列表/创建 | `meetings` |  |
| GET,POST | `/projects/:id/meetings` | 会议列表/创建 | `meetings` | `meetings --project` |
| ? | `/meetings/:id` | 会议详情/更新/删除 | `meeting` |  |

### 文档 / 附件 / 模块

| Method | Path | 说明 | Entry | 本项目 |
|--------|------|------|-------|--------|
| GET | `/doclibs` | 文档库列表 | `doclibs` | `doclibs` |
| GET | `/doclibs/:id` | 文档列表/创建 | `docs` | `docs --lib` |
| GET | `/docs` | 文档列表/创建 | `docs` |  |
| GET,PUT,DELETE | `/docs/:id` | 文档详情/更新/删除 | `doc` | `doc <id>` |
| POST | `/files` | 附件列表/上传 | `files` |  |
| GET,PUT | `/files/:id` | 附件详情/删除 | `file` | `file <id>` |
| GET | `/modules` | 模块树 | `modules` | `modules` |

### DevOps / CI / 网盘

| Method | Path | 说明 | Entry | 本项目 |
|--------|------|------|-------|--------|
| GET | `/repos` | 代码库 | `repos` |  |
| GET | `/repos/rules` | 代码库规则 | `reporules` |  |
| GET | `/jobs` | 流水线任务 | `jobs` |  |
| POST | `/mr` | 合并请求 | `mr` |  |
| GET | `/reports` | 报表 | `reports` |  |
| POST | `/host/heartbeat` | 主机心跳 | `hostHeartbeat` |  |
| POST | `/host/submitResult` | 主机结果提交 | `hostSubmit` |  |
| POST | `/ztf/submitResult` | ZTF 结果提交 | `ztfSubmit` |  |
| POST | `/gitlab/webhook` | GitLab Webhook | `gitlabWebhook` |  |
| POST | `/ciresults` | CI 结果 | `ciresults` |  |
| GET | `/z/folders` | 网盘目录列表 | `zfolders` |  |
| GET | `/z/folders/:id` | 网盘目录 | `zfolder` |  |
| GET | `/z/files/:id` | 网盘文件 | `zfile` |  |
| GET | `/z/files/:id/content` | 网盘文件内容 | `zfileContent` |  |

---

## 缺失 entry（路由有、实现无）

| Path | 声明 Entry |
|------|------------|
| `/comments` | `comments` |
| `/tickets/:id/assign` | `ticketAssignto` |
| `/tickets/:id/close` | `ticketClose` |
| `/productlines` | `productLines` |
| `/productlines/:id` | `productLine` |
| `/executions/:id/members` | `executionMembers` |
| `/meetings/:id` | `meeting` |

接入时勿依赖这些路径，除非目标禅道版本/版本版别已提供对应 entry。

## 源码索引

| 文件 | 作用 |
|------|------|
| `www/api.php` | API 入口 |
| `config/apiv1.php` | v1 路由表（本文档依据） |
| `config/apiv2.php` | v2 路由（另一套；本工具未用） |
| `api/v1/entries/*.php` | v1 业务实现 |
| `framework/api/router.class.php` | 解析 `/api.php/v1/...` 并调度 entry |
| `framework/base/router.class.php` | `HTTP_TOKEN` → session |

统计：路由 **142** 条；本工具 REST 只读由注册表驱动 CLI（`SPECIAL_CMDS` 仅保留 login/whoami/tasks/comment 等特例）。写操作与缺 entry 路由未接。
