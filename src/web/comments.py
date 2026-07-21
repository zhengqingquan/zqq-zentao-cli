#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Comment list / add / edit (PATHINFO)."""

from __future__ import annotations

from typing import Any

from .parse import html_comment, is_write_success, looks_auth_fail, looks_write_fail
from .session import Session


def list_comments(sess: Session, object_type: str, object_id: str | int) -> list[Any]:
    r = sess.request("GET", f"/action-ajaxGetList-{object_type}-{object_id}.html")
    if not isinstance(r["data"], list):
        r = sess.request("GET", f"/action-ajaxGetList-{object_type}-{object_id}.json")
    if looks_auth_fail(r) or not isinstance(r["data"], list):
        raise SystemExit(f"list failed HTTP {r['status']}: {r['raw'][:160]}")
    return r["data"]


def add_comment(sess: Session, object_type: str, object_id: str | int, comment: str) -> dict:
    sess.request(
        "GET",
        f"/action-comment-{object_type}-{object_id}.html",
        modal=True,
    )
    r = sess.request(
        "POST",
        f"/action-comment-{object_type}-{object_id}.html",
        form={"actioncomment": html_comment(comment)},
        modal=True,
    )
    if looks_auth_fail(r) or looks_write_fail(r) or not is_write_success(r["data"]):
        raise SystemExit(f"add failed HTTP {r['status']}: {r['raw'][:160]}")
    return r


def edit_comment(sess: Session, action_id: str | int, comment: str) -> dict:
    sess.request("GET", f"/action-editComment-{action_id}.html", modal=True)
    r = sess.request(
        "POST",
        f"/action-editComment-{action_id}.html",
        form={"lastComment": html_comment(comment)},
        modal=True,
    )
    if looks_auth_fail(r) or looks_write_fail(r) or not is_write_success(r["data"]):
        raise SystemExit(f"edit failed HTTP {r['status']}: {r['raw'][:160]}")
    return r
