#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task edit option lists (execution / module / parent), aligned with Web edit form."""

from __future__ import annotations

from typing import Any

from ..protocol import ZenTaoClient
from ..rest.client import RestClient
from ..task_shape import summarize_task


def _as_rest(client: ZenTaoClient) -> RestClient:
    if not isinstance(client, RestClient):
        raise SystemExit("task options requires --backend rest")
    return client


def _id_of(val: Any) -> int | None:
    if val is None or val == "" or val == "0" or val == 0:
        return None
    if isinstance(val, dict):
        raw = val.get("id")
    else:
        raw = val
    try:
        n = int(raw)
    except (TypeError, ValueError):
        return None
    return n if n > 0 else None


def _flatten_modules(nodes: Any, *, prefix: str = "") -> list[dict[str, Any]]:
    """Flatten REST module tree into id/name pairs for --module fill-in."""
    out: list[dict[str, Any]] = []
    if not nodes:
        return out
    if isinstance(nodes, dict):
        # Sometimes keyed by id.
        nodes = list(nodes.values())
    if not isinstance(nodes, list):
        return out
    for node in nodes:
        if not isinstance(node, dict):
            continue
        mid = node.get("id")
        name = str(node.get("name") or node.get("title") or "").strip()
        label = f"{prefix}{name}" if name else prefix.rstrip("/")
        if mid is not None and mid != "" and mid != 0 and mid != "0":
            out.append({"id": mid, "name": label or str(mid)})
        children = node.get("children") or node.get("child") or []
        if children:
            child_prefix = f"{label}/" if label else prefix
            out.extend(_flatten_modules(children, prefix=child_prefix))
    return out


def _status_of(row: dict[str, Any]) -> str:
    return str(row.get("status") or row.get("rawStatus") or "").strip().lower()


def _mode_of(row: dict[str, Any]) -> str:
    mode = row.get("mode")
    if mode is None:
        return ""
    return str(mode).strip().lower()


def _is_parent(row: dict[str, Any]) -> bool:
    raw = row.get("isParent")
    if raw in (True, 1, "1", "true", "True"):
        return True
    children = row.get("children")
    return isinstance(children, list) and len(children) > 0


def _consumed_of(row: dict[str, Any]) -> float:
    try:
        return float(row.get("consumed") or 0)
    except (TypeError, ValueError):
        return 0.0


def _parent_of(row: dict[str, Any]) -> int:
    return _id_of(row.get("parent")) or 0


def _child_ids_from_path(task: dict[str, Any], task_id: int) -> set[int]:
    """Approximate getAllChildId via path when present; else just self."""
    out = {task_id}
    path = str(task.get("path") or "").strip()
    if not path:
        return out
    # ZenTao path looks like ,1,2,3,
    for part in path.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            out.add(int(part))
        except ValueError:
            continue
    return out


def _walk_task_rows(rows: list[Any]) -> list[dict[str, Any]]:
    """Flatten mergeChildren nesting into a flat task list."""
    flat: list[dict[str, Any]] = []

    def walk(items: list[Any]) -> None:
        for row in items:
            if not isinstance(row, dict):
                continue
            flat.append(row)
            kids = row.get("children")
            if isinstance(kids, list) and kids:
                walk(kids)

    walk(rows)
    return flat


def filter_parent_candidates(
    rows: list[dict[str, Any]],
    *,
    task_id: int,
    append_parent_id: int | None = None,
    exclude_ids: set[int] | None = None,
) -> list[dict[str, Any]]:
    """Mirror task::getParentTaskPairs filters (best-effort on REST list fields)."""
    exclude = set(exclude_ids or ())
    exclude.add(task_id)
    blocked = {"cancel", "closed"}
    pairs: list[dict[str, Any]] = []
    seen: set[int] = set()

    for row in rows:
        tid = _id_of(row.get("id"))
        if tid is None:
            continue
        if tid in exclude:
            continue
        if _status_of(row) in blocked:
            continue
        if _parent_of(row) != 0:
            continue
        if _mode_of(row):
            continue
        if not _is_parent(row) and _consumed_of(row) > 0:
            continue
        if tid in seen:
            continue
        seen.add(tid)
        pairs.append({"id": tid, "name": row.get("name")})

    if append_parent_id and append_parent_id not in seen and append_parent_id not in exclude:
        for row in rows:
            if _id_of(row.get("id")) == append_parent_id:
                pairs.append({"id": append_parent_id, "name": row.get("name")})
                break
        else:
            pairs.append({"id": append_parent_id, "name": None})

    pairs.sort(key=lambda x: int(x["id"]))
    return pairs


def edit_options(
    client: ZenTaoClient,
    task_id: str | int,
    *,
    execution_id: str | int | None = None,
) -> dict[str, Any]:
    """Option lists for filling task update fields (Web edit form sources).

    - executions: project-scoped REST list (``execution::getByProject`` on Web)
    - modules: ``GET /modules?type=task&id=<execution>`` (``tree::getTaskOptionMenu``)
    - parents: REST execution tasks filtered like ``task::getParentTaskPairs``
    """
    rest = _as_rest(client)
    tid = int(task_id)
    task = rest.get_task(tid)
    project_id = _id_of(task.get("project"))
    current_execution = _id_of(task.get("execution"))
    target_execution = _id_of(execution_id) or current_execution
    current_module = _id_of(task.get("module"))
    current_parent = _id_of(task.get("parent"))

    executions: list[dict[str, Any]] = []
    if project_id:
        data = rest.list_resource(
            "executions",
            page=1,
            limit=200,
            scopes={"project": project_id},
        )
        for row in data.get("executions") or []:
            if not isinstance(row, dict):
                continue
            eid = row.get("id")
            if eid is None:
                continue
            executions.append(
                {
                    "id": eid,
                    "name": row.get("name"),
                    "status": row.get("status"),
                    "type": row.get("type"),
                }
            )

    modules: list[dict[str, Any]] = []
    if target_execution:
        mod_data = rest.list_resource(
            "modules",
            page=1,
            limit=500,
            query={"type": "task", "id": str(target_execution)},
        )
        modules = _flatten_modules(mod_data.get("modules") or [])

    parents: list[dict[str, Any]] = []
    parent_note = (
        "Filtered client-side like Web getParentTaskPairs; "
        "not a dedicated REST endpoint. Child exclusion uses task.path when present."
    )
    if target_execution:
        page = 1
        raw_rows: list[dict[str, Any]] = []
        seen: set[Any] = set()
        while page <= 100:
            data = rest.list_resource(
                "tasks",
                page=page,
                limit=200,
                scopes={"execution": target_execution},
            )
            chunk = data.get("tasks") or []
            if not chunk:
                break
            for row in _walk_task_rows(chunk if isinstance(chunk, list) else []):
                rid = row.get("id")
                if rid in seen:
                    continue
                seen.add(rid)
                raw_rows.append(row)
            total = int(data.get("total") or 0)
            if total and len(seen) >= total:
                break
            if len(chunk) < int(data.get("limit") or 200):
                break
            page += 1
        exclude = _child_ids_from_path(task, tid)
        parents = filter_parent_candidates(
            raw_rows,
            task_id=tid,
            append_parent_id=current_parent if target_execution == current_execution else None,
            exclude_ids=exclude,
        )

    return {
        "taskId": tid,
        "project": project_id,
        "execution": target_execution,
        "current": {
            "execution": current_execution,
            "module": current_module,
            "parent": current_parent,
            "name": task.get("name"),
            "status": task.get("status"),
        },
        "executions": executions,
        "modules": modules,
        "parents": parents,
        "notes": {
            "source": {
                "executions": "REST GET /projects/:id/executions (Web: execution::getByProject)",
                "modules": "REST GET /modules?type=task&id=:execution (Web: tree::ajaxGetOptionMenu / getTaskOptionMenu)",
                "parents": "REST GET /executions/:id/tasks + getParentTaskPairs filters (Web edit form; no dedicated REST)",
            },
            "parents": parent_note,
            "usage": {
                "execution": "task update <id> --execution=<eid> or --data '{\"execution\":…}'",
                "module": "task update <id> --data '{\"module\":…}'",
                "parent": "task update <id> --data '{\"parent\":…}'",
            },
        },
        "taskSummary": summarize_task(task),
        "backend": rest.backend,
    }
