#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""My bugs (PATHINFO / my-work-bug-*)."""

from __future__ import annotations

from typing import Any

from ..bug_shape import summarize_bug
from .lists import fetch_dtable_list
from .session import Session

# ZenTao 22.3: my::work → my::bug → bug->getUserBugs(assignedTo).
# assignedTo excludes closed bugs (see bug::getUserBugs workBug branch).
_MY_BUGS_PATH = "/my-work-bug-assignedTo.html?zin=1"


def fetch_my_bugs(sess: Session) -> list[dict[str, Any]]:
    return fetch_dtable_list(
        sess,
        _MY_BUGS_PATH,
        label="my-bugs",
        summarize=summarize_bug,
    )
