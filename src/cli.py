#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZenTao dual-backend CLI (Web PATHINFO / REST Token).

Auth:
  - Server/account: ZENTAO_SERVER (or ZENTAO_URL) / ZENTAO_ACCOUNT,
    or fallback ~/.config/zentao/zentao.json
  - Web: ZENTAO_PASSWORD (required)
  - REST: ZENTAO_TOKEN, or exchange ZENTAO_PASSWORD for a token
  - Backend: --backend / ZENTAO_BACKEND = web|rest|auto

Usage:
  zentao whoami
  zentao --backend rest whoami
  zentao my-tasks
  zentao tasks --execution 1664
  zentao task 39973
  zentao comment list task 39973

Never print Cookie / password / Token.
"""

from __future__ import annotations

import argparse
import json
from typing import Any

from .factory import create_client
from .services import comments as comment_svc
from .services import tasks as task_svc
from .web.parse import strip_tags


def print_json(obj: Any) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


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


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="zentao",
        description="ZenTao dual-backend client (Web Cookie / REST Token)",
    )
    p.add_argument(
        "--backend",
        choices=("web", "rest", "auto"),
        default=None,
        help="Transport backend (default: ZENTAO_BACKEND, or auto)",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("whoami", help="Show configured account and server (logs in)")
    sub.add_parser("my-tasks", help="Tasks assigned to me")

    p_tasks = sub.add_parser("tasks", help="Task list under an execution")
    p_tasks.add_argument("--execution", "-e", required=True, help="Execution ID")

    p_task = sub.add_parser("task", help="Task detail (JSON)")
    p_task.add_argument("id", help="Task ID")

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
    return args.cmd


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    cap = _capability(args)
    client = create_client(cap, cli_backend=args.backend)

    if args.cmd == "whoami":
        print_json(client.whoami())
        return 0

    if args.cmd == "my-tasks":
        print_task_table(task_svc.my_tasks(client))
        return 0

    if args.cmd == "tasks":
        print_task_table(task_svc.execution_tasks(client, args.execution))
        return 0

    if args.cmd == "task":
        print_json(task_svc.get_task(client, args.id))
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
