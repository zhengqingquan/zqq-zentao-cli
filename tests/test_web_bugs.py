#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline tests for web my-bugs dtable parsing."""

from __future__ import annotations

from zqq_zentao_cli.web.bugs import fetch_my_bugs


class _FakeSess:
    def __init__(self, payload: object, *, raw: str = "", status: int = 200) -> None:
        self._payload = payload
        self._raw = raw
        self._status = status

    def request(self, method: str, path: str) -> dict:
        assert method == "GET"
        assert path.startswith("/my-work-bug-assignedTo.html")
        return {"ok": True, "status": self._status, "data": self._payload, "raw": self._raw}


def test_fetch_my_bugs_from_zin_dtable() -> None:
    # Minimal zin fragment with dtable data attr (escaped like real HTML).
    inner = (
        '<div zui-create-dtable="{&quot;data&quot;:['
        '{&quot;id&quot;:10,&quot;title&quot;:&quot;fix&quot;,&quot;status&quot;:&quot;active&quot;,'
        '&quot;severity&quot;:1,&quot;pri&quot;:2,&quot;productName&quot;:&quot;P&quot;,'
        '&quot;assignedTo&quot;:&quot;me&quot;}]}">'
    )
    payload = [{"name": "main", "data": inner}]
    rows = fetch_my_bugs(_FakeSess(payload, raw=inner))  # type: ignore[arg-type]
    assert len(rows) == 1
    assert rows[0]["id"] == 10
    assert rows[0]["title"] == "fix"
    assert rows[0]["assignedTo"] == "me"
    assert rows[0]["productName"] == "P"


def test_fetch_my_bugs_empty_dtable() -> None:
    inner = '<div zui-create-dtable="{&quot;data&quot;:[]}">'
    payload = [{"name": "main", "data": inner}]
    rows = fetch_my_bugs(_FakeSess(payload, raw=inner))  # type: ignore[arg-type]
    assert rows == []
