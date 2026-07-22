#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story write operations via ZenTaoClient."""

from __future__ import annotations

from typing import Any

from ..confirm_util import confirm_or_exit
from ..protocol import ZenTaoClient


def create_story(
    client: ZenTaoClient,
    product_id: str | int,
    body: dict[str, Any],
    *,
    yes: bool = False,
) -> dict[str, Any]:
    confirm_or_exit(f"Create story under product {product_id}?", yes=yes)
    return client.create_story(product_id, body)


def update_story(
    client: ZenTaoClient,
    story_id: str | int,
    body: dict[str, Any],
    *,
    yes: bool = False,
) -> dict[str, Any]:
    confirm_or_exit(f"Update story {story_id}?", yes=yes)
    return client.update_story(story_id, body)


def delete_story(
    client: ZenTaoClient, story_id: str | int, *, yes: bool = False
) -> dict[str, Any]:
    confirm_or_exit(f"Delete story {story_id}? This cannot be undone easily.", yes=yes)
    return client.delete_story(story_id)


def story_action(
    client: ZenTaoClient,
    action: str,
    story_id: str | int,
    body: dict[str, Any] | None = None,
    *,
    yes: bool = False,
) -> dict[str, Any]:
    confirm_or_exit(f"Story {action} id={story_id}?", yes=yes)
    return client.story_action(story_id, action, body or {})
