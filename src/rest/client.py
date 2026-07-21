#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""REST (/api.php/v1 + Token) client."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from ..config import insecure_ssl, load_profile
from .session import RestSession


def _user_field(val: Any) -> str | None:
    if val is None:
        return None
    if isinstance(val, dict):
        return val.get("account") or val.get("realname") or val.get("name")
    return str(val)


def summarize_rest_task(row: dict[str, Any]) -> dict[str, Any]:
    assigned = row.get("assignedTo")
    opened = row.get("openedBy")
    return {
        "id": row.get("id"),
        "name": row.get("name"),
        "status": row.get("status") or row.get("rawStatus"),
        "pri": row.get("pri"),
        "deadline": row.get("deadline"),
        "assignedTo": _user_field(assigned) if not isinstance(assigned, str) else assigned,
        "assignedToRealName": (
            assigned.get("realname")
            if isinstance(assigned, dict)
            else row.get("assignedToRealName")
        ),
        "execution": row.get("execution") or row.get("executionID"),
        "executionName": row.get("executionName"),
        "project": row.get("project"),
        "projectName": row.get("projectName"),
        "type": row.get("type"),
        "progress": row.get("progress"),
        "consumed": row.get("consumed"),
        "left": row.get("left"),
        "estimate": row.get("estimate"),
        "openedBy": _user_field(opened) if not isinstance(opened, str) else opened,
        "openedDate": row.get("openedDate"),
        "desc": row.get("desc"),
    }


def _extract_task_list(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        for key in ("tasks", "data", "list"):
            val = data.get(key)
            if isinstance(val, list):
                return [x for x in val if isinstance(x, dict)]
    return []


class RestClient:
    backend = "rest"

    def __init__(self, profile: dict[str, str] | None = None, *, insecure: bool | None = None):
        self.profile = profile or load_profile()
        self._sess = RestSession(
            self.profile["server"],
            insecure=insecure_ssl() if insecure is None else insecure,
        )
        self._logged_in = False

    def login(self) -> None:
        self._sess.login(self.profile["account"])
        self._logged_in = True

    def _ensure_login(self) -> None:
        if not self._logged_in:
            self.login()

    def whoami(self) -> dict[str, Any]:
        self._ensure_login()
        r = self._sess.request("GET", "/user")
        if not r["ok"]:
            raise SystemExit(f"REST whoami failed HTTP {r['status']}: {r['raw'][:160]}")
        data = r["data"] if isinstance(r["data"], dict) else {}
        profile = data.get("profile") if isinstance(data.get("profile"), dict) else data
        return {
            "account": profile.get("account") or self.profile["account"],
            "realname": profile.get("realname"),
            "server": self.profile["server"],
            "backend": self.backend,
            "hasToken": bool(self._sess.token),
            "profile": profile,
        }

    def my_tasks(self) -> list[dict[str, Any]]:
        """Try GET /users/{account}/tasks; on failure suggest web or tasks -e."""
        self._ensure_login()
        account = self.profile["account"]
        r = self._sess.request(
            "GET",
            f"/users/{quote(account, safe='')}/tasks",
            query={"page": "1", "limit": "100"},
        )
        if r["ok"]:
            return [summarize_rest_task(x) for x in _extract_task_list(r["data"])]
        raise SystemExit(
            f"REST my-tasks unavailable HTTP {r['status']} ({r['raw'][:120]!r}). "
            "Use --backend web, or tasks --execution <id>."
        )

    def execution_tasks(self, execution_id: str | int) -> list[dict[str, Any]]:
        self._ensure_login()
        r = self._sess.request(
            "GET",
            f"/executions/{execution_id}/tasks",
            query={"page": "1", "limit": "200"},
        )
        if not r["ok"]:
            raise SystemExit(f"REST execution tasks failed HTTP {r['status']}: {r['raw'][:160]}")
        rows = _extract_task_list(r["data"])
        if not rows and r["data"]:
            raise SystemExit(
                f"Failed to parse REST execution task list. raw[:120]={r['raw'][:120]!r}"
            )
        return [summarize_rest_task(x) for x in rows]

    def get_task(self, task_id: str | int) -> dict[str, Any]:
        self._ensure_login()
        r = self._sess.request("GET", f"/tasks/{task_id}")
        if not r["ok"] or not isinstance(r["data"], dict):
            raise SystemExit(f"REST task failed HTTP {r['status']}: {r['raw'][:160]}")
        data = r["data"]
        # Some versions nest the payload under "task"
        if "id" not in data and isinstance(data.get("task"), dict):
            data = data["task"]
        return summarize_rest_task(data)

    def list_comments(self, object_type: str, object_id: str | int) -> list[Any]:
        raise SystemExit("comment.list requires --backend web")

    def add_comment(self, object_type: str, object_id: str | int, comment: str) -> dict[str, Any]:
        raise SystemExit("comment.add requires --backend web")

    def edit_comment(self, action_id: str | int, comment: str) -> dict[str, Any]:
        raise SystemExit("comment.edit requires --backend web")
