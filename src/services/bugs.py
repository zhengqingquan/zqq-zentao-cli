#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bug operations via ZenTaoClient."""

from __future__ import annotations

from typing import Any

from ..confirm_util import confirm_or_exit
from ..protocol import ZenTaoClient


def my_bugs(client: ZenTaoClient) -> list[dict[str, Any]]:
    return client.my_bugs()


def create_bug(
    client: ZenTaoClient,
    product_id: str | int,
    body: dict[str, Any],
    *,
    yes: bool = False,
) -> dict[str, Any]:
    confirm_or_exit(f"Create bug under product {product_id}?", yes=yes)
    return client.create_bug(product_id, body)


def update_bug(
    client: ZenTaoClient,
    bug_id: str | int,
    body: dict[str, Any],
    *,
    yes: bool = False,
) -> dict[str, Any]:
    confirm_or_exit(f"Update bug {bug_id}?", yes=yes)
    return client.update_bug(bug_id, body)


def delete_bug(client: ZenTaoClient, bug_id: str | int, *, yes: bool = False) -> dict[str, Any]:
    confirm_or_exit(f"Delete bug {bug_id}? This cannot be undone easily.", yes=yes)
    return client.delete_bug(bug_id)


def bug_action(
    client: ZenTaoClient,
    action: str,
    bug_id: str | int,
    body: dict[str, Any] | None = None,
    *,
    yes: bool = False,
) -> dict[str, Any]:
    confirm_or_exit(f"Bug {action} id={bug_id}?", yes=yes)
    return client.bug_action(bug_id, action, body or {})
