#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared Web zin + dtable list fetch helper."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .parse import looks_auth_fail, parse_dtable_rows, zin_main_html
from .session import Session

SummarizeFn = Callable[[dict[str, Any]], dict[str, Any]]


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
    r = sess.request("GET", path)
    if looks_auth_fail(r):
        raise SystemExit(f"{label} auth fail HTTP {r['status']}")
    html = zin_main_html(r["data"]) or (r["raw"] if isinstance(r["data"], str) else "")
    if not html and isinstance(r["data"], str):
        html = r["data"]
    rows = parse_dtable_rows(html or "")
    if not rows and "zui-create-dtable" not in (html or ""):
        raise SystemExit(
            f"Failed to parse {label} list HTTP {r['status']} (need zin dtable). "
            f"raw[:120]={r['raw'][:120]!r}"
        )
    return [summarize(x) for x in rows if isinstance(x, dict)]
