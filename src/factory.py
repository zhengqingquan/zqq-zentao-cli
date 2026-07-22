#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Create a client for the selected backend."""

from __future__ import annotations

from .capabilities import BackendName, resolve_backend
from .config import resolve_insecure, resolve_timeout_seconds
from .protocol import ZenTaoClient
from .rest import RestClient
from .web import WebClient


def create_client(
    capability: str,
    *,
    cli_backend: str | None = None,
    insecure: bool | None = None,
    timeout_ms: int | None = None,
) -> ZenTaoClient:
    backend: BackendName = resolve_backend(capability, cli_backend=cli_backend)
    skip_tls = resolve_insecure(insecure)
    timeout = resolve_timeout_seconds(timeout_ms)
    if backend == "rest":
        return RestClient(insecure=skip_tls, timeout=timeout)
    return WebClient(insecure=skip_tls, timeout=timeout)
