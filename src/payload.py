#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build JSON bodies for REST write commands (--data + field flags)."""

from __future__ import annotations

import json
from typing import Any


def parse_data_json(raw: str | None) -> dict[str, Any]:
    if raw is None or str(raw).strip() == "":
        return {}
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError as e:
        raise SystemExit(f"Invalid --data JSON: {e}") from e
    if not isinstance(obj, dict):
        raise SystemExit("--data must be a JSON object")
    return obj


def merge_payload(
    *,
    data_json: str | None = None,
    fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Merge --data JSON with explicit field flags (flags win)."""
    body = parse_data_json(data_json)
    for key, val in (fields or {}).items():
        if val is None:
            continue
        if isinstance(val, str) and val == "":
            continue
        body[key] = val
    return body


def drop_none(d: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}
