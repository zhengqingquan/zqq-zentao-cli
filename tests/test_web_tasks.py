#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline tests for web my-tasks / execution dtable parsing."""

from __future__ import annotations

import pytest

from zqq_zentao_cli.web.tasks import fetch_execution_tasks, fetch_my_tasks


class _FakeSess:
    def __init__(self, payload: object, *, raw: str = "", status: int = 200, path_prefix: str = "") -> None:
        self._payload = payload
        self._raw = raw
        self._status = status
        self._path_prefix = path_prefix

    def request(self, method: str, path: str) -> dict:
        assert method == "GET"
        if self._path_prefix:
            assert path.startswith(self._path_prefix)
        return {"ok": True, "status": self._status, "data": self._payload, "raw": self._raw}


def test_fetch_my_tasks_empty_dtable() -> None:
    inner = '<div zui-create-dtable="{&quot;data&quot;:[]}">'
    payload = [{"name": "main", "data": inner}]
    rows = fetch_my_tasks(_FakeSess(payload, raw=inner, path_prefix="/my-work-task"))  # type: ignore[arg-type]
    assert rows == []


def test_fetch_execution_tasks_empty_dtable() -> None:
    inner = '<div zui-create-dtable="{&quot;data&quot;:[]}">'
    payload = [{"name": "main", "data": inner}]
    rows = fetch_execution_tasks(
        _FakeSess(payload, raw=inner, path_prefix="/execution-task-"),  # type: ignore[arg-type]
        12,
    )
    assert rows == []


def test_fetch_my_tasks_missing_dtable_fails() -> None:
    payload = [{"name": "main", "data": "<div>no table</div>"}]
    with pytest.raises(SystemExit, match="Failed to parse my-tasks"):
        fetch_my_tasks(_FakeSess(payload, raw="no table", path_prefix="/my-work-task"))  # type: ignore[arg-type]
