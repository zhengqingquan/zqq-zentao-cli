#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Testcase write operations via ZenTaoClient."""

from __future__ import annotations

from typing import Any

from ..confirm_util import confirm_or_exit
from ..protocol import ZenTaoClient


def create_testcase(
    client: ZenTaoClient,
    product_id: str | int,
    body: dict[str, Any],
    *,
    yes: bool = False,
) -> dict[str, Any]:
    confirm_or_exit(f"Create testcase under product {product_id}?", yes=yes)
    return client.create_testcase(product_id, body)


def update_testcase(
    client: ZenTaoClient,
    case_id: str | int,
    body: dict[str, Any],
    *,
    yes: bool = False,
) -> dict[str, Any]:
    confirm_or_exit(f"Update testcase {case_id}?", yes=yes)
    return client.update_testcase(case_id, body)


def delete_testcase(
    client: ZenTaoClient, case_id: str | int, *, yes: bool = False
) -> dict[str, Any]:
    confirm_or_exit(
        f"Delete testcase {case_id}? This cannot be undone easily.", yes=yes
    )
    return client.delete_testcase(case_id)


def testcase_action(
    client: ZenTaoClient,
    action: str,
    case_id: str | int,
    body: dict[str, Any] | None = None,
    *,
    yes: bool = False,
) -> dict[str, Any]:
    confirm_or_exit(f"Testcase {action} id={case_id}?", yes=yes)
    return client.testcase_action(case_id, action, body or {})
