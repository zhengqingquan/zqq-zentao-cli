#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task domain operations (delegates to ZenTaoClient)."""

from __future__ import annotations

from typing import Any

from ..protocol import ZenTaoClient


def my_tasks(client: ZenTaoClient) -> list[dict[str, Any]]:
    return client.my_tasks()


def list_tasks(client: ZenTaoClient, *, page: int = 1, limit: int = 100) -> dict[str, Any]:
    return client.list_tasks(page=page, limit=limit)


def execution_tasks(client: ZenTaoClient, execution_id: str | int) -> list[dict[str, Any]]:
    return client.execution_tasks(execution_id)


def get_task(client: ZenTaoClient, task_id: str | int) -> dict[str, Any]:
    return client.get_task(task_id)
