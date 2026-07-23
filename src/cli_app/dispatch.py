# -*- coding: utf-8 -*-
"""CLI main dispatch after argparse."""

from __future__ import annotations

import argparse
from typing import Any

from ..config import set_config_path
from ..factory import create_client
from ..output import configure_output, emit, ensure_utf8_stdio
from ..rest.resources import (
    SPECIAL_CMDS,
    resource_by_detail_cmd,
    resource_by_list_cmd,
)
from ..list_stats import build_filters_echo
from ..services import auth as auth_svc
from ..services import comments as comment_svc
from ..services import my_pages as my_page_svc
from ..services import resources as resource_svc
from ..services import summary as summary_svc
from ..services import tasks as task_svc
from ..user_resolve import resolve_optional
from ..web.my_pages import my_page_by_cmd
from .capability import capability, cli_insecure
from .fields import fields_for
from .normalize import normalize_comment_rows
from .parser import build_parser
from .write_dispatch import WRITE_NOUNS, dispatch_write


def resolve_task_user_filters(
    client: Any, args: argparse.Namespace
) -> dict[str, str | None]:
    """Resolve user-ish task filters via REST list_users when available."""
    keys = (
        ("assignedTo", "assigned_to"),
        ("openedBy", "opened_by"),
        ("finishedBy", "finished_by"),
        ("closedBy", "closed_by"),
    )
    raw: dict[str, str | None] = {}
    for attr, out_key in keys:
        val = getattr(args, attr, None)
        raw[out_key] = str(val).strip() if val else None
    if not any(raw.values()):
        return raw
    list_users = getattr(client, "list_users", None)
    if list_users is None:
        return raw
    try:
        return {k: resolve_optional(list_users, v) if v else None for k, v in raw.items()}
    except SystemExit:
        if getattr(client, "backend", None) == "web":
            return raw
        raise


def _scope_filter_meta(args: argparse.Namespace) -> dict[str, Any]:
    meta: dict[str, Any] = {}
    for key in (
        "product",
        "project",
        "execution",
        "program",
        "assignedTo",
        "openedBy",
        "finishedBy",
        "resolvedBy",
        "closedBy",
        "status",
        "pri",
    ):
        val = getattr(args, key, None)
        if val is not None and str(val).strip() != "":
            meta[key] = val
    return meta


def _task_filters_echo(
    args: argparse.Namespace, resolved: dict[str, str | None]
) -> dict[str, Any]:
    return build_filters_echo(
        scopes={
            "execution": getattr(args, "execution", None),
        },
        status=resource_svc.status_from_args(args),
        pri=resource_svc.pri_from_args(args),
        user_inputs={
            "assignedTo": getattr(args, "assignedTo", None),
            "openedBy": getattr(args, "openedBy", None),
            "finishedBy": getattr(args, "finishedBy", None),
            "closedBy": getattr(args, "closedBy", None),
        },
        user_resolved={
            "assignedTo": resolved.get("assigned_to"),
            "openedBy": resolved.get("opened_by"),
            "finishedBy": resolved.get("finished_by"),
            "closedBy": resolved.get("closed_by"),
        },
    )


def dispatch_registry(client: Any, args: argparse.Namespace) -> bool:
    """Handle registry-driven list/detail commands. Returns True if handled."""
    list_res = resource_by_list_cmd(args.cmd)
    if list_res is not None and args.cmd not in SPECIAL_CMDS:
        path_param = None
        if list_res.path_param:
            path_param = getattr(args, list_res.path_param, None)
        scopes = resource_svc.scopes_from_args(args, list_res) if list_res.scopes else None
        query = (
            resource_svc.query_from_args(args, list_res) if list_res.query_params else None
        )
        filters = (
            resource_svc.user_filters_from_args(args, list_res)
            if list_res.user_filters
            else {
                "assigned_to": None,
                "opened_by": None,
                "finished_by": None,
                "resolved_by": None,
                "closed_by": None,
            }
        )
        status = resource_svc.status_from_args(args) if list_res.user_filters else None
        pri = resource_svc.pri_from_args(args) if list_res.user_filters else None
        count_only = bool(getattr(args, "count_only", False))
        page = getattr(args, "page", 1)
        limit = 1 if count_only else getattr(args, "limit", 50)
        payload = resource_svc.list_by_cmd(
            client,
            args.cmd,
            page=page,
            limit=limit,
            scopes=scopes,
            path_param=path_param,
            query=query,
            assigned_to=filters.get("assigned_to"),
            opened_by=filters.get("opened_by"),
            finished_by=filters.get("finished_by"),
            resolved_by=filters.get("resolved_by"),
            closed_by=filters.get("closed_by"),
            status=status,
            pri=pri,
        )
        if count_only and list_res.list_key:
            emit(
                summary_svc.count_only_from_list(
                    payload,
                    kind=args.cmd,
                    list_key=list_res.list_key,
                    filters=_scope_filter_meta(args),
                ),
                is_list=False,
            )
        else:
            emit(
                payload,
                is_list=True,
                fields=fields_for(args.cmd, args),
            )
        return True

    detail_res = resource_by_detail_cmd(args.cmd)
    if detail_res is not None and args.cmd not in SPECIAL_CMDS:
        emit(resource_svc.get_by_cmd(client, args.cmd, args.id), is_list=False)
        return True

    return False


def _dispatch_summary(client: Any, args: argparse.Namespace) -> int:
    kind = str(args.kind)
    if kind in ("bugs", "stories"):
        scopes = {
            "product": getattr(args, "product", None),
            "project": getattr(args, "project", None),
            "execution": getattr(args, "execution", None),
        }
        emit(
            summary_svc.summarize_bugs_or_stories(
                client,
                kind,
                scopes=scopes,
                assigned_to=getattr(args, "assignedTo", None),
                opened_by=getattr(args, "openedBy", None),
                resolved_by=getattr(args, "resolvedBy", None),
                closed_by=getattr(args, "closedBy", None),
                status=resource_svc.status_from_args(args),
                pri=resource_svc.pri_from_args(args),
                facet=getattr(args, "facet", None),
            ),
            is_list=False,
        )
        return 0
    filters = resolve_task_user_filters(client, args)
    emit(
        summary_svc.summarize_tasks(
            client,
            execution=getattr(args, "execution", None),
            assigned_to=filters.get("assigned_to"),
            opened_by=filters.get("opened_by"),
            finished_by=filters.get("finished_by"),
            closed_by=filters.get("closed_by"),
            status=resource_svc.status_from_args(args),
            pri=resource_svc.pri_from_args(args),
            facet=getattr(args, "facet", None),
        ),
        is_list=False,
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    ensure_utf8_stdio()
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.config:
        set_config_path(args.config)

    configure_output(
        format=args.format,
        silent=args.silent,
        machine_readable=args.machine_readable,
    )

    insecure = cli_insecure(args)
    timeout_ms = args.timeout

    if args.cmd == "login":
        result = auth_svc.do_login(
            server=args.server,
            account=args.account,
            password=args.password,
            backend=args.backend,
            insecure=insecure,
            timeout_ms=timeout_ms,
        )
        emit(result, is_list=False)
        return 0

    cap = capability(args)
    client = create_client(
        cap,
        cli_backend=args.backend,
        cli_api=getattr(args, "api", None),
        insecure=insecure,
        timeout_ms=timeout_ms,
    )

    if args.cmd == "whoami":
        emit(client.whoami(), is_list=False)
        return 0

    if args.cmd == "summary":
        return _dispatch_summary(client, args)

    if my_page_by_cmd(args.cmd) is not None:
        rows = my_page_svc.list_my(
            client,
            args.cmd,
            browse_type=getattr(args, "browse_type", None),
            scope=getattr(args, "scope", None),
        )
        emit(rows, is_list=True, fields=fields_for(args.cmd, args))
        return 0

    if args.cmd == "tasks":
        filters = resolve_task_user_filters(client, args)
        status = resource_svc.status_from_args(args)
        pri = resource_svc.pri_from_args(args)
        fields = fields_for("tasks", args)
        count_only = bool(getattr(args, "count_only", False))
        if args.execution:
            rows = task_svc.execution_tasks(
                client,
                args.execution,
                assigned_to=filters.get("assigned_to"),
                opened_by=filters.get("opened_by"),
                finished_by=filters.get("finished_by"),
                closed_by=filters.get("closed_by"),
                status=status,
                pri=pri,
            )
            if count_only:
                emit(
                    summary_svc.count_only_from_list(
                        {
                            "tasks": rows,
                            "total": len(rows),
                            "backend": getattr(client, "backend", None),
                            "resolvedFilters": _task_filters_echo(args, filters),
                        },
                        kind="tasks",
                        list_key="tasks",
                        filters=_scope_filter_meta(args),
                    ),
                    is_list=False,
                )
            else:
                emit(rows, is_list=True, fields=fields)
        else:
            limit = 1 if count_only else args.limit
            payload = task_svc.list_tasks(
                client,
                page=args.page,
                limit=limit,
                assigned_to=filters.get("assigned_to"),
                opened_by=filters.get("opened_by"),
                finished_by=filters.get("finished_by"),
                closed_by=filters.get("closed_by"),
                status=status,
                pri=pri,
            )
            if count_only:
                if isinstance(payload, dict):
                    payload = dict(payload)
                    payload["resolvedFilters"] = _task_filters_echo(args, filters)
                emit(
                    summary_svc.count_only_from_list(
                        payload,
                        kind="tasks",
                        list_key="tasks",
                        filters=_scope_filter_meta(args),
                    ),
                    is_list=False,
                )
            else:
                emit(payload, is_list=True, fields=fields)
        return 0

    write_noun = WRITE_NOUNS.get(args.cmd)
    if write_noun is not None:
        return dispatch_write(write_noun, client, args)

    if args.cmd == "comment":
        if args.c_cmd == "list":
            emit(
                normalize_comment_rows(
                    comment_svc.list_comments(client, args.type, args.id)
                ),
                is_list=True,
                fields=["id", "action", "editable", "comment"],
            )
            return 0
        if args.c_cmd == "add":
            text = " ".join(args.comment)
            r = comment_svc.add_comment(client, args.type, args.id, text)
            emit(
                {"http": r["status"], "result": r["data"], "backend": client.backend},
                is_list=False,
            )
            return 0
        if args.c_cmd == "edit":
            text = " ".join(args.comment)
            r = comment_svc.edit_comment(client, args.action_id, text)
            emit(
                {"http": r["status"], "result": r["data"], "backend": client.backend},
                is_list=False,
            )
            return 0

    if dispatch_registry(client, args):
        return 0

    parser.error("unknown command")
    return 2
