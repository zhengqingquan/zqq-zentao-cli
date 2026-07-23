# -*- coding: utf-8 -*-
"""Offline tests for REST API version + name/code search helpers."""

from __future__ import annotations

import pytest

from zqq_zentao_cli.config import resolve_api
from zqq_zentao_cli.rest.session import RestSession
from zqq_zentao_cli.rest.v2_search import (
    filters_query_pairs,
    match_name_code,
    project_name_code_filters,
    search_name_code_rows,
)


def test_resolve_api_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ZENTAO_API", raising=False)
    assert resolve_api(None) == "v1"
    monkeypatch.setenv("ZENTAO_API", "v2")
    assert resolve_api(None) == "v2"
    assert resolve_api("v1") == "v1"


def test_session_url_v1_v2() -> None:
    s1 = RestSession("https://example.com", api_version="v1")
    assert s1._url("/projects") == "https://example.com/api.php/v1/projects"
    s2 = RestSession("https://example.com", api_version="v2")
    assert s2._url("/projects") == "https://example.com/api.php/v2/projects"
    assert s2._url("/api.php/v1/tokens") == "https://example.com/api.php/v1/tokens"


def test_filters_query_pairs() -> None:
    pairs = filters_query_pairs(project_name_code_filters("FM270"))
    assert ("filters[0][field]", "name") in pairs
    assert ("filters[0][operator]", "include") in pairs
    assert ("filters[1][field]", "code") in pairs


def test_match_name_code() -> None:
    assert match_name_code({"name": "一起教育FM270", "code": "X"}, "FM270")
    assert match_name_code({"name": "x", "code": "FM270-02B"}, "fm270")
    assert not match_name_code({"name": "other", "code": ""}, "FM270")


def test_search_name_code_rows() -> None:
    def list_resource(key, *, page=1, limit=50, scopes=None, path_param=None, query=None):
        assert key == "projects"
        if page == 1:
            return {
                "projects": [
                    {"id": 1, "name": "alpha", "code": "A"},
                    {"id": 3337, "name": "一起教育FM270", "code": "FM270-02B"},
                ],
                "total": 2,
            }
        return {"projects": [], "total": 2}

    out = search_name_code_rows(
        list_resource, "projects", "projects", "FM270", page=1, limit=10
    )
    assert out["total"] == 1
    assert out["projects"][0]["id"] == 3337


def test_cli_api_flag() -> None:
    from zqq_zentao_cli.cli import build_parser

    parser = build_parser()
    args = parser.parse_args(["--api", "v2", "projects", "--search", "FM270"])
    assert args.api == "v2"
    assert args.search == "FM270"
