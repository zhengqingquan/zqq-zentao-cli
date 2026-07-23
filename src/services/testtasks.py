#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Testtask write operations via ZenTaoClient."""

from __future__ import annotations

from typing import Any

from ..confirm_util import confirm_or_exit
from ..protocol import ZenTaoClient


def create_testtask(
    client: ZenTaoClient,
    project_id: str | int,
    body: dict[str, Any],
    *,
    yes: bool = False,
) -> dict[str, Any]:
    confirm_or_exit(f"Create testtask under project {project_id}?", yes=yes)
    return client.create_testtask(project_id, body)


def update_testtask(
    client: ZenTaoClient,
    task_id: str | int,
    body: dict[str, Any],
    *,
    yes: bool = False,
) -> dict[str, Any]:
    raise SystemExit(
        "testtask update is not exposed by ZenTao REST APIv1 "
        f"(id={task_id}); body keys={sorted(body)!r}"
    )


def delete_testtask(
    client: ZenTaoClient, task_id: str | int, *, yes: bool = False
) -> dict[str, Any]:
    confirm_or_exit(
        f"Delete testtask {task_id}? This cannot be undone easily.", yes=yes
    )
    return client.delete_testtask(task_id)


def testtask_action(
    client: ZenTaoClient,
    action: str,
    task_id: str | int,
    body: dict[str, Any] | None = None,
    *,
    yes: bool = False,
) -> dict[str, Any]:
    raise SystemExit(
        f"Unknown testtask action {action!r} id={task_id}; "
        f"body keys={sorted(body or {})!r}"
    )
