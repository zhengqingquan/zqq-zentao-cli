# -*- coding: utf-8 -*-
"""REST APIv2 read-oriented resource registry (parallel to resources.py).

Writes stay on APIv1. Paths align with config/apiv2.php / docs/zentao-rest-apiv2.md.
"""

from __future__ import annotations

from .resources import Resource, RESOURCES as RESOURCES_V1

RESOURCES_V2: dict[str, Resource] = {}


def _add(res: Resource) -> None:
    if res.key in RESOURCES_V2:
        raise ValueError(f"Duplicate v2 resource key: {res.key}")
    RESOURCES_V2[res.key] = res


# Common browse surfaces (list + detail). Prefer same CLI cmds as v1.
_add(
    Resource(
        key="programs",
        help="Program list/detail (REST v2)",
        list_cmd="programs",
        detail_cmd="program",
        list_path="/programs",
        detail_path="/programs/{id}",
        list_key="programs",
        detail_keys=("program",),
        query_params=("search",),
    )
)
_add(
    Resource(
        key="products",
        help="Product list/detail (REST v2)",
        list_cmd="products",
        detail_cmd="product",
        list_path="/products/all",
        detail_path="/products/{id}",
        list_key="products",
        detail_keys=("product",),
        query_params=("search",),
    )
)
_add(
    Resource(
        key="projects",
        help="Project list/detail (REST v2; supports filters search)",
        list_cmd="projects",
        detail_cmd="project",
        list_path="/projects",
        detail_path="/projects/{id}",
        list_key="projects",
        detail_keys=("project",),
        scopes={
            "program": "/programs/{id}/projects",
            "product": "/products/{id}/projects",
        },
        query_params=("search",),
    )
)
_add(
    Resource(
        key="executions",
        help="Execution list/detail (REST v2)",
        list_cmd="executions",
        detail_cmd="execution",
        list_path="/executions",
        detail_path="/executions/{id}",
        list_key="executions",
        detail_keys=("execution", "executionStats"),
        scopes={"project": "/projects/{id}/executions"},
    )
)
_add(
    Resource(
        key="users",
        help="User list/detail (REST v2 falls back to v1 path shape when needed)",
        list_cmd="users",
        detail_cmd="user",
        list_path="/users",
        detail_path="/users/{id}",
        list_key="users",
        detail_keys=("user", "profile"),
        query_params=("search",),
    )
)
_add(
    Resource(
        key="stories",
        help="Story list/detail (REST v2; list needs scope)",
        list_cmd="stories",
        detail_cmd="story",
        list_path=None,
        detail_path="/stories/{id}",
        list_key="stories",
        detail_keys=("story",),
        scopes={
            "product": "/products/{id}/stories",
            "project": "/projects/{id}/stories",
            "execution": "/executions/{id}/stories",
        },
        require_scope=True,
        user_filters=("assignedTo", "openedBy"),
    )
)
_add(
    Resource(
        key="bugs",
        help="Bug list/detail (REST v2; list needs scope)",
        list_cmd="bugs",
        detail_cmd="bug",
        list_path=None,
        detail_path="/bugs/{id}",
        list_key="bugs",
        detail_keys=("bug",),
        scopes={
            "product": "/products/{id}/bugs",
            "project": "/projects/{id}/bugs",
            "execution": "/executions/{id}/bugs",
        },
        require_scope=True,
        user_filters=("assignedTo", "openedBy"),
    )
)
_add(
    Resource(
        key="tasks",
        help="Task list (REST v2 execution/task browse)",
        list_cmd="tasks",
        detail_cmd="task",
        list_path="/executions/task",
        detail_path="/tasks/{id}",
        list_key="tasks",
        detail_keys=("task",),
        scopes={"execution": "/executions/{id}/tasks", "project": "/projects/{id}/executions"},
    )
)


def resource_v2(key: str) -> Resource | None:
    return RESOURCES_V2.get(key)


def resolve_resource_for_api(key: str, api_version: str) -> Resource | None:
    """Pick v2 registry entry when available; else fall back to v1 definition."""
    if api_version == "v2":
        return RESOURCES_V2.get(key) or RESOURCES_V1.get(key)
    return RESOURCES_V1.get(key)
