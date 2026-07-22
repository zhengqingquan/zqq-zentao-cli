#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Web (PATHINFO + Cookie) client implementing ZenTaoClient."""

from __future__ import annotations

from typing import Any

from ..config import (
    LOGIN_HINT,
    clear_web_cookies,
    cookies_look_valid,
    insecure_ssl,
    load_profile,
    load_web_cookies,
    resolve_password,
    save_web_cookies,
    try_resolve_password,
)
from . import bugs as bugs_api
from . import comments as comments_api
from . import tasks as tasks_api
from .parse import looks_auth_fail
from .session import Session


class WebClient:
    backend = "web"

    def __init__(
        self,
        profile: dict[str, str] | None = None,
        *,
        insecure: bool | None = None,
        timeout: float | None = None,
    ):
        self.profile = profile or load_profile()
        self._sess = Session(
            self.profile["server"],
            insecure=insecure_ssl() if insecure is None else insecure,
            timeout=60.0 if timeout is None else timeout,
        )
        self._logged_in = False

    @property
    def session(self) -> Session:
        return self._sess

    def login(self, *, password: str | None = None, persist: bool = True) -> None:
        pwd = password if password is not None else resolve_password()
        self._sess.login(self.profile["account"], pwd)
        if persist:
            save_web_cookies(
                self._sess.cookies,
                server=self.profile["server"],
                account=self.profile["account"],
            )
        self._logged_in = True

    def _apply_cached_cookies(self) -> bool:
        cookies = load_web_cookies(
            server=self.profile["server"],
            account=self.profile["account"],
        )
        if not cookies_look_valid(cookies):
            return False
        self._sess.cookies = dict(cookies)
        self._sess.mark_cookie_auth(self.profile["account"])
        self._logged_in = True
        return True

    def _ensure_login(self) -> None:
        if self._logged_in:
            return
        if self._apply_cached_cookies():
            return
        if try_resolve_password():
            self.login()
            return
        raise SystemExit(f"Not logged in (web). {LOGIN_HINT}")

    def _relogin_on_auth_fail(self) -> bool:
        """Clear cache and re-login with password once. Returns True if retried."""
        clear_web_cookies(server=self.profile["server"], account=self.profile["account"])
        self._sess.cookies.clear()
        self._logged_in = False
        if not try_resolve_password():
            return False
        self.login()
        return True

    def _with_auth_retry(self, fn):
        self._ensure_login()
        try:
            return fn()
        except SystemExit as e:
            msg = str(e)
            if "auth fail" not in msg.lower() and "login" not in msg.lower():
                raise
            if not self._relogin_on_auth_fail():
                raise SystemExit(f"{msg}. {LOGIN_HINT}") from e
            return fn()

    def whoami(self) -> dict[str, Any]:
        self._ensure_login()
        return {
            "account": self.profile["account"],
            "server": self.profile["server"],
            "backend": self.backend,
            "hasZentaosid": bool(self._sess.cookies.get("zentaosid")),
            "hasZa": bool(self._sess.cookies.get("za")),
            "hasZp": bool(self._sess.cookies.get("zp")),
        }

    def my_tasks(self) -> list[dict[str, Any]]:
        def _run() -> list[dict[str, Any]]:
            return tasks_api.fetch_my_tasks(self._sess)

        return self._with_auth_retry(_run)

    def my_bugs(self) -> list[dict[str, Any]]:
        def _run() -> list[dict[str, Any]]:
            return bugs_api.fetch_my_bugs(self._sess)

        return self._with_auth_retry(_run)

    def my_page(
        self,
        cmd: str,
        *,
        scope: str,
        browse_type: str,
    ) -> list[dict[str, Any]]:
        from .my_pages import fetch_my_page, my_page_by_cmd

        page = my_page_by_cmd(cmd)
        if page is None:
            raise SystemExit(f"Unknown my-* command: {cmd}")

        def _run() -> list[dict[str, Any]]:
            return fetch_my_page(
                self._sess, page, browse_type=browse_type, scope=scope
            )

        return self._with_auth_retry(_run)

    def execution_tasks(self, execution_id: str | int) -> list[dict[str, Any]]:
        def _run() -> list[dict[str, Any]]:
            return tasks_api.fetch_execution_tasks(self._sess, execution_id)

        return self._with_auth_retry(_run)

    def get_task(self, task_id: str | int) -> dict[str, Any]:
        def _run() -> dict[str, Any]:
            return tasks_api.fetch_task(self._sess, task_id)

        return self._with_auth_retry(_run)

    def list_tasks(
        self,
        *,
        page: int = 1,
        limit: int = 100,
        assigned_to: str | None = None,
        opened_by: str | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        raise SystemExit("tasks without --execution requires --backend rest")

    def list_users(self, *, page: int = 1, limit: int = 50) -> dict[str, Any]:
        raise SystemExit("users requires --backend rest")

    def get_user(self, account: str) -> dict[str, Any]:
        raise SystemExit("user requires --backend rest")

    def list_projects(self, *, page: int = 1, limit: int = 50) -> dict[str, Any]:
        raise SystemExit("projects requires --backend rest")

    def list_programs(self, *, page: int = 1, limit: int = 50) -> dict[str, Any]:
        raise SystemExit("programs requires --backend rest")

    def list_executions(self, *, page: int = 1, limit: int = 50) -> dict[str, Any]:
        raise SystemExit("executions requires --backend rest")

    def get_execution(self, execution_id: str | int) -> dict[str, Any]:
        raise SystemExit("execution requires --backend rest")

    def list_departments(self) -> dict[str, Any]:
        raise SystemExit("departments requires --backend rest")

    def list_comments(self, object_type: str, object_id: str | int) -> list[Any]:
        def _run() -> list[Any]:
            return comments_api.list_comments(self._sess, object_type, object_id)

        return self._with_auth_retry(_run)

    def add_comment(self, object_type: str, object_id: str | int, comment: str) -> dict[str, Any]:
        def _run() -> dict[str, Any]:
            r = comments_api.add_comment(self._sess, object_type, object_id, comment)
            if looks_auth_fail(r):
                raise SystemExit(f"comment.add auth fail HTTP {r['status']}")
            return r

        return self._with_auth_retry(_run)

    def edit_comment(self, action_id: str | int, comment: str) -> dict[str, Any]:
        def _run() -> dict[str, Any]:
            r = comments_api.edit_comment(self._sess, action_id, comment)
            if looks_auth_fail(r):
                raise SystemExit(f"comment.edit auth fail HTTP {r['status']}")
            return r

        return self._with_auth_retry(_run)
