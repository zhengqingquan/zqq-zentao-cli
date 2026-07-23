#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Resolve ZenTao account from account / realname (client-side user scan)."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

ListUsersFn = Callable[..., dict[str, Any]]

# (server, account) → (monotonic_ts, rows)
_USER_CACHE: dict[tuple[str, str], tuple[float, list[dict[str, Any]]]] = {}
_USER_CACHE_TTL_SEC = 60.0


def clear_user_cache() -> None:
    """Drop all cached user tables (tests / forced refresh)."""
    _USER_CACHE.clear()


def _cache_key_for(list_users: ListUsersFn) -> tuple[str, str] | None:
    owner = getattr(list_users, "__self__", None)
    if owner is None:
        return None
    profile = getattr(owner, "profile", None)
    if isinstance(profile, dict):
        server = str(profile.get("server") or "").strip()
        account = str(profile.get("account") or "").strip()
        if server and account:
            return server, account
    server = str(getattr(owner, "server", "") or "").strip()
    account = str(getattr(owner, "account", "") or "").strip()
    if server and account:
        return server, account
    return None


def _user_fields(row: dict[str, Any]) -> tuple[str, str, str]:
    account = str(row.get("account") or "").strip()
    realname = str(row.get("realname") or "").strip()
    pinyin = str(row.get("pinyin") or "").strip()
    return account, realname, pinyin


def fetch_all_users(
    list_users: ListUsersFn,
    *,
    page_size: int = 200,
    ttl: float = _USER_CACHE_TTL_SEC,
) -> list[dict[str, Any]]:
    """Paginate GET /users until exhausted (short TTL cache per server+account)."""
    key = _cache_key_for(list_users)
    if key is not None and ttl > 0:
        hit = _USER_CACHE.get(key)
        if hit is not None:
            ts, rows = hit
            if (time.monotonic() - ts) < ttl:
                return list(rows)

    all_rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    cur = 1
    reported_total = 0
    while cur <= 100:
        data = list_users(page=cur, limit=page_size)
        rows = [r for r in (data.get("users") or []) if isinstance(r, dict)]
        reported_total = int(data.get("total") or reported_total or len(rows))
        if not rows:
            break
        for row in rows:
            account, _, _ = _user_fields(row)
            ukey = account or str(row.get("id") or id(row))
            if ukey in seen:
                continue
            seen.add(ukey)
            all_rows.append(row)
        if reported_total and len(all_rows) >= reported_total:
            break
        if len(rows) < page_size:
            break
        cur += 1

    if key is not None and ttl > 0:
        _USER_CACHE[key] = (time.monotonic(), list(all_rows))
    return all_rows


def search_users(list_users: ListUsersFn, q: str) -> list[dict[str, Any]]:
    """Match users by account / realname / pinyin substring (case-insensitive)."""
    needle = (q or "").strip().lower()
    if not needle:
        return []
    hits: list[dict[str, Any]] = []
    for row in fetch_all_users(list_users):
        account, realname, pinyin = _user_fields(row)
        hay = " ".join((account, realname, pinyin)).lower()
        if needle in hay:
            hits.append(row)
    return hits


def resolve_account(list_users: ListUsersFn, token: str) -> str:
    """Map account or realname token to a single account.

    - Exact account match wins.
    - Otherwise fuzzy unique match on account/realname/pinyin.
    - Zero or multiple fuzzy hits → SystemExit with candidates.
    """
    raw = (token or "").strip()
    if not raw:
        raise SystemExit("Empty user token (expected account or realname)")

    users = fetch_all_users(list_users)
    for row in users:
        account, _, _ = _user_fields(row)
        if account == raw:
            return account

    needle = raw.lower()
    hits: list[dict[str, Any]] = []
    for row in users:
        account, realname, pinyin = _user_fields(row)
        hay = " ".join((account, realname, pinyin)).lower()
        if needle in hay:
            hits.append(row)

    if len(hits) == 1:
        account, _, _ = _user_fields(hits[0])
        if not account:
            raise SystemExit(f"Matched user has empty account for {raw!r}")
        return account

    if not hits:
        raise SystemExit(
            f"No user matching {raw!r} (tried account / realname / pinyin). "
            "Use: users --search <name>"
        )

    lines = []
    for row in hits[:20]:
        account, realname, _ = _user_fields(row)
        label = f"{account} ({realname})" if realname else account
        lines.append(f"  - {label}")
    more = "" if len(hits) <= 20 else f"\n  … and {len(hits) - 20} more"
    raise SystemExit(
        f"Ambiguous user {raw!r} ({len(hits)} matches); use an account:\n"
        + "\n".join(lines)
        + more
    )


def resolve_optional(list_users: ListUsersFn, token: str | None) -> str | None:
    """Resolve non-empty token; blank/None stays None."""
    if token is None:
        return None
    s = str(token).strip()
    if not s:
        return None
    return resolve_account(list_users, s)
