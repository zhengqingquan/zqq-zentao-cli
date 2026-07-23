# -*- coding: utf-8 -*-
"""Comment list display rows (HTML strip). Task/bug use summarize + --pick."""

from __future__ import annotations

from typing import Any

from ..web.parse import strip_tags


def normalize_comment_rows(data: list[Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for a in data:
        if not isinstance(a, dict):
            continue
        comment = strip_tags(a.get("comment") or "") or "(no comment text)"
        rows.append(
            {
                "id": a.get("id"),
                "action": a.get("action"),
                "editable": "editable" if a.get("commentEditable") else "",
                "comment": comment,
            }
        )
    return rows
