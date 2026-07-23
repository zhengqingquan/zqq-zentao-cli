# -*- coding: utf-8 -*-
"""Aggregate list rows into counts / facets (offline-friendly)."""

from __future__ import annotations

from collections import Counter
from typing import Any, Iterable

from .list_filter import row_pri, row_status

_DEFAULT_FACETS = ("status", "pri")
_ALLOWED_FACETS = frozenset({"status", "pri", "assignedTo", "openedBy"})


def parse_facets(raw: str | None) -> tuple[str, ...]:
    """Parse ``--facet status,pri``; default status+pri."""
    if raw is None or not str(raw).strip():
        return _DEFAULT_FACETS
    parts = [p.strip() for p in str(raw).split(",") if p.strip()]
    if not parts:
        return _DEFAULT_FACETS
    bad = [p for p in parts if p not in _ALLOWED_FACETS]
    if bad:
        raise SystemExit(
            f"Unsupported --facet {bad[0]!r}; allowed: {', '.join(sorted(_ALLOWED_FACETS))}"
        )
    # Preserve order, drop dupes.
    seen: set[str] = set()
    out: list[str] = []
    for p in parts:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return tuple(out)


def _facet_value(row: dict[str, Any], facet: str) -> str:
    if facet == "status":
        val = row_status(row)
    elif facet == "pri":
        val = row_pri(row)
    elif facet in ("assignedTo", "openedBy"):
        from .list_filter import row_account

        val = row_account(row, facet)
    else:
        raw = row.get(facet)
        if isinstance(raw, dict):
            val = str(raw.get("account") or raw.get("name") or raw.get("code") or "")
        else:
            val = "" if raw is None else str(raw)
    return val.strip() or "(empty)"


def count_by_facet(rows: Iterable[dict[str, Any]], facet: str) -> dict[str, int]:
    """Count rows by one facet; keys sorted by count desc then label."""
    ctr: Counter[str] = Counter()
    for row in rows:
        if not isinstance(row, dict):
            continue
        ctr[_facet_value(row, facet)] += 1
    return dict(sorted(ctr.items(), key=lambda kv: (-kv[1], kv[0])))


def summarize_rows(
    rows: list[dict[str, Any]],
    *,
    facets: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Build ``{total, facets: {name: {value: count}}}`` from in-memory rows."""
    dict_rows = [r for r in rows if isinstance(r, dict)]
    facet_names = facets if facets is not None else _DEFAULT_FACETS
    return {
        "total": len(dict_rows),
        "facets": {name: count_by_facet(dict_rows, name) for name in facet_names},
    }


def as_count_only(
    payload: dict[str, Any],
    *,
    kind: str,
    list_key: str,
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Strip list rows; keep ``total`` (+ backend/api) for ``--count-only``."""
    total = payload.get("total")
    if total is None:
        rows = payload.get(list_key) or []
        total = len(rows) if isinstance(rows, list) else 0
    # Prefer server-built echo (resolved accounts) when present.
    echo = payload.get("resolvedFilters")
    if isinstance(echo, dict) and echo:
        clean_filters = dict(echo)
    else:
        clean_filters = {
            k: v
            for k, v in (filters or {}).items()
            if v is not None and str(v).strip() != ""
        }
    out: dict[str, Any] = {
        "kind": kind,
        "mode": "count-only",
        "total": int(total),
        "filters": clean_filters,
    }
    for meta in ("backend", "api", "searchMode", "browseType"):
        if meta in payload:
            out[meta] = payload[meta]
    return out


_USER_FILTER_KEYS = (
    "assignedTo",
    "openedBy",
    "finishedBy",
    "resolvedBy",
    "closedBy",
)


def build_filters_echo(
    *,
    scopes: dict[str, Any] | None = None,
    status: str | None = None,
    pri: str | None = None,
    user_inputs: dict[str, str | None] | None = None,
    user_resolved: dict[str, str | None] | None = None,
) -> dict[str, Any]:
    """Filters for stats output: resolved account + ``*Input`` when raw differs."""
    out: dict[str, Any] = {}
    for k, v in (scopes or {}).items():
        if v is not None and str(v).strip() != "":
            out[k] = v
    if status is not None and str(status).strip() != "":
        out["status"] = status
    if pri is not None and str(pri).strip() != "":
        out["pri"] = pri
    inputs = user_inputs or {}
    resolved = user_resolved or {}
    for key in _USER_FILTER_KEYS:
        raw = (inputs.get(key) or "").strip() or None
        acc = (resolved.get(key) or "").strip() or None
        if acc:
            out[key] = acc
            if raw and raw != acc:
                out[f"{key}Input"] = raw
        elif raw:
            out[key] = raw
    return out
