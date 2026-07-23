#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Client-side user-field / status / pri filters for list payloads."""

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


def parse_status_set(status: str | None) -> set[str] | None:
    """Parse comma-separated statuses into a non-empty set, or None."""
    if status is None:
        return None
    parts = {p.strip() for p in str(status).split(",") if p.strip()}
    return parts or None


def row_status(row: dict[str, Any]) -> str:
    val = row.get("status")
    if isinstance(val, dict):
        return str(val.get("code") or val.get("name") or val.get("status") or "").strip()
    if val is None:
        return ""
    return str(val).strip()


def row_pri(row: dict[str, Any]) -> str:
    val = row.get("pri")
    if val is None:
        val = row.get("priority")
    if val is None:
        return ""
    return str(val).strip()


def parse_pri_set(pri: str | None) -> set[str] | None:
    if pri is None:
        return None
    parts = {p.strip() for p in str(pri).split(",") if p.strip()}
    return parts or None


def filter_rows(
    rows: list[dict[str, Any]],
    *,
    assigned_to: str | None = None,
    opened_by: str | None = None,
    finished_by: str | None = None,
    resolved_by: str | None = None,
    closed_by: str | None = None,
    status: str | None = None,
    pri: str | None = None,
) -> list[dict[str, Any]]:
    """Keep rows matching optional account / status / pri filters."""
    want_assigned = (assigned_to or "").strip() or None
    want_opened = (opened_by or "").strip() or None
    want_finished = (finished_by or "").strip() or None
    want_resolved = (resolved_by or "").strip() or None
    want_closed = (closed_by or "").strip() or None
    want_status = parse_status_set(status)
    want_pri = parse_pri_set(pri)
    if not any(
        (
            want_assigned,
            want_opened,
            want_finished,
            want_resolved,
            want_closed,
            want_status,
            want_pri,
        )
    ):
        return rows
    out: list[dict[str, Any]] = []
    for row in rows:
        if want_assigned and row_account(row, "assignedTo") != want_assigned:
            continue
        if want_opened and row_account(row, "openedBy") != want_opened:
            continue
        if want_finished and row_account(row, "finishedBy") != want_finished:
            continue
        if want_resolved and row_account(row, "resolvedBy") != want_resolved:
            continue
        if want_closed and row_account(row, "closedBy") != want_closed:
            continue
        if want_status and row_status(row) not in want_status:
            continue
        if want_pri and row_pri(row) not in want_pri:
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
    finished_by: str | None = None,
    resolved_by: str | None = None,
    closed_by: str | None = None,
    status: str | None = None,
    pri: str | None = None,
    page: int | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    """Filter ``payload[list_key]`` and refresh total / optional page slice."""
    rows = payload.get(list_key)
    if not isinstance(rows, list):
        return payload
    dict_rows = [r for r in rows if isinstance(r, dict)]
    filtered = filter_rows(
        dict_rows,
        assigned_to=assigned_to,
        opened_by=opened_by,
        finished_by=finished_by,
        resolved_by=resolved_by,
        closed_by=closed_by,
        status=status,
        pri=pri,
    )
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


def filter_rows_by_search(
    rows: list[dict[str, Any]], q: str, *, fields: tuple[str, ...] = ("name", "title", "code")
) -> list[dict[str, Any]]:
    """Case-insensitive substring match on common text fields."""
    needle = (q or "").strip().lower()
    if not needle:
        return rows
    out: list[dict[str, Any]] = []
    for row in rows:
        hay_parts: list[str] = []
        for f in fields:
            val = row.get(f)
            if val is None:
                continue
            hay_parts.append(str(val))
        if needle in " ".join(hay_parts).lower():
            out.append(row)
    return out
