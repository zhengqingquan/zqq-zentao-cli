# 禅道 Web API（PATH_INFO）

## 公共约定

| 项 | 说明 |
|----|------|
| URL 风格 | `/{module}-{method}-{arg…}.html` |
| Ajax / 局部 | 列表页常见 `?zin=1`；请求头可有 `X-Requested-With`、`X-Zin-*` |
| 鉴权 | Cookie 会话：`zentaosid`，登录后还有 `za` / `zp` |

---

## 登录 / 会话

| Method | Path | 说明 |
|--------|------|------|
| GET | `/user-refreshRandom.html` | 刷新校验随机数 |
| GET | `/user-login-{refererBase64}.html` | 打开登录页（PATH_INFO 带 base64 回跳） |
| POST | `/user-login.html` | 网页登录 |
| GET | `/user-logout-{refererBase64}.html` | 退出 |

**POST `/user-login.html` 表单字段：**

| 字段 | 说明 |
|------|------|
| `account` | 账号 |
| `password` | 密码摘要：`md5(md5(明文) + verifyRand)` |
| `passwordStrength` | 强度标记 |
| `referer` | 登录后回跳 |
| `verifyRand` | 与 `refreshRandom` 配合 |
| `keepLogin` | 是否保持登录 |
| `captcha` | 验证码（可空） |

登录响应会 `Set-Cookie`：`lang`、`device`、`theme`、`logout`、`keepLogin`、`za`、`zp` 等。

---

## 导航 / 页面

| Method | Path | 说明 |
|--------|------|------|
| GET | `/` | 根 / 跳转 |
| GET | `/index-app.html` | 应用壳 |
| GET | `/my.html` | 我的地盘（常 `?zin=1`） |
| GET | `/my-work-task-assignedTo.html` | 指派给我的任务 |
| GET | `/my-work-bug-assignedTo.html` | 指派给我的 Bug（`my::work`→`bug`，默认排除已关闭） |
| GET | `/my-work-bug-openedBy.html` | 由我创建的 Bug |
| GET | `/my-work-bug-resolvedBy.html` | 由我解决的 Bug |
| GET | `/my-bug-assignedTo.html` | 同上（直接 `my::bug`，不经 work） |
| GET | `/execution-task.html` | 执行任务列表入口 |
| GET | `/execution-task-{executionID}.html` | 指定执行的任务列表 |
| GET | `/execution-ajaxGetDropMenu-{projectID}-execution-task-.html` | 执行下拉菜单 |
| GET | `/project-browse.html` | 项目浏览 |
| GET | `/qa.html` | 测试入口 |
| GET | `/task-view-{taskID}.html` | 任务详情 |

---

## 仪表盘 / 杂项

| Method | Path | 说明 |
|--------|------|------|
| GET | `/block-printBlock-{blockID}-{paramsBase64}.html` | 仪表盘区块；`paramsBase64` 为 `module=…&projectID=…` 的 base64 |
| GET | `/misc-checkUpdate-{hash}.html` | 检查更新 |
| GET | `/zai-ajaxGetToken.html` | ZAI token（常 deny，非登录凭证） |

---

## 备注

| Method | Path | 说明 |
|--------|------|------|
| GET/POST | `/action-comment-{objectType}-{objectID}.html` | 打开 / 提交新备注（字段 `actioncomment`） |
| GET/POST | `/action-editComment-{actionID}.html` | 打开 / 修改备注（字段 `lastComment`） |
| GET | `/action-ajaxGetList-{objectType}-{objectID}.html` | 历史列表 JSON |

请求头常见：`X-Requested-With: XMLHttpRequest`、`X-Zui-Modal: true`。须带有效网页 Cookie。

成功写响应示例：

```json
{
  "status": "success",
  "closeModal": true,
  "callback": {
    "name": "zui.HistoryPanel.update",
    "params": { "objectType": "task", "objectID": 38597 }
  }
}
```
