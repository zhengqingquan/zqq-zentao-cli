# 禅道 REST API v2（22.3）

从源码 `zentaopms/config/apiv2.php` **全文**整理。基址 `{server}/api.php/v2`。调度见 `framework/api/router.class.php`（`apiVersion == v2` → `routeV2`）。

与 [zentao-rest-apiv1.md](./zentao-rest-apiv1.md)（**v1**）对照：v2 **没有** `api/v2/entries/`，多数路由 `redirect` 到 Web control，再用 `response` 从视图数据抽 JSON；常带 `search.enabled`。

**本工具 `zqq-zentao` 当前只用 v1，未接 v2。** 本文供对照 / 评估（如「我的」列表、服务端 search）。

Web PATHINFO 见 [zentao-apis.md](./zentao-apis.md)；通道选择见 [channel-matrix.md](./channel-matrix.md)。

## 公共约定

| 项 | 说明 |
|----|------|
| Base URL | `{server}/api.php/v2` |
| 鉴权 | 与 v1 同属 API 会话；通常亦用 `Token` 头（以实机为准） |
| 路由值 | PHP `array(...)`：`redirect` / `response` / `search` / 按方法的 `get`/`post`/`put`/`delete` |
| Method 列 | 写明 `GET,POST,…` 的为按方法拆分；`GET*` 表示路由未声明方法键，框架按 GET-only 处理（见 router 注释） |
| search | `search.enabled` 时可用禅道搜索（常依赖 Session / searchModule） |
| 源码版本 | ZenTao **22.3** |
| 核对日期 | 2026-07-23；路由条数与 `apiv2.php` 一致 |

## 完整路由清单

### 项目集

| Path | Method | redirect | response | 备注 |
|------|--------|----------|----------|------|
| `/programs` | GET* |  | programs(array),pager | search:yes |
| `/programs/:programID` | GET* | /programs/:programID/edit | program |  |
| `/programs/:programID/projects` | GET* | /programs/:programID/project | projectStats(array)\|projects,pager |  |
| `/programs/:programID/products` | GET* | /programs/:programID/product | products(array),pager |  |

### 产品 / 需求 / 计划 / 发布

| Path | Method | redirect | response | 备注 |
|------|--------|----------|----------|------|
| `/products` | GET* | /products/all |  |  |
| `/products/all` | GET* |  | productStats\|products,pager |  |
| `/products/browse` | GET* |  | stories,pager · stories(array),pager |  |
| `/products/:productID` | GET* |  | product,dynamics,members,branches,reviewers |  |
| `/products/:productID/stories` | GET* | /products/browse?productID=:productID |  | search:yes |
| `/stories/:storyID` | GET* |  | story,actions(array) |  |
| `/products/:productID/epics` | GET* | /products/browse?productID=:productID&storyType=epic | stories(array)\|epics,pager | search:yes |
| `/epics/:storyID` | GET* |  | story\|epic,actions(array) |  |
| `/products/:productID/requirements` | GET* | /products/browse?productID=:productID&storyType=requirement | stories(array)\|requirements,pager | search:yes |
| `/requirements/:storyID` | GET* |  | story\|requirement,actions(array) |  |
| `/products/:productID/productplans` | GET* | /productplans?productID=:productID | plans(array)\|productplans,pager | search:yes |
| `/productplans/:planID` | GET,PUT |  | plan\|productplan,actions(array) · * |  |
| `/products/:productID/releases` | GET* | /releases?productID=:productID | releases,pager | search:yes |
| `/releases/:releaseID` | GET* |  | release,actions(array) |  |
| `/products/:productID/bugs` | GET* | /bugs?productID=:productID | bugs(array),pager | search:yes |
| `/products/:productID/testcases` | GET* | /testcases?productID=:productID | cases(array)\|testcases,pager | search:yes (testcase) |
| `/products/:productID/testtasks` | GET* | /testtasks?productID=:productID | tasks(array)\|testtasks,pager |  |
| `/products/:productID/testreports` | GET* | /testreports?objectID=:productID | reports(array)\|testreports,pager |  |
| `/products/:productID/feedbacks` | GET* | /feedbacks?param=:productID |  | search:yes |
| `/products/:productID/tickets` | GET* | /tickets?param=:productID |  | search:yes |
| `/products/:productID/systems` | GET* | /systems?productID=:productID |  |  |

### 项目 / 执行 / 任务 / 版本

| Path | Method | redirect | response | 备注 |
|------|--------|----------|----------|------|
| `/projects/:projectID/stories` | GET* | /projectstories/story?projectID=:projectID | stories(array),pager | search:yes (projectstory) |
| `/executions/:executionID/stories` | GET* | /executions/story?executionID=:executionID |  | search:yes (executionStory) |
| `/projects/:projectID/releases` | GET* | /projectreleases?projectID=:projectID | releases,pager | search:yes (release) |
| `/projects` | GET* |  | projectStats\|projects,pager | search:yes |
| `/projects/list/:browseType` | GET* | /projects?browseType=:browseType |  |  |
| `/projects/execution` | GET* |  | executionStats\|executions,pager |  |
| `/projects/build` | GET* |  | builds,pager | search:yes (build) |
| `/projects/bug` | GET* |  | bugs,pager · bugs(array),pager | search:yes (bug) |
| `/projects/testcase` | GET* |  | cases(array)\|testcases,pager | search:yes (testcase) |
| `/projects/testtask` | GET* |  | tasks(array)\|testtasks,pager |  |
| `/projects/testreport` | GET* |  | reports(array)\|testreports,pager |  |
| `/projects/team` | GET* |  | teamMembers(array)\|members |  |
| `/projects/:projectID/members` | GET,PUT | /projects/team?projectID=:projectID · /projects/manageMembers?projectID=:projectID |  |  |
| `/projects/:projectID` | GET* |  | project |  |
| `/executions` | GET* |  | executionStats\|executions,pager | search:yes (execution) · method=all |
| `/projects/:projectID/executions` | GET* | /projects/execution?projectID=:projectID |  |  |
| `/executions/task` | GET* |  | tasks(array),pager |  |
| `/executions/story` | GET* |  | stories(array),pager |  |
| `/executions/build` | GET* |  | builds,pager | search:yes (build) |
| `/executions/bug` | GET* |  | bugs(array),pager | search:yes (bug) |
| `/executions/testcase` | GET* |  | cases(array)\|testcases,pager | search:yes (testcase) |
| `/executions/testtask` | GET* |  | tasks(array)\|testtasks,pager |  |
| `/executions/testreport` | GET* |  | reports(array)\|testreports,pager |  |
| `/executions/:executionID` | GET* |  | execution |  |
| `/executions/:executionID/tasks` | GET* | /executions/task?executionID=:executionID |  |  |
| `/tasks/:taskID` | GET* |  | task,actions(array) |  |
| `/projects/:projectID/builds` | GET* | /projects/build?projectID=:projectID |  | search:yes (build) |
| `/executions/:executionID/builds` | GET* | /executions/build?executionID=:executionID |  | search:yes (build) |
| `/builds/:buildID` | GET* |  | build,actions(array) |  |
| `/projects/:projectID/bugs` | GET* | /projects/bug?projectID=:projectID |  | search:yes (projectBug) |
| `/executions/:executionID/bugs` | GET* | /executions/bug?executionID=:executionID |  | search:yes (executionBug) |
| `/projects/:projectID/testcases` | GET* | /projects/testcase?projectID=:projectID |  | search:yes (testcase) |
| `/executions/:executionID/testcases` | GET* | /executions/testcase?executionID=:executionID |  | search:yes (testcase) |
| `/projects/:projectID/testtasks` | GET* | /projects/testtask?projectID=:projectID |  |  |
| `/executions/:executionID/testtasks` | GET* | /executions/testtask?executionID=:executionID |  |  |
| `/projects/:projectID/testreports` | GET* | /projects/testreport?projectID=:projectID |  |  |
| `/executions/:executionID/testreports` | GET* | /executions/testreport?executionID=:executionID |  |  |
| `/projects/:projectID/issues` | GET* | /issues?objectID=:projectID |  | search:yes |
| `/executions/:executionID/issues` | GET* | /issues?objectID=:executionID&from=execution |  | search:yes |
| `/projects/:projectID/risks` | GET* | /risks?projectID=:projectID |  | search:yes |
| `/executions/:executionID/risks` | GET* | /risks?executionID=:executionID&from=execution |  | search:yes |
| `/projects/:projectID/opportunities` | GET* | /opportunities?projectID=:projectID |  | search:yes |
| `/executions/:executionID/opportunities` | GET* | /opportunities?executionID=:executionID&from=execution |  | search:yes |
| `/projects/:projectID/auditplans` | GET* | /auditplans?projectID=:projectID |  | search:yes |
| `/executions/:executionID/auditplans` | GET* | /auditplans?executionID=:executionID&from=execution |  | search:yes |

### Bug / 测试

| Path | Method | redirect | response | 备注 |
|------|--------|----------|----------|------|
| `/bugs/:bugID` | GET* |  | bug,actions(array) |  |
| `/testcases/:caseID` | GET,PUT |  | testcase,actions(array) |  |
| `/testtasks/:testtaskID` | GET* |  | task\|testtask,actions(array) |  |
| `/testreports/:reportID` | GET* |  | report\|testreport,actions(array) |  |

### 问题 / 风险 / 机会 / 审计

| Path | Method | redirect | response | 备注 |
|------|--------|----------|----------|------|
| `/issues` | GET* |  | issueList(array)\|issues,pager | search:yes |
| `/issues/:issueID` | GET* |  | issue,actions(array) |  |
| `/risks` | GET* |  | risks(array),pager | search:yes |
| `/risks/:riskID` | GET* |  | risk,actions(array) |  |
| `/opportunities` | GET* |  | opportunities(array),pager | search:yes |
| `/opportunities/:opportunityID` | GET* |  | opportunity,actions(array) |  |
| `/auditplans` | GET* |  | auditplans(array),pager | search:yes |

### 反馈 / 工单 / 应用 / 待办

| Path | Method | redirect | response | 备注 |
|------|--------|----------|----------|------|
| `/feedbacks` | GET* |  | feedbacks(array),pager | search:yes · method=admin |
| `/feedbacks/:feedbackID` | GET* |  | feedback,actions(array) |  |
| `/tickets` | GET* |  | tickets(array),pager | search:yes |
| `/tickets/:ticketID` | GET* |  | ticket,actions(array) |  |
| `/systems` | GET* |  | appList(array)\|systems,pager |  |
| `/systems/:systemID` | GET* |  | system,actions(array) |  |
| `/todos/:todoID` | GET* |  | todo |  |

### 我的 · work / todo

| Path | Method | redirect | response | 备注 |
|------|--------|----------|----------|------|
| `/todos/my` | GET* | /my/todo | todos(array),pager |  |
| `/my/todos` | GET* | /my/todo | todos(array),pager |  |
| `/my/tasks` | GET* | /my/task | tasks(array),pager | search:yes (my) · rawMethod=work mode=task |
| `/my/bugs` | GET* | /my/work?mode=bug | bugs(array),pager | search:yes (my) |
| `/my/stories` | GET* | /my/work?mode=story | stories(array),pager | search:yes (my) |
| `/my/epics` | GET* | /my/work?mode=epic | stories(array)\|epics,pager | search:yes (my) |
| `/my/requirements` | GET* | /my/work?mode=requirement | stories(array)\|requirements,pager | search:yes (my) |
| `/my/testtasks` | GET* | /my/work?mode=testtask | tasks(array)\|testtasks,pager |  |
| `/my/testcases` | GET* | /my/work?mode=testcase | cases(array)\|testcases,pager | search:yes (my) |
| `/my/projects` | GET* | /my/project | projects(array),pager |  |
| `/my/executions` | GET* | /my/execution | executions(array),pager |  |
| `/my/issues` | GET* | /my/work?mode=issue | issues(array),pager |  |
| `/my/risks` | GET* | /my/work?mode=risk | risks(array),pager | search:yes (my) |
| `/my/reviewissues` | GET* | /my/work?mode=reviewissue | reviewissues(array),pager | search:yes (my) |
| `/my/audits` | GET* | /my/audit | reviewList(array)\|audits,pager |  |
| `/my/auditplans` | GET* | /my/auditplan | auditplans(array),pager |  |
| `/my/ncs` | GET* | /my/nc | ncs(array),pager |  |
| `/my/meetings` | GET* | /my/work?mode=mymeeting | meetings(array),pager |  |
| `/my/feedbacks` | GET* | /my/work?mode=feedback | feedbacks(array),pager | search:yes (my) |
| `/my/tickets` | GET* | /my/work?mode=ticket | tickets(array),pager | search:yes (my) |

### 我的 · contribute（activity）

| Path | Method | redirect | response | 备注 |
|------|--------|----------|----------|------|
| `/my/activity/tasks` | GET* | /my/contribute?mode=task | tasks(array),pager | search:yes (my) |
| `/my/activity/bugs` | GET* | /my/contribute?mode=bug | bugs(array),pager | search:yes (my) |
| `/my/activity/stories` | GET* | /my/contribute?mode=story | stories(array),pager | search:yes (my) |
| `/my/activity/epics` | GET* | /my/contribute?mode=epic | stories(array)\|epics,pager | search:yes (my) |
| `/my/activity/requirements` | GET* | /my/contribute?mode=requirement | stories(array)\|requirements,pager | search:yes (my) |
| `/my/activity/testtasks` | GET* | /my/contribute?mode=testtask | tasks(array)\|testtasks,pager |  |
| `/my/activity/testcases` | GET* | /my/contribute?mode=testcase | cases(array)\|testcases,pager | search:yes (my) |
| `/my/activity/docs` | GET* | /my/contribute?mode=doc | docs(array),pager |  |
| `/my/activity/issues` | GET* | /my/contribute?mode=issue | issues(array),pager |  |
| `/my/activity/risks` | GET* | /my/contribute?mode=risk | risks(array),pager | search:yes (my) |
| `/my/activity/reviewissues` | GET* | /my/contribute?mode=reviewissue | reviewissues(array),pager | search:yes (my) |
| `/my/activity/audits` | GET* | /my/contribute?mode=audit | reviewList(array)\|audits,pager |  |
| `/my/activity/feedbacks` | GET* | /my/contribute?mode=feedback | feedbacks(array),pager | search:yes (my) |

### 文档空间 / 库 / 文档

| Path | Method | redirect | response | 备注 |
|------|--------|----------|----------|------|
| `/doc/my/spaces` | GET,POST | /doc/ajaxGetSpaceData?type=mine&picks=space · /doc/createSpace?type=mine |  |  |
| `/doc/team/spaces` | GET,POST | /doc/ajaxGetSpaceData?type=custom&picks=space · /doc/createSpace?type=custom |  |  |
| `/doc/product/spaces` | GET* | /doc/ajaxGetSpaceData?type=product&picks=space |  |  |
| `/doc/project/spaces` | GET* | /doc/ajaxGetSpaceData?type=project&picks=space |  |  |
| `/doc/spaces/:spaceID` | GET,PUT,DELETE | /doc/editSpace?spaceID=:spaceID · /doc/editSpace?spaceID=:spaceID · /doc/deleteSpace?libID=:spaceID | lib\|space |  |
| `/doc/my/spaces/:spaceID/libs` | GET,POST | /doc/ajaxGetSpaceData?type=mine&spaceID=:spaceID&picks=lib · /doc/createLib?type=mine&objectID=:spaceID&libID=0 |  |  |
| `/doc/team/spaces/:spaceID/libs` | GET,POST | /doc/ajaxGetSpaceData?type=custom&spaceID=:spaceID&picks=lib · /doc/createLib?type=custom&objectID=:spaceID&libID=0 |  |  |
| `/doc/product/spaces/:productID/libs` | GET,POST | /doc/ajaxGetSpaceData?type=product&spaceID=:productID&picks=lib · /doc/createLib?type=product&objectID=:productID&libID=0 |  |  |
| `/doc/project/spaces/:projectID/libs` | GET,POST | /doc/ajaxGetSpaceData?type=project&spaceID=:projectID&picks=lib · /doc/createLib?type=project&objectID=:projectID&libID=0 |  |  |
| `/doc/libs/:libID` | GET,PUT,DELETE | /doc/editLib?libID=:libID · /doc/editLib?libID=:libID · /doc/deleteLib?libID=:libID | lib |  |
| `/doc/my/spaces/:spaceID/libs/:libID/docs` | GET,POST | /doc/ajaxGetSpaceData?type=mine&spaceID=:spaceID&libID=:libID&picks=doc · /doc/create?objectType=mine&objectID=:spaceID&libID=:libID&moduleID=0&docType= |  |  |
| `/doc/team/spaces/:spaceID/libs/:libID/docs` | GET,POST | /doc/ajaxGetSpaceData?type=custom&spaceID=:spaceID&libID=:libID&picks=doc · /doc/create?objectType=custom&objectID=:spaceID&libID=:libID&moduleID=0&docType= |  |  |
| `/doc/product/spaces/:productID/libs/:libID/docs` | GET,POST | /doc/ajaxGetSpaceData?type=product&spaceID=:productID&libID=:libID&picks=doc · /doc/create?objectType=product&objectID=:productID&libID=:libID&moduleID=0&docType= |  |  |
| `/doc/project/spaces/:projectID/libs/:libID/docs` | GET,POST | /doc/ajaxGetSpaceData?type=project&spaceID=:projectID&libID=:libID&picks=doc · /doc/create?objectType=project&objectID=:projectID&libID=:libID&moduleID=0&docType= |  |  |
| `/doc/docs/:docID` | GET,PUT,DELETE | /doc/ajaxGetDoc?docID=:docID · /doc/edit?docID=:docID · /doc/delete?docID=:docID |  |  |
| `/doc/docs/:docID/collect` | POST | /doc/collect?objectID=:docID |  |  |
| `/doc/my/spaces/:spaceID/libs/:libID/modules` | GET,POST | /doc/ajaxGetSpaceData?type=mine&spaceID=:spaceID&libID=:libID&picks=module · /tree/ajaxCreateModule |  |  |
| `/doc/team/spaces/:spaceID/libs/:libID/modules` | GET,POST | /doc/ajaxGetSpaceData?type=custom&spaceID=:spaceID&libID=:libID&picks=module · /tree/ajaxCreateModule |  |  |
| `/doc/product/spaces/:productID/libs/:libID/modules` | GET,POST | /doc/ajaxGetSpaceData?type=product&spaceID=:productID&libID=:libID&picks=module · /tree/ajaxCreateModule |  |  |
| `/doc/project/spaces/:projectID/libs/:libID/modules` | GET,POST | /doc/ajaxGetSpaceData?type=project&spaceID=:projectID&libID=:libID&picks=module · /tree/ajaxCreateModule |  |  |
| `/doc/modules/:moduleID` | PUT,DELETE | /tree/edit?moduleID=:moduleID&type=doc · /tree/delete?moduleID=:moduleID |  |  |

### 动态

| Path | Method | redirect | response | 备注 |
|------|--------|----------|----------|------|
| `/dynamics/date/:timestamp` | GET* | /companies/dynamic?browseType=date&date=:timestamp&limit=100000 | dateGroups\|actions |  |
| `/dynamics/product/:productID` | GET* | /companies/dynamic?browseType=all&productID=:productID&limit=100000 | dateGroups\|actions |  |
| `/dynamics/project/:projectID` | GET* | /companies/dynamic?browseType=all&projectID=:projectID&limit=100000 | dateGroups\|actions |  |
| `/dynamics/execution/:executionID` | GET* | /companies/dynamic?browseType=all&executionID=:executionID&limit=100000 | dateGroups\|actions |  |
| `/dynamics/user/:userID` | GET* | /companies/dynamic?browseType=all&userID=:userID&limit=10000 | dateGroups\|actions |  |

### 组织 / 用户 / 附件

| Path | Method | redirect | response | 备注 |
|------|--------|----------|----------|------|
| `/depts` | GET* |  | sons\|depts |  |
| `/depts/browse` | GET* |  |  |  |
| `/depts/:deptID` | GET* | /depts/browse?deptID=:deptID | sons |  |
| `/users` | GET* | /companies/browse | users,pager | search:yes (user) |
| `/users/:userID` | GET* | /users/:userID/profile | user |  |
| `/files/:fileID` | GET* | /files/:fileID/ajaxQuery |  |  |
| `/files/:fileID/download` | GET* |  |  | method=download |

### 模块树（tree）

| Path | Method | redirect | response | 备注 |
|------|--------|----------|----------|------|
| `/executions/:executionID/task/modules` | GET,POST | /tree/browsetask?rootID=:executionID · /tree/ajaxCreateModule | tree |  |
| `/products/:productID/story/modules` | GET,POST | /tree/browse?viewType=story&rootID=:productID · /tree/ajaxCreateModule | tree |  |
| `/products/:productID/bug/modules` | GET,POST | /tree/browse?viewType=bug&rootID=:productID · /tree/ajaxCreateModule | tree |  |
| `/products/:productID/testcase/modules` | GET,POST | /tree/browse?viewType=case&rootID=:productID · /tree/ajaxCreateModule | tree |  |
| `/testcase/modules/:moduleID` | PUT,DELETE | /tree/edit?moduleID=:moduleID&type=case · /tree/delete?moduleID=:moduleID |  |  |
| `/:type/modules/:moduleID` | PUT,DELETE | /tree/edit?moduleID=:moduleID&type=:type · /tree/delete?moduleID=:moduleID |  |  |

## 源码索引

| 文件 | 作用 |
|------|------|
| `www/api.php` | API 入口 |
| `config/apiv2.php` | **本文依据**（v2 路由表） |
| `config/apiv1.php` | v1 路由表 → [zentao-rest-apiv1.md](./zentao-rest-apiv1.md) |
| `framework/api/router.class.php` | `parseRequest` / `routeV2` / `loadModule` |

统计：路由 **160** 条（与 `config/apiv2.php` 的 `$routes[...]` 声明一致）。

