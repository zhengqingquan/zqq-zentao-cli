#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Testsuite write operations via ZenTaoClient."""

from __future__ import annotations

from typing import Any

from ..confirm_util import confirm_or_exit
from ..protocol import ZenTaoClient


def create_testsuite(
    client: ZenTaoClient,
    product_id: str | int,
    body: dict[str, Any],
    *,
    yes: bool = False,
) -> dict[str, Any]:
    confirm_or_exit(f"Create testsuite under product {product_id}?", yes=yes)
    return client.create_testsuite(product_id, body)


def update_testsuite(
    client: ZenTaoClient,
    suite_id: str | int,
    body: dict[str, Any],
    *,
    yes: bool = False,
) -> dict[str, Any]:
    raise SystemExit(
        "testsuite update is not exposed by ZenTao REST APIv1 "
        f"(id={suite_id}); body keys={sorted(body)!r}"
    )


def delete_testsuite(
    client: ZenTaoClient, suite_id: str | int, *, yes: bool = False
) -> dict[str, Any]:
    confirm_or_exit(
        f"Delete testsuite {suite_id}? This cannot be undone easily.", yes=yes
    )
    return client.delete_testsuite(suite_id)


def testsuite_action(
    client: ZenTaoClient,
    action: str,
    suite_id: str | int,
    body: dict[str, Any] | None = None,
    *,
    yes: bool = False,
) -> dict[str, Any]:
    raise SystemExit(
        f"Unknown testsuite action {action!r} id={suite_id}; "
        f"body keys={sorted(body or {})!r}"
    )
