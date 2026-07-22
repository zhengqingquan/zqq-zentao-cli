#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""REST (/api.php/v1 + Token) client."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from ..config import LOGIN_HINT, insecure_ssl, load_profile, try_resolve_password
from . import tasks as tasks_api
from .resources import RESOURCES, Resource
from .session import RestSession

# Scope flag priority when multiple are set (first wins).
_SCOPE_ORDER = ("product", "project", "execution", "program", "lib")


def _extract_named_list(data: Any, *keys: str) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        for key in keys:
            val = data.get(key)
            if isinstance(val, list):
                return [x for x in val if isinstance(x, dict)]
        nested = data.get("data")
        if isinstance(nested, dict):
            for key in keys:
                val = nested.get(key)
                if isinstance(val, list):
                    return [x for x in val if isinstance(x, dict)]
        for key in ("data", "list"):
            val = data.get(key)
            if isinstance(val, list):
                return [x for x in val if isinstance(x, dict)]
    return []


def _extract_total(data: Any, rows_len: int) -> int:
    if not isinstance(data, dict):
        return rows_len
    for key in ("total", "recTotal"):
        if data.get(key) is not None:
            try:
                return int(data[key])
            except (TypeError, ValueError):
                pass
    nested = data.get("data")
    if isinstance(nested, dict):
        pager = nested.get("pager")
        if isinstance(pager, dict):
            for key in ("recTotal", "total"):
                if pager.get(key) is not None:
                    try:
                        return int(pager[key])
                    except (TypeError, ValueError):
                        pass
        for key in ("total", "recTotal"):
            if nested.get(key) is not None:
                try:
                    return int(nested[key])
                except (TypeError, ValueError):
                    pass
    pager = data.get("pager")
    if isinstance(pager, dict):
        for key in ("recTotal", "total"):
            if pager.get(key) is not None:
                try:
                    return int(pager[key])
                except (TypeError, ValueError):
                    pass
    return rows_len


def _unwrap_entity(data: Any, *keys: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise SystemExit(f"Expected object payload, got {type(data).__name__}")
    if any(k in data for k in ("id", "account", "name")) and not any(
        isinstance(data.get(k), dict) for k in keys
    ):
        return data
    for key in keys:
        nested = data.get(key)
        if isinstance(nested, dict):
            return nested
    return data


class RestClient:
    backend = "rest"

    def __init__(
        self,
        profile: dict[str, str] | None = None,
        *,
        insecure: bool | None = None,
        timeout: float | None = None,
    ):
        self.profile = profile or load_profile()
        self._sess = RestSession(
            self.profile["server"],
            insecure=insecure_ssl() if insecure is None else insecure,
            account=self.profile["account"],
            timeout=60.0 if timeout is None else timeout,
        )
        self._logged_in = False

    def login(self, *, password: str | None = None, force_password: bool = False) -> None:
        self._sess.login(
            self.profile["account"],
            password,
            force_password=force_password,
        )
        self._logged_in = True

    def _ensure_login(self) -> None:
        if self._logged_in:
            return
        try:
            self.login()
        except SystemExit as e:
            if try_resolve_password():
                raise
            raise SystemExit(f"{e}. {LOGIN_HINT}") from e

    def _get(self, path: str, *, query: dict[str, str] | None = None) -> Any:
        self._ensure_login()
        r = self._sess.request("GET", path, query=query)
        if not r["ok"]:
            raise SystemExit(f"REST GET {path} failed HTTP {r['status']}: {r['raw'][:160]}")
        return r["data"]

    def whoami(self) -> dict[str, Any]:
        data = self._get("/user")
        data = data if isinstance(data, dict) else {}
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
        """All tasks assigned to me (canonical rows)."""
        return tasks_api.fetch_my_tasks(self.list_resource, self.profile["account"])

    def my_bugs(self) -> list[dict[str, Any]]:
        raise SystemExit("my-bugs requires --backend web")

    def list_tasks(
        self,
        *,
        page: int = 1,
        limit: int = 100,
        assigned_to: str | None = None,
        opened_by: str | None = None,
    ) -> dict[str, Any]:
        """Task list: my-tasks by default, or search/filter by account."""
        at = (assigned_to or "").strip() or None
        ob = (opened_by or "").strip() or None
        if ob and not at:
            raise SystemExit(
                "tasks --openedBy without --execution requires --assignedTo "
                "(ZenTao GET /tasks?search=1 has no openedBy). "
                "Use: tasks -e <id> --openedBy <account>"
            )
        if at:
            out = tasks_api.search_tasks(
                self.list_resource,
                assigned_to=at,
                opened_by=ob,
                page=page,
                limit=limit,
            )
            out["backend"] = self.backend
            return out
        out = tasks_api.list_my_tasks(self.list_resource, page=page, limit=limit)
        out["backend"] = self.backend
        return out

    def execution_tasks(self, execution_id: str | int) -> list[dict[str, Any]]:
        """Tasks under one execution (canonical rows)."""
        return tasks_api.fetch_execution_tasks(self.list_resource, execution_id)

    def get_task(self, task_id: str | int) -> dict[str, Any]:
        return self.get_resource("tasks", task_id)

    def list_users(self, *, page: int = 1, limit: int = 50) -> dict[str, Any]:
        return self.list_resource("users", page=page, limit=limit)

    def get_user(self, account: str) -> dict[str, Any]:
        return self.get_resource("users", account)

    def list_projects(self, *, page: int = 1, limit: int = 50) -> dict[str, Any]:
        return self.list_resource("projects", page=page, limit=limit)

    def list_programs(self, *, page: int = 1, limit: int = 50) -> dict[str, Any]:
        return self.list_resource("programs", page=page, limit=limit)

    def list_executions(self, *, page: int = 1, limit: int = 50) -> dict[str, Any]:
        return self.list_resource("executions", page=page, limit=limit)

    def get_execution(self, execution_id: str | int) -> dict[str, Any]:
        return self.get_resource("executions", execution_id)

    def list_departments(self) -> dict[str, Any]:
        return self.list_resource("departments")


    def list_comments(self, object_type: str, object_id: str | int) -> list[Any]:
        raise SystemExit("comment.list requires --backend web")

    def add_comment(self, object_type: str, object_id: str | int, comment: str) -> dict[str, Any]:
        raise SystemExit("comment.add requires --backend web")

    def edit_comment(self, action_id: str | int, comment: str) -> dict[str, Any]:
        raise SystemExit("comment.edit requires --backend web")

    def _resolve_resource(self, name: str) -> Resource:
        res = RESOURCES.get(name)
        if res is None:
            raise SystemExit(f"Unknown REST resource: {name}")
        return res

    def _pick_scope(
        self, res: Resource, scopes: dict[str, str | int | None] | None
    ) -> tuple[str, str] | None:
        """Return (scope_name, scope_id) or None."""
        if not scopes:
            return None
        for name in _SCOPE_ORDER:
            if name not in res.scopes:
                continue
            val = scopes.get(name)
            if val is None or val == "":
                continue
            return name, str(val)
        # any other declared scope
        for name in res.scopes:
            val = scopes.get(name) if scopes else None
            if val is None or val == "":
                continue
            return name, str(val)
        return None

    def list_resource(
        self,
        name: str,
        *,
        page: int = 1,
        limit: int = 50,
        scopes: dict[str, str | int | None] | None = None,
        path_param: str | None = None,
        query: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Generic GET list for a registry resource."""
        res = self._resolve_resource(name)
        picked = self._pick_scope(res, scopes)
        if res.require_scope and not picked:
            needed = ", ".join(f"--{s}" for s in res.scopes)
            raise SystemExit(f"{res.list_cmd or name} requires one of: {needed}")
        if res.required_query:
            q = query or {}
            missing = [k for k in res.required_query if not q.get(k)]
            if missing:
                flags = ", ".join(f"--{k}" for k in missing)
                raise SystemExit(f"{res.list_cmd or name} requires: {flags}")

        if picked:
            scope_name, scope_id = picked
            path = res.scopes[scope_name].format(id=quote(scope_id, safe=""))
        elif res.path_param:
            if not path_param:
                raise SystemExit(f"{res.list_cmd or name} requires <{res.path_param}>")
            if not res.list_path:
                raise SystemExit(f"Resource {name} has no list_path")
            path = res.list_path.format(param=quote(str(path_param), safe=""))
        elif res.list_path:
            path = res.list_path
        else:
            needed = ", ".join(f"--{s}" for s in res.scopes) or "(scope)"
            raise SystemExit(f"{res.list_cmd or name} requires one of: {needed}")

        q: dict[str, str] = dict(query or {})
        if res.paginated:
            q.setdefault("page", str(page))
            q.setdefault("limit", str(limit))

        data = self._get(path, query=q or None)
        if res.list_key:
            rows = _extract_named_list(data, res.list_key)
            # groups etc. may return a bare list
            if not rows and isinstance(data, list):
                rows = [x for x in data if isinstance(x, dict)]
            meta = data if isinstance(data, dict) else {}
            out: dict[str, Any] = {
                res.list_key: rows,
                "backend": self.backend,
            }
            if res.paginated:
                out["page"] = meta.get("page", page)
                out["total"] = _extract_total(data, len(rows))
                out["limit"] = meta.get("limit", limit)
            elif isinstance(data, dict):
                for k, v in data.items():
                    if k != res.list_key:
                        out.setdefault(k, v)
            return out

        if isinstance(data, dict):
            return {**data, "backend": self.backend}
        return {"data": data, "backend": self.backend}

    def get_resource(self, name: str, resource_id: str | int) -> dict[str, Any]:
        """Generic GET detail for a registry resource."""
        res = self._resolve_resource(name)
        if not res.detail_path:
            raise SystemExit(f"Resource {name} has no detail endpoint")
        path = res.detail_path.format(id=quote(str(resource_id), safe=""))
        data = self._get(path)
        if res.detail_keys:
            entity = _unwrap_entity(data, *res.detail_keys)
            out = dict(entity) if isinstance(entity, dict) else {"value": entity}
        elif isinstance(data, dict):
            out = dict(data)
        else:
            out = {"data": data}
        # Preserve sibling fields (e.g. actions next to nested task).
        if isinstance(data, dict) and isinstance(out, dict):
            for key in ("actions",):
                if key in data and key not in out:
                    out[key] = data[key]
        out["backend"] = self.backend
        return out
