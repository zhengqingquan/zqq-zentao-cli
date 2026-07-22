#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline tests for REST task fetch (fake list_resource, no HTTP)."""

from __future__ import annotations

from typing import Any

import pytest

from zqq_zentao_cli.rest.tasks import fetch_execution_tasks, fetch_my_tasks, list_my_tasks


def test_fetch_my_tasks_sends_page_as_size_and_filters() -> None:
    calls: list[dict[str, str] | None] = []

    def fake_list_resource(
        name: str,
        *,
        page: int = 1,
        limit: int = 50,
        scopes: dict[str, Any] | None = None,
        path_param: str | None = None,
        query: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        assert name == "tasks"
        calls.append(query)
        return {
            "tasks": [
                {"id": 1, "name": "mine", "assignedTo": {"account": "me"}},
                {"id": 2, "name": "other", "assignedTo": {"account": "x"}},
            ],
            "total": 2,
        }

    rows = fetch_my_tasks(fake_list_resource, "me")
    assert [r["id"] for r in rows] == [1]
    assert rows[0]["assignedTo"] == "me"
    assert len(calls) == 1
    assert calls[0] is not None
    assert calls[0]["page"] == "200"
    assert calls[0]["type"] == "assignedTo"


def test_fetch_my_tasks_retries_when_total_exceeds_rows() -> None:
    calls: list[dict[str, str] | None] = []

    def fake_list_resource(
        name: str,
        *,
        page: int = 1,
        limit: int = 50,
        scopes: dict[str, Any] | None = None,
        path_param: str | None = None,
        query: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        calls.append(query)
        if len(calls) == 1:
            return {
                "tasks": [{"id": 1, "name": "a", "assignedTo": "me"}],
                "total": 3,
            }
        return {
            "tasks": [
                {"id": 1, "name": "a", "assignedTo": "me"},
                {"id": 2, "name": "b", "assignedTo": "me"},
                {"id": 3, "name": "c", "assignedTo": "me"},
            ],
            "total": 3,
        }

    rows = fetch_my_tasks(fake_list_resource, "me")
    assert [r["id"] for r in rows] == [1, 2, 3]
    assert len(calls) == 2
    assert calls[1] is not None
    assert calls[1]["page"] == "3"


def test_list_my_tasks_client_side_page() -> None:
    def fake_list_resource(
        name: str,
        *,
        page: int = 1,
        limit: int = 50,
        scopes: dict[str, Any] | None = None,
        path_param: str | None = None,
        query: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        return {
            "tasks": [{"id": i, "name": f"t{i}", "assignedTo": "me"} for i in range(1, 6)],
            "total": 5,
        }

    out = list_my_tasks(fake_list_resource, page=2, limit=2)
    assert out["page"] == 2
    assert out["limit"] == 2
    assert out["total"] == 5
    assert [t["id"] for t in out["tasks"]] == [3, 4]


def test_fetch_execution_tasks_paginates() -> None:
    pages_seen: list[int] = []

    def fake_list_resource(
        name: str,
        *,
        page: int = 1,
        limit: int = 50,
        scopes: dict[str, Any] | None = None,
        path_param: str | None = None,
        query: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        pages_seen.append(page)
        assert scopes == {"execution": 42}
        if page == 1:
            return {
                "tasks": [{"id": i, "name": f"t{i}"} for i in range(1, 201)],
                "total": 250,
                "limit": 200,
            }
        return {
            "tasks": [{"id": i, "name": f"t{i}"} for i in range(201, 251)],
            "total": 250,
            "limit": 200,
        }

    rows = fetch_execution_tasks(fake_list_resource, 42)
    assert len(rows) == 250
    assert pages_seen == [1, 2]


def test_fetch_execution_tasks_empty_raises() -> None:
    def fake_list_resource(
        name: str,
        *,
        page: int = 1,
        limit: int = 50,
        scopes: dict[str, Any] | None = None,
        path_param: str | None = None,
        query: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        return {"tasks": [], "total": 0, "limit": 200}

    with pytest.raises(SystemExit, match="execution task list"):
        fetch_execution_tasks(fake_list_resource, 1)
