#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline tests for task edit option filtering."""

from __future__ import annotations

from typing import Any

from zqq_zentao_cli.services.task_options import (
    _flatten_modules,
    filter_parent_candidates,
)


def test_flatten_modules_nested() -> None:
    tree = [
        {
            "id": 1,
            "name": "Root",
            "children": [{"id": 2, "name": "Child"}],
        }
    ]
    rows = _flatten_modules(tree)
    assert rows == [
        {"id": 1, "name": "Root"},
        {"id": 2, "name": "Root/Child"},
    ]


def test_filter_parent_candidates_mirrors_web_rules() -> None:
    rows: list[dict[str, Any]] = [
        {"id": 10, "name": "ok", "status": "wait", "parent": 0, "mode": "", "consumed": 0},
        {"id": 11, "name": "closed", "status": "closed", "parent": 0, "mode": "", "consumed": 0},
        {"id": 12, "name": "child", "status": "wait", "parent": 10, "mode": "", "consumed": 0},
        {"id": 13, "name": "multi", "status": "wait", "parent": 0, "mode": "multi", "consumed": 0},
        {
            "id": 14,
            "name": "consumed",
            "status": "doing",
            "parent": 0,
            "mode": "",
            "consumed": 1.5,
            "isParent": False,
        },
        {
            "id": 15,
            "name": "parent-ok",
            "status": "doing",
            "parent": 0,
            "mode": "",
            "consumed": 2,
            "isParent": True,
        },
        {"id": 99, "name": "self", "status": "wait", "parent": 0, "mode": "", "consumed": 0},
    ]
    got = filter_parent_candidates(
        rows,
        task_id=99,
        append_parent_id=None,
        exclude_ids={99},
    )
    assert [r["id"] for r in got] == [10, 15]


def test_filter_parent_candidates_appends_current() -> None:
    rows = [
        {"id": 20, "name": "cur", "status": "closed", "parent": 0, "mode": "", "consumed": 0},
    ]
    got = filter_parent_candidates(rows, task_id=1, append_parent_id=20)
    assert got == [{"id": 20, "name": "cur"}]
