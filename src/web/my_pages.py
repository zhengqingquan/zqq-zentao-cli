#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Registry for ZenTao 22.3 my-work / my-contribute / my-todo Web pages."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

from ..bug_shape import summarize_bug
from ..my_shape import (
    summarize_feedback,
    summarize_story,
    summarize_testcase,
    summarize_testtask,
    summarize_ticket,
    summarize_todo,
)
from ..task_shape import summarize_task
from .lists import fetch_dtable_list_paginated
from .session import Session

ScopeName = Literal["work", "contribute", "todo"]
SummarizeFn = Callable[[dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True)
class MyPage:
    """One ``my-<noun>`` CLI command backed by a Web PATHINFO list."""

    cmd: str
    help: str
    mode: str
    """PATHINFO mode segment (task/bug/story/…) or unused for todo."""

    default_scope: ScopeName
    default_type: str
    work_types: tuple[str, ...] = ()
    contribute_types: tuple[str, ...] = ()
    todo_types: tuple[str, ...] = ()
    table_fields: tuple[str, ...] = ()
    summarize: SummarizeFn = summarize_task
    """REST only for default work+assignedTo my-tasks."""
    rest_default: bool = False


MY_PAGES: dict[str, MyPage] = {}


def _add(page: MyPage) -> None:
    if page.cmd in MY_PAGES:
        raise ValueError(f"duplicate my page: {page.cmd}")
    MY_PAGES[page.cmd] = page


_add(
    MyPage(
        cmd="my-tasks",
        help="My tasks (work/contribute)",
        mode="task",
        default_scope="work",
        default_type="assignedTo",
        work_types=("assignedTo",),
        contribute_types=(
            "openedBy",
            "finishedBy",
            "myInvolved",
            "closedBy",
            "canceledBy",
            "assignedBy",
        ),
        table_fields=("id", "status", "pri", "deadline", "executionName", "name"),
        summarize=summarize_task,
        rest_default=True,
    )
)
_add(
    MyPage(
        cmd="my-bugs",
        help="My bugs (work/contribute; web only)",
        mode="bug",
        default_scope="work",
        default_type="assignedTo",
        work_types=("assignedTo",),
        contribute_types=("openedBy", "resolvedBy", "closedBy", "assignedBy"),
        table_fields=("id", "status", "severity", "pri", "productName", "title"),
        summarize=summarize_bug,
    )
)
_add(
    MyPage(
        cmd="my-stories",
        help="My stories (work/contribute; web only)",
        mode="story",
        default_scope="work",
        default_type="assignedTo",
        work_types=("assignedTo", "reviewBy"),
        contribute_types=("openedBy", "reviewedBy", "closedBy", "assignedBy"),
        table_fields=("id", "status", "pri", "stage", "title"),
        summarize=summarize_story,
    )
)
_add(
    MyPage(
        cmd="my-todos",
        help="My todos (web; /my-todo-*.html)",
        mode="todo",
        default_scope="todo",
        default_type="all",
        todo_types=("all", "undone", "future", "today", "thisWeek", "thisMonth"),
        table_fields=("id", "status", "pri", "date", "name"),
        summarize=summarize_todo,
    )
)
_add(
    MyPage(
        cmd="my-testcases",
        help="My testcases (work/contribute; web only)",
        mode="testcase",
        default_scope="work",
        default_type="assigntome",
        work_types=("assigntome",),
        contribute_types=("openedbyme",),
        table_fields=("id", "status", "pri", "type", "title"),
        summarize=summarize_testcase,
    )
)
_add(
    MyPage(
        cmd="my-testtasks",
        help="My testtasks (work/contribute; web only)",
        mode="testtask",
        default_scope="work",
        default_type="assignedTo",
        work_types=("assignedTo", "wait"),
        contribute_types=("done",),
        table_fields=("id", "status", "pri", "begin", "end", "name"),
        summarize=summarize_testtask,
    )
)
_add(
    MyPage(
        cmd="my-feedbacks",
        help="My feedbacks (work; web only)",
        mode="feedback",
        default_scope="work",
        default_type="assigntome",
        work_types=("assigntome", "assignedby"),
        contribute_types=("openedbyme",),
        table_fields=("id", "status", "pri", "title"),
        summarize=summarize_feedback,
    )
)
_add(
    MyPage(
        cmd="my-tickets",
        help="My tickets (work; web only)",
        mode="ticket",
        default_scope="work",
        default_type="assignedtome",
        work_types=("assignedtome",),
        contribute_types=("openedbyme",),
        table_fields=("id", "status", "pri", "title"),
        summarize=summarize_ticket,
    )
)


def my_page_by_cmd(cmd: str) -> MyPage | None:
    return MY_PAGES.get(cmd)


def my_page_cmds() -> list[str]:
    return list(MY_PAGES.keys())


def resolve_browse(
    page: MyPage,
    *,
    browse_type: str | None = None,
    scope: str | None = None,
) -> tuple[ScopeName, str]:
    """Resolve (scope, browseType) from CLI flags.

    Rules:
    - Default → page.default_scope + page.default_type
    - Explicit --scope must be valid for the page
    - Explicit --type: pick unique matching scope; if ambiguous require --scope
    """
    raw_type = (browse_type or "").strip() or None
    raw_scope = (scope or "").strip().lower() or None

    if raw_scope and raw_scope not in ("work", "contribute", "todo"):
        raise SystemExit(f"Invalid --scope={scope!r}; expected work|contribute|todo")

    if page.default_scope == "todo":
        if raw_scope and raw_scope != "todo":
            raise SystemExit(f"{page.cmd} only supports --scope todo (or omit)")
        t = raw_type or page.default_type
        if page.todo_types and t not in page.todo_types:
            raise SystemExit(
                f"Invalid --type={t!r} for {page.cmd}; "
                f"expected one of: {', '.join(page.todo_types)}"
            )
        return "todo", t

    if raw_scope == "todo":
        raise SystemExit(f"{page.cmd} does not use --scope todo")

    t = raw_type or page.default_type
    in_work = t in page.work_types
    in_contrib = t in page.contribute_types

    if raw_scope:
        if raw_scope == "work" and page.work_types and t not in page.work_types:
            raise SystemExit(
                f"Invalid --type={t!r} for {page.cmd} --scope work; "
                f"expected: {', '.join(page.work_types)}"
            )
        if raw_scope == "contribute" and page.contribute_types and t not in page.contribute_types:
            raise SystemExit(
                f"Invalid --type={t!r} for {page.cmd} --scope contribute; "
                f"expected: {', '.join(page.contribute_types)}"
            )
        return raw_scope, t  # type: ignore[return-value]

    if not raw_type:
        return page.default_scope, page.default_type

    if in_work and not in_contrib:
        return "work", t
    if in_contrib and not in_work:
        return "contribute", t
    if in_work and in_contrib:
        raise SystemExit(
            f"--type={t!r} is ambiguous for {page.cmd}; "
            "pass --scope work|contribute"
        )
    allowed = (*page.work_types, *page.contribute_types)
    raise SystemExit(
        f"Invalid --type={t!r} for {page.cmd}; expected one of: {', '.join(allowed)}"
    )


def build_path(
    page: MyPage,
    scope: ScopeName,
    browse_type: str,
    *,
    page_id: int = 1,
    rec_per_page: int = 200,
    param: int | str = 0,
    order_by: str = "id_desc",
    rec_total: int = 0,
) -> str:
    """Build PATHINFO URL with zin=1 and pager args (ZenTao 22.3).

    work/contribute → my::{work|contribute} → module method pager:
      /my-{scope}-{mode}-{browseType}-{param}-{orderBy}-{recTotal}-{recPerPage}-{pageID}.html
    todo → my::todo:
      /my-todo-{browseType}-{userID}-{status}-{orderBy}-{recTotal}-{recPerPage}-{pageID}.html
    """
    page_id = max(1, int(page_id))
    rec_per_page = max(1, int(rec_per_page))
    if scope == "todo":
        # userID empty; status=all
        return (
            f"/my-todo-{browse_type}--all-{order_by}-"
            f"{rec_total}-{rec_per_page}-{page_id}.html?zin=1"
        )
    return (
        f"/my-{scope}-{page.mode}-{browse_type}-{param}-{order_by}-"
        f"{rec_total}-{rec_per_page}-{page_id}.html?zin=1"
    )


def fetch_my_page(
    sess: Session,
    page: MyPage,
    *,
    browse_type: str | None = None,
    scope: str | None = None,
    rec_per_page: int = 200,
) -> list[dict[str, Any]]:
    resolved_scope, resolved_type = resolve_browse(
        page, browse_type=browse_type, scope=scope
    )
    label = f"{page.cmd} ({resolved_scope}/{resolved_type})"

    def path_for_page(page_id: int, size: int) -> str:
        return build_path(
            page,
            resolved_scope,
            resolved_type,
            page_id=page_id,
            rec_per_page=size,
        )

    return fetch_dtable_list_paginated(
        sess,
        path_for_page,
        label=label,
        summarize=page.summarize,
        rec_per_page=rec_per_page,
    )


def uses_rest_default(page: MyPage, scope: ScopeName, browse_type: str) -> bool:
    """True when dual-backend REST my-tasks path applies."""
    return bool(
        page.rest_default
        and scope == "work"
        and browse_type == page.default_type
    )
