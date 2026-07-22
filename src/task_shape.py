#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Canonical task row shape shared by web and REST backends."""

from __future__ import annotations

from typing import Any


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
        "openedDate": row.get("openedDate"),
        "desc": row.get("desc"),
    }
