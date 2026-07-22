#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""REST task fetch strategies (my-tasks pager workaround, execution pagination)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..task_shape import assigned_account, summarize_task

# Bound RestClient.list_resource (or compatible).
ListResourceFn = Callable[..., dict[str, Any]]


def _list_my_tasks_raw(
    list_resource: ListResourceFn, *, rec_per_page: int = 200
) -> dict[str, Any]:
    """Load assigned tasks via GET /tasks, working around APIv1 arg swap.

    ``tasksEntry`` calls ``my->task(type, order, total, limit, page)`` but
    ``my::task`` expects ``(browseType, param, orderBy, recTotal, recPerPage,
    pageID)``. So query ``page`` is treated as ``recPerPage``, and ``pageID``
    is always 1. We set ``page=<size>`` to fetch up to that many rows once.
    """
    size = max(1, int(rec_per_page))
    data = list_resource(
        "tasks",
        page=1,
        limit=size,
        query={
            "type": "assignedTo",
            "order": "0",
            "total": "id_desc",
            "limit": "0",
            "page": str(size),
        },
    )
    rows = data.get("tasks") or []
    total = int(data.get("total") or len(rows))
    if total > len(rows):
        data = list_resource(
            "tasks",
            page=1,
            limit=total,
            query={
                "type": "assignedTo",
                "order": "0",
                "total": "id_desc",
                "limit": "0",
                "page": str(total),
            },
        )
    return data


def fetch_my_tasks(list_resource: ListResourceFn, account: str) -> list[dict[str, Any]]:
    """All tasks assigned to ``account`` (canonical rows)."""
    data = _list_my_tasks_raw(list_resource, rec_per_page=200)
    rows = data.get("tasks") or []
    mine = [x for x in rows if assigned_account(x) == account]
    if rows and not mine:
        mine = rows
    return [summarize_task(x) for x in mine]


def list_my_tasks(
    list_resource: ListResourceFn, *, page: int = 1, limit: int = 100
) -> dict[str, Any]:
    """Paginated my-tasks (client-side slice after full-fetch workaround)."""
    page = max(1, int(page))
    limit = max(1, int(limit))
    need = page * limit
    data = _list_my_tasks_raw(list_resource, rec_per_page=max(need, limit, 100))
    rows = data.get("tasks") or []
    total = int(data.get("total") or len(rows))
    start = (page - 1) * limit
    chunk = rows[start : start + limit]
    return {
        "page": page,
        "total": total,
        "limit": limit,
        "tasks": [summarize_task(x) for x in chunk],
    }


def fetch_execution_tasks(
    list_resource: ListResourceFn, execution_id: str | int
) -> list[dict[str, Any]]:
    """Tasks under one execution (auto-paginate if server truncates)."""
    page = 1
    limit = 200
    all_rows: list[dict[str, Any]] = []
    seen: set[Any] = set()
    raw_last: Any = None
    while page <= 100:
        data = list_resource(
            "tasks",
            page=page,
            limit=limit,
            scopes={"execution": execution_id},
        )
        raw_last = data
        rows = data.get("tasks") or []
        if not rows:
            break
        for row in rows:
            tid = row.get("id")
            if tid in seen:
                continue
            seen.add(tid)
            all_rows.append(row)
        total = int(data.get("total") or 0)
        if total and len(all_rows) >= total:
            break
        if len(rows) < int(data.get("limit") or limit):
            break
        page += 1

    if not all_rows:
        raise SystemExit(
            f"Failed to parse REST execution task list. raw={raw_last!r}"[:200]
        )
    return [summarize_task(x) for x in all_rows]
