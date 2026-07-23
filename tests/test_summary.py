# -*- coding: utf-8 -*-
"""Offline tests for services.summary (tasks truncation semantics)."""

from __future__ import annotations

from typing import Any

from zqq_zentao_cli.services import summary as summary_svc


class _RestStub:
    backend = "rest"
    api_version = "v1"
    profile = {"account": "alice"}


def test_summarize_tasks_truncated_keeps_facet_total(
    monkeypatch: Any,
) -> None:
    def fake_list_tasks(*_a: Any, **_k: Any) -> dict[str, Any]:
        return {
            "tasks": [
                {"id": 1, "status": "wait", "pri": 1},
                {"id": 2, "status": "doing", "pri": 2},
            ],
            "total": 99,
            "backend": "rest",
            "api": "v1",
        }

    monkeypatch.setattr(summary_svc.task_svc, "list_tasks", fake_list_tasks)
    monkeypatch.setattr(summary_svc, "_as_rest", lambda _c: _RestStub())
    out = summary_svc.summarize_tasks(_RestStub(), facet="status")  # type: ignore[arg-type]
    assert out["truncated"] is True
    assert out["reportedTotal"] == 99
    assert out["total"] == 2
    assert sum(out["facets"]["status"].values()) == 2
