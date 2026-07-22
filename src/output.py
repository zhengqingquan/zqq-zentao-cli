#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CLI output formatting aligned with official zentao-cli (--format / --silent / --machine-readable)."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from typing import Any, Literal

FormatName = Literal["markdown", "json", "raw"]

_LIST_KEYS = (
    "tasks",
    "users",
    "projects",
    "programs",
    "products",
    "executions",
    "stories",
    "bugs",
    "departments",
    "productplans",
    "releases",
    "builds",
    "testtasks",
    "testcases",
    "feedbacks",
    "tickets",
    "files",
    "groups",
    "docs",
    "data",
    "list",
)


@dataclass
class OutputOptions:
    format: FormatName = "markdown"
    silent: bool = False
    machine_readable: bool = False
    fields: list[str] | None = None
    is_list: bool | None = None
    pager: dict[str, Any] | None = None
    raw_response: Any = None


_opts: OutputOptions = OutputOptions()


def configure_output(
    *,
    format: str | None = None,
    silent: bool = False,
    machine_readable: bool = False,
) -> OutputOptions:
    """Apply global CLI output options (call once from main)."""
    global _opts
    fmt: FormatName = "markdown"
    if format:
        f = format.strip().lower()
        if f not in ("markdown", "json", "raw"):
            raise SystemExit(f"Invalid --format={format!r}, expected markdown|json|raw")
        fmt = f  # type: ignore[assignment]
    if machine_readable:
        os.environ["NO_COLOR"] = "1"
        os.environ["FORCE_COLOR"] = "0"
    _opts = OutputOptions(
        format=fmt,
        silent=bool(silent),
        machine_readable=bool(machine_readable),
    )
    return _opts


def get_output_options() -> OutputOptions:
    return _opts


def _print_text(text: str) -> None:
    try:
        print(text)
    except UnicodeEncodeError:
        enc = getattr(sys.stdout, "encoding", None) or "utf-8"
        sys.stdout.buffer.write((text + "\n").encode(enc, errors="replace"))
        sys.stdout.buffer.flush()


def _cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _pick(obj: dict[str, Any], key: str) -> Any:
    cur: Any = obj
    for part in key.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def _json_dumps(obj: Any, *, pretty: bool) -> str:
    if pretty:
        return json.dumps(obj, ensure_ascii=False, indent=2)
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def _markdown_table(rows: list[dict[str, Any]], fields: list[str] | None) -> str:
    if not rows:
        return ""
    cols = fields or list(rows[0].keys())
    if not cols:
        return ""
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    body = [
        "| " + " | ".join(_cell(_pick(row, c)) for c in cols) + " |"
        for row in rows
    ]
    return "\n".join([header, sep, *body])


def _markdown_object(obj: dict[str, Any], fields: list[str] | None) -> str:
    keys = fields or list(obj.keys())
    return "\n".join(f"* {k}: {_cell(_pick(obj, k))}" for k in keys)


def _extract_list(data: Any) -> tuple[list[dict[str, Any]] | None, dict[str, Any] | None]:
    if isinstance(data, list):
        rows = [x for x in data if isinstance(x, dict)]
        return rows, None
    if not isinstance(data, dict):
        return None, None
    for key in _LIST_KEYS:
        val = data.get(key)
        if isinstance(val, list) and (not val or isinstance(val[0], dict)):
            rows = [x for x in val if isinstance(x, dict)]
            pager = None
            total = data.get("total") or data.get("recTotal")
            page = data.get("page") or data.get("pageID")
            limit = data.get("limit") or data.get("recPerPage")
            if total is not None or page is not None or limit is not None:
                pager = {
                    "total": total,
                    "page": page,
                    "recPerPage": limit,
                }
            return rows, pager
    return None, None


def _pager_footer(pager: dict[str, Any] | None, shown: int) -> str:
    if not pager:
        return ""
    total = pager.get("total") or pager.get("recTotal")
    page = pager.get("page") or pager.get("pageID")
    per = pager.get("recPerPage") or pager.get("limit")
    if total is None and page is None and per is None:
        return ""
    if not shown and not total:
        return "\n\n没有数据"
    parts = [f"已显示 {shown} 项"]
    if total is not None:
        parts.append(f"共 {total} 项")
    if page is not None:
        parts.append(f"当前第 {page} 页")
    if per is not None:
        parts.append(f"每页 {per} 条")
    return "\n\n" + "，".join(parts)


def render(
    data: Any,
    *,
    format: FormatName | None = None,
    is_list: bool | None = None,
    fields: list[str] | None = None,
    pager: dict[str, Any] | None = None,
    raw_response: Any = None,
) -> str:
    """Render payload text without printing."""
    opts = _opts
    fmt = format or opts.format
    pretty = not opts.machine_readable
    flds = fields if fields is not None else opts.fields

    if fmt == "raw":
        return _json_dumps(raw_response if raw_response is not None else data, pretty=pretty)

    if fmt == "json":
        payload: dict[str, Any] = {"status": "success", "data": data}
        use_pager = pager
        if use_pager is None and is_list is not False:
            _, extracted = _extract_list(data)
            use_pager = extracted
        if use_pager:
            payload["pager"] = {
                "total": use_pager.get("total") or use_pager.get("recTotal"),
                "page": use_pager.get("page") or use_pager.get("pageID"),
                "recPerPage": use_pager.get("recPerPage") or use_pager.get("limit"),
            }
        return _json_dumps(payload, pretty=pretty)

    # markdown
    list_hint = is_list if is_list is not None else opts.is_list
    rows, extracted_pager = _extract_list(data)
    use_pager = pager if pager is not None else extracted_pager
    as_list = list_hint is True or (list_hint is not False and rows is not None)

    if as_list:
        table_rows = rows or []
        text = _markdown_table(table_rows, flds)
        return text + _pager_footer(use_pager, len(table_rows))

    if isinstance(data, dict):
        return _markdown_object(data, flds)

    if isinstance(data, list):
        return _json_dumps(data, pretty=pretty)

    return _cell(data)


def emit(
    data: Any,
    *,
    format: FormatName | None = None,
    is_list: bool | None = None,
    fields: list[str] | None = None,
    pager: dict[str, Any] | None = None,
    raw_response: Any = None,
) -> None:
    """Print formatted output unless --silent."""
    if _opts.silent:
        return
    text = render(
        data,
        format=format,
        is_list=is_list,
        fields=fields,
        pager=pager,
        raw_response=raw_response,
    )
    if text:
        _print_text(text)


def package_version() -> str:
    try:
        from importlib.metadata import version

        return version("zqq-zentao-cli")
    except Exception:
        return "0.1.0"
