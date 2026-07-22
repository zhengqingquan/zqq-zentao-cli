# -*- coding: utf-8 -*-
"""REST v1 read-only resource registry (list / detail + scopes)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Resource:
    """One browsable REST resource.

    scopes: CLI flag name -> path template with ``{id}``.
    When a scope is provided, that path is used instead of ``list_path``.
    require_scope: listing needs at least one scope (API rejects bare list).
    path_param: positional CLI arg substituted into list_path as ``{param}``
                (e.g. tabs / options).
    query_params: optional/extra GET query flags exposed on the list command.
    required_query: subset of query_params that must be set.
    user_filters: CLI flags for account filters (client-side; e.g. assignedTo).
    """

    key: str
    help: str
    list_cmd: str | None = None
    detail_cmd: str | None = None
    list_path: str | None = None
    detail_path: str | None = None
    list_key: str | None = None
    detail_keys: tuple[str, ...] = ()
    paginated: bool = True
    scopes: dict[str, str] = field(default_factory=dict)
    require_scope: bool = False
    path_param: str | None = None
    query_params: tuple[str, ...] = ()
    required_query: tuple[str, ...] = ()
    user_filters: tuple[str, ...] = ()


# Hand-written CLI commands (custom parser and/or non-registry dispatch).
# Pure REST browse commands live only in RESOURCES and auto-register.
SPECIAL_CMDS = frozenset(
    {
        "login",
        "whoami",
        "my-tasks",
        "my-bugs",
        "my-stories",
        "my-todos",
        "my-testcases",
        "my-testtasks",
        "my-feedbacks",
        "my-tickets",
        "tasks",  # dual-backend + table output; also covers registry key "tasks"
        "task",
        "bug",  # get + REST write/actions (overrides registry detail-only)
        "story",  # get + REST write/actions (overrides registry detail-only)
        "comment",
    }
)
# Back-compat alias for imports.
EXISTING_CMDS = SPECIAL_CMDS

RESOURCES: dict[str, Resource] = {}


def _add(r: Resource) -> None:
    if r.key in RESOURCES:
        raise ValueError(f"duplicate resource key: {r.key}")
    RESOURCES[r.key] = r


# --- system ---
_add(
    Resource(
        key="ping",
        help="REST ping / token life",
        list_cmd="ping",
        list_path="/ping",
        paginated=False,
    )
)
_add(
    Resource(
        key="langs",
        help="Language pack (REST)",
        list_cmd="langs",
        list_path="/langs",
        paginated=False,
    )
)
_add(
    Resource(
        key="views",
        help="Views (REST)",
        list_cmd="views",
        list_path="/views",
        paginated=False,
    )
)
_add(
    Resource(
        key="groups",
        help="User groups (REST)",
        list_cmd="groups",
        list_path="/groups",
        list_key="groups",
        paginated=False,
    )
)
_add(
    Resource(
        key="tabs",
        help="Module tabs (REST)",
        list_cmd="tabs",
        list_path="/tabs/{param}",
        list_key="tabs",
        paginated=False,
        path_param="module",
    )
)
_add(
    Resource(
        key="options",
        help="Option lists for a type (REST)",
        list_cmd="options",
        list_path="/options/{param}",
        list_key="options",
        paginated=False,
        path_param="type",
    )
)
_add(
    Resource(
        key="configurations",
        help="Configuration list (REST)",
        list_cmd="configurations",
        list_path="/configurations",
        paginated=False,
    )
)
_add(
    Resource(
        key="configuration",
        help="Configuration item (REST)",
        detail_cmd="configuration",
        detail_path="/configurations/{id}",
        paginated=False,
    )
)
_add(
    Resource(
        key="required-fields",
        help="Required fields config (REST)",
        list_cmd="required-fields",
        list_path="/requiredFields",
        paginated=False,
    )
)

# --- org / structure ---
_add(
    Resource(
        key="users",
        help="User list/detail (REST)",
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
        key="departments",
        help="Department list/detail (REST)",
        list_cmd="departments",
        detail_cmd="department",
        list_path="/departments",
        detail_path="/departments/{id}",
        list_key="departments",
        detail_keys=("department",),
        paginated=False,
    )
)
_add(
    Resource(
        key="programs",
        help="Program list/detail (REST)",
        list_cmd="programs",
        detail_cmd="program",
        list_path="/programs",
        detail_path="/programs/{id}",
        list_key="programs",
        detail_keys=("program",),
    )
)
_add(
    Resource(
        key="products",
        help="Product list (REST)",
        list_cmd="products",
        detail_cmd="product",
        list_path="/products",
        detail_path="/products/{id}",
        list_key="products",
        detail_keys=("product",),
        scopes={"program": "/programs/{id}/products"},
    )
)
_add(
    Resource(
        key="projects",
        help="Project list/detail (REST)",
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
    )
)
_add(
    Resource(
        key="executions",
        help="Execution list/detail (REST)",
        list_cmd="executions",
        detail_cmd="execution",
        list_path="/executions",
        detail_path="/executions/{id}",
        list_key="executions",
        detail_keys=("execution",),
        scopes={"project": "/projects/{id}/executions"},
    )
)
_add(
    Resource(
        key="tasks",
        help="Task list/detail (REST)",
        list_cmd="tasks",
        detail_cmd="task",
        list_path="/tasks",
        detail_path="/tasks/{id}",
        list_key="tasks",
        detail_keys=("task",),
        scopes={"execution": "/executions/{id}/tasks"},
    )
)
_add(
    Resource(
        key="stakeholders",
        help="Program stakeholders (REST)",
        list_cmd="stakeholders",
        list_path=None,
        list_key="stakeholders",
        scopes={"program": "/programs/{id}/stakeholders"},
        require_scope=True,
    )
)

# --- story / bug ---
_add(
    Resource(
        key="stories",
        help="Story list/detail (REST; list needs --product/--project/--execution)",
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
        key="story-grades",
        help="Story grades (REST)",
        list_cmd="story-grades",
        list_path="/storygrades",
        paginated=False,
        query_params=("type", "status"),
    )
)
_add(
    Resource(
        key="bugs",
        help="Bug list/detail (REST; list needs --product/--project/--execution)",
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

# --- plan / release / build ---
_add(
    Resource(
        key="productplans",
        help="Product plan list/detail (REST; list needs --product)",
        list_cmd="productplans",
        detail_cmd="productplan",
        list_path=None,
        detail_path="/productplans/{id}",
        list_key="plans",
        detail_keys=("productplan", "plan"),
        scopes={"product": "/products/{id}/plans"},
        require_scope=True,
    )
)
_add(
    Resource(
        key="releases",
        help="Release list/detail (REST; list needs --product or --project)",
        list_cmd="releases",
        detail_cmd="release",
        list_path=None,
        detail_path="/releases/{id}",
        list_key="releases",
        detail_keys=("release",),
        scopes={
            "product": "/products/{id}/releases",
            "project": "/projects/{id}/releases",
        },
        require_scope=True,
    )
)
_add(
    Resource(
        key="builds",
        help="Build list/detail (REST; list needs --project or --execution)",
        list_cmd="builds",
        detail_cmd="build",
        list_path=None,
        detail_path="/builds/{id}",
        list_key="builds",
        detail_keys=("build",),
        scopes={
            "project": "/projects/{id}/builds",
            "execution": "/executions/{id}/builds",
        },
        require_scope=True,
    )
)

# --- test ---
_add(
    Resource(
        key="testcases",
        help="Testcase list/detail (REST; list needs scope)",
        list_cmd="testcases",
        detail_cmd="testcase",
        list_path=None,
        detail_path="/testcases/{id}",
        list_key="testcases",
        detail_keys=("testcase", "case"),
        scopes={
            "product": "/products/{id}/testcases",
            "project": "/projects/{id}/testcases",
            "execution": "/executions/{id}/testcases",
        },
        require_scope=True,
    )
)
_add(
    Resource(
        key="testsuites",
        help="Testsuite list/detail (REST; list needs --product)",
        list_cmd="testsuites",
        detail_cmd="testsuite",
        list_path=None,
        detail_path="/testsuites/{id}",
        list_key="testsuites",
        detail_keys=("testsuite", "suite"),
        scopes={"product": "/products/{id}/testsuites"},
        require_scope=True,
    )
)
_add(
    Resource(
        key="testtasks",
        help="Testtask list/detail (REST)",
        list_cmd="testtasks",
        detail_cmd="testtask",
        list_path="/testtasks",
        detail_path="/testtasks/{id}",
        list_key="testtasks",
        detail_keys=("testtask", "task"),
        scopes={"project": "/projects/{id}/testtasks"},
    )
)

# --- feedback / ticket / todo ---
_add(
    Resource(
        key="feedbacks",
        help="Feedback list/detail (REST)",
        list_cmd="feedbacks",
        detail_cmd="feedback",
        list_path="/feedbacks",
        detail_path="/feedbacks/{id}",
        list_key="feedbacks",
        detail_keys=("feedback",),
    )
)
_add(
    Resource(
        key="tickets",
        help="Ticket list/detail (REST)",
        list_cmd="tickets",
        detail_cmd="ticket",
        list_path="/tickets",
        detail_path="/tickets/{id}",
        list_key="tickets",
        detail_keys=("ticket",),
    )
)
_add(
    Resource(
        key="todos",
        help="Todo list/detail (REST)",
        list_cmd="todos",
        detail_cmd="todo",
        list_path="/todos",
        detail_path="/todos/{id}",
        list_key="todos",
        detail_keys=("todo",),
    )
)

# --- issue / risk / meeting ---
_add(
    Resource(
        key="issues",
        help="Issue list/detail (REST)",
        list_cmd="issues",
        detail_cmd="issue",
        list_path="/issues",
        detail_path="/issues/{id}",
        list_key="issues",
        detail_keys=("issue",),
        scopes={
            "product": "/products/{id}/issues",
            "project": "/projects/{id}/issues",
        },
    )
)
_add(
    Resource(
        key="risks",
        help="Risk list/detail (REST)",
        list_cmd="risks",
        detail_cmd="risk",
        list_path="/risks",
        detail_path="/risks/{id}",
        list_key="risks",
        detail_keys=("risk",),
        scopes={"project": "/projects/{id}/risks"},
    )
)
_add(
    Resource(
        key="meetings",
        help="Meeting list (REST; needs --project; no detail entry in OSS)",
        list_cmd="meetings",
        list_path=None,
        list_key="meetings",
        scopes={"project": "/projects/{id}/meetings"},
        require_scope=True,
    )
)

# --- docs / files / modules ---
_add(
    Resource(
        key="doclibs",
        help="Doc lib list (REST)",
        list_cmd="doclibs",
        list_path="/doclibs",
        list_key="libs",
        paginated=False,
    )
)
_add(
    Resource(
        key="docs",
        help="Doc list/detail (REST; list needs --lib)",
        list_cmd="docs",
        detail_cmd="doc",
        list_path=None,
        detail_path="/docs/{id}",
        list_key="docs",
        detail_keys=("doc",),
        scopes={"lib": "/doclibs/{id}"},
        require_scope=True,
        paginated=False,
    )
)
_add(
    Resource(
        key="file",
        help="File meta (REST)",
        detail_cmd="file",
        detail_path="/files/{id}",
        detail_keys=("file",),
    )
)
_add(
    Resource(
        key="modules",
        help="Module tree (REST; needs --type and --id)",
        list_cmd="modules",
        list_path="/modules",
        list_key="modules",
        paginated=False,
        query_params=("type", "id"),
        required_query=("type", "id"),
    )
)


def resources_for_cli() -> list[Resource]:
    """Resources that introduce at least one CLI command not in SPECIAL_CMDS."""
    out: list[Resource] = []
    for r in RESOURCES.values():
        cmds = [c for c in (r.list_cmd, r.detail_cmd) if c]
        if not cmds:
            continue
        if all(c in SPECIAL_CMDS for c in cmds):
            continue
        out.append(r)
    return out


def capability_names() -> list[str]:
    names: list[str] = []
    for r in resources_for_cli():
        if r.list_cmd and r.list_cmd not in SPECIAL_CMDS:
            names.append(r.list_cmd)
        if r.detail_cmd and r.detail_cmd not in SPECIAL_CMDS:
            names.append(r.detail_cmd)
    return names


def resource_by_list_cmd(cmd: str) -> Resource | None:
    for r in RESOURCES.values():
        if r.list_cmd == cmd:
            return r
    return None


def resource_by_detail_cmd(cmd: str) -> Resource | None:
    for r in RESOURCES.values():
        if r.detail_cmd == cmd:
            return r
    return None
