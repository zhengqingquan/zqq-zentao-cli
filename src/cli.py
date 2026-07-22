#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZenTao dual-backend CLI (Web PATHINFO / REST Token).

Auth:
  - zqq-zentao login -s <url> -u <account> -p <password>
  - Or env ZENTAO_SERVER/ZENTAO_URL, ZENTAO_ACCOUNT, ZENTAO_PASSWORD / ZENTAO_TOKEN
  - Caches webCookies + token in ~/.config/zentao/zentao.json (no password on disk)
  - Backend: --backend / ZENTAO_BACKEND = web|rest|auto
  - TLS: --insecure / --secure / ZENTAO_INSECURE (default skip verify)
  - Global (aligned with official zentao-cli):
      -V/--version-flag, --format, --silent, --timeout, --config, --machine-readable
      --pick <fields> for table column selection

Never print Cookie / password / Token.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any

from .config import set_config_path
from .factory import create_client
from .output import configure_output, emit, package_version
from .rest.resources import (
    SPECIAL_CMDS,
    resource_by_detail_cmd,
    resource_by_list_cmd,
    resources_for_cli,
)
from .services import auth as auth_svc
from .services import bugs as bug_svc
from .services import comments as comment_svc
from .services import my_pages as my_page_svc
from .services import resources as resource_svc
from .services import tasks as task_svc
from .payload import merge_payload
from .user_resolve import resolve_optional
from .web.my_pages import MY_PAGES, my_page_by_cmd, resolve_browse, uses_rest_default
from .web.parse import strip_tags

_BUG_OPS = frozenset(
    {"create", "update", "delete", "confirm", "resolve", "close", "activate", "assign"}
)
_TASK_OPS = frozenset(
    {"create", "update", "delete", "start", "finish", "close", "activate", "assign"}
)

_SCOPE_FLAGS = (
    ("product", "Scope by product ID"),
    ("project", "Scope by project ID"),
    ("execution", "Scope by execution ID"),
    ("program", "Scope by program ID"),
    ("lib", "Scope by doc lib ID"),
)

_TASK_FIELDS = ["id", "status", "pri", "deadline", "executionName", "name"]
_BUG_FIELDS = ["id", "status", "severity", "pri", "productName", "title"]
_STORY_FIELDS = ["id", "status", "pri", "stage", "title"]
_USER_FIELDS = ["account", "realname"]

_DEFAULT_LIST_FIELDS: dict[str, list[str]] = {
    "tasks": _TASK_FIELDS,
    "bugs": _BUG_FIELDS,
    "stories": _STORY_FIELDS,
    "users": _USER_FIELDS,
}
for _mp in MY_PAGES.values():
    _DEFAULT_LIST_FIELDS[_mp.cmd] = list(_mp.table_fields)

_QUERY_HELPS = {
    "search": "Search users by account / realname / pinyin (client-side)",
}


def _normalize_task_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for t in rows:
        out.append(
            {
                "id": t.get("id"),
                "status": t.get("status"),
                "pri": t.get("pri"),
                "deadline": t.get("deadline") or "",
                "executionName": t.get("executionName") or t.get("execution") or "",
                "name": t.get("name") or "",
            }
        )
    return out


def _normalize_bug_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for b in rows:
        out.append(
            {
                "id": b.get("id"),
                "status": b.get("status"),
                "severity": b.get("severity"),
                "pri": b.get("pri"),
                "productName": b.get("productName") or b.get("product") or "",
                "title": b.get("title") or "",
            }
        )
    return out


def _normalize_comment_rows(data: list[Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for a in data:
        if not isinstance(a, dict):
            continue
        comment = strip_tags(a.get("comment") or "") or "(no comment text)"
        rows.append(
            {
                "id": a.get("id"),
                "action": a.get("action"),
                "editable": "editable" if a.get("commentEditable") else "",
                "comment": comment,
            }
        )
    return rows


def _parse_pick(args: argparse.Namespace) -> list[str] | None:
    raw = getattr(args, "pick", None)
    if not raw:
        return None
    fields = [p.strip() for p in str(raw).split(",") if p.strip()]
    return fields or None


def _fields_for(cmd: str, args: argparse.Namespace) -> list[str] | None:
    picked = _parse_pick(args)
    if picked:
        return picked
    return _DEFAULT_LIST_FIELDS.get(cmd)


def _add_page_limit(parser: argparse.ArgumentParser, *, limit: int = 50) -> None:
    parser.add_argument("--page", type=int, default=1, help="Page number (default 1)")
    parser.add_argument(
        "--limit",
        type=int,
        default=limit,
        help=f"Page size (default {limit})",
    )


def _add_scope_flags(parser: argparse.ArgumentParser, scope_names: dict[str, str]) -> None:
    for name, help_text in _SCOPE_FLAGS:
        if name not in scope_names:
            continue
        parser.add_argument(f"--{name}", help=help_text)


def _add_user_filter_flags(
    parser: argparse.ArgumentParser, filter_names: tuple[str, ...]
) -> None:
    helps = {
        "assignedTo": "Filter by assignee (account or realname)",
        "openedBy": "Filter by opener (account or realname)",
    }
    for name in filter_names:
        parser.add_argument(f"--{name}", default=None, help=helps.get(name, f"Filter by {name}"))


def _add_status_flag(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--status",
        default=None,
        help="Filter by status (comma-separated, e.g. wait,doing)",
    )


def _add_my_page_flags(parser: argparse.ArgumentParser, page_cmd: str) -> None:
    page = my_page_by_cmd(page_cmd)
    assert page is not None
    types = (*page.work_types, *page.contribute_types, *page.todo_types)
    type_help = ", ".join(types) if types else page.default_type
    parser.add_argument(
        "--type",
        default=None,
        dest="browse_type",
        help=f"Browse type (default {page.default_type}); one of: {type_help}",
    )
    if page.default_scope != "todo":
        parser.add_argument(
            "--scope",
            choices=("work", "contribute"),
            default=None,
            help=f"my-work vs my-contribute (default {page.default_scope})",
        )


def _add_write_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip interactive confirmation for write operations",
    )
    parser.add_argument(
        "--data",
        default=None,
        help='JSON object body, e.g. \'{"title":"x","pri":1}\'',
    )
    parser.add_argument("--comment", default=None, help="Comment / remark field")
    parser.add_argument("--assignedTo", default=None, help="Assignee account")
    parser.add_argument("--title", default=None)
    parser.add_argument("--name", default=None)
    parser.add_argument("--pri", default=None)
    parser.add_argument("--severity", default=None)
    parser.add_argument("--type", dest="obj_type", default=None, help="Object type field")
    parser.add_argument("--resolution", default=None, help="Bug resolution")
    parser.add_argument("--product", default=None, help="Product id (bug create)")
    parser.add_argument("--execution", "-e", default=None, help="Execution id (task create)")
    parser.add_argument("--openedBuild", default=None, help="Bug openedBuild (default trunk)")
    parser.add_argument("--estStarted", default=None)
    parser.add_argument("--deadline", default=None)
    parser.add_argument("--consumed", default=None)
    parser.add_argument("--left", default=None)
    parser.add_argument("--currentConsumed", default=None)
    parser.add_argument("--finishedDate", default=None)
    parser.add_argument("--realStarted", default=None)


def _is_id_token(token: str | None) -> bool:
    return bool(token) and str(token).isdigit()


def _body_from_args(args: argparse.Namespace, *, extra: dict | None = None) -> dict:
    fields = {
        "comment": getattr(args, "comment", None),
        "assignedTo": getattr(args, "assignedTo", None),
        "title": getattr(args, "title", None),
        "name": getattr(args, "name", None),
        "pri": getattr(args, "pri", None),
        "severity": getattr(args, "severity", None),
        "type": getattr(args, "obj_type", None),
        "resolution": getattr(args, "resolution", None),
        "openedBuild": getattr(args, "openedBuild", None),
        "estStarted": getattr(args, "estStarted", None),
        "deadline": getattr(args, "deadline", None),
        "consumed": getattr(args, "consumed", None),
        "left": getattr(args, "left", None),
        "currentConsumed": getattr(args, "currentConsumed", None),
        "finishedDate": getattr(args, "finishedDate", None),
        "realStarted": getattr(args, "realStarted", None),
    }
    if extra:
        fields.update(extra)
    return merge_payload(data_json=getattr(args, "data", None), fields=fields)


def _register_my_page_parsers(sub: argparse._SubParsersAction[Any]) -> None:
    for page in MY_PAGES.values():
        p = sub.add_parser(page.cmd, help=page.help)
        _add_my_page_flags(p, page.cmd)


def _register_resource_parsers(sub: argparse._SubParsersAction[Any]) -> None:
    """Register REST browse commands from the resource registry."""
    registered: set[str] = set()
    for res in resources_for_cli():
        if res.list_cmd and res.list_cmd not in SPECIAL_CMDS and res.list_cmd not in registered:
            p = sub.add_parser(res.list_cmd, help=res.help)
            if res.path_param:
                p.add_argument(res.path_param, help=f"{res.path_param} path parameter")
            if res.paginated:
                _add_page_limit(p)
            if res.scopes:
                _add_scope_flags(p, res.scopes)
            if res.user_filters:
                _add_user_filter_flags(p, res.user_filters)
                _add_status_flag(p)
            for qname in res.query_params:
                req = qname in res.required_query
                p.add_argument(
                    f"--{qname}",
                    required=req,
                    default=None,
                    help=_QUERY_HELPS.get(
                        qname,
                        f"Query param {qname}" + (" (required)" if req else ""),
                    ),
                )
            registered.add(res.list_cmd)

        if (
            res.detail_cmd
            and res.detail_cmd not in SPECIAL_CMDS
            and res.detail_cmd not in registered
        ):
            p = sub.add_parser(res.detail_cmd, help=res.help)
            id_help = "Account" if res.detail_cmd == "user" else "Resource ID"
            p.add_argument("id", help=id_help)
            registered.add(res.detail_cmd)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="zqq-zentao",
        description="ZenTao dual-backend client (Web Cookie / REST Token)",
    )
    p.add_argument(
        "-V",
        "--version-flag",
        action="version",
        version=package_version(),
        help="Show version number",
    )
    p.add_argument(
        "--format",
        choices=("markdown", "json", "raw"),
        default=None,
        help="Output format (markdown|json|raw); default markdown",
    )
    p.add_argument(
        "--silent",
        action="store_true",
        help="Silent mode (suppress result output)",
    )
    p.add_argument(
        "--timeout",
        type=int,
        default=None,
        metavar="ms",
        help="Request timeout in milliseconds (default 60000)",
    )
    p.add_argument(
        "--config",
        metavar="config_file",
        help="Custom config file path (or ZENTAO_CONFIG_FILE)",
    )
    p.add_argument(
        "--machine-readable",
        action="store_true",
        help="Machine-readable mode: compact output, disable colors",
    )
    p.add_argument(
        "--pick",
        default=None,
        metavar="fields",
        help="Comma-separated fields for table output (overrides defaults)",
    )
    p.add_argument(
        "--backend",
        choices=("web", "rest", "auto"),
        default=None,
        help="Transport backend (default: ZENTAO_BACKEND, or auto)",
    )
    tls = p.add_mutually_exclusive_group()
    tls.add_argument(
        "--insecure",
        action="store_true",
        help="Skip TLS certificate verification (same idea as official zentao --insecure)",
    )
    tls.add_argument(
        "--secure",
        action="store_true",
        help="Verify TLS certificates (overrides default ZENTAO_INSECURE=1)",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    p_login = sub.add_parser(
        "login",
        help="Login and cache webCookies + REST token in ~/.config/zentao/zentao.json",
    )
    p_login.add_argument("-s", "--server", help="ZenTao URL (or ZENTAO_SERVER / ZENTAO_URL)")
    p_login.add_argument("-u", "--account", help="Account (or ZENTAO_ACCOUNT)")
    p_login.add_argument("-p", "--password", help="Password (or ZENTAO_PASSWORD)")

    sub.add_parser("whoami", help="Show configured account and server")
    _register_my_page_parsers(sub)

    p_tasks = sub.add_parser(
        "tasks",
        help="Task list: REST /tasks, or --execution for one execution (web/rest)",
    )
    p_tasks.add_argument("--execution", "-e", help="Execution ID")
    _add_user_filter_flags(p_tasks, ("assignedTo", "openedBy"))
    _add_status_flag(p_tasks)
    _add_page_limit(p_tasks, limit=100)

    p_task = sub.add_parser(
        "task",
        help="Task detail or write: task <id> | task create|update|delete|start|…",
    )
    p_task.add_argument(
        "op",
        help="Task id (detail) or action: create|update|delete|start|finish|close|activate|assign",
    )
    p_task.add_argument("id", nargs="?", help="Task id for write/actions")
    _add_write_flags(p_task)

    p_bug = sub.add_parser(
        "bug",
        help="Bug detail or write: bug <id> | bug create|update|delete|resolve|…",
    )
    p_bug.add_argument(
        "op",
        help="Bug id (detail) or action: create|update|delete|confirm|resolve|close|activate|assign",
    )
    p_bug.add_argument("id", nargs="?", help="Bug id for write/actions")
    _add_write_flags(p_bug)

    p_c = sub.add_parser("comment", help="Comment list/add/edit (web only)")
    csub = p_c.add_subparsers(dest="c_cmd", required=True)

    p_list = csub.add_parser("list", help="List comment history")
    p_list.add_argument("type", help="e.g. task / bug / story")
    p_list.add_argument("id", help="Object ID")

    p_add = csub.add_parser("add", help="Add a comment (does not change status)")
    p_add.add_argument("type")
    p_add.add_argument("id")
    p_add.add_argument("comment", nargs="+", help="Comment body")

    p_edit = csub.add_parser("edit", help="Edit an existing comment")
    p_edit.add_argument("action_id", help="Action ID (from list)")
    p_edit.add_argument("comment", nargs="+")

    _register_resource_parsers(sub)

    return p


def _capability(args: argparse.Namespace) -> str:
    if args.cmd == "comment":
        return f"comment.{args.c_cmd}"
    if args.cmd == "tasks" and not args.execution:
        return "tasks.list"
    if args.cmd == "task":
        if _is_id_token(args.op) and args.id is None:
            return "task"
        return "task.write"
    if args.cmd == "bug":
        return "bug" if (_is_id_token(args.op) and args.id is None) else "bug.write"
    page = my_page_by_cmd(args.cmd)
    if page is not None:
        scope, browse_type = resolve_browse(
            page,
            browse_type=getattr(args, "browse_type", None),
            scope=getattr(args, "scope", None),
        )
        if uses_rest_default(page, scope, browse_type):
            return page.cmd
        return "my-page"
    return args.cmd


def _cli_insecure(args: argparse.Namespace) -> bool | None:
    if args.insecure:
        return True
    if args.secure:
        return False
    return None


def _resolve_task_user_filters(client: Any, args: argparse.Namespace) -> tuple[str | None, str | None]:
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
        # Web-only clients cannot list users; fall back to literal token
        # only when backend is web (execution path).
        if getattr(client, "backend", None) == "web":
            return (
                (str(assigned_to).strip() or None) if assigned_to else None,
                (str(opened_by).strip() or None) if opened_by else None,
            )
        raise


def _dispatch_registry(client: Any, args: argparse.Namespace) -> bool:
    """Handle registry-driven list/detail commands. Returns True if handled."""
    list_res = resource_by_list_cmd(args.cmd)
    if list_res is not None and args.cmd not in SPECIAL_CMDS:
        path_param = None
        if list_res.path_param:
            path_param = getattr(args, list_res.path_param, None)
        scopes = resource_svc.scopes_from_args(args, list_res) if list_res.scopes else None
        query = resource_svc.query_from_args(args, list_res) if list_res.query_params else None
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
            fields=_fields_for(args.cmd, args),
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

    insecure = _cli_insecure(args)
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

    cap = _capability(args)
    client = create_client(
        cap,
        cli_backend=args.backend,
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
        fields = _fields_for(args.cmd, args)
        # Keep compact markdown for tasks/bugs defaults.
        if args.cmd == "my-tasks":
            rows = _normalize_task_rows(rows)
        elif args.cmd == "my-bugs":
            rows = _normalize_bug_rows(rows)
        emit(rows, is_list=True, fields=fields)
        return 0

    if args.cmd == "tasks":
        assigned_to, opened_by = _resolve_task_user_filters(client, args)
        status = resource_svc.status_from_args(args)
        fields = _fields_for("tasks", args)
        if args.execution:
            emit(
                _normalize_task_rows(
                    task_svc.execution_tasks(
                        client,
                        args.execution,
                        assigned_to=assigned_to,
                        opened_by=opened_by,
                        status=status,
                    )
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

    if args.cmd == "task":
        yes = bool(getattr(args, "yes", False))
        if _is_id_token(args.op) and args.id is None:
            emit(task_svc.get_task(client, args.op), is_list=False)
            return 0
        op = str(args.op).strip().lower()
        if op not in _TASK_OPS:
            raise SystemExit(
                f"Unknown task op {args.op!r}; use task <id> or "
                f"create|update|delete|start|finish|close|activate|assign"
            )
        if op == "create":
            execution = args.execution
            if not execution:
                raise SystemExit("task create requires --execution <id>")
            body = _body_from_args(args)
            emit(task_svc.create_task(client, execution, body, yes=yes), is_list=False)
            return 0
        tid = args.id
        if not tid:
            raise SystemExit(f"task {op} requires <id>")
        if op == "update":
            emit(
                task_svc.update_task(client, tid, _body_from_args(args), yes=yes),
                is_list=False,
            )
            return 0
        if op == "delete":
            emit(task_svc.delete_task(client, tid, yes=yes), is_list=False)
            return 0
        emit(
            task_svc.task_action(client, op, tid, _body_from_args(args), yes=yes),
            is_list=False,
        )
        return 0

    if args.cmd == "bug":
        yes = bool(getattr(args, "yes", False))
        if _is_id_token(args.op) and args.id is None:
            emit(resource_svc.get_by_cmd(client, "bug", args.op), is_list=False)
            return 0
        op = str(args.op).strip().lower()
        if op not in _BUG_OPS:
            raise SystemExit(
                f"Unknown bug op {args.op!r}; use bug <id> or "
                f"create|update|delete|confirm|resolve|close|activate|assign"
            )
        if op == "create":
            product = args.product
            if not product:
                raise SystemExit("bug create requires --product <id>")
            body = _body_from_args(args)
            if "openedBuild" not in body:
                body["openedBuild"] = ["trunk"]
            if "pri" not in body:
                body["pri"] = 3
            if "severity" not in body:
                body["severity"] = 3
            if "type" not in body:
                body["type"] = "codeerror"
            emit(bug_svc.create_bug(client, product, body, yes=yes), is_list=False)
            return 0
        bid = args.id
        if not bid:
            raise SystemExit(f"bug {op} requires <id>")
        if op == "update":
            emit(
                bug_svc.update_bug(client, bid, _body_from_args(args), yes=yes),
                is_list=False,
            )
            return 0
        if op == "delete":
            emit(bug_svc.delete_bug(client, bid, yes=yes), is_list=False)
            return 0
        emit(
            bug_svc.bug_action(client, op, bid, _body_from_args(args), yes=yes),
            is_list=False,
        )
        return 0

    if args.cmd == "comment":
        if args.c_cmd == "list":
            emit(
                _normalize_comment_rows(comment_svc.list_comments(client, args.type, args.id)),
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

    if _dispatch_registry(client, args):
        return 0

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
