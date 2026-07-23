#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Todo write operations via ZenTaoClient."""

from __future__ import annotations

from typing import Any

from ..confirm_util import confirm_or_exit
from ..protocol import ZenTaoClient


def create_todo(
    client: ZenTaoClient,
    _scope: str | int | None,
    body: dict[str, Any],
    *,
    yes: bool = False,
) -> dict[str, Any]:
    confirm_or_exit("Create todo?", yes=yes)
    return client.create_todo(body)


def update_todo(
    client: ZenTaoClient,
    todo_id: str | int,
    body: dict[str, Any],
    *,
    yes: bool = False,
) -> dict[str, Any]:
    confirm_or_exit(f"Update todo {todo_id}?", yes=yes)
    return client.update_todo(todo_id, body)


def delete_todo(
    client: ZenTaoClient, todo_id: str | int, *, yes: bool = False
) -> dict[str, Any]:
    confirm_or_exit(f"Delete todo {todo_id}? This cannot be undone easily.", yes=yes)
    return client.delete_todo(todo_id)


def todo_action(
    client: ZenTaoClient,
    action: str,
    todo_id: str | int,
    body: dict[str, Any] | None = None,
    *,
    yes: bool = False,
) -> dict[str, Any]:
    confirm_or_exit(f"Todo {action} id={todo_id}?", yes=yes)
    return client.todo_action(todo_id, action, body or {})
