# -*- coding: utf-8 -*-
"""Default table columns and --pick handling."""

from __future__ import annotations

import argparse

from ..web.my_pages import MY_PAGES

_TASK_FIELDS = ["id", "status", "pri", "deadline", "executionName", "name"]
_BUG_FIELDS = ["id", "status", "severity", "pri", "productName", "title"]
_STORY_FIELDS = ["id", "status", "pri", "stage", "title"]
_USER_FIELDS = ["account", "realname"]

DEFAULT_LIST_FIELDS: dict[str, list[str]] = {
    "tasks": _TASK_FIELDS,
    "bugs": _BUG_FIELDS,
    "stories": _STORY_FIELDS,
    "users": _USER_FIELDS,
}
for _mp in MY_PAGES.values():
    DEFAULT_LIST_FIELDS[_mp.cmd] = list(_mp.table_fields)


def parse_pick(args: argparse.Namespace) -> list[str] | None:
    raw = getattr(args, "pick", None)
    if not raw:
        return None
    fields = [p.strip() for p in str(raw).split(",") if p.strip()]
    return fields or None


def fields_for(cmd: str, args: argparse.Namespace) -> list[str] | None:
    picked = parse_pick(args)
    if picked:
        return picked
    return DEFAULT_LIST_FIELDS.get(cmd)
