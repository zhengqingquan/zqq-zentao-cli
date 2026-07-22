#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HTML / zin / dtable parsing and response success/failure checks."""

from __future__ import annotations

import json
import re
from html import escape, unescape
from typing import Any


def html_comment(text: str) -> str:
    return f"<p><span>{escape(text)}</span></p>"


def strip_tags(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s or "").strip()


def extract_balanced(text: str, start: int, open_ch: str, close_ch: str) -> str | None:
    if start < 0 or start >= len(text) or text[start] != open_ch:
        return None
    depth = 0
    in_str = False
    esc = False
    for j in range(start, len(text)):
        ch = text[j]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == open_ch:
            depth += 1
        elif ch == close_ch:
            depth -= 1
            if depth == 0:
                return text[start : j + 1]
    return None


def extract_attr_object(html: str, attr: str) -> str | None:
    key = f'{attr}="'
    i = html.find(key)
    if i < 0:
        return None
    start = html.find("{", i)
    return extract_balanced(html, start, "{", "}")


def extract_array_after(text: str, marker: str) -> str | None:
    i = text.find(marker)
    if i < 0:
        return None
    start = text.find("[", i)
    return extract_balanced(text, start, "[", "]")


def zin_main_html(payload: Any) -> str | None:
    """Extract main HTML from a ?zin=1 JSON fragment array."""
    if not isinstance(payload, list):
        return None
    for part in payload:
        if isinstance(part, dict) and part.get("name") == "main":
            html = part.get("data") or ""
            return unescape(str(html)).replace("&quot;", '"')
    return None


def parse_dtable_rows(html: str) -> list[dict[str, Any]]:
    html = unescape(html).replace("&quot;", '"')
    raw = extract_attr_object(html, "zui-create-dtable")
    if not raw:
        return []
    arr = extract_array_after(raw, '"data"')
    if not arr:
        return []
    try:
        rows = json.loads(arr)
    except json.JSONDecodeError:
        return []
    return rows if isinstance(rows, list) else []


def looks_auth_fail(r: dict[str, Any]) -> bool:
    data = r.get("data")
    s = data if isinstance(data, str) else json.dumps(data or {}, ensure_ascii=False)
    raw = r.get("raw") or ""
    if isinstance(data, dict) and (data.get("loginExpired") is True or data.get("load") == "login"):
        return True
    return bool(re.search(r"登录已超时|用户登录|loginExpired|重新登|登录失败", s + raw, re.I))


def looks_write_fail(r: dict[str, Any]) -> bool:
    data = r.get("data")
    return isinstance(data, dict) and data.get("result") == "fail" and not data.get("status")


def is_write_success(data: Any) -> bool:
    return (
        isinstance(data, dict)
        and data.get("status") == "success"
        and (data.get("closeModal") is True or (data.get("callback") or {}).get("name"))
    )


def parse_task_view_html(html: str, task_id: str | int) -> dict[str, Any]:
    html = unescape(html).replace("&quot;", '"')
    out: dict[str, Any] = {"id": int(task_id) if str(task_id).isdigit() else task_id}
    m = re.search(r'class="[^"]*entity-title[^"]*"[^>]*>(.*?)</div>', html, re.S | re.I)
    if m:
        title = strip_tags(m.group(1))
        title = re.sub(rf"^{re.escape(str(task_id))}\s*", "", title).strip(" ·-–—")
        out["name"] = title

    # ZenTao UI labels (Chinese) → field keys
    label_map = {
        "状态": "status",
        "任务状态": "status",
        "优先级": "pri",
        "指派给": "assignedToRealName",
        "截止日期": "deadline",
        "所属执行": "executionName",
        "所属项目": "projectName",
        "任务类型": "type",
        "预计开始": "estStarted",
        "实际开始": "realStarted",
        "由谁完成": "finishedBy",
    }
    for lab, key in label_map.items():
        # title="<label>" or plain label text followed by value
        pat = rf'(?:title="{re.escape(lab)}"[^>]*>|{re.escape(lab)})\s*([^<]{{0,80}})'
        mm = re.search(pat, html)
        if not mm:
            continue
        val = strip_tags(mm.group(1)).strip()
        val = re.sub(r"\s+", " ", val)
        # skip if value is just the label again
        if not val or val == lab:
            # try text="..." near the label
            mm2 = re.search(
                rf'{re.escape(lab)}[\s\S]{{0,120}}?text="([^"]+)"',
                html,
            )
            if mm2:
                val = mm2.group(1)
            else:
                continue
        if key == "pri" and re.search(r"\d+", val):
            out[key] = int(re.search(r"\d+", val).group())
        else:
            out[key] = val
    return out
