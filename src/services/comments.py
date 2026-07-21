#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Comment domain operations (web only for now)."""

from __future__ import annotations

from typing import Any

from ..protocol import ZenTaoClient


def list_comments(client: ZenTaoClient, object_type: str, object_id: str | int) -> list[Any]:
    return client.list_comments(object_type, object_id)


def add_comment(
    client: ZenTaoClient, object_type: str, object_id: str | int, comment: str
) -> dict[str, Any]:
    return client.add_comment(object_type, object_id, comment)


def edit_comment(client: ZenTaoClient, action_id: str | int, comment: str) -> dict[str, Any]:
    return client.edit_comment(action_id, comment)
