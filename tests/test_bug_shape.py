#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline tests for canonical bug row shape."""

from __future__ import annotations

from zqq_zentao_cli.bug_shape import summarize_bug


def test_summarize_rest_assigned_object() -> None:
    row = summarize_bug(
        {
            "id": 1,
            "title": "b",
            "assignedTo": {"account": "a", "realname": "A"},
            "openedBy": {"account": "b"},
            "rawStatus": "active",
            "product": {"id": 9, "name": "P"},
            "severity": 2,
            "pri": 3,
        }
    )
    assert row["id"] == 1
    assert row["title"] == "b"
    assert row["assignedTo"] == "a"
    assert row["assignedToRealName"] == "A"
    assert row["openedBy"] == "b"
    assert row["status"] == "active"
    assert row["product"] == 9
    assert row["productName"] == "P"


def test_summarize_web_assigned_string() -> None:
    row = summarize_bug(
        {
            "id": 2,
            "title": "u",
            "assignedTo": "a",
            "assignedToRealName": "A",
            "status": "resolved",
            "openedBy": "b",
            "productName": "Prod",
            "product": 3,
        }
    )
    assert row["assignedTo"] == "a"
    assert row["assignedToRealName"] == "A"
    assert row["openedBy"] == "b"
    assert row["status"] == "resolved"
    assert row["product"] == 3
    assert row["productName"] == "Prod"
