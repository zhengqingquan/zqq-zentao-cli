# -*- coding: utf-8 -*-
"""argparse construction for zqq-zentao."""

from __future__ import annotations

import argparse
from typing import Any

from ..output import package_version
from ..rest.resources import SPECIAL_CMDS, resources_for_cli
from ..web.my_pages import MY_PAGES, my_page_by_cmd

_SCOPE_FLAGS = (
    ("product", "Scope by product ID"),
    ("project", "Scope by project ID"),
    ("execution", "Scope by execution ID"),
    ("program", "Scope by program ID"),
    ("lib", "Scope by doc lib ID"),
)

_QUERY_HELPS = {
    "search": "Search by name/code (client-side; projects/products/programs; users by account/realname/pinyin)",
}


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
        parser.add_argument(
            f"--{name}", default=None, help=helps.get(name, f"Filter by {name}")
        )


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


def add_write_flags(parser: argparse.ArgumentParser) -> None:
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
    parser.add_argument("--product", default=None, help="Product id (bug/story create)")
    parser.add_argument("--execution", "-e", default=None, help="Execution id (task create)")
    parser.add_argument("--openedBuild", default=None, help="Bug openedBuild (default trunk)")
    parser.add_argument("--spec", default=None, help="Story description / spec")
    parser.add_argument("--verify", default=None, help="Story acceptance criteria")
    parser.add_argument("--category", default=None, help="Story category (e.g. feature)")
    parser.add_argument("--closedReason", default=None, help="Story close reason")
    parser.add_argument("--result", default=None, help="Story review result")
    parser.add_argument("--estStarted", default=None)
    parser.add_argument("--deadline", default=None)
    parser.add_argument("--consumed", default=None)
    parser.add_argument("--left", default=None)
    parser.add_argument("--currentConsumed", default=None)
    parser.add_argument("--finishedDate", default=None)
    parser.add_argument("--realStarted", default=None)


def _register_my_page_parsers(sub: argparse._SubParsersAction[Any]) -> None:
    for page in MY_PAGES.values():
        p = sub.add_parser(page.cmd, help=page.help)
        _add_my_page_flags(p, page.cmd)


def _register_resource_parsers(sub: argparse._SubParsersAction[Any]) -> None:
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
    p.add_argument(
        "--api",
        choices=("v1", "v2"),
        default=None,
        help="REST API version for reads (default: ZENTAO_API or v1); writes always use v1",
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
    add_write_flags(p_task)

    p_bug = sub.add_parser(
        "bug",
        help="Bug detail or write: bug <id> | bug create|update|delete|resolve|…",
    )
    p_bug.add_argument(
        "op",
        help="Bug id (detail) or action: create|update|delete|confirm|resolve|close|activate|assign",
    )
    p_bug.add_argument("id", nargs="?", help="Bug id for write/actions")
    add_write_flags(p_bug)

    p_story = sub.add_parser(
        "story",
        help="Story detail or write: story <id> | story create|update|delete|change|…",
    )
    p_story.add_argument(
        "op",
        help=(
            "Story id (detail) or action: create|update|delete|change|close|"
            "activate|assign|review|submitreview|recall"
        ),
    )
    p_story.add_argument("id", nargs="?", help="Story id for write/actions")
    add_write_flags(p_story)

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
