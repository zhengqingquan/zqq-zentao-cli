#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Create a client for the selected backend."""

from __future__ import annotations

import sys
from typing import Any

from .capabilities import BackendName, CAPABILITIES, resolve_backend
from .config import env_backend, resolve_api, resolve_insecure, resolve_timeout_seconds
from .protocol import ZenTaoClient
from .rest import RestClient
from .web import WebClient


def _make_client(
    backend: BackendName,
    *,
    skip_tls: bool,
    timeout: float,
    api: str,
    capability: str,
) -> ZenTaoClient:
    if backend == "rest":
        # Writes always use APIv1 session inside RestClient._write_sess.
        use_api = "v1" if capability.endswith(".write") else api
        return RestClient(insecure=skip_tls, timeout=timeout, api_version=use_api)
    return WebClient(insecure=skip_tls, timeout=timeout)


def _is_auto_choice(cli_backend: str | None) -> bool:
    if cli_backend is not None and cli_backend.strip():
        return cli_backend.strip().lower() == "auto"
    return env_backend() == "auto"


def _retriable_failure(exc: BaseException) -> bool:
    msg = str(exc).lower()
    needles = (
        "not logged in",
        "auth fail",
        "login",
        "token",
        "cookie",
        "timed out",
        "timeout",
        "connection",
        "temporarily unavailable",
        "access not allowed",
        "http 401",
        "http 403",
        "http 502",
        "http 503",
        "http 504",
    )
    return any(n in msg for n in needles)


class _FallbackClient:
    """Proxy: on retriable SystemExit from primary, try secondary once (auto only)."""

    def __init__(
        self,
        primary: ZenTaoClient,
        secondary: ZenTaoClient,
        *,
        capability: str,
    ):
        self._primary = primary
        self._secondary = secondary
        self._capability = capability
        self._active = primary
        self.backend = getattr(primary, "backend", "rest")

    def __getattr__(self, name: str) -> Any:
        attr = getattr(self._active, name)
        if not callable(attr):
            return attr

        def wrapped(*args: Any, **kwargs: Any) -> Any:
            try:
                return attr(*args, **kwargs)
            except SystemExit as e:
                if self._active is self._secondary or not _retriable_failure(e):
                    raise
                other = self._secondary
                other_name = getattr(other, "backend", "?")
                primary_name = getattr(self._primary, "backend", "?")
                print(
                    f"warn: {primary_name} failed for {self._capability} "
                    f"({e}); trying {other_name}",
                    file=sys.stderr,
                )
                self._active = other
                self.backend = other_name
                return getattr(other, name)(*args, **kwargs)

        return wrapped


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
    api = resolve_api(cli_api)

    primary = _make_client(
        backend,
        skip_tls=skip_tls,
        timeout=timeout,
        api=api,
        capability=capability,
    )

    supported = CAPABILITIES.get(capability) or frozenset()
    if (
        _is_auto_choice(cli_backend)
        and len(supported) > 1
        and not capability.endswith(".write")
    ):
        other: BackendName = "web" if backend == "rest" else "rest"
        if other in supported:
            secondary = _make_client(
                other,
                skip_tls=skip_tls,
                timeout=timeout,
                api=api,
                capability=capability,
            )
            return _FallbackClient(primary, secondary, capability=capability)  # type: ignore[return-value]

    return primary
