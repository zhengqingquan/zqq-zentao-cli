#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""My tasks / execution tasks / task detail (PATHINFO)."""

from __future__ import annotations

from typing import Any

from .comments import list_comments
from .parse import (
    looks_auth_fail,
    parse_dtable_rows,
    parse_task_view_html,
    strip_tags,
    summarize_task_row,
    zin_main_html,
)
from .session import Session


def fetch_my_tasks(sess: Session) -> list[dict[str, Any]]:
    r = sess.request("GET", "/my-work-task-assignedTo.html?zin=1")
    if looks_auth_fail(r):
        raise SystemExit(f"my-tasks auth fail HTTP {r['status']}")
    html = zin_main_html(r["data"]) or (r["raw"] if isinstance(r["data"], str) else "")
    if not html and isinstance(r["data"], str):
        html = r["data"]
    rows = parse_dtable_rows(html)
    if not rows:
        raise SystemExit(
            f"Failed to parse my-tasks list HTTP {r['status']} (need zin dtable). "
            f"raw[:120]={r['raw'][:120]!r}"
        )
    return [summarize_task_row(x) for x in rows]


def fetch_execution_tasks(sess: Session, execution_id: str | int) -> list[dict[str, Any]]:
    r = sess.request("GET", f"/execution-task-{execution_id}.html?zin=1")
    if looks_auth_fail(r):
        raise SystemExit(f"execution tasks auth fail HTTP {r['status']}")
    html = zin_main_html(r["data"]) or ""
    if not html and isinstance(r["data"], str):
        html = r["data"]
    rows = parse_dtable_rows(html)
    if not rows:
        raise SystemExit(
            f"Failed to parse execution task list HTTP {r['status']}. "
            f"raw[:120]={r['raw'][:120]!r}"
        )
    return [summarize_task_row(x) for x in rows]


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
