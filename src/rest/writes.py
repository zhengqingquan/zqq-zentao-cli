#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""REST write helpers (paths + response checks; no network)."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote


def bug_create_path(product_id: str | int) -> str:
    return f"/products/{quote(str(product_id), safe='')}/bugs"


def bug_item_path(bug_id: str | int) -> str:
    return f"/bugs/{quote(str(bug_id), safe='')}"


def bug_action_path(bug_id: str | int, action: str) -> str:
    # ZenTao: resolve/close/assign/confirm/active
    return f"/bugs/{quote(str(bug_id), safe='')}/{action}"


def task_create_path(execution_id: str | int) -> str:
    return f"/executions/{quote(str(execution_id), safe='')}/tasks"


def task_item_path(task_id: str | int) -> str:
    return f"/tasks/{quote(str(task_id), safe='')}"


def task_action_path(task_id: str | int, action: str) -> str:
    # ZenTao: start/finish/close/active/assignto
    return f"/tasks/{quote(str(task_id), safe='')}/{action}"


def story_create_path(product_id: str | int) -> str:
    return f"/products/{quote(str(product_id), safe='')}/stories"


def story_item_path(story_id: str | int) -> str:
    return f"/stories/{quote(str(story_id), safe='')}"


def story_action_path(story_id: str | int, action: str) -> str:
    # ZenTao: change/close/active/assign/review/submitreview/recall/estimate
    return f"/stories/{quote(str(story_id), safe='')}/{action}"


def check_write_response(r: dict[str, Any], *, label: str) -> Any:
    """Raise SystemExit on HTTP/API failure; return parsed data."""
    status = r.get("status")
    data = r.get("data")
    raw = (r.get("raw") or "")[:200]
    if not r.get("ok"):
        msg = data
        if isinstance(data, dict):
            msg = data.get("message") or data.get("error") or data
        raise SystemExit(f"{label} failed HTTP {status}: {msg!r} raw={raw!r}")
    if isinstance(data, dict):
        err = data.get("error") or data.get("message")
        # success payloads often include id/title; fail shapes vary
        if data.get("status") == "fail" or data.get("result") == "fail":
            raise SystemExit(f"{label} failed: {err or data!r}")
    return data
