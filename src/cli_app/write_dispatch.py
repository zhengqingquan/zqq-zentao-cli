# -*- coding: utf-8 -*-
"""Table-driven write dispatch (task/bug/story/todo/test*)."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from ..output import emit
from ..protocol import ZenTaoClient
from ..services import bugs as bug_svc
from ..services import resources as resource_svc
from ..services import stories as story_svc
from ..services import tasks as task_svc
from ..services import testcases as testcase_svc
from ..services import testsuites as testsuite_svc
from ..services import testtasks as testtask_svc
from ..services import todos as todo_svc
from .body import body_from_args, is_id_token

CreateFn = Callable[..., dict[str, Any]]
UpdateFn = Callable[..., dict[str, Any]]
DeleteFn = Callable[..., dict[str, Any]]
ActionFn = Callable[..., dict[str, Any]]
GetFn = Callable[[ZenTaoClient, str | int], dict[str, Any]]


@dataclass(frozen=True)
class WriteNoun:
    name: str
    ops: frozenset[str]
    ops_help: str
    create_scope: str  # argparse attr: execution|product|project|"" (none)
    create_defaults: dict[str, Any]
    require_on_create: tuple[str, ...]
    copy_title_to_spec: bool
    get_detail: GetFn
    create: CreateFn
    update: UpdateFn
    delete: DeleteFn
    action: ActionFn


def _get_task(client: ZenTaoClient, oid: str | int) -> dict[str, Any]:
    return task_svc.get_task(client, oid)


def _get_bug(client: ZenTaoClient, oid: str | int) -> dict[str, Any]:
    return resource_svc.get_by_cmd(client, "bug", oid)


def _get_story(client: ZenTaoClient, oid: str | int) -> dict[str, Any]:
    return resource_svc.get_by_cmd(client, "story", oid)


def _get_todo(client: ZenTaoClient, oid: str | int) -> dict[str, Any]:
    return resource_svc.get_by_cmd(client, "todo", oid)


def _get_testcase(client: ZenTaoClient, oid: str | int) -> dict[str, Any]:
    return resource_svc.get_by_cmd(client, "testcase", oid)


def _get_testsuite(client: ZenTaoClient, oid: str | int) -> dict[str, Any]:
    return resource_svc.get_by_cmd(client, "testsuite", oid)


def _get_testtask(client: ZenTaoClient, oid: str | int) -> dict[str, Any]:
    return resource_svc.get_by_cmd(client, "testtask", oid)


WRITE_NOUNS: dict[str, WriteNoun] = {
    "task": WriteNoun(
        name="task",
        ops=frozenset(
            {"create", "update", "delete", "start", "finish", "close", "activate", "assign"}
        ),
        ops_help="create|update|delete|start|finish|close|activate|assign",
        create_scope="execution",
        create_defaults={},
        require_on_create=(),
        copy_title_to_spec=False,
        get_detail=_get_task,
        create=task_svc.create_task,
        update=task_svc.update_task,
        delete=task_svc.delete_task,
        action=task_svc.task_action,
    ),
    "bug": WriteNoun(
        name="bug",
        ops=frozenset(
            {
                "create",
                "update",
                "delete",
                "confirm",
                "resolve",
                "close",
                "activate",
                "assign",
            }
        ),
        ops_help="create|update|delete|confirm|resolve|close|activate|assign",
        create_scope="product",
        create_defaults={
            "openedBuild": ["trunk"],
            "pri": 3,
            "severity": 3,
            "type": "codeerror",
        },
        require_on_create=(),
        copy_title_to_spec=False,
        get_detail=_get_bug,
        create=bug_svc.create_bug,
        update=bug_svc.update_bug,
        delete=bug_svc.delete_bug,
        action=bug_svc.bug_action,
    ),
    "story": WriteNoun(
        name="story",
        ops=frozenset(
            {
                "create",
                "update",
                "delete",
                "change",
                "close",
                "activate",
                "assign",
                "review",
                "submitreview",
                "recall",
            }
        ),
        ops_help=(
            "create|update|delete|change|close|activate|assign|review|submitreview|recall"
        ),
        create_scope="product",
        create_defaults={"pri": 3, "category": "feature", "type": "story"},
        require_on_create=("title",),
        copy_title_to_spec=True,
        get_detail=_get_story,
        create=story_svc.create_story,
        update=story_svc.update_story,
        delete=story_svc.delete_story,
        action=story_svc.story_action,
    ),
    "todo": WriteNoun(
        name="todo",
        ops=frozenset({"create", "update", "delete", "finish", "activate"}),
        ops_help="create|update|delete|finish|activate",
        create_scope="",
        create_defaults={"type": "custom", "pri": "3", "status": "wait"},
        require_on_create=("name",),
        copy_title_to_spec=False,
        get_detail=_get_todo,
        create=todo_svc.create_todo,
        update=todo_svc.update_todo,
        delete=todo_svc.delete_todo,
        action=todo_svc.todo_action,
    ),
    "testcase": WriteNoun(
        name="testcase",
        ops=frozenset({"create", "update", "delete", "results"}),
        ops_help="create|update|delete|results",
        create_scope="product",
        create_defaults={"type": "feature", "pri": 3},
        require_on_create=("title", "steps"),
        copy_title_to_spec=False,
        get_detail=_get_testcase,
        create=testcase_svc.create_testcase,
        update=testcase_svc.update_testcase,
        delete=testcase_svc.delete_testcase,
        action=testcase_svc.testcase_action,
    ),
    "testsuite": WriteNoun(
        name="testsuite",
        ops=frozenset({"create", "delete"}),
        ops_help="create|delete",
        create_scope="product",
        create_defaults={"type": "private"},
        require_on_create=("name",),
        copy_title_to_spec=False,
        get_detail=_get_testsuite,
        create=testsuite_svc.create_testsuite,
        update=testsuite_svc.update_testsuite,
        delete=testsuite_svc.delete_testsuite,
        action=testsuite_svc.testsuite_action,
    ),
    "testtask": WriteNoun(
        name="testtask",
        ops=frozenset({"create", "delete"}),
        ops_help="create|delete",
        create_scope="project",
        create_defaults={},
        require_on_create=("name", "product", "execution", "build", "begin", "end"),
        copy_title_to_spec=False,
        get_detail=_get_testtask,
        create=testtask_svc.create_testtask,
        update=testtask_svc.update_testtask,
        delete=testtask_svc.delete_testtask,
        action=testtask_svc.testtask_action,
    ),
}


def dispatch_write(noun: WriteNoun, client: ZenTaoClient, args: argparse.Namespace) -> int:
    yes = bool(getattr(args, "yes", False))
    if is_id_token(args.op) and args.id is None:
        emit(noun.get_detail(client, args.op), is_list=False)
        return 0

    op = str(args.op).strip().lower()
    if op not in noun.ops:
        raise SystemExit(
            f"Unknown {noun.name} op {args.op!r}; use {noun.name} <id> or {noun.ops_help}"
        )

    if op == "create":
        scope_id: str | int | None = None
        if noun.create_scope:
            scope_id = getattr(args, noun.create_scope, None)
            if not scope_id:
                raise SystemExit(f"{noun.name} create requires --{noun.create_scope} <id>")
        body = body_from_args(args)
        # Scope id is already in the URL path; do not also POST it (except fields
        # that are not the path param — e.g. testtask still needs product/execution/build).
        if noun.create_scope:
            body.pop(noun.create_scope, None)
        for key in noun.require_on_create:
            if key not in body:
                raise SystemExit(
                    f"{noun.name} create requires --{key} or --data with {key}"
                )
        if noun.copy_title_to_spec and "spec" not in body:
            body["spec"] = body["title"]
        for key, val in noun.create_defaults.items():
            if key not in body:
                body[key] = val
        emit(noun.create(client, scope_id, body, yes=yes), is_list=False)
        return 0

    oid = args.id
    if not oid:
        raise SystemExit(f"{noun.name} {op} requires <id>")
    if op == "update":
        emit(noun.update(client, oid, body_from_args(args), yes=yes), is_list=False)
        return 0
    if op == "delete":
        emit(noun.delete(client, oid, yes=yes), is_list=False)
        return 0
    emit(noun.action(client, op, oid, body_from_args(args), yes=yes), is_list=False)
    return 0
