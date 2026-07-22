# -*- coding: utf-8 -*-
"""Registry-driven REST resource browse helpers."""

from __future__ import annotations

from typing import Any

from ..list_filter import apply_user_filters
from ..protocol import ZenTaoClient
from ..rest.client import RestClient
from ..rest.resources import Resource, resource_by_detail_cmd, resource_by_list_cmd
from ..user_resolve import resolve_optional, search_users


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
    assigned_to: str | None = None,
    opened_by: str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    res = resource_by_list_cmd(cmd)
    if res is None:
        raise SystemExit(f"Unknown list command: {cmd}")
    rest = _as_rest(client)

    # users --search: client-side scan (REST /users has no search param).
    q = dict(query or {})
    search_q = q.pop("search", None) if q else None
    if res.key == "users" and search_q:
        from ..list_filter import slice_rows

        rows = search_users(rest.list_users, search_q)
        chunk, total = slice_rows(rows, page=page, limit=limit)
        return {
            "users": chunk,
            "page": max(1, int(page)),
            "total": total,
            "limit": max(1, int(limit)),
            "backend": rest.backend,
        }

    at = resolve_optional(rest.list_users, assigned_to) if assigned_to else None
    ob = resolve_optional(rest.list_users, opened_by) if opened_by else None
    st = (status or "").strip() or None

    if (at or ob or st) and res.list_key and res.paginated:
        return _list_all_then_filter(
            rest,
            res,
            page=page,
            limit=limit,
            scopes=scopes,
            path_param=path_param,
            query=q or None,
            assigned_to=at,
            opened_by=ob,
            status=st,
        )
    return rest.list_resource(
        res.key,
        page=page,
        limit=limit,
        scopes=scopes,
        path_param=path_param,
        query=q or None,
    )


def _list_all_then_filter(
    rest: RestClient,
    res: Resource,
    *,
    page: int,
    limit: int,
    scopes: dict[str, str | int | None] | None,
    path_param: str | None,
    query: dict[str, str] | None,
    assigned_to: str | None,
    opened_by: str | None,
    status: str | None = None,
) -> dict[str, Any]:
    """Paginate the full scoped list, then apply filters + client page."""
    assert res.list_key
    all_rows: list[dict[str, Any]] = []
    seen: set[Any] = set()
    cur = 1
    page_size = 200
    reported_total = 0
    while cur <= 100:
        data = rest.list_resource(
            res.key,
            page=cur,
            limit=page_size,
            scopes=scopes,
            path_param=path_param,
            query=query,
        )
        rows = [r for r in (data.get(res.list_key) or []) if isinstance(r, dict)]
        reported_total = int(data.get("total") or reported_total or len(rows))
        if not rows:
            break
        for row in rows:
            rid = row.get("id")
            key = rid if rid is not None else id(row)
            if key in seen:
                continue
            seen.add(key)
            all_rows.append(row)
        if reported_total and len(all_rows) >= reported_total:
            break
        if len(rows) < page_size:
            break
        cur += 1

    payload = {
        res.list_key: all_rows,
        "backend": rest.backend,
    }
    return apply_user_filters(
        payload,
        res.list_key,
        assigned_to=assigned_to,
        opened_by=opened_by,
        status=status,
        page=page,
        limit=limit,
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


def user_filters_from_args(args: Any, res: Resource) -> dict[str, str | None]:
    out: dict[str, str | None] = {"assigned_to": None, "opened_by": None}
    for name in res.user_filters:
        # CLI: --assignedTo -> dest assignedTo (argparse keeps case with default)
        val = getattr(args, name, None)
        if val is None:
            val = getattr(args, name.replace("To", "_to").lower(), None)
        if name == "assignedTo" and val:
            out["assigned_to"] = str(val)
        elif name == "openedBy" and val:
            out["opened_by"] = str(val)
    return out


def status_from_args(args: Any) -> str | None:
    val = getattr(args, "status", None)
    if val is None or val == "":
        return None
    return str(val)
