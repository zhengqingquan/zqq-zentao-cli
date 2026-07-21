#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Web (PATHINFO + Cookie) client implementing ZenTaoClient."""

from __future__ import annotations

from typing import Any

from ..config import insecure_ssl, load_profile, resolve_password
from . import comments as comments_api
from . import tasks as tasks_api
from .session import Session


class WebClient:
    backend = "web"

    def __init__(self, profile: dict[str, str] | None = None, *, insecure: bool | None = None):
        self.profile = profile or load_profile()
        self._sess = Session(
            self.profile["server"],
            insecure=insecure_ssl() if insecure is None else insecure,
        )
        self._logged_in = False

    @property
    def session(self) -> Session:
        return self._sess

    def login(self) -> None:
        self._sess.login(self.profile["account"], resolve_password())
        self._logged_in = True

    def _ensure_login(self) -> None:
        if not self._logged_in:
            self.login()

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
        self._ensure_login()
        return tasks_api.fetch_my_tasks(self._sess)

    def execution_tasks(self, execution_id: str | int) -> list[dict[str, Any]]:
        self._ensure_login()
        return tasks_api.fetch_execution_tasks(self._sess, execution_id)

    def get_task(self, task_id: str | int) -> dict[str, Any]:
        self._ensure_login()
        return tasks_api.fetch_task(self._sess, task_id)

    def list_comments(self, object_type: str, object_id: str | int) -> list[Any]:
        self._ensure_login()
        return comments_api.list_comments(self._sess, object_type, object_id)

    def add_comment(self, object_type: str, object_id: str | int, comment: str) -> dict[str, Any]:
        self._ensure_login()
        return comments_api.add_comment(self._sess, object_type, object_id, comment)

    def edit_comment(self, action_id: str | int, comment: str) -> dict[str, Any]:
        self._ensure_login()
        return comments_api.edit_comment(self._sess, action_id, comment)
