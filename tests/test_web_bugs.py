#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline tests for web my-bugs dtable parsing."""

from __future__ import annotations

from zqq_zentao_cli.web.bugs import fetch_my_bugs


def _dtable_html(rows_json: str) -> str:
    return f'<div zui-create-dtable="{{&quot;data&quot;:{rows_json}}}">'


class _FakeSess:
    def __init__(self, by_path: dict[str, tuple[object, str]]) -> None:
        self._by_path = by_path
        self.paths: list[str] = []

    def request(self, method: str, path: str) -> dict:
        assert method == "GET"
        self.paths.append(path)
        # Match by prefix key
        for prefix, (payload, raw) in self._by_path.items():
            if path.startswith(prefix):
                return {"ok": True, "status": 200, "data": payload, "raw": raw}
        raise AssertionError(f"unexpected path {path}")


def test_fetch_my_bugs_from_zin_dtable() -> None:
    inner = _dtable_html(
        "[{&quot;id&quot;:10,&quot;title&quot;:&quot;fix&quot;,&quot;status&quot;:&quot;active&quot;,"
        "&quot;severity&quot;:1,&quot;pri&quot;:2,&quot;productName&quot;:&quot;P&quot;,"
        "&quot;assignedTo&quot;:&quot;me&quot;}]"
    )
    payload = [{"name": "main", "data": inner}]
    sess = _FakeSess({"/my-work-bug-assignedTo-": (payload, inner)})
    rows = fetch_my_bugs(sess)  # type: ignore[arg-type]
    assert len(rows) == 1
    assert rows[0]["id"] == 10
    assert "recPerPage" in sess.paths[0] or "-200-1.html" in sess.paths[0]


def test_fetch_my_bugs_empty_dtable() -> None:
    inner = _dtable_html("[]")
    payload = [{"name": "main", "data": inner}]
    sess = _FakeSess({"/my-work-bug-assignedTo-": (payload, inner)})
    rows = fetch_my_bugs(sess)  # type: ignore[arg-type]
    assert rows == []


def test_fetch_my_bugs_paginates() -> None:
    page1_rows = ",".join(
        f'{{&quot;id&quot;:{i},&quot;title&quot;:&quot;t{i}&quot;,&quot;status&quot;:&quot;active&quot;}}'
        for i in range(1, 3)
    )
    page2_rows = '{&quot;id&quot;:3,&quot;title&quot;:&quot;t3&quot;,&quot;status&quot;:&quot;active&quot;}'
    p1 = _dtable_html(f"[{page1_rows}]")
    p2 = _dtable_html(f"[{page2_rows}]")

    class _PagerSess:
        def __init__(self) -> None:
            self.paths: list[str] = []

        def request(self, method: str, path: str) -> dict:
            self.paths.append(path)
            if path.endswith("-2-1.html?zin=1") or "-2-1.html" in path:
                # page_id=1, rec_per_page=2 for test we'll call with rec_per_page=2
                html = p1
            elif "-2-2.html" in path:
                html = p2
            else:
                # default first call uses 200; simulate short page for this unit via size=2 override
                html = p1
            payload = [{"name": "main", "data": html}]
            return {"ok": True, "status": 200, "data": payload, "raw": html}

    # Direct paginated helper with size=2
    from zqq_zentao_cli.web.lists import fetch_dtable_list_paginated
    from zqq_zentao_cli.bug_shape import summarize_bug

    sess = _PagerSess()

    def path_for_page(page_id: int, size: int) -> str:
        return f"/my-work-bug-assignedTo-0-id_desc-0-{size}-{page_id}.html?zin=1"

    rows = fetch_dtable_list_paginated(
        sess,  # type: ignore[arg-type]
        path_for_page,
        label="my-bugs",
        summarize=summarize_bug,
        rec_per_page=2,
    )
    assert [r["id"] for r in rows] == [1, 2, 3]
    assert len(sess.paths) == 2
