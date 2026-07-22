#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task operations via ZenTaoClient (shape: task_shape; fetch: web/rest tasks)."""

from __future__ import annotations

from typing import Any

from ..list_filter import filter_rows
from ..protocol import ZenTaoClient


def my_tasks(client: ZenTaoClient) -> list[dict[str, Any]]:
    return client.my_tasks()


def list_tasks(
    client: ZenTaoClient,
    *,
    page: int = 1,
    limit: int = 100,
    assigned_to: str | None = None,
    opened_by: str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    return client.list_tasks(
        page=page,
        limit=limit,
        assigned_to=assigned_to,
        opened_by=opened_by,
        status=status,
    )


def execution_tasks(
    client: ZenTaoClient,
    execution_id: str | int,
    *,
    assigned_to: str | None = None,
    opened_by: str | None = None,
    status: str | None = None,
) -> list[dict[str, Any]]:
    rows = client.execution_tasks(execution_id)
    at = (assigned_to or "").strip() or None
    ob = (opened_by or "").strip() or None
    st = (status or "").strip() or None
    if at or ob or st:
        return filter_rows(rows, assigned_to=at, opened_by=ob, status=st)
    return rows


def get_task(client: ZenTaoClient, task_id: str | int) -> dict[str, Any]:
    return client.get_task(task_id)
