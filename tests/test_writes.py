#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline tests for REST write paths and confirmation."""

from __future__ import annotations

import pytest

from zqq_zentao_cli.confirm_util import confirm_or_exit
from zqq_zentao_cli.payload import merge_payload, parse_data_json
from zqq_zentao_cli.rest.writes import (
    bug_action_path,
    bug_create_path,
    check_write_response,
    story_action_path,
    story_create_path,
    task_action_path,
    task_create_path,
)


def test_parse_data_json() -> None:
    assert parse_data_json('{"a":1}') == {"a": 1}
    assert parse_data_json(None) == {}
    with pytest.raises(SystemExit, match="JSON"):
        parse_data_json("{")


def test_merge_payload_flags_win() -> None:
    body = merge_payload(data_json='{"title":"from-data","pri":1}', fields={"title": "flag"})
    assert body == {"title": "flag", "pri": 1}


def test_write_paths() -> None:
    assert bug_create_path(12) == "/products/12/bugs"
    assert bug_action_path(9, "resolve") == "/bugs/9/resolve"
    assert task_create_path(100) == "/executions/100/tasks"
    assert task_action_path(3, "assignto") == "/tasks/3/assignto"
    assert story_create_path(12) == "/products/12/stories"
    assert story_action_path(100, "change") == "/stories/100/change"
    assert story_action_path(100, "active") == "/stories/100/active"
    assert story_action_path(100, "assign") == "/stories/100/assign"
    assert story_action_path(100, "submitreview") == "/stories/100/submitreview"
    assert story_action_path(100, "recall") == "/stories/100/recall"


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
