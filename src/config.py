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

USER_AGENT = "zentao-operator/0.3 (+python; web+rest)"
LOGIN_HINT = "Run: zqq-zentao login -s <url> -u <account> -p <password>"
DEFAULT_TIMEOUT_MS = 60_000

Backend = Literal["web", "rest", "auto"]
ApiVersion = Literal["v1", "v2"]

_config_path_override: Path | None = None


def default_config_path() -> Path:
    return Path.home() / ".config" / "zentao" / "zentao.json"


def get_config_path() -> Path:
    """Active config file: --config / ZENTAO_CONFIG_FILE / ~/.config/zentao/zentao.json."""
    if _config_path_override is not None:
        return _config_path_override
    env = (os.environ.get("ZENTAO_CONFIG_FILE") or "").strip()
    if env:
        return _expand_config_path(env)
    return default_config_path()


def set_config_path(path: str) -> Path:
    """Set config path from CLI --config (absolute or ~-expanded)."""
    global _config_path_override
    if not isinstance(path, str) or not path.strip():
        raise SystemExit("--config path must be a non-empty string")
    resolved = _expand_config_path(path.strip())
    _config_path_override = resolved
    return resolved


def _expand_config_path(path: str) -> Path:
    p = Path(path).expanduser()
    if not p.is_absolute():
        p = Path.cwd() / p
    return p.resolve()


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
    if not get_config_path().is_file():
        return {"profiles": [], "currentProfile": None}
    try:
        data = json.loads(get_config_path().read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SystemExit(f"Invalid config JSON at {get_config_path()}: {e}") from e
    if not isinstance(data, dict):
        raise SystemExit(f"Invalid config root at {get_config_path()}")
    return data


def _write_cfg(cfg: dict[str, Any]) -> None:
    get_config_path().parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(cfg, ensure_ascii=False, indent="\t") + "\n"
    fd, tmp_name = tempfile.mkstemp(
        dir=str(get_config_path().parent),
        prefix=".zentao-",
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        Path(tmp_name).replace(get_config_path())
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

    if get_config_path().is_file():
        cfg = _read_cfg()
        matched = _find_profile(cfg, server=server or None, account=account or None)
        if matched and matched.get("server") and matched.get("account"):
            return {
                "server": (server or str(matched["server"])).rstrip("/"),
                "account": account or str(matched["account"]),
            }

    if server and account:
        return {"server": server, "account": account}

    if not get_config_path().is_file():
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
    if not get_config_path().is_file():
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
    if not get_config_path().is_file():
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
    cfg = _read_cfg() if get_config_path().is_file() else {"profiles": [], "currentProfile": None}
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
    if not get_config_path().is_file():
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


def env_api() -> ApiVersion:
    """REST API version for reads. Default v1. Writes always use v1."""
    raw = (os.environ.get("ZENTAO_API") or "v1").strip().lower()
    if raw in ("v1", "v2"):
        return raw  # type: ignore[return-value]
    raise SystemExit(f"Invalid ZENTAO_API={raw!r}, expected v1|v2")


def resolve_api(cli_api: str | None = None) -> ApiVersion:
    """Priority: CLI --api > ZENTAO_API (default v1)."""
    if cli_api:
        raw = cli_api.strip().lower()
        if raw not in ("v1", "v2"):
            raise SystemExit(f"Invalid --api={cli_api!r}, expected v1|v2")
        return raw  # type: ignore[return-value]
    return env_api()


def insecure_ssl() -> bool:
    """True = skip TLS verify. Default ZENTAO_INSECURE=1 (skip)."""
    return os.environ.get("ZENTAO_INSECURE", "1") != "0"


def resolve_insecure(cli_insecure: bool | None = None) -> bool:
    """
    Resolve whether to skip TLS verification.
    Priority: CLI --insecure/--secure > ZENTAO_INSECURE (default skip).
    cli_insecure: True=skip, False=verify, None=use env.
    """
    if cli_insecure is not None:
        return bool(cli_insecure)
    return insecure_ssl()


def resolve_timeout_seconds(cli_timeout_ms: int | None = None) -> float:
    """
    Request timeout in seconds for urllib.
    Priority: CLI --timeout <ms> > default 60000ms (aligned unit with official zentao-cli).
    """
    if cli_timeout_ms is None:
        return DEFAULT_TIMEOUT_MS / 1000.0
    if cli_timeout_ms <= 0:
        raise SystemExit("--timeout must be a positive integer (milliseconds)")
    return cli_timeout_ms / 1000.0
