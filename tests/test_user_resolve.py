#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline tests for account / realname resolution."""

from __future__ import annotations

import pytest

from zqq_zentao_cli.user_resolve import resolve_account, resolve_optional, search_users


def _users_payload() -> dict:
    return {
        "users": [
            {"account": "zhangsan", "realname": "张三", "pinyin": "zhangsan"},
            {"account": "alice", "realname": "Alice", "pinyin": "alice"},
            {"account": "zhangsi", "realname": "张思", "pinyin": "zhangsi"},
        ],
        "total": 3,
    }


def _list_users(*, page: int = 1, limit: int = 50) -> dict:
    assert page == 1
    return _users_payload()


def test_resolve_exact_account() -> None:
    assert resolve_account(_list_users, "zhangsan") == "zhangsan"


def test_resolve_unique_realname() -> None:
    assert resolve_account(_list_users, "张三") == "zhangsan"


def test_resolve_unique_pinyin_substring() -> None:
    assert resolve_account(_list_users, "zhangsan") == "zhangsan"


def test_resolve_ambiguous() -> None:
    with pytest.raises(SystemExit, match="Ambiguous"):
        resolve_account(_list_users, "张")


def test_resolve_no_match() -> None:
    with pytest.raises(SystemExit, match="No user matching"):
        resolve_account(_list_users, "nobody")


def test_resolve_optional_blank() -> None:
    assert resolve_optional(_list_users, None) is None
    assert resolve_optional(_list_users, "  ") is None


def test_search_users() -> None:
    hits = search_users(_list_users, "张")
    assert {u["account"] for u in hits} == {"zhangsan", "zhangsi"}
