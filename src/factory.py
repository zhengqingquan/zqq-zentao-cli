#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Create a client for the selected backend."""

from __future__ import annotations

from .capabilities import BackendName, resolve_backend
from .config import resolve_api, resolve_insecure, resolve_timeout_seconds
from .protocol import ZenTaoClient
from .rest import RestClient
from .web import WebClient


def create_client(
    capability: str,
    *,
    cli_backend: str | None = None,
    cli_api: str | None = None,
    insecure: bool | None = None,
    timeout_ms: int | None = None,
) -> ZenTaoClient:
    backend: BackendName = resolve_backend(capability, cli_backend=cli_backend)
    skip_tls = resolve_insecure(insecure)
    timeout = resolve_timeout_seconds(timeout_ms)
    if backend == "rest":
        # Writes always use APIv1 session inside RestClient._write_sess.
        # For write capabilities, also keep read session on v1 for consistency.
        api = resolve_api(cli_api)
        if capability.endswith(".write"):
            api = "v1"
        return RestClient(insecure=skip_tls, timeout=timeout, api_version=api)
    return WebClient(insecure=skip_tls, timeout=timeout)
