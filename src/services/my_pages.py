#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""my-* list operations via ZenTaoClient."""

from __future__ import annotations

from typing import Any

from ..protocol import ZenTaoClient
from ..web.my_pages import my_page_by_cmd, resolve_browse, uses_rest_default


def list_my(
    client: ZenTaoClient,
    cmd: str,
    *,
    browse_type: str | None = None,
    scope: str | None = None,
) -> list[dict[str, Any]]:
    page = my_page_by_cmd(cmd)
    if page is None:
        raise SystemExit(f"Unknown my-* command: {cmd}")
    resolved_scope, resolved_type = resolve_browse(
        page, browse_type=browse_type, scope=scope
    )
    if uses_rest_default(page, resolved_scope, resolved_type):
        return client.my_tasks()
    return client.my_page(cmd, scope=resolved_scope, browse_type=resolved_type)
