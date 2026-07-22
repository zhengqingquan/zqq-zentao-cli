#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""REST browse helpers (users / projects / programs / executions / departments)."""

from __future__ import annotations

from typing import Any

from ..protocol import ZenTaoClient


def list_users(client: ZenTaoClient, *, page: int = 1, limit: int = 50) -> dict[str, Any]:
    return client.list_users(page=page, limit=limit)


def get_user(client: ZenTaoClient, account: str) -> dict[str, Any]:
    return client.get_user(account)


def list_projects(client: ZenTaoClient, *, page: int = 1, limit: int = 50) -> dict[str, Any]:
    return client.list_projects(page=page, limit=limit)


def list_programs(client: ZenTaoClient, *, page: int = 1, limit: int = 50) -> dict[str, Any]:
    return client.list_programs(page=page, limit=limit)


def list_executions(client: ZenTaoClient, *, page: int = 1, limit: int = 50) -> dict[str, Any]:
    return client.list_executions(page=page, limit=limit)


def get_execution(client: ZenTaoClient, execution_id: str | int) -> dict[str, Any]:
    return client.get_execution(execution_id)


def list_departments(client: ZenTaoClient) -> dict[str, Any]:
    return client.list_departments()
