# -*- coding: utf-8 -*-
"""Offline tests for list_stats (count-only + facets)."""

from __future__ import annotations

import pytest

from zqq_zentao_cli.list_stats import (
    as_count_only,
    build_filters_echo,
    count_by_facet,
    parse_facets,
    summarize_rows,
)


def test_parse_facets_default_and_custom() -> None:
    assert parse_facets(None) == ("status", "pri")
    assert parse_facets("") == ("status", "pri")
    assert parse_facets("pri") == ("pri",)
    assert parse_facets("status,pri,status") == ("status", "pri")


def test_parse_facets_rejects_unknown() -> None:
    with pytest.raises(SystemExit):
        parse_facets("severity")


def test_summarize_rows_status_and_pri() -> None:
    rows = [
        {"id": 1, "status": "active", "pri": 1},
        {"id": 2, "status": "active", "pri": "1"},
        {"id": 3, "status": "closed", "pri": 3},
        {"id": 4, "status": "resolved", "pri": 2},
    ]
    out = summarize_rows(rows)
    assert out["total"] == 4
    assert out["facets"]["status"] == {"active": 2, "closed": 1, "resolved": 1}
    assert out["facets"]["pri"] == {"1": 2, "2": 1, "3": 1}


def test_count_by_facet_assigned() -> None:
    rows = [
        {"assignedTo": "alice"},
        {"assignedTo": {"account": "alice"}},
        {"assignedTo": "bob"},
        {},
    ]
    assert count_by_facet(rows, "assignedTo") == {"alice": 2, "bob": 1, "(empty)": 1}


def test_as_count_only_strips_rows() -> None:
    payload = {
        "bugs": [{"id": 1}, {"id": 2}],
        "total": 84,
        "page": 1,
        "limit": 1,
        "backend": "rest",
        "api": "v1",
    }
    out = as_count_only(
        payload,
        kind="bugs",
        list_key="bugs",
        filters={"project": "3337", "status": "active", "pri": None},
    )
    assert out == {
        "kind": "bugs",
        "mode": "count-only",
        "total": 84,
        "filters": {"project": "3337", "status": "active"},
        "backend": "rest",
        "api": "v1",
    }
    assert "bugs" not in out


def test_as_count_only_prefers_resolved_filters() -> None:
    payload = {
        "bugs": [],
        "total": 2,
        "resolvedFilters": {
            "project": "3337",
            "assignedTo": "yjiansen",
            "assignedToInput": "建森",
        },
    }
    out = as_count_only(
        payload,
        kind="bugs",
        list_key="bugs",
        filters={"assignedTo": "建森"},
    )
    assert out["filters"]["assignedTo"] == "yjiansen"
    assert out["filters"]["assignedToInput"] == "建森"


def test_build_filters_echo_resolved_account() -> None:
    echo = build_filters_echo(
        scopes={"project": "3337"},
        status="active",
        user_inputs={"assignedTo": "建森"},
        user_resolved={"assignedTo": "yjiansen"},
    )
    assert echo == {
        "project": "3337",
        "status": "active",
        "assignedTo": "yjiansen",
        "assignedToInput": "建森",
    }
