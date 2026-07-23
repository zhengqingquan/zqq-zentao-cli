# -*- coding: utf-8 -*-
"""List count-only + facet summary for bugs / stories / tasks."""

from __future__ import annotations

import sys
from typing import Any

from ..list_filter import apply_user_filters
from ..list_stats import as_count_only, build_filters_echo, parse_facets, summarize_rows
from ..protocol import ZenTaoClient
from ..rest.browse_filter import plan_bugs_stories_filter
from ..rest.client import RestClient
from ..rest.resources import resource_by_list_cmd
from ..user_resolve import resolve_optional
from . import tasks as task_svc


def _as_rest(client: ZenTaoClient) -> RestClient:
    if not isinstance(client, RestClient):
        raise SystemExit("summary / --count-only requires --backend rest")
    return client


def count_only_from_list(
    payload: dict[str, Any],
    *,
    kind: str,
    list_key: str,
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return as_count_only(payload, kind=kind, list_key=list_key, filters=filters)


def _paginate_scoped(
    rest: RestClient,
    *,
    key: str,
    list_key: str,
    scopes: dict[str, str | int | None] | None,
    path_param: str | None,
    query: dict[str, str] | None,
) -> list[dict[str, Any]]:
    all_rows: list[dict[str, Any]] = []
    seen: set[Any] = set()
    cur = 1
    page_size = 200
    reported_total = 0
    while cur <= 100:
        data = rest.list_resource(
            key,
            page=cur,
            limit=page_size,
            scopes=scopes,
            path_param=path_param,
            query=query,
        )
        rows = [r for r in (data.get(list_key) or []) if isinstance(r, dict)]
        reported_total = int(data.get("total") or reported_total or len(rows))
        if not rows:
            break
        for row in rows:
            rid = row.get("id")
            ukey = rid if rid is not None else id(row)
            if ukey in seen:
                continue
            seen.add(ukey)
            all_rows.append(row)
        if reported_total and len(all_rows) >= reported_total:
            break
        if len(rows) < page_size:
            break
        cur += 1
    return all_rows


def _fetch_bugs_or_stories_rows(
    rest: RestClient,
    kind: str,
    *,
    scopes: dict[str, str | int | None] | None,
    assigned_to: str | None,
    opened_by: str | None,
    resolved_by: str | None,
    closed_by: str | None,
    status: str | None,
    pri: str | None,
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    res = resource_by_list_cmd(kind)
    if res is None or not res.list_key:
        raise SystemExit(f"Unknown list kind: {kind}")
    me = str(rest.profile.get("account") or "").strip()
    at = resolve_optional(rest.list_users, assigned_to) if assigned_to else None
    ob = resolve_optional(rest.list_users, opened_by) if opened_by else None
    rb = resolve_optional(rest.list_users, resolved_by) if resolved_by else None
    cb = resolve_optional(rest.list_users, closed_by) if closed_by else None
    st = (status or "").strip() or None
    pr = (pri or "").strip() or None
    echo = build_filters_echo(
        scopes=scopes,
        status=st,
        pri=pr,
        user_inputs={
            "assignedTo": assigned_to,
            "openedBy": opened_by,
            "resolvedBy": resolved_by,
            "closedBy": closed_by,
        },
        user_resolved={
            "assignedTo": at,
            "openedBy": ob,
            "resolvedBy": rb,
            "closedBy": cb,
        },
    )

    plan = plan_bugs_stories_filter(
        "bugs" if kind == "bugs" else "stories",
        me=me,
        assigned_to=at,
        opened_by=ob,
        status=st,
    )
    if plan.note:
        print(plan.note, file=sys.stderr)

    query: dict[str, str] | None = None
    if plan.server_status:
        query = {"status": plan.server_status}

    rows = _paginate_scoped(
        rest,
        key=res.key,
        list_key=res.list_key,
        scopes=scopes,
        path_param=None,
        query=query,
    )
    payload = apply_user_filters(
        {res.list_key: rows},
        res.list_key,
        assigned_to=plan.client_assigned_to,
        opened_by=plan.client_opened_by,
        resolved_by=rb,
        closed_by=cb,
        status=plan.client_status,
        pri=pr,
    )
    filtered = [r for r in (payload.get(res.list_key) or []) if isinstance(r, dict)]
    meta: dict[str, Any] = {
        "backend": rest.backend,
        "api": rest.api_version,
    }
    if plan.server_status:
        meta["browseType"] = plan.server_status
    return filtered, meta, echo


def summarize_bugs_or_stories(
    client: ZenTaoClient,
    kind: str,
    *,
    scopes: dict[str, str | int | None] | None,
    assigned_to: str | None = None,
    opened_by: str | None = None,
    resolved_by: str | None = None,
    closed_by: str | None = None,
    status: str | None = None,
    pri: str | None = None,
    facet: str | None = None,
) -> dict[str, Any]:
    if kind not in ("bugs", "stories"):
        raise SystemExit(f"summary kind must be bugs|stories, got {kind!r}")
    rest = _as_rest(client)
    res = resource_by_list_cmd(kind)
    if res is None:
        raise SystemExit(f"Unknown list kind: {kind}")
    if res.require_scope and not any(
        (scopes or {}).get(name) for name in (res.scopes or {})
    ):
        need = " / ".join(f"--{n}" for n in (res.scopes or {}))
        raise SystemExit(f"{kind} summary requires scope: {need}")

    rows, meta, echo = _fetch_bugs_or_stories_rows(
        rest,
        kind,
        scopes=scopes,
        assigned_to=assigned_to,
        opened_by=opened_by,
        resolved_by=resolved_by,
        closed_by=closed_by,
        status=status,
        pri=pri,
    )
    facets = parse_facets(facet)
    body = summarize_rows(rows, facets=facets)
    return {
        "kind": kind,
        "mode": "summary",
        "filters": echo,
        "facet": list(facets),
        **body,
        **meta,
    }


def summarize_tasks(
    client: ZenTaoClient,
    *,
    execution: str | int | None = None,
    assigned_to: str | None = None,
    opened_by: str | None = None,
    finished_by: str | None = None,
    closed_by: str | None = None,
    status: str | None = None,
    pri: str | None = None,
    facet: str | None = None,
) -> dict[str, Any]:
    facets = parse_facets(facet)
    truncated = False
    reported_total: int | None = None

    if execution:
        rows = task_svc.execution_tasks(
            client,
            execution,
            assigned_to=assigned_to,
            opened_by=opened_by,
            finished_by=finished_by,
            closed_by=closed_by,
            status=status,
            pri=pri,
        )
        meta: dict[str, Any] = {"backend": getattr(client, "backend", None)}
    else:
        rest = _as_rest(client)
        data = task_svc.list_tasks(
            client,
            page=1,
            limit=100000,
            assigned_to=assigned_to,
            opened_by=opened_by,
            finished_by=finished_by,
            closed_by=closed_by,
            status=status,
            pri=pri,
        )
        rows = [r for r in (data.get("tasks") or []) if isinstance(r, dict)]
        reported_total = int(data.get("total") or len(rows))
        if reported_total > len(rows):
            truncated = True
            print(
                "warn: summary tasks without --execution may be truncated "
                f"({len(rows)}/{reported_total}); pass -e for a full execution set.",
                file=sys.stderr,
            )
        meta = {
            "backend": data.get("backend") or rest.backend,
            "api": data.get("api") or rest.api_version,
        }

    body = summarize_rows(rows, facets=facets)
    echo = build_filters_echo(
        scopes={"execution": execution} if execution else None,
        status=status,
        pri=pri,
        user_inputs={
            "assignedTo": assigned_to,
            "openedBy": opened_by,
            "finishedBy": finished_by,
            "closedBy": closed_by,
        },
        user_resolved={
            "assignedTo": assigned_to,
            "openedBy": opened_by,
            "finishedBy": finished_by,
            "closedBy": closed_by,
        },
    )
    out: dict[str, Any] = {
        "kind": "tasks",
        "mode": "summary",
        "filters": echo,
        "facet": list(facets),
        **body,
        **meta,
    }
    if truncated and reported_total is not None:
        # Keep total == sum(facets); expose server pager separately.
        out["reportedTotal"] = reported_total
        out["truncated"] = True
    return out
