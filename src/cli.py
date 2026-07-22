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

Usage:
  zqq-zentao --insecure login -s https://zentao.example.com -u admin -p secret
  zqq-zentao whoami
  zqq-zentao my-tasks
  zqq-zentao tasks
  zqq-zentao tasks --execution 1664
  zqq-zentao task 39973
  zqq-zentao projects
  zqq-zentao executions
  zqq-zentao execution 1664
  zqq-zentao users
  zqq-zentao user admin
  zqq-zentao programs
  zqq-zentao departments
  zqq-zentao comment list task 39973

Never print Cookie / password / Token.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from .factory import create_client
from .services import auth as auth_svc
from .services import browse as browse_svc
from .services import comments as comment_svc
from .services import tasks as task_svc
from .web.parse import strip_tags


def print_json(obj: Any) -> None:
    text = json.dumps(obj, ensure_ascii=False, indent=2)
    try:
        print(text)
    except UnicodeEncodeError:
        enc = getattr(sys.stdout, "encoding", None) or "utf-8"
        sys.stdout.buffer.write((text + "\n").encode(enc, errors="replace"))
        sys.stdout.buffer.flush()


def print_task_table(rows: list[dict[str, Any]]) -> None:
    for t in rows:
        print(
            "\t".join(
                str(x) if x is not None else ""
                for x in [
                    t.get("id"),
                    t.get("status"),
                    t.get("pri"),
                    t.get("deadline") or "",
                    t.get("executionName") or t.get("execution") or "",
                    t.get("name") or "",
                ]
            )
        )
    print(f"count={len(rows)}")


def print_comment_list(data: list[Any]) -> None:
    for a in data:
        if not isinstance(a, dict):
            continue
        editable = "editable" if a.get("commentEditable") else ""
        comment = strip_tags(a.get("comment") or "") or "(no comment text)"
        cols = [a.get("id"), a.get("action"), editable, comment]
        print("\t".join(str(c) for c in cols if c not in ("", None)))
    print(f"count={len(data)}")


def _add_page_limit(parser: argparse.ArgumentParser, *, limit: int = 50) -> None:
    parser.add_argument("--page", type=int, default=1, help="Page number (default 1)")
    parser.add_argument(
        "--limit",
        type=int,
        default=limit,
        help=f"Page size (default {limit})",
    )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="zqq-zentao",
        description="ZenTao dual-backend client (Web Cookie / REST Token)",
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
    sub.add_parser("my-tasks", help="Tasks assigned to me")

    p_tasks = sub.add_parser(
        "tasks",
        help="Task list: REST /tasks, or --execution for one execution (web/rest)",
    )
    p_tasks.add_argument("--execution", "-e", help="Execution ID")
    _add_page_limit(p_tasks, limit=100)

    p_task = sub.add_parser("task", help="Task detail (JSON; REST returns full fields)")
    p_task.add_argument("id", help="Task ID")

    p_users = sub.add_parser("users", help="User list (REST)")
    _add_page_limit(p_users)

    p_user = sub.add_parser("user", help="User detail (REST)")
    p_user.add_argument("account", help="Account")

    p_projects = sub.add_parser("projects", help="Project list (REST)")
    _add_page_limit(p_projects)

    p_programs = sub.add_parser("programs", help="Program list (REST)")
    _add_page_limit(p_programs)

    p_executions = sub.add_parser("executions", help="Execution list (REST)")
    _add_page_limit(p_executions)

    p_execution = sub.add_parser("execution", help="Execution detail (REST)")
    p_execution.add_argument("id", help="Execution ID")

    sub.add_parser("departments", help="Department list (REST)")

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

    return p


def _capability(args: argparse.Namespace) -> str:
    if args.cmd == "comment":
        return f"comment.{args.c_cmd}"
    if args.cmd == "tasks" and not args.execution:
        return "tasks.list"
    return args.cmd


def _cli_insecure(args: argparse.Namespace) -> bool | None:
    if args.insecure:
        return True
    if args.secure:
        return False
    return None


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    insecure = _cli_insecure(args)

    if args.cmd == "login":
        result = auth_svc.do_login(
            server=args.server,
            account=args.account,
            password=args.password,
            backend=args.backend,
            insecure=insecure,
        )
        print_json(result)
        return 0

    cap = _capability(args)
    client = create_client(cap, cli_backend=args.backend, insecure=insecure)

    if args.cmd == "whoami":
        print_json(client.whoami())
        return 0

    if args.cmd == "my-tasks":
        print_task_table(task_svc.my_tasks(client))
        return 0

    if args.cmd == "tasks":
        if args.execution:
            print_task_table(task_svc.execution_tasks(client, args.execution))
        else:
            print_json(task_svc.list_tasks(client, page=args.page, limit=args.limit))
        return 0

    if args.cmd == "task":
        print_json(task_svc.get_task(client, args.id))
        return 0

    if args.cmd == "users":
        print_json(browse_svc.list_users(client, page=args.page, limit=args.limit))
        return 0

    if args.cmd == "user":
        print_json(browse_svc.get_user(client, args.account))
        return 0

    if args.cmd == "projects":
        print_json(browse_svc.list_projects(client, page=args.page, limit=args.limit))
        return 0

    if args.cmd == "programs":
        print_json(browse_svc.list_programs(client, page=args.page, limit=args.limit))
        return 0

    if args.cmd == "executions":
        print_json(browse_svc.list_executions(client, page=args.page, limit=args.limit))
        return 0

    if args.cmd == "execution":
        print_json(browse_svc.get_execution(client, args.id))
        return 0

    if args.cmd == "departments":
        print_json(browse_svc.list_departments(client))
        return 0

    if args.cmd == "comment":
        if args.c_cmd == "list":
            print_comment_list(comment_svc.list_comments(client, args.type, args.id))
            return 0
        if args.c_cmd == "add":
            text = " ".join(args.comment)
            r = comment_svc.add_comment(client, args.type, args.id, text)
            print_json({"http": r["status"], "result": r["data"], "backend": client.backend})
            return 0
        if args.c_cmd == "edit":
            text = " ".join(args.comment)
            r = comment_svc.edit_comment(client, args.action_id, text)
            print_json({"http": r["status"], "result": r["data"], "backend": client.backend})
            return 0

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
