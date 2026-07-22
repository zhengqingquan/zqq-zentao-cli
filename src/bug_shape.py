#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Canonical bug row shape shared by web (and future REST) backends."""

from __future__ import annotations

from typing import Any

from .task_shape import user_field


def summarize_bug(row: dict[str, Any]) -> dict[str, Any]:
    """Map a raw bug dict (REST JSON or web dtable) to the CLI table/JSON shape."""
    assigned = row.get("assignedTo")
    opened = row.get("openedBy")
    resolved = row.get("resolvedBy")
    product = row.get("product")
    return {
        "id": row.get("id"),
        "title": row.get("title") or row.get("name"),
        "status": row.get("status") or row.get("rawStatus"),
        "severity": row.get("severity"),
        "pri": row.get("pri"),
        "assignedTo": user_field(assigned) if isinstance(assigned, dict) else assigned,
        "assignedToRealName": (
            assigned.get("realname")
            if isinstance(assigned, dict)
            else row.get("assignedToRealName")
        ),
        "openedBy": user_field(opened) if isinstance(opened, dict) else opened,
        "openedDate": row.get("openedDate"),
        "resolvedBy": user_field(resolved) if isinstance(resolved, dict) else resolved,
        "resolution": row.get("resolution"),
        "confirmed": row.get("confirmed"),
        "product": product.get("id") if isinstance(product, dict) else product,
        "productName": (
            product.get("name")
            if isinstance(product, dict)
            else row.get("productName")
        ),
        "type": row.get("type"),
    }
