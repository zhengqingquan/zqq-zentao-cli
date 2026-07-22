#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for global CLI options and output formatting."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from zqq_zentao_cli import config as cfg
from zqq_zentao_cli.cli import build_parser, main
from zqq_zentao_cli.output import configure_output, package_version, render


def test_version_flag(capsys: pytest.CaptureFixture[str]) -> None:
    parser = build_parser()
    with pytest.raises(SystemExit) as ei:
        parser.parse_args(["-V"])
    assert ei.value.code == 0
    assert package_version() in capsys.readouterr().out


def test_help_lists_global_options() -> None:
    parser = build_parser()
    help_text = parser.format_help()
    for flag in (
        "--version-flag",
        "--format",
        "--silent",
        "--insecure",
        "--timeout",
        "--config",
        "--machine-readable",
        "--pick",
    ):
        assert flag in help_text


def test_tasks_parser_has_status() -> None:
    parser = build_parser()
    args = parser.parse_args(["tasks", "--status", "wait,doing", "--assignedTo", "张三"])
    assert args.status == "wait,doing"
    assert args.assignedTo == "张三"


def test_bugs_parser_has_status_and_users_search() -> None:
    parser = build_parser()
    bugs = parser.parse_args(["bugs", "--product", "1", "--status", "active"])
    assert bugs.status == "active"
    users = parser.parse_args(["users", "--search", "张"])
    assert users.search == "张"


def test_pick_fields_parse() -> None:
    from zqq_zentao_cli.cli import _fields_for, _parse_pick

    parser = build_parser()
    args = parser.parse_args(["--pick", "id,status,title", "tasks"])
    assert _parse_pick(args) == ["id", "status", "title"]
    assert _fields_for("tasks", args) == ["id", "status", "title"]
    args2 = parser.parse_args(["tasks"])
    assert _fields_for("tasks", args2) == [
        "id",
        "status",
        "pri",
        "deadline",
        "executionName",
        "name",
    ]


def test_render_markdown_list() -> None:
    configure_output(format="markdown")
    text = render(
        [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}],
        is_list=True,
        fields=["id", "name"],
    )
    assert "| id | name |" in text
    assert "| 1 | a |" in text


def test_render_markdown_object() -> None:
    configure_output(format="markdown")
    text = render({"id": 9, "title": "x"}, is_list=False)
    assert "* id: 9" in text
    assert "* title: x" in text


def test_render_json_wrapper() -> None:
    configure_output(format="json", machine_readable=True)
    text = render({"id": 1}, is_list=False)
    payload = json.loads(text)
    assert payload == {"status": "success", "data": {"id": 1}}


def test_render_raw() -> None:
    configure_output(format="raw", machine_readable=True)
    text = render({"id": 1}, is_list=False)
    assert json.loads(text) == {"id": 1}


def test_silent_suppresses_output(capsys: pytest.CaptureFixture[str]) -> None:
    from zqq_zentao_cli.output import emit

    configure_output(format="json", silent=True)
    emit({"ok": True})
    assert capsys.readouterr().out == ""


def test_config_path_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cfg, "_config_path_override", None)
    custom = tmp_path / "custom.json"
    custom.write_text(
        json.dumps(
            {
                "profiles": [{"server": "https://example.com", "account": "u1"}],
                "currentProfile": "u1@https://example.com",
            }
        ),
        encoding="utf-8",
    )
    cfg.set_config_path(str(custom))
    assert cfg.get_config_path() == custom.resolve()
    profile = cfg.load_profile()
    assert profile["account"] == "u1"
    monkeypatch.setattr(cfg, "_config_path_override", None)


def test_config_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cfg, "_config_path_override", None)
    custom = tmp_path / "env.json"
    custom.write_text("{}", encoding="utf-8")
    monkeypatch.setenv("ZENTAO_CONFIG_FILE", str(custom))
    assert cfg.get_config_path() == custom.resolve()
    monkeypatch.delenv("ZENTAO_CONFIG_FILE", raising=False)


def test_resolve_timeout() -> None:
    assert cfg.resolve_timeout_seconds(None) == 60.0
    assert cfg.resolve_timeout_seconds(1500) == 1.5
    with pytest.raises(SystemExit):
        cfg.resolve_timeout_seconds(0)


def test_main_rejects_unknown_format() -> None:
    with pytest.raises(SystemExit):
        main(["--format", "yaml", "whoami"])
