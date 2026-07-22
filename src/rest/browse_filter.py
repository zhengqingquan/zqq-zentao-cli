#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Map bugs/stories CLI filters onto ZenTao REST ``status`` (= browseType).

ZenTao 22.3 product/project/execution bug & story list APIs pass query
``status`` into browseType (not the row ``status`` field). Useful values:

- bugs: assigntome, openedbyme, unclosed, unresolved (=active), toclosed (=resolved), …
- stories: assignedtome, openedbyme, unclosed, activestory, closedstory, …

Arbitrary other-account ``assignedTo`` / ``openedBy`` still need client-side
full-list filter (no REST param). Prefer ``my-bugs`` / ``my-stories`` for self.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Kind = Literal["bugs", "stories"]
Mode = Literal["passthrough", "server_page", "server_then_client", "client_all"]

# From module/bug/config.php browseTypeList (subset safe for REST status=).
BUG_BROWSE_TYPES = frozenset(
    {
        "all",
        "assigntome",
        "openedbyme",
        "resolvedbyme",
        "assigntonull",
        "unconfirmed",
        "unresolved",
        "unclosed",
        "toclosed",
        "longlifebugs",
        "postponedbugs",
        "overduebugs",
        "assignedbyme",
        "needconfirm",
    }
)

# product::browse / projectstory browseType names (lower-case).
STORY_BROWSE_TYPES = frozenset(
    {
        "allstory",
        "unclosed",
        "assignedtome",
        "openedbyme",
        "reviewbyme",
        "draftstory",
        "reviewedbyme",
        "assignedbyme",
        "closedbyme",
        "activestory",
        "changingstory",
        "reviewingstory",
        "willclose",
        "closedstory",
        "all",
    }
)

# Row field status → browseType when filtering by status alone.
_BUG_FIELD_TO_BROWSE = {
    "active": "unresolved",
    "resolved": "toclosed",
}
_STORY_FIELD_TO_BROWSE = {
    "active": "activestory",
    "closed": "closedstory",
    "draft": "draftstory",
    "changing": "changingstory",
    "reviewing": "reviewingstory",
}


@dataclass(frozen=True)
class BrowseFilterPlan:
    """How to apply assignedTo/openedBy/status for bugs or stories lists."""

    mode: Mode
    server_status: str | None = None
    client_assigned_to: str | None = None
    client_opened_by: str | None = None
    client_status: str | None = None
    note: str | None = None  # stderr hint when client_all / partial


def _norm_account(value: str | None) -> str | None:
    s = (value or "").strip()
    return s or None


def _single_status(status: str | None) -> str | None:
    if status is None:
        return None
    parts = [p.strip() for p in str(status).split(",") if p.strip()]
    if len(parts) != 1:
        return None
    return parts[0]


def plan_bugs_stories_filter(
    kind: Kind,
    *,
    me: str,
    assigned_to: str | None = None,
    opened_by: str | None = None,
    status: str | None = None,
) -> BrowseFilterPlan:
    """Decide REST browseType query vs remaining client-side filters."""
    me_acc = _norm_account(me) or ""
    at = _norm_account(assigned_to)
    ob = _norm_account(opened_by)
    st = (status or "").strip() or None
    if not at and not ob and not st:
        return BrowseFilterPlan(mode="passthrough")

    browse_types = BUG_BROWSE_TYPES if kind == "bugs" else STORY_BROWSE_TYPES
    field_map = _BUG_FIELD_TO_BROWSE if kind == "bugs" else _STORY_FIELD_TO_BROWSE
    assign_browse = "assigntome" if kind == "bugs" else "assignedtome"
    opened_browse = "openedbyme"

    server_status: str | None = None
    client_at, client_ob, client_st = at, ob, st
    note: str | None = None

    # Self assignee / opener → server browseType (narrows list a lot).
    if at and at == me_acc and not ob:
        server_status = assign_browse
        client_at = None
        # Keep field --status as client filter on the smaller set.
    elif ob and ob == me_acc and not at:
        server_status = opened_browse
        client_ob = None
    elif at and at != me_acc:
        note = (
            f"{kind}: --assignedTo {at!r} is not the current user; "
            "REST has no per-account filter — fetching full scoped list then filtering locally "
            "(slow on large products). Prefer my-bugs/my-stories for self."
        )
    elif ob and ob != me_acc:
        note = (
            f"{kind}: --openedBy {ob!r} is not the current user; "
            "REST has no per-account filter — fetching full scoped list then filtering locally "
            "(slow on large products)."
        )

    # Status-only (or leftover status) → browseType when possible.
    if server_status is None and not at and not ob and st:
        one = _single_status(st)
        if one:
            low = one.lower()
            if low in browse_types:
                server_status = low
                client_st = None
            elif low in field_map:
                server_status = field_map[low]
                client_st = None
            elif kind == "bugs" and low == "closed":
                # No "closed-only" browseType; need all then client filter.
                server_status = "all"
                client_st = st
                note = (
                    "bugs: --status closed uses status=all then client filter "
                    "(no closed-only browseType)."
                )

    # Both at+ob set, or other-user filters: may still have no server_status.
    if server_status is None and (client_at or client_ob or client_st):
        return BrowseFilterPlan(
            mode="client_all",
            client_assigned_to=client_at,
            client_opened_by=client_ob,
            client_status=client_st,
            note=note,
        )

    if server_status and (client_at or client_ob or client_st):
        return BrowseFilterPlan(
            mode="server_then_client",
            server_status=server_status,
            client_assigned_to=client_at,
            client_opened_by=client_ob,
            client_status=client_st,
            note=note,
        )

    if server_status:
        return BrowseFilterPlan(
            mode="server_page",
            server_status=server_status,
            note=note,
        )

    return BrowseFilterPlan(mode="passthrough")
