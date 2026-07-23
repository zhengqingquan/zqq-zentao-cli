# -*- coding: utf-8 -*-
"""Registry-driven REST resource browse helpers."""

from __future__ import annotations

import sys
from typing import Any

from ..list_filter import apply_user_filters, slice_rows
from ..protocol import ZenTaoClient
from ..rest.browse_filter import plan_bugs_stories_filter
from ..rest.client import RestClient
from ..rest.resources import Resource, resource_by_detail_cmd, resource_by_list_cmd
from ..rest.v2_search import (
    filters_query_pairs,
    project_name_code_filters,
    search_name_code_rows,
)
from ..user_resolve import resolve_optional, search_users

_NAME_CODE_SEARCH_KEYS = frozenset({"projects", "products", "programs"})


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

    q = dict(query or {})
    search_q = q.pop("search", None) if q else None

    # users --search: client-side scan.
    if res.key == "users" and search_q:
        rows = search_users(rest.list_users, search_q)
        chunk, total = slice_rows(rows, page=page, limit=limit)
        return {
            "users": chunk,
            "page": max(1, int(page)),
            "total": total,
            "limit": max(1, int(limit)),
            "backend": rest.backend,
            "api": rest.api_version,
        }

    # projects/products/programs --search
    if res.key in _NAME_CODE_SEARCH_KEYS and search_q:
        return _search_name_code(
            rest,
            res,
            search_q,
            page=page,
            limit=limit,
            scopes=scopes,
            path_param=path_param,
            query=q or None,
        )

    at = resolve_optional(rest.list_users, assigned_to) if assigned_to else None
    ob = resolve_optional(rest.list_users, opened_by) if opened_by else None
    st = (status or "").strip() or None

    if (at or ob or st) and res.list_key and res.paginated:
        if res.key in ("bugs", "stories"):
            return _list_bugs_stories_filtered(
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
    out = rest.list_resource(
        res.key,
        page=page,
        limit=limit,
        scopes=scopes,
        path_param=path_param,
        query=q or None,
    )
    if isinstance(out, dict):
        out.setdefault("api", rest.api_version)
    return out


def _search_name_code(
    rest: RestClient,
    res: Resource,
    needle: str,
    *,
    page: int,
    limit: int,
    scopes: dict[str, str | int | None] | None,
    path_param: str | None,
    query: dict[str, str] | None,
) -> dict[str, Any]:
    assert res.list_key
    # Prefer APIv2 server filters for projects when --api v2.
    if rest.api_version == "v2" and res.key == "projects":
        try:
            out = _projects_v2_filters_search(
                rest,
                res,
                needle,
                page=page,
                limit=limit,
                scopes=scopes,
                query=query,
            )
            rows = out.get(res.list_key) or []
            if rows:
                return out
            print(
                "warn: v2 filters returned 0 rows; falling back to v1 client scan",
                file=sys.stderr,
            )
        except SystemExit as e:
            print(
                f"warn: v2 filters search failed ({e}); falling back to v1 client scan",
                file=sys.stderr,
            )

    # Client scan: use v1 list when on v2 — APIv2 /projects paging is unreliable
    # (same page repeated; limit ignored).
    list_fn = rest.list_resource
    prev_api = rest.api_version
    if prev_api == "v2" and res.key in _NAME_CODE_SEARCH_KEYS:
        list_fn = _list_resource_v1(rest)

    out = search_name_code_rows(
        list_fn,
        res.key,
        res.list_key,
        needle,
        page=page,
        limit=limit,
        scopes=scopes,
    )
    out["backend"] = rest.backend
    out["api"] = rest.api_version
    out["searchMode"] = "client" if prev_api == "v1" else "client-via-v1"
    return out


def _list_resource_v1(rest: RestClient):
    """Temporarily list via APIv1 session (shared token)."""

    def _call(
        name: str,
        *,
        page: int = 1,
        limit: int = 50,
        scopes: dict[str, str | int | None] | None = None,
        path_param: str | None = None,
        query: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        # Swap read session to v1 for this call only.
        from ..rest.session import RestSession

        old = rest._sess
        rest._sess = RestSession(
            rest.profile["server"],
            insecure=old.insecure,
            account=old.account,
            timeout=old.timeout,
            api_version="v1",
        )
        rest._sess.token = old.token
        try:
            return rest.list_resource(
                name,
                page=page,
                limit=limit,
                scopes=scopes,
                path_param=path_param,
                query=query,
            )
        finally:
            rest._sess = old

    return _call


def _projects_v2_filters_search(
    rest: RestClient,
    res: Resource,
    needle: str,
    *,
    page: int,
    limit: int,
    scopes: dict[str, str | int | None] | None,
    query: dict[str, str] | None,
) -> dict[str, Any]:
    """GET /projects with filters[i][field]=… (APIv2 prepareV2Search)."""
    assert res.list_key
    pairs = filters_query_pairs(project_name_code_filters(needle))
    q = dict(query or {})
    q.setdefault("page", str(page))
    q.setdefault("limit", str(limit))
    for k, v in q.items():
        pairs.append((k, str(v)))

    # Use list path; scope overrides when set.
    path = res.list_path or "/projects"
    picked = None
    if scopes and res.scopes:
        for name in ("program", "product"):
            val = scopes.get(name)
            if val is not None and val != "" and name in res.scopes:
                from urllib.parse import quote

                path = res.scopes[name].format(id=quote(str(val), safe=""))
                picked = name
                break

    data = rest._get(path, query=pairs)  # noqa: SLF001 — shared REST helper
    from ..rest.client import _extract_named_list, _extract_total

    rows = _extract_named_list(data, res.list_key, "projectStats")
    meta = data if isinstance(data, dict) else {}
    return {
        res.list_key: rows,
        "page": meta.get("page", page),
        "total": _extract_total(data, len(rows)),
        "limit": meta.get("limit", limit),
        "backend": rest.backend,
        "api": rest.api_version,
        "searchMode": "v2-filters",
        "scope": picked,
    }


def _list_bugs_stories_filtered(
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
    status: str | None,
) -> dict[str, Any]:
    """Prefer REST browseType (status=) for bugs/stories; else full client filter."""
    assert res.key in ("bugs", "stories")
    me = str(rest.profile.get("account") or "").strip()
    plan = plan_bugs_stories_filter(
        "bugs" if res.key == "bugs" else "stories",
        me=me,
        assigned_to=assigned_to,
        opened_by=opened_by,
        status=status,
    )
    if plan.note:
        print(plan.note, file=sys.stderr)

    q = dict(query or {})
    if plan.server_status:
        q["status"] = plan.server_status

    if plan.mode in ("passthrough", "server_page"):
        return rest.list_resource(
            res.key,
            page=page,
            limit=limit,
            scopes=scopes,
            path_param=path_param,
            query=q or None,
        )

    return _list_all_then_filter(
        rest,
        res,
        page=page,
        limit=limit,
        scopes=scopes,
        path_param=path_param,
        query=q or None,
        assigned_to=plan.client_assigned_to,
        opened_by=plan.client_opened_by,
        status=plan.client_status,
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
        "api": rest.api_version,
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
