#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""My bugs (PATHINFO / my-work-bug-*)."""

from __future__ import annotations

from typing import Any

from ..bug_shape import summarize_bug
from .parse import looks_auth_fail, parse_dtable_rows, zin_main_html
from .session import Session

# ZenTao 22.3: my::work → my::bug → bug->getUserBugs(assignedTo).
# assignedTo excludes closed bugs (see bug::getUserBugs workBug branch).
_MY_BUGS_PATH = "/my-work-bug-assignedTo.html?zin=1"


def fetch_my_bugs(sess: Session) -> list[dict[str, Any]]:
    r = sess.request("GET", _MY_BUGS_PATH)
    if looks_auth_fail(r):
        raise SystemExit(f"my-bugs auth fail HTTP {r['status']}")
    html = zin_main_html(r["data"]) or (r["raw"] if isinstance(r["data"], str) else "")
    if not html and isinstance(r["data"], str):
        html = r["data"]
    rows = parse_dtable_rows(html)
    if not rows and "zui-create-dtable" not in (html or ""):
        raise SystemExit(
            f"Failed to parse my-bugs list HTTP {r['status']} (need zin dtable). "
            f"raw[:120]={r['raw'][:120]!r}"
        )
    return [summarize_bug(x) for x in rows]
