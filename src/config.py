#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared config: server, account, password, token, backend."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Literal

CONFIG_PATH = Path.home() / ".config" / "zentao" / "zentao.json"
USER_AGENT = "zentao-operator/0.3 (+python; web+rest)"

Backend = Literal["web", "rest", "auto"]


def md5_hex(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def load_profile() -> dict[str, str]:
    server = (os.environ.get("ZENTAO_SERVER") or os.environ.get("ZENTAO_URL") or "").rstrip("/")
    account = os.environ.get("ZENTAO_ACCOUNT") or ""
    if server and account:
        return {"server": server, "account": account}

    if not CONFIG_PATH.is_file():
        raise SystemExit(
            f"Config not found. Set ZENTAO_SERVER + ZENTAO_ACCOUNT, or create {CONFIG_PATH}"
        )
    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    key = cfg.get("currentProfile")
    profiles = cfg.get("profiles") or {}

    profile = None
    if isinstance(profiles, dict):
        profile = profiles.get(key) if key else None
        if not profile and key:
            for p in profiles.values():
                if f"{p.get('account')}@{p.get('server')}" == key:
                    profile = p
                    break
        if not profile:
            profile = next(iter(profiles.values()), None)
    elif isinstance(profiles, list):
        if key:
            for p in profiles:
                if not isinstance(p, dict):
                    continue
                if f"{p.get('account')}@{p.get('server')}" == key:
                    profile = p
                    break
                if p.get("account") == key or p.get("server") == key:
                    profile = p
                    break
        if not profile:
            profile = next((p for p in profiles if isinstance(p, dict)), None)

    if not profile or not profile.get("server") or not profile.get("account"):
        raise SystemExit("profile missing server/account")
    return {
        "server": str(profile["server"]).rstrip("/"),
        "account": os.environ.get("ZENTAO_ACCOUNT") or str(profile["account"]),
    }


def resolve_password() -> str:
    pwd = os.environ.get("ZENTAO_PASSWORD") or ""
    if not pwd:
        raise SystemExit("Set env ZENTAO_PASSWORD (password is not stored on disk)")
    return pwd


def resolve_token() -> str:
    """Optional: use an existing REST token."""
    return (os.environ.get("ZENTAO_TOKEN") or "").strip()


def env_backend() -> Backend:
    raw = (os.environ.get("ZENTAO_BACKEND") or "auto").strip().lower()
    if raw in ("web", "rest", "auto"):
        return raw  # type: ignore[return-value]
    raise SystemExit(f"Invalid ZENTAO_BACKEND={raw!r}, expected web|rest|auto")


def insecure_ssl() -> bool:
    return os.environ.get("ZENTAO_INSECURE", "1") != "0"
