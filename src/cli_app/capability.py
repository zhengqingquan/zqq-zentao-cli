# -*- coding: utf-8 -*-
"""Map parsed args to capabilities / TLS override."""

from __future__ import annotations

import argparse

from ..web.my_pages import my_page_by_cmd, resolve_browse, uses_rest_default
from .body import is_id_token


def capability(args: argparse.Namespace) -> str:
    if args.cmd == "comment":
        return f"comment.{args.c_cmd}"
    if args.cmd == "tasks" and not args.execution:
        return "tasks.list"
    if args.cmd == "task":
        if is_id_token(args.op) and args.id is None:
            return "task"
        if str(args.op).strip().lower() == "options":
            return "task.options"
        return "task.write"
    if args.cmd == "bug":
        return "bug" if (is_id_token(args.op) and args.id is None) else "bug.write"
    if args.cmd == "story":
        return "story" if (is_id_token(args.op) and args.id is None) else "story.write"
    if args.cmd in ("todo", "testcase", "testsuite", "testtask"):
        if is_id_token(args.op) and args.id is None:
            return args.cmd
        return f"{args.cmd}.write"
    page = my_page_by_cmd(args.cmd)
    if page is not None:
        scope, browse_type = resolve_browse(
            page,
            browse_type=getattr(args, "browse_type", None),
            scope=getattr(args, "scope", None),
        )
        if uses_rest_default(page, scope, browse_type):
            return page.cmd
        return "my-page"
    return args.cmd


def cli_insecure(args: argparse.Namespace) -> bool | None:
    if args.insecure:
        return True
    if args.secure:
        return False
    return None
