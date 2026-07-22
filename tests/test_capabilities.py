#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline tests for backend capability resolution."""

from __future__ import annotations

import pytest

from zqq_zentao_cli.capabilities import resolve_backend


def test_comment_auto_forces_web() -> None:
    assert resolve_backend("comment.list", cli_backend="auto") == "web"
    assert resolve_backend("comment.add", cli_backend="auto") == "web"


def test_my_bugs_auto_forces_web() -> None:
    assert resolve_backend("my-bugs", cli_backend="auto") == "web"
    assert resolve_backend("my-bugs", cli_backend="web") == "web"


def test_my_bugs_rejects_rest() -> None:
    with pytest.raises(SystemExit, match="does not support backend=rest"):
        resolve_backend("my-bugs", cli_backend="rest")


def test_registry_cmd_auto_forces_rest() -> None:
    assert resolve_backend("users", cli_backend="auto") == "rest"
    assert resolve_backend("stories", cli_backend="auto") == "rest"


def test_cli_backend_overrides_auto() -> None:
    assert resolve_backend("my-tasks", cli_backend="web") == "web"
    assert resolve_backend("my-tasks", cli_backend="rest") == "rest"


def test_reject_unsupported_backend() -> None:
    with pytest.raises(SystemExit, match="does not support backend=rest"):
        resolve_backend("comment.list", cli_backend="rest")


def test_unknown_capability() -> None:
    with pytest.raises(SystemExit, match="Unknown capability"):
        resolve_backend("no-such-cmd", cli_backend="auto")


def test_prefer_rest_when_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("zqq_zentao_cli.capabilities.resolve_token", lambda: "tok")
    monkeypatch.setattr("zqq_zentao_cli.capabilities.env_backend", lambda: "auto")
    assert resolve_backend("my-tasks", cli_backend=None) == "rest"


def test_prefer_web_without_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("zqq_zentao_cli.capabilities.resolve_token", lambda: None)
    monkeypatch.setattr("zqq_zentao_cli.capabilities.env_backend", lambda: "auto")
    assert resolve_backend("my-tasks", cli_backend=None) == "web"
