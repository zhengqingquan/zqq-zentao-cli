#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Create a client for the selected backend."""

from __future__ import annotations

from .capabilities import BackendName, resolve_backend
from .protocol import ZenTaoClient
from .rest import RestClient
from .web import WebClient


def create_client(
    capability: str,
    *,
    cli_backend: str | None = None,
) -> ZenTaoClient:
    backend: BackendName = resolve_backend(capability, cli_backend=cli_backend)
    if backend == "rest":
        return RestClient()
    return WebClient()
