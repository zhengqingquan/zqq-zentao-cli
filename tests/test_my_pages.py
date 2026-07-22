#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline tests for my-* page registry."""

from __future__ import annotations

import pytest

from zqq_zentao_cli.web.my_pages import (
    build_path,
    my_page_by_cmd,
    resolve_browse,
    uses_rest_default,
)


def test_resolve_defaults() -> None:
    page = my_page_by_cmd("my-bugs")
    assert page is not None
    assert resolve_browse(page) == ("work", "assignedTo")


def test_resolve_contribute_type() -> None:
    page = my_page_by_cmd("my-bugs")
    assert page is not None
    assert resolve_browse(page, browse_type="resolvedBy") == ("contribute", "resolvedBy")


def test_resolve_explicit_scope() -> None:
    page = my_page_by_cmd("my-tasks")
    assert page is not None
    assert resolve_browse(page, browse_type="openedBy", scope="contribute") == (
        "contribute",
        "openedBy",
    )


def test_resolve_invalid_type() -> None:
    page = my_page_by_cmd("my-stories")
    assert page is not None
    with pytest.raises(SystemExit, match="Invalid --type"):
        resolve_browse(page, browse_type="nope")


def test_todo_path_and_types() -> None:
    page = my_page_by_cmd("my-todos")
    assert page is not None
    scope, browse = resolve_browse(page, browse_type="today")
    assert (scope, browse) == ("todo", "today")
    assert build_path(page, scope, browse) == "/my-todo-today.html?zin=1"


def test_work_path() -> None:
    page = my_page_by_cmd("my-stories")
    assert page is not None
    assert (
        build_path(page, "work", "assignedTo")
        == "/my-work-story-assignedTo.html?zin=1"
    )


def test_uses_rest_default_only_for_my_tasks() -> None:
    tasks = my_page_by_cmd("my-tasks")
    bugs = my_page_by_cmd("my-bugs")
    assert tasks is not None and bugs is not None
    assert uses_rest_default(tasks, "work", "assignedTo")
    assert not uses_rest_default(tasks, "contribute", "openedBy")
    assert not uses_rest_default(bugs, "work", "assignedTo")


def test_cli_registers_my_pages() -> None:
    from zqq_zentao_cli.cli import build_parser

    parser = build_parser()
    args = parser.parse_args(["my-bugs", "--type", "openedBy"])
    assert args.cmd == "my-bugs"
    assert args.browse_type == "openedBy"
    stories = parser.parse_args(["my-stories", "--scope", "contribute", "--type", "openedBy"])
    assert stories.scope == "contribute"
    assert stories.browse_type == "openedBy"
