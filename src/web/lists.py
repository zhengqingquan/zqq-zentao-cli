#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared Web zin + dtable list fetch helper."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .parse import looks_auth_fail, parse_dtable_rows, zin_main_html
from .session import Session

SummarizeFn = Callable[[dict[str, Any]], dict[str, Any]]
PathForPageFn = Callable[[int, int], str]


def _fetch_dtable_html(sess: Session, path: str, *, label: str) -> str:
    r = sess.request("GET", path)
    if looks_auth_fail(r):
        raise SystemExit(f"{label} auth fail HTTP {r['status']}")
    html = zin_main_html(r["data"]) or (r["raw"] if isinstance(r["data"], str) else "")
    if not html and isinstance(r["data"], str):
        html = r["data"]
    return html or ""


def fetch_dtable_list(
    sess: Session,
    path: str,
    *,
    label: str,
    summarize: SummarizeFn,
) -> list[dict[str, Any]]:
    """GET a zin page, parse dtable rows, map via ``summarize``.

    Empty dtable (``data:[]`` with ``zui-create-dtable`` present) is success ``[]``.
    Missing dtable markup is a parse failure.
    """
    html = _fetch_dtable_html(sess, path, label=label)
    rows = parse_dtable_rows(html)
    if not rows and "zui-create-dtable" not in html:
        raise SystemExit(
            f"Failed to parse {label} list (need zin dtable). path={path!r}"
        )
    return [summarize(x) for x in rows if isinstance(x, dict)]


def fetch_dtable_list_paginated(
    sess: Session,
    path_for_page: PathForPageFn,
    *,
    label: str,
    summarize: SummarizeFn,
    rec_per_page: int = 200,
    max_pages: int = 100,
) -> list[dict[str, Any]]:
    """Fetch all dtable pages (large recPerPage + pageID loop)."""
    rec_per_page = max(1, int(rec_per_page))
    all_rows: list[dict[str, Any]] = []
    seen: set[Any] = set()
    for page_id in range(1, max_pages + 1):
        path = path_for_page(page_id, rec_per_page)
        html = _fetch_dtable_html(sess, path, label=f"{label} page={page_id}")
        rows = [r for r in parse_dtable_rows(html) if isinstance(r, dict)]
        if not rows and page_id == 1 and "zui-create-dtable" not in html:
            raise SystemExit(
                f"Failed to parse {label} list (need zin dtable). path={path!r}"
            )
        if not rows:
            break
        for row in rows:
            rid = row.get("id")
            key = rid if rid is not None else id(row)
            if key in seen:
                continue
            seen.add(key)
            all_rows.append(row)
        if len(rows) < rec_per_page:
            break
    return [summarize(x) for x in all_rows]


def with_query(path: str, **params: str | int) -> str:
    """Merge query params into a PATHINFO URL (keeps existing zin=1 etc.)."""
    parts = urlsplit(path)
    q = dict(parse_qsl(parts.query, keep_blank_values=True))
    for k, v in params.items():
        q[str(k)] = str(v)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(q), parts.fragment))
