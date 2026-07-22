#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""My tasks / execution tasks / task detail (PATHINFO)."""

from __future__ import annotations

from typing import Any

from ..task_shape import summarize_task
from .comments import list_comments
from .lists import fetch_dtable_list
from .parse import looks_auth_fail, parse_task_view_html, strip_tags, zin_main_html
from .session import Session


def fetch_my_tasks(sess: Session) -> list[dict[str, Any]]:
    return fetch_dtable_list(
        sess,
        "/my-work-task-assignedTo.html?zin=1",
        label="my-tasks",
        summarize=summarize_task,
    )


def fetch_execution_tasks(sess: Session, execution_id: str | int) -> list[dict[str, Any]]:
    return fetch_dtable_list(
        sess,
        f"/execution-task-{execution_id}.html?zin=1",
        label="execution tasks",
        summarize=summarize_task,
    )


def fetch_task(sess: Session, task_id: str | int) -> dict[str, Any]:
    tid = str(task_id)
    try:
        for row in fetch_my_tasks(sess):
            if str(row.get("id")) == tid:
                return row
    except SystemExit:
        pass

    r = sess.request("GET", f"/task-view-{tid}.html")
    if looks_auth_fail(r):
        raise SystemExit(f"task-view auth fail HTTP {r['status']}")
    html = r["raw"]
    if isinstance(r["data"], list):
        html = zin_main_html(r["data"]) or r["raw"]
    detail = parse_task_view_html(html, tid)
    try:
        comments = list_comments(sess, "task", tid)
        detail["commentsPreview"] = [
            {
                "id": c.get("id"),
                "action": c.get("action"),
                "comment": strip_tags(c.get("comment") or "")[:200],
            }
            for c in comments[:8]
        ]
    except SystemExit:
        pass
    return detail
