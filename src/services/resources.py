# -*- coding: utf-8 -*-
"""Registry-driven REST resource browse helpers."""

from __future__ import annotations

from typing import Any

from ..protocol import ZenTaoClient
from ..rest.client import RestClient
from ..rest.resources import Resource, resource_by_detail_cmd, resource_by_list_cmd


def _as_rest(client: ZenTaoClient) -> RestClient:
    if not isinstance(client, RestClient):
        raise SystemExit("This command requires --backend rest")
    return client


def list_by_cmd(
    client: ZenTaoClient,
    cmd: str,
    *,
    page: int = 1,
    limit: int = 50,
    scopes: dict[str, str | int | None] | None = None,
    path_param: str | None = None,
    query: dict[str, str] | None = None,
) -> dict[str, Any]:
    res = resource_by_list_cmd(cmd)
    if res is None:
        raise SystemExit(f"Unknown list command: {cmd}")
    return _as_rest(client).list_resource(
        res.key,
        page=page,
        limit=limit,
        scopes=scopes,
        path_param=path_param,
        query=query,
    )


def get_by_cmd(client: ZenTaoClient, cmd: str, resource_id: str | int) -> dict[str, Any]:
    res = resource_by_detail_cmd(cmd)
    if res is None:
        raise SystemExit(f"Unknown detail command: {cmd}")
    return _as_rest(client).get_resource(res.key, resource_id)


def scopes_from_args(args: Any, res: Resource) -> dict[str, str | int | None]:
    out: dict[str, str | int | None] = {}
    for name in res.scopes:
        out[name] = getattr(args, name, None)
    return out


def query_from_args(args: Any, res: Resource) -> dict[str, str]:
    q: dict[str, str] = {}
    for name in res.query_params:
        val = getattr(args, name.replace("-", "_"), None)
        if val is None:
            val = getattr(args, name, None)
        if val is not None and val != "":
            q[name] = str(val)
    return q
