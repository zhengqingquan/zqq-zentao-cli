#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Explicit login: Web cookies + REST token into ~/.config/zentao/zentao.json."""

from __future__ import annotations

import sys
from typing import Any

from ..config import (
    Backend,
    env_account,
    env_backend,
    env_server,
    resolve_insecure,
    resolve_timeout_seconds,
    save_profile_credentials,
    try_resolve_password,
)
from ..rest.session import RestSession
from ..web.session import Session


def resolve_login_args(
    *,
    server: str | None,
    account: str | None,
    password: str | None,
) -> tuple[str, str, str]:
    srv = (server or env_server() or "").rstrip("/")
    acc = (account or env_account() or "").strip()
    pwd = (password if password is not None else try_resolve_password()) or ""
    missing: list[str] = []
    if not srv:
        missing.append("-s/--server or ZENTAO_SERVER/ZENTAO_URL")
    if not acc:
        missing.append("-u/--account or ZENTAO_ACCOUNT")
    if not pwd:
        missing.append("-p/--password or ZENTAO_PASSWORD")
    if missing:
        raise SystemExit("login requires: " + "; ".join(missing))
    return srv, acc, pwd


def do_login(
    *,
    server: str | None = None,
    account: str | None = None,
    password: str | None = None,
    backend: str | None = None,
    insecure: bool | None = None,
    timeout_ms: int | None = None,
) -> dict[str, Any]:
    srv, acc, pwd = resolve_login_args(server=server, account=account, password=password)
    chosen: Backend | str = (backend or env_backend() or "auto").strip().lower()
    if chosen not in ("web", "rest", "auto"):
        raise SystemExit(f"Invalid backend={chosen!r}, expected web|rest|auto")

    skip_tls = resolve_insecure(insecure)
    timeout = resolve_timeout_seconds(timeout_ms)
    did_web = False
    did_rest = False

    if chosen in ("web", "auto"):
        sess = Session(srv, insecure=skip_tls, timeout=timeout)
        sess.login(acc, pwd)
        save_profile_credentials(srv, acc, cookies=dict(sess.cookies))
        did_web = True

    if chosen in ("rest", "auto"):
        rest = RestSession(srv, insecure=skip_tls, account=acc, timeout=timeout)
        token = rest.login(acc, pwd, force_password=True, prefer_stored=False)
        save_profile_credentials(srv, acc, token=token)
        did_rest = True

    parts: list[str] = []
    if did_web:
        parts.append("webCookies")
    if did_rest:
        parts.append("token")
    print(
        f"login ok: account={acc} server={srv} saved={','.join(parts)} insecure={skip_tls}",
        file=sys.stderr,
    )
    return {
        "account": acc,
        "server": srv,
        "savedWebCookies": did_web,
        "savedToken": did_rest,
        "backend": chosen,
        "insecure": skip_tls,
    }
