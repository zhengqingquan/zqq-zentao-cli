#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task operations via ZenTaoClient (shape: task_shape; fetch: web/rest tasks)."""

from __future__ import annotations

from typing import Any

from ..confirm_util import confirm_or_exit
from ..list_filter import filter_rows
from ..protocol import ZenTaoClient
from ..task_shape import enrich_task_detail


def my_tasks(client: ZenTaoClient) -> list[dict[str, Any]]:
    return client.my_tasks()


def list_tasks(
    client: ZenTaoClient,
    *,
    page: int = 1,
    limit: int = 100,
    assigned_to: str | None = None,
    opened_by: str | None = None,
    finished_by: str | None = None,
    closed_by: str | None = None,
    status: str | None = None,
    pri: str | None = None,
) -> dict[str, Any]:
    return client.list_tasks(
        page=page,
        limit=limit,
        assigned_to=assigned_to,
        opened_by=opened_by,
        finished_by=finished_by,
        closed_by=closed_by,
        status=status,
        pri=pri,
    )


def execution_tasks(
    client: ZenTaoClient,
    execution_id: str | int,
    *,
    assigned_to: str | None = None,
    opened_by: str | None = None,
    finished_by: str | None = None,
    closed_by: str | None = None,
    status: str | None = None,
    pri: str | None = None,
) -> list[dict[str, Any]]:
    rows = client.execution_tasks(execution_id)
    return filter_rows(
        rows,
        assigned_to=(assigned_to or "").strip() or None,
        opened_by=(opened_by or "").strip() or None,
        finished_by=(finished_by or "").strip() or None,
        closed_by=(closed_by or "").strip() or None,
        status=(status or "").strip() or None,
        pri=(pri or "").strip() or None,
    )


def get_task(client: ZenTaoClient, task_id: str | int) -> dict[str, Any]:
    return enrich_task_detail(client.get_task(task_id))


def create_task(
    client: ZenTaoClient,
    execution_id: str | int,
    body: dict[str, Any],
    *,
    yes: bool = False,
) -> dict[str, Any]:
    confirm_or_exit(f"Create task under execution {execution_id}?", yes=yes)
    return client.create_task(execution_id, body)


def update_task(
    client: ZenTaoClient,
    task_id: str | int,
    body: dict[str, Any],
    *,
    yes: bool = False,
) -> dict[str, Any]:
    confirm_or_exit(f"Update task {task_id}?", yes=yes)
    return client.update_task(task_id, body)


def delete_task(
    client: ZenTaoClient, task_id: str | int, *, yes: bool = False
) -> dict[str, Any]:
    confirm_or_exit(f"Delete task {task_id}? This cannot be undone easily.", yes=yes)
    return client.delete_task(task_id)


def task_action(
    client: ZenTaoClient,
    action: str,
    task_id: str | int,
    body: dict[str, Any] | None = None,
    *,
    yes: bool = False,
) -> dict[str, Any]:
    confirm_or_exit(f"Task {action} id={task_id}?", yes=yes)
    return client.task_action(task_id, action, body or {})
