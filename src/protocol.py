#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ZenTao dual-backend client protocol."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ZenTaoClient(Protocol):
    """Domain operations implemented by WebClient and RestClient."""

    backend: str
    profile: dict[str, str]

    def login(self) -> None: ...

    def whoami(self) -> dict[str, Any]: ...

    def my_tasks(self) -> list[dict[str, Any]]: ...

    def my_bugs(self) -> list[dict[str, Any]]: ...

    def my_page(
        self,
        cmd: str,
        *,
        scope: str,
        browse_type: str,
    ) -> list[dict[str, Any]]: ...

    def list_tasks(
        self,
        *,
        page: int = 1,
        limit: int = 100,
        assigned_to: str | None = None,
        opened_by: str | None = None,
        status: str | None = None,
    ) -> dict[str, Any]: ...

    def execution_tasks(self, execution_id: str | int) -> list[dict[str, Any]]: ...

    def get_task(self, task_id: str | int) -> dict[str, Any]: ...

    def list_users(self, *, page: int = 1, limit: int = 50) -> dict[str, Any]: ...

    def get_user(self, account: str) -> dict[str, Any]: ...

    def list_projects(self, *, page: int = 1, limit: int = 50) -> dict[str, Any]: ...

    def list_programs(self, *, page: int = 1, limit: int = 50) -> dict[str, Any]: ...

    def list_executions(self, *, page: int = 1, limit: int = 50) -> dict[str, Any]: ...

    def get_execution(self, execution_id: str | int) -> dict[str, Any]: ...

    def list_departments(self) -> dict[str, Any]: ...

    def list_comments(self, object_type: str, object_id: str | int) -> list[Any]: ...

    def add_comment(
        self, object_type: str, object_id: str | int, comment: str
    ) -> dict[str, Any]: ...

    def edit_comment(self, action_id: str | int, comment: str) -> dict[str, Any]: ...
