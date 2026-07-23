#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Canonical task row shape shared by web and REST backends."""

from __future__ import annotations

from typing import Any

# ZenTao view config: suffixActions (see module/task/config.php).
# REST GET /tasks/:id only returns mainActions in operateMenu — omitting edit.
_TASK_SUFFIX_ACTIONS = ("edit", "create", "delete", "view")


def user_field(val: Any) -> str | None:
    """Normalize ZenTao user-ish values to a display/account string."""
    if val is None:
        return None
    if isinstance(val, dict):
        return val.get("account") or val.get("realname") or val.get("name")
    return str(val)


def assigned_account(row: dict[str, Any]) -> str:
    """Account string for filtering (REST assignedTo may be object or string)."""
    assigned = row.get("assignedTo")
    if isinstance(assigned, dict):
        return str(assigned.get("account") or "").strip()
    if assigned is None:
        return ""
    return str(assigned).strip()


def summarize_task(row: dict[str, Any]) -> dict[str, Any]:
    """Map a raw task dict (REST JSON or web dtable) to the CLI table/JSON shape."""
    assigned = row.get("assignedTo")
    opened = row.get("openedBy")
    finished = row.get("finishedBy")
    closed = row.get("closedBy")
    return {
        "id": row.get("id"),
        "name": row.get("name"),
        "status": row.get("status") or row.get("rawStatus"),
        "pri": row.get("pri"),
        "deadline": row.get("deadline"),
        "assignedTo": user_field(assigned) if isinstance(assigned, dict) else assigned,
        "assignedToRealName": (
            assigned.get("realname")
            if isinstance(assigned, dict)
            else row.get("assignedToRealName")
        ),
        "execution": row.get("execution") or row.get("executionID"),
        "executionName": row.get("executionName"),
        "project": row.get("project"),
        "projectName": row.get("projectName"),
        "type": row.get("type"),
        "progress": row.get("progress"),
        "consumed": row.get("consumed"),
        "left": row.get("left"),
        "estimate": row.get("estimate"),
        "openedBy": user_field(opened) if isinstance(opened, dict) else opened,
        "finishedBy": user_field(finished) if isinstance(finished, dict) else finished,
        "closedBy": user_field(closed) if isinstance(closed, dict) else closed,
        "openedDate": row.get("openedDate"),
        "desc": row.get("desc"),
    }


def enrich_task_detail(row: dict[str, Any]) -> dict[str, Any]:
    """Augment task detail so CLI/agents do not confuse mainActions with edit.

    ZenTao ``isClickable(..., 'edit')`` does **not** require activate for closed
    tasks; Web edit is ``/task-edit-{id}.html``, REST ``PUT /tasks/:id`` → same
    ``task::edit``. REST detail only lists ``mainActions`` in ``operateMenu``.
    """
    out = dict(row)
    main = [str(x) for x in (out.get("operateMenu") or []) if x]
    out["operateMenuMain"] = list(main)
    merged = list(main)
    for name in _TASK_SUFFIX_ACTIONS:
        if name not in merged:
            merged.append(name)
    out["operateMenu"] = merged
    # Field edit (name/desc/…) vs status actions (start/finish/activate/…).
    out["canFieldEdit"] = True
    return out
