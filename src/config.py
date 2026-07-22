#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared config: server, account, password, token, backend, webCookies."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

CONFIG_PATH = Path.home() / ".config" / "zentao" / "zentao.json"
USER_AGENT = "zentao-operator/0.3 (+python; web+rest)"
LOGIN_HINT = "Run: zqq-zentao login -s <url> -u <account> -p <password>"

Backend = Literal["web", "rest", "auto"]


def md5_hex(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def env_server() -> str:
    return (os.environ.get("ZENTAO_SERVER") or os.environ.get("ZENTAO_URL") or "").rstrip("/")


def env_account() -> str:
    return (os.environ.get("ZENTAO_ACCOUNT") or "").strip()


def try_resolve_password() -> str:
    return (os.environ.get("ZENTAO_PASSWORD") or "").strip()


def resolve_password() -> str:
    pwd = try_resolve_password()
    if not pwd:
        raise SystemExit(f"Password required. Set ZENTAO_PASSWORD, or {LOGIN_HINT}")
    return pwd


def profile_key(server: str, account: str) -> str:
    return f"{account}@{server.rstrip('/')}"


def cookies_look_valid(cookies: dict[str, str] | None) -> bool:
    if not cookies:
        return False
    if not cookies.get("zentaosid"):
        return False
    return bool(cookies.get("za") or cookies.get("zp") or cookies.get("keepLogin"))


def _read_cfg() -> dict[str, Any]:
    if not CONFIG_PATH.is_file():
        return {"profiles": [], "currentProfile": None}
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SystemExit(f"Invalid config JSON at {CONFIG_PATH}: {e}") from e
    if not isinstance(data, dict):
        raise SystemExit(f"Invalid config root at {CONFIG_PATH}")
    return data


def _write_cfg(cfg: dict[str, Any]) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(cfg, ensure_ascii=False, indent="\t") + "\n"
    fd, tmp_name = tempfile.mkstemp(
        dir=str(CONFIG_PATH.parent),
        prefix=".zentao-",
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        Path(tmp_name).replace(CONFIG_PATH)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def _iter_profiles(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    profiles = cfg.get("profiles") or []
    if isinstance(profiles, dict):
        return [p for p in profiles.values() if isinstance(p, dict)]
    if isinstance(profiles, list):
        return [p for p in profiles if isinstance(p, dict)]
    return []


def _find_profile(
    cfg: dict[str, Any],
    *,
    server: str | None = None,
    account: str | None = None,
) -> dict[str, Any] | None:
    profiles = cfg.get("profiles") or []
    key = cfg.get("currentProfile")

    if server and account:
        want = profile_key(server, account)
        for p in _iter_profiles(cfg):
            if profile_key(str(p.get("server") or ""), str(p.get("account") or "")) == want:
                return p
            if str(p.get("server") or "").rstrip("/") == server.rstrip("/") and str(
                p.get("account") or ""
            ) == account:
                return p

    if isinstance(profiles, dict):
        profile = profiles.get(key) if key else None
        if isinstance(profile, dict):
            return profile
        if key:
            for p in profiles.values():
                if not isinstance(p, dict):
                    continue
                if f"{p.get('account')}@{p.get('server')}" == key:
                    return p
        return next((p for p in profiles.values() if isinstance(p, dict)), None)

    if isinstance(profiles, list):
        if key:
            for p in profiles:
                if not isinstance(p, dict):
                    continue
                if f"{p.get('account')}@{p.get('server')}" == key:
                    return p
                if p.get("account") == key or p.get("server") == key:
                    return p
        return next((p for p in profiles if isinstance(p, dict)), None)

    return None


def load_profile() -> dict[str, str]:
    server = env_server()
    account = env_account()

    if CONFIG_PATH.is_file():
        cfg = _read_cfg()
        matched = _find_profile(cfg, server=server or None, account=account or None)
        if matched and matched.get("server") and matched.get("account"):
            return {
                "server": (server or str(matched["server"])).rstrip("/"),
                "account": account or str(matched["account"]),
            }

    if server and account:
        return {"server": server, "account": account}

    if not CONFIG_PATH.is_file():
        raise SystemExit(
            f"Config not found. {LOGIN_HINT}, or set ZENTAO_SERVER/ZENTAO_URL + ZENTAO_ACCOUNT"
        )

    cfg = _read_cfg()
    profile = _find_profile(cfg)
    if not profile or not profile.get("server") or not profile.get("account"):
        raise SystemExit(f"profile missing server/account. {LOGIN_HINT}")
    return {
        "server": str(profile["server"]).rstrip("/"),
        "account": account or str(profile["account"]),
    }


def load_web_cookies(
    *,
    server: str | None = None,
    account: str | None = None,
) -> dict[str, str]:
    if not CONFIG_PATH.is_file():
        return {}
    cfg = _read_cfg()
    profile = _find_profile(cfg, server=server, account=account)
    if not profile:
        return {}
    raw = profile.get("webCookies")
    if not isinstance(raw, dict):
        return {}
    return {str(k): str(v) for k, v in raw.items() if v is not None}


def load_stored_token(
    *,
    server: str | None = None,
    account: str | None = None,
) -> str:
    if not CONFIG_PATH.is_file():
        return ""
    cfg = _read_cfg()
    profile = _find_profile(cfg, server=server, account=account)
    if not profile:
        return ""
    return str(profile.get("token") or "").strip()


def resolve_token(
    *,
    server: str | None = None,
    account: str | None = None,
) -> str:
    """Env ZENTAO_TOKEN first, then profile token from zentao.json."""
    env = (os.environ.get("ZENTAO_TOKEN") or "").strip()
    if env:
        return env
    if server is None or account is None:
        try:
            profile = load_profile()
            server = server or profile["server"]
            account = account or profile["account"]
        except SystemExit:
            return ""
    return load_stored_token(server=server, account=account)


def save_profile_credentials(
    server: str,
    account: str,
    *,
    cookies: dict[str, str] | None = None,
    token: str | None = None,
) -> None:
    server = server.rstrip("/")
    cfg = _read_cfg() if CONFIG_PATH.is_file() else {"profiles": [], "currentProfile": None}
    profiles = cfg.get("profiles")
    key = profile_key(server, account)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

    if isinstance(profiles, dict):
        profile = None
        store_key = None
        if key in profiles and isinstance(profiles[key], dict):
            profile = profiles[key]
            store_key = key
        else:
            for k, p in profiles.items():
                if not isinstance(p, dict):
                    continue
                if profile_key(str(p.get("server") or ""), str(p.get("account") or "")) == key:
                    profile = p
                    store_key = k
                    break
        if profile is None:
            profile = {"server": server, "account": account}
            store_key = key
            profiles[store_key] = profile
        profile["server"] = server
        profile["account"] = account
        if cookies is not None:
            profile["webCookies"] = dict(cookies)
            profile["webCookiesUpdatedAt"] = now
        if token is not None:
            profile["token"] = token
            profile["loginTime"] = now
            profile["lastUsedTime"] = now
        cfg["profiles"] = profiles
        cfg["currentProfile"] = key
    else:
        if not isinstance(profiles, list):
            profiles = []
        profile = None
        for p in profiles:
            if not isinstance(p, dict):
                continue
            if profile_key(str(p.get("server") or ""), str(p.get("account") or "")) == key:
                profile = p
                break
        if profile is None:
            profile = {"server": server, "account": account}
            profiles.append(profile)
        profile["server"] = server
        profile["account"] = account
        if cookies is not None:
            profile["webCookies"] = dict(cookies)
            profile["webCookiesUpdatedAt"] = now
        if token is not None:
            profile["token"] = token
            profile["loginTime"] = now
            profile["lastUsedTime"] = now
        cfg["profiles"] = profiles
        cfg["currentProfile"] = key

    _write_cfg(cfg)


def save_web_cookies(
    cookies: dict[str, str],
    *,
    server: str | None = None,
    account: str | None = None,
) -> None:
    profile = load_profile() if (server is None or account is None) else {
        "server": (server or "").rstrip("/"),
        "account": account or "",
    }
    save_profile_credentials(
        profile["server"],
        profile["account"],
        cookies=cookies,
    )


def clear_web_cookies(
    *,
    server: str | None = None,
    account: str | None = None,
) -> None:
    if not CONFIG_PATH.is_file():
        return
    profile = load_profile() if (server is None or account is None) else {
        "server": (server or "").rstrip("/"),
        "account": account or "",
    }
    cfg = _read_cfg()
    matched = _find_profile(cfg, server=profile["server"], account=profile["account"])
    if not matched:
        return
    matched.pop("webCookies", None)
    matched.pop("webCookiesUpdatedAt", None)
    _write_cfg(cfg)


def env_backend() -> Backend:
    raw = (os.environ.get("ZENTAO_BACKEND") or "auto").strip().lower()
    if raw in ("web", "rest", "auto"):
        return raw  # type: ignore[return-value]
    raise SystemExit(f"Invalid ZENTAO_BACKEND={raw!r}, expected web|rest|auto")


def insecure_ssl() -> bool:
    return os.environ.get("ZENTAO_INSECURE", "1") != "0"
