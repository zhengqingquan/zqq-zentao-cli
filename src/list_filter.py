#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Client-side user-field filters for list payloads (assignedTo / openedBy)."""

from __future__ import annotations

from typing import Any


def row_account(row: dict[str, Any], field: str) -> str:
    """Account string from a user-ish column (object or string)."""
    val = row.get(field)
    if isinstance(val, dict):
        return str(val.get("account") or "").strip()
    if val is None:
        return ""
    return str(val).strip()


def filter_rows(
    rows: list[dict[str, Any]],
    *,
    assigned_to: str | None = None,
    opened_by: str | None = None,
) -> list[dict[str, Any]]:
    """Keep rows matching optional account filters (case-sensitive account)."""
    want_assigned = (assigned_to or "").strip() or None
    want_opened = (opened_by or "").strip() or None
    if not want_assigned and not want_opened:
        return rows
    out: list[dict[str, Any]] = []
    for row in rows:
        if want_assigned and row_account(row, "assignedTo") != want_assigned:
            continue
        if want_opened and row_account(row, "openedBy") != want_opened:
            continue
        out.append(row)
    return out


def slice_rows(
    rows: list[dict[str, Any]],
    *,
    page: int = 1,
    limit: int = 50,
) -> tuple[list[dict[str, Any]], int]:
    """Client-side page slice; returns (chunk, total)."""
    page = max(1, int(page))
    limit = max(1, int(limit))
    total = len(rows)
    start = (page - 1) * limit
    return rows[start : start + limit], total


def apply_user_filters(
    payload: dict[str, Any],
    list_key: str,
    *,
    assigned_to: str | None = None,
    opened_by: str | None = None,
    page: int | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    """Filter ``payload[list_key]`` and refresh total / optional page slice."""
    rows = payload.get(list_key)
    if not isinstance(rows, list):
        return payload
    dict_rows = [r for r in rows if isinstance(r, dict)]
    filtered = filter_rows(dict_rows, assigned_to=assigned_to, opened_by=opened_by)
    out = dict(payload)
    if page is not None and limit is not None:
        chunk, total = slice_rows(filtered, page=page, limit=limit)
        out[list_key] = chunk
        out["total"] = total
        out["page"] = max(1, int(page))
        out["limit"] = max(1, int(limit))
    else:
        out[list_key] = filtered
        out["total"] = len(filtered)
    return out
