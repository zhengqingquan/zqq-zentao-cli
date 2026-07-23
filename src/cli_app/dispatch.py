# -*- coding: utf-8 -*-
"""CLI main dispatch after argparse."""

from __future__ import annotations

import argparse
from typing import Any

from ..config import set_config_path
from ..factory import create_client
from ..output import configure_output, emit
from ..rest.resources import (
    SPECIAL_CMDS,
    resource_by_detail_cmd,
    resource_by_list_cmd,
)
from ..services import auth as auth_svc
from ..services import comments as comment_svc
from ..services import my_pages as my_page_svc
from ..services import resources as resource_svc
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
) -> tuple[str | None, str | None]:
    """Resolve assignedTo/openedBy via REST list_users when available."""
    assigned_to = getattr(args, "assignedTo", None)
    opened_by = getattr(args, "openedBy", None)
    if not assigned_to and not opened_by:
        return None, None
    list_users = getattr(client, "list_users", None)
    if list_users is None:
        return (
            (str(assigned_to).strip() or None) if assigned_to else None,
            (str(opened_by).strip() or None) if opened_by else None,
        )
    try:
        at = resolve_optional(list_users, assigned_to)
        ob = resolve_optional(list_users, opened_by)
        return at, ob
    except SystemExit:
        if getattr(client, "backend", None) == "web":
            return (
                (str(assigned_to).strip() or None) if assigned_to else None,
                (str(opened_by).strip() or None) if opened_by else None,
            )
        raise


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
            else {"assigned_to": None, "opened_by": None}
        )
        status = resource_svc.status_from_args(args) if list_res.user_filters else None
        page = getattr(args, "page", 1)
        limit = getattr(args, "limit", 50)
        emit(
            resource_svc.list_by_cmd(
                client,
                args.cmd,
                page=page,
                limit=limit,
                scopes=scopes,
                path_param=path_param,
                query=query,
                assigned_to=filters.get("assigned_to"),
                opened_by=filters.get("opened_by"),
                status=status,
            ),
            is_list=True,
            fields=fields_for(args.cmd, args),
        )
        return True

    detail_res = resource_by_detail_cmd(args.cmd)
    if detail_res is not None and args.cmd not in SPECIAL_CMDS:
        emit(resource_svc.get_by_cmd(client, args.cmd, args.id), is_list=False)
        return True

    return False


def main(argv: list[str] | None = None) -> int:
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
        assigned_to, opened_by = resolve_task_user_filters(client, args)
        status = resource_svc.status_from_args(args)
        fields = fields_for("tasks", args)
        if args.execution:
            emit(
                task_svc.execution_tasks(
                    client,
                    args.execution,
                    assigned_to=assigned_to,
                    opened_by=opened_by,
                    status=status,
                ),
                is_list=True,
                fields=fields,
            )
        else:
            emit(
                task_svc.list_tasks(
                    client,
                    page=args.page,
                    limit=args.limit,
                    assigned_to=assigned_to,
                    opened_by=opened_by,
                    status=status,
                ),
                is_list=True,
                fields=fields,
            )
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
