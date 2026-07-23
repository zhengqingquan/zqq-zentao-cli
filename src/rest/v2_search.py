# -*- coding: utf-8 -*-
"""APIv2 filters query helpers + name/code client search."""

from __future__ import annotations

from typing import Any, Callable

from ..list_filter import slice_rows

ListResourceFn = Callable[..., dict[str, Any]]


def filters_query_pairs(
    filters: list[dict[str, Any]],
) -> list[tuple[str, str]]:
    """Encode ZenTao APIv2 ``filters[i][field]=…`` query pairs."""
    pairs: list[tuple[str, str]] = []
    for i, f in enumerate(filters):
        for key, val in f.items():
            if val is None:
                continue
            pairs.append((f"filters[{i}][{key}]", str(val)))
    return pairs


def project_name_code_filters(needle: str) -> list[dict[str, Any]]:
    """OR match name include + code include/eq (project search form)."""
    q = (needle or "").strip()
    return [
        {
            "field": "name",
            "operator": "include",
            "value": q,
            "join": "and",
            "group": 1,
        },
        {
            "field": "code",
            "operator": "include",
            "value": q,
            "join": "or",
            "group": 1,
        },
    ]


def match_name_code(row: dict[str, Any], needle: str) -> bool:
    n = (needle or "").strip().lower()
    if not n:
        return False
    hay = " ".join(
        str(row.get(k) or "") for k in ("name", "code", "title", "account", "realname")
    ).lower()
    return n in hay


def search_name_code_rows(
    list_resource: ListResourceFn,
    resource_key: str,
    list_key: str,
    needle: str,
    *,
    page: int = 1,
    limit: int = 50,
    scopes: dict[str, str | int | None] | None = None,
    page_size: int = 200,
) -> dict[str, Any]:
    """Paginate list_resource then client-filter name/code/title."""
    all_rows: list[dict[str, Any]] = []
    seen: set[Any] = set()
    cur = 1
    reported_total = 0
    fetched = 0
    while cur <= 100:
        data = list_resource(
            resource_key,
            page=cur,
            limit=page_size,
            scopes=scopes,
        )
        rows = [r for r in (data.get(list_key) or []) if isinstance(r, dict)]
        if data.get("total") is not None:
            try:
                reported_total = int(data["total"])
            except (TypeError, ValueError):
                pass
        if not rows:
            break
        fetched += len(rows)
        for row in rows:
            if not match_name_code(row, needle):
                continue
            rid = row.get("id")
            key = rid if rid is not None else id(row)
            if key in seen:
                continue
            seen.add(key)
            all_rows.append(row)
        # Some ZenTao APIv2 lists ignore large limit (e.g. always ~15–20).
        if reported_total and fetched >= reported_total:
            break
        if not reported_total and len(rows) < page_size:
            break
        cur += 1

    chunk, total = slice_rows(all_rows, page=page, limit=limit)
    return {
        list_key: chunk,
        "page": max(1, int(page)),
        "total": total,
        "limit": max(1, int(limit)),
    }
