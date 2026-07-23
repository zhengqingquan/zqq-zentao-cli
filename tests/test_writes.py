#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline tests for REST write paths and confirmation."""

from __future__ import annotations

import pytest

from zqq_zentao_cli.confirm_util import confirm_or_exit
from zqq_zentao_cli.payload import merge_payload, parse_data_json
from zqq_zentao_cli.rest import writes as write_paths
from zqq_zentao_cli.rest.writes import check_write_response


def test_parse_data_json() -> None:
    assert parse_data_json('{"a":1}') == {"a": 1}
    assert parse_data_json(None) == {}
    with pytest.raises(SystemExit, match="JSON"):
        parse_data_json("{")


def test_merge_payload_flags_win() -> None:
    body = merge_payload(data_json='{"title":"from-data","pri":1}', fields={"title": "flag"})
    assert body == {"title": "flag", "pri": 1}


def test_write_paths() -> None:
    assert write_paths.bug_create_path(12) == "/products/12/bugs"
    assert write_paths.bug_action_path(9, "resolve") == "/bugs/9/resolve"
    assert write_paths.task_create_path(100) == "/executions/100/tasks"
    assert write_paths.task_action_path(3, "assignto") == "/tasks/3/assignto"
    assert write_paths.story_create_path(12) == "/products/12/stories"
    assert write_paths.story_action_path(100, "change") == "/stories/100/change"
    assert write_paths.story_action_path(100, "active") == "/stories/100/active"
    assert write_paths.story_action_path(100, "assign") == "/stories/100/assign"
    assert write_paths.story_action_path(100, "submitreview") == "/stories/100/submitreview"
    assert write_paths.story_action_path(100, "recall") == "/stories/100/recall"
    assert write_paths.todo_create_path() == "/todos"
    assert write_paths.todo_item_path(5) == "/todos/5"
    assert write_paths.todo_action_path(5, "finish") == "/todos/5/finish"
    assert write_paths.todo_action_path(5, "activate") == "/todos/5/activate"
    assert write_paths.testcase_create_path(12) == "/products/12/testcases"
    assert write_paths.testcase_results_path(8) == "/testcases/8/results"
    assert write_paths.testsuite_create_path(12) == "/products/12/testsuites"
    assert write_paths.testtask_create_path(3) == "/projects/3/testtasks"


def test_check_write_response_ok() -> None:
    data = check_write_response(
        {"ok": True, "status": 200, "data": {"id": 1}, "raw": "{}"},
        label="x",
    )
    assert data == {"id": 1}


def test_check_write_response_http_fail() -> None:
    with pytest.raises(SystemExit, match="failed HTTP 400"):
        check_write_response(
            {"ok": False, "status": 400, "data": {"message": "bad"}, "raw": "bad"},
            label="bug resolve",
        )


def test_confirm_yes_skips() -> None:
    confirm_or_exit("should not prompt", yes=True)


def test_confirm_non_tty_requires_yes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("zqq_zentao_cli.confirm_util.sys.stdin.isatty", lambda: False)
    with pytest.raises(SystemExit, match="--yes"):
        confirm_or_exit("write?", yes=False)


def test_cli_task_bug_write_parsers() -> None:
    from zqq_zentao_cli.cli import build_parser, _capability

    parser = build_parser()
    get_t = parser.parse_args(["task", "99"])
    assert get_t.op == "99"
    assert _capability(get_t) == "task"

    start = parser.parse_args(["task", "start", "99", "--yes", "--comment", "go"])
    assert start.op == "start"
    assert start.id == "99"
    assert start.yes is True
    assert _capability(start) == "task.write"

    resolve = parser.parse_args(
        ["bug", "resolve", "7", "--yes", "--resolution", "fixed", "--data", '{"comment":"ok"}']
    )
    assert resolve.op == "resolve"
    assert resolve.id == "7"
    assert _capability(resolve) == "bug.write"

    create_b = parser.parse_args(
        ["bug", "create", "--product", "12", "--title", "t", "--yes"]
    )
    assert create_b.op == "create"
    assert create_b.product == "12"

    get_s = parser.parse_args(["story", "100"])
    assert get_s.op == "100"
    assert _capability(get_s) == "story"

    change = parser.parse_args(
        ["story", "change", "100", "--yes", "--title", "new", "--spec", "desc"]
    )
    assert change.op == "change"
    assert change.id == "100"
    assert change.spec == "desc"
    assert _capability(change) == "story.write"

    create_s = parser.parse_args(
        [
            "story",
            "create",
            "--product",
            "12",
            "--title",
            "need login",
            "--spec",
            "as user…",
            "--yes",
        ]
    )
    assert create_s.op == "create"
    assert create_s.product == "12"
    assert create_s.title == "need login"

    todo_c = parser.parse_args(["todo", "create", "--name", "buy milk", "--yes"])
    assert todo_c.op == "create"
    assert todo_c.name == "buy milk"
    assert _capability(todo_c) == "todo.write"

    todo_f = parser.parse_args(["todo", "finish", "9", "--yes"])
    assert todo_f.op == "finish"
    assert todo_f.id == "9"

    tc = parser.parse_args(
        [
            "testcase",
            "create",
            "--product",
            "12",
            "--title",
            "login",
            "--data",
            '{"steps":[{"desc":"open","expect":"ok"}]}',
            "--yes",
        ]
    )
    assert tc.op == "create"
    assert tc.product == "12"
    assert _capability(tc) == "testcase.write"

    ts = parser.parse_args(
        ["testsuite", "create", "--product", "12", "--name", "smoke", "--yes"]
    )
    assert ts.op == "create"
    assert _capability(ts) == "testsuite.write"

    tt = parser.parse_args(
        [
            "testtask",
            "create",
            "--project",
            "3",
            "--product",
            "12",
            "--execution",
            "20",
            "--build",
            "5",
            "--name",
            "round1",
            "--begin",
            "2026-01-01",
            "--end",
            "2026-01-07",
            "--yes",
        ]
    )
    assert tt.op == "create"
    assert tt.project == "3"
    assert tt.build == "5"
    assert _capability(tt) == "testtask.write"


def test_create_strips_path_scope_from_body() -> None:
    from zqq_zentao_cli.cli_app.body import body_from_args
    from zqq_zentao_cli.cli_app.parser import build_parser
    from zqq_zentao_cli.cli_app.write_dispatch import WRITE_NOUNS

    parser = build_parser()
    bug_args = parser.parse_args(
        ["bug", "create", "--product", "12", "--title", "t", "--yes"]
    )
    body = body_from_args(bug_args)
    assert "product" in body  # flags still merge
    # After dispatch strip (mirror create path):
    body.pop(WRITE_NOUNS["bug"].create_scope, None)
    assert "product" not in body
    assert body["title"] == "t"

    tt_args = parser.parse_args(
        [
            "testtask",
            "create",
            "--project",
            "3",
            "--product",
            "12",
            "--execution",
            "20",
            "--build",
            "5",
            "--name",
            "round1",
            "--begin",
            "2026-01-01",
            "--end",
            "2026-01-07",
            "--yes",
        ]
    )
    tt_body = body_from_args(tt_args)
    tt_body.pop(WRITE_NOUNS["testtask"].create_scope, None)
    assert "project" not in tt_body
    assert tt_body["product"] == "12"
    assert tt_body["execution"] == "20"
    assert tt_body["build"] == "5"
