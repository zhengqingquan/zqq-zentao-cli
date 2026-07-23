#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline tests for canonical task row shape."""

from __future__ import annotations

from zqq_zentao_cli.task_shape import (
    assigned_account,
    enrich_task_detail,
    summarize_task,
    user_field,
)


def test_user_field_object_and_string() -> None:
    assert user_field(None) is None
    assert user_field("alice") == "alice"
    assert user_field({"account": "a", "realname": "A"}) == "a"
    assert user_field({"realname": "OnlyName"}) == "OnlyName"


def test_assigned_account() -> None:
    assert assigned_account({"assignedTo": {"account": "me"}}) == "me"
    assert assigned_account({"assignedTo": "me"}) == "me"
    assert assigned_account({"assignedTo": None}) == ""
    assert assigned_account({}) == ""


def test_summarize_rest_assigned_object() -> None:
    row = summarize_task(
        {
            "id": 1,
            "name": "t",
            "assignedTo": {"account": "a", "realname": "A"},
            "openedBy": {"account": "b"},
            "rawStatus": "wait",
            "executionID": 9,
        }
    )
    assert row["id"] == 1
    assert row["assignedTo"] == "a"
    assert row["assignedToRealName"] == "A"
    assert row["openedBy"] == "b"
    assert row["status"] == "wait"
    assert row["execution"] == 9


def test_summarize_web_assigned_string() -> None:
    row = summarize_task(
        {
            "id": 2,
            "name": "u",
            "assignedTo": "a",
            "assignedToRealName": "A",
            "status": "doing",
            "openedBy": "b",
        }
    )
    assert row["assignedTo"] == "a"
    assert row["assignedToRealName"] == "A"
    assert row["openedBy"] == "b"
    assert row["status"] == "doing"


def test_enrich_task_detail_adds_edit_for_closed() -> None:
    """REST operateMenu is mainActions only; closed still allows field edit."""
    raw = {
        "id": 38597,
        "status": "closed",
        "operateMenu": ["recordWorkhour", "activate"],
        "name": "demo",
    }
    out = enrich_task_detail(raw)
    assert out["operateMenuMain"] == ["recordWorkhour", "activate"]
    assert "edit" in out["operateMenu"]
    assert out["canFieldEdit"] is True
    assert out["status"] == "closed"
