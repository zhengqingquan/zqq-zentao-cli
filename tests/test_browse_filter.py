#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for bugs/stories REST browseType filter planning."""

from __future__ import annotations

from zqq_zentao_cli.rest.browse_filter import plan_bugs_stories_filter


def test_passthrough_no_filters() -> None:
    p = plan_bugs_stories_filter("bugs", me="alice")
    assert p.mode == "passthrough"


def test_bugs_assigned_to_self_server_page() -> None:
    p = plan_bugs_stories_filter("bugs", me="alice", assigned_to="alice")
    assert p.mode == "server_page"
    assert p.server_status == "assigntome"
    assert p.client_assigned_to is None


def test_bugs_assigned_to_self_plus_status_field() -> None:
    p = plan_bugs_stories_filter(
        "bugs", me="alice", assigned_to="alice", status="active"
    )
    assert p.mode == "server_then_client"
    assert p.server_status == "assigntome"
    assert p.client_status == "active"


def test_bugs_opened_by_self() -> None:
    p = plan_bugs_stories_filter("bugs", me="alice", opened_by="alice")
    assert p.mode == "server_page"
    assert p.server_status == "openedbyme"


def test_bugs_status_active_maps_unresolved() -> None:
    p = plan_bugs_stories_filter("bugs", me="alice", status="active")
    assert p.mode == "server_page"
    assert p.server_status == "unresolved"
    assert p.client_status is None


def test_bugs_status_browse_type_passthrough() -> None:
    p = plan_bugs_stories_filter("bugs", me="alice", status="unclosed")
    assert p.mode == "server_page"
    assert p.server_status == "unclosed"


def test_bugs_other_user_client_all() -> None:
    p = plan_bugs_stories_filter("bugs", me="alice", assigned_to="bob")
    assert p.mode == "client_all"
    assert p.client_assigned_to == "bob"
    assert p.note and "bob" in p.note


def test_stories_assigned_to_self() -> None:
    p = plan_bugs_stories_filter("stories", me="alice", assigned_to="alice")
    assert p.mode == "server_page"
    assert p.server_status == "assignedtome"


def test_stories_status_active() -> None:
    p = plan_bugs_stories_filter("stories", me="alice", status="active")
    assert p.mode == "server_page"
    assert p.server_status == "activestory"
