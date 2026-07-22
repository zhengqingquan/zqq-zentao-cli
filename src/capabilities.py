#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Backend capability matrix and selection."""

from __future__ import annotations

from typing import Literal

from .config import Backend, env_backend, resolve_token
from .rest.resources import capability_names
from .web.my_pages import MY_PAGES

BackendName = Literal["web", "rest"]

CAPABILITIES: dict[str, frozenset[BackendName]] = {
    "whoami": frozenset({"web", "rest"}),
    "tasks": frozenset({"web", "rest"}),
    "tasks.list": frozenset({"rest"}),
    "task": frozenset({"web", "rest"}),
    "task.write": frozenset({"rest"}),
    "bug": frozenset({"rest"}),
    "bug.write": frozenset({"rest"}),
    "story": frozenset({"rest"}),
    "story.write": frozenset({"rest"}),
    "comment.list": frozenset({"web"}),
    "comment.add": frozenset({"web"}),
    "comment.edit": frozenset({"web"}),
    # Non-default my-* type/scope always Web PATHINFO.
    "my-page": frozenset({"web"}),
}

# my-* pages: web; my-tasks default also rest (selected via uses_rest_default in CLI).
for _page in MY_PAGES.values():
    if _page.rest_default:
        CAPABILITIES[_page.cmd] = frozenset({"web", "rest"})
    else:
        CAPABILITIES[_page.cmd] = frozenset({"web"})

for _cap in capability_names():
    CAPABILITIES.setdefault(_cap, frozenset({"rest"}))


def prefer_backend() -> BackendName:
    """For auto: prefer rest when a token is set, otherwise web."""
    return "rest" if resolve_token() else "web"


def resolve_backend(
    capability: str,
    *,
    cli_backend: str | None = None,
) -> BackendName:
    """
    Resolve the final backend.
    Priority: --backend > ZENTAO_BACKEND > auto heuristics.
    """
    supported = CAPABILITIES.get(capability)
    if not supported:
        raise SystemExit(f"Unknown capability: {capability}")

    if cli_backend:
        chosen: Backend | str = cli_backend.strip().lower()
    else:
        chosen = env_backend()

    if chosen == "auto":
        if supported == frozenset({"web"}):
            return "web"
        if supported == frozenset({"rest"}):
            return "rest"
        return prefer_backend()

    if chosen not in ("web", "rest"):
        raise SystemExit(f"Invalid backend={chosen!r}, expected web|rest|auto")

    if chosen not in supported:
        others = ", ".join(sorted(supported))
        raise SystemExit(
            f"Capability {capability} does not support backend={chosen} "
            f"(available: {others}). "
            f"Use --backend {next(iter(sorted(supported)))} or another command."
        )
    return chosen  # type: ignore[return-value]
