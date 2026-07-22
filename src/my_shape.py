#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lightweight row summarizers for my-* Web dtable lists."""

from __future__ import annotations

from typing import Any

from .task_shape import user_field


def _status(row: dict[str, Any]) -> Any:
    return row.get("status") or row.get("rawStatus")


def _assigned(row: dict[str, Any]) -> Any:
    assigned = row.get("assignedTo")
    return user_field(assigned) if isinstance(assigned, dict) else assigned


def summarize_story(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row.get("id"),
        "title": row.get("title") or row.get("name"),
        "status": _status(row),
        "pri": row.get("pri"),
        "stage": row.get("stage"),
        "assignedTo": _assigned(row),
        "openedBy": (
            user_field(row["openedBy"])
            if isinstance(row.get("openedBy"), dict)
            else row.get("openedBy")
        ),
        "productName": row.get("productName") or row.get("product"),
    }


def summarize_todo(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row.get("id"),
        "name": row.get("name") or row.get("title"),
        "status": _status(row),
        "pri": row.get("pri"),
        "date": row.get("date"),
        "begin": row.get("begin"),
        "end": row.get("end"),
        "assignedTo": _assigned(row),
    }


def summarize_testcase(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row.get("id"),
        "title": row.get("title") or row.get("name"),
        "status": _status(row),
        "pri": row.get("pri"),
        "type": row.get("type"),
        "assignedTo": _assigned(row),
        "openedBy": (
            user_field(row["openedBy"])
            if isinstance(row.get("openedBy"), dict)
            else row.get("openedBy")
        ),
    }


def summarize_testtask(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row.get("id"),
        "name": row.get("name") or row.get("title"),
        "status": _status(row),
        "pri": row.get("pri"),
        "begin": row.get("begin"),
        "end": row.get("end"),
        "assignedTo": _assigned(row),
    }


def summarize_feedback(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row.get("id"),
        "title": row.get("title") or row.get("name"),
        "status": _status(row),
        "pri": row.get("pri"),
        "type": row.get("type"),
        "assignedTo": _assigned(row),
        "openedBy": (
            user_field(row["openedBy"])
            if isinstance(row.get("openedBy"), dict)
            else row.get("openedBy")
        ),
        "productName": row.get("productName") or row.get("product"),
    }


def summarize_ticket(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row.get("id"),
        "title": row.get("title") or row.get("name"),
        "status": _status(row),
        "pri": row.get("pri"),
        "type": row.get("type"),
        "assignedTo": _assigned(row),
        "openedBy": (
            user_field(row["openedBy"])
            if isinstance(row.get("openedBy"), dict)
            else row.get("openedBy")
        ),
        "productName": row.get("productName") or row.get("product"),
    }
