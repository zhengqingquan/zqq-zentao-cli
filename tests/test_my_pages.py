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


def test_work_path() -> None:
    page = my_page_by_cmd("my-stories")
    assert page is not None
    assert (
        build_path(page, "work", "assignedTo")
        == "/my-work-story-assignedTo-0-id_desc-0-200-1.html?zin=1"
    )


def test_requirement_and_epic_registered() -> None:
    req = my_page_by_cmd("my-requirements")
    epic = my_page_by_cmd("my-epics")
    assert req is not None and epic is not None
    assert resolve_browse(req) == ("work", "assignedTo")
    assert (
        build_path(req, "work", "assignedTo")
        == "/my-work-requirement-assignedTo-0-id_desc-0-200-1.html?zin=1"
    )
    assert (
        build_path(epic, "contribute", "openedBy")
        == "/my-contribute-epic-openedBy-0-id_desc-0-200-1.html?zin=1"
    )


def test_docs_contribute_only() -> None:
    page = my_page_by_cmd("my-docs")
    assert page is not None
    assert resolve_browse(page) == ("contribute", "openedbyme")
    assert resolve_browse(page, browse_type="editedbyme") == ("contribute", "editedbyme")
    assert (
        build_path(page, "contribute", "openedbyme")
        == "/my-contribute-doc-openedbyme-0-id_desc-0-200-1.html?zin=1"
    )


def test_projects_browse_path() -> None:
    page = my_page_by_cmd("my-projects")
    assert page is not None
    assert resolve_browse(page) == ("browse", "doing")
    assert (
        build_path(page, "browse", "doing")
        == "/my-project-doing-id_desc-0-200-1.html?zin=1"
    )


def test_executions_browse_path() -> None:
    page = my_page_by_cmd("my-executions")
    assert page is not None
    assert resolve_browse(page, browse_type="done") == ("browse", "done")
    assert (
        build_path(page, "browse", "undone")
        == "/my-execution-undone-id_desc-0-200-1.html?zin=1"
    )


def test_todo_path_and_types() -> None:
    page = my_page_by_cmd("my-todos")
    assert page is not None
    scope, browse = resolve_browse(page, browse_type="today")
    assert (scope, browse) == ("todo", "today")
    assert (
        build_path(page, scope, browse)
        == "/my-todo-today--all-id_desc-0-200-1.html?zin=1"
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
