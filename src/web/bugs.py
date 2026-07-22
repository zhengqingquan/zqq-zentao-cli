#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""My bugs (PATHINFO / my-work-bug-* / my-contribute-bug-*)."""

from __future__ import annotations

from typing import Any

from .my_pages import fetch_my_page, my_page_by_cmd
from .session import Session


def fetch_my_bugs(
    sess: Session,
    *,
    browse_type: str | None = None,
    scope: str | None = None,
) -> list[dict[str, Any]]:
    page = my_page_by_cmd("my-bugs")
    assert page is not None
    return fetch_my_page(sess, page, browse_type=browse_type, scope=scope)
