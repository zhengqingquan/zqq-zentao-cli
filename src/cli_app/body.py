# -*- coding: utf-8 -*-
"""Write-flag payload helpers."""

from __future__ import annotations

import argparse

from ..payload import merge_payload


def is_id_token(token: str | None) -> bool:
    return bool(token) and str(token).isdigit()


def body_from_args(args: argparse.Namespace, *, extra: dict | None = None) -> dict:
    fields = {
        "comment": getattr(args, "comment", None),
        "assignedTo": getattr(args, "assignedTo", None),
        "title": getattr(args, "title", None),
        "name": getattr(args, "name", None),
        "pri": getattr(args, "pri", None),
        "severity": getattr(args, "severity", None),
        "type": getattr(args, "obj_type", None),
        "resolution": getattr(args, "resolution", None),
        "openedBuild": getattr(args, "openedBuild", None),
        "spec": getattr(args, "spec", None),
        "verify": getattr(args, "verify", None),
        "category": getattr(args, "category", None),
        "closedReason": getattr(args, "closedReason", None),
        "result": getattr(args, "result", None),
        "estStarted": getattr(args, "estStarted", None),
        "deadline": getattr(args, "deadline", None),
        "consumed": getattr(args, "consumed", None),
        "left": getattr(args, "left", None),
        "currentConsumed": getattr(args, "currentConsumed", None),
        "finishedDate": getattr(args, "finishedDate", None),
        "realStarted": getattr(args, "realStarted", None),
    }
    if extra:
        fields.update(extra)
    return merge_payload(data_json=getattr(args, "data", None), fields=fields)
