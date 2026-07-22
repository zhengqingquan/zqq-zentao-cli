#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline tests for list user filters."""

from __future__ import annotations

from zqq_zentao_cli.list_filter import filter_rows, row_account, slice_rows
from zqq_zentao_cli.rest.tasks import search_tasks


def test_row_account_object_and_string() -> None:
    assert row_account({"assignedTo": {"account": "a"}}, "assignedTo") == "a"
    assert row_account({"assignedTo": "b"}, "assignedTo") == "b"
    assert row_account({}, "assignedTo") == ""


def test_filter_rows_assigned_and_opened() -> None:
    rows = [
        {"id": 1, "assignedTo": "alice", "openedBy": "bob"},
        {"id": 2, "assignedTo": {"account": "alice"}, "openedBy": {"account": "carol"}},
        {"id": 3, "assignedTo": "dave", "openedBy": "bob"},
    ]
    assert [r["id"] for r in filter_rows(rows, assigned_to="alice")] == [1, 2]
    assert [r["id"] for r in filter_rows(rows, opened_by="bob")] == [1, 3]
    assert [r["id"] for r in filter_rows(rows, assigned_to="alice", opened_by="carol")] == [2]


def test_slice_rows() -> None:
    rows = [{"id": i} for i in range(1, 6)]
    chunk, total = slice_rows(rows, page=2, limit=2)
    assert total == 5
    assert [r["id"] for r in chunk] == [3, 4]


def test_search_tasks_uses_search_query_and_filters() -> None:
    calls: list[dict[str, str] | None] = []

    def fake_list_resource(
        name: str,
        *,
        page: int = 1,
        limit: int = 50,
        scopes: dict | None = None,
        path_param: str | None = None,
        query: dict[str, str] | None = None,
    ) -> dict:
        assert name == "tasks"
        calls.append(query)
        return {
            "tasks": [
                {
                    "id": 1,
                    "name": "t1",
                    "assignedTo": {"account": "alice"},
                    "openedBy": {"account": "bob"},
                },
                {
                    "id": 2,
                    "name": "t2",
                    "assignedTo": {"account": "alice"},
                    "openedBy": {"account": "carol"},
                },
            ],
            "total": 2,
        }

    out = search_tasks(
        fake_list_resource, assigned_to="alice", opened_by="carol", page=1, limit=10
    )
    assert out["total"] == 1
    assert out["tasks"][0]["id"] == 2
    assert calls and calls[0] is not None
    assert calls[0]["search"] == "1"
    assert calls[0]["assignedTo"] == "alice"
